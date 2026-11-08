#!/usr/bin/env python3
"""ch4icos: five-day-ahead daily methane baselines at ICOS towers, with and without data latency.

Prepares MV2's entry for Zindi's Green Rising Methane Innovation Challenge (daily CH4 five days
ahead at 59 stations, many of them ICOS). ICOS data files now need a logged-in account to be
downloaded by script, but ICOS's public Zarr proxy (https://zarr.icos-cp.eu, ObsPack store,
CC BY 4.0) answers anonymous /query requests with hourly CH4, including the near-real-time tail.
This job:

  1. Census: which ICOS CH4 inlets the proxy serves and how old each one's newest hour is.
  2. For each site, its highest inlet: hourly CH4 (apply_qc=true) from 2021, UTC daily means
     (days with at least 12 valid hours).
  3. Six forecasts of the daily mean five days after origin t, each using only data on or
     before its newest usable day:
       P0  persistence: value on t, else t-1, else t-2
       M7  mean of the values in [t-6, t] (at least 3)
       C   seasonal fit: linear trend + 2 annual harmonics on the 4 calendar years before t's
           year, evaluated at t+5
       D0  C + phi(gap) * anomaly of the P0 value, gap = days from that value to t+5,
           phi(k) = lag-k regression of the fit's residuals on themselves, clipped to [0, 1]
       P2  persistence when the newest usable day is t-2 (value on t-2, else t-3, else t-4)
       D2  D0 computed from the P2 value (two days of data latency)
     Origins from 2025-01-01 to the last day with a target.

Standard library only. MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: ICOS ObsPack via the ICOS Carbon Portal Zarr proxy, CC BY 4.0
(collection doi:10.18160/JZ2X-GZGU; please cite the ICOS data providers).
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

VERSION = "0.1.0"
QUERY_URL = "https://zarr.icos-cp.eu/query"
VAR_ID = "icos-obspack.ch4.ch4"
H = 5
LAT = 2
TEST_START = date(2025, 1, 1)
HIST_START_YEAR = 2021
FIT_YEARS = 4
MIN_FIT_OBS = 500
MIN_ORIGINS = 200
MIN_HOURS = 12
PERSIST_BACK = 2
M7_DAYS = 7
M7_MIN = 3
MAX_LAG = 12
FRESH_DAYS = 4.0
PROBE = (date(2025, 6, 1), date(2025, 6, 2))
METHODS = ("P0", "M7", "C", "D0", "P2", "D2")
NEED_COLS = ("station", "time_ch4", "ch4", "sampling_height")
USER_AGENT = "MV2-Munim-Inc-research ch4icos/%s (mv2@munimtech.com)" % VERSION
PAUSE = 0.3


def parse_time(s):
    s = s.strip().replace("T", " ")[:19]
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def parse_csv(text):
    """Proxy CSV -> ([(station, datetime, ppb, flag, height)], stats). Empty, NaN or non-positive
    CH4 values are skipped."""
    rd = csv.reader(io.StringIO(text))
    stats = {"lines": 0, "rows": 0, "skipped": 0}
    head = None
    out = []
    for parts in rd:
        if not parts:
            continue
        stats["lines"] += 1
        if head is None:
            head = [p.strip() for p in parts]
            for c in NEED_COLS:
                if c not in head:
                    raise ValueError("column %r missing in header %s" % (c, head))
            ix = {c: head.index(c) for c in head}
            continue
        try:
            v = float(parts[ix["ch4"]])
        except (ValueError, IndexError):
            stats["skipped"] += 1
            continue
        if math.isnan(v) or v <= 0:
            stats["skipped"] += 1
            continue
        flag = parts[ix["ch4_qc_flag"]] if "ch4_qc_flag" in ix else ""
        out.append((parts[ix["station"]], parse_time(parts[ix["time_ch4"]]), v, flag,
                    float(parts[ix["sampling_height"]])))
        stats["rows"] += 1
    if head is None:
        raise ValueError("empty response")
    return out, stats


def site_code(station):
    m = re.match(r"[A-Za-z]+", station)
    return m.group(0).upper() if m else station


def pick_top(heights):
    """{station: height} -> {site: station of its highest inlet} (ties: smaller station id)."""
    best = {}
    for st in sorted(heights):
        s = site_code(st)
        if s not in best or heights[st] > heights[best[s]]:
            best[s] = st
    return best


def census(rows, now):
    c = {}
    for st, t, v, flag, h in rows:
        e = c.setdefault(st, {"height": h, "n": 0, "last": t})
        e["n"] += 1
        if t > e["last"]:
            e["last"] = t
    for e in c.values():
        e["lag_days"] = round((now - e["last"]).total_seconds() / 86400.0, 3)
        e["last"] = e["last"].strftime("%Y-%m-%dT%H:%M:%SZ")
    return c


def daily_means(rows):
    hours = {}
    for st, t, v, flag, h in rows:
        hours.setdefault(t.date(), {})[t] = v
    return {d: sum(hs.values()) / len(hs) for d, hs in hours.items() if len(hs) >= MIN_HOURS}


def design(x):
    row = [1.0, x]
    for k in (1, 2):
        row += [math.sin(2 * math.pi * k * x), math.cos(2 * math.pi * k * x)]
    return row


def solve(a, b):
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
    """Seasonal fit on the FIT_YEARS calendar years before `year`; phi[k] for k = 1..MAX_LAG."""

    def __init__(self, series, year):
        self.d0 = date(year - FIT_YEARS, 1, 1)
        end = date(year, 1, 1)
        pts = sorted((d, v) for d, v in series.items() if self.d0 <= d < end)
        self.n = len(pts)
        if self.n < MIN_FIT_OBS:
            raise ValueError("only %d daily values in %d-%d" % (self.n, year - FIT_YEARS, year - 1))
        self.coef = lstsq([design(self.x(d)) for d, _ in pts], [v for _, v in pts])
        res = {d: v - self(d) for d, v in pts}
        self.phi, self.phi_raw = {}, {}
        for k in range(1, MAX_LAG + 1):
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

    def x(self, d):
        return (d - self.d0).days / 365.25

    def __call__(self, d):
        return sum(c * f for c, f in zip(self.coef, design(self.x(d))))

    def info(self):
        return {"n": self.n, "phi5": round(self.phi[5], 4), "phi7": round(self.phi[7], 4),
                "phi5_raw": round(self.phi_raw[5], 4), "resid_sd": round(self.resid_sd, 3)}


def latest(series, d, back):
    for k in range(back + 1):
        x = d - timedelta(days=k)
        if x in series:
            return x
    return None


def forecasts(series, t, fit):
    """Forecasts of day t+H issued at origin t, or None when any method is undefined."""
    tp0 = latest(series, t, PERSIST_BACK)
    tp2 = latest(series, t - timedelta(days=LAT), PERSIST_BACK)
    if tp0 is None or tp2 is None:
        return None
    win = [series[t - timedelta(days=k)] for k in range(M7_DAYS) if (t - timedelta(days=k)) in series]
    if len(win) < M7_MIN:
        return None
    target = t + timedelta(days=H)
    clim = fit(target)

    def damp(tp):
        gap = min((target - tp).days, MAX_LAG)
        return clim + fit.phi[gap] * (series[tp] - fit(tp))

    return {"P0": series[tp0], "M7": sum(win) / len(win), "C": clim, "D0": damp(tp0),
            "P2": series[tp2], "D2": damp(tp2)}


def rmse(errors):
    return math.sqrt(sum(e * e for e in errors) / len(errors))


def ratio(a, b):
    return None if b == 0 else a / b


def evaluate_site(series):
    if not series:
        return {"included": False, "reason": "no daily values", "origins": 0}
    last = max(series)
    fits, fit_info, used = {}, {}, {}
    errs = {m: [] for m in METHODS}
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
    n = len(errs["P0"])
    out = {"origins": n, "fits": {str(y): fit_info[y] for y in sorted(fit_info)},
           "included": n >= MIN_ORIGINS}
    if n == 0:
        out["reason"] = "no scorable origins"
        return out
    if n < MIN_ORIGINS:
        out["reason"] = "fewer than %d scorable origins" % MIN_ORIGINS
    raw = {m: rmse(errs[m]) for m in METHODS}
    out["methods"] = {m: {"rmse": round(raw[m], 4),
                          "mae": round(sum(abs(e) for e in errs[m]) / n, 4),
                          "bias": round(sum(errs[m]) / n, 4)} for m in METHODS}
    g = ratio(raw["D0"], raw["C"])
    out["d0_gain_vs_c"] = None if g is None else round(1 - g, 4)
    c = ratio(raw["D2"], raw["D0"])
    out["latency_cost"] = None if c is None else round(c - 1, 4)
    out["best"] = min(METHODS, key=lambda m: raw[m])
    phis = [fits[y].phi[5] for y in used if fits.get(y) is not None]
    out["mean_phi5"] = round(sum(phis) / len(phis), 4) if phis else None
    return out


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def grade(sites):
    inc = {s: e for s, e in sites.items() if e.get("included")}
    n = len(inc)
    g = {"included_sites": n, "Q1_at_least_25_sites": n >= 25}
    fresh = [s for s, e in sites.items()
             if e.get("proxy_lag_days") is not None and e["proxy_lag_days"] <= FRESH_DAYS]
    g["fresh_sites"] = len(fresh)
    g["median_proxy_lag_days"] = median([e["proxy_lag_days"] for e in sites.values()
                                         if e.get("proxy_lag_days") is not None])
    g["F1_at_least_25_sites_fresh_within_4d"] = len(fresh) >= 25
    if not inc:
        return g
    ms = [e["methods"] for e in inc.values()]
    k2 = sum(1 for m in ms if m["D0"]["rmse"] < m["P0"]["rmse"])
    k3 = sum(1 for m in ms if m["C"]["rmse"] < m["P0"]["rmse"])
    g["sites_D0_beats_P0"] = k2
    g["sites_C_beats_P0"] = k3
    g["Q2_D0_beats_P0_at_80pct"] = k2 >= 0.8 * n
    g["Q3_C_beats_P0_at_majority"] = k3 > n / 2.0
    gain = median([e["d0_gain_vs_c"] for e in inc.values() if e.get("d0_gain_vs_c") is not None])
    g["median_d0_gain_vs_c"] = None if gain is None else round(gain, 4)
    g["Q4_median_D0_gain_over_C_in_0_to_0.10"] = gain is not None and 0 <= gain < 0.10
    phi = median([e["mean_phi5"] for e in inc.values() if e.get("mean_phi5") is not None])
    g["median_mean_phi5"] = None if phi is None else round(phi, 4)
    g["Q5_median_phi5_in_0.1_to_0.5"] = phi is not None and 0.1 <= phi <= 0.5
    cost = median([e["latency_cost"] for e in inc.values() if e.get("latency_cost") is not None])
    g["median_latency_cost"] = None if cost is None else round(cost, 4)
    g["Q6_median_latency_cost_below_0.05"] = cost is not None and cost < 0.05
    return g


def build_url(params):
    return QUERY_URL + "?" + urllib.parse.urlencode(params)


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read(), [(k, v) for k, v in r.getheaders()]
        except Exception as e:  # retried, then reported
            last = e
            time.sleep(10 * (i + 1))
    raise last


def truncated(headers):
    """True when a response header says the selection was cut at the server's row cap."""
    for k, v in headers:
        lk, lv = k.lower(), v.lower().replace(" ", "")
        if "trunc" in lk and lv not in ("false", "0", "no", ""):
            return True
        if '"truncated":true' in lv:
            return True
    return False


