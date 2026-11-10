"""vessel_mix5 0.5.0: does training on more recorders shrink the unseen-recorder penalty?

vesselmix-v3 and v4 (vessel_mix3.py 0.3.0, vessel_mix4.py 0.4.0) found that on account-free
SanctSound mixtures, every trained learner beat a constant when the test background's recorder was
among the three training recorders, and lost to the constant when it was held out, even with
gain-free inputs. Only the untrained floor share F1 kept its edge. But those models saw only two
recorders' backgrounds; Zindi's Underwater Vessel Noise Challenge releases ten sites.

SanctSound publishes 1-minute HMD spectra for many deployments of SB01, SB03 (21 each) and GR01 (7).
Each deployment is a separate recording period (and usually a separately calibrated instrument).
This script treats deployments 01-07 of each site as 21 background "recorders" (5 daily files
each: days 0-2 train, days 3-4 test) and, for every held-out recorder t, retrains the v3/v4
learners on backgrounds from:
  Dn     n random other recorders (nested: D1 inside D2 inside ... D16), any site
  Sn     n random recorders from the OTHER two sites only; SALL = all of them
  SAME   the other deployments of t's own site only
  INn    t itself plus the first n-1 recorders of Dn's order (t's training days, never its test days)
Vessel passages are v1's exactly (deployment 01 of SB01/SB03, leave one vessel site out), so only
the backgrounds change. Learners (unchanged code from v1-v4): C0 constant, F1 untrained floor
share, G1F learned floor share, G1L level + floor share, G1T 132 features on randomised vessel
spectra, B = (G1L + G1T) / 2.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound (NCEI,
doi:10.25921/ymf8-5k59 for the HMD product); used as published, not redistributed here.
Usage: python vessel_mix5.py --data-dir /data/sanctsound --out-dir /out
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

VERSION = "0.5.0"
SITES = ("gr01", "sb01", "sb03")
DEPS = ("01", "02", "03", "04", "05", "06", "07")
N_DEP_FILES = 5            # daily HMD files per extra deployment: the 2nd to the 6th in name order
TRAIN_DAYS = (0, 1, 2)
TEST_DAYS = (3, 4)
N_TEST_FOLD = 100          # test mixtures per held-out recorder and vessel fold
NS = (1, 2, 4, 8, 16)
S_NS = (1, 4)
IN_N = 16
MIN_RECORDERS = 15
MIN_PER_SITE = 4
MIN_TRAIN_WIN = 150        # of 288 possible
MIN_TEST_WIN = 80          # of 192 possible
MODELS = ("C0", "F1", "G1F", "G1L", "G1T", "B")
IDX_F = np.array([v2.NF - 1])   # floor share only (v4's G1F)


def cond_names(ns=NS, s_ns=S_NS, in_n=IN_N):
    return tuple(["D%d" % n for n in ns] + ["S%d" % n for n in s_ns] + ["SALL", "SAME", "IN%d" % in_n])


CONDS = cond_names()


# ---------------------------------------------------------------- data
def fetch_recorder(site, dep, data_dir, log):
    """v1's vm.fetch_site for one deployment and N_DEP_FILES days; vm's globals are restored."""
    saved = (vm.DEPLOYMENT, vm.N_DAYS)
    vm.DEPLOYMENT, vm.N_DAYS = dep, N_DEP_FILES
    sub = {}
    try:
        sd = vm.fetch_site(site, os.path.join(data_dir, "dep" + dep), sub)
    finally:
        vm.DEPLOYMENT, vm.N_DAYS = saved
    info = sub.get(site, {})
    log["%s_%s" % (site, dep)] = {"hmd_files_listed": info.get("hmd_files_listed"), "error": info.get("error"),
                                  "complete_minutes": [d.get("complete_minutes") for d in info.get("days", [])]}
    return sd


def build_recorder(sd, name):
    """v1's 15-minute background grid for one recorder, split by day into train and test."""
    b = vm.build_site(sd, n_train_days=len(TRAIN_DAYS))
    for g in b["grid"]:
        g["rec"] = name
    tr = [g for g in b["grid"] if g["day"] in TRAIN_DAYS]
    te = [g for g in b["grid"] if g["day"] in TEST_DAYS]
    lv = 10.0 * np.log10(np.array([g["E"] for g in tr], dtype=float)) if tr else None
    return {"site": sd["site"], "train": tr, "test": te,
            "median_train_db": None if lv is None else float(np.median(lv))}


