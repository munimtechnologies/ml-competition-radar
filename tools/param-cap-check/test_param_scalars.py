# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Tests for param_scalars.py (stdlib unittest; no network)."""
import json
import os
import tempfile
import unittest

import param_scalars as ps

H = {
    "__metadata__": {"format": "pt"},
    "a.weight": {"dtype": "BF16", "shape": [2, 3]},
    "a.input_scale": {"dtype": "F32", "shape": []},
    "b.input_max": {"dtype": "BF16", "shape": []},
    "c.weight": {"dtype": "F8_E4M3", "shape": [4]},
}
META1 = {"sha": "abc", "safetensors": {"parameters": {"BF16": 6, "F8_E4M3": 4}, "total": 10}}
META2 = {"sha": "abc", "safetensors": {"parameters": {"BF16": 7, "F32": 1, "F8_E4M3": 4}, "total": 12}}


class DtypeTests(unittest.TestCase):
    def test_dtype_sums(self):
        params, zero, names = ps.dtype_sums([H])
        self.assertEqual(params, {"BF16": 7, "F32": 1, "F8_E4M3": 4})
        self.assertEqual(zero, {"F32": 1, "BF16": 1})
        self.assertEqual(names, ["a.input_scale", "b.input_max"])

    def test_gap_from_zero_dim(self):
        r = ps.explain("x/one", META1, [H], ["model.safetensors"])
        self.assertEqual(r["ours_total"], 12)
        self.assertEqual(r["gap"], 2)
        self.assertEqual(r["zero_dim_tensors"], 2)
        self.assertTrue(r["gap_equals_zero_dim"])
        self.assertFalse(r["dtype_match_counting_zero_dim_as_1"])
        self.assertTrue(r["dtype_match_counting_zero_dim_as_0"])
        self.assertEqual(r["dtypes_missing_from_api"], ["F32"])
        self.assertEqual(r["zero_dim_by_part"], {"quant_scale": 1, "text_core": 1})
        self.assertEqual(r["zero_dim_by_leaf"], {"input_scale": 1, "input_max": 1})

    def test_api_counts_scalars(self):
        r = ps.explain("x/one", META2, [H], ["model.safetensors"])
        self.assertEqual(r["gap"], 0)
        self.assertFalse(r["gap_equals_zero_dim"])
        self.assertTrue(r["dtype_match_counting_zero_dim_as_1"])
        self.assertFalse(r["dtype_match_counting_zero_dim_as_0"])
        self.assertEqual(r["dtypes_missing_from_api"], [])

    def test_no_api_numbers(self):
        r = ps.explain("x/one", {"sha": "abc"}, [H], ["model.safetensors"])
        self.assertIsNone(r["api_total"])
        self.assertIsNone(r["gap"])
        self.assertFalse(r["gap_equals_zero_dim"])


class MainTests(unittest.TestCase):
    def test_main_with_stubs(self):
        metas = {
            "x/one": dict(META1, siblings=[{"rfilename": "model.safetensors"},
                                           {"rfilename": "README.md"}]),
            "x/gated": {"gated": "auto", "sha": "g"},
        }
        calls = []

        def api(m):
            if m == "x/bad":
                raise ValueError("boom")
            return metas[m]

        def header(m, rev, f):
            calls.append((m, rev, f))
            return H

        with tempfile.TemporaryDirectory() as d:
            models = os.path.join(d, "models.txt")
            with open(models, "w", encoding="utf-8") as fh:
                fh.write("x/one\nx/gated  # gated\nx/bad\nx/one\n")
            out = os.path.join(d, "out")
            rc = ps.main(["--models", models, "--out-dir", out], api=api, header=header,
                         index=lambda m, rev, f: {}, pause=0)
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [("x/one", "abc", "model.safetensors")])
            with open(os.path.join(out, "param-scalars.json"), encoding="utf-8") as fh:
                rep = json.load(fh)
            self.assertEqual(rep["summary"], {"models": 3, "read": 1, "gap_zero": 0,
                                              "gap_equals_zero_dim": 1, "with_zero_dim": 1})
            self.assertEqual(rep["rows"][1], {"model": "x/gated", "skipped": "gated (no token used)"})
            self.assertEqual(rep["rows"][2], {"model": "x/bad", "error": "ValueError: boom"})
            with open(os.path.join(out, "param-scalars.md"), encoding="utf-8") as fh:
                md = fh.read()
            self.assertIn("| x/one | 12 | 10 | 2 | 2 | yes | quant_scale 1, text_core 1 | F32 |", md)
            self.assertIn("| x/gated | - | - | - | - | - | - | gated (no token used) |", md)


if __name__ == "__main__":
    unittest.main()
