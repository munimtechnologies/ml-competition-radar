"""Fake-data tests for quant_run.py and quant_table.py (no torch, no network).
MV2 of Munim, Inc. Apache-2.0."""
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quant_run  # noqa: E402
import quant_table  # noqa: E402

CODE_DIR = os.environ.get("SPARK_CODE_DIR", "/out/code")
STAND_IN = '''import json, os
def run(db, ranked, out_dir, scorer, depth=50):
    os.makedirs(out_dir, exist_ok=True)
    s = {"needs": 1, "rerank_depth": depth, "scores": scorer.score("q", ["a", "bb"])}
    with open(os.path.join(out_dir, "rerank.json"), "w") as f:
        json.dump(s, f)
    return s
'''
TEXT = "secret question words"


class LenScorer:
    def __init__(self, *args):
        self.args = args

    def score(self, query, docs):
        return [float(len(d)) for d in docs]


class WordScorer:
    def score(self, query, docs):
        words = query.lower().split()
        return [float(sum(d.lower().split().count(w) for w in words) - 2) for d in docs]


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def rows(lists):
    return [{"info_need_id": i, "info_need": TEXT, "candidates": [[p, 0.5] for p in c]}
            for i, c in lists]


BASE = [("q1", [1, 2, 3, 4, 5, 6]), ("q2", [7, 8, 9, 10, 11])]
GOLD = [{"info_need_id": "q1", "gold": ["1"]}, {"info_need_id": "q2", "gold": ["9"]}]


def make_arm(root, arm, legs, lists, ms, pairs=10):
    for g in legs:
        d = os.path.join(root, arm, g)
        write_jsonl(os.path.join(d, "ranked.jsonl"), rows(lists))
        with open(os.path.join(d, "rerank.json"), "w", encoding="utf-8") as f:
            json.dump({"pairs": pairs, "seconds": ms * pairs / 1000.0, "ms_per_pair": ms,
                       "median_need_seconds": 2.5, "missing_text": 0, "variant": arm}, f)


def make_legs(d):
    base, gold = os.path.join(d, "base.jsonl"), os.path.join(d, "gold.jsonl")
    write_jsonl(base, rows(BASE))
    write_jsonl(gold, GOLD)
    return {g: (base, gold) for g in quant_table.LEGS}


class QuantRun(unittest.TestCase):
    def test_variant(self):
        self.assertEqual(quant_run.variant(True, 256), "int8_256")
        self.assertEqual(quant_run.variant(False, 512), "fp32_512")

    def test_main_with_stand_in(self):
        with tempfile.TemporaryDirectory() as d:
            code = os.path.join(d, "code")
            os.makedirs(code)
            with open(os.path.join(code, "rerank_run.py"), "w", encoding="utf-8") as f:
                f.write(STAND_IN)
            made = []

            def make(*args):
                made.append(args)
                return LenScorer(*args)
            out = os.path.join(d, "out")
            rc = quant_run.main(["--code-dir", code, "--db", "x.db", "--ranked", "r.jsonl",
                                 "--model-dir", "m", "--out-dir", out, "--quantize",
                                 "--max-length", "256"], make_scorer=make)
            with open(os.path.join(out, "rerank.json"), encoding="utf-8") as f:
                s = json.load(f)
        self.assertEqual(rc, 0)
        self.assertEqual(made, [(code, "m", 256, 8, 2, True)])
        self.assertEqual((s["variant"], s["quantize"], s["max_length"], s["rerank_depth"]),
                         ("int8_256", True, 256, 50))
        self.assertEqual(s["scores"], [1.0, 2.0])
        self.assertEqual(s["quant_run_version"], quant_run.VERSION)

    @unittest.skipUnless(os.path.exists(os.path.join(CODE_DIR, "rerank_run.py")), "needs fetched rerank_run.py")
    def test_real_rerank_run(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "idx.db")
            con = sqlite3.connect(db)
            con.execute("CREATE VIRTUAL TABLE docs USING fts5(title, abstract, mesh)")
            for pmid, t, a in ((11, "Kinase", "zebrafish fins"), (13, "Zebrafish", "zebrafish fin"),
                               (15, "Tail", "zebrafish zebrafish")):
                con.execute("INSERT INTO docs(rowid, title, abstract, mesh) VALUES (?,?,?,?)", (pmid, t, a, ""))
            con.commit()
            con.close()
            ranked = os.path.join(d, "ranked.jsonl")
            write_jsonl(ranked, [{"info_need_id": "Q", "info_need": "zebrafish fin",
                                  "candidates": [[11, 0.9], [13, 0.8], [15, 0.1]], "depth": 3}])
            s = quant_run.run(CODE_DIR, db, ranked, os.path.join(d, "o"), WordScorer(), 2, False, 512)
            out = quant_table.load_jsonl(os.path.join(d, "o", "ranked.jsonl"))
            with open(os.path.join(d, "o", "rerank.json"), encoding="utf-8") as f:
                saved = json.load(f)
        self.assertEqual([p for p, _ in out[0]["candidates"]], [13, 11, 15])
        self.assertEqual((s["pairs"], s["variant"], s["rerank_depth"]), (2, "fp32_512", 2))
        self.assertEqual(saved, s)


