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

# Shaped like https://api.zindi.world/v1/competitions as read on 2026-10-14.
ZINDI_FIXTURE = {
    "data": [
        {"id": "bias-bounty-mapping-equity-challenge",
         "title": "Bias Bounty Mapping Equity Challenge",
         "reward": "$10 000 USD", "reward_type": "prize",
         "start_time": "2026-08-28T14:00:00.000Z", "end_time": "2026-10-31T23:59:00.000Z",
         "entries_close_at": None, "kind": "competition", "open": True,
         "is_access_restricted": False, "secret_code_required": False},
        {"id": "sasol-customer-value-recruitment-challenge",
         "title": "Sasol Customer Value Recruitment Challenge",
         "reward": "R25 000 ZAR", "end_time": "2026-10-18T23:59:00.000Z",
         "kind": "competition", "open": True,
         "is_access_restricted": False, "secret_code_required": False},
        {"id": "eswatini-indabax-hack", "title": "IndabaX Eswatini: VAT File & Pay",
         "reward": "50 000 SZL", "end_time": "2026-10-31T22:15:00.000Z",
         "kind": "hackathon", "open": True,
         "is_access_restricted": True, "secret_code_required": True},
        {"id": "google-waxal-asr-challenge-october-study-jam",
         "title": "October Study Jam: Google WAXAL ASR Challenge",
         "reward": "500 Points", "end_time": "2026-10-31T23:59:00.000Z",
         "kind": "hackathon", "open": True,
         "is_access_restricted": False, "secret_code_required": False},
        {"id": "road-barbados-historic-handwriting-challenge",
         "title": "R.O.A.D. Barbados Historic Handwriting Challenge",
         "reward": "$25 000 USD", "end_time": "2026-10-04T23:59:00.000Z",
         "kind": "competition", "open": False},
        {"id": "closed-but-future-date", "title": "Closed early",
         "reward": "$3 000 USD", "end_time": "2026-12-01T00:00:00.000Z",
         "kind": "competition", "open": False},
    ],
    "meta": {"total_count": 6, "open_count": 4, "closed_count": 2, "per_page": 10},
}


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

    def test_parse_iso_date(self):
        self.assertEqual(radar.parse_iso_date("2026-10-31T23:59:00.000Z"), dt.date(2026, 10, 31))
        self.assertIsNone(radar.parse_iso_date(None))
        self.assertIsNone(radar.parse_iso_date("31 Oct 2026"))
        self.assertIsNone(radar.parse_iso_date("2026-02-31T00:00:00Z"))

    def test_parse_prize(self):
        self.assertEqual(radar.parse_prize("$52,000"), 52000)
        self.assertEqual(radar.parse_prize("$1"), 1)
        self.assertEqual(radar.parse_prize(None), 0)
        self.assertEqual(radar.parse_prize(""), 0)
        self.assertEqual(radar.parse_prize(700000), 700000)

    def test_parse_reward(self):
        self.assertEqual(radar.parse_reward("$10 000 USD"), (10000, "USD", True))
        self.assertEqual(radar.parse_reward("R25 000 ZAR"), (25000, "ZAR", True))
        self.assertEqual(radar.parse_reward("€2 000 EUR"), (2000, "EUR", True))
        self.assertEqual(radar.parse_reward("1000 CHF"), (1000, "CHF", True))
        self.assertEqual(radar.parse_reward("$5,000"), (5000, "USD", True))
        self.assertEqual(radar.parse_reward("500 Points"), (500, None, False))
        self.assertEqual(radar.parse_reward("Knowledge"), (0, None, False))
        self.assertEqual(radar.parse_reward(None), (0, None, False))

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


