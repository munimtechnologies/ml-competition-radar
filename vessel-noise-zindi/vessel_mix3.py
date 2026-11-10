"""vessel_mix3 0.3.0: does the loudness cue survive an unseen background recorder, and does a blend help?

vesselmix-v2 (vessel_mix2.py 0.2.0) found that on account-free SanctSound mixtures, the learner
that sees only the window's absolute level and floor share (G1L) beat v1's 132-feature learner
when training vessels come from other sites (pooled RMSE 0.2342 vs 0.2694), and that randomising
the training vessels' spectra (G1T, 0.2463) helped too. Their errors sit in different share bins.
In v1/v2 the test backgrounds came from the same three recorders as the training backgrounds.

This script re-runs v2's exact folds and test mixtures and adds:
  B      the average of G1L's and G1T's predictions (no extra fitting)
  OUT    for every test window whose background comes from site h, C0, G1L, G1T and B are
         retrained with training backgrounds from the OTHER two sites only (same vessels, shares
         drawn afresh), so the test background's recorder was never seen in training
IN is v2's setting (training backgrounds from all three sites). F1 needs no training.
Gate GD checks that IN G1L and G1T reproduce v2's pooled RMSE.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound (NCEI,
doi:10.25921/ymf8-5k59 for the HMD product); used as published, not redistributed here.
Usage: python vessel_mix3.py --data-dir /data/sanctsound --out-dir /out
"""
import argparse
import json
import os
import sys
import time

import numpy as np

import vessel_mix as vm
import vessel_mix2 as v2

VERSION = "0.3.0"
V2_RMSE = {"G1L": 0.23420903245117503, "G1T": 0.24633835050771377}   # results2.json, 2026-11-09
V2_G1, V2_G0 = 0.2694491587478854, 0.19277983158394127
R2_MAX = V2_G1 - 0.5 * (V2_G1 - V2_G0)                                # 0.2311144951659133...
GD_TOL = 1e-6
MODELS = ("C0", "F1", "G1L", "G1T", "B")
TRAINED = ("C0", "G1L", "G1T", "B")


def fit(X, y, seed=0):
    from sklearn.ensemble import HistGradientBoostingRegressor
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=seed)
    m.fit(X, y)
    return m


def pred(model, X):
    return np.clip(model.predict(X), 0.0, 1.0)


def predict_set(tr, trt, X, seed=0):
    """C0 from tr's mean share, G1L on tr's two loudness features, G1T on trt (augmented), B = mean."""
    gl = pred(fit(tr["X"][:, v2.IDX_L], tr["y"], seed), X[:, v2.IDX_L])
    gt = pred(fit(trt["X"], trt["y"], seed), X)
    return {"C0": np.full(len(X), float(tr["y"].mean())), "G1L": gl, "G1T": gt, "B": 0.5 * (gl + gt)}


def bg_without(bgs, site):
    return [g for g in bgs if g["site"] != site]


def level_summary(b):
    out = {}
    for part in ("bg_train", "bg_test"):
        lv = 10.0 * np.log10(np.array([g["E"] for g in b[part]], dtype=float)) if b[part] else None
        out[part] = None if lv is None else {
            "n": int(len(lv)), "p10_db": float(np.percentile(lv, 10)),
            "median_db": float(np.median(lv)), "p90_db": float(np.percentile(lv, 90))}
    return out


def stats_by(P, y, sites, names):
    return {h: {m: vm.stats(P[m][sites == h], y[sites == h]) for m in names}
            for h in sorted(set(sites.tolist()))}


