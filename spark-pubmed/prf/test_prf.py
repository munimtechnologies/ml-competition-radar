import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prf  # noqa: E402

# Record counts (porter stems): zebrafish 2, heart 2, fin 2, regrowth 3, failure 1, trial 1,
# liver 1, kidney 1. PMID 99 is not in the index.
DOCS = [(1, "zebrafish heart", "fin regrowth fin", ""),
        (2, "heart failure", "trial", ""),
        (3, "fin regrowth", "zebrafish", ""),
        (4, "liver", "liver growth", ""),
        (5, "kidney", "regrowth", "")]
NEEDS = [{"info_need_id": "a", "info_need": "Zebrafish heart", "candidates": [[1, 2.0]], "ms": 100.0},
         {"info_need_id": "b", "info_need": "liver", "candidates": [], "ms": 50.0},
         {"info_need_id": "c", "info_need": "kidney trial", "candidates": [[99, 1.0]]}]


def make_db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE VIRTUAL TABLE docs USING fts5(title, abstract, mesh, "
                "tokenize='porter unicode61 remove_diacritics 2', detail=full)")
    con.executemany("INSERT INTO docs(rowid, title, abstract, mesh) VALUES (?, ?, ?, ?)", DOCS)
    con.commit()
    return con


class Parts(unittest.TestCase):
    def test_words(self):
        self.assertEqual(prf.words("The 2020 study of Cell cells, a b"), ["study", "cell", "cells"])
        self.assertEqual(prf.words("covid19 19"), ["covid19"])
        self.assertEqual(prf.tokens("Zebrafish heart, zebrafish"), ["zebrafish", "heart"])

    def test_feedback_weights(self):
        self.assertEqual(prf.feedback_weights([(3.0, "fin fin heart"), (1.0, "heart"), (0.0, "")]),
                         {"fin": 0.5, "heart": 0.5})
        self.assertEqual(prf.feedback_weights([(-1.0, "fin"), (-2.0, "heart heart")]),
                         {"fin": 0.5, "heart": 0.5})
        self.assertEqual(prf.feedback_weights([]), {})

    def test_expansion(self):
        w = {"a1": 0.5, "b2": 0.4, "c3": 0.3, "d4": 0.2, "e5": 0.1}
        df = {"a1": 5, "b2": 0, "c3": 2, "d4": 1, "e5": 1}.get
        self.assertEqual(prf.expansion(w, {"a1"}, df, 3, 2, 10), ["c3", "d4"])
        self.assertEqual(prf.expansion(w, {"a1"}, df, 3, 2, 2), ["c3"])
        self.assertEqual(prf.expansion({"zz": 0.5, "aa": 0.5}, set(), {"zz": 1, "aa": 1}.get, 3, 1, 5), ["aa"])

    def test_rrf(self):
        a, b = [[1, 9.0], [2, 8.0], [3, 7.0]], [[3, 1.0], [4, 0.5]]
        self.assertEqual([p for p, _ in prf.rrf([a, b], 60, 10)], [3, 1, 2, 4])
        self.assertEqual(prf.rrf([a, b], 60, 2)[1], [1, 0.016393])
        self.assertEqual(prf.rrf([[], []]), [])


class Run(unittest.TestCase):
    def test_run(self):
        with tempfile.TemporaryDirectory() as d:
            db, needs, out = os.path.join(d, "x.db"), os.path.join(d, "ranked.jsonl"), os.path.join(d, "o")
            make_db(db).close()
            prf.write_jsonl(needs, NEEDS)
            s = prf.run(db, needs, out, depth=10, fb_terms=2, max_df=3, question_max_df=3)
            fused = prf.load_jsonl(os.path.join(out, "ranked.jsonl"))
            exp = prf.load_jsonl(os.path.join(out, "ranked_exp.jsonl"))
            with open(os.path.join(out, "run.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), s)
        self.assertEqual([r["expansion_terms"] for r in fused], [2, 0, 0])
        self.assertEqual([r["kept"] for r in exp], [2, 1, 2])
        self.assertEqual(sorted(p for p, _ in exp[0]["candidates"]), [1, 2, 3, 5])
        self.assertEqual((fused[0]["candidates"][0][0], sorted(p for p, _ in fused[0]["candidates"])),
                         (1, [1, 2, 3, 5]))
        self.assertEqual([p for p, _ in fused[1]["candidates"]], [4])
        self.assertEqual((fused[2]["candidates"][0][0], sorted(p for p, _ in fused[2]["candidates"])),
                         (99, [2, 5, 99]))
        self.assertEqual((s["needs"], s["no_expansion"], s["missing_text"], s["mean_expansion_terms"]),
                         (3, 2, 1, 0.67))
        self.assertEqual((s["no_candidates_fused"], s["no_candidates_exp"], s["probed_terms"]), (0, 0, 7))
        self.assertEqual(s["baseline_median_ms"], 75.0)
        self.assertGreater(s["median_total_ms"], 50.0)

    def test_main_all_question_words(self):
        with tempfile.TemporaryDirectory() as d:
            db, needs, out = os.path.join(d, "x.db"), os.path.join(d, "ranked.jsonl"), os.path.join(d, "o")
            make_db(db).close()
            prf.write_jsonl(needs, NEEDS)
            self.assertEqual(prf.main(["--db", db, "--needs", needs, "--out-dir", out, "--depth", "10",
                                       "--fb-terms", "2", "--max-df", "3"]), 0)
            with open(os.path.join(out, "run.json"), encoding="utf-8") as f:
                s = json.load(f)
            with self.assertRaises(FileNotFoundError):
                prf.run(os.path.join(d, "none.db"), needs, os.path.join(d, "o2"))
        self.assertEqual((s["question_max_df"], s["probed_terms"], s["no_expansion"]), (0, 2, 2))


if __name__ == "__main__":
    unittest.main()
