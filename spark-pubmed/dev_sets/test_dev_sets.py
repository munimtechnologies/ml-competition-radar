"""Offline tests for dev_sets.py (fake E-utilities and a tiny fake corpus file). Apache-2.0."""
import gzip
import hashlib
import io
import json
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dev_sets as D  # noqa: E402

TITLE = "A programmable dual-RNA-guided DNA endonuclease in adaptive bacterial immunity"
ITEM = {"id": "L01", "question": "q", "title": TITLE, "year": 2012, "journal": "Science",
        "first_author": "Jinek M", "contested": False}


def summ(uid, title, pubdate, pubtype=("Journal Article",), pmc=None):
    ids = [{"idtype": "pubmed", "value": uid}]
    if pmc:
        ids.append({"idtype": "pmc", "value": pmc})
    return {"uid": uid, "title": title, "pubdate": pubdate, "source": "Science",
            "sortfirstauthor": "Jinek M", "authors": [{"name": "Jinek M"}],
            "pubtype": list(pubtype), "articleids": ids}


class FakeEu:
    def __init__(self, hits, docs, fail=False):
        self.hits, self.docs, self.fail, self.calls, self.terms = hits, docs, fail, 0, []

    def search(self, term):
        if self.fail:
            raise RuntimeError("esearch.fcgi: OSError: down")
        self.terms.append(term)
        for key, ids in self.hits:
            if key in term:
                return ids
        return []

    def summary(self, pmids):
        return [self.docs[p] for p in pmids]


def rec_xml(pmid, year=1990, words=5, ptype="Journal Article", title="Some title", label=None):
    lab = ' Label="%s"' % label if label else ""
    return ("<PubmedArticle><MedlineCitation><PMID>%d</PMID><Article><Journal><JournalIssue><PubDate>"
            "<Year>%d</Year></PubDate></JournalIssue><ISOAbbreviation>J X</ISOAbbreviation></Journal>"
            "<ArticleTitle>%s</ArticleTitle><Abstract><AbstractText%s>%s</AbstractText></Abstract>"
            "<PublicationTypeList><PublicationType>%s</PublicationType></PublicationTypeList></Article>"
            "<MeshHeadingList><MeshHeading><DescriptorName>Humans</DescriptorName></MeshHeading>"
            "</MeshHeadingList></MedlineCitation><PubmedData><ArticleIdList>"
            "<ArticleId IdType=\"pmc\">PMC%d</ArticleId></ArticleIdList></PubmedData></PubmedArticle>"
            % (pmid, year, title, lab, " ".join(["word"] * words), ptype, pmid))


def corpus_bytes():
    recs = [rec_xml(1, label="BACKGROUND")] + [rec_xml(i) for i in range(2, 11)]
    recs += [rec_xml(11, ptype="Editorial"), rec_xml(12, words=4), rec_xml(13, year=1950),
             rec_xml(15, title="")]
    xml = '<?xml version="1.0"?>\n<PubmedArticleSet>%s</PubmedArticleSet>' % "".join(recs)
    return gzip.compress(xml.encode("utf-8"))


class TitleTest(unittest.TestCase):
    def test_title_term(self):
        self.assertEqual(D.title_term(TITLE, 2012),
                         "programmable[ti] AND dual[ti] AND rna[ti] AND guided[ti] AND dna[ti] AND "
                         "endonuclease[ti] AND adaptive[ti] AND bacterial[ti] AND immunity[ti] AND 2012[dp]")
        self.assertEqual(D.title_term("Delta Delta C(T) method"), "delta[ti] AND method[ti]")

    def test_title_ratio(self):
        self.assertEqual(D.title_ratio("Basic local alignment search tool.", "basic local alignment search tool"), 1.0)
        self.assertEqual(D.title_ratio("Köhler", "Kohler"), 1.0)
        self.assertLess(D.title_ratio(TITLE, "Unrelated paper about mice"), D.TITLE_MIN)

    def test_year_of_pubdate(self):
        self.assertEqual(D.year_of_pubdate("2012 Aug 17"), 2012)
        self.assertIsNone(D.year_of_pubdate(""))