def analyze3(sites_data, n_test=vm.N_TEST, n_train=vm.N_TRAIN, n_train_days=vm.N_TRAIN_DAYS,
             n_days=vm.N_DAYS, min_passages=vm.MIN_PASSAGES, seed=0):
    built = {sd["site"]: vm.build_site(sd, n_train_days) for sd in sites_data}
    ga, ga_detail = vm.gates(sites_data, n_days)
    bg_train = [g for s in sorted(built) for g in built[s]["bg_train"]]
    bg_test = [g for s in sorted(built) for g in built[s]["bg_test"]]
    vessel_sites = [s for s in sorted(built)
                    if len(built[s]["train_p"]) >= min_passages and len(built[s]["test_p"]) >= min_passages]
    bg_sites = sorted(s for s in built if built[s]["bg_train"])
    gb = len(vessel_sites) >= 2 and bool(bg_train) and bool(bg_test) and len(bg_sites) >= 2
    res = {"version": VERSION, "base_versions": {"vessel_mix": vm.VERSION, "vessel_mix2": v2.VERSION},
           "gate_GA": ga, "gate_GA_detail": ga_detail, "gate_GB": gb, "gate_GD": None,
           "gate_GD_detail": None, "vessel_sites": vessel_sites, "background_sites": bg_sites,
           "site_levels_db": {s: level_summary(built[s]) for s in sorted(built)},
           "folds": [], "pooled_in": {}, "pooled_out": {}, "by_site_in": {}, "by_site_out": {}}
    if not gb:
        return res
    pool = {"y": [], "site": []}
    for c in ("in", "out"):
        for m in MODELS:
            pool[c + ":" + m] = []
    for idx, k in enumerate(vessel_sites):
        te = vm.make_set(np.random.default_rng(seed + 1000 + idx), bg_test, built[k]["test_p"], n_test)
        others = [p for s in sorted(built) if s != k for p in built[s]["train_p"]]
        tr1 = v2.make_set2(np.random.default_rng(seed + 2000 + idx), bg_train, others, n_train)
        tr1t = v2.make_set2(np.random.default_rng(seed + 2000 + idx), bg_train, others, n_train,
                            aug_rng=np.random.default_rng(seed + 4000 + idx))
        pin = predict_set(tr1, tr1t, te["X"], seed)
        pin["F1"] = te["F1"]
        n = len(te["y"])
        pout = {m: np.full(n, np.nan) for m in TRAINED}
        pout["F1"] = te["F1"]
        out_train = {}
        for j, h in enumerate(bg_sites):
            sel = te["site"] == h
            if not sel.any():
                continue
            bgo = bg_without(bg_train, h)
            tro = v2.make_set2(np.random.default_rng(seed + 6000 + 10 * idx + j), bgo, others, n_train)
            trot = v2.make_set2(np.random.default_rng(seed + 6000 + 10 * idx + j), bgo, others, n_train,
                                aug_rng=np.random.default_rng(seed + 7000 + 10 * idx + j))
            ph = predict_set(tro, trot, te["X"][sel], seed)
            for m in TRAINED:
                pout[m][sel] = ph[m]
            out_train[h] = {"train_backgrounds": len(bgo), "test_windows": int(sel.sum()),
                            "c0": float(tro["y"].mean())}
        res["folds"].append({"test_vessel_site": k, "train_vessels": len(others),
                             "test_vessels": len(built[k]["test_p"]), "out": out_train,
                             "stats_in": {m: vm.stats(pin[m], te["y"]) for m in MODELS},
                             "stats_out": {m: vm.stats(pout[m], te["y"]) for m in MODELS}})
        pool["y"].append(te["y"])
        pool["site"].append(te["site"])
        for m in MODELS:
            pool["in:" + m].append(pin[m])
            pool["out:" + m].append(pout[m])
    y = np.concatenate(pool["y"])
    sites = np.concatenate(pool["site"])
    PI = {m: np.concatenate(pool["in:" + m]) for m in MODELS}
    PO = {m: np.concatenate(pool["out:" + m]) for m in MODELS}
    res["pooled_in"] = {m: vm.stats(PI[m], y) for m in MODELS}
    res["pooled_out"] = {m: vm.stats(PO[m], y) for m in MODELS}
    res["by_site_in"] = stats_by(PI, y, sites, MODELS)
    res["by_site_out"] = stats_by(PO, y, sites, MODELS)
    det = {m: {"rmse": res["pooled_in"][m]["rmse"], "v2": V2_RMSE[m],
               "abs_diff": abs(res["pooled_in"][m]["rmse"] - V2_RMSE[m])} for m in V2_RMSE}
    res["gate_GD"] = bool(all(d["abs_diff"] <= GD_TOL for d in det.values()))
    res["gate_GD_detail"] = det
    return res


# ---------------------------------------------------------------- grading (pre-registered)
RIDS = ("R1", "R2", "R3", "R4", "R5", "R6", "R7")


