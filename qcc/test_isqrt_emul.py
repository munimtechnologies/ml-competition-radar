"""Fake-data and small-range tests for isqrt_emul.py (numpy only). Apache-2.0."""
import json
import math
import os
import tempfile
import unittest

import numpy as np

import isqrt_emul as E


class Basics(unittest.TestCase):
    def test_version_and_range(self):
        self.assertEqual(E.VERSION, "0.1.0")
        self.assertEqual(E.X_MAX, 3133452)
        self.assertEqual(E.NBITS, 22)

    def test_normalize_edges(self):
        x = np.array([1, 2, 3, 4, 2 ** 20 - 1, 2 ** 20, E.X_MAX], dtype=np.int64)
        xn, s = E.normalize(x)
        self.assertEqual(s.tolist(), [10, 10, 10, 9, 1, 0, 0])
        self.assertTrue(np.all(xn == x << (2 * s)))

    def test_normalize_random(self):
        x = np.random.default_rng(1).integers(1, E.X_MAX + 1, 5000)
        xn, s = E.normalize(x)
        self.assertTrue(np.all(xn >= 2 ** 20) and np.all(xn < 2 ** 22))
        self.assertTrue(np.all(xn == x << (2 * s)))

    def test_width(self):
        self.assertEqual(E.width(np.array([0, 5])), 3)
        self.assertEqual(E.width(np.array([-1, 3])), 3)
        self.assertEqual(E.width(np.array([-4, 3])), 3)
        self.assertEqual(E.width(np.array([-5, 3])), 4)


class Tmul(unittest.TestCase):
    def test_exact_without_truncation(self):
        rng = np.random.default_rng(2)
        a = rng.integers(-2 ** 20, 2 ** 20, 3000)
        b = rng.integers(0, 2 ** 12, 3000)
        self.assertTrue(np.array_equal(E.tmul(a, 10, b, 12, 12, 22), a * b))

    def test_floor_bound(self):
        rng = np.random.default_rng(3)
        a = rng.integers(-2 ** 20, 2 ** 20, 3000)
        b = rng.integers(0, 2 ** 12, 3000)
        got = E.tmul(a, 10, b, 12, 12, 8)
        exact = a.astype(np.float64) * b / 2.0 ** 14
        lost = exact - got
        self.assertTrue(np.all(lost >= 0) and np.all(lost < 12))

    def test_big_shift_is_safe(self):
        self.assertEqual(int(E.tmul(np.array([5]), 80, np.array([1]), 0, 1, 0)[0]), 0)
        self.assertEqual(int(E.tmul(np.array([-5]), 80, np.array([1]), 0, 1, 0)[0]), -1)


class Costs(unittest.TestCase):
    def test_mac_cost_full_rows(self):
        self.assertEqual(E.mac_cost(10, 0, 10, 12, 4, 4), (40, 48, 10))

    def test_mac_cost_truncated(self):
        # rows i = 0..3, drop = 3 - i bits: kept 7, 8, 9, 10
        self.assertEqual(E.mac_cost(10, 10, 11, 12, 4, 4), (34, 48, 10))

    def test_rotation_price_matches_reference(self):
        # 37 rotations and a 2^-35.69 turn margin give the reference's ~27.28 T each
        self.assertAlmostEqual(E.rotation_t(2.0 ** -35.69, 37), 27.28, places=2)
        self.assertIsNone(E.rotation_t(0.0, 37))

    def test_qrom(self):
        self.assertEqual(E.qrom_cost(256), (255, 32))
        self.assertEqual(E.qrom_cost(3), (2, 4))


class Reference(unittest.TestCase):
    def test_tables(self):
        c = E.ref_tables(17)
        self.assertEqual(int(c[0][0]), int(round(E.A[0] * 2 ** 17)))
        self.assertEqual(int(c[1][3]), int(round(E.B[1] / (2 * math.sqrt(2)) * 2 ** 17)))

    def test_float_first_guess(self):
        # the four cubic cases in floating point, before any truncation
        for lo, hi, coef, off, sc in ((1.0, 1.5, E.A, 1.0, 1.0), (1.5, 2.0, E.B, 1.5, 1.0),
                                      (2.0, 3.0, E.A, 2.0, 2.0), (3.0, 4.0, E.B, 3.0, 2.0)):
            X = np.linspace(lo, hi, 501)[:-1]
            u = (X - off) / sc
            p = coef[0] - coef[1] * u + coef[2] * u ** 2 - coef[3] * u ** 3
            p = p / math.sqrt(sc)
            self.assertLess(float(np.max(np.abs(p * np.sqrt(X) - 1))), 2.0 ** -12)

    def test_pipeline_sane_on_sample(self):
        x = np.concatenate([np.arange(1, 300), np.random.default_rng(4).integers(1, E.X_MAX + 1, 3000),
                            np.array([E.X_MAX, 2588411])]).astype(np.int64)
        y, F, mid = E.ref_pipeline(x)
        self.assertEqual(F, 40)
        self.assertLess(float(np.max(E.rel_err(y, F, x))), 2.0 ** -20)


class Poly(unittest.TestCase):
    def test_layout(self):
        lay = E.Layout(6, 5)
        self.assertEqual((lay.D, lay.L), (16, 96))
        x = np.random.default_rng(5).integers(1, E.X_MAX + 1, 4000)
        xn, _ = E.normalize(x)
        seg, t = lay.seg_t(xn)
        self.assertTrue(np.all(seg >= 0) and np.all(seg < lay.L))
        X = xn / 2.0 ** 20
        for j in np.unique(seg)[:40]:
            lo, hi, base = lay.interval(int(j))
            m = seg == j
            self.assertTrue(np.all(X[m] >= lo) and np.all(X[m] < hi))
            self.assertTrue(np.allclose(X[m] - base, t[m] / 2.0 ** 20, atol=0))
        with self.assertRaises(ValueError):
            E.Layout(3, 5)

    def test_fit_quadratic(self):
        lay = E.Layout(7, 6)
        c = E.fit(lay, 2)
        for j in (0, 77, lay.L - 1):
            lo, hi, base = lay.interval(j)
            X = np.linspace(lo, hi, 200)
            t = X - base
            p = c[0, j] + c[1, j] * t + c[2, j] * t * t
            self.assertLess(float(np.max(np.abs(p * np.sqrt(X) - 1))), 2.0 ** -25)

    def test_design_small_range(self):
        x = E.all_x(20000)
        d = E.Design(2, 7, 6, x)
        st, cint, accs = d.evaluate([30, 26, 20])
        self.assertEqual(st["fails"], 0)
        self.assertLess(st["worst_rel"], 2.0 ** -24)
        r = d.search(f_start=30)
        self.assertTrue(r["feasible"])
        self.assertTrue(all(6 <= v <= 30 for v in r["f"]))
        self.assertGreater(r["cost"]["Q"], 22)


class Run(unittest.TestCase):
    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "o", "emul.json")
            self.assertEqual(E.main(["--out", out, "--x-max", "4000", "--grid", "2,6"]), 0)
            with open(out, encoding="utf-8") as fh:
                rep = json.load(fh)
            self.assertEqual(rep["n_inputs"], 4000)
            self.assertIn("model", rep["reference"])
            self.assertEqual(len(rep["designs"]), 2)


if __name__ == "__main__":
    unittest.main()
