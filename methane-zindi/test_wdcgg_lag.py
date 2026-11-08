"""Offline tests for wdcgg_lag (no network). MV2 of Munim, Inc. (made with AI agents). Apache-2.0."""
import datetime as dt
import os
import tempfile
import unittest

import wdcgg_lag as W

AS_OF = dt.date(2026, 11, 8)

PAGE_A = """<html><body><p>This data set is submitted by <b>JMA</b></p>
<table><tr><td>Hourly</td><td>ch4_mnm2029_surface-insitu_1_9999-9999_hourly</td>
<td>1994-01-01 00:00:00&nbsp;-&nbsp;2026-07-31 23:00:00</td><td>(Text: 43.53MB)</td></tr>
<tr><td>Daily</td><td>ch4_mnm2029_surface-insitu_1_9999-9999_daily</td>
<td>1994-01-01 00:00:00 - 2026-07-31 00:00:00</td></tr>
<tr><td>MET</td><td>ch4_mnm2029_surface-insitu_1_9999-9999_hourly_met</td>
<td>1994-01-01 00:00:00 - 2026-08-31 23:00:00</td></tr></table>
<p>Version 2026-09-07-0218</p></body></html>"""

PAGE_B = ("<div>submitted by AGAGE</div><ul><li>2016-08-01 00:00:00 - 2025-10-01 00:00:00 "
          "<span>ch4_rpb4036_surface-insitu_4_2024-9999_monthly</span></li>"
          "<li>2016-08-12 - 2025-10-26 <span>ch4_rpb4036_surface-insitu_4_2024-9999_event</span></li></ul>")


# layout of the real page (period cell before file name; open-ended metadata spans after the table)
PAGE_C = """<p>Version <a>2026-09-07-0218</a> (Last updated: 2026-09-16)</p>
<p>This data set is submitted by <a href="https://gaw.kishou.go.jp/search/contributor#1">JMA</a>.</p>
<table><tr><th>DL</th><th>Period</th><th>Filename</th></tr>
<tr><td>CH4</td><td>Minamitorishima</td><td>JMA</td><td>hourly</td>
<td>1994-01-01 00:00:00 - 2026-07-31 23:00:00</td><td>ch4_mnm2029_surface-insitu_1_9999-9999_hourly</td>
<td>(Text: 43.53MB ; NetCDF: 69.74MB )</td></tr>
<tr><td>daily</td><td>1994-01-01 00:00:00 - 2026-07-31 00:00:00</td>
<td>ch4_mnm2029_surface-insitu_1_9999-9999_daily</td></tr>
<tr><td>monthly</td><td>1994-01-01 00:00:00 - 2026-07-01 00:00:00</td>
<td>ch4_mnm2029_surface-insitu_1_9999-9999_monthly</td></tr>
</table>
<p>Calibration Scale</p><p>1994-01-01 00:00:00 - 9999-12-31 23:59:59: WMO CH4 X2004A</p>
<p>2024-04-01 00:00:00 - 9999-12-31 23:59:59: Picarro G2301</p>"""


def mk(network, platform, end, station="X", typ="insitu"):
    return {"network": network, "platform": platform, "type": typ, "station": station, "end": end,
            "file_id": station + end, "lag_days": (AS_OF - dt.date.fromisoformat(end)).days}


def sample_rows():
    rows = [mk("ICOS", "surface", "2026-08-23", "I%d" % i) for i in range(13)]
    rows += [mk("AGAGE", "surface", "2025-10-25", "A%d" % i) for i in range(5)]
    rows += [mk("AGAGE", "surface", "2017-02-15", "OLD")]
    rows += [mk("NOAA", "surface", "2025-12-31", "N%d" % i) for i in range(3)]
    rows += [mk("NOAA", "surface", "2025-12-24", "BRW")]
    rows += [mk("ICOS", "tower", "2026-08-20", "T%d" % i) for i in range(9)]
    rows += [mk("ICOS", "tower", "2025-05-01", "TOLD")]
    return rows


