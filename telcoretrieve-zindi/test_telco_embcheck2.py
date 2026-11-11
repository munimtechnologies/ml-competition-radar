"""Offline tests for telco_embcheck2.py (no network, no model). Apache-2.0.
MV2 of Munim, Inc. (made with AI agents working in his name)."""
import json
import os
import struct
import tempfile
import unittest

import numpy as np

import telco_embcheck2 as t2


class TestBase(unittest.TestCase):
    def test_reused_module(self):
        self.assertEqual(t2.e1.VERSION, "0.1.0")
        self.assertEqual(t2.VERSION, "0.2.0")
        self.assertEqual(t2.DATA_REV, "2ec07608ee2a77a59a3f5995ca3c10e9cba4c976")


class TestQuestions(unittest.TestCase):
    def test_filter_strip_dedupe(self):
        raw = json.dumps([{"question": "What is X? [3GPP Release 18]"},
                          {"question": "What is Y? [IEEE 802.11]"},
                          {"question": "What is X? [3GPP Release 17]"},
                          {"question": "No tag"},
                          {"question": "  [3GPP Release 19]"},
                          {"q": 1},
                          "str"]).encode("utf-8")
        self.assertEqual(t2.load_questions(raw), ["What is X?"])

    def test_inner_brackets_and_dict_layout(self):
        raw = json.dumps({"data": [{"question": "What is [X] in Y? [3GPP Release 18]"}]}).encode("utf-8")
        self.assertEqual(t2.load_questions(raw), ["What is [X] in Y?"])

    def test_bad_layout(self):
        with self.assertRaises(ValueError):
            t2.load_questions(b"5")

    def test_pick(self):
        qs = ["a", "b", "c", "d", "e"]
        self.assertEqual(t2.pick_questions(qs, 10, 1), qs)
        p = t2.pick_questions(qs, 2, 1)
        self.assertEqual(len(p), 2)
        idx = [qs.index(x) for x in p]
        self.assertEqual(idx, sorted(idx))
        self.assertEqual(p, t2.pick_questions(qs, 2, 1))


