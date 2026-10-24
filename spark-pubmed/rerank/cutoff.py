"""Cutoff, calibration and fusion counts for SPARK Task 1 reranked candidates.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Reads a ranked.jsonl written by rerank_run.py (candidates [pmid, sigmoid score] in cross-encoder
order, raw `logits` of the reranked head, `bm25_rank` of every candidate) and a t1.py gold.jsonl
({"info_need_id", "gold": [pmid, ...]}), and writes cutoff.json with counts only, never text:

- policies: MRR@5, hit share, mean items returned, mean wrong items and three penalised scores
  for "top:k" (first k), "abs:t" (first item always, others at sigmoid >= t), "abs0:t" (every
  item at sigmoid >= t, possibly none) and "margin:m" (items within m logits of the first);
- best: the policy with the highest MRR ("0") and the highest penalised score per lambda;
- calibration: how often the first item is gold, by its score band, and the AUROC of the first
  item's score for "first item is gold" (and of every top-5 item's score for "item is gold");
- orders: MRR@5 and hit share for the cross-encoder order, the BM25 order, and reciprocal-rank
  fusion of the two over the reranked head, 1/(k + CE rank) + 1/(k + BM25 rank), k = 10 and 60.

Task 1 says submissions "will be penalized if they include incorrect citations" but not how.
The penalised score here, the mean over questions of RR - lambda * wrong / 5 (lambda 0.25, 0.5,
1), is an assumption for comparing policies, not the challenge's metric. On BioGen, "wrong" means
"not judged Supports", which includes unjudged papers. Standard library only.

  python cutoff.py --ranked F --gold F --out-dir D
"""
import argparse
import json
import os
import sys

VERSION = "0.1.0"
MAX_ITEMS = 5
LAMBDAS = (0.25, 0.5, 1.0)
POLICIES = ("top:1", "top:2", "top:3", "top:4", "top:5",
            "abs:0.1", "abs:0.3", "abs:0.5", "abs:0.7", "abs:0.9",
            "abs0:0.1", "abs0:0.3", "abs0:0.5", "abs0:0.7", "abs0:0.9",
            "margin:1", "margin:2", "margin:4")
BANDS = (0.0, 0.1, 0.3, 0.5, 0.7, 0.9)
FUSION_K = (10, 60)


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def parse_policy(policy):
    kind, _, value = policy.partition(":")
    x = float(value)  # ValueError for a bad number
    if kind == "top" and x == int(x) and 1 <= x <= MAX_ITEMS:
        return kind, int(x)
    if kind in ("abs", "abs0") and 0 <= x <= 1:
        return kind, x
    if kind == "margin" and x >= 0:
        return kind, x
    raise ValueError("bad policy %r" % policy)


def cut(row, policy):
    """PMIDs (str) to return for one ranked row under a policy."""
    kind, x = parse_policy(policy)
    top = row["candidates"][:MAX_ITEMS]
    if not top:
        return []
    if kind == "top":
        return [str(p) for p, _ in top[:x]]
    if kind == "abs":
        return [str(top[0][0])] + [str(p) for p, s in top[1:] if s >= x]
    if kind == "abs0":
        return [str(p) for p, s in top if s >= x]
    logits = row.get("logits") or []
    if not logits:
        return [str(top[0][0])]
    return [str(p) for (p, _), lg in zip(top, logits) if lg >= logits[0] - x]


def rr_of(kept, good):
    for i, p in enumerate(kept, 1):
        if p in good:
            return 1.0 / i
    return 0.0


def policy_scores(rows, by, policies=POLICIES, lambdas=LAMBDAS):
    out, n = {}, len(rows)
    for pol in policies:
        rr = hits = returned = wrong = empty = 0
        pen = dict.fromkeys(lambdas, 0.0)
        for r in rows:
            kept = cut(r, pol)
            good = by[r["info_need_id"]]
            x = rr_of(kept, good)
            w = sum(1 for p in kept if p not in good)
            rr += x
            hits += x > 0
            returned += len(kept)
            wrong += w
            empty += not kept
            for lam in lambdas:
                pen[lam] += x - lam * w / MAX_ITEMS
        out[pol] = {"mrr": round(rr / n, 4), "hit": round(hits / n, 4),
                    "mean_returned": round(returned / n, 3), "mean_wrong": round(wrong / n, 3),
                    "empty": empty, "penalised": {str(lam): round(pen[lam] / n, 4) for lam in lambdas}}
    return out


