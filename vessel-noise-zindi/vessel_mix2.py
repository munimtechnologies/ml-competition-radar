"""vessel_mix2 0.2.0: can an entrant close the vessel-source gap that vesselmix-v1 measured?

vesselmix-v1 (vessel_mix.py 0.1.0, same folder) built known-answer mixtures of NOAA/U.S. Navy
SanctSound backgrounds and ship passages in the 25 third-octave bands of Zindi's Underwater Vessel
Noise Challenge. A gradient-boosting learner trained on vessel passages from OTHER sites (G1, an
entrant's position) cut RMSE only 8.5% below a constant, while the same learner trained on passages
from the test vessels' own site (G0) cut it 34.5%. Almost all of G1's extra error came from windows
where the vessel carries more than half the energy.

This script re-runs v1's exact folds and test mixtures and adds four G1 variants an entrant could
use without knowing the organisers' vessels:
  G1S   G1 without the spectral-shape features and the absolute level (106 of 132 features)
  G1L   G1 with only the absolute level and the floor share F1 (2 features)
  G1T   G1 trained on augmented vessel passages: a random spectral tilt (uniform +-6 dB per decade
        around 1 kHz), an independent random gain per band (uniform +-2 dB) and, with probability
        0.5, the passage played backwards in time. Same backgrounds, shares and vessel draws as G1.
  G1TS  G1T's training set with G1S's features
G1, G0, C0 and F1 are v1's estimators, reproduced; gate GC checks that G1 reproduces v1's number.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound (NCEI,
doi:10.25921/ymf8-5k59 for the HMD product); used as published, not redistributed here.
Usage: python vessel_mix2.py --data-dir /data/sanctsound --out-dir /out
"""
import argparse
import json
import os
import sys
import time

import numpy as np

import vessel_mix as vm

VERSION = "0.2.0"
TILT_DB = 6.0          # spectral tilt, dB per decade of frequency, drawn uniformly from [-6, +6]
GAIN_DB = 2.0          # independent per-band gain, dB, drawn uniformly from [-2, +2]
P_REVERSE = 0.5        # probability of playing the passage window backwards in time
V1_G1_RMSE = 0.2694491587478854   # vesselmix-v1 pooled RMSE of G1 (results.json, 2026-11-09)
GC_TOL = 1e-6

NF = vm.N_FEATURES     # 132: shape 0-24, range 25-49, sd 50-74, excess 75-99, profile 100-114,
                       # sorted profile 115-129, absolute level 130, floor share F1 131
IDX_ALL = np.arange(NF)
IDX_S = np.array([i for i in range(25, NF) if i != NF - 2])
IDX_L = np.array([NF - 2, NF - 1])
BAND_LOG_F = np.array([n / 10.0 - 3.0 for n in vm.TOL_N])   # log10(band centre / 1 kHz)
MODELS = ("C0", "F1", "G1", "G1S", "G1L", "G1T", "G1TS", "G0")
VARIANTS = ("G1T", "G1S", "G1TS")


def augment(L_db, rng, tilt=TILT_DB, gain=GAIN_DB, p_rev=P_REVERSE):
    """Random spectral tilt, per-band gain and time reversal of a (minutes x 25) level window.
    Always draws the same number of random values, so streams stay aligned whatever the settings."""
    L = np.asarray(L_db, dtype=float)
    t = rng.uniform(-tilt, tilt)
    g = rng.uniform(-gain, gain, size=L.shape[1])
    r = rng.random()
    out = L + t * BAND_LOG_F[None, :] + g[None, :]
    if r < p_rev:
        out = out[::-1].copy()
    return out


def make_set2(rng, bgs, ves, n, aug_rng=None):
    """vm.make_set's draws in the same order (so aug_rng=None reproduces it exactly); with aug_rng,
    each drawn vessel window is augmented before mixing. Shares and draws are unchanged."""
    X, y = [], []
    for _ in range(n):
        b = bgs[int(rng.integers(len(bgs)))]
        s = vm.draw_share(rng)
        v = ves[int(rng.integers(len(ves)))]["L"] if s > 0 else None
        if v is not None and aug_rng is not None:
            v = augment(v, aug_rng)
        L, s = vm.mix(b["L"], v, s)
        X.append(vm.features(L))
        y.append(s)
    return {"X": np.array(X), "y": np.array(y)}


