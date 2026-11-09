"""Offline tests for vessel_mix2 (no network). MV2 of Munim, Inc. Apache-2.0."""
import json
import math
import unittest

import numpy as np

import vessel_mix as vm
import vessel_mix2 as v2

DAY0 = 1440 * 17000


class TestBase(unittest.TestCase):
    def test_base_version(self):
        self.assertEqual(vm.VERSION, "0.1.0")
        self.assertEqual(vm.N_FEATURES, 132)


class TestAugment(unittest.TestCase):
    def setUp(self):
        self.L = np.random.default_rng(3).normal(80, 4, (15, 25))

    def test_identity(self):
        out = v2.augment(self.L, np.random.default_rng(0), tilt=0.0, gain=0.0, p_rev=0.0)
        self.assertTrue(np.array_equal(out, self.L))

    def test_tilt_only(self):
        out = v2.augment(self.L, np.random.default_rng(1), tilt=6.0, gain=0.0, p_rev=0.0)
        d = out - self.L
        self.assertTrue(np.allclose(d, d[0][None, :]))          # same offset every minute
        self.assertAlmostEqual(float(d[0, 15]), 0.0, places=12)  # band 15 is 1 kHz
        slope = (d[0, 24] - d[0, 0]) / 2.4                       # 31.6 Hz -> 7.94 kHz is 2.4 decades
        self.assertLessEqual(abs(slope), 6.0 + 1e-9)
        self.assertTrue(np.allclose(d[0], slope * v2.BAND_LOG_F))

    def test_gain_bounds(self):
        out = v2.augment(self.L, np.random.default_rng(2), tilt=0.0, gain=2.0, p_rev=0.0)
        d = out - self.L
        self.assertTrue(np.allclose(d, d[0][None, :]))
        self.assertLessEqual(float(np.abs(d).max()), 2.0)
        self.assertGreater(float(np.abs(d).max()), 0.0)

    def test_reverse(self):
        out = v2.augment(self.L, np.random.default_rng(0), tilt=0.0, gain=0.0, p_rev=1.0)
        self.assertTrue(np.array_equal(out, self.L[::-1]))
        self.assertTrue(np.array_equal(self.L, np.random.default_rng(3).normal(80, 4, (15, 25))))

    def test_same_draw_count(self):
        a, b = np.random.default_rng(9), np.random.default_rng(9)
        v2.augment(self.L, a, tilt=0.0, gain=0.0, p_rev=0.0)
        v2.augment(self.L, b)
        self.assertEqual(a.random(), b.random())


class TestSubsets(unittest.TestCase):
    def test_indices(self):
        self.assertEqual(len(v2.IDX_S), 106)
        self.assertEqual(list(v2.IDX_L), [130, 131])
        s = set(int(i) for i in v2.IDX_S)
        self.assertFalse(s & set(range(25)))
        self.assertNotIn(130, s)
        self.assertIn(131, s)
        self.assertIn(25, s)
        self.assertIn(129, s)

    def test_subset_is_offset_free(self):
        L = np.random.default_rng(4).normal(80, 4, (15, 25))
        a = vm.features(L)[v2.IDX_S]
        b = vm.features(L + 10.0)[v2.IDX_S]
        self.assertTrue(np.allclose(a, b, atol=1e-6))
        full_a, full_b = vm.features(L), vm.features(L + 10.0)
        self.assertFalse(np.allclose(full_a, full_b, atol=1e-6))   # the absolute level moves


def pools(seed=5, nb=12, nv=4):
    rng = np.random.default_rng(seed)
    bgs = [{"L": rng.normal(80, 2, (15, 25)), "ship": bool(i % 2), "site": "sb01"} for i in range(nb)]
    ves = [{"L": rng.normal(90, 6, (15, 25))} for _ in range(nv)]
    return bgs, ves


class TestMakeSet2(unittest.TestCase):
    def test_reproduces_v1(self):
        bgs, ves = pools()
        a = vm.make_set(np.random.default_rng(7), bgs, ves, 40)
        b = v2.make_set2(np.random.default_rng(7), bgs, ves, 40)
        self.assertTrue(np.array_equal(a["X"], b["X"]))
        self.assertTrue(np.array_equal(a["y"], b["y"]))

    def test_augmented_keeps_shares(self):
        bgs, ves = pools()
        a = v2.make_set2(np.random.default_rng(7), bgs, ves, 40)
        b = v2.make_set2(np.random.default_rng(7), bgs, ves, 40, aug_rng=np.random.default_rng(8))
        self.assertTrue(np.array_equal(a["y"], b["y"]))
        self.assertGreater(int((a["y"] > 0).sum()), 0)
        self.assertFalse(np.allclose(a["X"], b["X"]))
        zero = a["y"] == 0
        self.assertTrue(np.array_equal(a["X"][zero], b["X"][zero]))


