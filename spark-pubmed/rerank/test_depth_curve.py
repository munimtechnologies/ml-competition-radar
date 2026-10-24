import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import depth_curve  # noqa: E402

# A: gold 11 is BM25 rank 3, cross-encoder first; 14 sits past the rerank depth.
# B: gold 22 is BM25 rank 1, cross-encoder second. C has no gold.
A = {"info_need_id": "A", "info_need": "q", "candidates": [[11, 0.99], [12, 0.9], [13, 0.5], [14, 0.0]],
     "logits": [3.0, 2.0, 0.0], "bm25_rank": [3, 1, 2, 4], "rerank_depth": 3}
B = {"info_need_id": "B", "info_need": "q", "candidates": [[21, 0.8], [22, 0.7], [23, 0.6]],
     "logits": [1.0, 0.5, 0.2], "bm25_rank": [2, 1, 3], "rerank_depth": 3}
C = dict(B, info_need_id="C")
GOLD = [{"info_need_id": "A", "gold": ["11"]}, {"info_need_id": "B", "gold": [22]}]
# D: gold 46 is BM25 rank 1 but only sixth by the cross-encoder, so depth 7 loses it.
D = {"info_need_id": "D", "info_need": "q", "candidates": [[p, 0.5] for p in range(41, 48)],
     "logits": [7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0], "bm25_rank": [2, 3, 4, 5, 6, 1, 7], "rerank_depth": 7}


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


class Curve(unittest.TestCase):
    def test_parts(self):
        self.assertEqual(depth_curve.head(A), [("11", 3), ("12", 1), ("13", 2)])
        self.assertEqual(depth_curve.at_depth(A, 2), ["12", "13"])
        self.assertEqual(depth_curve.at_depth(D, 7), ["41", "42", "43", "44", "45"])
        self.assertTrue(depth_curve.reaches(A, 3, {"11"}))
        self.assertFalse(depth_curve.reaches(A, 2, {"11"}))
        self.assertEqual(depth_curve.rr_of(["1", "2"], {"2"}), 0.5)

    def test_curve(self):
        res = depth_curve.curve([A, B, C], GOLD, [1, 2, 3, 5])
        self.assertEqual((res["needs"], res["no_gold"], res["rerank_depth"]), (2, 1, 3))
        self.assertEqual((res["skipped_depths"], res["base_depth"]), ([5], 1))
        self.assertEqual(res["depths"]["1"], {"reach": 1, "mrr": 0.5, "hit5": 1, "hit1": 1,
                                              "gained_vs_base": 0, "lost_vs_base": 0})
        self.assertEqual(res["depths"]["2"], {"reach": 1, "mrr": 0.25, "hit5": 1, "hit1": 0,
                                              "gained_vs_base": 0, "lost_vs_base": 0})
        self.assertEqual(res["depths"]["3"], {"reach": 2, "mrr": 0.75, "hit5": 2, "hit1": 1,
                                              "gained_vs_base": 1, "lost_vs_base": 0})

    def test_loss_and_base_50(self):
        res = depth_curve.curve([D], [{"info_need_id": "D", "gold": ["46"]}], [1, 7, 50])
        self.assertEqual((res["base_depth"], res["skipped_depths"]), (1, [50]))
        self.assertEqual(res["depths"]["7"], {"reach": 1, "mrr": 0.0, "hit5": 0, "hit1": 0,
                                              "gained_vs_base": 0, "lost_vs_base": 1})
        e = {"info_need_id": "E", "info_need": "q", "candidates": [[51, 0.9], [52, 0.8], [53, 0.0]],
             "logits": [2.0, 1.0], "bm25_rank": [80, 10, 5], "rerank_depth": 100}
        res = depth_curve.curve([e], [{"info_need_id": "E", "gold": ["51"]}])
        self.assertEqual((res["base_depth"], res["skipped_depths"]), (50, [150, 200, 300]))
        self.assertEqual(sorted(res["depths"], key=int), ["20", "50", "100"])
        self.assertEqual((res["depths"]["50"]["mrr"], res["depths"]["50"]["reach"]), (0.0, 0))
        self.assertEqual(res["depths"]["100"], {"reach": 1, "mrr": 1.0, "hit5": 1, "hit1": 1,
                                                "gained_vs_base": 1, "lost_vs_base": 0})

    def test_unreranked_gold_counts_for_reach_only(self):
        f = {"info_need_id": "F", "info_need": "q", "candidates": [[61, 0.0]], "logits": [],
             "bm25_rank": [1], "rerank_depth": 50}
        res = depth_curve.curve([f], [{"info_need_id": "F", "gold": ["61"]}], [50])
        self.assertEqual(res["depths"]["50"], {"reach": 1, "mrr": 0.0, "hit5": 0, "hit1": 0,
                                               "gained_vs_base": 0, "lost_vs_base": 0})
        self.assertEqual(depth_curve.curve([], GOLD)["needs"], 0)

    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            rk, gd, out = os.path.join(d, "ranked.jsonl"), os.path.join(d, "gold.jsonl"), os.path.join(d, "o")
            write_jsonl(rk, [A, B, C])
            write_jsonl(gd, GOLD)
            self.assertEqual(depth_curve.main(["--ranked", rk, "--gold", gd, "--out-dir", out,
                                               "--depths", "1,3"]), 0)
            with open(os.path.join(out, "curve.json"), encoding="utf-8") as f:
                res = json.load(f)
            self.assertEqual((res["version"], res["depths"]["3"]["mrr"]), ("0.1.0", 0.75))
            self.assertEqual(depth_curve.main(["--ranked", rk, "--gold", gd, "--out-dir", out,
                                               "--depths", "9"]), 1)
            write_jsonl(gd, [])
            self.assertEqual(depth_curve.main(["--ranked", rk, "--gold", gd, "--out-dir", out]), 1)


if __name__ == "__main__":
    unittest.main()
