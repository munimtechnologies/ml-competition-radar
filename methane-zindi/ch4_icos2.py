#!/usr/bin/env python3
"""ch4icos2: can the bias of the five-day seasonal floor at ICOS towers be fixed?

ch4icos-v1 (graded 2026-11-08) found that its seasonal fit C was biased high at 52 of 54 ICOS
sites (median +7.5 ppb). C fits a straight trend plus two annual harmonics on the four calendar
years before the origin's year, then extrapolates up to a year past that window, while global
methane growth slowed in 2024-2025. On the same origins and rules as v1, this job adds:

  Cr   the same trend + 2 harmonics, refitted monthly on the FIT_DAYS days that end LAT_GAP days
       before the first day of the origin's month (so it never uses data newer than t - 2)
  Dr   Cr + phi_r(gap) x the anomaly of the P0 value against Cr (as D0, with Cr instead of C)
  Dr2  Dr computed from the P2 value (two days of data latency, as D2)
  L30  C + the mean residual from C over the L_DAYS days ending on the P0 day (>= L_MIN values)

Downloads, daily means, C, D0 and D2 come unchanged from ch4_icos 0.1.0 (the code ch4icos-v1
ran), fetched from its pinned public commit by fetch_base.py.

Standard library only. MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: ICOS ObsPack via the ICOS Carbon Portal Zarr proxy, CC BY 4.0
(collection doi:10.18160/JZ2X-GZGU; please cite the ICOS data providers).
"""
import argparse
import json
import math
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

sys.path.append("/tmp/ch4base")
import ch4_icos as base  # noqa: E402

VERSION = "0.2.0"
FIT_DAYS = 1461
LAT_GAP = 2
L_DAYS = 30
L_MIN = 10
CLEAN_N = 10
METHODS = ("C", "D0", "D2", "Cr", "Dr", "Dr2", "L30")


class RFit(base.Fit):
    """Trend + 2 annual harmonics on the FIT_DAYS days before `end` (exclusive), with phi[k]."""

    def __init__(self, series, end):
        self.d0 = end - timedelta(days=FIT_DAYS)
        pts = sorted((d, v) for d, v in series.items() if self.d0 <= d < end)
        self.n = len(pts)
        if self.n < base.MIN_FIT_OBS:
            raise ValueError("only %d daily values before %s" % (self.n, end))
        self.coef = base.lstsq([base.design(self.x(d)) for d, _ in pts], [v for _, v in pts])
        res = {d: v - self(d) for d, v in pts}
        self.phi, self.phi_raw = {}, {}
        for k in range(1, base.MAX_LAG + 1):
            num = den = 0.0
            for d, r in res.items():
                r2 = res.get(d + timedelta(days=k))
                if r2 is not None:
                    num += r * r2
                    den += r * r
            raw = num / den if den > 0 else 0.0
            self.phi_raw[k] = raw
            self.phi[k] = min(1.0, max(0.0, raw))
        self.resid_sd = math.sqrt(sum(r * r for r in res.values()) / len(res))


def fit_end(t):
    """Exclusive end of the rolling fit window used for origin t."""
    return date(t.year, t.month, 1) - timedelta(days=LAT_GAP)


def level(series, tp, fit):
    """Mean of (value - fit) over the L_DAYS days ending on tp, or None with fewer than L_MIN."""
    rs = [series[d] - fit(d) for d in (tp - timedelta(days=k) for k in range(L_DAYS)) if d in series]
    return sum(rs) / len(rs) if len(rs) >= L_MIN else None


def forecasts2(series, t, f, r):
    """All METHODS for day t+H issued at origin t, or None when any is undefined."""
    b = base.forecasts(series, t, f)
    if b is None:
        return None
    tp0 = base.latest(series, t, base.PERSIST_BACK)
    tp2 = base.latest(series, t - timedelta(days=base.LAT), base.PERSIST_BACK)
    lv = level(series, tp0, f)
    if lv is None:
        return None
    target = t + timedelta(days=base.H)

    def damp(fit, tp):
        gap = min((target - tp).days, base.MAX_LAG)
        return fit(target) + fit.phi[gap] * (series[tp] - fit(tp))

    return {"C": b["C"], "D0": b["D0"], "D2": b["D2"], "Cr": r(target), "Dr": damp(r, tp0),
            "Dr2": damp(r, tp2), "L30": b["C"] + lv}


def _try(cls, *args):
    try:
        return cls(*args)
    except ValueError:
        return None


def gain(a, b):
    g = base.ratio(a, b)
    return None if g is None else round(1 - g, 4)


