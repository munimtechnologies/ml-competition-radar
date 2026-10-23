"""Time BM25 queries on the SPARK PubMed index, to plan the scoring jobs.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Runs 20 fixed, general health questions (written for this probe, not taken from any challenge
or test set) through build_index.search at depth --k, twice: the first pass meets a cold page
cache, the second a warm one. A query that runs past --query-seconds is interrupted and counted.
Writes probe.json with timings and result counts only (no titles, no abstracts).
"""
import argparse
import json
import os
import sqlite3
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index  # noqa: E402

VERSION = "0.1"
QUERIES = (
    "metformin effect on blood glucose in type 2 diabetes",
    "statin therapy and risk of cardiovascular events",
    "vitamin D supplementation and bone fracture risk in older adults",
    "aspirin for primary prevention of stroke",
    "exercise training and depression symptoms",
    "smoking cessation and lung function decline",
    "antibiotic resistance in urinary tract infections",
    "BRCA1 mutation and breast cancer risk",
    "sleep duration and obesity in children",
    "influenza vaccination effectiveness in the elderly",
    "long term proton pump inhibitor use and kidney disease",
    "mediterranean diet and cognitive decline",
    "blood pressure targets in chronic kidney disease",
    "iron deficiency anemia in pregnancy and birth outcomes",
    "physical therapy for chronic low back pain",
    "gut microbiome and inflammatory bowel disease",
    "HPV vaccination and cervical cancer incidence",
    "air pollution exposure and asthma exacerbations",
    "caffeine intake and atrial fibrillation",
    "beta blockers for migraine prevention",
)


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def timed(con, text, k, limit_s, clock=time.perf_counter):
    """(ms, results or None if interrupted)."""
    t0 = clock()
    con.set_progress_handler(lambda: 1 if clock() - t0 > limit_s else 0, 100000)
    try:
        res = build_index.search(con, text, k)
    except sqlite3.OperationalError as e:
        if "interrupt" not in str(e):
            raise
        res = None
    finally:
        con.set_progress_handler(None, 0)
    return round((clock() - t0) * 1000, 1), res


def summarise(rows):
    ms = [r["ms"] for r in rows]
    done = [r for r in rows if r["results"] is not None]
    return {"queries": len(rows), "interrupted": len(rows) - len(done),
            "ms_median": round(statistics.median(ms), 1) if ms else None,
            "ms_p90": pct(ms, 0.9), "ms_max": max(ms, default=None),
            "results_min": min((r["results"] for r in done), default=None)}


def probe(db, k=50, limit_s=120.0, queries=QUERIES):
    con = sqlite3.connect(db)
    try:
        files, docs = con.execute("SELECT COUNT(*), COALESCE(SUM(docs), 0) - COALESCE(SUM(replaced), 0) "
                                  "FROM built").fetchone()
        passes = []
        for _ in range(2):
            rows = []
            for q in queries:
                ms, res = timed(con, q, k, limit_s)
                rows.append({"ms": ms, "results": None if res is None else len(res)})
            passes.append(rows)
    finally:
        con.close()
    return {"version": VERSION, "files_built": files, "docs": docs, "k": k,
            "query_seconds_limit": limit_s, "cold": summarise(passes[0]), "warm": summarise(passes[1]),
            "cold_ms": [r["ms"] for r in passes[0]], "warm_ms": [r["ms"] for r in passes[1]]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--k", type=int, default=50)
    ap.add_argument("--query-seconds", type=float, default=120.0)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    res = {"version": VERSION, "problem": None}
    try:
        if not os.path.exists(a.db):
            raise FileNotFoundError(a.db)
        res.update(probe(a.db, a.k, a.query_seconds))
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    with open(os.path.join(a.out_dir, "probe.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    return 1 if res["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