class VerifyTest(unittest.TestCase):
    def test_fallback_to_author(self):
        docs = {"111": summ("111", TITLE + ".", "2012 Aug 17", pmc="PMC6286148"),
                "112": summ("112", "Some other paper", "2012")}
        r = D.verify(ITEM, FakeEu([("Jinek M[1au]", ["111", "112"])], docs))
        self.assertEqual(r["status"], "verified")
        self.assertEqual(r["strategy"], "author+year+journal")
        self.assertEqual((r["pmid"], r["pmcid"], r["year_diff"], r["runner_up"]), ("111", "PMC6286148", 0, None))
        self.assertTrue(r["in_window"])
        self.assertEqual([t["hits"] for t in r["tried"]], [0, 2])

    def test_wrong_title_rejected(self):
        docs = {"222": summ("222", "Unrelated paper about mice", "2012")}
        r = D.verify(ITEM, FakeEu([("[ti]", ["222"])], docs))
        self.assertEqual(r["status"], "not_found")
        self.assertEqual(len(r["tried"]), 3)

    def test_year_window(self):
        r = D.verify(ITEM, FakeEu([("[ti]", ["333"])], {"333": summ("333", TITLE, "2015")}))
        self.assertEqual(r["status"], "not_found")
        r = D.verify(ITEM, FakeEu([("[ti]", ["333"])], {"333": summ("333", TITLE, "2013 Jan")}))
        self.assertEqual((r["status"], r["strategy"], r["year_diff"]), ("verified", "title+year", 1))

    def test_group_author_and_error(self):
        item = dict(ITEM, first_author="")
        self.assertEqual([n for n, _ in D.strategies(item)], ["title+year", "title"])
        r = D.verify(ITEM, FakeEu([], {}, fail=True))
        self.assertEqual(r["status"], "error")

    def test_run_landmarks(self):
        ctrl = {"id": "C01", "question": "q", "title": "Molecular structure of nucleic acids; a structure "
                "for deoxyribose nucleic acid", "year": 1953, "journal": "Nature",
                "first_author": "Watson JD", "contested": False, "control": True}
        docs = {"111": summ("111", TITLE + ".", "2012 Aug 17", pmc="PMC1"),
                "900": summ("900", ctrl["title"] + ".", "1953 Apr 25")}
        eu = FakeEu([("programmable[ti]", ["111"]), ("molecular[ti]", ["900"])], docs)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "landmarks.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"landmarks": [ITEM, ctrl]}, f)
            s = D.run_landmarks(path, tmp, eu)
            with open(os.path.join(tmp, "landmarks_verified.json"), encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)), 2)
        self.assertEqual((s["landmarks"], s["controls"], s["verified"], s["verified_title_year"]), (1, 1, 1, 1))
        self.assertEqual((s["verified_in_window"], s["verified_with_pmcid"]), (1, 1))
        self.assertEqual((s["controls_found"], s["controls_in_window"], s["not_found"]), (["C01"], [], []))


class EutilsTest(unittest.TestCase):
    def test_retry_then_success(self):
        calls, slept = [], []

        def opener(url):
            calls.append(url)
            if len(calls) == 1:
                raise OSError("boom")
            return io.BytesIO(json.dumps({"esearchresult": {"idlist": ["5"]}}).encode())

        eu = D.Eutils(opener=opener, pause=0.4, sleep=slept.append)
        self.assertEqual(eu.search("x[ti]"), ["5"])
        self.assertEqual(slept, [0.4, 2, 0.4])
        self.assertEqual(eu.calls, 2)
        self.assertIn("tool=mv2-munim-spark-dev", calls[1])
        self.assertIn("db=pubmed", calls[1])

    def test_gives_up(self):
        def opener(url):
            raise OSError("down")

        eu = D.Eutils(opener=opener, sleep=lambda s: None)
        with self.assertRaises(RuntimeError):
            eu.search("x[ti]")

    def test_summary(self):
        res = {"result": {"uids": ["1", "2"], "1": {"uid": "1"}, "2": {"uid": "2"}}}
        eu = D.Eutils(opener=lambda url: io.BytesIO(json.dumps(res).encode()), sleep=lambda s: None)
        self.assertEqual([s["uid"] for s in eu.summary(["1", "2"])], ["1", "2"])
        self.assertEqual(eu.summary([]), [])
        self.assertEqual(eu.calls, 1)


class PoolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "f.xml.gz")
        with open(self.path, "wb") as f:
            f.write(corpus_bytes())

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse(self):
        first = next(D.parse_file(self.path))
        self.assertEqual((first["pmid"], first["year"], first["journal"], first["pmcid"]), (1, 1990, "J X", "PMC1"))
        self.assertEqual((first["mesh"], first["pubtypes"]), (["Humans"], ["Journal Article"]))
        self.assertTrue(first["abstract"].startswith("BACKGROUND: word"))

    def test_sample_is_eligible_and_deterministic(self):
        s1, total, n_ok = D.sample_file(self.path, 3, random.Random(1), 5)
        s2, _, _ = D.sample_file(self.path, 3, random.Random(1), 5)
        self.assertEqual((total, n_ok, len(s1)), (14, 10, 3))
        self.assertEqual([r["pmid"] for r in s1], [r["pmid"] for r in s2])
        self.assertTrue(all(1 <= r["pmid"] <= 10 for r in s1))
        everything, _, _ = D.sample_file(self.path, 20, random.Random(1), 5)
        self.assertEqual([r["pmid"] for r in everything], list(range(1, 11)))

    def test_download_and_pool(self):
        data = corpus_bytes()
        md5 = hashlib.md5(data).hexdigest()
        urls = {D.CORPUS + "pubmed27n0001.xml.gz": data,
                D.CORPUS + "pubmed27n0001.xml.gz.md5": ("MD5(pubmed27n0001.xml.gz)= %s\n" % md5).encode(),
                D.CORPUS + "pubmed27n0002.xml.gz": data,
                D.CORPUS + "pubmed27n0002.xml.gz.md5": ("MD5(pubmed27n0002.xml.gz)= %s\n" % ("0" * 32)).encode()}

        def opener(url):
            if url not in urls:
                raise OSError("404 " + url)
            return io.BytesIO(urls[url])

        raw, out = os.path.join(self.tmp.name, "raw"), os.path.join(self.tmp.name, "out")
        os.makedirs(out)
        s = D.run_pool([1], raw, out, 3, 5, 7, opener)
        self.assertEqual((s["pool"], s["unique_pmids"], s["failed"]), (3, 3, []))
        f = s["files"][0]
        self.assertEqual((f["problem"], f["records"], f["eligible"], f["sampled"]), (None, 14, 10, 3))
        with open(os.path.join(out, "r_pool.jsonl"), encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        self.assertEqual([r["file"] for r in rows], ["pubmed27n0001.xml.gz"] * 3)
        self.assertTrue(D.run_pool([1], raw, out, 3, 5, 7, opener)["files"][0]["skipped"])
        bad = D.run_pool([2], raw, out, 3, 5, 7, opener)
        self.assertEqual(bad["failed"], ["pubmed27n0002.xml.gz"])
        self.assertTrue(bad["files"][0]["problem"].startswith("md5 mismatch"))
        self.assertFalse(os.path.exists(os.path.join(raw, "pubmed27n0002.xml.gz")))


class LandmarkFileTest(unittest.TestCase):
    def test_landmarks_file(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "landmarks.json"), encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("\t", text)
        items = json.loads(text)["landmarks"]
        self.assertEqual(len({i["id"] for i in items}), len(items))
        for it in items:
            for key in ("id", "question", "title", "year", "journal", "first_author", "contested"):
                self.assertIn(key, it, it["id"])
            self.assertTrue(D.title_term(it["title"]), it["id"])
            if it.get("control"):
                self.assertLess(it["year"], 1959, it["id"])
            else:
                self.assertTrue(1959 <= it["year"] <= 2026, it["id"])
        self.assertEqual(sum(1 for i in items if not i.get("control")), 47)
        self.assertEqual(sum(1 for i in items if i.get("control")), 4)


if __name__ == "__main__":
    unittest.main()
