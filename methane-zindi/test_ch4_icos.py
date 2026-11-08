"""Offline tests for ch4_icos.py (no network). MV2 of Munim, Inc. (made with AI agents working in his
name). Apache-2.0."""
import math
import unittest
from datetime import date, datetime, timedelta, timezone

import ch4_icos as m

HEAD = '"station","time_ch4","ch4","latitude","longitude","ch4_qc_flag","sampling_height"\n'


def utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


class FakeFit:
    phi = {k: 0.5 for k in range(1, m.MAX_LAG + 1)}

    def __call__(self, d):
        return 1900.0


class TestParse(unittest.TestCase):
    def test_parse_time(self):
        self.assertEqual(m.parse_time("2026-11-01 00:30:00.000000000"), utc(2026, 11, 1, 0, 30))
        self.assertEqual(m.parse_time("2026-11-01T23:30:00Z"), utc(2026, 11, 1, 23, 30))

    def test_parse_csv(self):
        text = (HEAD
                + '"CBW207",2026-11-01 00:30:00.000000000,2080.97,51.9703,4.9264,"U",207\n'
                + '"CBW207",2026-11-01 01:30:00.000000000,,51.9703,4.9264,"U",207\n'
                + '"CBW207",2026-11-01 02:30:00.000000000,nan,51.9703,4.9264,"U",207\n'
                + '"LIN2",2026-11-01 03:30:00.000000000,-999,52.1,14.1,"O",2.5\n')
        rows, stats = m.parse_csv(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], ("CBW207", utc(2026, 11, 1, 0, 30), 2080.97, "U", 207.0))
        self.assertEqual(stats["rows"], 1)
        self.assertEqual(stats["skipped"], 3)
        self.assertEqual(stats["lines"], 5)

    def test_parse_csv_header_only_and_missing_column(self):
        rows, stats = m.parse_csv(HEAD)
        self.assertEqual(rows, [])
        with self.assertRaises(ValueError):
            m.parse_csv('"station","time_ch4","ch4"\n')
        with self.assertRaises(ValueError):
            m.parse_csv("")


class TestSites(unittest.TestCase):
    def test_site_code(self):
        self.assertEqual(m.site_code("JFJ13"), "JFJ")
        self.assertEqual(m.site_code("LIN2"), "LIN")
        self.assertEqual(m.site_code("SMR125"), "SMR")

    def test_pick_top(self):
        got = m.pick_top({"LIN2": 2.5, "LIN98": 98.0, "LIN40": 40.0, "CBW207": 207.0, "JFJ5": 5.0, "JFJ13": 13.9})
        self.assertEqual(got, {"LIN": "LIN98", "CBW": "CBW207", "JFJ": "JFJ13"})

    def test_census(self):
        rows = [("CBW207", utc(2026, 11, 5, 23, 30), 2000.0, "U", 207.0),
                ("CBW207", utc(2026, 11, 4, 0, 30), 2001.0, "U", 207.0),
                ("LIN98", utc(2026, 11, 6, 11, 30), 1990.0, "U", 98.0)]
        c = m.census(rows, utc(2026, 11, 8, 0, 0))
        self.assertEqual(c["CBW207"]["n"], 2)
        self.assertEqual(c["CBW207"]["last"], "2026-11-05T23:30:00Z")
        self.assertEqual(c["CBW207"]["lag_days"], 2.021)
        self.assertEqual(c["LIN98"]["lag_days"], 1.521)

    def test_daily_means(self):
        rows = [("X1", utc(2026, 1, 1, h, 30), 10.0, "O", 1.0) for h in range(12)]
        rows.append(("X1", utc(2026, 1, 1, 0, 30), 10.0, "O", 1.0))  # duplicate hour
        rows += [("X1", utc(2026, 1, 2, h, 30), 20.0 + h, "O", 1.0) for h in range(11)]
        d = m.daily_means(rows)
        self.assertEqual(d, {date(2026, 1, 1): 10.0})

    def test_chunks(self):
        stop = date(2026, 11, 9)
        self.assertEqual(m.chunks(2025, stop, 1), [(date(2025, 1, 1), date(2026, 1, 1))])
        self.assertEqual(m.chunks(2026, stop, 1), [(date(2026, 1, 1), date(2026, 11, 9))])
        q = m.chunks(2026, stop, 4)
        self.assertEqual(q, [(date(2026, 1, 1), date(2026, 4, 1)), (date(2026, 4, 1), date(2026, 7, 1)),
                             (date(2026, 7, 1), date(2026, 10, 1)), (date(2026, 10, 1), date(2026, 11, 9))])
        mo = m.chunks(2026, stop, 12)
        self.assertEqual(len(mo), 11)
        self.assertEqual(mo[-1], (date(2026, 11, 1), date(2026, 11, 9)))

    def test_truncated(self):
        self.assertFalse(m.truncated([("Content-Type", "text/csv"), ("X-Truncated", "false")]))
        self.assertTrue(m.truncated([("X-Truncated", "true")]))
        self.assertTrue(m.truncated([("X-DataPassport", '{"rows": 5, "truncated": true}')]))
        self.assertFalse(m.truncated([("X-DataPassport", '{"rows": 5, "truncated": false}')]))

    def test_build_url(self):
        u = m.build_url({"id": m.VAR_ID, "station": "CBW207", "start": "2021-01-01"})
        self.assertTrue(u.startswith("https://zarr.icos-cp.eu/query?"))
        self.assertIn("id=icos-obspack.ch4.ch4", u)
        self.assertIn("station=CBW207", u)
        self.assertIn("start=2021-01-01", u)


