"""Compare two compose.py score files made on the same BioGen 2024 dev questions (SPARK Task 2).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

compose.py `score` gives each answer's citation shares by judged class and its Supports recall.
Most citations are unjudged (BioGen's pool came from 2024 runs), so the judged pool alone cannot
rank systems (RESULTS-t2dev.md). For each file this reports judged precision, (Supports + mixed)
/ judged from the mean shares exactly as RESULTS-t2dev.md computes it, the judged citations, the
answers with no judged citation, and the means; then, over the topics in both files, how many
topics are higher, lower or level in A than in B on Supports share, unjudged share, Supports
recall and per-topic judged precision (topics judged in both). Standard library only.

  python compare.py --a SCORES --b SCORES --out F
"""
import argparse
import json
import os
import sys

VERSION = "0.1.0"
PAIRED = ("supports_share", "unjudged_share", "supports_recall")
MEANS = ("mean_supports_share", "mean_mixed_share", "mean_contradicts_share", "mean_other_share",
         "mean_unjudged_share", "mean_supports_recall", "mean_supports_only_recall")
EPS = 1e-9


def judged_precision(s):
    """(mean Supports share + mean mixed share) / (1 - mean unjudged share), 4 decimals."""
    judged = 1 - s["mean_unjudged_share"]
    if judged <= EPS:
        return None
    return round((s["mean_supports_share"] + s["mean_mixed_share"]) / judged, 4)


def judged_count(p):
    return round(p["citations"] * (1 - p["unjudged_share"]))


def topic_precision(p):
    judged = 1 - p["unjudged_share"]
    if not p["citations"] or judged <= EPS:
        return None
    return (p["supports_share"] + p["mixed_share"]) / judged


def summary(s):
    per = s["per_topic"]
    out = {"answers": s["answers_scored"], "judged_precision": judged_precision(s),
           "citations": sum(p["citations"] for p in per),
           "judged_citations": sum(judged_count(p) for p in per),
           "answers_without_judged": sum(1 for p in per if judged_count(p) == 0),
           "topics_with_mixed_found": s.get("topics_with_mixed_found")}
    out.update({k: s.get(k) for k in MEANS})
    return out


def updown(pairs):
    out = {"a_higher": 0, "a_lower": 0, "equal": 0}
    for x, y in pairs:
        if x is None or y is None:
            continue
        if abs(x - y) < EPS:
            out["equal"] += 1
        elif x > y:
            out["a_higher"] += 1
        else:
            out["a_lower"] += 1
    return out


def paired(a, b):
    """Per topic present in both files: is A higher, lower or level than B."""
    pa = {str(p["topic"]): p for p in a["per_topic"]}
    pb = {str(p["topic"]): p for p in b["per_topic"]}
    common = sorted(set(pa) & set(pb))
    out = {"topics": len(common)}
    for k in PAIRED:
        out[k] = updown([(pa[t][k], pb[t][k]) for t in common])
    prec = [(topic_precision(pa[t]), topic_precision(pb[t])) for t in common]
    out["topics_judged_in_both"] = sum(1 for x, y in prec if x is not None and y is not None)
    out["judged_precision"] = updown(prec)
    return out


def compare(a, b):
    return {"version": VERSION, "a": summary(a), "b": summary(b), "paired": paired(a, b)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    with open(args.a, encoding="utf-8") as f:
        a = json.load(f)
    with open(args.b, encoding="utf-8") as f:
        b = json.load(f)
    res = compare(a, b)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    return 0 if res["paired"]["topics"] else 1


if __name__ == "__main__":
    sys.exit(main())
