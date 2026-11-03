"""Tests for ch4_baselines (standard library only). MV2 of Munim, Inc. Apache-2.0."""
import math
import unittest
from datetime import date, timedelta

import ch4_baselines as cb

COMMENT_HEADER = """# header_lines : 2
# data_fields: site_code year month day hour minute second value qcflag
BRW 2020 1 1 0 0 0 1900.50 ...
BRW 2020 1 2 0 0 0 -999.99 *..
BRW 2020 1 3 0 0 0 1901.00 N..
BRW 2020 1 4 0 0 0 1902.00 .C.
BRW 2020 1 4 0 0 0 1999.00 ...
"""

PLAIN_HEADER = """site_code year month day value qcflag
MLO 2021 5 6 1890.1 ...
"""


def daily(start, end, fn):
    out, d = {}, start
    while d <= end:
        out[d] = fn(d)
        d += timedelta(days=1)
    return out


class ParseTests(unittest.TestCase):
    def test_comment_header(self):
        s, st = cb.parse_daily(COMMENT_HEADER)
        self.assertEqual(sorted(s), [date(2020, 1, 1), date(2020, 1, 4)])
        self.assertEqual(s[date(2020, 1, 4)], 1902.0)
        self.assertEqual((st["missing"], st["rejected"], st["duplicates"], st["kept"]), (1, 1, 1, 2))
        self.assertEqual(st["data_lines"], 5)

    def test_plain_header(self):
        s, st = cb.parse_daily(PLAIN_HEADER)
        self.assertEqual(s, {date(2021, 5, 6): 1890.1})
        self.assertEqual(st["columns"][0], "site_code")

    def test_no_header_raises(self):
        with self.assertRaises(ValueError):
            cb.parse_daily("BRW 2020 1 1 1900.0 ...\n")

    def test_missing_value_column_raises(self):
        with self.assertRaises(ValueError):
            cb.parse_daily("site_code year month day qcflag\nBRW 2020 1 1 ...\n")


