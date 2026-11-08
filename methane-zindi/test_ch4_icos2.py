"""Offline tests for ch4_icos2 (no network). MV2 of Munim, Inc. (made with AI agents). Apache-2.0."""
import unittest
from datetime import date, timedelta

import ch4_icos2 as m

D0 = date(2021, 1, 1)


def linear(start, end, a=1900.0, per_day=0.01):
    out, d = {}, start
    while d <= end:
        out[d] = a + per_day * (d - D0).days
        d += timedelta(days=1)
    return out


class Const:
    def __init__(self, v):
        self.v = v

    def __call__(self, d):
        return self.v


class TestPieces(unittest.TestCase):
    def test_fit_end(self):
        self.assertEqual(m.fit_end(date(2025, 3, 1)), date(2025, 2, 27))
        self.assertEqual(m.fit_end(date(2025, 3, 31)), date(2025, 2, 27))
        self.assertEqual(m.fit_end(date(2025, 1, 15)), date(2024, 12, 30))

    def test_level(self):
        tp = date(2025, 6, 30)
        s = {tp - timedelta(days=k): 10.0 for k in range(12)}
        self.assertAlmostEqual(m.level(s, tp, Const(7.0)), 3.0)
        s9 = {tp - timedelta(days=k): 10.0 for k in range(9)}
        self.assertIsNone(m.level(s9, tp, Const(7.0)))
        # days older than L_DAYS are ignored
        s9[tp - timedelta(days=40)] = 10.0
        s9[tp - timedelta(days=30)] = 10.0
        self.assertIsNone(m.level(s9, tp, Const(7.0)))

    def test_rfit_linear_and_no_leak(self):
        end = date(2025, 2, 27)
        s = linear(D0, date(2025, 12, 31))
        r = m.RFit(s, end)
        tgt = end + timedelta(days=30)
        self.assertAlmostEqual(r(tgt), 1900.0 + 0.01 * (tgt - D0).days, places=6)
        s2 = dict(s)
        for k in range(0, 300):
            s2[end + timedelta(days=k)] = 99999.0
        self.assertAlmostEqual(m.RFit(s2, end)(tgt), r(tgt), places=9)
        with self.assertRaises(ValueError):
            m.RFit(linear(date(2024, 10, 1), date(2025, 6, 1)), end)

    def test_forecasts2_linear_exact(self):
        s = linear(D0, date(2025, 12, 31))
        t = date(2025, 6, 15)
        f = m.base.Fit(s, 2025)
        r = m.RFit(s, m.fit_end(t))
        fc = m.forecasts2(s, t, f, r)
        truth = s[t + timedelta(days=5)]
        for k in ("C", "D0", "D2", "Cr", "Dr", "Dr2", "L30"):
            self.assertAlmostEqual(fc[k], truth, places=5, msg=k)

    def test_evaluate_site_break(self):
        # slope 12 ppb/yr through 2024, then flat through 2025: C overshoots, the fixes less so
        s = linear(D0, date(2024, 12, 31), per_day=12.0 / 365.25)
        flat = s[date(2024, 12, 31)]
        d = date(2025, 1, 1)
        while d <= date(2025, 12, 31):
            s[d] = flat
            d += timedelta(days=1)
        e = m.evaluate_site(s)
        self.assertEqual(e["origins"], 360)
        self.assertTrue(e["included"])
        b = {k: v["bias"] for k, v in e["methods"].items()}
        self.assertGreater(b["C"], 3.0)
        self.assertLess(b["Cr"], b["C"])
        self.assertGreater(b["L30"], 0.0)
        self.assertLess(b["L30"], 1.0)
        self.assertGreater(e["gain_l30_vs_c"], 0.5)


def site(c, cr, d0, dr, l30, gdr, lat, included=True):
    return {"included": included, "gain_dr_vs_d0": gdr, "latency_cost_dr": lat,
            "methods": {"C": {"rmse": c[0], "bias": c[1]}, "Cr": {"rmse": cr[0], "bias": cr[1]},
                        "D0": {"rmse": d0, "bias": 0.0}, "Dr": {"rmse": dr, "bias": 0.0},
                        "D2": {"rmse": d0, "bias": 0.0}, "Dr2": {"rmse": dr, "bias": 0.0},
                        "L30": {"rmse": l30, "bias": 0.0}}}


class TestGrade(unittest.TestCase):
    def sites(self):
        return {"A": site((10, 6), (8, 2), 9, 8, 9, 0.1111, 0.01),
                "B": site((20, 8), (19, 3), 19, 18, 21, 0.0526, 0.02),
                "C": site((30, 4), (31, 1), 29, 29.5, 29, -0.0172, 0.03),
                "D": site((40, 10), (38, 4), 39, 37, 38, 0.0513, 0.06),
                "E": site((1, 9), (1, 9), 1, 9, 1, -1.0, 9.0, included=False)}

    def test_all_hold(self):
        g = m.grade(self.sites(), clean_n=2)
        self.assertEqual(g["included_sites"], 4)
        self.assertEqual(g["median_bias"]["C"], 7.0)
        self.assertEqual(g["median_bias"]["Cr"], 2.5)
        self.assertEqual(g["sites_C_bias_positive"], 4)
        self.assertTrue(g["context_B0_median_C_bias_at_least_5"])
        self.assertTrue(g["R1_median_Cr_bias_below_half_of_C"])
        self.assertEqual(g["sites_Cr_beats_C"], 3)
        self.assertTrue(g["R2_Cr_beats_C_at_75pct"])
        self.assertEqual(g["sites_Dr_beats_D0"], 3)
        self.assertTrue(g["R3_Dr_beats_D0_at_75pct"])
        self.assertAlmostEqual(g["median_gain_dr_vs_d0"], 0.05195, places=3)
        self.assertTrue(g["R4_median_gain_dr_vs_d0_at_least_0.02"])
        self.assertEqual(g["clean_sites"], ["A", "B"])
        self.assertAlmostEqual(g["clean_median_gain_dr_vs_d0"], 0.08185, places=3)
        self.assertTrue(g["R5_clean_median_gain_dr_vs_d0_at_least_0.05"])
        self.assertEqual(g["sites_L30_beats_C"], 3)
        self.assertTrue(g["R6_L30_beats_C_at_majority"])
        self.assertAlmostEqual(g["median_latency_cost_dr"], 0.025, places=4)
        self.assertTrue(g["R7_median_latency_cost_dr_below_0.05"])

    def test_failures(self):
        s = self.sites()
        s["A"]["methods"]["Cr"]["rmse"] = 11
        s["B"]["methods"]["Cr"]["bias"] = 9
        s["D"]["methods"]["Cr"]["bias"] = 9
        g = m.grade(s, clean_n=2)
        self.assertEqual(g["sites_Cr_beats_C"], 2)
        self.assertFalse(g["R2_Cr_beats_C_at_75pct"])
        self.assertFalse(g["R1_median_Cr_bias_below_half_of_C"])

    def test_empty(self):
        self.assertEqual(m.grade({}), {"included_sites": 0})


if __name__ == "__main__":
    unittest.main()
