# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for param_parts (no network). Made with AI agents for MV2 of Munim, Inc."""
import json
import os
import struct
import tempfile
import unittest
import urllib.error

import param_parts as pp

CAP = 3e9


def blob(header):
    raw = json.dumps(header).encode("utf-8")
    return struct.pack("<Q", len(raw)) + raw + b"\x00" * 16


def t(*shape):
    return {"dtype": "BF16", "shape": list(shape), "data_offsets": [0, 0]}


class ClassifyTests(unittest.TestCase):
    def test_qwen35_names(self):
        self.assertEqual(pp.classify("model.visual.blocks.0.attn.qkv.weight"), "vision")
        self.assertEqual(pp.classify("mtp.layers.0.self_attn.q_proj.weight"), "mtp")
        self.assertEqual(pp.classify("model.language_model.embed_tokens.weight"), "embed")
        self.assertEqual(pp.classify("model.language_model.layers.3.self_attn.q_proj.weight"), "text_core")

    def test_gemma_names(self):
        self.assertEqual(pp.classify("model.language_model.embed_tokens_per_layer.weight"), "per_layer_embed")
        self.assertEqual(pp.classify("model.audio_tower.conformer.0.ffw.weight"), "audio")
        self.assertEqual(pp.classify("model.embed_audio.embedding_projection.weight"), "audio")
        self.assertEqual(pp.classify("model.embed_vision.embedding_projection.weight"), "vision")

    def test_other_names(self):
        self.assertEqual(pp.classify("model.multi_modal_projector.linear_1.weight"), "vision")
        self.assertEqual(pp.classify("lm_head.weight"), "lm_head")
        self.assertEqual(pp.classify("model.layers.0.self_attn.q_proj.weight_scale_inv"), "quant_scale")

    def test_numel_and_prefix(self):
        self.assertEqual(pp.numel([3, 4]), 12)
        self.assertEqual(pp.numel([]), 1)
        self.assertEqual(pp.prefix("model.layers.12.mlp.up_proj.weight"), "model.layers.*")


class HeaderTests(unittest.TestCase):
    def test_read_header_from_bytes(self):
        header = {"__metadata__": {"format": "pt"}, "a": t(2, 3)}
        data = blob(header)
        got = pp.read_header("u", getter=lambda url, s, e: data[s:e + 1])
        self.assertEqual(got, header)

    def test_implausible_length(self):
        data = struct.pack("<Q", 0) + b"{}"
        with self.assertRaises(ValueError):
            pp.read_header("u", getter=lambda url, s, e: data[s:e + 1])

    def test_short_read(self):
        data = struct.pack("<Q", 50) + b'{"a": 1}'
        with self.assertRaises(ValueError):
            pp.read_header("u", getter=lambda url, s, e: data[s:e + 1])


class PickTests(unittest.TestCase):
    def test_single_file_wins_over_consolidated(self):
        files, how = pp.pick_files(["consolidated.safetensors", "model.safetensors"], lambda f: {})
        self.assertEqual((files, how), (["model.safetensors"], "model.safetensors"))

    def test_index(self):
        idx = {"weight_map": {"a": "m-2.safetensors", "b": "m-1.safetensors", "c": "m-1.safetensors"}}
        files, how = pp.pick_files(["model.safetensors.index.json", "m-1.safetensors", "m-2.safetensors"],
                                   lambda f: idx)
        self.assertEqual((files, how), (["m-1.safetensors", "m-2.safetensors"], "index"))

    def test_fallback(self):
        files, how = pp.pick_files(["b.safetensors", "sub/x.safetensors", "a.safetensors", "README.md"],
                                   lambda f: {})
        self.assertEqual((files, how), (["a.safetensors", "b.safetensors"], "all-root-safetensors"))


GEMMA_LIKE = {
    "model.language_model.embed_tokens.weight": t(1000, 1000),           # 1.0e6
    "model.language_model.embed_tokens_per_layer.weight": t(1000, 2000),  # 2.0e6
    "model.language_model.layers.0.mlp.up_proj.weight": t(500, 1000),     # 0.5e6
    "model.vision_tower.blocks.0.weight": t(300, 1000),                   # 0.3e6
    "model.audio_tower.blocks.0.weight": t(200, 1000),                    # 0.2e6
    "mtp.fc.weight": t(150, 1000),                                        # 0.15e6
    "__metadata__": {"format": "pt"},
}


class PartsTests(unittest.TestCase):
    def test_split_and_readings(self):
        sums, tensors, prefixes = pp.split_parts([GEMMA_LIKE])
        self.assertEqual(tensors, 6)
        self.assertEqual(sums["per_layer_embed"], 2000000)
        c = pp.readings(sums)
        self.assertEqual(c, {"stored": 4150000, "no_towers": 3650000,
                             "no_towers_mtp": 3450000, "text_effective": 1450000})
        self.assertEqual(prefixes["model.vision_tower.blocks"]["part"], "vision")

    def test_assess_against_cap(self):
        meta = {"sha": "s", "safetensors": {"total": 4150000}}
        r = pp.assess("g/e", meta, [GEMMA_LIKE], "model.safetensors", ["model.safetensors"], 3.5e6)
        self.assertTrue(r["matches_api"])
        self.assertEqual(r["fits"], {"stored": False, "no_towers": False,
                                     "no_towers_mtp": True, "text_effective": True})

    def test_mismatch_flagged(self):
        meta = {"sha": "s", "safetensors": {"total": 1}}
        r = pp.assess("g/e", meta, [GEMMA_LIKE], "x", ["x"], CAP)
        self.assertFalse(r["matches_api"])


class MainTests(unittest.TestCase):
    def test_main_with_stubs(self):
        metas = {
            "g/e": {"sha": "s1", "gated": False, "safetensors": {"total": 4150000},
                    "siblings": [{"rfilename": "model.safetensors"}]},
            "m/l": {"sha": "s2", "gated": "manual", "safetensors": {"total": 5}},
        }

        def api(m):
            if m not in metas:
                raise urllib.error.HTTPError("u", 404, "nf", {}, None)
            return metas[m]

        seen = []

        def header(m, rev, f):
            seen.append((m, rev, f))
            return GEMMA_LIKE

        with tempfile.TemporaryDirectory() as tmp:
            models = os.path.join(tmp, "models.txt")
            with open(models, "w", encoding="utf-8") as fh:
                fh.write("g/e\nm/l\nx/y\n")
            out = os.path.join(tmp, "out")
            rc = pp.main(["--models", models, "--out-dir", out, "--cap", "3.5e6"],
                         api=api, header=header, index=lambda m, rev, f: {}, pause=0)
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "param-parts.json"), encoding="utf-8") as fh:
                report = json.load(fh)
            with open(os.path.join(out, "param-parts.md"), encoding="utf-8") as fh:
                md = fh.read()
        self.assertEqual(seen, [("g/e", "s1", "model.safetensors")])
        self.assertEqual(report["summary"]["read"], 1)
        self.assertEqual(report["summary"]["fits"]["text_effective"], 1)
        self.assertEqual(report["rows"][1]["skipped"], "gated (no token used)")
        self.assertEqual(report["rows"][2]["error"], "HTTP 404")
        self.assertIn("| g/e | 0.000 | 0.000 | 0.000 | 0.002 | **0.004** | **0.004** | 0.003 | 0.001 | yes |", md)


if __name__ == "__main__":
    unittest.main()
