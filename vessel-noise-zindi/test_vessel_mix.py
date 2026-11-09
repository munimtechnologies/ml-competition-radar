"""Offline tests for vessel_mix (no network, no netCDF files). MV2 of Munim, Inc. Apache-2.0."""
import math
import unittest

import numpy as np

import vessel_mix as vm

DAY0 = 1440 * 17000  # an epoch minute at 00:00 UTC


def hmd_grid():
    f1 = np.arange(20, 436, dtype=float)
    mk = np.arange(2639, int(1000 * math.log10(24000)) + 1)
    return np.concatenate([f1, 10.0 ** (mk / 1000.0)])


class TestBands(unittest.TestCase):
    def test_edges(self):
        e = vm.tol_edges()
        self.assertEqual(len(e), 25)
        self.assertAlmostEqual(math.sqrt(e[0][0] * e[0][1]), 31.6228, places=3)
        self.assertAlmostEqual(math.sqrt(e[-1][0] * e[-1][1]), 7943.28, places=1)
        for a, b in zip(e, e[1:]):
            self.assertAlmostEqual(a[1] / b[0], 1.0, places=9)

    def test_flat_psd_gives_bandwidth(self):
        f = hmd_grid()
        W = vm.tol_matrix(f)
        out = vm.psd_db_to_tol_db(np.zeros((2, len(f))), W)
        for j, (lo, hi) in enumerate(vm.tol_edges()):
            got = 10 ** (out[0, j] / 10)
            self.assertLess(abs(got / (hi - lo) - 1), 0.1, (j, got, hi - lo))
        self.assertTrue(np.allclose(out[0], out[1]))

    def test_nan_only_poisons_used_bins(self):
        f = hmd_grid()
        W = vm.tol_matrix(f)
        psd = np.zeros((3, len(f)))
        psd[1, int(np.where(f == 30)[0][0])] = np.nan
        psd[2, int(np.argmin(abs(f - 20000)))] = np.nan
        out = vm.psd_db_to_tol_db(psd, W)
        self.assertTrue(np.all(np.isnan(out[1])))
        self.assertTrue(np.all(np.isfinite(out[0])))
        self.assertTrue(np.allclose(out[0], out[2]))


class TestLabels(unittest.TestCase):
    def test_epoch_and_minutes(self):
        self.assertEqual(vm.iso_to_epoch("1970-01-01T00:01:00.000Z"), 60.0)
        self.assertEqual(vm.ship_minutes([(65.0, 179.0)]), {1, 2})
        self.assertEqual(vm.ship_minutes([(60.0, 180.0)]), {1, 2, 3})

    def test_parse_ships(self):
        text = ("ISOStartTime,ISOEndTime,Labels\n"
                "2018-11-12T20:22:05.000Z,2018-11-12T20:31:00.000Z,ship\n"
                "\n"
                "2018-11-12T19:00:05.000Z,2018-11-12T19:54:35.000Z,ship\n"
                "2018-11-12T21:00:00.000Z,2018-11-12T21:10:00.000Z,0\n")
        s = vm.parse_ships(text)
        self.assertEqual(len(s), 2)
        self.assertLess(s[0][0], s[1][0])
        self.assertEqual(s[0][1] - s[0][0], 54 * 60 + 30)


class TestMixAndEstimators(unittest.TestCase):
    def test_mix_share_exact(self):
        rng = np.random.default_rng(1)
        B = rng.normal(80, 3, (15, 25))
        V = rng.normal(90, 5, (15, 25))
        M, s = vm.mix(B, V, 0.3)
        PB, PM = 10 ** (B / 10), 10 ** (M / 10)
        self.assertAlmostEqual((PM.sum() - PB.sum()) / PM.sum(), 0.3, places=9)
        self.assertEqual(s, 0.3)
        M0, s0 = vm.mix(B, None, 0.0)
        self.assertTrue(np.array_equal(M0, B))
        self.assertEqual(s0, 0.0)

    def test_floor_share(self):
        self.assertAlmostEqual(vm.floor_share(np.zeros((15, 25))), 0.0, places=12)
        L = np.zeros((15, 25))
        L[5:10] = 10.0
        self.assertAlmostEqual(vm.floor_share(L), 0.75, places=9)

    def test_features_offset_invariant(self):
        rng = np.random.default_rng(2)
        L = rng.normal(80, 4, (15, 25))
        a, b = vm.features(L), vm.features(L + 10)
        self.assertEqual(len(a), vm.N_FEATURES)
        self.assertTrue(np.all(np.isfinite(a)))
        keep = np.ones(len(a), bool)
        keep[-2] = False
        self.assertTrue(np.allclose(a[keep], b[keep], atol=1e-6))
        self.assertAlmostEqual(b[-2] - a[-2], 10.0, places=6)


def flat_site(name):
    lv = {DAY0 + i: np.zeros(25) for i in range(1440)}
    ships = []
    for k, (off, boost) in enumerate([(100, 10.0), (300, 10.0), (500, 10.0), (700, 10.0), (900, 1.0)]):
        p = DAY0 + off
        for i in range(15):
            lv[p + i] = np.full(25, boost)
        ships.append((p * 60.0, (p + 15) * 60.0))
    return {"site": name, "lv": lv, "day_of": {m: 0 for m in lv}, "ships": ships,
            "days": [{"complete_minutes": 1440}]}


