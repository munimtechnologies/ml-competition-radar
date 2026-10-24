"""Checks for the SPARK Task 1 system: does it reproduce an earlier ranking, and does a resumed
run write the same submission files?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

  rank: compare the first k items per question of two ranked.jsonl files (spark_t1.py's against
        rerank_run.py's from an earlier job); writes counts and question ids only, never text.
  snap: sha256 of every submission_*.jsonl in a folder, saved to a JSON file.
  same: exit 0 if the folder's submission files still match a snap, else 1.
Standard library only.

  python agree.py rank --a F --b F --out F [--k 5]
  python agree.py snap --dir D --out F
  python agree.py same --dir D --snap F
"""
import argparse
import hashlib
import json
import os
import sys

VERSION = "0.1.0"


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def first_k(row, k):
    return [str(c[0]) for c in row["candidates"][:k]]


def rank(a_rows, b_rows, k=5):
    a = {r["info_need_id"]: first_k(r, k) for r in a_rows}
    b = {r["info_need_id"]: first_k(r, k) for r in b_rows}
    common = [i for i in a if i in b]
    return {"version": VERSION, "k": k, "common": len(common),
            "only_a": len(a) - len(common), "only_b": len(b) - len(common),
            "same_order": sum(1 for i in common if a[i] == b[i]),
            "same_set": sum(1 for i in common if set(a[i]) == set(b[i])),
            "same_first": sum(1 for i in common if a[i][:1] == b[i][:1]),
            "differ_ids": sorted(str(i) for i in common if a[i] != b[i])[:50]}


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def snap(folder):
    return {n: sha256_of(os.path.join(folder, n))
            for n in sorted(os.listdir(folder)) if n.startswith("submission_") and n.endswith(".jsonl")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rank")
    r.add_argument("--a", required=True)
    r.add_argument("--b", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--k", type=int, default=5)
    s = sub.add_parser("snap")
    s.add_argument("--dir", required=True)
    s.add_argument("--out", required=True)
    m = sub.add_parser("same")
    m.add_argument("--dir", required=True)
    m.add_argument("--snap", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "same":
        with open(a.snap, encoding="utf-8") as f:
            before = json.load(f)
        now = snap(a.dir)
        res = {"same": bool(before) and now == before, "before": before, "now": now}
        print(json.dumps(res, indent=1))
        return 0 if res["same"] else 1
    res = rank(load_jsonl(a.a), load_jsonl(a.b), a.k) if a.cmd == "rank" else snap(a.dir)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    return 0 if (res["common"] if a.cmd == "rank" else res) else 1


if __name__ == "__main__":
    sys.exit(main())
