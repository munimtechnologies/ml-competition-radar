"""Fake-data tests for rerank_run.py (no network, no torch). MV2 of Munim, Inc. Apache-2.0."""
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rerank_run  # noqa: E402

DOCS = {11: ("Kinase alpha", "zebrafish fins"), 12: ("Kinase beta", "mouse liver"),
        13: ("Zebrafish kinase", "zebrafish fin regrowth after injury"), 14: ("Unrelated", ""),
        15: ("Tail item", "zebrafish zebrafish zebrafish")}


class WordScorer:
    """Logit = count of query words in the article - 2 (so some logits are negative)."""
    def __init__(self):
        self.calls = []

    def score(self, query, docs):
        self.calls.append(len(docs))
        words = query.lower().split()
        return [float(sum(d.lower().split().count(w) for w in words) - 2) for d in docs]


def make_db(d):
    db = os.path.join(d, "idx.db")
    con = sqlite3.connect(db)
    con.execute("CREATE VIRTUAL TABLE docs USING fts5(title, abstract, mesh)")
    for pmid, (t, a) in DOCS.items():
        con.execute("INSERT INTO docs(rowid, title, abstract, mesh) VALUES (?,?,?,?)", (pmid, t, a, ""))
    con.commit()
    con.close()
    return db


def make_ranked(d, rows):
    path = os.path.join(d, "ranked.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return path


class RerankRunTest(unittest.TestCase):
    def test_sigmoid_and_text(self):
        self.assertEqual(rerank_run.sigmoid(0.0), 0.5)
        self.assertAlmostEqual(rerank_run.sigmoid(2.0) + rerank_run.sigmoid(-2.0), 1.0)
        self.assertEqual(rerank_run.sigmoid(-1000.0), 0.0)
        self.assertEqual(rerank_run.sigmoid(1000.0), 1.0)
        self.assertEqual(rerank_run.doc_text(" A title ", None), "A title")
        self.assertEqual(rerank_run.doc_text("T", "abs"), "T abs")

    def test_rerank_depth_tail_and_missing(self):
        need = {"info_need_id": "Q1", "info_need": "zebrafish fin",
                "candidates": [[12, 9.0], [99, 8.0], [11, 7.0], [13, 6.0], [15, 5.0]], "depth": 5}
        with tempfile.TemporaryDirectory() as d:
            db, scorer = make_db(d), WordScorer()
            s = rerank_run.run(db, make_ranked(d, [need]), os.path.join(d, "out"), scorer, depth=4)
            rows = rerank_run.load_jsonl(os.path.join(d, "out", "ranked.jsonl"))
        r = rows[0]
        # head = 12, 99 (no text), 11, 13; logits: 13 -> 2 zebrafish + 1 fin - 2 = 1,
        # 11 -> 1 zebrafish ("fins" is not "fin") - 2 = -1, 12 -> -2; 15 is past the depth
        self.assertEqual([p for p, _ in r["candidates"]], [13, 11, 12, 99, 15])
        self.assertEqual(r["logits"], [1.0, -1.0, -2.0])
        self.assertEqual(r["candidates"][0][1], round(rerank_run.sigmoid(1.0), 6))
        self.assertEqual([c[1] for c in r["candidates"][3:]], [0.0, 0.0])
        self.assertEqual(r["bm25_rank"], [4, 3, 1, 2, 5])
        self.assertEqual((r["missing_text"], r["depth"], r["rerank_depth"]), ([99], 5, 4))
        self.assertEqual(scorer.calls, [3])
        self.assertEqual((s["needs"], s["pairs"], s["needs_top1_changed"], s["missing_text"]), (1, 3, 1, 1))
        self.assertEqual(s["rerank_depth"], 4)

    def test_ties_keep_bm25_order_and_empty_need(self):
        needs = [{"info_need_id": "Q2", "info_need": "nothing matches", "candidates": [[14, 3.0], [12, 2.0]]},
                 {"info_need_id": "Q3", "info_need": "the", "candidates": []}]
        with tempfile.TemporaryDirectory() as d:
            db, scorer = make_db(d), WordScorer()
            s = rerank_run.run(db, make_ranked(d, needs), os.path.join(d, "out"), scorer)
            rows = rerank_run.load_jsonl(os.path.join(d, "out", "ranked.jsonl"))
            with open(os.path.join(d, "out", "rerank.json"), encoding="utf-8") as f:
                saved = json.load(f)
        self.assertEqual([p for p, _ in rows[0]["candidates"]], [14, 12])
        self.assertEqual(rows[0]["depth"], 2)
        self.assertEqual(rows[1]["candidates"], [])
        self.assertEqual(scorer.calls, [2])
        self.assertEqual((s["needs"], s["pairs"], s["needs_top1_changed"]), (2, 2, 0))
        self.assertEqual(saved, s)

    def test_missing_db(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                rerank_run.run(os.path.join(d, "none.db"), "x", d, WordScorer())


if __name__ == "__main__":
    unittest.main()
