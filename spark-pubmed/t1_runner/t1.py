"""SPARK Task 1 runner: questions -> BM25 candidates -> cutoff -> submission JSONL, plus scoring.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Stage 1 of the Task 1 plan: BM25 over the FTS5 index that build_index.py writes (title x2,
abstract x1, MeSH x0.5). A reranker and a priority prior plug in later between `candidates`
and `cut`. The task penalises incorrect citations, so how many of the five allowed items to
return is a policy: "top:k" keeps the first k, "ratio:r" keeps every item scoring at least r
times the best one (always at least one, never more than five). `score` reports MRR@5, hits,
items returned and wrong citations for every policy, so the cutoff is chosen on dev data.
Python standard library only.

Commands:
  devsets  --r-questions F [--r-titles F] [--landmarks F] --out-dir D   dev needs + gold files
  run      --db DB --needs F --out-dir D [--depth 20] [--policy top:5]  ranked + submission files
  score    --ranked F --gold F --out-dir D                              scores.json, every policy
  validate FILE                                                        submission format check
"""
import argparse
import json
import os
import re
import sqlite3
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index  # noqa: E402

MAX_ITEMS = 5
ID_RX = re.compile(r"(PMC)?[1-9][0-9]{0,9}")
META_KEYS = ("team_id", "submission_id", "info_need_id", "info_need")
POLICIES = ("top:1", "top:2", "top:3", "top:4", "top:5",
            "ratio:0.5", "ratio:0.6", "ratio:0.7", "ratio:0.8", "ratio:0.9")
DEPTHS = (1, 5, 10, 20, 50, 100)
L_OVERRIDES = {"L37": "8458085"}  # hand-verified in run 172 (dev_sets/RESULTS.md)


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def headline_l(items, overrides=L_OVERRIDES):
    """Headline L (dev_sets PREREGISTRATION.md): verified, in window, not contested, not a
    control, no excluded publication type; plus hand-verified overrides. Returns (needs, gold)."""
    needs, gold = [], []
    for it in items:
        pmid = None
        if it["id"] in overrides:
            pmid = overrides[it["id"]]
        elif (it.get("status") == "verified" and it.get("in_window") and not it.get("contested")
              and not it.get("control") and not it.get("excluded_types")):
            pmid = it["pmid"]
        if pmid:
            needs.append({"info_need_id": it["id"], "info_need": it["question"]})
            gold.append({"info_need_id": it["id"], "gold": [str(pmid)]})
    return needs, gold


def devsets(r_questions, out_dir, r_titles=None, landmarks=None):
    """Write needs_r.jsonl (+ needs_rt.jsonl, needs_l.jsonl) and one gold.jsonl for all sets."""
    os.makedirs(out_dir, exist_ok=True)
    counts, gold = {}, []
    sets = [("r", "R-", r_questions, "question")]
    if r_titles:
        sets.append(("rt", "RT-", r_titles, "title"))
    for key, prefix, path, field in sets:
        rows = load_jsonl(path)
        write_jsonl(os.path.join(out_dir, "needs_%s.jsonl" % key),
                    [{"info_need_id": "%s%s" % (prefix, r["pmid"]), "info_need": r[field]} for r in rows])
        gold += [{"info_need_id": "%s%s" % (prefix, r["pmid"]), "gold": [str(r["pmid"])]} for r in rows]
        counts[key] = len(rows)
    if landmarks:
        with open(landmarks, encoding="utf-8") as f:
            items = json.load(f)
        needs, g = headline_l(items)
        write_jsonl(os.path.join(out_dir, "needs_l.jsonl"), needs)
        gold += g
        counts["l"] = len(needs)
    write_jsonl(os.path.join(out_dir, "gold.jsonl"), gold)
    ids = [g["info_need_id"] for g in gold]
    counts["duplicate_ids"] = sorted({i for i in ids if ids.count(i) > 1})
    return counts