def query(start, end, station=None):
    p = {"id": VAR_ID, "start": start.isoformat(), "end": end.isoformat(), "apply_qc": "true",
         "format": "csv"}
    if station:
        p["station"] = station
    raw, headers = fetch(build_url(p))
    time.sleep(PAUSE)
    rows, stats = parse_csv(raw.decode("utf-8", "replace"))
    stats["truncated"] = truncated(headers)
    return raw, rows, stats


def chunks(y, stop, parts):
    """Split [y-01-01, min(y+1-01-01, stop)) into `parts` month-aligned pieces (empty ones dropped)."""
    step = 12 // parts
    out = []
    for i in range(parts):
        a = date(y, 1 + i * step, 1)
        b = date(y + 1, 1, 1) if i == parts - 1 else date(y, 1 + (i + 1) * step, 1)
        b = min(b, stop)
        if a < b:
            out.append((a, b))
    return out


def to_markdown(rep):
    L = ["# ch4icos %s results" % rep["version"], "",
         "Five-day-ahead daily mean CH4 (ppb) at the highest inlet of each ICOS site, from the public",
         "ICOS Zarr proxy; origins from %s; query time %s." % (TEST_START, rep["started_utc"]),
         "D0 gain = 1 - RMSE(D0)/RMSE(C); latency cost = RMSE(D2)/RMSE(D0) - 1; proxy lag = query time",
         "minus the inlet's newest hour.", "",
         "| site | inlet | proxy lag (d) | origins | P0 | M7 | C | D0 | P2 | D2 | D0 gain | latency cost | phi5 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s, e in sorted(rep["sites"].items()):
        lag = e.get("proxy_lag_days")
        lag = "" if lag is None else "%.2f" % lag
        if "methods" not in e:
            L.append("| %s | %s | %s | %s | %s |  |  |  |  |  |  |  |  |" % (
                s, e.get("station", ""), lag, e.get("origins", 0), e.get("error") or e.get("reason", "")))
            continue
        r = e["methods"]
        f = lambda x: "" if x is None else "%.3f" % x
        L.append("| %s%s | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            s, "" if e["included"] else " (excluded)", e["station"], lag, e["origins"],
            *["%.2f" % r[m]["rmse"] for m in METHODS], f(e.get("d0_gain_vs_c")), f(e.get("latency_cost")),
            f(e.get("mean_phi5"))))
    L += ["", "Checks: `%s`" % json.dumps(rep["checks"]), ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-sites", type=int, default=0)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    now = datetime.now(timezone.utc)
    rep = {"version": VERSION, "started_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "config": {"query_url": QUERY_URL, "variable": VAR_ID, "horizon_days": H, "latency_days": LAT,
                      "test_start": TEST_START.isoformat(), "history_from": "%d-01-01" % HIST_START_YEAR,
                      "fit_years": FIT_YEARS, "min_fit_obs": MIN_FIT_OBS, "min_origins": MIN_ORIGINS,
                      "min_hours_per_day": MIN_HOURS, "fresh_days": FRESH_DAYS},
           "sites": {}}
    tomorrow = (now + timedelta(days=1)).date()
    recent = (now.date() - timedelta(days=3), now.date() - timedelta(days=2))
    heights, rep["probes"] = {}, []
    for win in (PROBE, recent):
        raw, prow, pstats = query(*win)
        found = {st: h for st, t, v, f, h in prow}
        heights.update(found)
        rep["probes"].append({"window": [d.isoformat() for d in win], "parse": pstats, "inlets": sorted(found)})
    top = pick_top(heights)
    rep["inlets_found"] = len(heights)
    rep["sites_found"] = len(top)
    print("inlets", len(heights), "sites", len(top))
    for i, (s, st) in enumerate(sorted(top.items())):
        if a.max_sites and i >= a.max_sites:
            break
        e = {"station": st, "height": heights[st], "proxy_lag_days": None, "truncated_chunks": 0}
        try:
            allrows, nbytes, h = [], 0, hashlib.sha256()
            for y in range(HIST_START_YEAR, tomorrow.year + 1):
                for parts in (1, 4, 12):
                    got, bad = [], False
                    for c0, c1 in chunks(y, tomorrow, parts):
                        raw, yrows, ystats = query(c0, c1, st)
                        nbytes += len(raw)
                        h.update(raw)
                        got += [r for r in yrows if r[0] == st]
                        bad = bad or ystats["truncated"]
                    if not bad:
                        break
                    e["truncated_chunks"] += 1
                allrows += got
            e["bytes"], e["sha256"], e["hours"] = nbytes, h.hexdigest(), len(allrows)
            if allrows:
                e["newest_hour"] = max(r[1] for r in allrows).strftime("%Y-%m-%dT%H:%M:%SZ")
                e["proxy_lag_days"] = census(allrows, now)[st]["lag_days"]
            series = daily_means(allrows)
            e["days"] = len(series)
            if series:
                e["first"], e["last"] = min(series).isoformat(), max(series).isoformat()
            e.update(evaluate_site(series))
        except Exception as ex:
            e["error"] = "%s: %s" % (type(ex).__name__, ex)
            e["included"] = False
        rep["sites"][s] = e
        print(s, json.dumps({k: e.get(k) for k in ("station", "hours", "days", "last", "origins", "included",
                                                  "best", "d0_gain_vs_c", "latency_cost", "error")}))
    rep["checks"] = grade(rep["sites"])
    rep["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    with open(os.path.join(a.out_dir, "RESULTS-ch4icos.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(rep))
    print(json.dumps(rep["checks"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
