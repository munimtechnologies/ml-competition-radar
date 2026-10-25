"""Table and decision for job spark42-quant-v1: does a cheaper cross-encoder keep Task 1's ranking?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

For each variant (a folder under --arms-dir) and leg (its subfolders l, bg, r, each holding
quant_run.py's ranked.jsonl and rerank.json): top:5 MRR, hit@5 and hit@1 against the leg's gold;
the change from the fp32/512 ranking the earlier jobs wrote (the leg's BASE file); how many
questions keep the same first item and the same top-five set; which questions gain or lose a
top-five hit (ids only); ms per pair and median seconds per question; and the cross-encoder
hours that 1,000 questions would take at depths 50, 100 and 200 at that speed. Then the rule
written in PREREGISTRATION-spark42.md picks the variant. Reads ranked files but writes counts and
ids only, never question or abstract text. Standard library only.

  python quant_table.py --arms-dir D --out F --leg l=BASE=GOLD --leg bg=BASE=GOLD --leg r=BASE=GOLD
                        [--control fp32_512]
"""
import argparse
import json
import os
import sys

VERSION = "0.1.0"
LEGS = ("l", "bg", "r")
MEAN_TOL, LEG_TOL, MIN_SPEEDUP = 0.01, 0.03, 1.2
DEPTHS = (50, 100, 200)
EPS = 1e-9


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def gold_map(rows):
    return {str(g["info_need_id"]): {str(p) for p in g["gold"]} for g in rows}


def top(row, k):
    return [str(c[0]) for c in row["candidates"][:k]]


def metrics(rows, gold):
    """top:5 MRR, hit@5, hit@1 over the rows that have gold; per-question first gold rank (or 0)."""
    first = {}
    for r in rows:
        i = str(r["info_need_id"])
        if i in gold:
            ranks = [n for n, p in enumerate(top(r, 5), 1) if p in gold[i]]
            first[i] = ranks[0] if ranks else 0
    n = len(first)
    mrr = sum(1.0 / v for v in first.values() if v) / n if n else 0.0
    return {"needs": n, "mrr5": mrr, "hit5": sum(1 for v in first.values() if v),
            "hit1": sum(1 for v in first.values() if v == 1)}, first


def compare(arm_rows, base_rows, gold):
    m, first = metrics(arm_rows, gold)
    bm, bfirst = metrics(base_rows, gold)
    a = {str(r["info_need_id"]): r for r in arm_rows}
    b = {str(r["info_need_id"]): r for r in base_rows}
    common = sorted(i for i in a if i in b)
    m.update({"d_mrr5": m["mrr5"] - bm["mrr5"], "common": len(common),
              "same_first": sum(1 for i in common if top(a[i], 1) == top(b[i], 1)),
              "same_set5": sum(1 for i in common if set(top(a[i], 5)) == set(top(b[i], 5))),
              "gained5": sorted(i for i in first if first[i] and not bfirst.get(i)),
              "lost5": sorted(i for i in first if bfirst.get(i) and not first[i])})
    return m


def hours(ms_per_pair, questions=1000, depths=DEPTHS):
    return {str(d): round(ms_per_pair * d * questions / 3.6e6, 2) for d in depths}


def rounded(m):
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}


