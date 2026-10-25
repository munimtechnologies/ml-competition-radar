"""Fake-data tests for dense_build.py, dense_search.py and dense_eval.py (numpy only; no torch,
no network). MV2 of Munim, Inc. Apache-2.0."""
import io
import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dense_build  # noqa: E402
import dense_eval  # noqa: E402
import dense_search  # noqa: E402

DIM = 64
TEXT = "secret question words"


class Resp(io.BytesIO):
    def __init__(self, data, length=None):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data) if length is None else length)}


def npy_bytes(arr):
    f = io.BytesIO()
    np.save(f, arr)
    return f.getvalue()


def chunk(k, n, seed):
    emb = np.random.default_rng(seed).normal(size=(n, DIM)).astype(np.float32)
    return emb, k * 1000000 + np.arange(1, n + 1) * 7


def fake_server(chunks):
    """open_url serving the given chunks, and the list of urls it was asked for."""
    files, asked = {}, []
    for k, (emb, pmids) in chunks.items():
        files["embeds_chunk_%d.npy" % k] = npy_bytes(emb)
        files["pmids_chunk_%d.json" % k] = json.dumps([str(p) for p in pmids]).encode()

    def open_url(url):
        asked.append(url)
        name = url.rsplit("/", 1)[-1]
        if name not in files:
            raise OSError("404 " + name)
        return Resp(files[name])
    return open_url, asked


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


class FakeEncoder:
    def __init__(self, model_dir, threads=2):
        self.args = (model_dir, threads)

    def __call__(self, texts):
        q = np.random.default_rng(len(texts)).normal(size=(len(texts), DIM)).astype(np.float32)
        return q, [len(t.split()) * 30 for t in texts]


