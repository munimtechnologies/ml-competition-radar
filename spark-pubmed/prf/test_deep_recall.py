import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deep_recall  # noqa: E402

GOLD = [{"info_need_id": "L1", "gold": ["7"]}, {"info_need_id": "L2", "gold": ["9", "3"]},
        {"info_need_id": "L3", "gold": ["99"]}]


def cands(pmids):
    return [[p, 10.0 - i] for i, p in enumerate(pmids)]


RANKED = [{"info_need_id": "L1", "info_need": "q1", "candidates": cands(list(range(1, 251)))},
          {"info_need_id": "L2", "info_need": "q2", "candidates": cands([5, 3, 9])},
          {"info_need_id": "L3", "info_need": "q3", "candidates": cands([1, 2])},
          {"info_need_id": "X9", "info_need": "q4", "candidates": cands([1])}]


class Deep(unittest.TestCase):
    def test_first_gold_rank(self):
        self.assertEqual(deep_recall.first_gold_rank(cands([4, 9, 3]), {"3", "9"}), 2)
        self.assertIsNone(deep_recall.first_gold_rank(cands([4]), {"3"}))
        self.assertIsNone(deep_recall.first_gold_rank([], {"3"}))

    def test_deep(self):
        r = deep_recall.deep(RANKED, GOLD)
        self.assertEqual((r["needs"], r["max_candidates"], r["no_gold"], r["not_found"]), (3, 250, ["X9"], 1))
        self.assertEqual(r["hits_at"], {"1": 0, "5": 1, "10": 2, "20": 2, "50": 2, "100": 2, "200": 2})
        self.assertEqual((r["recall_at"]["5"], r["recall_at"]["10"]), (0.3333, 0.6667))
        self.assertNotIn("300", r["hits_at"])
        self.assertEqual(r["first_gold_rank_bands"],
                         {"1-5": 1, "6-50": 1, "51-100": 0, "101-200": 0, "201-500": 0, "501-1000": 0})

    def test_deep_band_edges(self):
        ranked = [{"info_need_id": "L1", "candidates": cands(list(range(2000, 1901, -1)) + [7])}]
        r = deep_recall.deep(ranked, GOLD[:1])
        self.assertEqual((r["max_candidates"], r["hits_at"]["50"], r["hits_at"]["100"]), (100, 0, 1))
        self.assertEqual(r["first_gold_rank_bands"]["51-100"], 1)
        ranked = [{"info_need_id": "L1", "candidates": cands(list(range(2000, 1001, -1)) + [7])}]
        r = deep_recall.deep(ranked, GOLD[:1])
        self.assertEqual((r["max_candidates"], r["hits_at"]["500"], r["hits_at"]["1000"]), (1000, 0, 1))
        self.assertEqual(r["not_found"], 0)
        self.assertEqual(r["first_gold_rank_bands"]["501-1000"], 1)

    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            rp, gp, out = os.path.join(d, "r.jsonl"), os.path.join(d, "g.jsonl"), os.path.join(d, "o")
            for path, rows in ((rp, RANKED), (gp, GOLD)):
                with open(path, "w", encoding="utf-8") as f:
                    f.write("".join(json.dumps(x) + "\n" for x in rows))
            self.assertEqual(deep_recall.main(["--ranked", rp, "--gold", gp, "--out-dir", out]), 0)
            with open(os.path.join(out, "deep.json"), encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["hits_at"]["200"], 2)
            self.assertNotIn("q1", json.dumps(saved))
            with open(gp, "w", encoding="utf-8") as f:
                f.write(json.dumps({"info_need_id": "none", "gold": ["1"]}) + "\n")
            self.assertEqual(deep_recall.main(["--ranked", rp, "--gold", gp, "--out-dir", out]), 1)


if __name__ == "__main__":
    unittest.main()
