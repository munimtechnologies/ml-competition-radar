"""Offline tests for vessel_mix5 (no network). MV2 of Munim, Inc. Apache-2.0."""
import json
import math
import os
import tempfile
import unittest

import numpy as np

import vessel_mix as vm
import vessel_mix2 as v2
import vessel_mix3 as v3
import vessel_mix5 as v5

DAY0 = 1440 * 17000


def synth_site(name, seed, n_days=5, per_day=6, offset=0.0):
    rng = np.random.default_rng(seed)
    tilt = np.linspace(6, -6, 25)
    lv = {}
    for m in range(DAY0, DAY0 + 1440 * n_days):
        lv[m] = 80 + offset + tilt + rng.normal(0, 1, 25)
    ships = []
    shape = np.concatenate([np.full(10, 20.0), np.zeros(15)])
    for d in range(n_days):
        for p in sorted(rng.choice(np.arange(30, 1380, 45), per_day, replace=False)):
            start = DAY0 + 1440 * d + int(p)
            for i in range(20):
                amp = 1 - abs(i - 10) / 10.0
                lv[start + i] = 10 * np.log10(10 ** (lv[start + i] / 10) + 10 ** ((80 + offset + shape * amp) / 10) * (shape > 0))
            ships.append((start * 60.0, (start + 20) * 60.0))
    return {"site": name, "lv": lv, "day_of": {m: (m - DAY0) // 1440 for m in lv}, "ships": ships,
            "days": [{"complete_minutes": 1440}] * n_days}


class TestBase(unittest.TestCase):
    def test_versions_and_names(self):
        self.assertEqual(vm.VERSION, "0.1.0")
        self.assertEqual(v2.VERSION, "0.2.0")
        self.assertEqual(v3.VERSION, "0.3.0")
        self.assertEqual(v5.VERSION, "0.5.0")
        self.assertEqual(list(v5.IDX_F), [131])
        self.assertEqual(v5.CONDS, ("D1", "D2", "D4", "D8", "D16", "S1", "S4", "SALL", "SAME", "IN16"))

    def test_fetch_recorder_restores_globals(self):
        seen = {}

        def stub(site, data_dir, log):
            seen.update(dep=vm.DEPLOYMENT, n=vm.N_DAYS, dir=data_dir)
            log[site] = {"hmd_files_listed": 9, "days": [{"complete_minutes": 1440}] * 5}
            return {"site": site, "lv": {}, "day_of": {}, "ships": [], "days": []}

        saved = vm.fetch_site
        vm.fetch_site = stub
        try:
            log = {}
            sd = v5.fetch_recorder("sb01", "04", "datadir", log)
        finally:
            vm.fetch_site = saved
        self.assertEqual(seen, {"dep": "04", "n": 5, "dir": os.path.join("datadir", "dep04")})
        self.assertEqual((vm.DEPLOYMENT, vm.N_DAYS), ("01", 12))
        self.assertEqual(sd["site"], "sb01")
        self.assertEqual(log, {"sb01_04": {"hmd_files_listed": 9, "error": None, "complete_minutes": [1440] * 5}})

    def test_build_recorder_days(self):
        r = v5.build_recorder(synth_site("sb01", 1), "sb01_02")
        self.assertEqual(len(r["train"]), 3 * 96)
        self.assertEqual(len(r["test"]), 2 * 96)
        self.assertEqual({g["day"] for g in r["train"]}, {0, 1, 2})
        self.assertEqual({g["day"] for g in r["test"]}, {3, 4})
        self.assertEqual({g["rec"] for g in r["train"]}, {"sb01_02"})
        self.assertEqual(r["site"], "sb01")
        self.assertTrue(math.isfinite(r["median_train_db"]))


class TestConditions(unittest.TestCase):
    def test_conditions(self):
        usable = sorted("%s_%s" % (s, d) for s in ("gr01", "sb01", "sb03") for d in ("01", "02", "03"))
        site_of = {n: n[:4] for n in usable}
        t = "sb01_01"
        c = v5.conditions(t, usable, site_of, np.random.default_rng(0), ns=(1, 2, 4, 16), s_ns=(1, 4, 10), in_n=4)
        self.assertEqual(sorted(c), sorted(["D1", "D2", "D4", "S1", "S4", "SALL", "SAME", "IN4"]))
        self.assertEqual(c["D2"][:1], c["D1"])
        self.assertEqual(c["D4"][:2], c["D2"])
        self.assertEqual(len(set(c["D4"])), 4)
        self.assertEqual(c["IN4"], [t] + c["D4"][:3])
        self.assertEqual(c["S4"][:1], c["S1"])
        for k in ("D1", "D2", "D4", "S1", "S4", "SALL", "SAME"):
            self.assertNotIn(t, c[k])
        self.assertEqual(sorted(c["SALL"]), sorted(n for n in usable if not n.startswith("sb01")))
        self.assertTrue(all(not n.startswith("sb01") for n in c["S4"]))
        self.assertEqual(sorted(c["SAME"]), ["sb01_02", "sb01_03"])


class TestPredict(unittest.TestCase):
    def test_v3_models_unchanged(self):
        rng = np.random.default_rng(3)
        X = rng.normal(0, 1, (300, 132))
        y = np.clip(0.5 + 0.1 * X[:, 130] + 0.1 * X[:, 131], 0, 1)
        tr, trt = {"X": X, "y": y}, {"X": X.copy(), "y": y}
        Xt = rng.normal(0, 1, (40, 132))
        p = v5.predict5(tr, trt, Xt, 0)
        q = v3.predict_set(tr, trt, Xt, 0)
        for m in ("C0", "G1L", "G1T", "B"):
            self.assertTrue(np.array_equal(p[m], q[m]), m)
        self.assertEqual(sorted(p), sorted(["C0", "G1L", "G1T", "B", "G1F"]))
        Xs = Xt.copy()
        Xs[:, 130] += 10.0
        self.assertTrue(np.array_equal(p["G1F"], v5.predict5(tr, trt, Xs, 0)["G1F"]))


def st(r):
    return {"rmse": r, "bias": 0.0, "n": 10, "bins": {}}


def fake(vals, complete=None, gate=True):
    return {"gate_GA": gate, "gate_GB": True,
            "pooled": {c: {m: st(v) for m, v in d.items()} for c, d in vals.items()},
            "complete": complete if complete is not None else {c: True for c in vals}}


HOLD = {"D1": {"G1L": 0.36, "G1T": 0.40},
        "D16": {"G1L": 0.28, "C0": 0.29, "B": 0.26, "F1": 0.27, "G1T": 0.27, "G1F": 0.265},
        "SAME": {"G1L": 0.27}, "SALL": {"G1L": 0.33}, "IN16": {"G1L": 0.25}}
FAIL = {"D1": {"G1L": 0.36, "G1T": 0.40},
        "D16": {"G1L": 0.37, "C0": 0.29, "B": 0.30, "F1": 0.27, "G1T": 0.42, "G1F": 0.28},
        "SAME": {"G1L": 0.34}, "SALL": {"G1L": 0.33}, "IN16": {"G1L": 0.38}}


class TestGrade5(unittest.TestCase):
    def test_all_hold(self):
        # T1 .28<.36; T2 .28<.29; T3 .26<.27; T4 .40/.27=1.481 > .36/.28=1.286; T5 .27<.33;
        # T6 .25<.28; T7 .265<.27
        g = {x["id"]: x["held"] for x in v5.grade5(fake(HOLD))}
        self.assertEqual(g, {s: True for s in v5.TIDS})

    def test_all_fail(self):
        # T1 .37>.36; T2 .37>.29; T3 .30>.27; T4 .40/.42=.952 < .36/.37=.973; T5 .34>.33;
        # T6 .38>.37; T7 .28>.27
        g = {x["id"]: x["held"] for x in v5.grade5(fake(FAIL))}
        self.assertEqual(g, {s: False for s in v5.TIDS})

    def test_t4_values(self):
        x = [x for x in v5.grade5(fake(HOLD)) if x["id"] == "T4"][0]["value"]
        self.assertAlmostEqual(x["G1T_ratio"], 0.40 / 0.27, places=12)
        self.assertAlmostEqual(x["G1L_ratio"], 0.36 / 0.28, places=12)

    def test_incomplete_condition_is_ungraded(self):
        comp = {c: True for c in HOLD}
        comp["D16"] = False
        g = {x["id"]: x["held"] for x in v5.grade5(fake(HOLD, complete=comp))}
        self.assertEqual(g, {"T1": None, "T2": None, "T3": None, "T4": None, "T5": True, "T6": None, "T7": None})

    def test_gate_fail(self):
        g = v5.grade5(fake(HOLD, gate=False))
        self.assertEqual([x["id"] for x in g], list(v5.TIDS))
        self.assertTrue(all(x["held"] is None for x in g))


class TestEndToEnd(unittest.TestCase):
    KW = dict(n_test=20, n_train=200, ns=(1, 2), s_ns=(1,), in_n=2, min_recorders=6, min_per_site=2,
              min_passages=3)

    @classmethod
    def setUpClass(cls):
        cls.sd01 = [synth_site(s, i, per_day=1 if s == "gr01" else 6) for i, s in enumerate(vm.SITES)]
        recs = [("%s_01" % sd["site"], sd) for sd in cls.sd01]
        for i, s in enumerate(v5.SITES):
            recs.append(("%s_02" % s, synth_site(s, 20 + i, offset=4.0)))
        cls.res = v5.analyze5(cls.sd01, recs, **cls.KW)

    def test_gates_and_counts(self):
        res = self.res
        self.assertTrue(res["gate_GA"])
        self.assertTrue(res["gate_GB"])
        self.assertTrue(res["gate_GC"])
        self.assertEqual(res["vessel_sites"], ["sb01", "sb03"])
        self.assertEqual(res["usable"], ["gr01_01", "gr01_02", "sb01_01", "sb01_02", "sb03_01", "sb03_02"])
        self.assertEqual(res["per_site"], {"gr01": 2, "sb01": 2, "sb03": 2})
        self.assertEqual(res["conditions"], ["D1", "D2", "S1", "SALL", "SAME", "IN2"])
        self.assertEqual((vm.DEPLOYMENT, vm.N_DAYS), ("01", 12))
        n = 20 * 2 * 6
        for c in res["conditions"]:
            self.assertEqual(res["n_recorders"][c], 6)
            for m in v5.MODELS:
                self.assertEqual(res["pooled"][c][m]["n"], n)
                self.assertTrue(math.isfinite(res["pooled"][c][m]["rmse"]))
                self.assertEqual(sum(d[m]["n"] for d in res["by_site"][c].values()), n)
            self.assertEqual(res["pooled"][c]["F1"]["rmse"], res["pooled"]["D1"]["F1"]["rmse"])
        self.assertEqual(len(res["per_recorder"]), 6)
        self.assertEqual(res["trend_G1L"]["recorders"], 6)
        for t, pr in res["per_recorder"].items():
            self.assertEqual(pr["conditions"]["IN2"][0], t)
            self.assertEqual(pr["conditions"]["SAME"], [n for n in res["usable"] if n[:4] == t[:4] and n != t])

    def test_report(self):
        res = dict(self.res)
        res["grades"] = v5.grade5(res)
        self.assertEqual([x["id"] for x in res["grades"]], list(v5.TIDS))
        json.dumps(res)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.md")
            v5.write_md5(res, path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
        self.assertIn("| D1 | 6 | True |", text)
        self.assertIn("| SAME | G1L |", text)
        self.assertIn("| T7 |", text)
        self.assertIn("| sb03_02 | sb03 | 288 | 192 |", text)


if __name__ == "__main__":
    unittest.main()
