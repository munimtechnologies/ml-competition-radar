"""Fake-data tests for build_index.py (no network). MV2 of Munim, Inc. Apache-2.0."""
import gzip
import itertools
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index  # noqa: E402


def art(pmid, title, abstract, year=1990, pmc=False):
    return ("<PubmedArticle><MedlineCitation><PMID Version=\"1\">%d</PMID><Article><Journal>"
            "<JournalIssue><PubDate><Year>%d</Year></PubDate></JournalIssue><ISOAbbreviation>J Fake"
            "</ISOAbbreviation></Journal><ArticleTitle>%s</ArticleTitle><Abstract>"
            "<AbstractText Label=\"BACKGROUND\">%s</AbstractText></Abstract></Article>"
            "<MeshHeadingList><MeshHeading><DescriptorName>Humans</DescriptorName></MeshHeading>"
            "</MeshHeadingList></MedlineCitation><PubmedData><ArticleIdList>"
            "<ArticleId IdType=\"pubmed\">%d</ArticleId>%s</ArticleIdList></PubmedData></PubmedArticle>"
            % (pmid, year, title, abstract, pmid, "<ArticleId IdType=\"pmc\">PMC%d</ArticleId>" % pmid if pmc else ""))


def body(pmids, tag="old"):
    return "".join(art(p, "Kinase w%da w%db %s" % (p, p, tag), "We studied w%dc in patients." % p, pmc=p % 2 == 0)
                   for p in pmids)


def put(raw, name, xml, verified=True):
    with open(os.path.join(raw, name), "wb") as f:
        f.write(gzip.compress(xml.encode("utf-8")))
    if verified:
        with open(os.path.join(raw, name + ".md5ok"), "w", encoding="ascii") as f:
            f.write("x")


def corpus(d):
    """Files 1 and 2 verified (file 2 repeats PMID 3 with a new title); file 3 not verified."""
    raw = os.path.join(d, "raw")
    os.makedirs(raw)
    put(raw, "pubmed27n0001.xml.gz", "<PubmedArticleSet>" + body(range(1, 6)) + "</PubmedArticleSet>")
    put(raw, "pubmed27n0002.xml.gz", "<PubmedArticleSet>" + body(range(6, 9))
        + body([3], tag="newer zebrafish") + "</PubmedArticleSet>")
    put(raw, "pubmed27n0003.xml.gz", "<PubmedArticleSet>" + body(range(20, 23)) + "</PubmedArticleSet>",
        verified=False)
    return raw


