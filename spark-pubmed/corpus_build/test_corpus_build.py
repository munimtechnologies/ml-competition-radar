"""Fake-data tests for fetch_corpus.py v0.2.2 and full_count.py v0.2 (no network).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
"""
import gzip
import hashlib
import io
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_corpus  # noqa: E402
import full_count  # noqa: E402


def art(pmid, title, abstract, year=1990, pmc=False):
    return ("<PubmedArticle><MedlineCitation><PMID Version=\"1\">%d</PMID><Article><Journal>"
            "<JournalIssue><PubDate><Year>%d</Year></PubDate></JournalIssue><ISOAbbreviation>J Fake"
            "</ISOAbbreviation></Journal><ArticleTitle>%s</ArticleTitle><Abstract>"
            "<AbstractText Label=\"BACKGROUND\">%s</AbstractText></Abstract></Article>"
            "<MeshHeadingList><MeshHeading><DescriptorName>Humans</DescriptorName></MeshHeading>"
            "</MeshHeadingList></MedlineCitation><PubmedData><ArticleIdList>"
            "<ArticleId IdType=\"pubmed\">%d</ArticleId>%s</ArticleIdList></PubmedData></PubmedArticle>"
            % (pmid, year, title, abstract, pmid, "<ArticleId IdType=\"pmc\">PMC%d</ArticleId>" % pmid if pmc else ""))


def fake_file(first, count):
    body = "".join(art(p, "Kinase w%da w%db in cells" % (p, p),
                       "We studied w%dc w%dd in patients. Results were mixed for kinase." % (p, p), pmc=p % 2 == 0)
                   for p in range(first, first + count))
    return gzip.compress(("<PubmedArticleSet>" + body + "</PubmedArticleSet>").encode("utf-8"))


def site(files, bad_md5=()):
    pages, links = {}, []
    for name, data in files.items():
        md5 = "0" * 32 if name in bad_md5 else hashlib.md5(data).hexdigest()
        pages[fetch_corpus.BASE + name] = data
        pages[fetch_corpus.BASE + name + ".md5"] = ("MD5(%s)= %s\n" % (name, md5)).encode()
        links.append('<a href="%s">%s</a> <a href="%s.md5">%s.md5</a>' % (name, name, name, name))
    pages[fetch_corpus.BASE] = ("<html>" + "\n".join(links) + "</html>").encode()
    return pages


def opener_for(pages, calls=None):
    def opener(url, timeout=120):
        if calls is not None:
            calls.append(url)
        if url not in pages:
            raise OSError("no such url")
        return io.BytesIO(pages[url])
    return opener


