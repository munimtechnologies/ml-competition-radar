# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for param_cap_check (no network). Made with AI agents for MV2 of Munim, Inc."""
import json
import os
import tempfile
import unittest
import urllib.error

import param_cap_check as pc

CAP = 3e9


def meta(total=None, licence=None, licence_name=None, tags=None):
    m = {"tags": tags or [], "pipeline_tag": "text-generation", "gated": False,
         "sha": "abc", "lastModified": "2026-01-01T00:00:00.000Z"}
    card = {}
    if licence is not None:
        card["license"] = licence
    if licence_name is not None:
        card["license_name"] = licence_name
    if card:
        m["cardData"] = card
    if total is not None:
        m["safetensors"] = {"total": total, "parameters": {"BF16": total}}
    return m


class LicenceTests(unittest.TestCase):
    def test_card_licence(self):
        self.assertEqual(pc.licence_of(meta(licence="Apache-2.0")), "apache-2.0")

    def test_other_licence_keeps_name(self):
        self.assertEqual(pc.licence_of(meta(licence="other", licence_name="qwen-research")),
                         "other:qwen-research")

    def test_licence_from_tags(self):
        self.assertEqual(pc.licence_of(meta(tags=["text-generation", "license:mit"])), "mit")

    def test_unknown_licence(self):
        self.assertEqual(pc.licence_of(meta()), "unknown")


class AssessTests(unittest.TestCase):
    def test_ok_under_cap(self):
        r = pc.assess("Qwen/Qwen3-1.7B", meta(2031739904, "apache-2.0"), CAP)
        self.assertEqual(r["verdict"], "ok")
        self.assertEqual(r["params_b"], 2.032)

    def test_named_3b_over_cap(self):
        r = pc.assess("HuggingFaceTB/SmolLM3-3B", meta(3075098624, "apache-2.0"), CAP)
        self.assertEqual(r["verdict"], "over-cap")
        self.assertFalse(r["fits_cap"])

    def test_exactly_at_cap_fits(self):
        r = pc.assess("x/y", meta(3000000000, "mit"), CAP)
        self.assertEqual(r["verdict"], "ok")

    def test_unknown_size(self):
        r = pc.assess("x/y", meta(None, "mit"), CAP)
        self.assertEqual(r["verdict"], "unknown-size")
        self.assertIsNone(r["params_b"])

    def test_over_cap_and_licence(self):
        r = pc.assess("meta-llama/Llama-3.2-3B-Instruct", meta(3212749824, "llama3.2"), CAP)
        self.assertEqual(r["verdict"], "over-cap-and-licence")

    def test_licence_only(self):
        r = pc.assess("LiquidAI/LFM2-2.6B", meta(2569272320, "other", "lfm1.0"), CAP)
        self.assertEqual(r["verdict"], "licence")
        self.assertEqual(r["licence"], "other:lfm1.0")


class IoTests(unittest.TestCase):
    def test_read_models(self):
        text = "# header\nA/b\n\nC/d  # note\nA/b\n"
        self.assertEqual(pc.read_models(text), ["A/b", "C/d"])

    def test_markdown_rows(self):
        rows = [pc.assess("A/b", meta(1500000000, "mit"), CAP),
                {"model": "C/d", "verdict": "error", "error": "HTTP 404"}]
        md = pc.to_markdown(rows, CAP)
        self.assertIn("| A/b | 1,500,000,000 | 1.500 | mit | ok |", md)
        self.assertIn("| C/d | - | - | - | error: HTTP 404 |", md)
        self.assertIn("3,000,000,000", md)

    def test_main_with_stub_fetcher(self):
        fake = {"A/b": meta(2000000000, "apache-2.0"), "C/d": meta(4000000000, "apache-2.0")}

        def fetcher(model_id):
            if model_id not in fake:
                raise urllib.error.HTTPError("u", 404, "nf", {}, None)
            return fake[model_id]

        with tempfile.TemporaryDirectory() as tmp:
            models = os.path.join(tmp, "models.txt")
            with open(models, "w", encoding="utf-8") as fh:
                fh.write("A/b\nC/d\nE/f\n")
            out = os.path.join(tmp, "out")
            self.assertEqual(pc.main(["--models", models, "--out-dir", out], fetcher=fetcher, pause=0), 0)
            with open(os.path.join(out, "param-cap.json"), encoding="utf-8") as fh:
                report = json.load(fh)
            self.assertEqual(report["counts"], {"error": 1, "ok": 1, "over-cap": 1})
            self.assertEqual(report["cap"], 3000000000)
            self.assertTrue(os.path.exists(os.path.join(out, "param-cap.md")))


if __name__ == "__main__":
    unittest.main()