def candidates(con, text, depth=20):
    """Top-depth (pmid, score) by BM25; score = -bm25(), so higher is better."""
    q = build_index.match_expr(text)
    if not q:
        return []
    rows = con.execute("SELECT rowid, bm25(docs, ?, ?, ?) FROM docs WHERE docs MATCH ? ORDER BY 2 LIMIT ?",
                       build_index.WEIGHTS + (q, depth)).fetchall()
    return [(int(pmid), round(-s, 6)) for pmid, s in rows]


def parse_policy(policy):
    kind, _, value = policy.partition(":")
    try:
        x = float(value)
    except ValueError:
        raise ValueError("bad policy %r" % policy)
    if kind == "top" and x == int(x) and 1 <= x <= MAX_ITEMS:
        return kind, int(x)
    if kind == "ratio" and 0 <= x <= 1:
        return kind, x
    raise ValueError("bad policy %r" % policy)


def cut(cands, policy):
    """PMIDs to return for one need under a policy (cands sorted best first)."""
    kind, x = parse_policy(policy)
    top = cands[:MAX_ITEMS]
    if not top:
        return []
    if kind == "top":
        return [p for p, _ in top[:x]]
    best = top[0][1]
    return [top[0][0]] + [p for p, s in top[1:] if s >= x * best]


def submission_rows(ranked, policy, team_id, submission_id):
    return [{"metadata": {"team_id": team_id, "submission_id": submission_id,
                          "info_need_id": r["info_need_id"], "info_need": r["info_need"]},
             "response": [str(p) for p in cut(r["candidates"], policy)]} for r in ranked]


def validate(path):
    """Problems with a Task 1 submission file (empty list = valid); empty responses are counted."""
    problems, seen, lines, empty = [], set(), 0, 0
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            lines += 1
            try:
                row = json.loads(line)
            except ValueError:
                problems.append("line %d: not JSON" % n)
                continue
            meta, resp = row.get("metadata"), row.get("response")
            if not isinstance(meta, dict) or any(k not in meta for k in META_KEYS):
                problems.append("line %d: metadata needs %s" % (n, ", ".join(META_KEYS)))
                continue
            if meta["info_need_id"] in seen:
                problems.append("line %d: info_need_id %s repeated" % (n, meta["info_need_id"]))
            seen.add(meta["info_need_id"])
            if not isinstance(resp, list):
                problems.append("line %d: response is not a list" % n)
                continue
            if len(resp) > MAX_ITEMS:
                problems.append("line %d: %d items > %d" % (n, len(resp), MAX_ITEMS))
            if len(set(map(str, resp))) != len(resp):
                problems.append("line %d: repeated item" % n)
            bad = [i for i in resp if not isinstance(i, str) or not ID_RX.fullmatch(i)]
            if bad:
                problems.append("line %d: bad ids %s" % (n, bad))
            empty += not resp
    return {"lines": lines, "empty_responses": empty, "problems": problems}


