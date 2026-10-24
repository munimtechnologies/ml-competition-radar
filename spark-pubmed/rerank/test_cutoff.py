import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cutoff  # noqa: E402

A = {"info_need_id": "A", "candidates": [[11, 0.95], [12, 0.6], [13, 0.2], [14, 0.05], [15, 0.01], [16, 0.0]],
     "logits": [3.0, 0.4, -1.4, -2.9, -4.6], "bm25_rank": [3, 1, 2, 5, 4, 6]}
B = {"info_need_id": "B", "candidates": [[21, 0.4], [22, 0.3], [23, 0.1]],
     "logits": [-0.4, -0.85, -2.2], "bm25_rank": [1, 2, 3]}
C = {"info_need_id": "C", "candidates": [[31, 0.8], [32, 0.7]], "logits": [1.4, 0.85], "bm25_rank": [2, 1]}
D = {"info_need_id": "D", "candidates": [[41, 0.5]], "logits": [0.0], "bm25_rank": [1]}
GOLD = [{"info_need_id": "A", "gold": ["12"]}, {"info_need_id": "B", "gold": ["21"]},
        {"info_need_id": "C", "gold": ["99"]}]
BY = {g["info_need_id"]: set(g["gold"]) for g in GOLD}


class Cut(unittest.TestCase):
    def test_policies(self):
        self.assertEqual(cutoff.cut(A, "top:2"), ["11", "12"])
        self.assertEqual(cutoff.cut(A, "abs:0.5"), ["11", "12"])
        self.assertEqual(cutoff.cut(A, "abs:0.7"), ["11"])
        self.assertEqual(cutoff.cut(B, "abs0:0.5"), [])
        self.assertEqual(cutoff.cut(B, "abs0:0.3"), ["21", "22"])
        self.assertEqual(cutoff.cut(A, "margin:1"), ["11"])
        self.assertEqual(cutoff.cut(A, "margin:4"), ["11", "12"])
        self.assertEqual(cutoff.cut({"candidates": [[7, 0.0], [8, 0.0]]}, "margin:2"), ["7"])
        self.assertEqual(cutoff.cut({"candidates": []}, "top:5"), [])

    def test_bad_policies(self):
        for bad in ("top:6", "top:2.5", "abs:1.5", "margin:-1", "foo:1", "top:x"):
            with self.assertRaises(ValueError):
                cutoff.parse_policy(bad)
        for pol in cutoff.POLICIES:
            cutoff.parse_policy(pol)


class Scores(unittest.TestCase):
    def test_policy_scores(self):
        s = cutoff.policy_scores([A, B, C], BY)
        self.assertEqual(s["top:1"], {"mrr": 0.3333, "hit": 0.3333, "mean_returned": 1.0, "mean_wrong": 0.667,
                                      "empty": 0, "penalised": {"0.25": 0.3, "0.5": 0.2667, "1.0": 0.2}})
        self.assertEqual(s["top:5"], {"mrr": 0.5, "hit": 0.6667, "mean_returned": 3.333, "mean_wrong": 2.667,
                                      "empty": 0, "penalised": {"0.25": 0.3667, "0.5": 0.2333, "1.0": -0.0333}})
        self.assertEqual({k: s["abs0:0.5"][k] for k in ("mrr", "hit", "mean_returned", "mean_wrong", "empty")},
                         {"mrr": 0.1667, "hit": 0.3333, "mean_returned": 1.333, "mean_wrong": 1.0, "empty": 1})
        self.assertEqual(list(s), list(cutoff.POLICIES))

    def test_best(self):
        pols = {"top:1": {"mrr": 0.3, "mean_returned": 1.0, "penalised": {"0.25": 0.3, "0.5": 0.28, "1.0": 0.2}},
                "top:5": {"mrr": 0.5, "mean_returned": 3.3, "penalised": {"0.25": 0.37, "0.5": 0.2, "1.0": -0.03}},
                "abs:0.5": {"mrr": 0.5, "mean_returned": 2.0, "penalised": {"0.25": 0.1, "0.5": 0.1, "1.0": 0.1}}}
        self.assertEqual(cutoff.best(pols), {"0": "abs:0.5", "0.25": "top:5", "0.5": "top:1", "1.0": "top:1"})

    def test_calibration(self):
        c = cutoff.calibration([A, B, C], BY)
        self.assertEqual((c["first_is_gold"], c["first_not_gold"], c["first_item_auroc"]), (1, 2, 0.0))
        self.assertEqual((c["top5_items_gold"], c["top5_items_not_gold"], c["top5_item_auroc"]), (2, 8, 0.625))
        self.assertEqual(list(c["bands"]), ["0.0-0.1", "0.1-0.3", "0.3-0.5", "0.5-0.7", "0.7-0.9", "0.9-1.0"])
        self.assertEqual(c["bands"]["0.3-0.5"], {"needs": 1, "first_is_gold": 1})
        self.assertEqual(c["bands"]["0.9-1.0"], {"needs": 1, "first_is_gold": 0})
        self.assertEqual(c["bands"]["0.0-0.1"], {"needs": 0, "first_is_gold": 0})
        self.assertIsNone(cutoff.auroc([], [0.5]))
        self.assertEqual(cutoff.auroc([0.5], [0.5]), 0.5)


