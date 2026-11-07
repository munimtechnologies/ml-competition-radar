"""Offline tests for ch4_latency.py (no network). MV2 of Munim, Inc. Apache-2.0."""
import io
import json
import unittest
import zipfile
from datetime import datetime, timezone

import ch4_latency as m

UTC = timezone.utc
NOW = datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
S = "http://meta.icos-cp.eu/resources/stations/"
O = "https://meta.icos-cp.eu/objects/"


def rows():
    return [
        {"dobj": O + "aaa", "station": S + "AS_ZEP", "stationId": "ZEP", "stationName": "Zeppelin",
         "samplingHeight": "15.0", "timeEnd": "2026-11-06T23:00:00Z", "submTime": "2026-11-07T10:10:00Z",
         "fileName": "f1"},
        {"dobj": O + "bbb", "station": S + "AS_ZEP", "stationId": "ZEP", "stationName": "Zeppelin",
         "samplingHeight": "15.0", "timeEnd": "2025-03-31T23:00:00Z", "submTime": "2025-04-01T10:00:00Z"},
        {"dobj": O + "ccc", "station": S + "AS_JFJ", "samplingHeight": "13.9",
         "timeEnd": "2026-09-01T23:00:00Z", "submTime": "2026-09-02T10:00:00Z"},
        {"dobj": O + "ddd", "station": S + "AS_SAC", "samplingHeight": "100.0",
         "timeEnd": "2026-10-25T00:00:00Z", "submTime": "2026-10-25T12:00:00Z"},
    ]


class TestTimeAndStats(unittest.TestCase):
    def test_parse_time(self):
        self.assertEqual(m.parse_time("2023-07-03T10:15:17.325Z"),
                         datetime(2023, 7, 3, 10, 15, 17, 325000, tzinfo=UTC))
        self.assertEqual(m.parse_time("2026-01-01T00:00:00"), datetime(2026, 1, 1, tzinfo=UTC))

    def test_median(self):
        self.assertEqual(m.median([3, 1, 2]), 2)
        self.assertEqual(m.median([4, 1, 3, 2]), 2.5)
        self.assertIsNone(m.median([]))


class TestSparql(unittest.TestCase):
    def test_json(self):
        body = json.dumps({"head": {"vars": ["dobj", "station", "x"]},
                           "results": {"bindings": [{"dobj": {"type": "uri", "value": "u1"},
                                                     "station": {"type": "uri", "value": "s1"}}]}}).encode()
        self.assertEqual(m.parse_sparql(body), [{"dobj": "u1", "station": "s1"}])

    def test_csv(self):
        body = "dobj,station,samplingHeight\r\nu1,s1,\r\nu2,s2,5.0\r\n"
        self.assertEqual(m.parse_sparql(body), [{"dobj": "u1", "station": "s1"},
                                                {"dobj": "u2", "station": "s2", "samplingHeight": "5.0"}])

    def test_xml(self):
        body = ('<?xml version="1.0"?><sparql xmlns="http://www.w3.org/2005/sparql-results#">'
                '<head><variable name="dobj"/></head><results><result>'
                '<binding name="dobj"><uri>u1</uri></binding>'
                '<binding name="h"><literal datatype="x">5.0</literal></binding>'
                '</result></results></sparql>')
        self.assertEqual(m.parse_sparql(body), [{"dobj": "u1", "h": "5.0"}])