class TestParse(unittest.TestCase):
    def test_file_ids_dedup_in_order(self):
        h = ('<a href="/search/file/0001-2029-1002-01-01-9999">x</a>'
             '<a href="https://gaw.kishou.go.jp/search/file/0001-2029-1002-01-01-9999">y</a>'
             '<a href="/search/file/0004-4036-1002-01-01-2024">z</a>')
        self.assertEqual(W.file_ids(h), ["0001-2029-1002-01-01-9999", "0004-4036-1002-01-01-2024"])

    def test_name_first_layout(self):
        recs, contrib = W.parse_file_page(PAGE_A)
        self.assertEqual(contrib, "JMA")
        self.assertEqual([r["name"] for r in recs], [
            "ch4_mnm2029_surface-insitu_1_9999-9999_hourly",
            "ch4_mnm2029_surface-insitu_1_9999-9999_daily",
            "ch4_mnm2029_surface-insitu_1_9999-9999_hourly_met"])
        self.assertEqual([r["end"] for r in recs], ["2026-07-31", "2026-07-31", "2026-08-31"])
        self.assertEqual(recs[0]["start"], "1994-01-01")
        row = W.dataset_row("0001-2029-1002-01-01-9999", recs, contrib, AS_OF)
        self.assertEqual(row["end"], "2026-07-31")  # the _met file is ignored
        self.assertEqual(row["lag_days"], 100)
        self.assertEqual((row["station"], row["platform"], row["type"], row["network"]),
                         ("MNM", "surface", "insitu", "JMA"))
        self.assertEqual(row["resolutions"], ["daily", "hourly"])

    def test_range_first_layout(self):
        recs, contrib = W.parse_file_page(PAGE_B)
        self.assertEqual(contrib, "AGAGE")
        self.assertEqual([(r["name"][-7:], r["start"], r["end"]) for r in recs],
                         [("monthly", "2016-08-01", "2025-10-01"), ("9_event", "2016-08-12", "2025-10-26")])
        row = W.dataset_row("0004-4036-1002-01-01-2024", recs, contrib, AS_OF)
        self.assertEqual((row["network"], row["end"], row["lag_days"]), ("AGAGE", "2025-10-26", 378))

    def test_real_layout_ignores_open_ended_spans(self):
        recs, contrib = W.parse_file_page(PAGE_C)
        self.assertEqual(contrib, "JMA")
        self.assertEqual([r["end"] for r in recs], ["2026-07-31", "2026-07-31", "2026-07-01"])
        row = W.dataset_row("0001-2029-1002-01-01-9999", recs, contrib, AS_OF)
        self.assertEqual((row["end"], row["lag_days"], row["start"]), ("2026-07-31", 100, "1994-01-01"))
        self.assertEqual(row["resolutions"], ["daily", "hourly", "monthly"])

    def test_no_names(self):
        recs, contrib = W.parse_file_page("<p>submitted by NOAA</p><p>2020-01-01 - 2021-01-01</p>")
        self.assertEqual(recs, [])
        self.assertEqual(contrib, "NOAA")
        self.assertIsNone(W.dataset_row("0002-1-1002-01-01-1", recs, contrib, AS_OF))


class TestChecks(unittest.TestCase):
    def test_all_but_p5_hold(self):
        c = W.checks(sample_rows(), 300, 300, 290)
        self.assertTrue(c["G1"]["held"] and c["G2"]["held"])
        for k in ("P1", "P2", "P3", "P4", "P6"):
            self.assertTrue(c[k]["held"], k)
            self.assertTrue(c[k]["graded"], k)
        self.assertEqual(c["P2"]["n"], 5)
        self.assertEqual(c["P5"]["n"], 22)
        self.assertEqual(c["P5"]["median_lag_days"], 77)
        self.assertFalse(c["P5"]["held"])
        self.assertEqual((c["P6"]["n"], c["P6"]["n_in_window"]), (10, 9))

    def test_gate_failure_ungrades(self):
        c = W.checks(sample_rows(), 299, 299, 299)
        self.assertFalse(c["G1"]["held"])
        self.assertFalse(c["P1"]["graded"])

    def test_p4_fails_on_fresh_row(self):
        rows = sample_rows() + [mk("KMA", "surface", "2026-10-01", "AMY")]
        c = W.checks(rows, 300, 300, 300)
        self.assertFalse(c["P4"]["held"])
        self.assertEqual(c["P4"]["after"], [("KMA", "AMY", "2026-10-01")])

    def test_summary_and_md(self):
        rows = sample_rows()
        s = W.summarize(rows)
        g = s["ICOS | surface-insitu"]
        self.assertEqual((g["n"], g["n_active"], g["newest_end"], g["min_lag_days"],
                          g["median_lag_days_active"]), (13, 13, "2026-08-23", 77, 77))
        self.assertEqual(s["AGAGE | surface-insitu"]["n_active"], 5)
        for r in rows:
            r["url"] = "u"
        out = {"run_at_utc": "t", "as_of": "2026-11-08", "n_ids": 300, "n_rows": len(rows),
               "fetch_errors": [], "summary": s, "checks": W.checks(rows, 300, 300, 300), "rows": rows}
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.md")
            W.write_md(p, out)
            with open(p, encoding="utf-8") as f:
                txt = f.read()
        self.assertIn("| ICOS | surface-insitu | 13 | 13 | 2026-08-23 | 77 | 77 |", txt)


if __name__ == "__main__":
    unittest.main()