def grade3(res):
    g = []

    def add(pid, text, held, value):
        g.append({"id": pid, "prediction": text, "held": held, "value": value})

    if not (res.get("gate_GA") and res.get("gate_GB") and res.get("pooled_in")):
        for pid in RIDS:
            add(pid, "ungraded", None, "gate failed (GA=%s, GB=%s)" % (res.get("gate_GA"), res.get("gate_GB")))
        return g
    pi = {m: v["rmse"] for m, v in res["pooled_in"].items()}
    po = {m: v["rmse"] for m, v in res["pooled_out"].items()}
    add("R1", "IN: RMSE(B) < min(RMSE(G1L), RMSE(G1T))", pi["B"] < min(pi["G1L"], pi["G1T"]),
        {"B": pi["B"], "G1L": pi["G1L"], "G1T": pi["G1T"]})
    add("R2", "IN: RMSE(B) <= %.6f (closes >= 50%% of v2's G1 -> G0 gap)" % R2_MAX, pi["B"] <= R2_MAX,
        {"B": pi["B"], "threshold": R2_MAX, "fraction_closed": (V2_G1 - pi["B"]) / (V2_G1 - V2_G0)})
    rl, rt = po["G1L"] / pi["G1L"], po["G1T"] / pi["G1T"]
    add("R3", "OUT/IN RMSE ratio of G1L > that of G1T", rl > rt, {"G1L_ratio": rl, "G1T_ratio": rt})
    add("R4", "OUT: RMSE(G1L) > RMSE(G1T)", po["G1L"] > po["G1T"], {"G1L": po["G1L"], "G1T": po["G1T"]})
    bso, bsi = res["by_site_out"], res["by_site_in"]
    v5 = {h: [bso[h]["G1L"]["rmse"], bso[h]["C0"]["rmse"]] for h in sorted(bso)}
    add("R5", "OUT: on at least one background site, RMSE(G1L) > RMSE(C0)",
        any(a > b for a, b in v5.values()), v5)
    v6 = {h: [bsi[h]["G1L"]["rmse"], bsi[h]["G1T"]["rmse"]] for h in sorted(bsi)}
    add("R6", "IN: on every background site, RMSE(G1L) < RMSE(G1T)", all(a < b for a, b in v6.values()), v6)
    add("R7", "RMSE(F1) < OUT RMSE(B)", pi["F1"] < po["B"], {"F1": pi["F1"], "B_out": po["B"]})
    return g


def write_md3(res, path):
    lines = ["# vessel_mix3 %s: automatic results" % res["version"], "",
             "Gates: GA=%s, GB=%s, GD=%s (%s). Vessel folds: %s. Background sites: %s." % (
                 res["gate_GA"], res["gate_GB"], res["gate_GD"], json.dumps(res["gate_GD_detail"]),
                 ", ".join(res["vessel_sites"]) or "none", ", ".join(res["background_sites"]) or "none")]
    lines += ["", "| site | train bg median dB (p10-p90) | test bg median dB (p10-p90) |", "|---|---|---|"]
    for s, v in res["site_levels_db"].items():
        cells = []
        for part in ("bg_train", "bg_test"):
            x = v[part]
            cells.append("-" if not x else "%.1f (%.1f-%.1f)" % (x["median_db"], x["p10_db"], x["p90_db"]))
        lines.append("| %s | %s | %s |" % (s, cells[0], cells[1]))
    if res["pooled_in"]:
        lines += ["", "| estimator | IN RMSE | OUT RMSE | OUT/IN | IN RMSE share=0 | OUT RMSE share=0 | "
                  "IN RMSE share>0.5 | OUT RMSE share>0.5 |", "|---|---|---|---|---|---|---|---|"]
        for m in MODELS:
            a, b = res["pooled_in"][m], res["pooled_out"][m]

            def cell(p, k):
                return "%.4f" % p["bins"][k]["rmse"] if k in p["bins"] else "-"
            lines.append("| %s | %.4f | %.4f | %.3f | %s | %s | %s | %s |" % (
                m, a["rmse"], b["rmse"], b["rmse"] / a["rmse"] if a["rmse"] else float("nan"),
                cell(a, "zero"), cell(b, "zero"), cell(a, "0.5-0.9"), cell(b, "0.5-0.9")))
        lines += ["", "| background site | n | " + " | ".join("IN %s" % m for m in MODELS) + " | " +
                  " | ".join("OUT %s" % m for m in MODELS) + " |", "|---|---|" + "---|" * (2 * len(MODELS))]
        for h in sorted(res["by_site_in"]):
            si, so = res["by_site_in"][h], res["by_site_out"][h]
            lines.append("| %s | %d | %s | %s |" % (h, si["C0"]["n"],
                         " | ".join("%.4f" % si[m]["rmse"] for m in MODELS),
                         " | ".join("%.4f" % so[m]["rmse"] for m in MODELS)))
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
    res = analyze3(sites_data)
    res["fetch"] = {s: {k: v for k, v in d.items() if k != "days"} for s, d in log.items()}
    res["grades"] = grade3(res)
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(a.out_dir, "results3.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    write_md3(res, os.path.join(a.out_dir, "RESULTS-vesselmix3-auto.md"))
    print(json.dumps({"gates": [res["gate_GA"], res["gate_GB"], res["gate_GD"]],
                      "in": {m: v["rmse"] for m, v in res["pooled_in"].items()},
                      "out": {m: v["rmse"] for m, v in res["pooled_out"].items()},
                      "grades": [(g["id"], g["held"]) for g in res["grades"]]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
