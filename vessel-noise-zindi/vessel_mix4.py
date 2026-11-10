"""vessel_mix4 0.4.0: do gain-free learners keep their gain on an unseen background recorder?

vesselmix-v3 (vessel_mix3.py 0.3.0) found that on account-free SanctSound mixtures, the loudness
learner G1L, the randomised-spectrum learner G1T and their average B all beat a constant when the
test background's recorder was among the training recorders (IN), and all did worse than the
constant when it was held out (OUT). The untrained floor estimator F1, which a gain offset cannot
move, was the best model in OUT. The one input of G1L and G1T that a gain offset moves is the
window's absolute level (feature 130).

This script re-runs v3's analysis through v3's own code (same folds, seeds, training sets and test
windows) and adds two learners, each removing ONE thing from an existing one:
  G1F    G1L without the absolute level: a learned calibration of the floor share (1 feature)
  G1TI   G1T without the absolute level (131 features, all unaffected by a gain offset)
Gate GE checks that C0/G1L/G1T/B reproduce v3's pooled IN and OUT RMSE.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound (NCEI,
doi:10.25921/ymf8-5k59 for the HMD product); used as published, not redistributed here.
Usage: python vessel_mix4.py --data-dir /data/sanctsound --out-dir /out
"""
import argparse
import json
import os
import sys
import time

import numpy as np

import vessel_mix as vm
import vessel_mix2 as v2
import vessel_mix3 as v3

VERSION = "0.4.0"
IDX_F = np.array([v2.NF - 1])                                   # floor share only
IDX_TI = np.array([i for i in range(v2.NF) if i != v2.NF - 2])  # everything but the absolute level
MODELS = ("C0", "F1", "G1L", "G1T", "B", "G1F", "G1TI")
TRAINED = ("C0", "G1L", "G1T", "B", "G1F", "G1TI")
V3_RMSE = {  # results3.json, 2026-11-10
    "pooled_in": {"C0": 0.29430116814239327, "G1L": 0.23420903245117503, "G1T": 0.24633835050771377,
                  "B": 0.22513543865984875},
    "pooled_out": {"C0": 0.29436815912717373, "G1L": 0.35870221882164427, "G1T": 0.37436427871655276,
                   "B": 0.35923512166080196}}
GE_TOL = 1e-6
S6_MAX = 1.10

_V3_PREDICT = v3.predict_set


def predict_set4(tr, trt, X, seed=0):
    """v3's C0/G1L/G1T/B, plus G1F (tr, floor share only) and G1TI (trt, all but absolute level)."""
    p = _V3_PREDICT(tr, trt, X, seed)
    p["G1F"] = v3.pred(v3.fit(tr["X"][:, IDX_F], tr["y"], seed), X[:, IDX_F])
    p["G1TI"] = v3.pred(v3.fit(trt["X"][:, IDX_TI], trt["y"], seed), X[:, IDX_TI])
    return p


def analyze4(sites_data, **kw):
    """Run v3.analyze3 unchanged with the two extra learners plugged in, then restore v3."""
    saved = (v3.predict_set, v3.MODELS, v3.TRAINED)
    v3.predict_set, v3.MODELS, v3.TRAINED = predict_set4, MODELS, TRAINED
    try:
        res = v3.analyze3(sites_data, **kw)
    finally:
        v3.predict_set, v3.MODELS, v3.TRAINED = saved
    res["version"] = VERSION
    res["base_versions"]["vessel_mix3"] = v3.VERSION
    res["features"] = {"G1F": len(IDX_F), "G1TI": len(IDX_TI), "G1L": len(v2.IDX_L), "G1T": v2.NF}
    res["gate_GE"], res["gate_GE_detail"], res["worst_case"] = None, None, {}
    if res.get("pooled_in"):
        det = {part: {m: {"rmse": res[part][m]["rmse"], "v3": v,
                          "abs_diff": abs(res[part][m]["rmse"] - v)} for m, v in d.items()}
               for part, d in V3_RMSE.items()}
        res["gate_GE"] = bool(all(x["abs_diff"] <= GE_TOL for d in det.values() for x in d.values()))
        res["gate_GE_detail"] = det
        res["worst_case"] = {m: max(res["pooled_in"][m]["rmse"], res["pooled_out"][m]["rmse"])
                             for m in MODELS}
    return res


