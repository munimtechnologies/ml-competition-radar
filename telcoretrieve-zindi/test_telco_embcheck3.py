"""Offline tests for telco_embcheck3.py (no network, standard library only). Apache-2.0.
MV2 of Munim, Inc. (made with AI agents working in his name)."""
import json
import os
import sqlite3
import tempfile
import unittest

import telco_embcheck3 as t3


ROWS = [("R/23_series/a.md::c::0", "x" * 254),
        ("R/23_series/a.md::c::1", "y" * 254),
        ("R/23_series/a.md::c::2", "z" * 210),
        ("R/24_series/b.md::c::0", "w" * 254),
        ("R/24_series/b.md::c::1", "short"),
        ("bad", None)]


class TestPure(unittest.TestCase):
    def test_version(self):
        self.assertEqual(t3.VERSION, "0.3.0")
        self.assertEqual(t3.L, 254)

    def test_parse_doc_id(self):
        self.assertEqual(t3.parse_doc_id("Rel-19/23_series/23288-j20.md::otel-0.6b::1113"),
                         ("Rel-19/23_series/23288-j20.md", 1113))
        self.assertEqual(t3.parse_doc_id("abc"), ("abc", None))
        self.assertEqual(t3.parse_doc_id("a::b::x"), ("a", None))

    def test_series(self):
        self.assertEqual(t3.series_of("Rel-19/23_series/23288-j20.md"), "23_series")
        self.assertEqual(t3.series_of("x.md"), "?")

    def test_spike_ratio(self):
        self.assertAlmostEqual(t3.spike_ratio({254: 280, 250: 28}), 280.0)
        self.assertIsNone(t3.spike_ratio({254: 5}))
        self.assertAlmostEqual(t3.spike_ratio({10: 6, 9: 2, 11: 4}, at=10, width=1), 2.0)

    def test_neighbour_share(self):
        keys = {("a", 1), ("a", 2), ("a", 5), ("b", 3)}
        self.assertAlmostEqual(t3.neighbour_share(keys), 0.5)
        self.assertIsNone(t3.neighbour_share(set()))

    def test_features(self):
        f = t3.features("ab 1.")
        self.assertAlmostEqual(f["letters"], 0.4)
        self.assertAlmostEqual(f["digits"], 0.2)
        self.assertAlmostEqual(f["spaces"], 0.2)
        self.assertFalse(f["pipe"])
        self.assertTrue(f["ends_period"])
        self.assertTrue(f["starts_lower"])
        self.assertEqual(f["newlines"], 0)
        self.assertEqual(f["max_token"], 2)
        g = t3.features("| X |\n")
        self.assertAlmostEqual(g["letters"], 1 / 6.0)
        self.assertAlmostEqual(g["spaces"], 0.5)
        self.assertTrue(g["pipe"])
        self.assertFalse(g["ends_period"])
        self.assertFalse(g["starts_lower"])
        self.assertEqual(g["newlines"], 1)
        self.assertEqual(g["max_token"], 1)
        e = t3.features("")
        self.assertEqual(e["letters"], 0.0)
        self.assertEqual(e["max_token"], 0)
        self.assertFalse(e["starts_lower"])

    def test_median_summarize(self):
        self.assertEqual(t3.median([3, 1, 2]), 2.0)
        self.assertEqual(t3.median([4, 1, 3, 2]), 2.5)
        self.assertIsNone(t3.median([]))
        self.assertEqual(t3.summarize([]), {"n": 0})
        s = t3.summarize([t3.features("ab 1."), t3.features("| X |\n")])
        self.assertEqual(s["n"], 2)
        self.assertAlmostEqual(s["letters_median"], (0.4 + 1 / 6.0) / 2)
        self.assertAlmostEqual(s["pipe_share"], 0.5)
        self.assertAlmostEqual(s["ends_period_share"], 0.5)
        self.assertAlmostEqual(s["starts_lower_share"], 0.5)
        self.assertAlmostEqual(s["newlines_median"], 0.5)
        self.assertAlmostEqual(s["max_token_median"], 1.5)

    def test_scan_rows(self):
        cell, lens, samples = t3.scan_rows(ROWS)
        self.assertEqual(cell["total"], 6)
        self.assertEqual(cell["l254_count"], 3)
        self.assertAlmostEqual(cell["l254_share"], 0.5)
        self.assertEqual(cell["near_count"], 1)
        self.assertIsNone(cell["spike_ratio"])
        self.assertEqual(cell["hist_240_268"]["254"], 3)
        self.assertEqual(len(cell["hist_240_268"]), 29)
        self.assertEqual(cell["top_lengths"], [[254, 3], [0, 1], [5, 1], [210, 1]])
        self.assertAlmostEqual(cell["l254_neighbour_share"], 2 / 3.0)
        self.assertEqual(cell["near_neighbour_share"], 0.0)
        self.assertEqual(cell["l254_docs"], 2)
        self.assertEqual([x["series"] for x in cell["series_l254"]], ["23_series", "24_series"])
        self.assertAlmostEqual(cell["series_l254"][0]["share_of_l254"], 2 / 3.0)
        self.assertAlmostEqual(cell["series_l254"][0]["share_of_series_rows"], 2 / 3.0)
        self.assertAlmostEqual(cell["series_l254"][1]["share_of_series_rows"], 0.5)
        self.assertEqual(cell["features_l254"]["n"], 3)
        self.assertEqual(cell["features_near"]["n"], 1)
        self.assertEqual(len(lens), 5)
        self.assertEqual(lens[("R/23_series/a.md", 2)], 210)
        self.assertEqual([s["doc_id"] for s in samples],
                         ["R/23_series/a.md::c::0", "R/23_series/a.md::c::1", "R/24_series/b.md::c::0"])

    def test_compare_lens(self):
        r = t3.compare_lens({("a", 0): 1, ("a", 1): 2}, {("a", 0): 1, ("a", 1): 3, ("b", 0): 1})
        self.assertEqual(r, {"keys_a": 2, "keys_b": 3, "common": 2, "same_length_share": 0.5})
        self.assertIsNone(t3.compare_lens({}, {})["same_length_share"])

    def test_grade(self):
        self.assertEqual(t3.grade({"gates": {"GF": False}}), {p: None for p in t3.PREDICTIONS})
        o = {"l254_share": 0.08, "l254_count": 1000, "total": 1000000, "spike_ratio": 50.0,
             "l254_neighbour_share": 0.7,
             "features_l254": {"n": 5, "letters_median": 0.3, "ends_period_share": 0.1},
             "features_near": {"n": 5, "letters_median": 0.6, "ends_period_share": 0.4}}
        c = {"l254_count": 1500}
        res = {"gates": {"GF": True}, "cells": {"otel-0.6b": o, "qwen3-embedding-0.6b": c}}
        self.assertEqual(t3.grade(res), {p: True for p in t3.PREDICTIONS})
        c["l254_count"] = 3000
        o["spike_ratio"] = 10.0
        g = t3.grade(res)
        self.assertFalse(g["D2"])
        self.assertFalse(g["D3"])
        self.assertTrue(g["D1"])


