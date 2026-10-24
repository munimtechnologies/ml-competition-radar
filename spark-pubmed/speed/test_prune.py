import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prune  # noqa: E402

# Record counts (porter stems): cell 4, growth 3, liver 1, heart 1, zebrafish 1, kidney 1.
DOCS = [(1, "cell heart", "zebrafish heart regeneration", ""),
        (2, "cell biology", "cell growth", ""),
        (3, "cell liver", "liver cell growth", ""),
        (4, "cell signalling", "cell", ""),
        (5, "kidney", "kidney growth", "")]
NEEDS = [{"info_need_id": "a", "info_need": "Zebrafish heart cell growth",
          "candidates": [[1, 5.0], [2, 1.0]], "ms": 1000.0},
         {"info_need_id": "b", "info_need": "cell growth in the liver", "candidates": [[3, 2.0]], "ms": 500.0},
         {"info_need_id": "c", "info_need": "kidney or zebrafish", "candidates": [], "ms": 10.0}]


def make_db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE VIRTUAL TABLE docs USING fts5(title, abstract, mesh, "
                "tokenize='porter unicode61 remove_diacritics 2', detail=full)")
    con.executemany("INSERT INTO docs(rowid, title, abstract, mesh) VALUES (?, ?, ?, ?)", DOCS)
    con.commit()
    return con


class Prune(unittest.TestCase):
    def test_tokens(self):
        self.assertEqual(prune.tokens("The effect of Metformin on metformin-treated mice, a study"),
                         ["effect", "metformin", "treated", "mice", "study"])
        many = prune.tokens(" ".join("w%d" % i for i in range(40)))
        self.assertEqual((len(many), many[0], many[-1]), (32, "w0", "w31"))
        self.assertEqual(prune.match_expr(["a1", "b2"]), '"a1" OR "b2"')

    def test_doc_freq_capped(self):
        df = prune.DocFreq(make_db(":memory:"), 2)
        self.assertEqual([df("cell"), df("cells"), df("zebrafish"), df("absent")], [3, 3, 1, 0])
        self.assertEqual(df("cell"), 3)
        self.assertEqual(sorted(df.cache), ["absent", "cell", "cells", "zebrafish"])

    def test_prune(self):
        df = prune.DocFreq(make_db(":memory:"), 2)
        self.assertEqual(prune.prune(["zebrafish", "heart", "cell", "growth"], df, 2),
                         (["zebrafish", "heart"], False))
        self.assertEqual(prune.prune(["cell", "growth", "liver"], df, 2),
                         (["cell", "growth", "liver"], True))
        self.assertEqual(prune.prune(["kidney", "absent", "liver"], df, 2), (["kidney", "liver"], False))
        self.assertEqual(prune.prune(["kidney", "absent"], df, 2), (["kidney", "absent"], True))
        self.assertEqual(prune.prune(["kidney"], df, 2, min_terms=1), (["kidney"], False))

    def test_compare(self):
        self.assertEqual(prune.compare([[1, 2.0], [2, 1.0]], [[1, 3.0], [3, 1.0]]), (True, 0.5))
        self.assertEqual(prune.compare([], [[1, 1.0]]), (False, 0.0))
        self.assertEqual(prune.compare([[1, 1.0]], []), (False, None))

    def test_run(self):
        with tempfile.TemporaryDirectory() as d:
            db, needs, out = os.path.join(d, "x.db"), os.path.join(d, "ranked.jsonl"), os.path.join(d, "o")
            make_db(db).close()
            prune.write_jsonl(needs, NEEDS)
            s = prune.run(db, needs, out, depth=10, max_df=2)
            rows = prune.load_jsonl(os.path.join(out, "ranked.jsonl"))
            with open(os.path.join(out, "run.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), s)
        self.assertEqual((s["needs"], s["no_candidates"], s["fallbacks"], s["probed_terms"]), (3, 0, 1, 6))
        self.assertEqual([(r["terms"], r["kept"], r["fallback"]) for r in rows],
                         [(4, 2, False), (3, 3, True), (2, 2, False)])
        self.assertEqual(rows[0]["candidates"][0][0], 1)
        self.assertEqual(len(rows[0]["candidates"]), 1)
        self.assertEqual((rows[1]["candidates"][0][0], len(rows[1]["candidates"])), (3, 5))
        self.assertEqual(sorted(p for p, _ in rows[2]["candidates"]), [1, 5])
        self.assertEqual((s["top1_same"], s["mean_top5_overlap"]), (1.0, 0.75))
        self.assertEqual((s["mean_terms"], s["mean_kept"], s["baseline_median_ms"]), (3.0, 2.33, 500.0))
        self.assertGreater(s["median_speedup"], 1.0)

    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            db, needs = os.path.join(d, "x.db"), os.path.join(d, "ranked.jsonl")
            make_db(db).close()
            prune.write_jsonl(needs, NEEDS)
            self.assertEqual(prune.main(["--db", db, "--needs", needs, "--out-dir", os.path.join(d, "o"),
                                         "--depth", "10", "--max-df", "2"]), 0)
            with self.assertRaises(FileNotFoundError):
                prune.run(os.path.join(d, "none.db"), needs, os.path.join(d, "o2"))


if __name__ == "__main__":
    unittest.main()
