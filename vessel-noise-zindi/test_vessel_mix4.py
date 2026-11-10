"""Offline tests for vessel_mix4 (no network). MV2 of Munim, Inc. Apache-2.0."""
import json
import math
import os
import tempfile
import unittest

import numpy as np

import vessel_mix as vm
import vessel_mix2 as v2
import vessel_mix3 as v3
import vessel_mix4 as v4

DAY0 = 1440 * 17000


class TestBase(unittest.TestCase):
    def test_base_versions(self):
        self.assertEqual(vm.VERSION, "0.1.0")
        self.assertEqual(v2.VERSION, "0.2.0")
        self.assertEqual(v3.VERSION, "0.3.0")
        self.assertEqual(v4.VERSION, "0.4.0")

    def test_indices(self):
        self.assertEqual(v2.NF, 132)
        self.assertEqual(list(v4.IDX_F), [131])
        self.assertEqual(len(v4.IDX_TI), 131)
        self.assertNotIn(130, list(v4.IDX_TI))
        self.assertIn(131, list(v4.IDX_TI))


class TestInvariance(unittest.TestCase):
    """G1F and G1TI must not move when only the absolute level (feature 130) is shifted."""

    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(3)
        X = rng.normal(0, 1, (400, 132))
        y = np.clip(0.5 + 0.1 * X[:, 130] + 0.1 * X[:, 131], 0, 1)
        cls.tr, cls.trt = {"X": X, "y": y}, {"X": X.copy(), "y": y}
        cls.Xt = rng.normal(0, 1, (60, 132))
        cls.Xs = cls.Xt.copy()
        cls.Xs[:, 130] += 10.0
        cls.p = v4.predict_set4(cls.tr, cls.trt, cls.Xt, 0)
        cls.q = v4.predict_set4(cls.tr, cls.trt, cls.Xs, 0)

    def test_gain_free(self):
        self.assertTrue(np.array_equal(self.p["G1F"], self.q["G1F"]))
        self.assertTrue(np.array_equal(self.p["G1TI"], self.q["G1TI"]))
        self.assertFalse(np.allclose(self.p["G1L"], self.q["G1L"]))

    def test_v3_models_unchanged(self):
        r = v3.predict_set(self.tr, self.trt, self.Xt, 0)
        for m in ("C0", "G1L", "G1T", "B"):
            self.assertTrue(np.array_equal(self.p[m], r[m]), m)


def st(r):
    return {"rmse": r, "bias": 0.0, "n": 10, "bins": {}}


def fake(gate=True, pin=None, pout=None, bso=None):
    pin = pin or {"C0": 0.30, "F1": 0.27, "G1L": 0.234, "G1T": 0.246, "B": 0.225, "G1F": 0.25, "G1TI": 0.28}
    pout = pout or {"C0": 0.30, "F1": 0.27, "G1L": 0.36, "G1T": 0.37, "B": 0.36, "G1F": 0.26, "G1TI": 0.30}
    bso = bso or {"a": {"G1F": 0.25, "C0": 0.30}, "b": {"G1F": 0.28, "C0": 0.29}}
    return {"gate_GA": gate, "gate_GB": True,
            "pooled_in": {m: st(v) for m, v in pin.items()}, "pooled_out": {m: st(v) for m, v in pout.items()},
            "by_site_out": {h: {m: st(v) for m, v in d.items()} for h, d in bso.items()}}


class TestGrade4(unittest.TestCase):
    def test_all_hold(self):
        g = {x["id"]: x["held"] for x in v4.grade4(fake())}
        self.assertEqual(g, {s: True for s in v4.SIDS})

    def test_all_fail(self):
        r = fake(pin={"C0": 0.30, "F1": 0.27, "G1L": 0.234, "G1T": 0.246, "B": 0.225, "G1F": 0.27, "G1TI": 0.24},
                 pout={"C0": 0.30, "F1": 0.27, "G1L": 0.30, "G1T": 0.29, "B": 0.30, "G1F": 0.31, "G1TI": 0.30},
                 bso={"a": {"G1F": 0.31, "C0": 0.30}, "b": {"G1F": 0.28, "C0": 0.29}})
        g = {x["id"]: x["held"] for x in v4.grade4(r)}
        self.assertEqual(g, {s: False for s in v4.SIDS})
        # S1 0.27 !< 0.27; S2 0.31 > 0.27; S3 0.31 > 0.30; S4 0.30 > 0.29; S5 0.24 < 0.246;
        # S6 0.31/0.27 = 1.148 >= 1.10; S7 site a 0.31 > 0.30

    def test_s6_ratio(self):
        x = [x for x in v4.grade4(fake()) if x["id"] == "S6"][0]["value"]
        self.assertAlmostEqual(x["ratio"], 0.26 / 0.25, places=12)

    def test_gate_fail(self):
        g = v4.grade4(fake(gate=False))
        self.assertEqual([x["id"] for x in g], list(v4.SIDS))
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
        cls.sites = [synth_site(s, i, offset=6.0 if i == 2 else 0.0) for i, s in enumerate(vm.SITES)]
        cls.kw = dict(n_test=80, n_train=300, n_train_days=2, n_days=3, min_passages=2)
        cls.res = v4.analyze4(cls.sites, **cls.kw)

    def test_v3_restored(self):
        self.assertIs(v3.predict_set, v4._V3_PREDICT)
        self.assertEqual(v3.MODELS, ("C0", "F1", "G1L", "G1T", "B"))
        self.assertEqual(v3.TRAINED, ("C0", "G1L", "G1T", "B"))

    def test_reproduces_v3(self):
        base = v3.analyze3(self.sites, **self.kw)
        for part in ("pooled_in", "pooled_out"):
            for m in v3.MODELS:
                self.assertAlmostEqual(self.res[part][m]["rmse"], base[part][m]["rmse"], places=12)
        for h in base["by_site_out"]:
            for m in v3.MODELS:
                self.assertAlmostEqual(self.res["by_site_out"][h][m]["rmse"],
                                       base["by_site_out"][h][m]["rmse"], places=12)

    def test_gates_and_shape(self):
        res = self.res
        self.assertTrue(res["gate_GA"])
        self.assertTrue(res["gate_GB"])
        self.assertFalse(res["gate_GE"])          # synthetic data cannot reproduce v3's numbers
        self.assertEqual(res["version"], "0.4.0")
        self.assertEqual(res["base_versions"]["vessel_mix3"], "0.3.0")
        n = 80 * len(res["folds"])
        for m in v4.MODELS:
            for part in ("pooled_in", "pooled_out"):
                self.assertEqual(res[part][m]["n"], n)
                self.assertTrue(math.isfinite(res[part][m]["rmse"]))
            self.assertEqual(sum(d[m]["n"] for d in res["by_site_out"].values()), n)
            self.assertEqual(res["worst_case"][m],
                             max(res["pooled_in"][m]["rmse"], res["pooled_out"][m]["rmse"]))
        self.assertEqual(res["pooled_in"]["F1"]["rmse"], res["pooled_out"]["F1"]["rmse"])

    def test_report(self):
        res = dict(self.res)
        res["grades"] = v4.grade4(res)
        self.assertEqual([x["id"] for x in res["grades"]], list(v4.SIDS))
        json.dumps(res)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.md")
            v4.write_md4(res, path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
        self.assertIn("| G1F |", text)
        self.assertIn("| G1TI |", text)
        self.assertIn("| S7 |", text)
        self.assertIn("| sb03 |", text)


if __name__ == "__main__":
    unittest.main()
