"""embcheck-3: what are the exactly-254-character chunks in TelcoRetrieve's text_baseline cells?

embcheck-2 (exploratory) found that chunks exactly 254 characters long are 8-9% of the sampled vectors
in GSMA's text_baseline cells but almost never reach a top 10 for public 3GPP questions. This script
reads every row of each cell's SQLite FTS5 chunk table (already in the job's data volume from
embcheck-2) and describes them: how many, whether 254 is a spike, whether they come in runs inside a
document, and simple character features against chunks of 200-253 characters. Pre-registered in
PREREGISTRATION-embcheck3.md before this job ran. Standard library only.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python telco_embcheck3.py --data-dir /data/telco --out-dir /out
"""
import argparse
import json
import os
import random
import sqlite3
import sys
import time
from urllib.request import pathname2url

VERSION = "0.3.0"
SEED = 20261112
L = 254
NEAR = (200, 253)
WIDTH = 14
MIN_ROWS = 1000000
N_SAMPLES = 25
CELLS = ("otel-0.6b", "qwen3-embedding-0.6b")
TABLE, ID_COL, TEXT_COL = "bm25_index", "doc_id", "text"
REPO = "GSMA/telco-retrieve-chunks"
BASE = "telcoretrievechallenge/fixed-grid/text_baseline"
DATA_REV = "2ec07608ee2a77a59a3f5995ca3c10e9cba4c976"  # the revision embcheck-1 and -2 read
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"
PREDICTIONS = ("D1", "D2", "D3", "D4", "D5", "D6")


# ---- pure functions (unit-tested offline) ----
def parse_doc_id(doc_id):
    """'Rel-19/23_series/23288-j20.md::otel-0.6b::1113' -> ('Rel-19/23_series/23288-j20.md', 1113)."""
    parts = str(doc_id).split("::")
    if len(parts) < 3:
        return parts[0], None
    try:
        return parts[0], int(parts[-1])
    except ValueError:
        return parts[0], None


def series_of(doc):
    parts = doc.split("/")
    return parts[1] if len(parts) >= 3 else "?"


def spike_ratio(hist, at=L, width=WIDTH):
    around = [hist.get(n, 0) for n in range(at - width, at + width + 1) if n != at]
    mean = sum(around) / float(len(around))
    return hist.get(at, 0) / mean if mean > 0 else None


def neighbour_share(keys):
    """Share of (doc, idx) keys whose (doc, idx - 1) or (doc, idx + 1) is also in keys."""
    if not keys:
        return None
    hit = sum(1 for d, i in keys if (d, i - 1) in keys or (d, i + 1) in keys)
    return hit / float(len(keys))


def features(text):
    n = len(text)
    s = text.rstrip()
    first = text.lstrip()[:1]
    return {"letters": sum(c.isalpha() for c in text) / float(n) if n else 0.0,
            "digits": sum(c.isdigit() for c in text) / float(n) if n else 0.0,
            "spaces": sum(c.isspace() for c in text) / float(n) if n else 0.0,
            "pipe": "|" in text,
            "ends_period": s.endswith("."),
            "starts_lower": first.islower(),
            "newlines": text.count("\n"),
            "max_token": max([len(w) for w in text.split()] or [0])}


def median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return float(xs[m]) if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def summarize(feats):
    out = {"n": len(feats)}
    if not feats:
        return out
    for k in ("letters", "digits", "spaces", "newlines", "max_token"):
        out[k + "_median"] = median([f[k] for f in feats])
    for k in ("pipe", "ends_period", "starts_lower"):
        out[k + "_share"] = sum(1 for f in feats if f[k]) / float(len(feats))
    return out