class TestSite(unittest.TestCase):
    def test_parity_and_snr(self):
        b = vm.build_site(flat_site("sb01"), n_train_days=1)
        self.assertEqual(len(b["grid"]), 96)
        self.assertAlmostEqual(b["median_window_energy"], 375.0, places=6)
        self.assertEqual(b["passage_windows_complete"], 5)
        self.assertEqual(len(b["train_p"]), 2)
        self.assertEqual(len(b["test_p"]), 2)
        self.assertEqual([p["m0"] for p in b["train_p"]], [DAY0 + 100, DAY0 + 500])
        self.assertAlmostEqual(b["train_p"][0]["snr_db"], 10.0, places=6)
        self.assertEqual(len(b["bg_train"]), 96)
        self.assertEqual(len(b["bg_test"]), 0)
        self.assertGreaterEqual(sum(g["ship"] for g in b["grid"]), 5)


def fake_res(gate=True):
    st = lambda r: {"rmse": r, "bias": 0.0, "bins": {}, "n": 10}
    return {"gate_GA": gate, "gate_GB": True,
            "folds": [{"test_vessel_site": "sb01", "stats": {"G0": st(0.10), "G1": st(0.12)}},
                      {"test_vessel_site": "sb03", "stats": {"G0": st(0.09), "G1": st(0.11)}}],
            "pooled": {"C0": st(0.30), "F1": st(0.25), "G0": st(0.10), "G1": st(0.12),
                       "F1_mean_on_zero": 0.1, "F1_bias_share_ge_0.5": -0.1,
                       "P7_by_site": {"sb01": {"n_ship": 30, "n_noship": 25, "G1_mean_ship": 0.2, "G1_mean_noship": 0.1},
                                      "gr01": {"n_ship": 2, "n_noship": 50, "G1_mean_ship": 0.0, "G1_mean_noship": 0.1}}}}


class TestGrade(unittest.TestCase):
    def test_all_hold(self):
        g = {x["id"]: x["held"] for x in vm.grade(fake_res())}
        self.assertEqual(g, {"P1": True, "P2": True, "P3": True, "P4": True, "P5": True, "P6": True, "P7": True})

    def test_some_fail(self):
        r = fake_res()
        r["pooled"]["G1"]["rmse"] = 0.2
        r["pooled"]["F1_mean_on_zero"] = 0.01
        g = {x["id"]: x["held"] for x in vm.grade(r)}
        self.assertFalse(g["P1"])
        self.assertTrue(g["P3"])
        self.assertTrue(g["P4"])
        self.assertFalse(g["P5"])

    def test_gate_fail(self):
        g = vm.grade(fake_res(gate=False))
        self.assertEqual(len(g), 7)
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


try:
    import netCDF4  # noqa: F401
    HAVE_NC = True
except ImportError:
    HAVE_NC = False


@unittest.skipUnless(HAVE_NC, "netCDF4 not installed")
class TestReadHmd(unittest.TestCase):
    def _write(self, path, transpose):
        import netCDF4
        f = hmd_grid()[:50]
        day0 = vm.file_day0_minute(path)
        ds = netCDF4.Dataset(path, "w")
        ds.createDimension("time", 3)
        ds.createDimension("frequency", len(f))
        fv = ds.createVariable("frequency", "f8", ("frequency",))
        fv[:] = f
        tv = ds.createVariable("time", "f8", ("time",))
        tv.units = "seconds since 1970-01-01 00:00:00"
        tv[:] = day0 * 60.0 + np.array([0.0, 60.0, 120.0])
        dims = ("frequency", "time") if transpose else ("time", "frequency")
        pv = ds.createVariable("psd", "f4", dims, fill_value=-9999.0)
        data = np.arange(3 * len(f), dtype=float).reshape(3, len(f)) % 7
        pv[:] = data.T if transpose else data
        if transpose:
            pv[5, 1] = np.ma.masked
        else:
            pv[1, 5] = np.ma.masked
        ds.close()
        return f, day0, data

    def test_read_both_orientations(self):
        import os
        import tempfile
        for transpose in (False, True):
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "NEFSC_SBNMS_201811_SB01_20181113.nc")
                f, day0, data = self._write(path, transpose)
                freqs, minutes, arr, meta = vm.read_hmd(path)
                self.assertEqual(len(freqs), len(f))
                self.assertEqual(arr.shape, (3, len(f)))
                self.assertEqual(minutes, [day0, day0 + 1, day0 + 2])
                self.assertEqual(meta["time_method"], "time variable")
                self.assertEqual(meta["psd_var"], "psd")
                self.assertTrue(np.isnan(arr[1, 5]))
                self.assertEqual(arr[2, 7], data[2, 7])


class TestEndToEnd(unittest.TestCase):
    def test_small_synthetic_run(self):
        sites = [synth_site(s, i) for i, s in enumerate(vm.SITES)]
        res = vm.analyze(sites, n_test=80, n_train=300, n_train_days=2, n_days=3, min_passages=2)
        self.assertTrue(res["gate_GA"])
        self.assertTrue(res["gate_GB"])
        self.assertGreaterEqual(len(res["vessel_sites"]), 2)
        self.assertEqual(len(res["folds"]), len(res["vessel_sites"]))
        for m in ("C0", "F1", "G0", "G1"):
            self.assertTrue(math.isfinite(res["pooled"][m]["rmse"]))
            self.assertEqual(res["pooled"][m]["n"], 80 * len(res["folds"]))
        g = vm.grade(res)
        self.assertEqual([x["id"] for x in g], ["P1", "P2", "P3", "P4", "P5", "P6", "P7"])
        self.assertIsNotNone(g[0]["held"])
        import json
        json.dumps(res)


if __name__ == "__main__":
    unittest.main()
