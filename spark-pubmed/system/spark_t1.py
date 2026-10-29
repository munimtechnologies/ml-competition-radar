"""SPARK Task 1 system: the whole pipeline as one no-network command, questions in, submission
files out.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

This is the entry point the challenge's Docker image runs (Dockerfile in this folder). Per
question: BM25 over the FTS5 index for the first --depth candidates (t1.candidates), then the
MedCPT cross-encoder over (question, title + abstract) of the first --rerank-depth of them
(rerank_run.rerank_need), then one submission file per cut-off policy (t1.submission_rows; the
current plan is submission 1 = top:5, submission 2 = top:1), each checked with t1.validate.

Every answered question is appended to ranked.jsonl at once (flushed and fsynced) with the time
each stage took, so a stopped run resumes at the first unanswered question and every question's
compute time stays on record (compute time is one of the challenge's tie-breakers). Rows of an
earlier run are reused only if the question text, the depths and the scorer are the same; a torn
last line is dropped. Submission files are written only once every question is answered.

Questions: JSONL, one object per line with info_need_id and info_need at the top level or under
"metadata" (the submission format), or one JSON list of such objects; other keys are ignored.
The model loads from a local folder with HF_HUB_OFFLINE and TRANSFORMERS_OFFLINE set, and
nothing here opens a network connection. Standard library only, except --scorer medcpt
(rerank.py: torch + transformers), imported only when used, so the tests need neither.

0.1.1: the default depth is 150, the depth spark40-depth-v1's pre-registered rule chose
(rerank/RESULTS-spark40.md); 0.1.0 defaulted to 50.
0.2.0: --immutable opens the index with ro_db.connect(immutable=True) (mode=ro&immutable=1), so
the WAL-mode index can sit on a read-only mount with no -shm or -wal files (RESULTS-rodb1.md).
Without the flag the index is opened as before. Rankings do not depend on the flag.

  python spark_t1.py --db DB --questions F --out-dir D [--scorer medcpt --model-dir M | --scorer none]
         [--depth 150] [--rerank-depth N] [--policies top:5,top:1] [--submission-ids 1,2]
         [--team-id TEAM] [--max-minutes 0] [--threads 2] [--batch 8] [--immutable]
Exit 0 = complete and valid, 1 = a submission file failed validation, 4 = stopped by
--max-minutes (run the same command again to continue).
"""
import argparse
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# Flat in the Docker image; in the repository t1.py and rerank_run.py sit in sibling folders.
sys.path[:0] = [d for d in (HERE, os.path.join(HERE, "..", "t1_runner"), os.path.join(HERE, "..", "rerank"))
                if os.path.isdir(d)]
import rerank_run  # noqa: E402
import ro_db  # noqa: E402
import t1  # noqa: E402

VERSION = "0.2.0"
DEPTH = 150  # chosen by spark40-depth-v1's pre-registered rule (best mean top:5 MRR of the eligible depths)
POLICIES = ("top:5", "top:1")
STOPPED = 4


def need_of(obj):
    """{info_need_id, info_need} of one question object; the id is kept as given (str or int)."""
    src = obj.get("metadata") if isinstance(obj, dict) and isinstance(obj.get("metadata"), dict) else obj
    if not isinstance(src, dict):
        raise ValueError("question is not an object: %s" % json.dumps(obj)[:200])
    nid, text = src.get("info_need_id"), src.get("info_need")
    if isinstance(nid, bool) or not isinstance(nid, (str, int)) or not isinstance(text, str):
        raise ValueError("question needs info_need_id and info_need: %s" % json.dumps(obj)[:200])
    return {"info_need_id": nid, "info_need": text}


def read_questions(path):
    with open(path, encoding="utf-8-sig") as f:
        text = f.read().strip()
    objs = json.loads(text) if text.startswith("[") else [json.loads(x) for x in text.splitlines() if x.strip()]
    needs, seen = [], set()
    for o in objs:
        nd = need_of(o)
        if nd["info_need_id"] in seen:
            raise ValueError("info_need_id %s repeated" % nd["info_need_id"])
        seen.add(nd["info_need_id"])
        needs.append(nd)
    return needs


def load_done(path, needs, settings):
    """Rows of an earlier run that answer the same question text with the same settings."""
    want = {nd["info_need_id"]: nd["info_need"] for nd in needs}
    done = {}
    if not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue  # a torn last line from a stopped run
            nid = row.get("info_need_id") if isinstance(row, dict) else None
            if (isinstance(nid, (str, int)) and nid in want and nid not in done
                    and want[nid] == row.get("info_need")
                    and all(row.get(k) == v for k, v in settings.items())):
                done[nid] = row
    return done


def answer(con, need, depth, rerank_depth=0, scorer=None, scorer_name="none", clock=time.perf_counter):
    """One question through both stages; the row rerank_run writes plus the time of each stage."""
    t0 = clock()
    cands = t1.candidates(con, need["info_need"], depth)
    t_bm25 = clock()
    row = {"info_need_id": need["info_need_id"], "info_need": need["info_need"],
           "candidates": [[p, s] for p, s in cands], "depth": depth}
    if scorer is not None:
        row, _, _ = rerank_run.rerank_need(con, scorer, row, rerank_depth)
    t_end = clock()
    row.update({"depth": depth, "rerank_depth": rerank_depth if scorer is not None else 0,
                "scorer": scorer_name, "bm25_ms": round(1000 * (t_bm25 - t0), 1),
                "rerank_ms": round(1000 * (t_end - t_bm25), 1), "total_ms": round(1000 * (t_end - t0), 1)})
    return row


