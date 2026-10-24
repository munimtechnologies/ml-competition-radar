import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2dev  # noqa: E402

TOPICS, ASSESS = "BioGen2024topics-json.txt", "biogen_collection_v3.json"
BASE = "https://trec.nist.gov/data/biogen/"
GOOD = [{"url": BASE + TOPICS, "bytes": 21598, "sha256": t2dev.PINS[TOPICS][1]},
        {"url": BASE + ASSESS, "bytes": 11128359, "sha256": t2dev.PINS[ASSESS][1]}]
ROWS = [{"topic": 116, "supports": ["5", "30"], "contradicts": ["30", "7"], "neutral": ["9"],
         "notrelevant": ["11"]},
        {"topic": "117", "supports": [], "contradicts": [], "neutral": [], "notrelevant": ["4"]}]


class Clock:
    def __init__(self, path=None, at=None):
        self.t, self.sleeps, self.path, self.at = 0.0, 0, path, at

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s
        self.sleeps += 1
        if self.path and self.t >= self.at:
            open(self.path, "w").close()


class Wait(unittest.TestCase):
    def test_times_out(self):
        with tempfile.TemporaryDirectory() as d:
            c = Clock()
            r = t2dev.wait_for(os.path.join(d, "never"), 2, 60, c.now, c.sleep)
            self.assertEqual((r["found"], r["waited_seconds"], c.sleeps), (False, 120.0, 2))

    def test_file_appears(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "gold.jsonl")
            c = Clock(p, 120)
            r = t2dev.wait_for(p, 10, 60, c.now, c.sleep)
            self.assertEqual((r["found"], r["waited_seconds"], c.sleeps), (True, 120.0, 2))

    def test_main_wait(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o", "wait.json")
            self.assertEqual(t2dev.main(["wait", "--path", d, "--minutes", "0", "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                self.assertTrue(json.load(f)["found"])
            self.assertEqual(t2dev.main(["wait", "--path", os.path.join(d, "no"), "--minutes", "0",
                                         "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                r = json.load(f)
            self.assertEqual((r["found"], r["waited_seconds"], r["version"]), (False, 0.0, "0.1.0"))


class Gold(unittest.TestCase):
    def test_pins(self):
        self.assertEqual(t2dev.check_pins(GOOD), [])
        bad = [dict(GOOD[0], sha256="0" * 64), {"url": BASE + "other.json", "bytes": 1, "sha256": "x"}]
        p = t2dev.check_pins(bad)
        self.assertEqual(len(p), 3)
        self.assertTrue(p[0].startswith("BioGen2024topics-json.txt: 21598 bytes, sha256 000"))
        self.assertEqual(p[1:], ["unexpected file other.json", "missing biogen_collection_v3.json"])

    def test_t1_gold(self):
        self.assertEqual(t2dev.t1_gold(ROWS, ("supports",)), [{"info_need_id": "116", "gold": ["5", "30"]}])
        self.assertEqual(t2dev.t1_gold(ROWS, ("supports", "contradicts", "neutral")),
                         [{"info_need_id": "116", "gold": ["5", "7", "9", "30"]}])

    def test_main_gold(self):
        with tempfile.TemporaryDirectory() as d:
            cen, out = os.path.join(d, "census"), os.path.join(d, "gold")
            os.makedirs(cen)
            with open(os.path.join(cen, "download.json"), "w", encoding="utf-8") as f:
                json.dump(GOOD, f)
            t2dev.write_jsonl(os.path.join(cen, "gold_t2.jsonl"), ROWS)
            self.assertEqual(t2dev.main(["gold", "--census-dir", cen, "--out-dir", out]), 0)
            self.assertEqual(t2dev.load_jsonl(os.path.join(out, "gold_relevant.jsonl")),
                             [{"info_need_id": "116", "gold": ["5", "7", "9", "30"]}])
            with open(os.path.join(out, "gold.json"), encoding="utf-8") as f:
                r = json.load(f)
            self.assertEqual((r["problems"], r["topics"]), ([], 2))
            self.assertEqual(r["supports"], {"topics": 1, "pmids": 2, "distinct_pmids": 2})
            self.assertEqual(r["relevant"], {"topics": 1, "pmids": 4, "distinct_pmids": 4})
            with open(os.path.join(cen, "download.json"), "w", encoding="utf-8") as f:
                json.dump(GOOD[:1], f)
            self.assertEqual(t2dev.main(["gold", "--census-dir", cen, "--out-dir", out]), 1)


if __name__ == "__main__":
    unittest.main()
