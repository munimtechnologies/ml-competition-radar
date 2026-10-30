import json
import os
import sqlite3
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compose_ro  # noqa: E402

CODE = os.environ.get("SPARK_CODE", "/tmp/code")  # where the job's fetch_code.py step puts it
HAVE_CODE = all(os.path.isfile(os.path.join(CODE, n)) for n in ("compose.py", "ro_db.py"))
DOCS = [(11, "Statins and stroke", "Statins reduce the risk of stroke in older adults. The effect was "
         "significant in women. Statins were well tolerated in this cohort."),
        (12, "A statin trial", "Statins did not reduce the risk of stroke in this trial. No significant "
         "difference in stroke was found between the groups."),
        (13, "Another topic", "Vitamin D levels were measured in children. Bone density was recorded at baseline.")]
QUESTION = "Do statins reduce the risk of stroke?"


def make_db(path, keep_open=False):
    """A tiny WAL-mode docs table like the index's; closed (no side files) unless keep_open."""
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=wal")
    con.execute("CREATE TABLE docs(title TEXT, abstract TEXT)")
    con.executemany("INSERT INTO docs(rowid, title, abstract) VALUES (?, ?, ?)", DOCS)
    con.commit()
    if keep_open:
        return con
    con.close()
    return None


@unittest.skipUnless(HAVE_CODE, "compose.py and ro_db.py not found in SPARK_CODE")
class ReadOnlyCompose(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.db = os.path.join(d, "index.db")
        make_db(self.db)
        self.ranked = os.path.join(d, "ranked.jsonl")
        with open(self.ranked, "w", encoding="utf-8") as f:
            f.write(json.dumps({"info_need_id": "1", "info_need": QUESTION,
                                "candidates": [["11", 9.0], ["12", 8.0], ["13", 1.0]]}) + "\n")
        self.out = os.path.join(d, "out")
        self.rc = compose_ro.main(["--code", CODE, "compose", "--db", self.db, "--ranked", self.ranked,
                                   "--out-dir", self.out, "--depth", "20"])

    def tearDown(self):
        self.tmp.cleanup()

    def answers(self):
        with open(os.path.join(self.out, "answers.jsonl"), encoding="utf-8") as f:
            return [json.loads(x) for x in f if x.strip()]

    def test_same_answers_as_compose(self):
        self.assertEqual(self.rc, 0)
        compose = compose_ro.load(CODE)
        want = compose.compose(QUESTION, [(str(p), t, a) for p, t, a in DOCS])
        rows = self.answers()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["docs_with_abstract"], 3)
        self.assertGreater(len(rows[0]["responses"]), 0)
        for k in ("responses", "conflicts", "uncertain", "words"):
            self.assertEqual(rows[0][k], want[k])

    def test_no_side_files_and_no_writes(self):
        self.assertEqual(self.rc, 0)
        self.assertFalse(os.path.exists(self.db + "-wal"))
        self.assertFalse(os.path.exists(self.db + "-shm"))
        compose = compose_ro.load(CODE)
        self.assertIsInstance(compose.sqlite3, compose_ro.ReadOnly)
        con = compose.sqlite3.connect(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM docs").fetchone()[0], 3)
            with self.assertRaises(sqlite3.OperationalError):
                con.execute("INSERT INTO docs(title, abstract) VALUES ('x', 'y')")
        finally:
            con.close()
        self.assertFalse(os.path.exists(self.db + "-wal"))

    def test_refuses_unsaved_wal(self):
        db2 = os.path.join(self.tmp.name, "busy.db")
        con = make_db(db2, keep_open=True)
        try:
            self.assertGreater(os.path.getsize(db2 + "-wal"), 0)
            with self.assertRaises(ValueError):
                compose_ro.main(["--code", CODE, "compose", "--db", db2, "--ranked", self.ranked,
                                 "--out-dir", os.path.join(self.tmp.name, "out2")])
        finally:
            con.close()

    def test_score_passes_through(self):
        gold = os.path.join(self.tmp.name, "gold.jsonl")
        with open(gold, "w", encoding="utf-8") as f:
            f.write(json.dumps({"topic": "1", "supports": ["11"], "contradicts": ["12"],
                                "neutral": [], "notrelevant": ["13"]}) + "\n")
        sdir = os.path.join(self.tmp.name, "score")
        rc = compose_ro.main(["--code", CODE, "score", "--answers", os.path.join(self.out, "answers.jsonl"),
                              "--gold", gold, "--out-dir", sdir])
        self.assertEqual(rc, 0)
        with open(os.path.join(sdir, "scores.json"), encoding="utf-8") as f:
            s = json.load(f)
        self.assertEqual(s["answers_scored"], 1)
        shares = sum(s["mean_%s_share" % k] for k in ("supports", "mixed", "contradicts", "other", "unjudged"))
        self.assertAlmostEqual(shares, 1.0, places=3)
        self.assertEqual(s["mean_unjudged_share"], 0.0)


class Usage(unittest.TestCase):
    def test_usage(self):
        self.assertEqual(compose_ro.main([]), 2)
        self.assertEqual(compose_ro.main(["compose", "--db", "x"]), 2)
        self.assertEqual(compose_ro.VERSION, "0.1.0")


if __name__ == "__main__":
    unittest.main()
