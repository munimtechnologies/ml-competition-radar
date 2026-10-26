"""Fake-data tests for dense_wbits.py (numpy only, no network). dense_build.py is loaded from
DENSE_CODE_DIR (default /out/code, where fetch_code.py puts group "dense" in the job)."""
import io
import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dense_wbits  # noqa: E402

CODE = os.environ.get("DENSE_CODE_DIR", "/out/code")
BUILD = dense_wbits.load_build(CODE)


def patterns():
    """All 256 eight-bit patterns, row r = pattern r; value of dim j is 0 or 2^j."""
    b = ((np.arange(256)[:, None] >> np.arange(8)) & 1).astype(np.float32)
    w = (2.0 ** np.arange(8)).astype(np.float32)
    return b * w, w


class Resp:
    def __init__(self, data, length):
        self.buf, self.headers = io.BytesIO(data), {"Content-Length": str(length)}

    def read(self, n):
        return self.buf.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def npy_bytes(x):
    buf = io.BytesIO()
    np.save(buf, x)
    return buf.getvalue()


class Parts(unittest.TestCase):
    def test_cond_means(self):
        emb = np.array([[1, 10], [3, 20], [5, 60]], dtype=np.float32)
        lo, hi, up = dense_wbits.cond_means(emb, np.array([3, 30], dtype=np.float32), block=2)
        np.testing.assert_allclose(lo, [2, 15])
        np.testing.assert_allclose(hi, [5, 60])
        np.testing.assert_allclose(up, [1 / 3, 1 / 3])

    def test_codes(self):
        t = np.array([[0], [1], [2]], dtype=np.float32)
        x = np.array([[-1], [0.5], [1.5], [3], [0], [1], [2]], dtype=np.float32)
        self.assertEqual(dense_wbits.codes(x, t)[:, 0].tolist(), [0, 1, 2, 3, 0, 1, 2])

    def test_quartiles(self):
        emb = np.arange(8, dtype=np.float32)[:, None]
        t = dense_wbits.quartile_thresholds(emb, stride=2)
        np.testing.assert_allclose(t[:, 0], [1.5, 3, 4.5])

    def test_code_means_and_empty_cells(self):
        t = np.array([[0, 0], [1, 1], [2, 2]], dtype=np.float32)
        emb = np.array([[-1, 0.5], [3, 0.7], [0.5, 0.9]], dtype=np.float32)
        cm, cnt = dense_wbits.code_means(emb, t, block=2)
        np.testing.assert_allclose(cm[:, 0], [-1, 0.5, 1.5, 3], atol=1e-6)
        np.testing.assert_allclose(cm[:, 1], [0, 0.7, 1.5, 2], atol=1e-6)
        self.assertEqual(cnt[:, 0].tolist(), [1, 1, 0, 1])
        self.assertEqual(cnt[:, 1].tolist(), [0, 3, 0, 0])

    def test_weighted_ranks_like_reconstruction(self):
        rng = np.random.default_rng(3)
        x = rng.normal(size=(50, 16)).astype(np.float32) * rng.uniform(0.1, 5, size=16).astype(np.float32)
        mu = x.mean(axis=0)
        lo, hi, _ = dense_wbits.cond_means(x, mu, block=7)
        b = (x > mu).astype(np.float32)
        q = rng.normal(size=(3, 16)).astype(np.float32)
        gap = q @ (lo + b * (hi - lo)).T - (q * (hi - lo)) @ b.T
        np.testing.assert_allclose(gap, np.repeat((q @ lo)[:, None], 50, axis=1), atol=1e-4)

    def test_fidelity_by_hand(self):
        x, w = patterns()
        mu = w / 2
        bits = BUILD.binarise(x, mu)
        lo, hi, _ = dense_wbits.cond_means(x, mu, block=64)
        np.testing.assert_allclose(lo, 0)
        np.testing.assert_allclose(hi, w)
        t = dense_wbits.quartile_thresholds(x, stride=1)
        np.testing.assert_allclose(t, np.stack([0 * w, w / 2, w]))
        cm, cnt = dense_wbits.code_means(x, t, block=64)
        np.testing.assert_allclose(cm, np.stack([0 * w, w / 4, w, w]))
        q = np.ones((1, 8), dtype=np.float32)
        fid = dense_wbits.fidelity(BUILD, x, bits, q, hi - lo, t, cm, block=64)
        # exact order is the pattern value; plain q . b is the popcount, ties to the smaller row:
        # top 10 = 255, the eight 7-bit patterns, then 63; five of them are in 246-255
        self.assertEqual(fid["plain"]["overlap10"], 0.5)
        for v in ("weighted", "two_bit"):
            self.assertEqual(fid[v], {"overlap10": 1.0, "overlap100": 1.0, "exact10_in_bits100": 1.0,
                                      "exact100_in_bits1000": 1.0})