def scan_rows(rows, seed=SEED, n_samples=N_SAMPLES):
    """rows: iterable of (doc_id, text). Returns (cell summary, {(doc, idx): length}, samples)."""
    hist, series_all, series_l, cache = {}, {}, {}, {}
    keys_l, keys_near, lens = set(), set(), {}
    feats_l, feats_near, l_rows = [], [], []
    total = 0
    for doc_id, text in rows:
        text = text if isinstance(text, str) else ("" if text is None else str(text))
        n = len(text)
        total += 1
        hist[n] = hist.get(n, 0) + 1
        doc, idx = parse_doc_id(doc_id)
        doc = cache.setdefault(doc, doc)
        s = series_of(doc)
        series_all[s] = series_all.get(s, 0) + 1
        if idx is not None:
            lens[(doc, idx)] = n
        if n == L:
            series_l[s] = series_l.get(s, 0) + 1
            feats_l.append(features(text))
            l_rows.append((str(doc_id), text))
            if idx is not None:
                keys_l.add((doc, idx))
        elif NEAR[0] <= n <= NEAR[1]:
            feats_near.append(features(text))
            if idx is not None:
                keys_near.add((doc, idx))
    rng = random.Random(seed)
    picks = sorted(rng.sample(range(len(l_rows)), min(n_samples, len(l_rows))))
    samples = [{"doc_id": l_rows[i][0], "text": l_rows[i][1]} for i in picks]
    n_l = hist.get(L, 0)
    top = sorted(series_l.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
    cell = {"total": total,
            "l254_count": n_l,
            "l254_share": n_l / float(total) if total else None,
            "near_count": len(feats_near),
            "spike_ratio": spike_ratio(hist),
            "hist_240_268": {str(k): hist.get(k, 0) for k in range(L - WIDTH, L + WIDTH + 1)},
            "top_lengths": [[k, v] for k, v in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))[:10]],
            "l254_neighbour_share": neighbour_share(keys_l),
            "near_neighbour_share": neighbour_share(keys_near),
            "l254_docs": len(set(d for d, _ in keys_l)),
            "series_l254": [{"series": s, "l254": c, "share_of_l254": c / float(n_l),
                             "share_of_series_rows": c / float(series_all[s])} for s, c in top],
            "features_l254": summarize(feats_l),
            "features_near": summarize(feats_near)}
    return cell, lens, samples


def compare_lens(a, b):
    common = set(a) & set(b)
    same = sum(1 for k in common if a[k] == b[k])
    return {"keys_a": len(a), "keys_b": len(b), "common": len(common),
            "same_length_share": same / float(len(common)) if common else None}


def grade(res):
    if not (res.get("gates") or {}).get("GF"):
        return {p: None for p in PREDICTIONS}
    o, c = res["cells"][CELLS[0]], res["cells"][CELLS[1]]
    fl, fn = o["features_l254"], o["features_near"]
    both = fl["n"] > 0 and fn["n"] > 0
    return {"D1": 0.05 <= o["l254_share"] <= 0.12,
            "D2": abs(o["l254_count"] - c["l254_count"]) < 0.001 * o["total"],
            "D3": o["spike_ratio"] is not None and o["spike_ratio"] >= 20,
            "D4": o["l254_neighbour_share"] is not None and o["l254_neighbour_share"] >= 0.5,
            "D5": both and fl["letters_median"] < fn["letters_median"],
            "D6": both and fl["ends_period_share"] < fn["ends_period_share"]}


# ---- I/O (only in the sealed job) ----
def _http(url, tries=4):
    import urllib.request
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            return urllib.request.urlopen(req, timeout=180)
        except Exception as e:  # network hiccup: retry
            last = "%s: %s" % (type(e).__name__, e)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("GET %s failed: %s" % (url, last))


def download_db(name, dest):
    """Fallback when embcheck-2's cached copy is not in this host's volume: fetch the cell's
    FTS5 database at the pinned dataset revision."""
    api = "https://huggingface.co/api/datasets/%s/tree/%s/%s/%s/db" % (REPO, DATA_REV, BASE, name)
    with _http(api) as r:
        entries = json.loads(r.read().decode("utf-8"))
    hits = [x for x in entries if x.get("type") == "file" and x.get("path", "").endswith("_fts.db")]
    if len(hits) != 1:
        raise RuntimeError("%s: expected one _fts.db, got %d" % (name, len(hits)))
    size = (hits[0].get("lfs") or {}).get("size", hits[0].get("size"))
    url = "https://huggingface.co/datasets/%s/resolve/%s/%s" % (REPO, DATA_REV, hits[0]["path"])
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    with _http(url) as r, open(dest + ".part", "wb") as f:
        while True:
            block = r.read(1 << 22)
            if not block:
                break
            f.write(block)
    if os.path.getsize(dest + ".part") != size:
        raise RuntimeError("%s: got %d bytes, expected %s" % (url, os.path.getsize(dest + ".part"), size))
    os.replace(dest + ".part", dest)
    return "downloaded"


