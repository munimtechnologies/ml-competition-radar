"""Fake-data tests for fetch_corpus.py and fts_pilot.py (no network). MV2 of Munim, Inc. Apache-2.0."""
import gzip
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_corpus  # noqa: E402
import fts_pilot  # noqa: E402
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
    """count articles with PMIDs first.. ; every title/abstract has words unique to its paper."""
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


class Blocked(object):
    """A response whose first read waits until the test releases it."""

    def __init__(self, release):
        self.release = release

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read1(self, n):
        self.release.wait(10)
        return b""


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
            self.assertIn("1 file(s) failed", s["problem"])
            self.assertFalse(os.path.exists(os.path.join(raw, "pubmed27n0002.xml.gz.part")))
            self.assertFalse(os.path.exists(os.path.join(raw, "pubmed27n0002.xml.gz")))
            self.assertTrue(os.path.exists(os.path.join(raw, "pubmed27n0001.xml.gz.md5ok")))

            calls = []
            s2 = fetch_corpus.run(raw, out, 1, 0, opener_for(site(files), calls))
            self.assertIsNone(s2["problem"])
            self.assertEqual((s2["files_ok"], s2["files_resumed"]), (2, 1))
            self.assertEqual([c for c in calls if c.endswith(".xml.gz")],
                             [fetch_corpus.BASE + "pubmed27n0002.xml.gz"])
            self.assertEqual(s2["bytes_total"], sum(len(v) for v in files.values()))
            with open(os.path.join(out, "fetch.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["files_ok"], 2)

    def test_disk_guard(self):
        with tempfile.TemporaryDirectory() as d:
            s = fetch_corpus.run(os.path.join(d, "raw"), os.path.join(d, "out"), 1, 1e12,
                                 opener_for({}))
            self.assertIn("not enough free disk", s["problem"])

    def test_disk_floor_skips_download(self):
        name = "pubmed27n0001.xml.gz"
        calls = []
        with tempfile.TemporaryDirectory() as d:
            info = fetch_corpus.get(name, d, opener_for(site({name: fake_file(1, 1)}), calls),
                                    tries=1, min_free_bytes=1e18)
            self.assertTrue(info["problem"].startswith("disk floor"))
            self.assertEqual(calls, [])
            self.assertFalse(os.path.exists(os.path.join(d, name + ".md5ok")))

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

    def test_max_minutes_records_unfinished_file(self):
        files = {"pubmed27n0001.xml.gz": fake_file(1, 2), "pubmed27n0002.xml.gz": fake_file(5, 2)}
        pages, release = site(files), threading.Event()

        def opener(url, timeout=120):
            if url == fetch_corpus.BASE + "pubmed27n0002.xml.gz":
                return Blocked(release)
            return io.BytesIO(pages[url])
        with tempfile.TemporaryDirectory() as d:
            t0 = time.time()
            s = fetch_corpus.run(os.path.join(d, "raw"), os.path.join(d, "out"), 2, 0, opener,
                                 max_minutes=0.01, file_minutes=10)
            self.assertLess(time.time() - t0, 5)
            self.assertEqual(s["unfinished"], 1)
            self.assertEqual(s["files_ok"], 1)
            self.assertEqual(s["files_failed"], ["pubmed27n0002.xml.gz"])
            with open(os.path.join(d, "out", "fetch_files.jsonl"), encoding="utf-8") as f:
                rows = [json.loads(line) for line in f]
            self.assertEqual(len(rows), 2)
            self.assertIn("not finished", rows[1]["problem"])
            self.assertEqual(fetch_corpus.exit_code(s, 0), 1)
            self.assertEqual(fetch_corpus.exit_code(s, 1), 0)
            release.set()
            time.sleep(0.3)

    def test_exit_code(self):
        self.assertEqual(fetch_corpus.exit_code({"problem": None}, 0), 0)
        self.assertEqual(fetch_corpus.exit_code({"problem": "not enough free disk"}, 5), 1)
        self.assertEqual(fetch_corpus.exit_code(
            {"problem": "x", "files_failed": ["a", "b"], "files_ok": 3}, 1), 1)
        self.assertEqual(fetch_corpus.exit_code(
            {"problem": "x", "files_failed": ["a", "b"], "files_ok": 0}, 5), 1)


class PilotTest(unittest.TestCase):
    def test_parse_and_query_helpers(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.xml.gz")
            with open(p, "wb") as f:
                f.write(fake_file(4, 1))
            rec = list(fts_pilot.parse_file(p))[0]
        self.assertEqual(rec["pmid"], 4)
        self.assertEqual(rec["title"], "Kinase w4a w4b in cells")
        self.assertTrue(rec["abstract"].startswith("BACKGROUND: We studied w4c"))
        self.assertEqual((rec["mesh"], rec["year"], rec["pmcid"]), ("Humans", 1990, "PMC4"))
        self.assertEqual(fts_pilot.match_expr("The KINASE of kinase, and NOT x"), '"kinase"')
        self.assertEqual(fts_pilot.match_expr("Gene editing in CRISPR"), '"gene" OR "editing" OR "crispr"')
        self.assertEqual(fts_pilot.match_expr("a an the"), "")
        self.assertEqual(fts_pilot.first_sentence("BACKGROUND: We studied w4c w4d in patients. More."),
                         "BACKGROUND: We studied w4c w4d in patients.")
        self.assertEqual(fts_pilot.first_sentence("Too short. " + "x " * 30).split()[:3], ["Too", "short.", "x"])

    def test_run_pilot_and_compare(self):
        with tempfile.TemporaryDirectory() as d:
            raw = os.path.join(d, "raw")
            os.makedirs(raw)
            for i, first in enumerate((1, 101, 201, 301), 1):
                name = "pubmed27n%04d.xml.gz" % i
                with open(os.path.join(raw, name), "wb") as f:
                    f.write(fake_file(first, 20))
                if i != 4:  # file 4 has no .md5ok marker, so it is not verified and is ignored
                    with open(os.path.join(raw, name + ".md5ok"), "w", encoding="ascii") as f:
                        f.write("x")
            s = fts_pilot.run(raw, os.path.join(d, "db"), os.path.join(d, "out"), 1, 10, 7)
            self.assertIsNone(s["problem"])
            self.assertEqual(s["verified_files"], 3)
            p = s["pilot"]
            self.assertEqual((p["docs"], p["duplicate_pmids"], p["files"]), (60, 0, 3))
            self.assertGreater(p["bytes_per_doc"], 0)
            self.assertGreater(p["index_bytes"], 0)
            self.assertGreater(p["text_bytes"], 0)
            self.assertIn("extrapolated_gb_full_corpus", p)
            self.assertEqual(p["queries"]["title"]["n"], 10)
            self.assertEqual(p["queries"]["title"]["mrr_at_5"], 1.0)
            self.assertEqual(p["queries"]["first_sentence"]["mrr_at_5"], 1.0)
            self.assertEqual(s["compare_files"], ["pubmed27n0001.xml.gz", "pubmed27n0002.xml.gz",
                                                  "pubmed27n0003.xml.gz"])
            self.assertEqual([c["detail"] for c in s["compare"]], ["full", "column", "none"])
            full = s["compare"][0]
            self.assertEqual(full["docs"], 60)
            self.assertEqual(full["queries"]["title"]["mrr_at_5"], 1.0)
            for c in s["compare"][1:]:
                self.assertNotIn("error", c)
                self.assertEqual(c["docs"], 60)
            self.assertTrue(os.path.exists(os.path.join(d, "db", "pilot_full.db")))
            self.assertFalse(os.path.exists(os.path.join(d, "db", "compare_none.db")))
            with open(os.path.join(d, "out", "pilot.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["pilot"]["docs"], 60)

    def test_duplicate_pmid_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.xml.gz")
            with open(p, "wb") as f:
                f.write(fake_file(1, 2))
            con = fts_pilot.open_db(os.path.join(d, "t.db"), "full")
            self.assertEqual(fts_pilot.add_file(con, p), (2, 0))
            self.assertEqual(fts_pilot.add_file(con, p), (0, 2))
            self.assertEqual(fts_pilot.search(con, "w2a w2b"), [2])
            con.close()

    def test_fts5_available(self):
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        con.close()


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
    def test_count_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            raw = os.path.join(d, "raw")
            os.makedirs(raw)
            for name, body, verified in (("pubmed27n0001.xml.gz", COUNT_A, True),
                                         ("pubmed27n0002.xml.gz", COUNT_B, True),
                                         ("pubmed27n0003.xml.gz", COUNT_A, False)):
                with open(os.path.join(raw, name), "wb") as f:
                    f.write(gzip.compress(body.encode("utf-8")))
                if verified:
                    with open(os.path.join(raw, name + ".md5ok"), "w", encoding="ascii") as f:
                        f.write("x")
            for attempt in (1, 2):  # the second run must give the same answer from checkpoints
                s = full_count.run(raw, os.path.join(d, "state"), os.path.join(d, "out%d" % attempt), 1)
                self.assertIsNone(s["problem"])
                self.assertEqual((s["verified_files"], s["files_ok"]), (2, 2))
                t = s["totals"]
                self.assertEqual(t["records"], 5)
                self.assertEqual(t["journal_before_1959"], 1)
                self.assertEqual(t["journal_after_2026_07"], 2)
                self.assertEqual(t["no_date_on_or_before_end"], 1)  # PMID 5; PMID 2 has a June e-date
                self.assertEqual(t["electronic_after_2026_07"], 0)
                self.assertEqual(t["pubmed_after_2026_07"], 1)
                self.assertEqual(t["deleted_pmids"], 1)
                self.assertEqual(s["duplicate_pmids"], 1)
                self.assertEqual((s["pmid_min"], s["pmid_max"]), (1, 5))
                self.assertEqual(s["records_per_file"], {"2": 1, "3": 1})
                w = s["watched_types"]
                self.assertEqual((w["D016421"]["records"], w["D016421"]["examples"]), (1, [2]))
                self.assertEqual((w["D016456"]["records"], w["D016456"]["examples"]), (1, [3]))
                self.assertEqual((w["D000076942"]["records"], w["D000076942"]["examples"]), (1, [5]))
                self.assertEqual(s["publication_types"]["D016428"], {"name": "X", "records": 2})
                with open(os.path.join(d, "out%d" % attempt, "full_files.jsonl"), encoding="utf-8") as f:
                    self.assertEqual(len(f.read().splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