class Run(unittest.TestCase):
    def setup_dirs(self, d, flip_row=None):
        x, w = patterns()
        mu = w / 2
        bits = BUILD.binarise(x, mu)
        if flip_row is not None:
            bits[flip_row, 0] ^= 1
        dirs = {k: os.path.join(d, k) for k in ("index", "tmp", "q", "out", "keep")}
        for p in (dirs["index"], dirs["q"]):
            os.makedirs(p)
        np.save(os.path.join(dirs["index"], "bits_36.npy"), bits)
        np.save(os.path.join(dirs["index"], "mu.npy"), mu)
        np.save(os.path.join(dirs["q"], "queries.npy"), np.ones((2, 8), dtype=np.float32))
        with open(os.path.join(dirs["q"], "queries.json"), "w", encoding="utf-8") as f:
            json.dump({"order": ["l"]}, f)
        return x, w, dirs

    def call(self, dirs, open_url, disk_free=lambda p: 10 ** 12):
        return dense_wbits.run(CODE, dirs["index"], dirs["tmp"], dirs["q"], dirs["out"], dirs["keep"],
                               stride=1, open_url=open_url, disk_free=disk_free)

    def test_run_ok(self):
        with tempfile.TemporaryDirectory() as d:
            x, w, dirs = self.setup_dirs(d)
            data = npy_bytes(x)
            urls = []

            def opener(url):
                urls.append(url)
                return Resp(data, len(data))
            rep = self.call(dirs, opener)
            self.assertEqual(rep["problems"], [])
            self.assertEqual(urls, [BUILD.BASE + "embeds_chunk_36.npy"])
            self.assertEqual((rep["rows"], rep["queries"], rep["bits_mismatch_rows"]), (256, 2, 0))
            self.assertEqual(rep["w_max_over_min"], 128.0)
            self.assertEqual(rep["w_top5_dims"], [7, 6, 5, 4, 3])
            self.assertEqual(rep["empty_code_cells"], 16)
            self.assertEqual(rep["fidelity"]["plain"]["overlap10"], 0.5)
            self.assertEqual(rep["fidelity"]["weighted"]["overlap100"], 1.0)
            np.testing.assert_allclose(np.load(os.path.join(dirs["out"], "wdense", "queries.npy")),
                                       np.repeat(w[None, :], 2, axis=0))
            with open(os.path.join(dirs["out"], "wdense", "queries.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"order": ["l"]})
            np.testing.assert_allclose(np.load(os.path.join(dirs["keep"], "wbits_36.npz"))["w"], w)
            self.assertEqual(os.listdir(dirs["tmp"]), [])

    def test_bits_mismatch_is_a_problem(self):
        with tempfile.TemporaryDirectory() as d:
            x, _, dirs = self.setup_dirs(d, flip_row=5)
            data = npy_bytes(x)
            rep = self.call(dirs, lambda url: Resp(data, len(data)))
            self.assertEqual(rep["bits_mismatch_rows"], 1)
            self.assertEqual(rep["problems"], ["1 rows of bits_36.npy differ from binarising the floats with mu.npy"])

    def test_disk_guard_and_short_download(self):
        with tempfile.TemporaryDirectory() as d:
            x, _, dirs = self.setup_dirs(d)

            def never(url):
                raise AssertionError("no download expected")
            rep = self.call(dirs, never, disk_free=lambda p: 0)
            self.assertEqual(rep["problems"], ["not started: 0 bytes free, need %d" % (8 * 1024 ** 3)])
            self.assertNotIn("download", rep)
            data = npy_bytes(x)
            rep = self.call(dirs, lambda url: Resp(data, len(data) + 1))
            self.assertEqual(rep["download"]["status"], "short")
            self.assertEqual(rep["problems"], ["download: short"])
            self.assertEqual(os.listdir(dirs["tmp"]), [])


if __name__ == "__main__":
    unittest.main()