def _connect(path):
    """Read-only, lock-free open; plain open if the URI form is refused."""
    conn = None
    try:
        uri = "file:%s?mode=ro&immutable=1" % pathname2url(os.path.abspath(path))
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("SELECT 1 FROM %s LIMIT 1" % TABLE).fetchall()
        return conn
    except sqlite3.Error:
        if conn is not None:
            conn.close()
        return sqlite3.connect(path)


def iter_rows(path):
    conn = _connect(path)
    try:
        for row in conn.execute("SELECT %s, %s FROM %s" % (ID_COL, TEXT_COL, TABLE)):
            yield row
    finally:
        conn.close()


def write_md(res, path):
    lines = ["# embcheck-3 automatic summary (grade by hand before trusting)", "",
             "Script %s; finished %s. Gates: %s" % (VERSION, res.get("finished_utc"), json.dumps(res.get("gates"))), ""]
    for name in CELLS:
        c = res["cells"].get(name)
        if not c:
            lines += ["## %s: %s" % (name, res.get("errors", {}).get(name)), ""]
            continue
        lines += ["## %s" % name, "",
                  "- rows %d; L254 %d (%s); NEAR %d; spike ratio %s" % (
                      c["total"], c["l254_count"], c["l254_share"], c["near_count"], c["spike_ratio"]),
                  "- neighbour share L254 %s, NEAR %s; L254 docs %d" % (
                      c["l254_neighbour_share"], c["near_neighbour_share"], c["l254_docs"]),
                  "- top lengths %s" % json.dumps(c["top_lengths"]),
                  "- features L254 %s" % json.dumps(c["features_l254"]),
                  "- features NEAR %s" % json.dumps(c["features_near"]), ""]
    lines += ["## Cross-cell", "", json.dumps(res.get("cross")), "", "## Predictions (automatic)", ""]
    lines += ["- %s: %s" % (k, {True: "held", False: "failed", None: "not graded"}[v])
              for k, v in sorted((res.get("grades") or {}).items())]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--no-download", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    res = {"version": VERSION, "seed": SEED, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "cells": {}, "errors": {}}
    lens, samples = {}, {}
    for name in CELLS:
        path = os.path.join(a.data_dir, name + "_fts.db")
        try:
            fetch = "cached"
            if not os.path.exists(path):
                if a.no_download:
                    raise FileNotFoundError(path)
                print("%s: no cached database, downloading" % name, flush=True)
                fetch = download_db(name, path)
            cell, lens[name], samples[name] = scan_rows(iter_rows(path))
            cell["db_fetch"] = fetch
            cell["db_bytes"] = os.path.getsize(path)
            res["cells"][name] = cell
            print("[%7.1fs] %s rows %d L254 %d" % (time.time() - t0, name, cell["total"], cell["l254_count"]), flush=True)
        except Exception as e:
            res["errors"][name] = "%s: %s" % (type(e).__name__, str(e)[:2000])
            print("%s failed: %s" % (name, res["errors"][name]), flush=True)
    if all(n in lens for n in CELLS):
        res["cross"] = compare_lens(lens[CELLS[0]], lens[CELLS[1]])
    lens = None
    res["gates"] = {"GF": all(res["cells"].get(n, {}).get("total", 0) >= MIN_ROWS for n in CELLS)}
    res["grades"] = grade(res)
    res["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(a.out_dir, "embcheck3.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(a.out_dir, "samples_embcheck3.json"), "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=1, ensure_ascii=False)
    write_md(res, os.path.join(a.out_dir, "RESULTS-embcheck3-auto.md"))
    print("grades %s" % res["grades"], flush=True)
    return 0 if not res["errors"] else 3


if __name__ == "__main__":
    sys.exit(main())
