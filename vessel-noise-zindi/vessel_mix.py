"""vessel_mix 0.1.0: an account-free public proxy for the Zindi Underwater Vessel Noise task.

The Zindi challenge (french-embassy-underwater-vessel-noise-challenge) asks, for each 15-minute
window of third-octave levels (25 bands, 31.6 Hz to 7.94 kHz), what share of the window's total
energy comes from a vessel passage that the organisers mixed into a real background. Its own data
need a Zindi account. This script builds the same kind of task from NOAA/US Navy SanctSound data
that anyone can download (public Google Cloud bucket noaa-passive-bioacoustic): 1-minute hybrid
millidecade spectra (HMD) converted to the contest's 25 third-octave bands, and SanctSound's own
ship-passage detections, at three sites (Stellwagen Bank SB01 and SB03, Gray's Reef GR01).

It then compares four estimators on mixtures whose answer is known:
  C0  a constant (the mean share of the training mixtures; the contest's benchmark is a constant)
  F1  an untrained background floor: per band, the lowest 3-minute running mean, times 15
  G1  gradient boosting trained on synthetic mixtures whose vessel passages come from OTHER sites
      than the test passages (an entrant's position: the organisers' vessel recordings are unknown)
  G0  the same learner trained on other passages from the SAME site as the test passages
Folds: leave one vessel site out. Backgrounds: first 8 days train, last 4 days test, all sites.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound (NCEI,
doi:10.25921/ymf8-5k59 for the HMD product); used as published, not redistributed here.
Usage: python vessel_mix.py --data-dir /data/sanctsound --out-dir /out
"""
import argparse
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import numpy as np

VERSION = "0.1.0"
BUCKET = "noaa-passive-bioacoustic"
LIST_API = "https://storage.googleapis.com/storage/v1/b/%s/o" % BUCKET
OBJ = "https://storage.googleapis.com/%s/" % BUCKET
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"

SITES = ["sb01", "sb03", "gr01"]
DEPLOYMENT = "01"
N_DAYS = 12            # daily HMD files per site: the 2nd to the 13th in name order
N_TRAIN_DAYS = 8       # first 8 of them give training backgrounds, the last 4 test backgrounds
MIN_DAY_MINUTES = 1000
WIN = 15               # minutes per window, as in the contest
RUN = 3                # minutes in the floor estimator's running mean
SNR_DB = 3.0           # a passage window must carry >= 3 dB more energy than the site's median window
MIN_PASSAGES = 6       # per pool (train and test) for a site to be a vessel fold
N_TEST = 1500          # test mixtures per fold (the contest's Test.csv has 1,500 windows)
N_TRAIN = 6000         # training mixtures per learner per fold
P_ZERO = 0.25          # share of mixtures with nothing added
SHARE_LO, SHARE_HI = 0.05, 0.90
TOL_N = list(range(15, 40))  # base-10 third-octave centres 10**(n/10): 31.6 Hz .. 7943 Hz


# ---------------------------------------------------------------- spectra -> third-octave levels
def tol_edges():
    return [(10 ** (n / 10.0 - 0.05), 10 ** (n / 10.0 + 0.05)) for n in TOL_N]


def bin_widths(freqs):
    f = np.asarray(freqs, dtype=float)
    mid = (f[1:] + f[:-1]) / 2.0
    lo = np.concatenate([[f[0] - (mid[0] - f[0])], mid])
    hi = np.concatenate([mid, [f[-1] + (f[-1] - mid[-1])]])
    return hi - lo


def tol_matrix(freqs):
    """(n_bins, 25) weights: a bin's width if its centre lies in the band, else 0."""
    f = np.asarray(freqs, dtype=float)
    w = bin_widths(f)
    W = np.zeros((len(f), len(TOL_N)))
    for j, (lo, hi) in enumerate(tol_edges()):
        sel = (f >= lo) & (f < hi)
        W[sel, j] = w[sel]
    return W


def psd_db_to_tol_db(psd_db, W):
    """PSD rows in dB re 1 uPa^2/Hz -> 25 band levels in dB. A row with a missing value in any bin
    that a band uses comes back all-NaN."""
    P = 10.0 ** (np.asarray(psd_db, dtype=float) / 10.0)
    used = W.sum(axis=1) > 0
    bad = np.isnan(P[:, used]).any(axis=1)
    lin = np.nan_to_num(P, nan=0.0) @ W
    with np.errstate(divide="ignore"):
        out = 10.0 * np.log10(lin)
    out[bad] = np.nan
    return out