def evaluate_site(series):
    if not series:
        return {"included": False, "reason": "no daily values", "origins": 0}
    last = max(series)
    yfits, rfits = {}, {}
    errs = {m: [] for m in METHODS}
    t = base.TEST_START
    while t + timedelta(days=base.H) <= last:
        target = t + timedelta(days=base.H)
        if target in series:
            if t.year not in yfits:
                yfits[t.year] = _try(base.Fit, series, t.year)
            k = fit_end(t)
            if k not in rfits:
                rfits[k] = _try(RFit, series, k)
            f, r = yfits[t.year], rfits[k]
            if f is not None and r is not None:
                fc = forecasts2(series, t, f, r)
                if fc is not None:
                    obs = series[target]
                    for m in METHODS:
                        errs[m].append(fc[m] - obs)
        t += timedelta(days=1)
    n = len(errs["C"])
    good = [v for v in rfits.values() if v is not None]
    out = {"origins": n, "included": n >= base.MIN_ORIGINS, "rolling_fits": len(good)}
    if n == 0:
        out["reason"] = "no scorable origins"
        return out
    if n < base.MIN_ORIGINS:
        out["reason"] = "fewer than %d scorable origins" % base.MIN_ORIGINS
    raw = {m: base.rmse(errs[m]) for m in METHODS}
    out["methods"] = {m: {"rmse": round(raw[m], 4),
                          "mae": round(sum(abs(e) for e in errs[m]) / n, 4),
                          "bias": round(sum(errs[m]) / n, 4)} for m in METHODS}
    out["gain_cr_vs_c"] = gain(raw["Cr"], raw["C"])
    out["gain_dr_vs_d0"] = gain(raw["Dr"], raw["D0"])
    out["gain_l30_vs_c"] = gain(raw["L30"], raw["C"])
    c = base.ratio(raw["Dr2"], raw["Dr"])
    out["latency_cost_dr"] = None if c is None else round(c - 1, 4)
    out["best"] = min(METHODS, key=lambda m: raw[m])
    out["mean_rphi5"] = round(sum(v.phi[5] for v in good) / len(good), 4) if good else None
    return out


def grade(sites, clean_n=CLEAN_N):
    inc = {s: e for s, e in sites.items() if e.get("included")}
    n = len(inc)
    g = {"included_sites": n}
    if not n:
        return g
    ms = {s: e["methods"] for s, e in inc.items()}

    def med(key, m):
        return round(base.median([x[m][key] for x in ms.values()]), 4)

    bc, br = med("bias", "C"), med("bias", "Cr")
    g["median_bias"] = {m: med("bias", m) for m in METHODS}
    g["sites_C_bias_positive"] = sum(1 for x in ms.values() if x["C"]["bias"] > 0)
    g["context_B0_median_C_bias_at_least_5"] = bc >= 5
    g["R1_median_Cr_bias_below_half_of_C"] = bc > 0 and abs(br) < 0.5 * bc
    k2 = sum(1 for x in ms.values() if x["Cr"]["rmse"] < x["C"]["rmse"])
    k3 = sum(1 for x in ms.values() if x["Dr"]["rmse"] < x["D0"]["rmse"])
    k6 = sum(1 for x in ms.values() if x["L30"]["rmse"] < x["C"]["rmse"])
    g["sites_Cr_beats_C"], g["sites_Dr_beats_D0"], g["sites_L30_beats_C"] = k2, k3, k6
    g["R2_Cr_beats_C_at_75pct"] = k2 >= 0.75 * n
    g["R3_Dr_beats_D0_at_75pct"] = k3 >= 0.75 * n
    gd = base.median([e["gain_dr_vs_d0"] for e in inc.values() if e.get("gain_dr_vs_d0") is not None])
    g["median_gain_dr_vs_d0"] = None if gd is None else round(gd, 4)
    g["R4_median_gain_dr_vs_d0_at_least_0.02"] = gd is not None and gd >= 0.02
    clean = sorted(inc, key=lambda s: inc[s]["methods"]["C"]["rmse"])[:clean_n]
    g["clean_sites"] = clean
    gc = base.median([inc[s]["gain_dr_vs_d0"] for s in clean if inc[s].get("gain_dr_vs_d0") is not None])
    g["clean_median_gain_dr_vs_d0"] = None if gc is None else round(gc, 4)
    g["R5_clean_median_gain_dr_vs_d0_at_least_0.05"] = gc is not None and gc >= 0.05
    g["R6_L30_beats_C_at_majority"] = k6 > n / 2.0
    lc = base.median([e["latency_cost_dr"] for e in inc.values() if e.get("latency_cost_dr") is not None])
    g["median_latency_cost_dr"] = None if lc is None else round(lc, 4)
    g["R7_median_latency_cost_dr_below_0.05"] = lc is not None and lc < 0.05
    return g


