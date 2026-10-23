"""Fake-data tests for host_guard.py and query_probe.py (no network). MV2 of Munim, Inc. Apache-2.0."""
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index  # noqa: E402
import host_guard  # noqa: E402
import query_probe  # noqa: E402
from test_build_index import corpus  # noqa: E402


def index(d):
    db = os.path.join(d, "idx", "spark.db")
    build_index.run(corpus(d), db, os.path.join(d, "build-out"))
    return db  # 2 files, 8 records (PMID 3 replaced once)


class GuardTest(unittest.TestCase):
    def test_missing_index_is_never_created(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "none.db")
            rec = host_guard.check(db, 1, 0)
            self.assertFalse(rec["ok"])
            self.assertIn("no index", rec["problem"])
            self.assertFalse(os.path.exists(db))

    def test_thresholds(self):
        with tempfile.TemporaryDirectory() as d:
            db = index(d)
            rec = host_guard.check(db, 2, 8)
            self.assertEqual((rec["ok"], rec["files_built"], rec["docs"], rec["last_file"], rec["problem"]),
                             (True, 2, 8, "pubmed27n0002.xml.gz", None))
            self.assertGreater(rec["db_bytes"], 0)
            rec = host_guard.check(db, 3, 0)
            self.assertFalse(rec["ok"])
            self.assertIn("below", rec["problem"])
            self.assertFalse(host_guard.check(db, 2, 9)["ok"])

    def test_not_an_index(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "other.db")
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE x (y)")
            con.commit()
            con.close()
            rec = host_guard.check(db, 1, 0)
            self.assertFalse(rec["ok"])
            self.assertIn("OperationalError", rec["problem"])

    def test_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            db, out = index(d), os.path.join(d, "out")
            self.assertEqual(host_guard.main(["--db", db, "--out-dir", out, "--min-built", "2"]), 0)
            self.assertEqual(host_guard.main(["--db", db, "--out-dir", out, "--min-built", "830",
                                              "--min-docs", "24899997"]), 3)
            with open(os.path.join(out, "guard.json"), encoding="utf-8") as f:
                g = json.load(f)
            self.assertEqual((g["ok"], g["files_built"], g["min_built"]), (False, 2, 830))


class ProbeTest(unittest.TestCase):
    def test_probe(self):
        with tempfile.TemporaryDirectory() as d:
            db = index(d)
            p = query_probe.probe(db, k=5, queries=("kinase w1a", "zebrafish newer"))
            self.assertEqual((p["files_built"], p["docs"], p["k"]), (2, 8, 5))
            for side in ("cold", "warm"):
                self.assertEqual((p[side]["queries"], p[side]["interrupted"], p[side]["results_min"]),
                                 (2, 0, 1))
                self.assertGreaterEqual(p[side]["ms_max"], p[side]["ms_median"])
            self.assertEqual(len(p["cold_ms"]), 2)

    def test_interrupted_query_is_counted(self):
        real = build_index.search

        def slow(con, text, k=5):
            raise sqlite3.OperationalError("interrupted")

        with tempfile.TemporaryDirectory() as d:
            db = index(d)
            build_index.search = slow
            try:
                p = query_probe.probe(db, k=5, queries=("kinase",))
            finally:
                build_index.search = real
            self.assertEqual((p["cold"]["interrupted"], p["cold"]["results_min"]), (1, None))

    def test_pct_and_query_set(self):
        self.assertEqual(query_probe.pct([5, 1, 3, 2, 4], 0.9), 5)
        self.assertIsNone(query_probe.pct([], 0.5))
        self.assertEqual(len(query_probe.QUERIES), 20)
        self.assertTrue(all(build_index.match_expr(q) for q in query_probe.QUERIES))

    def test_main_records_problem(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "out")
            self.assertEqual(query_probe.main(["--db", os.path.join(d, "none.db"), "--out-dir", out]), 1)
            with open(os.path.join(out, "probe.json"), encoding="utf-8") as f:
                self.assertIn("FileNotFoundError", json.load(f)["problem"])


if __name__ == "__main__":
    unittest.main()