class TestBlocks(unittest.TestCase):
    def test_starts(self):
        s = t2.block_starts(1000, 3, 100, 1)
        self.assertEqual(len(s), 3)
        self.assertEqual(s, sorted(set(s)))
        self.assertTrue(all(x % 100 == 0 and 0 <= x <= 900 for x in s))
        self.assertEqual(s, t2.block_starts(1000, 3, 100, 1))
        self.assertEqual(t2.block_starts(250, 5, 100, 1), [0, 100])

    def test_parse_block(self):
        hdr = {"size_data_per_element": 32, "offset_data": 8, "label_offset": 24}

        def el(links, flags, vec, label):
            return struct.pack("<HB", links, flags) + b"\x00" * 5 + struct.pack("<4f", *vec) + struct.pack("<Q", label)

        b = el(3, 0, [1, 2, 3, 4], 7) + el(1, 1, [0, 0, 1, 0], 9)
        out = t2.parse_block(b, hdr, 500, 2)
        self.assertEqual([o["internal_id"] for o in out], [500, 501])
        self.assertEqual([o["label"] for o in out], [7, 9])
        self.assertEqual([o["deleted"] for o in out], [False, True])
        self.assertEqual(out[0]["vector"].tolist(), [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(out[1]["vector"][2], 1.0)
        with self.assertRaises(ValueError):
            t2.parse_block(b[:-1], hdr, 500, 2)


class TestMetrics(unittest.TestCase):
    def test_groups(self):
        g = t2.groups([254, 100, 600, 255, 500])
        self.assertEqual(g["L254"].tolist(), [True, False, False, False, False])
        self.assertEqual(g["SHORT"].tolist(), [True, True, False, False, False])
        self.assertEqual(g["LONG"].tolist(), [False, False, True, False, True])

    def test_topk(self):
        sv = np.array([[1, 0], [0, 1], [0.6, 0.8], [0.8, 0.6]])
        self.assertEqual(t2.topk(np.array([[1.0, 0.0]]), sv, 2).tolist(), [[0, 3]])
        self.assertEqual(t2.topk(np.array([[1.0, 0.0]]), sv, 3).tolist(), [[0, 3, 2]])
        self.assertEqual(t2.topk(np.array([[0.0, 1.0]]), sv, 2).tolist(), [[1, 2]])

    def test_skewness(self):
        self.assertEqual(t2.skewness([1, 1, 1]), 0.0)
        self.assertAlmostEqual(t2.skewness([0, 0, 0, 3]), 2 / 3 ** 0.5, places=6)
        self.assertAlmostEqual(t2.skewness([2, 1, 2, 1]), 0.0, places=12)

    def test_hub_stats(self):
        top = np.array([[0, 3], [1, 2], [0, 2]])
        h = t2.hub_stats(top, 4, np.array([False, False, True, False]))
        self.assertEqual(h["slots"], 6)
        self.assertAlmostEqual(h["base_rate"], 0.25)
        self.assertAlmostEqual(h["topk_share"], 2 / 6)
        self.assertAlmostEqual(h["ratio"], 4 / 3)
        self.assertAlmostEqual(h["any_in_topk"], 2 / 3)
        self.assertEqual(h["top1_share"], 0.0)
        self.assertEqual(h["n10_max"], 2)
        self.assertAlmostEqual(h["top1pct_slot_share"], 2 / 6)
        self.assertEqual(h["never_retrieved"], 0.0)
        self.assertAlmostEqual(h["n10_skew"], 0.0, places=12)
        self.assertIsNone(t2.hub_stats(top, 4, np.zeros(4, dtype=bool))["ratio"])

    def test_median_or_none(self):
        self.assertEqual(t2.median_or_none([1, 2, 3], np.array([True, False, True])), 2.0)
        self.assertIsNone(t2.median_or_none([1, 2, 3], np.zeros(3, dtype=bool)))


def fake(oq=3.0, od=1.2, cq=1.1, br=0.14, ao=(0.9, 0.5), ac=(0.6, 0.55), so=5.0, sc=2.0, ga=True):
    def cell(q, d, skew, aff):
        return {"base_rates": {"L254": br}, "affinity": {"L254": aff[0], "LONG": aff[1]},
                "hubs": {"Q": {"L254": {"ratio": q, "n10_skew": skew}}, "D": {"L254": {"ratio": d, "n10_skew": skew}}}}
    return {"gates": {"GA": ga, "GQ": True}, "otel": cell(oq, od, so, ao), "control": cell(cq, 1.0, sc, ac)}


class TestGrade(unittest.TestCase):
    def test_all_hold(self):
        self.assertEqual(t2.grade(fake()), {p: True for p in t2.PREDICTIONS})

    def test_all_fail(self):
        r = fake(oq=1.0, od=2.0, cq=1.6, br=0.3, ao=(0.5, 0.45), ac=(0.9, 0.5), so=1.0, sc=2.0)
        self.assertEqual(t2.grade(r), {p: False for p in t2.PREDICTIONS})

    def test_gate_and_missing(self):
        self.assertEqual(t2.grade(fake(ga=False)), {p: None for p in t2.PREDICTIONS})
        g = t2.grade(fake(od=None))
        self.assertIsNone(g["P4"])
        self.assertTrue(g["P2"])
        r = fake()
        r["otel"]["affinity"]["L254"] = None
        self.assertIsNone(t2.grade(r)["P5"])


class TestReport(unittest.TestCase):
    def test_write_md(self):
        top = np.array([[0, 3], [1, 2], [0, 2]])
        h = t2.hub_stats(top, 4, np.array([False, False, True, False]))
        cell = {"cell": "otel-0.6b", "resolved": 4, "sampled": 4, "prompts": {"dtype": "torch.float32"},
                "encode_seconds": 1.0, "base_rates": {"L254": 0.25}, "affinity": {"L254": 0.9},
                "hubs": {"Q": {"L254": h, "SHORT": h}, "D": {"L254": h, "SHORT": h}}}
        res = {"otel": cell, "control_error": "RuntimeError: x", "gates": {"GA": False, "GQ": True},
               "grades": {p: None for p in t2.PREDICTIONS}, "questions": {"used": 3}}
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.md")
            t2.write_md(res, p)
            with open(p, encoding="utf-8") as f:
                txt = f.read()
        self.assertIn("## otel (otel-0.6b)", txt)
        self.assertIn("## control: RuntimeError: x", txt)
        self.assertIn("| Q | L254 | 0.2500 | 0.3333 | 1.33 |", txt)
        self.assertIn("- P1: not graded", txt)


if __name__ == "__main__":
    unittest.main()
