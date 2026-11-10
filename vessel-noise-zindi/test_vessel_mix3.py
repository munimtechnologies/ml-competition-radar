"""Offline tests for vessel_mix3 (no network). MV2 of Munim, Inc. Apache-2.0."""
import json
import math
import os
import tempfile
import unittest

import numpy as np

import vessel_mix as vm
import vessel_mix2 as v2
import vessel_mix3 as v3

DAY0 = 1440 * 17000


class TestBase(unittest.TestCase):
    def test_base_versions(self):
        self.assertEqual(vm.VERSION, "0.1.0")
        self.assertEqual(v2.VERSION, "0.2.0")
        self.assertEqual(list(v2.IDX_L), [130, 131])

    def test_r2_threshold(self):
        self.assertAlmostEqual(v3.R2_MAX, 0.2694491587478854 - 0.5 * (0.2694491587478854 - 0.19277983158394127),
                               places=15)
        self.assertGreater(v3.R2_MAX, 0.2311)
        self.assertLess(v3.R2_MAX, 0.2312)


class TestFit(unittest.TestCase):
    def test_same_as_v1_fit_predict(self):
        rng = np.random.default_rng(1)
        X = rng.normal(0, 1, (300, 5))
        y = np.clip(0.3 + 0.1 * X[:, 0], 0, 1)
        Xt = rng.normal(0, 1, (50, 5))
        a = vm.fit_predict(X, y, Xt, 0)
        b = v3.pred(v3.fit(X, y, 0), Xt)
        self.assertTrue(np.allclose(a, b, atol=1e-12))

    def test_bg_without(self):
        bgs = [{"site": s} for s in ("gr01", "sb01", "sb03", "sb01")]
        out = v3.bg_without(bgs, "sb01")
        self.assertEqual(len(out), 2)
        self.assertTrue(all(g["site"] != "sb01" for g in out))


def st(r):
    return {"rmse": r, "bias": 0.0, "n": 10, "bins": {}}


def fake(gate=True, pin=None, pout=None, bsi=None, bso=None):
    pin = pin or {"C0": 0.30, "F1": 0.27, "G1L": 0.234, "G1T": 0.246, "B": 0.22}
    pout = pout or {"C0": 0.30, "F1": 0.27, "G1L": 0.30, "G1T": 0.26, "B": 0.28}
    bsi = bsi or {"a": {"G1L": 0.20, "G1T": 0.25, "C0": 0.30}, "b": {"G1L": 0.21, "G1T": 0.24, "C0": 0.30}}
    bso = bso or {"a": {"G1L": 0.35, "G1T": 0.25, "C0": 0.30}, "b": {"G1L": 0.25, "G1T": 0.24, "C0": 0.30}}
    return {"gate_GA": gate, "gate_GB": True,
            "pooled_in": {m: st(v) for m, v in pin.items()}, "pooled_out": {m: st(v) for m, v in pout.items()},
            "by_site_in": {h: {m: st(v) for m, v in d.items()} for h, d in bsi.items()},
            "by_site_out": {h: {m: st(v) for m, v in d.items()} for h, d in bso.items()}}