def st(r, hb=-0.3):
    return {"rmse": r, "bias": 0.0, "n": 10, "bins": {"0.5-0.9": {"n": 3, "rmse": r, "bias": hb}}}


def fake(gate=True, **over):
    r = {"C0": 0.30, "F1": 0.27, "G1": 0.27, "G1S": 0.25, "G1L": 0.26, "G1T": 0.24, "G1TS": 0.23, "G0": 0.19}
    r.update(over)
    return {"gate_GA": gate, "gate_GB": True, "pooled": {m: st(v) for m, v in r.items()}}


class TestGrade2(unittest.TestCase):
    def test_all_hold(self):
        g = {x["id"]: x["held"] for x in v2.grade2(fake())}
        self.assertEqual(g, {q: True for q in v2.QIDS})
        q3 = [x for x in v2.grade2(fake()) if x["id"] == "Q3"][0]["value"]
        self.assertEqual(q3["best"], "G1TS")
        self.assertAlmostEqual(q3["fraction_closed"], 0.5, places=9)

    def test_some_fail(self):
        r = fake(G1T=0.28, G1S=0.27, G1TS=0.265, G1L=0.18)
        r["pooled"]["G1TS"]["bins"]["0.5-0.9"]["bias"] = -0.1
        g = {x["id"]: x["held"] for x in v2.grade2(r)}
        self.assertFalse(g["Q1"])
        self.assertFalse(g["Q2"])     # equal is not lower
        self.assertFalse(g["Q3"])     # (0.27 - 0.265) / 0.08 = 0.0625
        self.assertFalse(g["Q4"])     # G1L 0.18 beats G0 0.19
        self.assertTrue(g["Q5"])
        self.assertTrue(g["Q6"])
        self.assertFalse(g["Q7"])

    def test_no_gap(self):
        g = {x["id"]: x["held"] for x in v2.grade2(fake(G0=0.28))}
        self.assertIsNone(g["Q3"])

    def test_gate_fail(self):
        g = v2.grade2(fake(gate=False))
        self.assertEqual([x["id"] for x in g], list(v2.QIDS))
        self.assertTrue(all(x["held"] is None for x in g))


def synth_site(name, seed, n_days=3, per_day=6):
    rng = np.random.default_rng(seed)
    tilt = np.linspace(6, -6, 25)
    lv = {}
    for m in range(DAY0, DAY0 + 1440 * n_days):
        lv[m] = 80 + tilt + rng.normal(0, 1, 25)
    ships = []
    shape = np.concatenate([np.full(10, 20.0), np.zeros(15)])
    for d in range(n_days):
        for p in sorted(rng.choice(np.arange(30, 1380, 45), per_day, replace=False)):
            start = DAY0 + 1440 * d + int(p)
            for i in range(20):
                amp = 1 - abs(i - 10) / 10.0
                lv[start + i] = 10 * np.log10(10 ** (lv[start + i] / 10) + 10 ** ((80 + shape * amp) / 10) * (shape > 0))
            ships.append((start * 60.0, (start + 20) * 60.0))
    return {"site": name, "lv": lv, "day_of": {m: (m - DAY0) // 1440 for m in lv}, "ships": ships,
            "days": [{"complete_minutes": 1440}] * n_days}


class TestEndToEnd(unittest.TestCase):
    def test_small_synthetic_run(self):
        sites = [synth_site(s, i) for i, s in enumerate(vm.SITES)]
        kw = dict(n_test=80, n_train=300, n_train_days=2, n_days=3, min_passages=2)
        res = v2.analyze2(sites, **kw)
        self.assertTrue(res["gate_GA"])
        self.assertTrue(res["gate_GB"])
        self.assertFalse(res["gate_GC"])          # synthetic data cannot reproduce v1's number
        self.assertEqual(len(res["folds"]), len(res["vessel_sites"]))
        for f in res["folds"]:
            self.assertTrue(f["same_shares_G1_G1T"])
        for m in v2.MODELS:
            self.assertTrue(math.isfinite(res["pooled"][m]["rmse"]))
            self.assertEqual(res["pooled"][m]["n"], 80 * len(res["folds"]))
        base = vm.analyze(sites, **kw)            # v1 on the same data: G1, G0, C0, F1 identical
        for m in ("C0", "F1", "G1", "G0"):
            self.assertAlmostEqual(res["pooled"][m]["rmse"], base["pooled"][m]["rmse"], places=12)
        res["grades"] = v2.grade2(res)
        self.assertEqual([x["id"] for x in res["grades"]], list(v2.QIDS))
        json.dumps(res)
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.md")
            v2.write_md2(res, path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
        self.assertIn("| G1TS |", text)
        self.assertIn("| Q7 |", text)


if __name__ == "__main__":
    unittest.main()