def conditions(t, usable, site_of, rng, ns=NS, s_ns=S_NS, in_n=IN_N):
    """Training-background recorder lists for held-out recorder t (nested random orders)."""
    others = [n for n in usable if n != t]
    other_site = [n for n in others if site_of[n] != site_of[t]]
    same_site = [n for n in others if site_of[n] == site_of[t]]
    perm = [others[i] for i in rng.permutation(len(others))]
    perm_s = [other_site[i] for i in rng.permutation(len(other_site))]
    c = {}
    for n in ns:
        if n <= len(others):
            c["D%d" % n] = perm[:n]
    for n in s_ns:
        if n <= len(other_site):
            c["S%d" % n] = perm_s[:n]
    if other_site:
        c["SALL"] = list(other_site)
    if same_site:
        c["SAME"] = list(same_site)
    if in_n - 1 <= len(others):
        c["IN%d" % in_n] = [t] + perm[:in_n - 1]
    return c


# ---------------------------------------------------------------- learners
def predict5(tr, trt, X, seed=0):
    """v3's C0/G1L/G1T/B unchanged, plus v4's G1F (floor share only, trained on tr)."""
    p = v3.predict_set(tr, trt, X, seed)
    p["G1F"] = v3.pred(v3.fit(tr["X"][:, IDX_F], tr["y"], seed), X[:, IDX_F])
    return p


def rmse(p, y):
    return float(np.sqrt(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2)))