class TestGrade3(unittest.TestCase):
    def test_all_hold(self):
        g = {x["id"]: x["held"] for x in v3.grade3(fake())}
        self.assertEqual(g, {r: True for r in v3.RIDS})

    def test_all_fail(self):
        r = fake(pin={"C0": 0.30, "F1": 0.27, "G1L": 0.234, "G1T": 0.246, "B": 0.234},
                 pout={"C0": 0.30, "F1": 0.27, "G1L": 0.24, "G1T": 0.26, "B": 0.25},
                 bsi={"a": {"G1L": 0.20, "G1T": 0.25, "C0": 0.30}, "b": {"G1L": 0.25, "G1T": 0.24, "C0": 0.30}},
                 bso={"a": {"G1L": 0.29, "G1T": 0.25, "C0": 0.30}, "b": {"G1L": 0.25, "G1T": 0.24, "C0": 0.30}})
        g = {x["id"]: x["held"] for x in v3.grade3(r)}
        self.assertEqual(g, {q: False for q in v3.RIDS})
        # R1: 0.234 is not < 0.234; R2: 0.234 > 0.2311; R3: 0.24/0.234 = 1.026 < 0.26/0.246 = 1.057;
        # R4: 0.24 < 0.26; R5: 0.29 < 0.30 and 0.25 < 0.30; R6: site b 0.25 > 0.24; R7: 0.27 > 0.25

    def test_r2_fraction(self):
        x = [x for x in v3.grade3(fake()) if x["id"] == "R2"][0]["value"]
        self.assertAlmostEqual(x["fraction_closed"], (v3.V2_G1 - 0.22) / (v3.V2_G1 - v3.V2_G0), places=12)

    def test_gate_fail(self):
        g = v3.grade3(fake(gate=False))
        self.assertEqual([x["id"] for x in g], list(v3.RIDS))
        self.assertTrue(all(x["held"] is None for x in g))


def synth_site(name, seed, n_days=3, per_day=6, offset=0.0):
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


class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # the third site is 6 dB louder, so an unseen-recorder shift exists in the synthetic data
        cls.sites = [synth_site(s, i, offset=6.0 if i == 2 else 0.0) for i, s in enumerate(vm.SITES)]
        cls.kw = dict(n_test=80, n_train=300, n_train_days=2, n_days=3, min_passages=2)
        cls.res = v3.analyze3(cls.sites, **cls.kw)

    def test_gates_and_shape(self):
        res = self.res
        self.assertTrue(res["gate_GA"])
        self.assertTrue(res["gate_GB"])
        self.assertFalse(res["gate_GD"])          # synthetic data cannot reproduce v2's numbers
        self.assertEqual(res["background_sites"], sorted(vm.SITES))
        self.assertEqual(len(res["folds"]), len(res["vessel_sites"]))
        n = 80 * len(res["folds"])
        for m in v3.MODELS:
            for part in ("pooled_in", "pooled_out"):
                self.assertEqual(res[part][m]["n"], n)
                self.assertTrue(math.isfinite(res[part][m]["rmse"]))
            self.assertEqual(sum(d[m]["n"] for d in res["by_site_in"].values()), n)
            self.assertEqual(sum(d[m]["n"] for d in res["by_site_out"].values()), n)
        self.assertEqual(res["pooled_in"]["F1"]["rmse"], res["pooled_out"]["F1"]["rmse"])
        for f in res["folds"]:
            for h, o in f["out"].items():
                self.assertEqual(o["train_backgrounds"],
                                 sum(1 for s in self.sites if s["site"] != h) * 2 * 1440 // vm.WIN)

    def test_in_reproduces_v2(self):
        base = v2.analyze2(self.sites, **self.kw)
        for m in ("C0", "F1", "G1L", "G1T"):
            self.assertAlmostEqual(self.res["pooled_in"][m]["rmse"], base["pooled"][m]["rmse"], places=12)

    def test_blend_not_worse_than_mean(self):
        p = self.res["pooled_in"]
        self.assertLessEqual(p["B"]["rmse"], 0.5 * (p["G1L"]["rmse"] + p["G1T"]["rmse"]) + 1e-12)
        q = self.res["pooled_out"]
        self.assertLessEqual(q["B"]["rmse"], 0.5 * (q["G1L"]["rmse"] + q["G1T"]["rmse"]) + 1e-12)

    def test_levels_and_report(self):
        res = dict(self.res)
        lv = res["site_levels_db"]
        self.assertGreater(lv["gr01"]["bg_test"]["median_db"], lv["sb03"]["bg_test"]["median_db"] + 4.0)
        res["grades"] = v3.grade3(res)
        self.assertEqual([x["id"] for x in res["grades"]], list(v3.RIDS))
        json.dumps(res)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.md")
            v3.write_md3(res, path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
        self.assertIn("| B |", text)
        self.assertIn("| R7 |", text)
        self.assertIn("| sb03 |", text)


if __name__ == "__main__":
    unittest.main()