class Trickle(object):
    """A response that sends one byte every 20 ms and never ends (the run-1 stall)."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read1(self, n):
        time.sleep(0.02)
        return b"x"


class ReadOnly(object):
    """A response with read() but no read1()."""

    def __init__(self, data):
        self.buf = io.BytesIO(data)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, n=-1):
        return self.buf.read(n)


class FetchTest(unittest.TestCase):
    def test_fetch_resume_and_md5(self):
        files = {"pubmed27n0001.xml.gz": fake_file(1, 3), "pubmed27n0002.xml.gz": fake_file(10, 2)}
        with tempfile.TemporaryDirectory() as d:
            raw, out = os.path.join(d, "raw"), os.path.join(d, "out")
            s = fetch_corpus.run(raw, out, 2, 0, opener_for(site(files, bad_md5={"pubmed27n0002.xml.gz"})))
            self.assertEqual(s["listing_files"], 2)
            self.assertEqual(s["files_ok"], 1)
            self.assertEqual(s["files_failed"], ["pubmed27n0002.xml.gz"])
            self.assertFalse(os.path.exists(os.path.join(raw, "pubmed27n0002.xml.gz")))
            with open(os.path.join(raw, "pubmed27n0001.xml.gz.md5ok"), encoding="ascii") as f:
                self.assertEqual(f.read(), hashlib.md5(files["pubmed27n0001.xml.gz"]).hexdigest())
            calls = []
            s2 = fetch_corpus.run(raw, out, 1, 0, opener_for(site(files), calls))
            self.assertIsNone(s2["problem"])
            self.assertEqual((s2["files_ok"], s2["files_resumed"], s2["files_rehashed"]), (2, 1, 0))
            self.assertEqual([c for c in calls if c.endswith(".xml.gz")],
                             [fetch_corpus.BASE + "pubmed27n0002.xml.gz"])
            self.assertEqual(s2["bytes_total"], sum(len(v) for v in files.values()))

    def test_rehash_repairs_truncated_file(self):
        name1, name2 = "pubmed27n0001.xml.gz", "pubmed27n0002.xml.gz"
        files = {name1: fake_file(1, 3), name2: fake_file(10, 40)}
        full = sum(len(v) for v in files.values())
        with tempfile.TemporaryDirectory() as d:
            raw, out = os.path.join(d, "raw"), os.path.join(d, "out")
            s = fetch_corpus.run(raw, out, 2, 0, opener_for(site(files)))
            self.assertIsNone(s["problem"])
            self.assertEqual((s["files_ok"], s["stale_markers"]), (2, []))
            p2 = os.path.join(raw, name2)
            with open(p2, "r+b") as f:  # what spark27-fts-v3 found: marker kept, data cut short
                f.truncate(len(files[name2]) // 2)
            s1 = fetch_corpus.run(raw, out, 1, 0, opener_for(site(files)))  # v0.2.1 behaviour: marker trusted
            self.assertEqual((s1["files_ok"], s1["files_resumed"], s1["stale_markers"]), (2, 2, []))
            self.assertLess(s1["bytes_total"], full)
            calls = []
            s2 = fetch_corpus.run(raw, out, 1, 0, opener_for(site(files), calls), rehash=True)
            self.assertIsNone(s2["problem"])
            self.assertTrue(s2["rehash"])
            self.assertEqual(s2["stale_markers"], [name2])
            self.assertEqual((s2["files_ok"], s2["files_resumed"], s2["files_rehashed"]), (2, 1, 1))
            self.assertEqual([c for c in calls if c.endswith(".xml.gz")], [fetch_corpus.BASE + name2])
            self.assertEqual(s2["bytes_total"], full)
            with open(p2, "rb") as f:
                self.assertEqual(f.read(), files[name2])
            with open(os.path.join(out, "fetch_files.jsonl"), encoding="utf-8") as f:
                rows = {r["file"]: r for r in (json.loads(line) for line in f)}
            self.assertIn("downloaded again", rows[name2]["stale"])
            self.assertIsNone(rows[name2]["problem"])
            self.assertTrue(rows[name1]["rehashed"])
            s3 = fetch_corpus.run(raw, out, 1, 0, opener_for(site(files)), rehash=True)
            self.assertEqual((s3["files_rehashed"], s3["stale_markers"]), (2, []))

    def test_md5_of(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.bin")
            data = b"abc" * 500000
            with open(p, "wb") as f:
                f.write(data)
            self.assertEqual(fetch_corpus.md5_of(p), hashlib.md5(data).hexdigest())
            fetch_corpus.fsync_dir(d)  # must not raise
            fetch_corpus.fsync_dir(os.path.join(d, "missing"))

    def test_response_without_read1(self):
        name = "pubmed27n0001.xml.gz"
        data = fake_file(1, 2)
        pages = site({name: data})

        def opener(url, timeout=120):
            return ReadOnly(pages[url]) if url == fetch_corpus.BASE + name else io.BytesIO(pages[url])
        with tempfile.TemporaryDirectory() as d:
            info = fetch_corpus.get(name, d, opener, tries=1)
            self.assertIsNone(info["problem"])
            self.assertEqual(info["bytes"], len(data))
            self.assertTrue(os.path.exists(os.path.join(d, name + ".md5ok")))

    def test_trickling_download_times_out(self):
        name = "pubmed27n0001.xml.gz"
        pages = site({name: fake_file(1, 1)})

        def opener(url, timeout=120):
            return Trickle() if url == fetch_corpus.BASE + name else io.BytesIO(pages[url])
        with tempfile.TemporaryDirectory() as d:
            t0 = time.time()
            info = fetch_corpus.get(name, d, opener, tries=1, file_seconds=0.3)
            self.assertLess(time.time() - t0, 5)
            self.assertIn("TimeoutError", info["problem"])
            self.assertFalse(os.path.exists(os.path.join(d, name + ".md5ok")))

    def test_disk_floor_and_exit_code(self):
        name = "pubmed27n0001.xml.gz"
        calls = []
        with tempfile.TemporaryDirectory() as d:
            info = fetch_corpus.get(name, d, opener_for(site({name: fake_file(1, 1)}), calls),
                                    tries=1, min_free_bytes=1e18)
            self.assertTrue(info["problem"].startswith("disk floor"))
            self.assertEqual(calls, [])
        self.assertEqual(fetch_corpus.exit_code({"problem": None}, 0), 0)
        self.assertEqual(fetch_corpus.exit_code(
            {"problem": "x", "files_failed": ["a"], "files_ok": 3}, 0), 1)
        self.assertEqual(fetch_corpus.exit_code(
            {"problem": "x", "files_failed": ["a"], "files_ok": 3}, 1), 0)


def art2(pmid, pubdate, ptype="D016428", elec="", pubmed=""):
    return ("<PubmedArticle><MedlineCitation><PMID Version=\"1\">%d</PMID><Article><Journal><JournalIssue>"
            "<PubDate>%s</PubDate></JournalIssue></Journal><ArticleTitle>T</ArticleTitle>%s"
            "<PublicationTypeList><PublicationType UI=\"%s\">X</PublicationType></PublicationTypeList>"
            "</Article></MedlineCitation><PubmedData><History>%s</History><ArticleIdList>"
            "<ArticleId IdType=\"pubmed\">%d</ArticleId></ArticleIdList></PubmedData></PubmedArticle>"
            % (pmid, pubdate, elec, ptype, pubmed, pmid))


ELEC_JUNE = "<ArticleDate DateType=\"Electronic\"><Year>2026</Year><Month>06</Month><Day>10</Day></ArticleDate>"
PUBMED_AUG = "<PubMedPubDate PubStatus=\"pubmed\"><Year>2026</Year><Month>8</Month><Day>2</Day></PubMedPubDate>"
COUNT_A = ("<PubmedArticleSet>" + art2(1, "<Year>1975</Year>")
           + art2(2, "<Year>2026</Year><Month>Sep</Month>", "D016421", ELEC_JUNE)
           + art2(3, "<Year>1950</Year>", "D016456") + "</PubmedArticleSet>")
COUNT_B = ("<PubmedArticleSet>" + art2(3, "<MedlineDate>1975 Jan-Feb</MedlineDate>")
           + art2(5, "<Year>2026</Year><Month>Aug</Month>", "D000076942", pubmed=PUBMED_AUG)
           + "<DeleteCitation><PMID Version=\"1\">9</PMID></DeleteCitation></PubmedArticleSet>")


class FullCountTest(unittest.TestCase):
    def put(self, raw, name, data):
        with open(os.path.join(raw, name), "wb") as f:
            f.write(data)
        with open(os.path.join(raw, name + ".md5ok"), "w", encoding="ascii") as f:
            f.write("x")

    def test_truncated_file_fails_then_resumes_with_duplicate_examples(self):
        a, b = gzip.compress(COUNT_A.encode("utf-8")), gzip.compress(COUNT_B.encode("utf-8"))
        with tempfile.TemporaryDirectory() as d:
            raw, state = os.path.join(d, "raw"), os.path.join(d, "state")
            os.makedirs(raw)
            self.put(raw, "pubmed27n0001.xml.gz", a)
            self.put(raw, "pubmed27n0002.xml.gz", b[:len(b) // 2])
            s1 = full_count.run(raw, state, os.path.join(d, "out1"), 1)
            self.assertEqual(s1["files_failed"], ["pubmed27n0002.xml.gz"])
            self.assertIn("1 file(s) failed", s1["problem"])
            self.assertEqual((s1["totals"]["records"], s1["duplicate_pmids"], s1["duplicate_examples"]), (3, 0, []))
            self.assertFalse(os.path.exists(os.path.join(state, "pubmed27n0002.xml.gz.json")))
            with open(os.path.join(d, "out1", "full_files.jsonl"), encoding="utf-8") as f:
                rows = [json.loads(line) for line in f]
            self.assertTrue(rows[1]["problem"].startswith("EOFError"))
            self.put(raw, "pubmed27n0002.xml.gz", b)  # the repaired file
            for attempt in (2, 3):  # the third run must give the same answer from checkpoints only
                s = full_count.run(raw, state, os.path.join(d, "out%d" % attempt), 1)
                self.assertIsNone(s["problem"])
                self.assertEqual((s["verified_files"], s["files_ok"]), (2, 2))
                t = s["totals"]
                self.assertEqual(t["records"], 5)
                self.assertEqual(t["journal_before_1959"], 1)
                self.assertEqual(t["journal_after_2026_07"], 2)
                self.assertEqual(t["no_date_on_or_before_end"], 1)
                self.assertEqual(t["pubmed_after_2026_07"], 1)
                self.assertEqual(t["deleted_pmids"], 1)
                self.assertEqual(s["duplicate_pmids"], 1)
                self.assertEqual(s["duplicate_examples"],
                                 [{"pmid": 3, "files": ["pubmed27n0001.xml.gz", "pubmed27n0002.xml.gz"]}])
                self.assertEqual((s["pmid_min"], s["pmid_max"]), (1, 5))
                self.assertEqual(s["records_per_file"], {"2": 1, "3": 1})
                w = s["watched_types"]
                self.assertEqual((w["D016421"]["records"], w["D016421"]["examples"]), (1, [2]))
                self.assertEqual((w["D016456"]["records"], w["D016456"]["examples"]), (1, [3]))
                self.assertEqual((w["D000076942"]["records"], w["D000076942"]["examples"]), (1, [5]))
                with open(os.path.join(d, "out%d" % attempt, "full_count.json"), encoding="utf-8") as f:
                    self.assertEqual(json.load(f)["duplicate_examples"][0]["pmid"], 3)

    def test_v01_checkpoint_still_read(self):
        """A checkpoint written by v0.1 (same fields, no duplicate list) is reused as it is."""
        with tempfile.TemporaryDirectory() as d:
            raw, state = os.path.join(d, "raw"), os.path.join(d, "state")
            os.makedirs(raw)
            self.put(raw, "pubmed27n0001.xml.gz", gzip.compress(COUNT_A.encode("utf-8")))
            s = full_count.run(raw, state, os.path.join(d, "out"), 1)
            self.assertIsNone(s["problem"])
            os.remove(os.path.join(raw, "pubmed27n0001.xml.gz"))  # only the checkpoint is left
            with open(os.path.join(raw, "pubmed27n0001.xml.gz"), "wb") as f:
                f.write(b"not gzip")
            s2 = full_count.run(raw, state, os.path.join(d, "out2"), 1)
            self.assertIsNone(s2["problem"])
            self.assertEqual(s2["totals"]["records"], 3)


if __name__ == "__main__":
    unittest.main()