class TestStations(unittest.TestCase):
    def test_table(self):
        t = m.station_table(rows(), NOW)
        self.assertEqual(list(t), ["AS_JFJ", "AS_SAC", "AS_ZEP"])
        z = t["AS_ZEP"]
        self.assertEqual(z["objects"], 2)
        self.assertEqual(z["heights"], [15.0])
        self.assertEqual(z["dobj"], O + "aaa")
        self.assertEqual(z["time_end"], "2026-11-06T23:00:00Z")
        self.assertEqual(z["file_name"], "f1")
        self.assertEqual(z["lag_days"], 0.542)
        self.assertEqual(z["publish_delay_days"], 0.465)
        self.assertTrue(z["live"])
        self.assertFalse(z["stale"])
        self.assertEqual(t["AS_JFJ"]["lag_days"], 66.542)
        self.assertTrue(t["AS_JFJ"]["stale"])
        self.assertFalse(t["AS_JFJ"]["live"])
        self.assertEqual(t["AS_SAC"]["lag_days"], 13.5)
        self.assertFalse(t["AS_SAC"]["live"])
        self.assertFalse(t["AS_SAC"]["stale"])
        self.assertEqual(t["AS_SAC"]["publish_delay_days"], 0.5)

    def test_summary(self):
        s = m.summarize(m.station_table(rows(), NOW))
        self.assertEqual(s, {"stations": 3, "live": 1, "stale": 1, "lagging_7_to_30_days": 1,
                             "median_lag_live_days": 0.542, "median_publish_delay_live_days": 0.465})

    def test_pick_sample(self):
        r = rows() + [{"dobj": O + "eee", "station": S + "AS_ABC", "timeEnd": "2026-11-06T23:00:00Z",
                       "submTime": "2026-11-07T10:00:00Z"}]
        t = m.station_table(r, NOW)
        self.assertEqual([e["station"] for e in m.pick_sample(t, 5)], ["AS_ABC", "AS_ZEP"])
        self.assertEqual([e["station"] for e in m.pick_sample(t, 1)], ["AS_ABC"])
        self.assertIsNone(t["AS_ABC"]["height"])
        self.assertEqual(t["AS_ABC"]["heights"], [])


ATC = """# HEADER LINES: 4
# TITLE: test
#Site;SamplingHeight;Year;Month;Day;Hour;Minute;DecimalDate;ch4;Stdev;NbPoints;Flag
ZEP;15.0;2026;11;06;21;00;2026.85;1990.12;1.2;20;O
ZEP;15.0;2026;11;06;22;00;2026.85;-999.99;-9.99;0;N
ZEP;15.0;2026;11;06;23;00;2026.85;-999.99;-9.99;0;N
ZEP;15.0;2026;11
"""


