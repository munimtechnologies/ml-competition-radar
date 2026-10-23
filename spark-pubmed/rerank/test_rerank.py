"""Fake-data tests for fetch_model.py, rerank.py and bench.py (no network, tiny random BERT).

MV2 of Munim, Inc. Apache-2.0.
"""
import json
import math
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_model  # noqa: E402

WORDS = ("kinase tumour cell gene mouse study patients we found a the of in and treatment diabetes "
         "zebrafish heart review insulin trial").split()

CARD = '''# MedCPT-Cross-Encoder (fake card)

```python
import torch
query = "diabetes treatment"
# 6 articles to be ranked for the input query
articles = [
\t"Diabetes treatment in mouse heart. We found insulin [...]",
\t"Kinase gene study. A review of tumour cell [...]",
]
```

```bash
tensor([  1.0000,  -2.5000])
```
'''


def tiny_model(d):
    """A 2-layer BERT with random weights plus a matching WordPiece tokenizer, saved to d."""
    import torch
    from transformers import BertConfig, BertForSequenceClassification, BertTokenizerFast
    vocab = os.path.join(d, "vocab.txt")
    with open(vocab, "w", encoding="utf-8") as f:
        f.write("\n".join(["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"] + WORDS) + "\n")
    BertTokenizerFast(vocab_file=vocab, do_lower_case=True).save_pretrained(d)
    torch.manual_seed(0)
    cfg = BertConfig(vocab_size=5 + len(WORDS), hidden_size=32, num_hidden_layers=2, num_attention_heads=2,
                     intermediate_size=64, max_position_embeddings=512, num_labels=1)
    BertForSequenceClassification(cfg).save_pretrained(d)
    with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
        f.write(CARD)
    return d


DOCS = ["kinase", "the tumour cell study of patients in mouse heart", "insulin trial",
        "a review of diabetes treatment and insulin in patients with heart gene", "zebrafish"]


