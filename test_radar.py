import datetime as dt
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import radar  # noqa: E402

TODAY = dt.date(2026, 10, 13)

FIXTURE = [
    {
        "name": "Predict 2D Chemical Structures From Mass Spectra",
        "url": "https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra?ref=mlcontests",
        "tags": ["biology", "chemistry", "supervised", "ranking", "measurable"],
        "launched": "14 Sep 2026",
        "registration-deadline": "7 Dec 2026",
        "deadline": "14 Dec 2026",
        "prize": "$50,000",
        "platform": "Kaggle",
        "sponsor": "Enveda",
    },
    {
        "name": "Detect root misconceptions in K-12 math solutions",
        "url": "https://www.kaggle.com/competitions/misconception-detection-in-k-12-student-math-workings/overview",
        "tags": ["supervised", "vision", "nlp", "education", "tabular", "classification"],
        "deadline": "17 Nov 2026",
        "registration-deadline": None,
        "prize": "$6,000",
        "platform": "Kaggle",
    },
    {
        "name": "Closed already",
        "url": "https://example.org/closed",
        "tags": ["tabular"],
        "deadline": "11 Oct 2026",
        "prize": "$9,999",
        "platform": "Independent",
    },
    {
        "name": "Malformed date",
        "url": "https://example.org/bad",
        "tags": ["tabular"],
        "deadline": "11 May 2026 Apr 2026",
        "prize": "$1",
        "platform": "Independent",
    },
    {
        "name": "No cash",
        "url": "https://zindi.africa/competitions/x?utm_source=mlcontest&utm_medium=referral",
        "tags": ["nlp"],
        "deadline": "30 Nov 2026",
        "prize": None,
        "platform": "Zindi",
    },
    "not-a-dict",
]


class ParseTests(unittest.TestCase):
    def test_parse_date_ok(self):
        self.assertEqual(radar.parse_date("7 Dec 2026"), dt.date(2026, 12, 7))
        self.assertEqual(radar.parse_date("07 Dec 2026"), dt.date(2026, 12, 7))
        self.assertEqual(radar.parse_date(" 2 Nov 2026 "), dt.date(2026, 11, 2))

    def test_parse_date_bad(self):
        self.assertIsNone(radar.parse_date(None))
        self.assertIsNone(radar.parse_date(""))
        self.assertIsNone(radar.parse_date("11 May 2026 Apr 2026"))
        self.assertIsNone(radar.parse_date("31 Feb 2026"))
        self.assertIsNone(radar.parse_date("2026-10-13"))

    def test_parse_prize(self):
        self.assertEqual(radar.parse_prize("$52,000"), 52000)
        self.assertEqual(radar.parse_prize("$1"), 1)
        self.assertEqual(radar.parse_prize(None), 0)
        self.assertEqual(radar.parse_prize(""), 0)
        self.assertEqual(radar.parse_prize(700000), 700000)

    def test_clean_url(self):
        self.assertEqual(
            radar.clean_url("https://a.b/c?ref=mlcontests"), "https://a.b/c"
        )
        self.assertEqual(
            radar.clean_url("https://a.b/c?utm_source=x&utm_medium=y"), "https://a.b/c"
        )
        self.assertEqual(
            radar.clean_url("https://a.b/c?id=5&ref=mlcontests&lang=en"),
            "https://a.b/c?id=5&lang=en",
        )
        self.assertEqual(radar.clean_url(None), "")


class SelectTests(unittest.TestCase):
    def test_open_only_sorted_by_prize(self):
        rows = radar.select(FIXTURE, TODAY)
        names = [r["name"] for r in rows]
        self.assertEqual(
            names,
            [
                "Predict 2D Chemical Structures From Mass Spectra",
                "Detect root misconceptions in K-12 math solutions",
            ],
        )

    def test_min_prize_zero_keeps_no_cash(self):
        rows = radar.select(FIXTURE, TODAY, min_prize=0)
        self.assertIn("No cash", [r["name"] for r in rows])

    def test_days_filter(self):
        rows = radar.select(FIXTURE, TODAY, days=40)
        self.assertEqual([r["name"] for r in rows],
                         ["Detect root misconceptions in K-12 math solutions"])

    def test_tags_filter(self):
        rows = radar.select(FIXTURE, TODAY, tags=["chemistry"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["platform"], "Kaggle")
        self.assertEqual(rows[0]["registration_deadline"], dt.date(2026, 12, 7))

    def test_deadline_on_today_is_open(self):
        rows = radar.select([{"name": "x", "deadline": "13 Oct 2026", "prize": "$5"}], TODAY)
        self.assertEqual(len(rows), 1)


class RenderTests(unittest.TestCase):
    def test_markdown(self):
        rows = radar.select(FIXTURE, TODAY)
        md = radar.render_markdown(rows, TODAY)
        self.assertIn("| 50,000 | 2026-12-14 | 62 |", md)
        self.assertIn("(https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra)", md)
        self.assertNotIn("ref=mlcontests", md)
        self.assertIn(radar.SOURCE_URL, md)

    def test_markdown_empty(self):
        md = radar.render_markdown([], TODAY)
        self.assertIn("(none match)", md)

    def test_json_roundtrip(self):
        rows = radar.select(FIXTURE, TODAY)
        text = json.dumps(radar.to_jsonable(rows))
        back = json.loads(text)
        self.assertEqual(back[0]["deadline"], "2026-12-14")
        self.assertIsNone(back[1]["registration_deadline"])


class CliTests(unittest.TestCase):
    def test_main_offline_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "competitions.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(FIXTURE, fh)
            import io
            from contextlib import redirect_stdout

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = radar.main(["--input", path, "--today", "2026-10-13", "--json"])
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["prize_usd"], 50000)

    def test_main_wrapper_object(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "c.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"competitions": FIXTURE}, fh)
            self.assertEqual(len(radar.load_entries(path)), len(FIXTURE))


if __name__ == "__main__":
    unittest.main()