class ZindiTests(unittest.TestCase):
    def rows(self, **kw):
        items = radar.zindi_items(ZINDI_FIXTURE)
        return radar.select_rows([radar.normalize_zindi(e) for e in items], TODAY, **kw)

    def test_normalize(self):
        r = radar.normalize_zindi(ZINDI_FIXTURE["data"][0])
        self.assertEqual(r["url"], "https://zindi.world/competitions/bias-bounty-mapping-equity-challenge")
        self.assertEqual(r["prize_usd"], 10000)
        self.assertEqual(r["deadline"], dt.date(2026, 10, 31))
        self.assertEqual(r["platform"], "Zindi")
        self.assertFalse(r["restricted"])

    def test_default_filter(self):
        # open, unrestricted, cash: the USD prize first, then the ZAR prize
        names = [r["name"] for r in self.rows()]
        self.assertEqual(names, ["Bias Bounty Mapping Equity Challenge",
                                 "Sasol Customer Value Recruitment Challenge"])

    def test_non_usd_prize_dropped_by_usd_threshold(self):
        names = [r["name"] for r in self.rows(min_prize=1000)]
        self.assertEqual(names, ["Bias Bounty Mapping Equity Challenge"])

    def test_include_restricted(self):
        names = [r["name"] for r in self.rows(include_restricted=True)]
        self.assertIn("IndabaX Eswatini: VAT File & Pay", names)

    def test_points_and_closed_excluded(self):
        names = [r["name"] for r in self.rows(min_prize=0, include_restricted=True)]
        self.assertIn("October Study Jam: Google WAXAL ASR Challenge", names)  # min_prize 0 keeps no-cash
        self.assertNotIn("Closed early", names)  # open: false even though the date is ahead
        self.assertNotIn("R.O.A.D. Barbados Historic Handwriting Challenge", names)

    def test_markdown_shows_foreign_currency(self):
        md = radar.render_markdown(self.rows(), TODAY)
        self.assertIn("| R25 000 ZAR | 2026-10-18 | 5 |", md)
        self.assertIn("| 10,000 | 2026-10-31 | 18 |", md)

    def test_pagination_stops(self):
        calls = []

        def fetch(url):
            calls.append(url)
            return ZINDI_FIXTURE  # the API ignoring ?page= must not loop

        items = radar.load_zindi(fetch=fetch)
        self.assertEqual(len(items), len(ZINDI_FIXTURE["data"]))
        self.assertLessEqual(len(calls), 2)

    def test_pagination_follows_pages(self):
        page1 = {"data": [{"id": "a", "open": True}], "meta": {"open_count": 2}}
        page2 = {"data": [{"id": "b", "open": True}], "meta": {"open_count": 2}}
        pages = {radar.ZINDI_API_URL: page1, radar.ZINDI_API_URL + "?page=2": page2}
        items = radar.load_zindi(fetch=lambda u: pages[u])
        self.assertEqual([i["id"] for i in items], ["a", "b"])

    def test_dedupe_across_sources(self):
        ml = [{"name": "Bias Bounty Mapping Equity Challenge", "deadline": "31 Oct 2026",
               "prize": "$10,000", "platform": "Zindi"}]
        rows = [radar.normalize(e) for e in ml]
        rows += [radar.normalize_zindi(e) for e in ZINDI_FIXTURE["data"]]
        out = radar.select_rows(rows, TODAY)
        self.assertEqual(sum(1 for r in out if r["name"].startswith("Bias Bounty")), 1)


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
    def run_main(self, argv):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = radar.main(argv)
        return rc, buf.getvalue()

    def test_main_offline_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "competitions.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(FIXTURE, fh)
            rc, out = self.run_main(["--input", path, "--today", "2026-10-13", "--json"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["prize_usd"], 50000)

    def test_main_offline_both_sources(self):
        with tempfile.TemporaryDirectory() as d:
            ml = os.path.join(d, "competitions.json")
            zi = os.path.join(d, "zindi.json")
            with open(ml, "w", encoding="utf-8") as fh:
                json.dump(FIXTURE, fh)
            with open(zi, "w", encoding="utf-8") as fh:
                json.dump(ZINDI_FIXTURE, fh)
            rc, out = self.run_main(["--input", ml, "--zindi-input", zi,
                                     "--today", "2026-10-13", "--json"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual([r["source"] for r in data],
                             ["mlcontests", "zindi", "mlcontests", "zindi"])

    def test_unknown_source(self):
        import io
        from contextlib import redirect_stderr

        with redirect_stderr(io.StringIO()):
            rc, _ = self.run_main(["--sources", "nope"])
        self.assertEqual(rc, 2)

    def test_main_wrapper_object(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "c.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"competitions": FIXTURE}, fh)
            self.assertEqual(len(radar.load_entries(path)), len(FIXTURE))


if __name__ == "__main__":
    unittest.main()