def to_markdown(rep):
    L = ["# ch4icos2 %s results" % rep["version"], "",
         "Five-day-ahead daily mean CH4 (ppb) at the highest inlet of each ICOS site, from the public",
         "ICOS Zarr proxy; origins from %s; query time %s. Each cell is RMSE / bias (forecast minus"
         % (base.TEST_START, rep["started_utc"]),
         "observed). Gains are 1 - RMSE(new)/RMSE(old).", "",
         "| site | origins | C | Cr | D0 | Dr | Dr2 | L30 | gain Cr/C | gain Dr/D0 | gain L30/C | best |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda x: "" if x is None else "%.3f" % x
    for s, e in sorted(rep["sites"].items()):
        if "methods" not in e:
            L.append("| %s | %s | %s |  |  |  |  |  |  |  |  |  |" % (
                s, e.get("origins", 0), e.get("error") or e.get("reason", "")))
            continue
        r = e["methods"]
        cells = ["%.2f / %+.2f" % (r[m]["rmse"], r[m]["bias"]) for m in ("C", "Cr", "D0", "Dr", "Dr2", "L30")]
        L.append("| %s%s | %d | %s | %s | %s | %s | %s |" % (
            s, "" if e["included"] else " (excluded)", e["origins"], " | ".join(cells),
            f(e.get("gain_cr_vs_c")), f(e.get("gain_dr_vs_d0")), f(e.get("gain_l30_vs_c")), e["best"]))
    L += ["", "Checks: `%s`" % json.dumps(rep["checks"]), ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-sites", type=int, default=0)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    now = datetime.now(timezone.utc)
    rep = {"version": VERSION, "base_version": base.VERSION,
           "started_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "config": {"fit_days": FIT_DAYS, "lat_gap": LAT_GAP, "level_days": L_DAYS, "level_min": L_MIN,
                      "clean_n": CLEAN_N, "horizon_days": base.H, "latency_days": base.LAT,
                      "test_start": base.TEST_START.isoformat(), "min_origins": base.MIN_ORIGINS},
           "sites": {}}
    tomorrow = (now + timedelta(days=1)).date()
    recent = (now.date() - timedelta(days=3), now.date() - timedelta(days=2))
    heights, rep["probes"] = {}, []
    for win in (base.PROBE, recent):
        raw, prow, pstats = base.query(*win)
        found = {st: h for st, t, v, fl, h in prow}
        heights.update(found)
        rep["probes"].append({"window": [d.isoformat() for d in win], "parse": pstats, "inlets": len(found)})
    top = base.pick_top(heights)
    rep["inlets_found"], rep["sites_found"] = len(heights), len(top)
    print("inlets", len(heights), "sites", len(top))
    daily = {}
    for i, (s, st) in enumerate(sorted(top.items())):
        if a.max_sites and i >= a.max_sites:
            break
        e = {"station": st, "height": heights[st], "proxy_lag_days": None, "truncated_chunks": 0}
        try:
            allrows = []
            for y in range(base.HIST_START_YEAR, tomorrow.year + 1):
                for parts in (1, 4, 12):
                    got, bad = [], False
                    for c0, c1 in base.chunks(y, tomorrow, parts):
                        raw, yrows, ystats = base.query(c0, c1, st)
                        got += [r for r in yrows if r[0] == st]
                        bad = bad or ystats["truncated"]
                    if not bad:
                        break
                    e["truncated_chunks"] += 1
                allrows += got
            e["hours"] = len(allrows)
            if allrows:
                e["newest_hour"] = max(r[1] for r in allrows).strftime("%Y-%m-%dT%H:%M:%SZ")
                e["proxy_lag_days"] = base.census(allrows, now)[st]["lag_days"]
            series = base.daily_means(allrows)
            e["days"] = len(series)
            daily[s] = {"station": st, "values": {d.isoformat(): round(v, 3) for d, v in sorted(series.items())}}
            e.update(evaluate_site(series))
        except Exception as ex:
            e["error"] = "%s: %s" % (type(ex).__name__, ex)
            e["included"] = False
        rep["sites"][s] = e
        print(s, json.dumps({k: e.get(k) for k in ("station", "days", "origins", "included", "best",
                                                  "gain_cr_vs_c", "gain_dr_vs_d0", "gain_l30_vs_c", "error")}))
    rep["checks"] = grade(rep["sites"])
    rep["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    with open(os.path.join(a.out_dir, "RESULTS-ch4icos2.md"), "w", encoding="utf-8") as fh:
        fh.write(to_markdown(rep))
    with open(os.path.join(a.out_dir, "daily_means.json"), "w", encoding="utf-8") as fh:
        json.dump({"note": "UTC daily means (>= 12 valid hours) of ICOS ObsPack CH4 via the ICOS Zarr proxy, "
                           "CC BY 4.0, doi:10.18160/JZ2X-GZGU", "query_utc": rep["started_utc"],
                   "sites": daily}, fh)
    print(json.dumps(rep["checks"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
