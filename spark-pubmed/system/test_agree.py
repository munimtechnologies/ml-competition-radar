import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agree  # noqa: E402


def row(nid, pmids):
    return {"info_need_id": nid, "info_need": "q", "candidates": [[p, 0.5] for p in pmids]}


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


class Agree(unittest.TestCase):
    def test_rank(self):
        a = [row("A", [1, 2, 3]), row("B", [4, 5, 6]), row("C", [7, 8]), row(9, [1])]
        b = [row("A", [1, 2, 3, 99]), row("B", [5, 4, 6]), row("C", [7, 10]), row("D", [1])]
        res = agree.rank(a, b, k=3)
        self.assertEqual((res["common"], res["only_a"], res["only_b"]), (3, 1, 1))
        self.assertEqual((res["same_order"], res["same_set"], res["same_first"]), (1, 2, 2))
        self.assertEqual(res["differ_ids"], ["B", "C"])
        self.assertEqual(agree.rank(a, b, k=1)["same_order"], 2)

    def test_rank_b_depth(self):
        # A deeper rerank: three reranked items (logits), then one BM25-only tail item.
        a = [row("A", [10, 20]), row("B", [5])]
        b = [{"info_need_id": "A", "candidates": [[30, 3.0], [10, 2.0], [20, 1.0], [40, 0.1]],
              "logits": [3.0, 2.0, 1.0], "bm25_rank": [3, 1, 2, 4]},
             {"info_need_id": "B", "candidates": [[5, 1.0], [6, 0.5]], "logits": [1.0, 0.5], "bm25_rank": [2, 1]}]
        self.assertEqual(agree.at_depth(b[0], 2)["candidates"], [[10, 2.0], [20, 1.0]])
        res = agree.rank(a, b, k=5, b_depth=2)
        self.assertEqual((res["b_depth"], res["same_order"], res["same_set"], res["same_first"], res["differ_ids"]),
                         (2, 1, 1, 2, ["B"]))
        res = agree.rank(a, b, k=5)
        self.assertEqual((res["b_depth"], res["same_order"], res["same_first"]), (0, 0, 1))
        self.assertEqual(len(b[0]["candidates"]), 4)

    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            pa, pb, out = os.path.join(d, "a.jsonl"), os.path.join(d, "b.jsonl"), os.path.join(d, "o", "agree.json")
            write_jsonl(pa, [row("A", [1, 2])])
            write_jsonl(pb, [row("A", [1, 2])])
            self.assertEqual(agree.main(["rank", "--a", pa, "--b", pb, "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["same_order"], 1)
            write_jsonl(pb, [row("Z", [1])])
            self.assertEqual(agree.main(["rank", "--a", pa, "--b", pb, "--out", out]), 1)

    def test_snap_same(self):
        with tempfile.TemporaryDirectory() as d:
            sub, snapf = os.path.join(d, "s"), os.path.join(d, "snap.json")
            os.makedirs(sub)
            self.assertEqual(agree.main(["snap", "--dir", sub, "--out", snapf]), 1)  # nothing to snap
            write_jsonl(os.path.join(sub, "submission_top5.jsonl"), [{"x": 1}])
            write_jsonl(os.path.join(sub, "ranked.jsonl"), [{"y": 1}])
            self.assertEqual(agree.main(["snap", "--dir", sub, "--out", snapf]), 0)
            self.assertEqual(sorted(agree.snap(sub)), ["submission_top5.jsonl"])
            self.assertEqual(agree.main(["same", "--dir", sub, "--snap", snapf]), 0)
            write_jsonl(os.path.join(sub, "submission_top5.jsonl"), [{"x": 2}])
            self.assertEqual(agree.main(["same", "--dir", sub, "--snap", snapf]), 1)


if __name__ == "__main__":
    unittest.main()