def run(db, needs_path, out_dir, depth=20, policy="top:5", team_id="TEAM", submission_id="dev",
        gold_path=None):
    """Retrieve for every need; write ranked.jsonl, submission.jsonl and run.json."""
    parse_policy(policy)
    os.makedirs(out_dir, exist_ok=True)
    needs = load_jsonl(needs_path)
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    con = sqlite3.connect(db)
    ranked, ms = [], []
    for nd in needs:
        t0 = time.perf_counter()
        c = candidates(con, nd["info_need"], depth)
        ms.append((time.perf_counter() - t0) * 1000)
        ranked.append({"info_need_id": nd["info_need_id"], "info_need": nd["info_need"],
                       "candidates": c, "depth": depth, "ms": round(ms[-1], 1)})
    missing = None
    if gold_path:
        golds = sorted({p for g in load_jsonl(gold_path) for p in g["gold"] if p.isdigit()}, key=int)
        missing = [p for p in golds
                   if not con.execute("SELECT 1 FROM meta WHERE pmid=?", (int(p),)).fetchone()]
    docs = con.execute("SELECT COUNT(*) FROM meta").fetchone()[0]
    con.close()
    write_jsonl(os.path.join(out_dir, "ranked.jsonl"), ranked)
    sub = os.path.join(out_dir, "submission.jsonl")
    write_jsonl(sub, submission_rows(ranked, policy, team_id, submission_id))
    srt = sorted(ms)
    summary = {"needs": len(needs), "index_docs": docs, "depth": depth, "policy": policy,
               "no_candidates": sum(1 for r in ranked if not r["candidates"]),
               "median_ms": round(statistics.median(srt), 1) if srt else None,
               "p95_ms": round(srt[min(len(srt) - 1, int(0.95 * len(srt)))], 1) if srt else None,
               "gold_missing_from_index": missing, "validate": validate(sub)}
    with open(os.path.join(out_dir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def score(ranked, gold, policies=POLICIES, depths=DEPTHS):
    """MRR@5, hit share, mean items returned and mean wrong citations per policy, plus recall
    of the gold item within the first d candidates (what a reranker could still reach)."""
    by = {g["info_need_id"]: set(g["gold"]) for g in gold}
    rows = [r for r in ranked if r["info_need_id"] in by]
    n = len(rows)
    out = {"needs": n, "no_gold": [r["info_need_id"] for r in ranked if r["info_need_id"] not in by],
           "recall_at": {}, "policies": {}}
    if not n:
        return out
    max_depth = max(r.get("depth", len(r["candidates"])) for r in rows)
    for d in depths:
        if d <= max(max_depth, 1):
            out["recall_at"][str(d)] = round(sum(
                1 for r in rows if by[r["info_need_id"]] & {str(p) for p, _ in r["candidates"][:d]}) / n, 4)
    for pol in policies:
        rr = hits = returned = wrong = 0
        for r in rows:
            kept = [str(p) for p in cut(r["candidates"], pol)]
            good = by[r["info_need_id"]]
            ranks = [i for i, p in enumerate(kept, 1) if p in good]
            rr += 1.0 / ranks[0] if ranks else 0.0
            hits += bool(ranks)
            returned += len(kept)
            wrong += sum(1 for p in kept if p not in good)
        out["policies"][pol] = {"mrr": round(rr / n, 4), "hit": round(hits / n, 4),
                                "mean_returned": round(returned / n, 3), "mean_wrong": round(wrong / n, 3)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("devsets")
    d.add_argument("--r-questions", required=True)
    d.add_argument("--r-titles")
    d.add_argument("--landmarks")
    d.add_argument("--out-dir", required=True)
    r = sub.add_parser("run")
    r.add_argument("--db", required=True)
    r.add_argument("--needs", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--depth", type=int, default=20)
    r.add_argument("--policy", default="top:5")
    r.add_argument("--team-id", default="TEAM")
    r.add_argument("--submission-id", default="dev")
    r.add_argument("--gold")
    s = sub.add_parser("score")
    s.add_argument("--ranked", required=True)
    s.add_argument("--gold", required=True)
    s.add_argument("--out-dir", required=True)
    v = sub.add_parser("validate")
    v.add_argument("file")
    a = ap.parse_args(argv)
    if a.cmd == "devsets":
        res = devsets(a.r_questions, a.out_dir, a.r_titles, a.landmarks)
        bad = bool(res["duplicate_ids"])
    elif a.cmd == "run":
        res = run(a.db, a.needs, a.out_dir, a.depth, a.policy, a.team_id, a.submission_id, a.gold)
        bad = bool(res["validate"]["problems"])
    elif a.cmd == "score":
        res = score(load_jsonl(a.ranked), load_jsonl(a.gold))
        os.makedirs(a.out_dir, exist_ok=True)
        with open(os.path.join(a.out_dir, "scores.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
        bad = not res["needs"]
    else:
        res = validate(a.file)
        bad = bool(res["problems"])
    print(json.dumps(res, indent=1)[:6000])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
