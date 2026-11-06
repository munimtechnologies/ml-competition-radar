"""Unit tests for dsqa_retrieval.py (standard library only).
MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0."""
import json
import os
import unittest

import dsqa_retrieval as r

HERE = os.path.dirname(os.path.abspath(__file__))


class TestChunk(unittest.TestCase):
    def test_pack_no_overlap(self):
        self.assertEqual(r.chunk_text("aaaa\n\nbbbb\n\ncccc", size=9, overlap=0), ["aaaa bbbb", "cccc"])

    def test_pack_with_overlap(self):
        self.assertEqual(r.chunk_text("aaaa\n\nbbbb\n\ncccc", size=9, overlap=2), ["aaaa bbbb", "bb cccc"])

    def test_long_paragraph_split_at_spaces(self):
        self.assertEqual(r.chunk_text("abc def ghi", size=5, overlap=0), ["abc", "def", "ghi"])

    def test_empty(self):
        self.assertEqual(r.chunk_text("\n\n  \n\n", size=10, overlap=0), [])


class TestTokenize(unittest.TestCase):
    def test_lower_and_split(self):
        self.assertEqual(r.tokenize("RQ-Kmeans vs RQ-VAE, 2x"), ["rq", "kmeans", "vs", "rq", "vae", "2x"])


class TestBM25(unittest.TestCase):
    def setUp(self):
        self.bm = r.BM25([["apple", "banana"], ["apple", "cherry"], ["date"]])

    def test_single_rare_term(self):
        # idf = ln((3-1+0.5)/(1+0.5)+1) = ln(2.6667) = 0.98083; avgdl = 5/3;
        # norm = 0.25 + 0.75*2/(5/3) = 1.15; tf part = 2.5/(1+1.5*1.15) = 0.91743; score = 0.89984
        s = self.bm.scores(["banana"])
        self.assertAlmostEqual(s[0], 0.8998, places=3)
        self.assertEqual(s[1], 0.0)
        self.assertEqual(s[2], 0.0)
        self.assertEqual(r.rank_desc(s), [0, 1, 2])

    def test_shared_term_ties(self):
        s = self.bm.scores(["apple", "apple"])
        self.assertGreater(s[0], 0.0)
        self.assertAlmostEqual(s[0], s[1], places=9)
        self.assertEqual(s[2], 0.0)

    def test_unknown_term(self):
        self.assertEqual(self.bm.scores(["zebra"]), [0.0, 0.0, 0.0])


class TestFusionAndMetrics(unittest.TestCase):
    def test_rrf(self):
        # item 0: 1/62 + 1/61; item 2: 1/61 + 1/63; item 1: 1/63 + 1/62
        self.assertEqual(r.rrf([[2, 0, 1], [0, 1, 2]]), [0, 2, 1])

    def test_doc_order_and_first_rank(self):
        docs = r.doc_order([3, 1, 2, 0], ["A", "B", "A", "C"])
        self.assertEqual(docs, ["C", "B", "A"])
        self.assertEqual(r.first_rank(docs, {"A"}), 3)
        self.assertIsNone(r.first_rank(docs, {"Z"}))

    def test_context_take(self):
        self.assertEqual(r.context_take([3, 1, 2, 0], [5, 5, 5, 5], 12), [3, 1])

    def test_evaluate_small_budget(self):
        e = r.evaluate_question([3, 1, 2, 0], ["A", "B", "A", "C"], [5, 5, 5, 5], {"A"}, 12)
        self.assertFalse(e["top1_gold"])
        self.assertEqual(e["first_gold_chunk_rank"], 3)
        self.assertEqual(e["gold_doc_rank"], 3)
        self.assertFalse(e["gold_in_context"])
        self.assertEqual(e["gold_share"], 0.0)
        self.assertEqual(e["context_chunks"], 2)
        self.assertEqual(e["top_doc"], "C")

    def test_evaluate_full_budget(self):
        e = r.evaluate_question([3, 1, 2, 0], ["A", "B", "A", "C"], [5, 5, 5, 5], {"A"}, 20)
        self.assertTrue(e["gold_in_context"])
        self.assertEqual(e["gold_share"], 0.5)
        self.assertEqual(e["context_chunks"], 4)

    def test_summarize(self):
        s = r.summarize([
            {"top1_gold": True, "gold_doc_rank": 1, "gold_in_context": True},
            {"top1_gold": False, "gold_doc_rank": 4, "gold_in_context": False},
            {"top1_gold": False, "gold_doc_rank": None, "gold_in_context": False},
        ])
        # mrr = (1 + 0.25 + 0) / 3 = 0.41667
        self.assertEqual(s, {"n": 3, "hit1": 1, "mrr_doc": 0.4167, "in_context": 1})


class TestCorpusFile(unittest.TestCase):
    def test_corpus_consistent(self):
        with open(os.path.join(HERE, "corpus.json"), encoding="utf-8") as f:
            c = json.load(f)
        ids = [d["id"] for d in c["docs"]]
        self.assertEqual(len(ids), len(set(ids)))
        for d in c["docs"]:
            self.assertIn(d["role"], ("gold", "hard"))
            self.assertTrue(d["urls"])
            self.assertEqual(bool(d.get("gold_for")), d["role"] == "gold")
        covered = sorted(q for d in c["docs"] for q in d.get("gold_for", []))
        self.assertEqual(covered, sorted(c["questions"]))


class TestGrade(unittest.TestCase):
    def test_grade(self):
        def summ(n, hit1, inc):
            return {"n": n, "hit1": hit1, "mrr_doc": 0.0, "in_context": inc}
        res = {
            "extraction_totals": {"pymupdf_seconds": 2.0, "pypdf_seconds": 7.0},
            "roles": {"kr": "hard", "bz": "gold"},
            "methods": {
                "bm25_pymupdf": {"summary": summ(9, 7, 9), "index_seconds": 3.0,
                                 "per_question": {"23": {"top_doc": "kr"}}},
                "dense_pymupdf": {"summary": summ(9, 5, 8)},
                "hybrid_pymupdf": {"summary": summ(9, 6, 8)},
            },
        }
        g = r.grade(res)
        # P1 7 >= 6; P2 7 >= 6.75; P3 7 >= 5; P4 81>=72, 72>=72, 72>=72; P5 6 >= 6; P6 hard; P7 5 < 60
        self.assertEqual(g, {"P1": True, "P2": True, "P3": True, "P4": True, "P5": True,
                             "P6": True, "P7": True, "gradable": True})


if __name__ == "__main__":
    unittest.main()