class FetchTest(unittest.TestCase):
    def test_digests(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x")
            open(p, "wb").close()
            self.assertEqual(fetch_model.digest(p, "git"), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
            with open(p, "wb") as f:
                f.write(b"hello\n")
            self.assertEqual(fetch_model.digest(p, "git"), "ce013625030ba8dba906f756967f9e9ca394464a")
            with open(p, "wb") as f:
                f.write(b"abc")
            self.assertEqual(fetch_model.digest(p, "sha256"),
                             "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_pinned_spec(self):
        self.assertEqual(len(fetch_model.COMMIT), 40)
        self.assertEqual(sum(s for s, _, _ in fetch_model.FILES.values()), 438937324)
        for size, kind, want in fetch_model.FILES.values():
            self.assertEqual(len(want), 40 if kind == "git" else 64)
            int(want, 16)
        self.assertIn(fetch_model.COMMIT, fetch_model.BASE)

    def test_fetch_resume_and_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "src")
            os.makedirs(src)
            with open(os.path.join(src, "a.txt"), "wb") as f:
                f.write(b"hello\n")
            with open(os.path.join(src, "b.bin"), "wb") as f:
                f.write(b"abc")
            base = pathlib.Path(src).as_uri() + "/"
            spec = {"a.txt": (6, "git", "ce013625030ba8dba906f756967f9e9ca394464a"),
                    "b.bin": (3, "sha256", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")}
            dst = os.path.join(d, "model")
            rep = fetch_model.fetch_all(dst, spec, base)
            self.assertTrue(rep["ok"])
            self.assertEqual([r["status"] for r in rep["files"]], ["downloaded", "downloaded"])
            self.assertEqual(rep["total_bytes"], 9)
            rep = fetch_model.fetch_all(dst, spec, base)
            self.assertEqual([r["status"] for r in rep["files"]], ["kept", "kept"])

            bad = {"b.bin": (3, "sha256", "0" * 64), "gone.txt": (1, "git", "0" * 40)}
            dst2 = os.path.join(d, "model2")
            rep = fetch_model.fetch_all(dst2, bad, base)
            self.assertFalse(rep["ok"])
            st = {r["file"]: r for r in rep["files"]}
            self.assertEqual(st["b.bin"]["status"], "mismatch")
            self.assertEqual(st["b.bin"]["attempts"], 3)
            self.assertEqual(st["gone.txt"]["status"], "error")
            self.assertEqual(os.listdir(dst2), [])

    def test_main_writes_report(self):
        with tempfile.TemporaryDirectory() as d:
            orig = fetch_model.fetch_all
            fetch_model.fetch_all = lambda model_dir: {"ok": False, "files": []}
            try:
                self.assertEqual(fetch_model.main(["--model-dir", d, "--out-dir", d]), 1)
            finally:
                fetch_model.fetch_all = orig
            with open(os.path.join(d, "fetch_model.json"), encoding="utf-8") as f:
                self.assertFalse(json.load(f)["ok"])


class RerankTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = tiny_model(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def enc(self, **kw):
        from rerank import CrossEncoder
        return CrossEncoder(self.dir, **kw)

    def test_doc_text(self):
        from rerank import doc_text
        self.assertEqual(doc_text("A title.", "  Abstract text "), "A title. Abstract text")
        self.assertEqual(doc_text(None, "x"), "x")
        self.assertEqual(doc_text("t", None), "t")

    def test_batching_does_not_change_scores(self):
        a = self.enc(batch_size=2).score("diabetes insulin", DOCS)
        b = self.enc(batch_size=16).score("diabetes insulin", DOCS)
        self.assertEqual(len(a), len(DOCS))
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, places=4)
        self.assertEqual(self.enc().score("q", []), [])

    def test_matches_card_style_call(self):
        import torch
        e = self.enc(batch_size=2)
        enc = e.tokenizer([["diabetes insulin", t] for t in DOCS], truncation=True, padding=True,
                          return_tensors="pt", max_length=512)
        with torch.no_grad():
            direct = e.model(**enc).logits.squeeze(dim=1).tolist()
        for x, y in zip(e.score("diabetes insulin", DOCS), direct):
            self.assertAlmostEqual(x, y, places=4)

    def test_rerank(self):
        e = self.enc()
        cands = [("p%d" % i, t) for i, t in enumerate(DOCS)]
        top = e.rerank("heart gene", cands, k=3)
        self.assertEqual(len(top), 3)
        self.assertEqual([s for _, s in top], sorted([s for _, s in top], reverse=True))
        self.assertTrue(set(i for i, _ in top) <= set(i for i, _ in cands))
        self.assertEqual(len(e.rerank("heart gene", cands, k=50)), len(DOCS))
        self.assertGreaterEqual(e.last_seconds, 0.0)

    def test_quantize(self):
        e = self.enc()
        e.quantize()
        s = e.score("diabetes insulin", DOCS)
        self.assertEqual(len(s), len(DOCS))
        self.assertTrue(all(math.isfinite(x) for x in s))


class BenchTest(unittest.TestCase):
    def test_parse_card(self):
        import bench
        q, arts, printed = bench.parse_card(CARD)
        self.assertEqual(q, "diabetes treatment")
        self.assertEqual(arts, ["Diabetes treatment in mouse heart. We found insulin [...]",
                                "Kinase gene study. A review of tumour cell [...]"])
        self.assertEqual(printed, [1.0, -2.5])
        self.assertEqual(bench.parse_card("no example here"), (None, None, None))

    def test_budget(self):
        import bench
        self.assertEqual(bench.depth_for_budget({"256": 250.0, "512": 250.0})["depth"], 144)
        self.assertEqual(bench.depth_for_budget({"256": 100.0, "512": 300.0})["ms_per_pair"], 150.0)

    def test_batches_and_card_check(self):
        import bench
        from rerank import CrossEncoder
        with tempfile.TemporaryDirectory() as d:
            tiny_model(d)
            e = CrossEncoder(d)
            q, arts, _ = bench.parse_card(CARD)
            pool = bench.id_pool(e.tokenizer, arts, 512)
            self.assertEqual(len(pool), 512)
            self.assertEqual(len(bench.id_pool(e.tokenizer, None, 40)), 40)
            for L in (32, 128):
                b = bench.make_batch(e.tokenizer, pool, L, 3)
                self.assertEqual(tuple(b["input_ids"].shape), (3, L))
                self.assertEqual(int(b["input_ids"][0, 0]), e.tokenizer.cls_token_id)
                self.assertEqual(int(b["input_ids"][0, -1]), e.tokenizer.sep_token_id)
                self.assertGreater(bench.time_forward(e.model, b, 1), 0.0)
            own = e._logits([[q, a] for a in arts])
            c = bench.card_check(e, q, arts, own)
            self.assertTrue(c["graded"])
            self.assertLess(c["max_abs_diff"], 1e-4)
            self.assertTrue(c["same_order"])
            self.assertFalse(bench.card_check(e, q, arts, own + [0.0])["graded"])

    def test_main_end_to_end(self):
        import bench
        with tempfile.TemporaryDirectory() as d:
            tiny_model(d)
            out = os.path.join(d, "out")
            self.assertEqual(bench.main(["--model-dir", d, "--out-dir", out, "--batch", "2", "--batches", "1"]), 0)
            with open(os.path.join(out, "bench.json"), encoding="utf-8") as f:
                rep = json.load(f)
            self.assertTrue(rep["fp32"]["card"]["graded"])
            self.assertEqual(rep["fp32"]["card"]["n"], 2)
            self.assertEqual(sorted(rep["int8"]["speedup"]), ["128", "256", "512"])
            self.assertIn("max_abs_diff_vs_fp32", rep["int8"])
            self.assertIsInstance(rep["fp32"]["budget"]["depth"], int)
            self.assertGreater(rep["peak_rss_gb"], 0.0)


if __name__ == "__main__":
    unittest.main()
