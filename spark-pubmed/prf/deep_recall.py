"""How deep BM25 must go to reach the gold paper (job spark38-prf-v1, leg D).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

t1.py score stops at depth 100. A reranker can only reorder what the first stage returns, so this
counts, for a ranked.jsonl run at a larger depth, how many questions have a gold paper within the
first d candidates for d up to that depth, and where the first gold paper sits. It writes counts and
ranks only (never question text) to deep.json. Standard library only.

  python deep_recall.py --ranked RANKED --gold GOLD --out-dir D
"""
import argparse
import json
import os
import sys

VERSION = "0.1.0"
DEPTHS = (1, 5, 10, 20, 50, 100, 200, 300, 500, 1000)
BANDS = ((1, 5), (6, 50), (51, 100), (101, 200), (201, 500), (501, 1000))


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def first_gold_rank(cands, good):
    """1-based rank of the first gold PMID in [[pmid, score], ...], or None."""
    for i, (p, _) in enumerate(cands, 1):
        if str(p) in good:
            return i
    return None


def deep(ranked, gold, depths=DEPTHS, bands=BANDS):
    by = {g["info_need_id"]: set(g["gold"]) for g in gold}
    rows = [r for r in ranked if r["info_need_id"] in by]
    n = len(rows)
    max_depth = max((len(r["candidates"]) for r in rows), default=0)
    ranks = [first_gold_rank(r["candidates"], by[r["info_need_id"]]) for r in rows]
    out = {"version": VERSION, "needs": n, "max_candidates": max_depth,
           "no_gold": sorted(r["info_need_id"] for r in ranked if r["info_need_id"] not in by),
           "hits_at": {}, "recall_at": {}, "first_gold_rank_bands": {}, "not_found": sum(1 for k in ranks if k is None)}
    for d in depths:
        if d <= max_depth:
            hits = sum(1 for k in ranks if k is not None and k <= d)
            out["hits_at"][str(d)] = hits
            out["recall_at"][str(d)] = round(hits / n, 4) if n else None
    for lo, hi in bands:
        out["first_gold_rank_bands"]["%d-%d" % (lo, hi)] = sum(1 for k in ranks if k is not None and lo <= k <= hi)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ranked", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    res = deep(load_jsonl(a.ranked), load_jsonl(a.gold))
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "deep.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    return 0 if res["needs"] else 1


if __name__ == "__main__":
    sys.exit(main())
