"""Rerank-depth curve for SPARK Task 1: what reranking only BM25's first d candidates would have
scored, read from one cross-encoder run at a larger depth.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

rerank_run.py scores every (question, article) pair on its own and breaks ties by BM25 order, so
reranking BM25's first d candidates gives the same order as keeping, from a deeper rerank, only
the reranked items whose BM25 rank is at most d (up to float noise from padded batches). Reads a
ranked.jsonl written by rerank_run.py (candidates in cross-encoder order, `logits` of the reranked
head, `bm25_rank` of every candidate) and a t1.py gold.jsonl, and writes curve.json with counts
only, never text. For each depth d up to the run's rerank depth:

- reach: questions with a gold paper within BM25's first d candidates (the ceiling at depth d);
- mrr, hit5, hit1: top:5 MRR and the number of questions with a gold paper in the first five
  and first place of the restricted cross-encoder order;
- gained_vs_base, lost_vs_base: questions that gain or lose a top-5 hit against the base depth
  (50 when it is measured, else the smallest), i.e. what the extra candidates buy and cost.

Standard library only.

  python depth_curve.py --ranked F --gold F --out-dir D [--depths 20,50,100,150,200,300]
"""
import argparse
import json
import os
import sys

VERSION = "0.1.0"
MAX_ITEMS = 5
DEPTHS = (20, 50, 100, 150, 200, 300)


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def head(row):
    """(pmid, BM25 rank) of the reranked candidates, in cross-encoder order."""
    n = len(row.get("logits") or [])
    bm = row["bm25_rank"]
    return [(str(row["candidates"][i][0]), bm[i]) for i in range(n)]


def at_depth(row, d):
    """The first five items had only BM25's first d candidates been reranked."""
    return [p for p, b in head(row) if b <= d][:MAX_ITEMS]


def reaches(row, d, good):
    """Whether a gold paper is within BM25's first d candidates (reranked or not)."""
    return any(str(p) in good and b <= d for (p, _), b in zip(row["candidates"], row["bm25_rank"]))


def rr_of(kept, good):
    for i, p in enumerate(kept, 1):
        if p in good:
            return 1.0 / i
    return 0.0


def curve(ranked, gold, depths=DEPTHS):
    by = {g["info_need_id"]: {str(p) for p in g["gold"]} for g in gold}
    rows = [r for r in ranked if r["info_need_id"] in by]
    out = {"version": VERSION, "needs": len(rows),
           "no_gold": sum(1 for r in ranked if r["info_need_id"] not in by)}
    if not rows:
        return out
    top = min(r.get("rerank_depth", len(r.get("logits") or [])) for r in rows)
    used = sorted(d for d in set(depths) if d <= top)
    out["rerank_depth"] = top
    out["skipped_depths"] = sorted(d for d in set(depths) if d > top)
    out["depths"] = {}
    if not used:
        return out
    base = 50 if 50 in used else used[0]
    hit_base = {r["info_need_id"]: rr_of(at_depth(r, base), by[r["info_need_id"]]) > 0 for r in rows}
    n = len(rows)
    for d in used:
        rr = hit5 = hit1 = reach = gained = lost = 0
        for r in rows:
            good, was = by[r["info_need_id"]], hit_base[r["info_need_id"]]
            x = rr_of(at_depth(r, d), good)
            rr += x
            hit5 += x > 0
            hit1 += x == 1.0
            reach += reaches(r, d, good)
            gained += x > 0 and not was
            lost += x == 0 and was
        out["depths"][str(d)] = {"reach": reach, "mrr": round(rr / n, 4), "hit5": hit5, "hit1": hit1,
                                 "gained_vs_base": gained, "lost_vs_base": lost}
    out["base_depth"] = base
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ranked", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--depths", default=",".join(str(d) for d in DEPTHS))
    a = ap.parse_args(argv)
    depths = [int(x) for x in a.depths.split(",") if x.strip()]
    res = curve(load_jsonl(a.ranked), load_jsonl(a.gold), depths)
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "curve.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    return 0 if res["needs"] and res.get("depths") else 1


if __name__ == "__main__":
    sys.exit(main())