# ---------------------------------------------------------------- labels and windows
def iso_to_epoch(s):
    s = s.strip().replace("Z", "")[:19]
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()


def parse_ships(text):
    out = []
    for line in text.splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        if len(parts) > 2 and parts[2].lower() in ("0", "no", "none", "noship", "false"):
            continue
        try:
            out.append((iso_to_epoch(parts[0]), iso_to_epoch(parts[1])))
        except ValueError:
            continue
    return sorted(out)


def ship_minutes(ships):
    """Epoch minutes touched by any detection (an end exactly on a minute boundary includes it)."""
    out = set()
    for s, e in ships:
        out.update(range(int(s // 60), int(e // 60) + 1))
    return out


def window(lv, m0, n=WIN):
    rows = [lv.get(m0 + i) for i in range(n)]
    if any(r is None for r in rows):
        return None
    return np.vstack(rows)


def energy(L_db):
    return float((10.0 ** (np.asarray(L_db) / 10.0)).sum())


# ---------------------------------------------------------------- mixing, estimators, features
def draw_share(rng):
    if rng.random() < P_ZERO:
        return 0.0
    return float(rng.uniform(SHARE_LO, SHARE_HI))


def mix(B_db, V_db, share):
    """Add V scaled so that it carries `share` of the mixture's total energy (all bands, minutes)."""
    if share <= 0 or V_db is None:
        return np.array(B_db, dtype=float), 0.0
    PB = 10.0 ** (np.asarray(B_db, dtype=float) / 10.0)
    PV = 10.0 ** (np.asarray(V_db, dtype=float) / 10.0)
    g = share * PB.sum() / ((1.0 - share) * PV.sum())
    return 10.0 * np.log10(PB + g * PV), float(share)


def _floor(P, k=RUN):
    run = np.stack([P[i:i + k].mean(axis=0) for i in range(P.shape[0] - k + 1)])
    return run.min(axis=0)


def floor_share(L_db):
    P = 10.0 ** (np.asarray(L_db, dtype=float) / 10.0)
    bg = P.shape[0] * _floor(P)
    return float(np.clip(1.0 - bg.sum() / P.sum(), 0.0, 1.0))


N_FEATURES = 25 * 4 + WIN * 2 + 2


def features(L_db):
    """Per band: spectral shape, temporal range, temporal sd, excess over the floor (all offset-free);
    per minute: broadband profile minus its median, raw and sorted; then absolute level and F1."""
    L = np.asarray(L_db, dtype=float)
    P = 10.0 ** (L / 10.0)
    mu = 10.0 * np.log10(P.mean(axis=0))
    shape = mu - mu.mean()
    rng_ = L.max(axis=0) - L.min(axis=0)
    sd = L.std(axis=0)
    excess = mu - 10.0 * np.log10(_floor(P))
    tot = 10.0 * np.log10(P.sum(axis=1))
    prof = tot - np.median(tot)
    absl = 10.0 * np.log10(P.sum())
    return np.concatenate([shape, rng_, sd, excess, prof, np.sort(prof), [absl, floor_share(L)]])


def fit_predict(Xtr, ytr, Xte, seed=0):
    from sklearn.ensemble import HistGradientBoostingRegressor
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=seed)
    m.fit(Xtr, ytr)
    return np.clip(m.predict(Xte), 0.0, 1.0)


# ---------------------------------------------------------------- per-site pools
def build_site(sd, n_train_days=N_TRAIN_DAYS):
    lv, day_of = sd["lv"], sd["day_of"]
    smin = ship_minutes(sd["ships"])
    grid = []
    for m in sorted(lv):
        if m % WIN:
            continue
        L = window(lv, m)
        if L is None:
            continue
        grid.append({"site": sd["site"], "m0": m, "L": L, "E": energy(L), "day": day_of[m],
                     "ship": any((m + i) in smin for i in range(WIN))})
    passages, seen, snrs = [], set(), []
    med = float(np.median([g["E"] for g in grid])) if grid else None
    if med:
        for s, e in sd["ships"]:
            m0 = int(math.floor(((s + e) / 2.0 - WIN * 30.0) / 60.0))
            if m0 in seen:
                continue
            L = window(lv, m0)
            if L is None:
                continue
            snr = 10.0 * math.log10(energy(L) / med)
            snrs.append(snr)
            if snr < SNR_DB:
                continue
            seen.add(m0)
            passages.append({"site": sd["site"], "m0": m0, "L": L, "snr_db": snr})
    return {"grid": grid, "median_window_energy": med,
            "bg_train": [g for g in grid if g["day"] < n_train_days],
            "bg_test": [g for g in grid if g["day"] >= n_train_days],
            "train_p": passages[0::2], "test_p": passages[1::2],
            "passage_windows_complete": len(snrs),
            "passage_snr_median_db": float(np.median(snrs)) if snrs else None}


def make_set(rng, bgs, ves, n):
    X, y, f1, ship, site = [], [], [], [], []
    for _ in range(n):
        b = bgs[int(rng.integers(len(bgs)))]
        s = draw_share(rng)
        v = ves[int(rng.integers(len(ves)))]["L"] if s > 0 else None
        L, s = mix(b["L"], v, s)
        x = features(L)
        X.append(x)
        y.append(s)
        f1.append(x[-1])
        ship.append(b["ship"])
        site.append(b["site"])
    return {"X": np.array(X), "y": np.array(y), "F1": np.array(f1), "ship": np.array(ship, bool),
            "site": np.array(site)}


def stats(pred, y):
    pred, y = np.asarray(pred, float), np.asarray(y, float)
    out = {"n": int(len(y)), "rmse": float(np.sqrt(np.mean((pred - y) ** 2))),
           "bias": float(np.mean(pred - y)), "bins": {}}
    for name, sel in (("zero", y == 0), ("0-0.25", (y > 0) & (y <= 0.25)),
                      ("0.25-0.5", (y > 0.25) & (y <= 0.5)), ("0.5-0.9", y > 0.5)):
        if sel.any():
            out["bins"][name] = {"n": int(sel.sum()), "rmse": float(np.sqrt(np.mean((pred[sel] - y[sel]) ** 2))),
                                 "bias": float(np.mean(pred[sel] - y[sel]))}
    return out


def gates(sites_data, n_days=N_DAYS):
    ga_detail = {sd["site"]: {"days": len(sd["days"]),
                              "min_complete_minutes": min([d["complete_minutes"] for d in sd["days"]] or [0])}
                 for sd in sites_data}
    ga = (len(sites_data) == len(SITES) and
          all(v["days"] >= n_days and v["min_complete_minutes"] >= MIN_DAY_MINUTES for v in ga_detail.values()))
    return ga, ga_detail


def analyze(sites_data, n_test=N_TEST, n_train=N_TRAIN, n_train_days=N_TRAIN_DAYS, n_days=N_DAYS,
            min_passages=MIN_PASSAGES, seed=0):
    built = {sd["site"]: build_site(sd, n_train_days) for sd in sites_data}
    ga, ga_detail = gates(sites_data, n_days)
    bg_train = [g for s in sorted(built) for g in built[s]["bg_train"]]
    bg_test = [g for s in sorted(built) for g in built[s]["bg_test"]]
    vessel_sites = [s for s in sorted(built)
                    if len(built[s]["train_p"]) >= min_passages and len(built[s]["test_p"]) >= min_passages]
    gb = len(vessel_sites) >= 2 and bool(bg_train) and bool(bg_test)
    res = {"version": VERSION, "gate_GA": ga, "gate_GA_detail": ga_detail, "gate_GB": gb,
           "vessel_sites": vessel_sites, "sites": {}, "folds": [], "pooled": {}}
    for s in sorted(built):
        b = built[s]
        res["sites"][s] = {"grid_windows": len(b["grid"]), "bg_train": len(b["bg_train"]),
                           "bg_test": len(b["bg_test"]),
                           "bg_windows_with_ship": int(sum(g["ship"] for g in b["grid"])),
                           "passage_windows_complete": b["passage_windows_complete"],
                           "passage_snr_median_db": b["passage_snr_median_db"],
                           "passages_train": len(b["train_p"]), "passages_test": len(b["test_p"])}
    if not gb:
        return res
    pool = {k: [] for k in ("y", "C0", "F1", "G0", "G1", "ship", "site")}
    for idx, k in enumerate(vessel_sites):
        te = make_set(np.random.default_rng(seed + 1000 + idx), bg_test, built[k]["test_p"], n_test)
        others = [p for s in sorted(built) if s != k for p in built[s]["train_p"]]
        tr1 = make_set(np.random.default_rng(seed + 2000 + idx), bg_train, others, n_train)
        tr0 = make_set(np.random.default_rng(seed + 3000 + idx), bg_train, built[k]["train_p"], n_train)
        c0 = float(tr1["y"].mean())
        preds = {"C0": np.full(len(te["y"]), c0), "F1": te["F1"],
                 "G1": fit_predict(tr1["X"], tr1["y"], te["X"], seed),
                 "G0": fit_predict(tr0["X"], tr0["y"], te["X"], seed)}
        fold = {"test_vessel_site": k, "c0": c0, "train_vessels_G1": len(others),
                "train_vessels_G0": len(built[k]["train_p"]), "test_vessels": len(built[k]["test_p"]),
                "stats": {m: stats(p, te["y"]) for m, p in preds.items()}}
        res["folds"].append(fold)
        pool["y"].append(te["y"])
        pool["ship"].append(te["ship"])
        pool["site"].append(te["site"])
        for m in ("C0", "F1", "G0", "G1"):
            pool[m].append(preds[m])
    P = {k: np.concatenate(v) for k, v in pool.items()}
    res["pooled"] = {m: stats(P[m], P["y"]) for m in ("C0", "F1", "G0", "G1")}
    zero = P["y"] == 0
    res["pooled"]["F1_mean_on_zero"] = float(P["F1"][zero].mean()) if zero.any() else None
    hi = P["y"] >= 0.5
    res["pooled"]["F1_bias_share_ge_0.5"] = float((P["F1"][hi] - P["y"][hi]).mean()) if hi.any() else None
    p7 = {}
    for s in sorted(built):
        a = zero & (P["site"] == s) & P["ship"]
        b = zero & (P["site"] == s) & ~P["ship"]
        p7[s] = {"n_ship": int(a.sum()), "n_noship": int(b.sum()),
                 "G1_mean_ship": float(P["G1"][a].mean()) if a.any() else None,
                 "G1_mean_noship": float(P["G1"][b].mean()) if b.any() else None}
    res["pooled"]["P7_by_site"] = p7
    return res


# ---------------------------------------------------------------- grading (pre-registered)
def grade(res):
    g = []

    def add(pid, text, held, value):
        g.append({"id": pid, "prediction": text, "held": held, "value": value})

    ok = res.get("gate_GA") and res.get("gate_GB") and res.get("pooled")
    if not ok:
        for pid in ("P1", "P2", "P3", "P4", "P5", "P6", "P7"):
            add(pid, "ungraded", None, "gate failed (GA=%s, GB=%s)" % (res.get("gate_GA"), res.get("gate_GB")))
        return g
    p = res["pooled"]
    r = {m: p[m]["rmse"] for m in ("C0", "F1", "G0", "G1")}
    add("P1", "pooled RMSE(G1) <= 0.6 x RMSE(C0)", r["G1"] <= 0.6 * r["C0"],
        {"G1": r["G1"], "C0": r["C0"], "ratio": r["G1"] / r["C0"]})
    add("P2", "pooled RMSE(F1) < RMSE(C0)", r["F1"] < r["C0"], {"F1": r["F1"], "C0": r["C0"]})
    add("P3", "pooled RMSE(G1) < RMSE(F1)", r["G1"] < r["F1"], {"G1": r["G1"], "F1": r["F1"]})
    every = all(f["stats"]["G0"]["rmse"] < f["stats"]["G1"]["rmse"] for f in res["folds"])
    ratio = r["G1"] / r["G0"] if r["G0"] > 0 else None
    add("P4", "RMSE(G0) < RMSE(G1) in every fold and pooled RMSE(G1)/RMSE(G0) >= 1.10",
        bool(every and ratio is not None and ratio >= 1.10),
        {"every_fold": every, "pooled_ratio": ratio,
         "folds": {f["test_vessel_site"]: [f["stats"]["G0"]["rmse"], f["stats"]["G1"]["rmse"]] for f in res["folds"]}})
    v5 = p["F1_mean_on_zero"]
    add("P5", "mean F1 on share-0 windows > 0.05", None if v5 is None else v5 > 0.05, v5)
    v6 = p["F1_bias_share_ge_0.5"]
    add("P6", "mean (F1 - share) on windows with share >= 0.5 is < 0", None if v6 is None else v6 < 0, v6)
    elig = {s: v for s, v in p["P7_by_site"].items() if v["n_ship"] >= 20 and v["n_noship"] >= 20}
    if not elig:
        add("P7", "share-0 windows: G1 mean higher with a labelled ship in the background (within site)",
            None, {"eligible_sites": 0, "by_site": p["P7_by_site"]})
    else:
        wins = sum(1 for v in elig.values() if v["G1_mean_ship"] > v["G1_mean_noship"])
        add("P7", "share-0 windows: G1 mean higher with a labelled ship in the background (within site)",
            wins * 2 > len(elig), {"eligible_sites": len(elig), "sites_higher": wins, "by_site": p["P7_by_site"]})
    return g


# ---------------------------------------------------------------- download and read
def http_get(url, tries=4):
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # transient network errors
            last = e
            time.sleep(5 * (t + 1))
    raise last


def list_objects(prefix):
    items, token = [], None
    while True:
        q = {"prefix": prefix, "fields": "items(name,size),nextPageToken"}
        if token:
            q["pageToken"] = token
        data = json.loads(http_get(LIST_API + "?" + urllib.parse.urlencode(q)).decode("utf-8"))
        items += data.get("items", [])
        token = data.get("nextPageToken")
        if not token:
            return items


def download(item, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, item["name"].rsplit("/", 1)[-1])
    size = int(item.get("size", -1))
    if os.path.exists(path) and os.path.getsize(path) == size:
        return path
    url = OBJ + urllib.parse.quote(item["name"])
    last = None
    for t in range(4):
        try:
            tmp = path + ".part"
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            if size >= 0 and os.path.getsize(tmp) != size:
                raise IOError("size mismatch for %s" % item["name"])
            os.replace(tmp, path)
            return path
        except Exception as e:
            last = e
            time.sleep(10 * (t + 1))
    raise last


def file_day0_minute(path):
    m = re.search(r"(\d{8})\.nc$", path)
    if not m:
        return None
    d = datetime.strptime(m.group(1), "%Y%m%d").replace(tzinfo=timezone.utc)
    return int(d.timestamp() // 60)


def read_hmd(path):
    import netCDF4
    ds = netCDF4.Dataset(path)
    try:
        fvar = next((n for n in ("frequency", "frequency_bins", "freq")
                     if n in ds.variables and ds.variables[n].ndim == 1), None)
        if fvar is None and "psd" in ds.variables:
            fvar = next((d for d in ds.variables["psd"].dimensions
                         if d in ds.variables and ds.variables[d].ndim == 1 and d != "time"), None)
        if fvar is None:
            raise ValueError("no frequency variable; variables: %s" % list(ds.variables))
        freqs = np.asarray(ds.variables[fvar][:], dtype=float)
        nf = len(freqs)
        pvar = next((n for n in ("psd",) + tuple(ds.variables)
                     if n in ds.variables and n != fvar and ds.variables[n].ndim == 2
                     and nf in ds.variables[n].shape), None)
        if pvar is None:
            raise ValueError("no 2-D spectrum variable; variables: %s" % list(ds.variables))
        v = ds.variables[pvar]
        arr = np.ma.asarray(v[:]).astype(float).filled(np.nan)
        if v.dimensions[0] == ds.variables[fvar].dimensions[0]:
            arr = arr.T
        n = arr.shape[0]
        day0 = file_day0_minute(path)
        minutes, method = None, "row index from file name date"
        if "time" in ds.variables:
            try:
                tv = ds.variables["time"]
                dts = netCDF4.num2date(tv[:], tv.units, getattr(tv, "calendar", "standard"),
                                       only_use_cftime_datetimes=False, only_use_python_datetimes=True)
                cand = [int(math.floor(d.replace(tzinfo=timezone.utc).timestamp() / 60.0 + 1e-6))
                        for d in np.ravel(dts)]
                if len(cand) == n and (day0 is None or (day0 - 1440 <= min(cand) and max(cand) < day0 + 2880)):
                    minutes, method = cand, "time variable"
            except Exception as e:  # fall back to the file name's date
                method = "row index from file name date (time decode failed: %s)" % type(e).__name__
        if minutes is None:
            if day0 is None:
                raise ValueError("cannot place rows in time")
            minutes = [day0 + i for i in range(n)]
        return freqs, minutes, arr, {"psd_var": pvar, "freq_var": fvar, "n_freq": nf,
                                     "f_min": float(freqs.min()), "f_max": float(freqs.max()),
                                     "time_method": method}
    finally:
        ds.close()


def fetch_site(site, data_dir, log):
    rec = {"site": site, "lv": {}, "day_of": {}, "ships": [], "days": []}
    info = log.setdefault(site, {})
    try:
        hprefix = "sanctsound/products/sound_level_metrics/%s/sanctsound_%s_%s_hmd/data/" % (site, site, DEPLOYMENT)
        items = sorted([i for i in list_objects(hprefix) if i["name"].endswith(".nc")], key=lambda i: i["name"])
        info["hmd_files_listed"] = len(items)
        chosen = items[1:1 + N_DAYS]
        sprefix = "sanctsound/products/detections/%s/sanctsound_%s_%s_ships/data/" % (site, site, DEPLOYMENT)
        csvs = [i for i in list_objects(sprefix) if i["name"].endswith(".csv")]
        info["ships_file"] = csvs[0]["name"] if csvs else None
        if csvs:
            rec["ships"] = parse_ships(http_get(OBJ + urllib.parse.quote(csvs[0]["name"])).decode("utf-8", "replace"))
        info["ship_detections"] = len(rec["ships"])
        for di, it in enumerate(chosen):
            path = download(it, os.path.join(data_dir, site))
            freqs, minutes, psd, meta = read_hmd(path)
            tol = psd_db_to_tol_db(psd, tol_matrix(freqs))
            n_ok = 0
            for m, row in zip(minutes, tol):
                if np.all(np.isfinite(row)) and m not in rec["lv"]:
                    rec["lv"][m] = row
                    rec["day_of"][m] = di
                    n_ok += 1
            day = {"file": it["name"].rsplit("/", 1)[-1], "rows": len(minutes), "complete_minutes": n_ok}
            day.update(meta)
            rec["days"].append(day)
    except Exception as e:
        info["error"] = "%s: %s" % (type(e).__name__, e)
    info["days"] = rec["days"]
    return rec


def write_md(res, path):
    lines = ["# vessel_mix %s: automatic results" % res["version"], "",
             "Gates: GA=%s, GB=%s. Vessel folds: %s." % (res["gate_GA"], res["gate_GB"], ", ".join(res["vessel_sites"]) or "none"),
             "", "| site | grid windows | bg train | bg test | bg with ship | passage windows | median SNR dB | passages train/test |",
             "|---|---|---|---|---|---|---|---|"]
    for s, v in res["sites"].items():
        snr = v["passage_snr_median_db"]
        lines.append("| %s | %d | %d | %d | %d | %d | %s | %d/%d |" % (
            s, v["grid_windows"], v["bg_train"], v["bg_test"], v["bg_windows_with_ship"],
            v["passage_windows_complete"], "-" if snr is None else "%.1f" % snr, v["passages_train"], v["passages_test"]))
    if res["pooled"]:
        lines += ["", "| estimator | pooled RMSE | bias | " + " | ".join("fold %s" % f["test_vessel_site"] for f in res["folds"]) + " |",
                  "|---|---|---|" + "---|" * len(res["folds"])]
        for m in ("C0", "F1", "G0", "G1"):
            p = res["pooled"][m]
            lines.append("| %s | %.4f | %+.4f | %s |" % (m, p["rmse"], p["bias"],
                         " | ".join("%.4f" % f["stats"][m]["rmse"] for f in res["folds"])))
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
    sites_data = [fetch_site(s, a.data_dir, log) for s in SITES]
    res = analyze(sites_data)
    res["fetch"] = log
    res["grades"] = grade(res)
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    write_md(res, os.path.join(a.out_dir, "RESULTS-vesselmix-auto.md"))
    print(json.dumps({"gates": [res["gate_GA"], res["gate_GB"]], "vessel_sites": res["vessel_sites"],
                      "pooled_rmse": {m: res["pooled"][m]["rmse"] for m in ("C0", "F1", "G0", "G1")} if res["pooled"] else None,
                      "grades": [(g["id"], g["held"]) for g in res["grades"]]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