def analyze5(sd01, recs, n_test=N_TEST_FOLD, n_train=vm.N_TRAIN, seed=0, ns=NS, s_ns=S_NS, in_n=IN_N,
             min_recorders=MIN_RECORDERS, min_per_site=MIN_PER_SITE, min_train=MIN_TRAIN_WIN,
             min_test=MIN_TEST_WIN, min_passages=vm.MIN_PASSAGES):
    """sd01: v1's three deployment-01 site records (vessel passages). recs: [(name, site record)]."""
    built01 = {sd["site"]: vm.build_site(sd) for sd in sd01}
    vessel_sites = [s for s in sorted(built01) if len(built01[s]["train_p"]) >= min_passages
                    and len(built01[s]["test_p"]) >= min_passages]
    R = {name: build_recorder(sd, name) for name, sd in recs}
    site_of = {n: R[n]["site"] for n in R}
    usable = sorted(n for n in R if len(R[n]["train"]) >= min_train and len(R[n]["test"]) >= min_test)
    per_site = {s: sum(1 for n in usable if site_of[n] == s) for s in sorted(set(site_of.values()))}
    ga = len(usable) >= min_recorders and all(v >= min_per_site for v in per_site.values())
    gb = len(vessel_sites) >= 2
    names = cond_names(ns, s_ns, in_n)
    res = {"version": VERSION,
           "base_versions": {"vessel_mix": vm.VERSION, "vessel_mix2": v2.VERSION, "vessel_mix3": v3.VERSION},
           "gate_GA": bool(ga), "gate_GB": bool(gb), "gate_GC": None, "usable": usable, "per_site": per_site,
           "recorders": {n: {"site": R[n]["site"], "train_windows": len(R[n]["train"]),
                             "test_windows": len(R[n]["test"]), "median_train_db": R[n]["median_train_db"]}
                         for n in sorted(R)},
           "vessel_sites": vessel_sites,
           "vessel_passages": {s: [len(built01[s]["train_p"]), len(built01[s]["test_p"])] for s in sorted(built01)},
           "conditions": list(names), "pooled": {}, "complete": {}, "n_recorders": {}, "by_site": {},
           "per_recorder": {}, "trend_G1L": None}
    if not (ga and gb):
        return res
    store = {c: {"y": [], "site": [], "P": {m: [] for m in MODELS}} for c in names}
    for ti, t in enumerate(usable):
        conds = conditions(t, usable, site_of, np.random.default_rng(seed + 50000 + ti), ns, s_ns, in_n)
        acc = {}
        for idx, k in enumerate(vessel_sites):
            te = vm.make_set(np.random.default_rng(seed + 60000 + 10 * ti + idx), R[t]["test"],
                             built01[k]["test_p"], n_test)
            ves = [p for s in sorted(built01) if s != k for p in built01[s]["train_p"]]
            for ci, c in enumerate(names):
                if c not in conds:
                    continue
                bgs = [g for n in conds[c] for g in R[n]["train"]]
                s0 = seed + 100000 + 10000 * ti + 1000 * idx + 10 * ci
                tr = v2.make_set2(np.random.default_rng(s0), bgs, ves, n_train)
                trt = v2.make_set2(np.random.default_rng(s0), bgs, ves, n_train,
                                   aug_rng=np.random.default_rng(s0 + 5))
                p = predict5(tr, trt, te["X"], seed)
                p["F1"] = te["F1"]
                a = acc.setdefault(c, {"y": [], "P": {m: [] for m in MODELS}})
                a["y"].append(te["y"])
                for m in MODELS:
                    a["P"][m].append(p[m])
        res["per_recorder"][t] = {"site": site_of[t], "conditions": conds, "rmse": {}}
        for c in names:
            if c not in acc:
                continue
            y = np.concatenate(acc[c]["y"])
            P = {m: np.concatenate(acc[c]["P"][m]) for m in MODELS}
            res["per_recorder"][t]["rmse"][c] = {m: rmse(P[m], y) for m in MODELS}
            st = store[c]
            st["y"].append(y)
            st["site"].append(np.array([site_of[t]] * len(y)))
            for m in MODELS:
                st["P"][m].append(P[m])
    for c in names:
        k = len(store[c]["y"])
        res["n_recorders"][c] = k
        res["complete"][c] = k == len(usable)
        if not k:
            continue
        y = np.concatenate(store[c]["y"])
        sites = np.concatenate(store[c]["site"])
        P = {m: np.concatenate(store[c]["P"][m]) for m in MODELS}
        res["pooled"][c] = {m: vm.stats(P[m], y) for m in MODELS}
        res["by_site"][c] = v3.stats_by(P, y, sites, MODELS)
    res["gate_GC"] = bool(all(res["complete"].values()))
    lo, hi = "D%d" % min(ns), "D%d" % max(ns)
    both = [t for t in usable if lo in res["per_recorder"][t]["rmse"] and hi in res["per_recorder"][t]["rmse"]]
    res["trend_G1L"] = {"from": lo, "to": hi, "recorders": len(both),
                        "lower_at_to": sum(1 for t in both if res["per_recorder"][t]["rmse"][hi]["G1L"]
                                           < res["per_recorder"][t]["rmse"][lo]["G1L"])}
    return res


# ---------------------------------------------------------------- grading (pre-registered)
TIDS = ("T1", "T2", "T3", "T4", "T5", "T6", "T7")


def grade5(res):
    g = []

    def add(pid, text, held, value):
        g.append({"id": pid, "prediction": text, "held": held, "value": value})

    if not (res.get("gate_GA") and res.get("gate_GB") and res.get("pooled")):
        for pid in TIDS:
            add(pid, "ungraded", None, "gate failed (GA=%s, GB=%s)" % (res.get("gate_GA"), res.get("gate_GB")))
        return g
    P, comp = res["pooled"], res.get("complete", {})

    def r(c, m):
        if c not in P or not comp.get(c):
            return None
        return P[c][m]["rmse"]

    def less(pid, text, a, b):
        add(pid, text, None if a is None or b is None else bool(a < b), {"lhs": a, "rhs": b})

    less("T1", "G1L: RMSE(D16) < RMSE(D1)", r("D16", "G1L"), r("D1", "G1L"))
    less("T2", "D16: RMSE(G1L) < RMSE(C0)", r("D16", "G1L"), r("D16", "C0"))
    less("T3", "D16: RMSE(B) < RMSE(F1)", r("D16", "B"), r("D16", "F1"))
    t1, t16, l1, l16 = r("D1", "G1T"), r("D16", "G1T"), r("D1", "G1L"), r("D16", "G1L")
    text4 = "RMSE(D1)/RMSE(D16) larger for G1T than for G1L"
    if None in (t1, t16, l1, l16):
        add("T4", text4, None, {"G1T": [t1, t16], "G1L": [l1, l16]})
    else:
        add("T4", text4, bool(t1 / t16 > l1 / l16),
            {"G1T_ratio": t1 / t16, "G1L_ratio": l1 / l16, "G1T": [t1, t16], "G1L": [l1, l16]})
    less("T5", "G1L: RMSE(SAME) < RMSE(SALL)", r("SAME", "G1L"), r("SALL", "G1L"))
    less("T6", "G1L: RMSE(IN16) < RMSE(D16)", r("IN16", "G1L"), r("D16", "G1L"))
    less("T7", "D16: RMSE(G1F) < RMSE(F1)", r("D16", "G1F"), r("D16", "F1"))
    return g