class QuantTable(unittest.TestCase):
    def test_metrics_and_compare(self):
        gold = quant_table.gold_map(GOLD)
        m, first = quant_table.metrics(rows(BASE), gold)
        self.assertEqual((m["needs"], m["hit5"], m["hit1"]), (2, 2, 1))
        self.assertAlmostEqual(m["mrr5"], (1 + 1 / 3) / 2)
        self.assertEqual(first, {"q1": 1, "q2": 3})
        c = quant_table.compare(rows([("q1", [2, 3, 4, 5, 6]), ("q2", [7, 8, 9])]), rows(BASE), gold)
        self.assertEqual((c["same_first"], c["same_set5"], c["lost5"], c["gained5"]), (1, 0, ["q1"], []))
        self.assertAlmostEqual(c["d_mrr5"], 1 / 6 - 2 / 3)

    def test_hours(self):
        self.assertEqual(quant_table.hours(250.0), {"50": 3.47, "100": 6.94, "200": 13.89})

    def test_build_picks_fast_acceptable(self):
        with tempfile.TemporaryDirectory() as d:
            legs, arms = make_legs(d), os.path.join(d, "arms")
            make_arm(arms, "fp32_512", ["l"], BASE, 500.0)
            make_arm(arms, "int8_512", quant_table.LEGS, [("q1", [2, 1, 3, 4, 5]), ("q2", [9, 7, 8, 10, 11])], 250.0)
            make_arm(arms, "int8_256", quant_table.LEGS, [("q1", [2, 3, 4, 5, 6]), ("q2", [7, 8, 9, 10, 11])], 150.0)
            make_arm(arms, "fp32_256", ["l", "bg"], BASE, 300.0)
            t = quant_table.build(arms, legs)
            text = json.dumps(t)
        self.assertEqual(t["chosen"], "int8_512")
        self.assertEqual(t["base_mean_mrr5"], 0.6667)
        a = t["arms"]["int8_512"]
        self.assertEqual((a["speedup_l"], a["ms_per_pair_all"], a["mean_mrr5"]), (2.0, 250.0, 0.75))
        self.assertEqual(a["ce_hours_per_1000q"]["200"], 13.89)
        self.assertEqual((a["legs"]["r"]["same_first"], a["legs"]["r"]["same_set5"]), (0, 2))
        self.assertEqual(t["why"]["int8_512"], ["acceptable"])
        self.assertTrue(t["why"]["int8_256"][0].startswith("mean MRR 0.1667"))
        self.assertEqual(len(t["why"]["int8_256"]), 4)
        self.assertEqual(t["why"]["fp32_256"], ["not all three legs"])
        self.assertNotIn("fp32_512", t["why"])
        self.assertFalse(t["arms"]["fp32_512"]["complete"])
        self.assertNotIn(TEXT, text)

    def test_build_keeps_control_when_not_faster(self):
        with tempfile.TemporaryDirectory() as d:
            legs, arms = make_legs(d), os.path.join(d, "arms")
            make_arm(arms, "fp32_512", ["l"], BASE, 260.0)
            make_arm(arms, "int8_512", quant_table.LEGS, BASE, 250.0)
            t = quant_table.build(arms, legs)
        self.assertEqual(t["chosen"], "fp32_512")
        self.assertEqual(t["why"]["int8_512"], ["L speed-up 1.04 < 1.2"])

    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            legs, arms = make_legs(d), os.path.join(d, "arms")
            make_arm(arms, "int8_512", quant_table.LEGS, BASE, 250.0)
            out = os.path.join(d, "t", "table.json")
            argv = ["--arms-dir", arms, "--out", out]
            for g, (b, gl) in legs.items():
                argv += ["--leg", "%s=%s=%s" % (g, b, gl)]
            self.assertEqual(quant_table.main(argv), 0)
            with open(out, encoding="utf-8") as f:
                t = json.load(f)
        self.assertEqual(t["chosen"], "fp32_512")
        self.assertEqual(t["why"]["int8_512"], ["L speed-up None < 1.2"])
        self.assertEqual(t["legs"], ["bg", "l", "r"])


if __name__ == "__main__":
    unittest.main()