def best(pols, lambdas=LAMBDAS):
    """Winning policy name per lambda ("0" = plain MRR); ties go to fewer items, then list order."""
    names = list(pols)
    res = {"0": max(names, key=lambda p: (pols[p]["mrr"], -pols[p]["mean_returned"]))}
    for lam in lambdas:
        k = str(lam)
        res[k] = max(names, key=lambda p: (pols[p]["penalised"][k], -pols[p]["mean_returned"]))
    return res


def auroc(pos, neg):
    """P(a random positive scores above a random negative), ties half; None if a side is empty."""
    if not pos or not neg:
        return None
    wins = 0.0
    for a in pos:
        for b in neg:
            wins += 1.0 if a > b else 0.5 if a == b else 0.0
    return round(wins / (len(pos) * len(neg)), 4)


def band_of(s, bands=BANDS):
    k = 0
    for i, lo in enumerate(bands):
        if s >= lo:
            k = i
    return k


def calibration(rows, by, bands=BANDS):
    labels = ["%.1f-%.1f" % (lo, bands[i + 1] if i + 1 < len(bands) else 1.0) for i, lo in enumerate(bands)]
    table = {lab: {"needs": 0, "first_is_gold": 0} for lab in labels}
    fp, fn, ip, ineg = [], [], [], []
    for r in rows:
        top = r["candidates"][:MAX_ITEMS]
        if not top:
            continue
        good = by[r["info_need_id"]]
        s0, ok = top[0][1], str(top[0][0]) in good
        lab = labels[band_of(s0, bands)]
        table[lab]["needs"] += 1
        table[lab]["first_is_gold"] += int(ok)
        (fp if ok else fn).append(s0)
        for p, s in top:
            (ip if str(p) in good else ineg).append(s)
    return {"bands": table, "first_is_gold": len(fp), "first_not_gold": len(fn),
            "first_item_auroc": auroc(fp, fn), "top5_items_gold": len(ip),
            "top5_items_not_gold": len(ineg), "top5_item_auroc": auroc(ip, ineg)}


def fuse(row, k):
    """Candidates with the reranked head reordered by reciprocal-rank fusion of cross-encoder and
    BM25 ranks (ties keep cross-encoder order); the rest follow unchanged."""
    cands = row["candidates"]
    n = len(row.get("logits") or [])
    bm = row.get("bm25_rank") or list(range(1, len(cands) + 1))
    head = sorted(range(n), key=lambda i: (-(1.0 / (k + i + 1) + 1.0 / (k + bm[i])), i))
    return [cands[i] for i in head] + cands[n:]


def bm25_order(row):
    cands = row["candidates"]
    bm = row.get("bm25_rank") or list(range(1, len(cands) + 1))
    return [cands[i] for i in sorted(range(len(cands)), key=lambda i: (bm[i], i))]


def order_scores(rows, by, ks=FUSION_K):
    orders = [("ce", lambda r: r["candidates"]), ("bm25", bm25_order)]
    orders += [("rrf%d" % k, lambda r, k=k: fuse(r, k)) for k in ks]
    out, n = {}, len(rows)
    for name, order in orders:
        rr = hits = 0
        for r in rows:
            x = rr_of([str(p) for p, _ in order(r)[:MAX_ITEMS]], by[r["info_need_id"]])
            rr += x
            hits += x > 0
        out[name] = {"mrr": round(rr / n, 4), "hit": round(hits / n, 4)}
    return out


def analyze(ranked, gold):
    by = {g["info_need_id"]: {str(p) for p in g["gold"]} for g in gold}
    rows = [r for r in ranked if r["info_need_id"] in by]
    out = {"version": VERSION, "needs": len(rows),
           "no_gold": sum(1 for r in ranked if r["info_need_id"] not in by), "lambdas": list(LAMBDAS)}
    if not rows:
        return out
    out["policies"] = policy_scores(rows, by)
    out["best"] = best(out["policies"])
    out["calibration"] = calibration(rows, by)
    out["orders"] = order_scores(rows, by)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ranked", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    res = analyze(load_jsonl(a.ranked), load_jsonl(a.gold))
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "cutoff.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ("needs", "no_gold", "best", "orders") if k in res}, indent=1))
    return 0 if res["needs"] else 1


if __name__ == "__main__":
    sys.exit(main())
