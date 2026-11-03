#!/usr/bin/env python3
"""ch4base: five-day-ahead daily methane baselines at NOAA GML in-situ stations.

Prepares MV2's entry for Zindi's Green Rising Methane Innovation Challenge (daily CH4
five days ahead at 59 stations). Before the contest data exist, this measures how far
five simple forecasts get on NOAA's public daily in-situ CH4 records (CC0 1.0):

  P   persistence: the latest observed daily value (origin day or up to 2 days before)
  M7  mean of the observed values in the 7 days ending at the origin (at least 3)
  C   seasonal fit: linear trend + 2 annual harmonics fitted on the 4 calendar years before
      the origin's year, evaluated at the target day
  S   C plus the latest anomaly from the fit (anomaly persistence)
  D   C plus phi times the latest anomaly, phi = lag-5 regression of fit residuals on
      themselves in the same 4 training years, clipped to [0, 1]

Every forecast uses only data on or before its origin day. Test origins run from
2021-01-01 to the last target day the file has. Standard library only.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: NOAA GML, Petron et al. 2026, doi:10.15138/ve0c-be70 (CC0 1.0).
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
import urllib.request
from datetime import date, timedelta

VERSION = "0.1.0"
BASE = "https://gml.noaa.gov/aftp/data/greenhouse_gases/ch4/in-situ/surface/txt/"
SITES = ("brw", "mko", "mlo", "smo")
H = 5
TEST_START = date(2021, 1, 1)
FIT_YEARS = 4
MIN_FIT_OBS = 500
MIN_ORIGINS = 365
PERSIST_BACK = 2
M7_DAYS = 7
M7_MIN = 3
METHODS = ("P", "M7", "C", "S", "D")
USER_AGENT = "MV2-Munim-Inc-research ch4base/%s (mv2@munimtech.com)" % VERSION


def file_url(site):
    return BASE + "ch4_%s_surface-insitu_1_ccgg_DailyData.txt" % site


def parse_daily(text):
    """Parse a NOAA GML DailyData.txt file into ({date: ppb}, stats).

    Columns come from a '# data_fields:' comment line or a plain 'site_code ...' header line.
    Values <= -900 are missing; a qcflag whose first character is not '.' is rejected.
    """
    cols = None
    out = {}
    stats = {"lines": 0, "data_lines": 0, "missing": 0, "rejected": 0, "duplicates": 0, "kept": 0}
    for raw in text.splitlines():
        stats["lines"] += 1
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            if body.lower().startswith("data_fields:"):
                cols = body.split(":", 1)[1].split()
            continue
        parts = line.split()
        if cols is None:
            if parts[0] == "site_code":
                cols = parts
                continue
            raise ValueError("data before any column header (line %d)" % stats["lines"])
        if parts == cols:
            continue
        if len(parts) < len(cols):
            raise ValueError("short line %d: %d fields, %d columns" % (stats["lines"], len(parts), len(cols)))
        row = dict(zip(cols, parts))
        for need in ("year", "month", "day", "value"):
            if need not in row:
                raise ValueError("column %r not found in %s" % (need, cols))
        stats["data_lines"] += 1
        d = date(int(row["year"]), int(row["month"]), int(row["day"]))
        v = float(row["value"])
        if math.isnan(v) or v <= -900.0:
            stats["missing"] += 1
            continue
        if row.get("qcflag", ".")[:1] != ".":
            stats["rejected"] += 1
            continue
        if d in out:
            stats["duplicates"] += 1
            continue
        out[d] = v
        stats["kept"] += 1
    if cols is None:
        raise ValueError("no column header found")
    stats["columns"] = cols
    return out, stats


def design(x):
    row = [1.0, x]
    for k in (1, 2):
        row += [math.sin(2 * math.pi * k * x), math.cos(2 * math.pi * k * x)]
    return row


def solve(a, b):
    """Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [list(a[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-12:
            raise ValueError("singular system")
        m[c], m[p] = m[p], m[c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            for k in range(c, n + 1):
                m[r][k] -= f * m[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (m[r][n] - sum(m[r][k] * x[k] for k in range(r + 1, n))) / m[r][r]
    return x


def lstsq(rows, ys):
    n = len(rows[0])
    a = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    for row, y in zip(rows, ys):
        for i in range(n):
            b[i] += row[i] * y
            for j in range(n):
                a[i][j] += row[i] * row[j]
    return solve(a, b)


class Fit:
    """Seasonal fit on the FIT_YEARS calendar years before `year`, with damping phi."""

    def __init__(self, series, year):
        self.year = year
        self.d0 = date(year - FIT_YEARS, 1, 1)
        end = date(year, 1, 1)
        pts = sorted((d, v) for d, v in series.items() if self.d0 <= d < end)
        self.n = len(pts)
        if self.n < MIN_FIT_OBS:
            raise ValueError("only %d observations in %d-%d" % (self.n, year - FIT_YEARS, year - 1))
        self.coef = lstsq([design(self.x(d)) for d, _ in pts], [v for _, v in pts])
        res = {d: v - self(d) for d, v in pts}
        num = den = 0.0
        pairs = 0
        for d, r in res.items():
            r2 = res.get(d + timedelta(days=H))
            if r2 is not None:
                num += r * r2
                den += r * r
                pairs += 1
        self.pairs = pairs
        self.phi_raw = num / den if den > 0 else 0.0
        self.phi = min(1.0, max(0.0, self.phi_raw))
        self.resid_sd = math.sqrt(sum(r * r for r in res.values()) / len(res))

    def x(self, d):
        return (d - self.d0).days / 365.25

    def __call__(self, d):
        return sum(c * f for c, f in zip(self.coef, design(self.x(d))))

    def info(self):
        return {"n": self.n, "pairs": self.pairs, "phi": round(self.phi, 4),
                "phi_raw": round(self.phi_raw, 4), "resid_sd": round(self.resid_sd, 3)}


def forecasts(series, t, fit):
    """Forecasts for day t+H issued at origin t, or None when any method is undefined."""
    tp = None
    for back in range(PERSIST_BACK + 1):
        d = t - timedelta(days=back)
        if d in series:
            tp = d
            break
    if tp is None:
        return None
    win = [series[t - timedelta(days=k)] for k in range(M7_DAYS) if (t - timedelta(days=k)) in series]
    if len(win) < M7_MIN:
        return None
    clim = fit(t + timedelta(days=H))
    anom = series[tp] - fit(tp)
    return {"P": series[tp], "M7": sum(win) / len(win), "C": clim,
            "S": clim + anom, "D": clim + fit.phi * anom}


def summarize(errors):
    n = len(errors)
    return {"rmse": round(math.sqrt(sum(e * e for e in errors) / n), 4),
            "mae": round(sum(abs(e) for e in errors) / n, 4),
            "bias": round(sum(errors) / n, 4)}


def evaluate_site(series):
    if not series:
        return {"included": False, "reason": "no valid daily values", "origins": 0}
    last = max(series)
    fits, fit_info = {}, {}
    errs = {m: [] for m in METHODS}
    used = {}
    t = TEST_START
    while t + timedelta(days=H) <= last:
        target = t + timedelta(days=H)
        if target in series:
            y = t.year
            if y not in fits:
                try:
                    fits[y] = Fit(series, y)
                    fit_info[y] = fits[y].info()
                except ValueError as e:
                    fits[y] = None
                    fit_info[y] = {"error": str(e)}
            f = fits[y]
            if f is not None:
                fc = forecasts(series, t, f)
                if fc is not None:
                    obs = series[target]
                    for m in METHODS:
                        errs[m].append(fc[m] - obs)
                    used[y] = used.get(y, 0) + 1
        t += timedelta(days=1)
    for y, info in fit_info.items():
        info["origins"] = used.get(y, 0)
    n = len(errs["P"])
    out = {"origins": n, "fits": {str(y): fit_info[y] for y in sorted(fit_info)},
           "included": n >= MIN_ORIGINS}
    if n == 0:
        out["reason"] = "no scorable origins"
        return out
    if n < MIN_ORIGINS:
        out["reason"] = "fewer than %d scorable origins" % MIN_ORIGINS
    methods = {m: summarize(errs[m]) for m in METHODS}
    base = methods["P"]["rmse"]
    for m in METHODS:
        methods[m]["skill_vs_P"] = None if base == 0 else round(1 - methods[m]["rmse"] / base, 4)
    out["methods"] = methods
    out["best"] = min(METHODS, key=lambda m: methods[m]["rmse"])
    return out


def grade(sites):
    inc = {s: e for s, e in sites.items() if e.get("included")}
    g = {"included_sites": sorted(inc), "P1_at_least_two_sites": len(inc) >= 2}
    if not inc:
        return g
    ms = {s: e["methods"] for s, e in inc.items()}
    g["P2_D_beats_P_every_site"] = all(m["D"]["rmse"] < m["P"]["rmse"] for m in ms.values())
    g["P3_D_at_most_C_every_site"] = all(m["D"]["rmse"] <= m["C"]["rmse"] for m in ms.values())
    g["P4_D_best_every_site"] = all(e["best"] == "D" for e in inc.values())
    g["P5_D_gain_10pct_every_site"] = all((m["D"]["skill_vs_P"] or 0) >= 0.10 for m in ms.values())
    phis = [f["phi"] for e in inc.values() for f in e["fits"].values() if f.get("origins") and "phi" in f]
    g["mean_phi"] = round(sum(phis) / len(phis), 4) if phis else None
    g["P6_mean_phi_between_0.2_and_0.8"] = bool(phis) and 0.2 <= g["mean_phi"] <= 0.8
    return g


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # retried, then reported
            last = e
            time.sleep(10 * (i + 1))
    raise last


def to_markdown(report):
    lines = ["# ch4base %s results" % report["version"], "",
             "Five-day-ahead daily CH4 (ppb) at NOAA GML in-situ sites; origins from %s." % TEST_START, "",
             "| site | origins | method | RMSE | MAE | bias | skill vs P |",
             "|---|---|---|---|---|---|---|"]
    for s, e in report["sites"].items():
        if "methods" not in e:
            lines.append("| %s | %s | - | %s | | | |" % (s, e.get("origins", 0), e.get("error") or e.get("reason", "")))
            continue
        for m in METHODS:
            r = e["methods"][m]
            lines.append("| %s%s | %d | %s | %.2f | %.2f | %.2f | %s |" % (
                s, "" if e["included"] else " (excluded)", e["origins"], m, r["rmse"], r["mae"],
                r["bias"], "" if r["skill_vs_P"] is None else "%.3f" % r["skill_vs_P"]))
    lines += ["", "Checks: `%s`" % json.dumps(report["checks"])]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    report = {"version": VERSION, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "config": {"horizon_days": H, "test_start": TEST_START.isoformat(), "fit_years": FIT_YEARS,
                         "min_fit_obs": MIN_FIT_OBS, "min_origins": MIN_ORIGINS,
                         "persist_back_days": PERSIST_BACK, "m7_days": M7_DAYS, "m7_min": M7_MIN},
              "sites": {}}
    for s in SITES:
        e = {"url": file_url(s)}
        try:
            raw = fetch(e["url"])
            e["bytes"] = len(raw)
            e["sha256"] = hashlib.sha256(raw).hexdigest()
            series, stats = parse_daily(raw.decode("utf-8", "replace"))
            e["parse"] = stats
            if series:
                e["first"], e["last"] = min(series).isoformat(), max(series).isoformat()
            e.update(evaluate_site(series))
        except Exception as ex:
            e["error"] = "%s: %s" % (type(ex).__name__, ex)
            e["included"] = False
        report["sites"][s] = e
        print(s, json.dumps({k: e.get(k) for k in ("bytes", "first", "last", "origins", "included", "best", "error")}))
    report["checks"] = grade(report["sites"])
    report["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    with open(os.path.join(a.out_dir, "RESULTS-ch4base.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(report))
    print(json.dumps(report["checks"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