class TestForecasts(unittest.TestCase):
    def test_forecasts_full(self):
        t = date(2025, 3, 10)
        series = {t - timedelta(days=k): 1910.0 - k for k in range(7)}
        fc = m.forecasts(series, t, FakeFit())
        self.assertEqual(fc["P0"], 1910.0)
        self.assertAlmostEqual(fc["M7"], 1907.0)
        self.assertEqual(fc["C"], 1900.0)
        self.assertAlmostEqual(fc["D0"], 1905.0)
        self.assertEqual(fc["P2"], 1908.0)
        self.assertAlmostEqual(fc["D2"], 1904.0)

    def test_forecasts_missing_origin_day(self):
        t = date(2025, 3, 10)
        series = {t - timedelta(days=k): 1910.0 - k for k in range(1, 7)}
        fc = m.forecasts(series, t, FakeFit())
        self.assertEqual(fc["P0"], 1909.0)
        self.assertAlmostEqual(fc["M7"], 1906.5)
        self.assertAlmostEqual(fc["D0"], 1904.5)
        self.assertEqual(fc["P2"], 1908.0)

    def test_forecasts_none_without_latent_value(self):
        t = date(2025, 3, 10)
        series = {t: 1.0, t - timedelta(days=1): 1.0, t - timedelta(days=5): 1.0}
        self.assertIsNone(m.forecasts(series, t, FakeFit()))


def smooth(d):
    k = (d - date(2021, 1, 1)).days
    return 1900.0 + 0.01 * k + 10.0 * math.sin(2 * math.pi * k / 365.25)


class TestEvaluate(unittest.TestCase):
    def test_fit_recovers_smooth_series(self):
        series = {}
        d = date(2021, 1, 1)
        while d < date(2025, 1, 1):
            series[d] = smooth(d)
            d += timedelta(days=1)
        f = m.Fit(series, 2025)
        self.assertEqual(f.n, 1461)
        self.assertAlmostEqual(f(date(2025, 3, 1)), smooth(date(2025, 3, 1)), places=5)
        for k in range(1, m.MAX_LAG + 1):
            self.assertTrue(0.0 <= f.phi[k] <= 1.0)

    def test_fit_too_few(self):
        with self.assertRaises(ValueError):
            m.Fit({date(2024, 1, 1): 1.0}, 2025)

    def test_evaluate_smooth(self):
        series = {}
        d = date(2021, 1, 1)
        while d <= date(2026, 6, 30):
            series[d] = smooth(d)
            d += timedelta(days=1)
        e = m.evaluate_site(series)
        self.assertEqual(e["origins"], 541)
        self.assertTrue(e["included"])
        self.assertLess(e["methods"]["C"]["rmse"], 1e-3)
        self.assertGreater(e["methods"]["P0"]["rmse"], 0.1)
        self.assertEqual(set(e["fits"]), {"2025", "2026"})
        self.assertEqual(e["fits"]["2025"]["origins"], 365)
        self.assertEqual(e["fits"]["2026"]["origins"], 176)

    def test_evaluate_empty(self):
        self.assertFalse(m.evaluate_site({})["included"])


def site(p0=10.0, c=8.0, d0=7.6, gain=0.05, cost=0.0263, phi=0.3, lag=1.0, included=True):
    meth = {k: {"rmse": v} for k, v in
            {"P0": p0, "M7": 9.0, "C": c, "D0": d0, "P2": 10.5, "D2": 7.8}.items()}
    return {"included": included, "methods": meth, "d0_gain_vs_c": gain, "latency_cost": cost,
            "mean_phi5": phi, "proxy_lag_days": lag}


class TestGrade(unittest.TestCase):
    def test_all_hold(self):
        sites = {"S%02d" % i: site() for i in range(25)}
        g = m.grade(sites)
        for k in ("Q1_at_least_25_sites", "Q2_D0_beats_P0_at_80pct", "Q3_C_beats_P0_at_majority",
                  "Q4_median_D0_gain_over_C_in_0_to_0.10", "Q5_median_phi5_in_0.1_to_0.5",
                  "Q6_median_latency_cost_below_0.05", "F1_at_least_25_sites_fresh_within_4d"):
            self.assertTrue(g[k], k)
        self.assertEqual(g["included_sites"], 25)
        self.assertEqual(g["median_proxy_lag_days"], 1.0)

    def test_failures(self):
        sites = {"S%02d" % i: site() for i in range(20)}
        sites.update({"T%02d" % i: site(p0=7.0, c=8.0, d0=7.5, gain=0.2, cost=0.1, phi=0.7, lag=5.0)
                      for i in range(4)})
        sites["U00"] = site(included=False, lag=None)
        g = m.grade(sites)
        self.assertEqual(g["included_sites"], 24)
        self.assertFalse(g["Q1_at_least_25_sites"])
        self.assertEqual(g["sites_D0_beats_P0"], 20)
        self.assertTrue(g["Q2_D0_beats_P0_at_80pct"])
        self.assertEqual(g["sites_C_beats_P0"], 20)
        self.assertEqual(g["fresh_sites"], 20)
        self.assertFalse(g["F1_at_least_25_sites_fresh_within_4d"])
        self.assertEqual(g["median_d0_gain_vs_c"], 0.05)


if __name__ == "__main__":
    unittest.main()
