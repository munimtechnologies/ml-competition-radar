"""Stage 2 for SPARK Task 1: rerank t1.py's BM25 candidates with the cross-encoder.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Reads the ranked.jsonl that `t1.py run` writes, takes the first --depth candidates of each need,
fetches their title + abstract from the FTS5 index (build_index.py's `docs` table, rowid = PMID),
scores every (question, article) pair and writes a ranked.jsonl in the same format, so
`t1.py score` and its cutoff policies apply unchanged. Candidate scores are sigmoid(logit), so
the "ratio:r" policies stay meaningful (logits can be negative); the raw logits are kept in
`logits`. Candidates past the depth, and any candidate with no text in the index, follow the
reranked ones in their BM25 order with score 0.0. Writes rerank.json with timings.

The scorer is any object with score(query, docs) -> list of floats; `main` uses
rerank.CrossEncoder (torch), imported only when the command runs, so this file and its tests need
only the standard library.
"""
import argparse
import json
import math
import os
import sqlite3
import statistics
import sys
import time

VERSION = "0.1.0"


def sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def doc_text(title, abstract):
    """Title then abstract, as in the MedCPT card example (same as rerank.doc_text)."""
    return ((title or "").strip() + " " + (abstract or "").strip()).strip()


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def article(con, pmid):
    row = con.execute("SELECT title, abstract FROM docs WHERE rowid=?", (int(pmid),)).fetchone()
    return doc_text(*row) if row else ""


def rerank_need(con, scorer, need, depth):
    """One ranked.jsonl row in, one out. Returns (row, pairs scored, seconds)."""
    cands = need["candidates"]
    head, tail = cands[:depth], cands[depth:]
    texts = [(p, article(con, p)) for p, _ in head]
    scored = [(p, t) for p, t in texts if t]
    missing = [p for p, t in texts if not t]
    t0 = time.perf_counter()
    logits = scorer.score(need["info_need"], [t for _, t in scored]) if scored else []
    secs = time.perf_counter() - t0
    order = sorted(range(len(scored)), key=lambda i: (-logits[i], i))  # ties keep BM25 order
    out = [[scored[i][0], round(sigmoid(logits[i]), 6)] for i in order]
    out += [[p, 0.0] for p in missing] + [[p, 0.0] for p, _ in tail]
    bm25_rank = {p: i for i, (p, _) in enumerate(cands, 1)}
    row = {"info_need_id": need["info_need_id"], "info_need": need["info_need"],
           "candidates": out, "logits": [round(logits[i], 4) for i in order],
           "bm25_rank": [bm25_rank[p] for p, _ in out],
           "depth": need.get("depth", len(cands)), "rerank_depth": depth,
           "missing_text": missing, "ms": round(secs * 1000, 1)}
    return row, len(scored), secs


def run(db, ranked_path, out_dir, scorer, depth=50):
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    os.makedirs(out_dir, exist_ok=True)
    needs = load_jsonl(ranked_path)
    con = sqlite3.connect(db)
    rows, pairs, secs = [], 0, []
    for nd in needs:
        row, n, s = rerank_need(con, scorer, nd, depth)
        rows.append(row)
        pairs += n
        secs.append(s)
    con.close()
    with open(os.path.join(out_dir, "ranked.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    total = sum(secs)
    top_changed = sum(1 for r, nd in zip(rows, needs)
                      if r["candidates"] and nd["candidates"] and r["candidates"][0][0] != nd["candidates"][0][0])
    summary = {"version": VERSION, "needs": len(needs), "rerank_depth": depth, "pairs": pairs,
               "seconds": round(total, 1), "ms_per_pair": round(1000 * total / pairs, 1) if pairs else None,
               "median_need_seconds": round(statistics.median(secs), 2) if secs else None,
               "max_need_seconds": round(max(secs), 2) if secs else None,
               "needs_top1_changed": top_changed,
               "missing_text": sum(len(r["missing_text"]) for r in rows)}
    with open(os.path.join(out_dir, "rerank.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--ranked", required=True)
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--depth", type=int, default=50)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--batch", type=int, default=8)
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from rerank import CrossEncoder  # torch; imported here so the tests do not need it
    scorer = CrossEncoder(a.model_dir, batch_size=a.batch, threads=a.threads)
    s = run(a.db, a.ranked, a.out_dir, scorer, a.depth)
    print(json.dumps(s, indent=1))
    return 0 if s["needs"] else 1


if __name__ == "__main__":
    sys.exit(main())