def fp(tr, te, idx, seed):
    return vm.fit_predict(tr["X"][:, idx], tr["y"], te["X"][:, idx], seed)


def analyze2(sites_data, n_test=vm.N_TEST, n_train=vm.N_TRAIN, n_train_days=vm.N_TRAIN_DAYS,
             n_days=vm.N_DAYS, min_passages=vm.MIN_PASSAGES, seed=0):
    built = {sd["site"]: vm.build_site(sd, n_train_days) for sd in sites_data}
    ga, ga_detail = vm.gates(sites_data, n_days)
    bg_train = [g for s in sorted(built) for g in built[s]["bg_train"]]
    bg_test = [g for s in sorted(built) for g in built[s]["bg_test"]]
    vessel_sites = [s for s in sorted(built)
                    if len(built[s]["train_p"]) >= min_passages and len(built[s]["test_p"]) >= min_passages]
    gb = len(vessel_sites) >= 2 and bool(bg_train) and bool(bg_test)
    res = {"version": VERSION, "base_version": vm.VERSION, "gate_GA": ga, "gate_GA_detail": ga_detail,
           "gate_GB": gb, "gate_GC": None, "gate_GC_detail": None, "vessel_sites": vessel_sites,
           "augment": {"tilt_db_per_decade": TILT_DB, "gain_db": GAIN_DB, "p_reverse": P_REVERSE},
           "features": {"G1S": len(IDX_S), "G1L": len(IDX_L), "all": NF},
           "folds": [], "pooled": {}}
    if not gb:
        return res
    pool = {k: [] for k in MODELS + ("y",)}
    for idx, k in enumerate(vessel_sites):
        te = vm.make_set(np.random.default_rng(seed + 1000 + idx), bg_test, built[k]["test_p"], n_test)
        others = [p for s in sorted(built) if s != k for p in built[s]["train_p"]]
        tr1 = make_set2(np.random.default_rng(seed + 2000 + idx), bg_train, others, n_train)
        tr1t = make_set2(np.random.default_rng(seed + 2000 + idx), bg_train, others, n_train,
                         aug_rng=np.random.default_rng(seed + 4000 + idx))
        tr0 = make_set2(np.random.default_rng(seed + 3000 + idx), bg_train, built[k]["train_p"], n_train)
        c0 = float(tr1["y"].mean())
        preds = {"C0": np.full(len(te["y"]), c0), "F1": te["F1"],
                 "G1": fp(tr1, te, IDX_ALL, seed), "G1S": fp(tr1, te, IDX_S, seed),
                 "G1L": fp(tr1, te, IDX_L, seed), "G1T": fp(tr1t, te, IDX_ALL, seed),
                 "G1TS": fp(tr1t, te, IDX_S, seed), "G0": fp(tr0, te, IDX_ALL, seed)}
        res["folds"].append({"test_vessel_site": k, "c0": c0, "train_vessels_G1": len(others),
                             "train_vessels_G0": len(built[k]["train_p"]),
                             "test_vessels": len(built[k]["test_p"]),
                             "same_shares_G1_G1T": bool(np.array_equal(tr1["y"], tr1t["y"])),
                             "stats": {m: vm.stats(p, te["y"]) for m, p in preds.items()}})
        pool["y"].append(te["y"])
        for m in MODELS:
            pool[m].append(preds[m])
    P = {k: np.concatenate(v) for k, v in pool.items()}
    res["pooled"] = {m: vm.stats(P[m], P["y"]) for m in MODELS}
    g1 = res["pooled"]["G1"]["rmse"]
    res["gate_GC"] = bool(abs(g1 - V1_G1_RMSE) <= GC_TOL)
    res["gate_GC_detail"] = {"G1_rmse": g1, "v1_G1_rmse": V1_G1_RMSE, "abs_diff": abs(g1 - V1_G1_RMSE)}
    return res


# ---------------------------------------------------------------- grading (pre-registered)
QIDS = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")