class Build(unittest.TestCase):
    def test_bits_score_ranks_like_signs(self):
        rng = np.random.default_rng(1)
        x = rng.normal(size=(50, DIM)).astype(np.float32)
        mu = rng.normal(scale=0.1, size=DIM).astype(np.float32)
        bits = dense_build.binarise(x, mu)
        self.assertEqual((bits.shape, bits.dtype), ((50, DIM // 8), np.uint8))
        b = dense_build.unpack(bits, DIM)
        np.testing.assert_array_equal(b, (x > mu).astype(np.float32))
        q = rng.normal(size=DIM).astype(np.float32)
        np.testing.assert_allclose((2 * b - 1) @ q, 2 * (b @ q) - q.sum(), rtol=1e-5, atol=1e-5)

    def test_topk_matches_full_sort(self):
        rng = np.random.default_rng(2)
        scores = rng.normal(size=(23, 3)).astype(np.float32)
        ids = np.arange(100, 123)
        top = dense_build.TopK(3, 5)
        for s in range(0, 23, 4):
            top.add(scores[s:s + 4], ids[s:s + 4])
        got_ids, got_scores = top.result()
        for j in range(3):
            order = np.argsort(-scores[:, j])[:5]
            self.assertEqual(got_ids[j].tolist(), ids[order].tolist())
            np.testing.assert_allclose(got_scores[j], scores[order, j])
        t = dense_build.TopK(1, 3)
        t.add(np.array([[1.0], [2.0], [2.0], [0.5]]), [9, 4, 7, 1])
        self.assertEqual(t.result()[0].tolist(), [[4, 7, 9]])

    def test_build_resume_and_fidelity(self):
        data = {0: chunk(0, 30, 3), 1: chunk(1, 20, 4)}
        open_url, asked = fake_server(data)
        q = np.random.default_rng(5).normal(size=(4, DIM)).astype(np.float32)
        with tempfile.TemporaryDirectory() as d:
            idx, tmp = os.path.join(d, "idx"), os.path.join(d, "tmp")
            kw = dict(chunks=(0, 1), first=1, queries=q, base="mem/", open_url=open_url, dim=DIM,
                      block=7, min_free=0)
            rep = dense_build.build(idx, tmp, **kw)
            self.assertTrue(rep["ok"], rep["problems"])
            self.assertEqual((rep["built"], rep["kept"], rep["vectors"], rep["bits_bytes"]), (2, 0, 50, 400))
            self.assertEqual([r["chunk"] for r in rep["records"]], [1, 0])
            self.assertEqual(rep["records"][0]["mu_from"], 1)
            mu = np.load(os.path.join(idx, "mu.npy"))
            np.testing.assert_allclose(mu, data[1][0].mean(axis=0), rtol=1e-5, atol=1e-6)
            np.testing.assert_array_equal(np.load(os.path.join(idx, "bits_0.npy")),
                                          np.packbits(data[0][0] > mu, axis=1))
            self.assertEqual(np.load(os.path.join(idx, "pmids_0.npy")).tolist(), data[0][1].tolist())
            self.assertEqual(os.listdir(tmp), [])
            self.assertEqual((rep["out_of_span"], rep["pmid_max"]), (0, 1000140))
            f = rep["fidelity"]
            self.assertEqual((f["queries"], f["rows"], f["exact100_in_bits1000"]), (4, 20, 1.0))
            self.assertEqual(len(asked), 4)
            again = dense_build.build(idx, tmp, **kw)
            self.assertEqual((again["built"], again["kept"], again["vectors"], again["ok"]), (0, 2, 50, True))
            self.assertEqual(len(asked), 4)
            self.assertEqual((again["fidelity"], again["records"][0]["fidelity_source"]), (f, "saved"))
            self.assertEqual((again["out_of_span"], again["pmid_max"]), (0, 1000140))

    def test_resume_after_stop_keeps_fidelity(self):
        data = {0: chunk(0, 30, 3), 1: chunk(1, 20, 4)}
        open_url, asked = fake_server(data)
        q = np.random.default_rng(5).normal(size=(4, DIM)).astype(np.float32)
        with tempfile.TemporaryDirectory() as d:
            idx, tmp = os.path.join(d, "idx"), os.path.join(d, "tmp")
            kw = dict(first=1, queries=q, base="mem/", open_url=open_url, dim=DIM, block=7, min_free=0)
            first = dense_build.build(idx, tmp, chunks=(1,), **kw)
            self.assertTrue(first["ok"], first["problems"])
            # As 0.1.0 left a stopped run: no saved fidelity record, a half-finished download.
            os.remove(os.path.join(idx, "fidelity_1.json"))
            with open(os.path.join(tmp, "embeds_chunk_0.npy.part"), "wb") as f:
                f.write(b"half")
            rep = dense_build.build(idx, tmp, chunks=(0, 1), **kw)
            self.assertTrue(rep["ok"], rep["problems"])
            self.assertEqual((rep["built"], rep["kept"], rep["vectors"]), (1, 1, 50))
            r1 = rep["records"][0]
            self.assertEqual((r1["chunk"], r1["status"], r1["fidelity_source"]), (1, "kept", "recomputed"))
            self.assertEqual(rep["fidelity"], first["fidelity"])
            self.assertEqual((rep["out_of_span"], rep["pmid_max"], rep["stale_files_removed"]), (0, 1000140, 1))
            self.assertEqual(len(asked), 5)
            self.assertEqual(os.listdir(tmp), [])
            again = dense_build.build(idx, tmp, chunks=(0, 1), **kw)
            self.assertEqual((again["records"][0]["fidelity_source"], again["fidelity"]),
                             ("saved", first["fidelity"]))
            self.assertEqual(len(asked), 5)
            other = dense_build.build(idx, tmp, chunks=(0, 1), **dict(kw, queries=q[:2]))
            self.assertEqual((other["records"][0]["fidelity_source"], other["fidelity"]["queries"]),
                             ("recomputed", 2))

    def test_failed_first_chunk_stops(self):
        open_url, asked = fake_server({0: chunk(0, 5, 6)})
        with tempfile.TemporaryDirectory() as d:
            rep = dense_build.build(os.path.join(d, "i"), os.path.join(d, "t"), chunks=(0, 1), first=1,
                                    base="mem/", open_url=open_url, dim=DIM, block=4, min_free=0)
            self.assertFalse(rep["ok"])
            self.assertEqual([r["status"] for r in rep["records"]], ["error"])
            self.assertIn("no mean vector", rep["problems"][-1])
            self.assertEqual(len(asked), 6)
            self.assertEqual(os.listdir(os.path.join(d, "t")), [])

    def test_download_short_and_disk_guard(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.bin")
            rec = dense_build.download("mem/f.bin", p, lambda u: Resp(b"abc", length=5), tries=2)
            self.assertEqual((rec["status"], rec["bytes"], rec["content_length"], rec["attempts"]),
                             ("short", 3, 5, 2))
            self.assertEqual(os.listdir(d), [])
            rec = dense_build.download("mem/f.bin", p, lambda u: Resp(b"abc"))
            self.assertEqual((rec["status"], rec["bytes"]), ("ok", 3))
            rep = dense_build.build(os.path.join(d, "i"), os.path.join(d, "t"), chunks=(0,), first=0,
                                    open_url=None, min_free=10, disk_free=lambda path: 5)
            self.assertFalse(rep["ok"])
            self.assertIn("5 bytes free", rep["problems"][0])
            self.assertEqual(rep["records"], [])


class Search(unittest.TestCase):
    def test_fetch_model_uses_pins(self):
        with tempfile.TemporaryDirectory() as d:
            code = os.path.join(d, "code")
            os.makedirs(code)
            with open(os.path.join(code, "fetch_model.py"), "w", encoding="utf-8") as f:
                f.write("def fetch_all(model_dir, files=None, base=None):\n"
                        "    return {'repo': 'x', 'commit': 'y', 'ok': True, 'n': len(files), 'base': base}\n")
            rc = dense_search.main(["fetch-model", "--code-dir", code, "--model-dir", "m", "--out-dir", d])
            with open(os.path.join(d, "fetch_qenc.json"), encoding="utf-8") as f:
                rep = json.load(f)
        self.assertEqual(rc, 0)
        self.assertEqual((rep["repo"], rep["commit"], rep["n"]), (dense_search.QREPO, dense_search.QCOMMIT, 8))
        self.assertTrue(rep["base"].endswith("/resolve/%s/" % dense_search.QCOMMIT))
        self.assertEqual(dense_search.QFILES["pytorch_model.bin"][0], 437993382)

    def test_encode_search_eval(self):
        open_url, _ = fake_server({0: chunk(0, 40, 7), 2: chunk(2, 25, 8)})
        rows_l = [{"info_need_id": "L1", "info_need": TEXT, "candidates": [[5, 2.0], [14, 1.0], [21, 0.5]]},
                  {"info_need_id": "L2", "info_need": TEXT + " two", "candidates": [[28, 1.0], [35, 0.9], [42, 0.1]]}]
        rows_r = [{"info_need_id": "R1", "info_need": "short", "candidates": [[7, 0.9], [14, 0.8]],
                   "bm25_rank": [2, 1]}]
        with tempfile.TemporaryDirectory() as d:
            idx, qdir = os.path.join(d, "idx"), os.path.join(d, "dense")
            dense_build.build(idx, os.path.join(d, "t"), chunks=(0, 2), first=0, base="mem/",
                              open_url=open_url, dim=DIM, block=9, min_free=0)
            l_path, r_path = os.path.join(d, "l.jsonl"), os.path.join(d, "r.jsonl")
            write_jsonl(l_path, rows_l)
            write_jsonl(r_path, rows_r)
            legs = ["--leg", "l=" + l_path, "--leg", "r=" + r_path]
            self.assertEqual(dense_search.main(["encode", "--model-dir", "m", "--out-dir", qdir] + legs,
                                               make_encoder=FakeEncoder), 0)
            with open(os.path.join(qdir, "queries.json"), encoding="utf-8") as f:
                meta = json.load(f)
            self.assertEqual((meta["order"], meta["questions"], meta["dim"]), (["l", "r"], 3, DIM))
            self.assertEqual((meta["legs"]["l"]["truncated"], meta["legs"]["r"]["truncated"]), (2, 0))
            self.assertEqual(meta["legs"]["l"]["ids"], ["L1", "L2"])
            argv = ["search", "--index-dir", idx, "--queries-dir", qdir, "--out-dir", qdir, "--depth", "10"]
            self.assertEqual(dense_search.main(argv + legs), 0)
            with open(os.path.join(qdir, "search.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual((s["chunks"], s["vectors"], s["questions"], s["problems"]), (2, 65, 3, []))
            q = np.load(os.path.join(qdir, "queries.npy"))
            bits = np.concatenate([np.load(os.path.join(idx, "bits_%d.npy" % k)) for k in (0, 2)])
            pmids = np.concatenate([np.load(os.path.join(idx, "pmids_%d.npy" % k)) for k in (0, 2)])
            full = dense_build.unpack(bits, DIM) @ q.T
            out = (dense_search.load_jsonl(os.path.join(qdir, "l", "ranked.jsonl"))
                   + dense_search.load_jsonl(os.path.join(qdir, "r", "ranked.jsonl")))
            for j, row in enumerate(out):
                order = np.lexsort((pmids, -full[:, j]))[:10]
                self.assertEqual([p for p, _ in row["candidates"]], pmids[order].tolist())
            self.assertEqual([r["info_need"] for r in out], [TEXT, TEXT + " two", "short"])
            gold = os.path.join(d, "gold.jsonl")
            write_jsonl(gold, [{"info_need_id": "L1", "gold": [str(out[0]["candidates"][0][0])]},
                               {"info_need_id": "L2", "gold": ["35", "999"]},
                               {"info_need_id": "R1", "gold": ["7"]}])
            res_path = os.path.join(d, "e", "eval.json")
            argv = ["--index-dir", idx, "--out", res_path,
                    "--leg", "l=%s=%s=%s" % (l_path, os.path.join(qdir, "l", "ranked.jsonl"), gold),
                    "--leg", "r=%s=%s=%s" % (r_path, os.path.join(qdir, "r", "ranked.jsonl"), gold)]
            self.assertEqual(dense_eval.main(argv), 0)
            with open(res_path, encoding="utf-8") as f:
                res = json.load(f)
            with open(os.path.join(qdir, "queries.json"), encoding="utf-8") as f:
                meta_text = f.read()
        l, r = res["legs"]["l"], res["legs"]["r"]
        n = len({str(out[0]["candidates"][0][0]), "35", "999"})  # 999 is not in the index
        self.assertEqual(l["coverage"], {"gold_pmids": n, "in_index": n - 1, "share": round((n - 1) / n, 4),
                                         "needs_with_gold_in_index": 2})
        self.assertGreaterEqual(l["dense_mrr5"], 0.5)
        self.assertEqual((r["coverage"]["share"], r["bm25_mrr5"], r["bm25_hit5"]), (1.0, 0.5, 1))
        self.assertFalse(res["decision"]["adopt"])
        self.assertNotIn(TEXT, json.dumps(res))
        self.assertNotIn(TEXT, meta_text)


class Eval(unittest.TestCase):
    def test_leg_eval(self):
        bm_rows = [{"info_need_id": "a", "candidates": [[3, .1], [1, .9], [2, .5]], "bm25_rank": [3, 1, 2]},
                   {"info_need_id": "b", "candidates": [[4, 1], [5, 1], [6, 1]]},
                   {"info_need_id": "c", "candidates": [[7, 1], [8, 1], [9, 1]]}]
        dn_rows = [{"info_need_id": "a", "candidates": [[9, 1], [3, 1], [1, 1]]},
                   {"info_need_id": "b", "candidates": [[6, 1], [10, 1], [11, 1]]}]
        gold = [{"info_need_id": "a", "gold": ["3"]}, {"info_need_id": "b", "gold": ["10"]},
                {"info_need_id": "c", "gold": ["8"]}]
        x = dense_eval.leg_eval(bm_rows, dn_rows, gold, {"3", "8"}, depths=(1, 2, 3),
                                unions=((1, 1), (2, 1), (1, 2)))
        self.assertEqual((x["needs"], x["no_gold"], x["no_dense"]), (2, 0, 1))
        self.assertEqual(x["coverage"], {"gold_pmids": 2, "in_index": 1, "share": 0.5,
                                         "needs_with_gold_in_index": 1})
        self.assertEqual((x["bm25"], x["dense"]), ({"1": 0, "2": 0, "3": 1}, {"1": 0, "2": 2, "3": 2}))
        self.assertEqual(x["union"]["1+2"], {"reach": 2, "mean_candidates": 3.0, "bm25_same_budget": 1,
                                             "gained": ["b"], "lost": []})
        self.assertEqual((x["union"]["2+1"]["reach"], x["union"]["2+1"]["lost"]), (0, ["a"]))
        self.assertEqual(x["union"]["1+1"]["mean_candidates"], 2.0)
        self.assertEqual((x["bm25_mrr5"], x["bm25_hit5"], x["dense_mrr5"], x["dense_hit5"]), (0.1667, 1, 0.5, 2))

    def test_decide(self):
        legs = {g: {"union": {"100+50": {"reach": r}}, "bm25": {"150": b}}
                for g, r, b in (("l", 28, 25), ("bg", 59, 60), ("r", 90, 90))}
        d = dense_eval.decide(legs)
        self.assertTrue(d["adopt"])
        self.assertEqual(d["reach_change"], {"l": 3, "bg": -1, "r": 0})
        legs["l"]["union"]["100+50"]["reach"] = 27
        legs["r"]["union"]["100+50"]["reach"] = 88
        self.assertEqual(dense_eval.decide(legs)["why"], ["L gains 2 < 3", "r loses 2 > 1"])
        self.assertFalse(dense_eval.decide({"l": {}})["adopt"])


if __name__ == "__main__":
    unittest.main()
