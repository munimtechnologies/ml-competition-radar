"""Counts for job spark44-dense-v1: does a dense first stage reach SPARK Task 1 targets that BM25
misses?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Per leg (a BM25 list, the dense list from dense_search.py and a t1.py gold file):

- coverage: distinct gold PMIDs, how many are in the one-bit index (PMID p is looked up in chunk
  p // 1,000,000), and questions with at least one gold paper in the index;
- reach: questions with a gold paper within the first d candidates, for BM25 alone and dense
  alone (depths up to each list's shortest length);
- union b+k: BM25's first b, then dense's first k not already in them; reach, mean number of
  candidates, and against BM25 alone at depth b+k, the ids of questions gained and lost;
- mrr5 / hit5: top:5 MRR and hits of each list on its own (no cross-encoder).

The rule written in PREREGISTRATION-spark44.md is applied in `decide`. Ids and counts only, never
question text.

  python dense_eval.py --index-dir D --out F --leg NAME=BM25=DENSE=GOLD [--leg ...]
"""
import argparse
import json
import os
import sys

import numpy as np

VERSION = "0.1.0"
SPAN = 1000000
DEPTHS = (20, 50, 100, 150, 200, 300, 1000)
UNIONS = ((50, 50), (100, 50), (150, 50), (50, 100), (100, 100))
KEY, BUDGET, NEED_GAIN, MAX_LOSS = "100+50", 150, 3, 1


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class IndexPmids:
    """Membership in the built index; each chunk's PMIDs are loaded once, sorted."""

    def __init__(self, index_dir):
        self.index_dir, self.cache = index_dir, {}

    def __contains__(self, pmid):
        x = int(pmid)
        k = x // SPAN
        if k not in self.cache:
            p = os.path.join(self.index_dir, "pmids_%d.npy" % k)
            self.cache[k] = np.sort(np.load(p)) if os.path.exists(p) else np.zeros(0, dtype=np.int64)
        arr = self.cache[k]
        i = int(np.searchsorted(arr, x))
        return i < len(arr) and int(arr[i]) == x


def bm25_list(row):
    """Candidates in BM25 order: by `bm25_rank` when a reranker reordered them, else as listed."""
    c = [str(p) for p, _ in row["candidates"]]
    if "bm25_rank" in row:
        return [p for _, p in sorted(zip(row["bm25_rank"], c))]
    return c


def union(a, b, na, nb):
    out = list(a[:na])
    seen = set(out)
    for p in b[:nb]:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def rr5(lst, good):
    for i, p in enumerate(lst[:5], 1):
        if p in good:
            return 1.0 / i
    return 0.0


def leg_eval(bm_rows, dense_rows, gold_rows, index, depths=DEPTHS, unions=UNIONS):
    gold = {str(g["info_need_id"]): {str(p) for p in g["gold"]} for g in gold_rows}
    bm = {str(r["info_need_id"]): bm25_list(r) for r in bm_rows}
    dn = {str(r["info_need_id"]): [str(p) for p, _ in r["candidates"]] for r in dense_rows}
    ids = [i for i in bm if i in gold and i in dn]
    out = {"needs": len(ids), "no_gold": sum(1 for i in bm if i not in gold),
           "no_dense": sum(1 for i in bm if i in gold and i not in dn)}
    if not ids:
        return out
    pm = sorted({p for i in ids for p in gold[i]})
    inside = {p for p in pm if p in index}
    out["coverage"] = {"gold_pmids": len(pm), "in_index": len(inside),
                       "share": round(len(inside) / len(pm), 4) if pm else None,
                       "needs_with_gold_in_index": sum(1 for i in ids if gold[i] & inside)}
    bm_depth, dn_depth = min(len(bm[i]) for i in ids), min(len(dn[i]) for i in ids)
    out.update(bm25_depth=bm_depth, dense_depth=dn_depth)

    def reach(lists, d):
        return sum(1 for i in ids if gold[i] & set(lists[i][:d]))
    out["bm25"] = {str(d): reach(bm, d) for d in depths if d <= bm_depth}
    out["dense"] = {str(d): reach(dn, d) for d in depths if d <= dn_depth}
    out["union"] = {}
    for na, nb in unions:
        if na + nb > bm_depth or nb > dn_depth:
            continue
        u = {i: union(bm[i], dn[i], na, nb) for i in ids}
        hit_u = {i for i in ids if gold[i] & set(u[i])}
        hit_b = {i for i in ids if gold[i] & set(bm[i][:na + nb])}
        out["union"]["%d+%d" % (na, nb)] = {
            "reach": len(hit_u), "mean_candidates": round(sum(len(u[i]) for i in ids) / len(ids), 1),
            "bm25_same_budget": len(hit_b), "gained": sorted(hit_u - hit_b), "lost": sorted(hit_b - hit_u)}
    for name, lists in (("bm25", bm), ("dense", dn)):
        rr = [rr5(lists[i], gold[i]) for i in ids]
        out["%s_mrr5" % name] = round(sum(rr) / len(ids), 4)
        out["%s_hit5" % name] = sum(1 for x in rr if x > 0)
    return out


def decide(legs, key=KEY, budget=BUDGET, need_gain=NEED_GAIN, max_loss=MAX_LOSS):
    rule = ("adopt union %s if on L its reach beats BM25 alone at depth %d by at least %d and on "
            "BioGen and R it is at most %d below BM25 alone at depth %d" % (key, budget, need_gain, max_loss, budget))
    why = []
    for g in ("l", "bg", "r"):
        x = legs.get(g, {})
        if key not in x.get("union", {}) or str(budget) not in x.get("bm25", {}):
            why.append("leg %s lacks union %s or BM25 at %d" % (g, key, budget))
    if why:
        return {"rule": rule, "adopt": False, "why": why}
    diff = {g: legs[g]["union"][key]["reach"] - legs[g]["bm25"][str(budget)] for g in ("l", "bg", "r")}
    if diff["l"] < need_gain:
        why.append("L gains %d < %d" % (diff["l"], need_gain))
    for g in ("bg", "r"):
        if diff[g] < -max_loss:
            why.append("%s loses %d > %d" % (g, -diff[g], max_loss))
    return {"rule": rule, "adopt": not why, "why": why or ["adopted"], "reach_change": diff}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--index-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--leg", action="append", required=True)
    a = ap.parse_args(argv)
    index, legs = IndexPmids(a.index_dir), {}
    for spec in a.leg:
        name, bm, dn, gold = spec.split("=", 3)
        legs[name] = leg_eval(load_jsonl(bm), load_jsonl(dn), load_jsonl(gold), index)
    res = {"version": VERSION, "legs": legs, "decision": decide(legs)}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    return 0 if legs and all(x["needs"] for x in legs.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