class TestAtc(unittest.TestCase):
    def test_semicolon(self):
        r = m.parse_atc(ATC)
        self.assertEqual(r["rows"], 3)
        self.assertEqual(r["short"], 1)
        self.assertEqual(r["missing"], 2)
        self.assertEqual(r["valid"], 1)
        self.assertEqual(r["flags"], {"O": 1, "N": 2})
        self.assertEqual(r["first_time"], "2026-11-06T21:00:00Z")
        self.assertEqual(r["last_time"], "2026-11-06T23:00:00Z")
        self.assertEqual(r["last_valid_time"], "2026-11-06T21:00:00Z")
        self.assertEqual(len(r["columns"]), 12)

    def test_timestamp_comma(self):
        r = m.parse_atc("TIMESTAMP,ch4,Flag\n2026-11-06T10:00:00Z,1950.5,O\n2026-11-06T11:00:00Z,nan,O\n")
        self.assertEqual((r["rows"], r["valid"], r["missing"]), (2, 1, 1))
        self.assertEqual(r["last_valid_time"], "2026-11-06T10:00:00Z")
        self.assertEqual(r["last_time"], "2026-11-06T11:00:00Z")

    def test_no_header(self):
        with self.assertRaises(ValueError):
            m.parse_atc("a;b\n1;2\n")

    def test_payload(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("data/", "")
            z.writestr("data/readme.pdf", b"%PDF")
            z.writestr("data/ICOS.csv", ATC)
        name, text = m.read_payload(buf.getvalue())
        self.assertEqual(name, "data/ICOS.csv")
        self.assertEqual(m.parse_atc(text)["valid"], 1)
        self.assertEqual(m.read_payload(b"x;y\n"), (None, "x;y\n"))
        with self.assertRaises(ValueError):
            m.read_payload(b"<!DOCTYPE html><html><body>licence</body></html>")


class TestNoaa(unittest.TestCase):
    def test_files(self):
        listing = ('<a href="?C=N;O=D">Name</a> <a href="/aftp/data/">Parent</a> '
                   '<a href="ch4_brw_surface-insitu_1_ccgg_DailyData.txt">x</a> '
                   '<a href="ch4_brw_surface-insitu_1_ccgg_DailyData.txt">dup</a> '
                   '<a href="ch4_mlo_surface-insitu_1_ccgg_HourlyData.txt">h</a> '
                   '<a href="README_ch4_surface-insitu_ccgg.html">r</a>')
        self.assertEqual(m.noaa_files(listing), ["ch4_brw_surface-insitu_1_ccgg_DailyData.txt"])

    def test_last_day(self):
        text = ("# header_lines : 3\n# data_fields: site_code year month day value qcflag\n"
                "BRW 2025 12 30 1990.1 ...\nBRW 2025 12 31 -999.99 ...\nBRW 2025 12 29 1985.0 *..\n")
        self.assertEqual(m.noaa_last_day(text), "2025-12-30")
        self.assertEqual(m.noaa_last_day("site_code year month day value qcflag\nMLO 2025 1 2 1900 ...\n"),
                         "2025-01-02")


class TestGradeAndReport(unittest.TestCase):
    def test_grade(self):
        s = {"live": 30, "stale": 6, "median_lag_live_days": 0.9, "median_publish_delay_live_days": 0.46}
        g = m.grade(s, [{"gap_days": 0.0}, {"gap_days": 1.5}, {"gap_days": 3.0}, {"error": "x"}])
        self.assertTrue(g["I1_at_least_25_live"])
        self.assertTrue(g["I2_median_lag_live_le_2d"])
        self.assertTrue(g["I3_at_least_5_stale"])
        self.assertTrue(g["I4_median_publish_delay_le_0.6d"])
        self.assertEqual((g["sample_parsed"], g["sample_within_gap"]), (3, 2))
        self.assertFalse(g["I5_sample_last_valid_within_2d"])
        g2 = m.grade({"live": 0, "stale": 0, "median_lag_live_days": None,
                      "median_publish_delay_live_days": None}, [{"gap_days": 0.0}, {"gap_days": 0.5}])
        self.assertFalse(g2["I1_at_least_25_live"])
        self.assertFalse(g2["I2_median_lag_live_le_2d"])
        self.assertFalse(g2["I4_median_publish_delay_le_0.6d"])
        self.assertIsNone(g2["I5_sample_last_valid_within_2d"])

    def test_markdown(self):
        t = m.station_table(rows(), NOW)
        rep = {"version": m.VERSION, "icos": {
            "queried_utc": "2026-11-07T12:00:00Z",
            "nrt": {"rows": 4, "summary": m.summarize(t), "stations": t},
            "l2": {"error": "HTTPError: 500"},
            "samples": [{"station": "AS_ZEP", "dobj": O + "aaa", "rows": 3, "valid": 1,
                         "last_valid_time": "2026-11-06T21:00:00Z", "gap_days": 0.083, "flags": {"O": 1}},
                        {"station": "AS_ABC", "dobj": O + "eee", "error": "HTTPError"}]},
            "noaa": {"files": [{"file": "ch4_brw_surface-insitu_1_ccgg_DailyData.txt",
                                "last_day": "2025-12-31", "lag_days": 310.5, "last_modified": "x"}]},
            "checks": {"I1_at_least_25_live": False}}
        md = m.to_markdown(rep)
        self.assertIn("## ICOS NRT (4 current objects)", md)
        self.assertIn("| AS_ZEP | ZEP | Zeppelin | 15 |", md)
        self.assertIn("## ICOS L2: error", md)
        self.assertIn("| AS_ZEP | aaa | 3 | 1 | 2026-11-06T21:00:00Z | 0.083 |", md)
        self.assertIn("| 2025-12-31 | 310.5 |", md)


if __name__ == "__main__":
    unittest.main()