class Orders(unittest.TestCase):
    F = {"candidates": [[1, 0.9], [2, 0.8], [3, 0.7], [4, 0.1], [5, 0.0]], "logits": [2, 1, 0, -2],
         "bm25_rank": [4, 3, 1, 2, 5]}

    def test_fuse_and_bm25(self):
        self.assertEqual([p for p, _ in cutoff.fuse(self.F, 10)], [3, 1, 2, 4, 5])
        self.assertEqual([p for p, _ in cutoff.bm25_order(self.F)], [3, 4, 2, 1, 5])
        e = {"candidates": [[1, 0.9], [2, 0.8], [3, 0.7]], "logits": [2, 1, 0], "bm25_rank": [3, 2, 1]}
        self.assertEqual([p for p, _ in cutoff.fuse(e, 60)], [1, 3, 2])

    def test_order_scores(self):
        o = cutoff.order_scores([A, B, C], BY)
        self.assertEqual(o, {"ce": {"mrr": 0.5, "hit": 0.6667}, "bm25": {"mrr": 0.6667, "hit": 0.6667},
                             "rrf10": {"mrr": 0.6667, "hit": 0.6667}, "rrf60": {"mrr": 0.6667, "hit": 0.6667}})


class Main(unittest.TestCase):
    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            ranked, gold, out = os.path.join(d, "ranked.jsonl"), os.path.join(d, "gold.jsonl"), os.path.join(d, "o")
            with open(ranked, "w", encoding="utf-8") as f:
                f.write("".join(json.dumps(r) + "\n" for r in (A, B, C, D)))
            with open(gold, "w", encoding="utf-8") as f:
                f.write("".join(json.dumps(g) + "\n" for g in GOLD))
            self.assertEqual(cutoff.main(["--ranked", ranked, "--gold", gold, "--out-dir", out]), 0)
            with open(os.path.join(out, "cutoff.json"), encoding="utf-8") as f:
                r = json.load(f)
            self.assertEqual((r["version"], r["needs"], r["no_gold"]), ("0.1.0", 3, 1))
            self.assertEqual(r["orders"]["ce"], {"mrr": 0.5, "hit": 0.6667})
            self.assertEqual(set(r["best"]), {"0", "0.25", "0.5", "1.0"})
            with open(gold, "w", encoding="utf-8") as f:
                f.write(json.dumps({"info_need_id": "Z", "gold": ["1"]}) + "\n")
            self.assertEqual(cutoff.main(["--ranked", ranked, "--gold", gold, "--out-dir", out]), 1)


if __name__ == "__main__":
    unittest.main()