# ---------------------------------------------------------------- grading (pre-registered)
SIDS = ("S1", "S2", "S3", "S4", "S5", "S6", "S7")


def grade4(res):
    g = []

    def add(pid, text, held, value):
        g.append({"id": pid, "prediction": text, "held": held, "value": value})

    if not (res.get("gate_GA") and res.get("gate_GB") and res.get("pooled_in")):
        for pid in SIDS:
            add(pid, "ungraded", None, "gate failed (GA=%s, GB=%s)" % (res.get("gate_GA"), res.get("gate_GB")))
        return g
    pi = {m: v["rmse"] for m, v in res["pooled_in"].items()}
    po = {m: v["rmse"] for m, v in res["pooled_out"].items()}
    add("S1", "IN: RMSE(G1F) < RMSE(F1)", pi["G1F"] < pi["F1"], {"G1F": pi["G1F"], "F1": pi["F1"]})
    add("S2", "OUT: RMSE(G1F) < RMSE(F1)", po["G1F"] < po["F1"], {"G1F": po["G1F"], "F1": po["F1"]})
    add("S3", "OUT: RMSE(G1F) < RMSE(G1L)", po["G1F"] < po["G1L"], {"G1F": po["G1F"], "G1L": po["G1L"]})
    add("S4", "OUT: RMSE(G1TI) < RMSE(G1T)", po["G1TI"] < po["G1T"], {"G1TI": po["G1TI"], "G1T": po["G1T"]})
    add("S5", "IN: RMSE(G1TI) > RMSE(G1T)", pi["G1TI"] > pi["G1T"], {"G1TI": pi["G1TI"], "G1T": pi["G1T"]})
    r6 = po["G1F"] / pi["G1F"]
    add("S6", "RMSE_OUT(G1F) / RMSE_IN(G1F) < %.2f" % S6_MAX, r6 < S6_MAX,
        {"ratio": r6, "in": pi["G1F"], "out": po["G1F"]})
    bso = res["by_site_out"]
    v7 = {h: [bso[h]["G1F"]["rmse"], bso[h]["C0"]["rmse"]] for h in sorted(bso)}
    add("S7", "OUT: on every background site, RMSE(G1F) < RMSE(C0)", all(a < b for a, b in v7.values()), v7)
    return g


def write_md4(res, path):
    lines = ["# vessel_mix4 %s: automatic results" % res["version"], "",
             "Gates: GA=%s, GB=%s, GD=%s, GE=%s. Vessel folds: %s. Background sites: %s." % (
                 res["gate_GA"], res["gate_GB"], res["gate_GD"], res["gate_GE"],
                 ", ".join(res["vessel_sites"]) or "none", ", ".join(res["background_sites"]) or "none"),
             "", "GE detail: `%s`" % json.dumps(res["gate_GE_detail"])]
    if res["pooled_in"]:
        lines += ["", "| estimator | IN RMSE | OUT RMSE | OUT/IN | worst case | IN bias | OUT bias | "
                  "OUT RMSE share=0 | OUT RMSE share>0.5 |", "|---|---|---|---|---|---|---|---|---|"]
        for m in MODELS:
            a, b = res["pooled_in"][m], res["pooled_out"][m]

            def cell(p, k):
                return "%.4f" % p["bins"][k]["rmse"] if k in p["bins"] else "-"
            lines.append("| %s | %.4f | %.4f | %.3f | %.4f | %+.3f | %+.3f | %s | %s |" % (
                m, a["rmse"], b["rmse"], b["rmse"] / a["rmse"] if a["rmse"] else float("nan"),
                res["worst_case"][m], a["bias"], b["bias"], cell(b, "zero"), cell(b, "0.5-0.9")))
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
    res = analyze4(sites_data)
    res["fetch"] = {s: {k: v for k, v in d.items() if k != "days"} for s, d in log.items()}
    res["grades"] = grade4(res)
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(a.out_dir, "results4.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    write_md4(res, os.path.join(a.out_dir, "RESULTS-vesselmix4-auto.md"))
    print(json.dumps({"gates": [res["gate_GA"], res["gate_GB"], res["gate_GD"], res["gate_GE"]],
                      "in": {m: v["rmse"] for m, v in res["pooled_in"].items()},
                      "out": {m: v["rmse"] for m, v in res["pooled_out"].items()},
                      "grades": [(g["id"], g["held"]) for g in res["grades"]]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