def ms_stats(values):
    v = sorted(values)
    if not v:
        return None
    return {"median": round(statistics.median(v), 1), "p95": v[min(len(v) - 1, int(0.95 * len(v)))],
            "max": v[-1], "total_seconds": round(sum(v) / 1000, 1)}


def write_row(f, row):
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
    f.flush()
    os.fsync(f.fileno())


def run(db, questions_path, out_dir, scorer=None, scorer_name="none", depth=DEPTH, rerank_depth=None,
        policies=POLICIES, submission_ids=None, team_id="TEAM", max_minutes=0, clock=time.perf_counter,
        immutable=False):
    """Answer every question (resuming), then write and validate one submission per policy."""
    for p in policies:
        t1.parse_policy(p)
    submission_ids = list(submission_ids or [str(i) for i in range(1, len(policies) + 1)])
    if len(submission_ids) != len(policies):
        raise ValueError("one submission id per policy")
    rerank_depth = 0 if scorer is None else (depth if rerank_depth is None else rerank_depth)
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    needs = read_questions(questions_path)
    os.makedirs(out_dir, exist_ok=True)
    ranked_path = os.path.join(out_dir, "ranked.jsonl")
    done = load_done(ranked_path, needs, {"depth": depth, "rerank_depth": rerank_depth, "scorer": scorer_name})
    resumed, answered, stopped = len(done), 0, None
    tmp = ranked_path + ".tmp"  # keep the reusable rows, in question order, before appending
    with open(tmp, "w", encoding="utf-8") as f:
        for nd in needs:
            if nd["info_need_id"] in done:
                f.write(json.dumps(done[nd["info_need_id"]], ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, ranked_path)
    start = clock()
    con = ro_db.connect(db, immutable=immutable)  # immutable: ValueError if -wal holds unchecked pages
    try:
        with open(ranked_path, "a", encoding="utf-8") as f:
            for nd in needs:
                if nd["info_need_id"] in done:
                    continue
                if max_minutes and clock() - start >= 60 * max_minutes:
                    stopped = "time budget"
                    break
                row = answer(con, nd, depth, rerank_depth, scorer, scorer_name, clock)
                write_row(f, row)
                done[nd["info_need_id"]] = row
                answered += 1
    finally:
        con.close()
    ranked = [done[nd["info_need_id"]] for nd in needs if nd["info_need_id"] in done]
    complete = len(ranked) == len(needs)
    subs = {}
    if complete:
        for pol, sid in zip(policies, submission_ids):
            path = os.path.join(out_dir, "submission_%s.jsonl" % pol.replace(":", ""))
            t1.write_jsonl(path, t1.submission_rows(ranked, pol, team_id, sid))
            subs[os.path.basename(path)] = {"policy": pol, "submission_id": sid, "validate": t1.validate(path)}
    summary = {"version": VERSION, "questions": len(needs), "answered_this_run": answered, "resumed": resumed,
               "complete": complete, "stopped": stopped, "depth": depth, "rerank_depth": rerank_depth,
               "scorer": scorer_name, "immutable": bool(immutable),
               "no_candidates": sum(1 for r in ranked if not r["candidates"]),
               "ms": {k: ms_stats([r[k + "_ms"] for r in ranked if k + "_ms" in r])
                      for k in ("total", "bm25", "rerank")},
               "submissions": subs,
               "problems": [p for s in subs.values() for p in s["validate"]["problems"]][:50]}
    with open(os.path.join(out_dir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def listing(text):
    return [x.strip() for x in (text or "").split(",") if x.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description="SPARK Task 1 system (MV2 of Munim, Inc.)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--scorer", choices=("medcpt", "none"), default="medcpt")
    ap.add_argument("--model-dir")
    ap.add_argument("--depth", type=int, default=DEPTH)
    ap.add_argument("--rerank-depth", type=int)
    ap.add_argument("--policies", default=",".join(POLICIES))
    ap.add_argument("--submission-ids")
    ap.add_argument("--team-id", default="TEAM")
    ap.add_argument("--max-minutes", type=float, default=0)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--immutable", action="store_true",
                    help="open the index read-only and immutable (for a read-only mount)")
    a = ap.parse_args(argv)
    scorer = None
    if a.scorer == "medcpt":
        if not a.model_dir:
            ap.error("--scorer medcpt needs --model-dir")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        from rerank import CrossEncoder  # torch + transformers; imported here so the tests need neither
        scorer = CrossEncoder(a.model_dir, batch_size=a.batch, threads=a.threads)
    s = run(a.db, a.questions, a.out_dir, scorer, a.scorer, a.depth, a.rerank_depth, listing(a.policies),
            listing(a.submission_ids) or None, a.team_id, a.max_minutes, immutable=a.immutable)
    print(json.dumps(s, indent=1))
    if s["problems"]:
        return 1
    return 0 if s["complete"] else STOPPED


if __name__ == "__main__":
    sys.exit(main())