class FitTests(unittest.TestCase):
    def test_solve(self):
        x = cb.solve([[2.0, 1.0], [1.0, 3.0]], [3.0, 5.0])
        self.assertAlmostEqual(x[0], 0.8)
        self.assertAlmostEqual(x[1], 1.4)

    def test_fit_recovers_trend_and_season(self):
        d0 = date(2016, 1, 1)

        def f(d):
            x = (d - d0).days / 365.25
            return 1800.0 + 10.0 * x + 5.0 * math.sin(2 * math.pi * x)

        s = daily(d0, date(2019, 12, 31), f)
        fit = cb.Fit(s, 2020)
        self.assertEqual(fit.n, len(s))
        for d in (date(2018, 3, 1), date(2020, 6, 1)):
            self.assertAlmostEqual(fit(d), f(d), places=5)
        self.assertEqual(fit.phi, min(1.0, max(0.0, fit.phi_raw)))

    def test_fit_too_few(self):
        s = daily(date(2019, 1, 1), date(2019, 12, 31), lambda d: 1900.0)
        with self.assertRaises(ValueError):
            cb.Fit(s, 2020)

    def test_phi_from_alternating_residuals(self):
        # residual sign flips every 5 days -> lag-5 regression is negative -> phi clipped to 0
        d0 = date(2016, 1, 1)
        s = daily(d0, date(2019, 12, 31), lambda d: 1900.0 + (3.0 if ((d - d0).days // 5) % 2 else -3.0))
        fit = cb.Fit(s, 2020)
        self.assertLess(fit.phi_raw, 0)
        self.assertEqual(fit.phi, 0.0)


class ForecastTests(unittest.TestCase):
    class FlatFit:
        phi = 0.5

        def __call__(self, d):
            return 1900.0

    def test_values_and_fallback(self):
        t = date(2021, 3, 10)
        s = {t - timedelta(days=k): 1900.0 + k for k in (1, 2, 3, 4)}  # origin day itself missing
        fc = cb.forecasts(s, t, self.FlatFit())
        self.assertEqual(fc["P"], 1901.0)
        self.assertAlmostEqual(fc["M7"], 1902.5)
        self.assertEqual(fc["C"], 1900.0)
        self.assertEqual(fc["S"], 1901.0)
        self.assertEqual(fc["D"], 1900.5)

    def test_none_when_no_recent_value(self):
        t = date(2021, 3, 10)
        s = {t - timedelta(days=k): 1900.0 for k in (3, 4, 5, 6)}
        self.assertIsNone(cb.forecasts(s, t, self.FlatFit()))

    def test_none_when_too_few_in_window(self):
        t = date(2021, 3, 10)
        s = {t: 1900.0, t - timedelta(days=1): 1900.0}
        self.assertIsNone(cb.forecasts(s, t, self.FlatFit()))


class EvaluateTests(unittest.TestCase):
    def test_constant_series(self):
        s = daily(date(2015, 1, 1), date(2022, 12, 31), lambda d: 1900.0)
        r = cb.evaluate_site(s)
        self.assertEqual(r["origins"], 725)
        self.assertTrue(r["included"])
        self.assertEqual(sorted(r["fits"]), ["2021", "2022"])
        self.assertEqual(r["fits"]["2021"]["origins"] + r["fits"]["2022"]["origins"], 725)
        for m in cb.METHODS:
            self.assertLess(r["methods"][m]["rmse"], 1e-6)
        self.assertIsNone(r["methods"]["D"]["skill_vs_P"])

    def test_short_series_excluded(self):
        s = daily(date(2017, 1, 1), date(2021, 3, 1), lambda d: 1900.0)
        r = cb.evaluate_site(s)
        self.assertFalse(r["included"])
        self.assertGreater(r["origins"], 0)
        self.assertIn("reason", r)

    def test_empty(self):
        self.assertFalse(cb.evaluate_site({})["included"])


class GradeTests(unittest.TestCase):
    def site(self, rm, best, phi):
        return {"included": True, "best": best, "fits": {"2021": {"phi": phi, "origins": 10}},
                "methods": {m: {"rmse": v, "skill_vs_P": round(1 - v / rm["P"], 4)} for m, v in rm.items()}}

    def test_grade(self):
        a = self.site({"P": 10.0, "M7": 9.5, "C": 12.0, "S": 10.5, "D": 8.0}, "D", 0.4)
        b = self.site({"P": 10.0, "M7": 8.0, "C": 9.5, "S": 10.5, "D": 9.5}, "M7", 0.6)
        c = {"included": False}
        g = cb.grade({"a": a, "b": b, "c": c})
        self.assertEqual(g["included_sites"], ["a", "b"])
        self.assertTrue(g["P1_at_least_two_sites"])
        self.assertTrue(g["P2_D_beats_P_every_site"])
        self.assertTrue(g["P3_D_at_most_C_every_site"])
        self.assertFalse(g["P4_D_best_every_site"])
        self.assertFalse(g["P5_D_gain_10pct_every_site"])
        self.assertEqual(g["mean_phi"], 0.5)
        self.assertTrue(g["P6_mean_phi_between_0.2_and_0.8"])

    def test_grade_none_included(self):
        g = cb.grade({"a": {"included": False}})
        self.assertFalse(g["P1_at_least_two_sites"])
        self.assertNotIn("P2_D_beats_P_every_site", g)


class MarkdownTests(unittest.TestCase):
    def test_markdown_rows(self):
        s = daily(date(2015, 1, 1), date(2022, 12, 31), lambda d: 1900.0)
        e = cb.evaluate_site(s)
        rep = {"version": cb.VERSION, "sites": {"x": e, "y": {"error": "URLError: boom", "included": False}},
               "checks": cb.grade({"x": e})}
        md = cb.to_markdown(rep)
        self.assertEqual(md.count("| x | 725 |"), 5)
        self.assertIn("URLError: boom", md)


if __name__ == "__main__":
    unittest.main()