def build(arms_dir, legs, control="fp32_512"):
    """legs: {leg: (base ranked path, gold path)}. Returns the table with the decision."""
    golds = {g: gold_map(load_jsonl(p)) for g, (_, p) in legs.items()}
    bases = {g: load_jsonl(p) for g, (p, _) in legs.items()}
    base = {g: metrics(bases[g], golds[g])[0] for g in legs}
    full = all(g in legs for g in LEGS)
    base_mean = sum(base[g]["mrr5"] for g in LEGS) / len(LEGS) if full else None
    arms = {}
    for arm in sorted(os.listdir(arms_dir)):
        if not os.path.isdir(os.path.join(arms_dir, arm)):
            continue
        entry, secs, pairs = {"legs": {}}, 0.0, 0
        for g in legs:
            d = os.path.join(arms_dir, arm, g)
            if not os.path.exists(os.path.join(d, "rerank.json")):
                continue
            with open(os.path.join(d, "rerank.json"), encoding="utf-8") as f:
                rr = json.load(f)
            m = compare(load_jsonl(os.path.join(d, "ranked.jsonl")), bases[g], golds[g])
            m.update({k: rr.get(k) for k in ("pairs", "ms_per_pair", "median_need_seconds",
                                              "missing_text", "variant")})
            entry["legs"][g] = m
            secs += rr.get("seconds") or 0.0
            pairs += rr.get("pairs") or 0
        entry["complete"] = all(g in entry["legs"] for g in LEGS)
        entry["ms_per_pair_all"] = round(1000.0 * secs / pairs, 1) if pairs else None
        if entry["ms_per_pair_all"]:
            entry["ce_hours_per_1000q"] = hours(entry["ms_per_pair_all"])
        if entry["complete"]:
            entry["mean_mrr5"] = sum(entry["legs"][g]["mrr5"] for g in LEGS) / len(LEGS)
        arms[arm] = entry
    ctl = arms.get(control, {}).get("legs", {}).get("l", {}).get("ms_per_pair")
    for arm, e in arms.items():
        mine = e["legs"].get("l", {}).get("ms_per_pair")
        e["speedup_l"] = round(ctl / mine, 2) if ctl and mine else None
    chosen, why = decide(arms, base_mean, control)
    out = {"version": VERSION, "legs": sorted(legs), "control": control,
           "base": {g: rounded(m) for g, m in base.items()},
           "base_mean_mrr5": round(base_mean, 4) if base_mean is not None else None,
           "arms": {}, "chosen": chosen, "why": why,
           "rule": "acceptable = all three legs, mean top:5 MRR >= base mean - %.2f, every leg >= its "
                   "base - %.2f, L speed-up vs %s >= %.1f; chosen = acceptable variant with the lowest "
                   "ms per pair over all legs, else %s" % (MEAN_TOL, LEG_TOL, control, MIN_SPEEDUP, control)}
    for arm, e in arms.items():
        o = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in e.items() if k != "legs"}
        o["legs"] = {g: rounded(m) for g, m in e["legs"].items()}
        out["arms"][arm] = o
    return out


def decide(arms, base_mean, control):
    why = {}
    ok = []
    for arm, e in sorted(arms.items()):
        if arm == control:
            continue
        reasons = []
        if not e["complete"] or base_mean is None:
            reasons.append("not all three legs")
        else:
            if e["mean_mrr5"] < base_mean - MEAN_TOL - EPS:
                reasons.append("mean MRR %.4f < %.4f" % (e["mean_mrr5"], base_mean - MEAN_TOL))
            for g in LEGS:
                if e["legs"][g]["d_mrr5"] < -LEG_TOL - EPS:
                    reasons.append("%s MRR fell %.4f" % (g, -e["legs"][g]["d_mrr5"]))
        if e.get("speedup_l") is None or e["speedup_l"] < MIN_SPEEDUP:
            reasons.append("L speed-up %s < %.1f" % (e.get("speedup_l"), MIN_SPEEDUP))
        why[arm] = reasons or ["acceptable"]
        if not reasons:
            ok.append(arm)
    if not ok:
        return control, why
    return min(ok, key=lambda a: (arms[a]["ms_per_pair_all"], a)), why


def parse_leg(spec):
    name, base, gold = spec.split("=", 2)
    return name, (base, gold)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--leg", action="append", required=True)
    ap.add_argument("--control", default="fp32_512")
    a = ap.parse_args(argv)
    t = build(a.arms_dir, dict(parse_leg(s) for s in a.leg), a.control)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(t, f, indent=1)
    print(json.dumps(t, indent=1))
    return 0 if t["arms"] else 1


if __name__ == "__main__":
    sys.exit(main())