def progress(out):
    with open(os.path.join(out, "progress.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class BuildTest(unittest.TestCase):
    def test_parse(self):
        with tempfile.TemporaryDirectory() as d:
            raw = corpus(d)
            recs = list(build_index.parse_file(os.path.join(raw, "pubmed27n0001.xml.gz")))
        self.assertEqual(len(recs), 5)
        self.assertEqual(recs[1], (2, "Kinase w2a w2b old", "BACKGROUND: We studied w2c in patients.",
                                   "Humans", 1990, "J Fake", "PMC2"))
        self.assertIsNone(recs[0][6])
        self.assertEqual(build_index.match_expr("The KINASE of kinase, and NOT x"), '"kinase"')

    def test_staged_build_resume_and_replace(self):
        with tempfile.TemporaryDirectory() as d:
            raw, db, out = corpus(d), os.path.join(d, "idx", "spark.db"), os.path.join(d, "out")
            s1 = build_index.run(raw, db, out, max_files=1)
            self.assertEqual((s1["verified_files"], s1["files_built"], s1["files_left"]), (2, 1, 1))
            self.assertEqual((s1["docs"], s1["stopped"], s1["complete"]), (5, "max_files", False))
            s2 = build_index.run(raw, db, out, optimize=True)
            self.assertEqual((s2["files_built"], s2["files_added_this_run"], s2["files_left"]), (2, 1, 0))
            self.assertEqual((s2["docs"], s2["replaced_total"], s2["complete"]), (8, 1, True))
            self.assertIsNone(s2["stopped"])
            self.assertIsNotNone(s2["optimize_seconds"])
            self.assertGreater(s2["bytes_per_doc"], 0)
            s3 = build_index.run(raw, db, out)  # nothing left: no file is indexed twice
            self.assertEqual((s3["files_added_this_run"], s3["docs"]), (0, 8))
            con = sqlite3.connect(db)
            self.assertEqual(build_index.search(con, "zebrafish newer kinase")[0], 3)
            self.assertEqual(con.execute("SELECT file FROM meta WHERE pmid=3").fetchone()[0],
                             "pubmed27n0002.xml.gz")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM docs WHERE docs MATCH 'old'").fetchone()[0], 7)
            self.assertEqual(build_index.search(con, "w7a w7b"), [7])
            self.assertEqual(build_index.search(con, "the of and"), [])
            con.close()

    def test_failed_file_rolls_back(self):
        with tempfile.TemporaryDirectory() as d:
            raw, db = corpus(d), os.path.join(d, "spark.db")
            put(raw, "pubmed27n0002.xml.gz", "<PubmedArticleSet>" + body([6]) + "<PubmedArticle><Medline")
            con = build_index.open_db(db, "full")
            self.assertEqual(build_index.add_file(con, os.path.join(raw, "pubmed27n0001.xml.gz"),
                                                  "pubmed27n0001.xml.gz"), (5, 0))
            with self.assertRaises(ET.ParseError):
                build_index.add_file(con, os.path.join(raw, "pubmed27n0002.xml.gz"), "pubmed27n0002.xml.gz")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM meta").fetchone()[0], 5)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM built").fetchone()[0], 1)
            self.assertEqual(build_index.search(con, "w6a w6b"), [])
            con.close()

    def test_guards(self):
        with tempfile.TemporaryDirectory() as d:
            raw, db, out = corpus(d), os.path.join(d, "spark.db"), os.path.join(d, "out")
            clock = itertools.chain([0.0], itertools.repeat(100.0)).__next__
            s = build_index.run(raw, db, out, max_minutes=1, clock=clock)
            self.assertEqual((s["stopped"], s["files_added_this_run"], s["docs"]), ("time budget", 0, 0))
            s = build_index.run(raw, db, out, min_free_gb=1e9)
            self.assertTrue(s["stopped"].startswith("free disk under"))
            with self.assertRaises(ValueError):
                build_index.run(raw, db, out, detail="column")
            empty = os.path.join(d, "empty")
            os.makedirs(empty)
            s = build_index.run(empty, os.path.join(d, "e.db"), out)
            self.assertIn("no verified corpus files", s["problem"])
            self.assertFalse(s["complete"])

    def test_column_detail(self):
        with tempfile.TemporaryDirectory() as d:
            raw, db = corpus(d), os.path.join(d, "col.db")
            s = build_index.run(raw, db, os.path.join(d, "out"), detail="column")
            self.assertEqual((s["detail"], s["docs"]), ("column", 8))
            con = sqlite3.connect(db)  # bm25 at detail=column is the pilot's Q6; here only matching
            self.assertEqual(con.execute("SELECT rowid FROM docs WHERE docs MATCH 'w5a'").fetchall(), [(5,)])
            con.close()

    def test_signal_rolls_back_and_records(self):
        """A SIGTERM in the middle of file 2 keeps file 1, drops file 2's rows, records both."""
        real = build_index.parse_file

        def interrupted(path):
            for i, rec in enumerate(real(path)):
                if path.endswith("pubmed27n0002.xml.gz") and i == 2:
                    raise build_index.Stopped("signal 15")
                yield rec

        with tempfile.TemporaryDirectory() as d:
            raw, db, out = corpus(d), os.path.join(d, "spark.db"), os.path.join(d, "out")
            build_index.parse_file = interrupted
            try:
                s = build_index.run(raw, db, out)
            finally:
                build_index.parse_file = real
            self.assertEqual((s["stopped"], s["files_built"], s["files_added_this_run"], s["files_left"]),
                             ("signal 15", 1, 1, 1))
            self.assertEqual((s["docs"], s["docs_check"], s["last_file"], s["complete"]),
                             (5, None, "pubmed27n0001.xml.gz", False))
            with open(os.path.join(out, "build.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["stopped"], "signal 15")
            rows = progress(out)
            self.assertEqual([(r["file"], r["docs"], r["replaced"]) for r in rows],
                             [("pubmed27n0001.xml.gz", 5, 0)])
            con = sqlite3.connect(db)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM meta").fetchone()[0], 5)
            self.assertEqual(build_index.search(con, "w6a w6b"), [])
            con.close()
            s2 = build_index.run(raw, db, out)  # the rerun picks up file 2 whole
            self.assertEqual((s2["stopped"], s2["files_added_this_run"], s2["docs"], s2["docs_check"]),
                             (None, 1, 8, 8))
            self.assertEqual((s2["replaced_total"], s2["complete"], s2["wal_bytes"]), (1, True, 0))
            self.assertEqual([r["file"] for r in progress(out)],
                             ["pubmed27n0001.xml.gz", "pubmed27n0002.xml.gz"])

    def test_on_signal(self):
        with self.assertRaises(build_index.Stopped) as cm:
            build_index.on_signal(15, None)
        self.assertEqual(str(cm.exception), "signal 15")


if __name__ == "__main__":
    unittest.main()