def write_md5(res, path):
    L = ["# vessel_mix5 %s: automatic results" % res["version"], "",
         "Gates: GA=%s, GB=%s, GC=%s. Usable recorders: %d (%s). Vessel folds: %s." % (
             res["gate_GA"], res["gate_GB"], res["gate_GC"], len(res["usable"]),
             ", ".join("%s %d" % (s, n) for s, n in sorted(res["per_site"].items())),
             ", ".join(res["vessel_sites"]) or "none"),
         "", "| recorder | site | train windows | test windows | median train level dB |", "|---|---|---|---|---|"]
    for n, r in sorted(res["recorders"].items()):
        L.append("| %s | %s | %d | %d | %s |" % (
            n, r["site"], r["train_windows"], r["test_windows"],
            "-" if r["median_train_db"] is None else "%.1f" % r["median_train_db"]))
    if res["pooled"]:
        L += ["", "| condition | recorders | complete | " + " | ".join(MODELS) + " |",
              "|---|---|---|" + "---|" * len(MODELS)]
        for c in res["conditions"]:
            if c in res["pooled"]:
                p = res["pooled"][c]
                L.append("| %s | %d | %s | %s |" % (c, res["n_recorders"][c], res["complete"][c],
                                                   " | ".join("%.4f" % p[m]["rmse"] for m in MODELS)))
        sites = sorted(res["per_site"])
        L += ["", "| condition | model | " + " | ".join(sites) + " |", "|---|---|" + "---|" * len(sites)]
        for c in res["conditions"]:
            if c not in res["by_site"]:
                continue
            for m in ("F1", "G1L", "B"):
                L.append("| %s | %s | %s |" % (c, m, " | ".join(
                    ("%.4f" % res["by_site"][c][h][m]["rmse"]) if h in res["by_site"][c] else "-" for h in sites)))
        L += ["", "Trend: `%s`" % json.dumps(res["trend_G1L"])]
    L += ["", "| id | prediction | held | value |", "|---|---|---|---|"]
    for x in res.get("grades", []):
        L.append("| %s | %s | %s | `%s` |" % (x["id"], x["prediction"], x["held"], json.dumps(x["value"])[:300]))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="/data/sanctsound")
    ap.add_argument("--out-dir", default="/out")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    log = {}
    sd01 = [vm.fetch_site(s, a.data_dir, log) for s in vm.SITES]
    recs = [("%s_01" % sd["site"], sd) for sd in sd01]
    for s in SITES:
        for d in DEPS[1:]:
            recs.append(("%s_%s" % (s, d), fetch_recorder(s, d, a.data_dir, log)))
    t1 = time.time()
    res = analyze5(sd01, recs)
    res["fetch"] = {k: {kk: vv for kk, vv in v.items() if kk != "days"} for k, v in log.items()}
    res["grades"] = grade5(res)
    res["seconds"] = {"fetch": round(t1 - t0), "total": round(time.time() - t0)}
    with open(os.path.join(a.out_dir, "results5.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    write_md5(res, os.path.join(a.out_dir, "RESULTS-vesselmix5-auto.md"))
    print(json.dumps({"gates": [res["gate_GA"], res["gate_GB"], res["gate_GC"]], "usable": len(res["usable"]),
                      "pooled": {c: {m: round(v[m]["rmse"], 4) for m in MODELS} for c, v in res["pooled"].items()},
                      "grades": [(x["id"], x["held"]) for x in res["grades"]]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