class TestMain(unittest.TestCase):
    def test_end_to_end_small(self):
        with tempfile.TemporaryDirectory() as d:
            data, out = os.path.join(d, "data"), os.path.join(d, "out")
            os.makedirs(data)
            for name in t3.CELLS:
                conn = sqlite3.connect(os.path.join(data, name + "_fts.db"))
                conn.execute("CREATE TABLE bm25_index (doc_id TEXT, text TEXT)")
                conn.executemany("INSERT INTO bm25_index VALUES (?, ?)", ROWS)
                conn.commit()
                conn.close()
            self.assertEqual(t3.main(["--data-dir", data, "--out-dir", out]), 0)
            with open(os.path.join(out, "embcheck3.json"), encoding="utf-8") as f:
                res = json.load(f)
            self.assertEqual(res["cells"]["otel-0.6b"]["total"], 6)
            self.assertEqual(res["cells"]["qwen3-embedding-0.6b"]["l254_count"], 3)
            self.assertEqual(res["gates"], {"GF": False})
            self.assertEqual(res["grades"], {p: None for p in t3.PREDICTIONS})
            self.assertEqual(res["cross"]["same_length_share"], 1.0)
            self.assertTrue(os.path.exists(os.path.join(out, "RESULTS-embcheck3-auto.md")))
            with open(os.path.join(out, "samples_embcheck3.json"), encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)["otel-0.6b"]), 3)

    def test_missing_db(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(t3.main(["--data-dir", d, "--out-dir", os.path.join(d, "out"), "--no-download"]), 3)


if __name__ == "__main__":
    unittest.main()