def grade2(res):
    g = []

    def add(pid, text, held, value):
        g.append({"id": pid, "prediction": text, "held": held, "value": value})

    ok = res.get("gate_GA") and res.get("gate_GB") and res.get("pooled")
    if not ok:
        for pid in QIDS:
            add(pid, "ungraded", None, "gate failed (GA=%s, GB=%s)" % (res.get("gate_GA"), res.get("gate_GB")))
        return g
    p = res["pooled"]
    r = {m: p[m]["rmse"] for m in MODELS}
    add("Q1", "pooled RMSE(G1T) < RMSE(G1)", r["G1T"] < r["G1"], {"G1T": r["G1T"], "G1": r["G1"]})
    add("Q2", "pooled RMSE(G1S) < RMSE(G1)", r["G1S"] < r["G1"], {"G1S": r["G1S"], "G1": r["G1"]})
    best = min(VARIANTS, key=lambda m: r[m])
    gap = r["G1"] - r["G0"]
    frac = (r["G1"] - r[best]) / gap if gap > 0 else None
    add("Q3", "the best of G1T, G1S, G1TS closes >= 25% of the pooled RMSE gap from G1 down to G0",
        None if frac is None else frac >= 0.25, {"best": best, "best_rmse": r[best], "fraction_closed": frac})
    others = ("G1T", "G1S", "G1TS", "G1L")
    add("Q4", "pooled RMSE(G0) < RMSE of every G1 variant (G1T, G1S, G1TS, G1L)",
        all(r["G0"] < r[m] for m in others), {m: r[m] for m in ("G0",) + others})
    add("Q5", "pooled RMSE(G1L) < RMSE(C0)", r["G1L"] < r["C0"], {"G1L": r["G1L"], "C0": r["C0"]})
    add("Q6", "pooled RMSE(G1L) < RMSE(G1)", r["G1L"] < r["G1"], {"G1L": r["G1L"], "G1": r["G1"]})
    hb = p[best]["bins"].get("0.5-0.9")
    add("Q7", "the best variant's mean bias on windows with share > 0.5 is below -0.20",
        None if hb is None else hb["bias"] < -0.20, {"best": best, "bin": hb})
    return g


def write_md2(res, path):
    lines = ["# vessel_mix2 %s: automatic results" % res["version"], "",
             "Gates: GA=%s, GB=%s, GC=%s (G1 reproduces v1: %s). Vessel folds: %s." % (
                 res["gate_GA"], res["gate_GB"], res["gate_GC"], json.dumps(res["gate_GC_detail"]),
                 ", ".join(res["vessel_sites"]) or "none")]
    if res["pooled"]:
        folds = res["folds"]
        lines += ["", "| estimator | pooled RMSE | bias | RMSE share>0.5 | bias share>0.5 | RMSE share=0 | " +
                  " | ".join("fold %s" % f["test_vessel_site"] for f in folds) + " |",
                  "|---|---|---|---|---|---|" + "---|" * len(folds)]
        for m in MODELS:
            p = res["pooled"][m]
            hb = p["bins"].get("0.5-0.9", {})
            zb = p["bins"].get("zero", {})
            lines.append("| %s | %.4f | %+.4f | %s | %s | %s | %s |" % (
                m, p["rmse"], p["bias"], "%.4f" % hb["rmse"] if hb else "-", "%+.4f" % hb["bias"] if hb else "-",
                "%.4f" % zb["rmse"] if zb else "-", " | ".join("%.4f" % f["stats"][m]["rmse"] for f in folds)))
    lines += ["", "| id | prediction | held | value |", "|---|---|---|---|"]
    for g in res.get("grades", []):
        lines.append("| %s | %s | %s | `%s` |" % (g["id"], g["prediction"], g["held"], json.dumps(g["value"])[:300]))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="/data/sanctsound")
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    log = {}
    sites_data = [vm.fetch_site(s, a.data_dir, log) for s in vm.SITES]
    res = analyze2(sites_data)
    res["fetch"] = {s: {k: v for k, v in d.items() if k != "days"} for s, d in log.items()}
    res["grades"] = grade2(res)
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(a.out_dir, "results2.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    write_md2(res, os.path.join(a.out_dir, "RESULTS-vesselmix2-auto.md"))
    print(json.dumps({"gates": [res["gate_GA"], res["gate_GB"], res["gate_GC"]],
                      "pooled_rmse": {m: res["pooled"][m]["rmse"] for m in MODELS} if res["pooled"] else None,
                      "grades": [(g["id"], g["held"]) for g in res["grades"]]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
