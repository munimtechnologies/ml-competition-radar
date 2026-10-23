"""Stop a continued index build unless the data volume holds the partial index it continues.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

The `pubmed-baseline` data volume exists separately on each machine that runs compute jobs, and a
job cannot choose its machine. Job spark33-build-v1 built 830 of 1,306 files into the copy on one
machine; on the other, the same job would start a second index from almost nothing. This check
reads the `built` table of the index (never creates one) and exits 3 unless at least
--min-built files and --min-docs records are already there, so the build step never starts on
the wrong volume. Writes guard.json. Python standard library only.
"""
import argparse
import json
import os
import sqlite3
import sys

VERSION = "0.1"


def check(db, min_built, min_docs):
    rec = {"version": VERSION, "db": db, "db_exists": os.path.exists(db), "db_bytes": None,
           "files_built": None, "docs": None, "last_file": None, "min_built": min_built,
           "min_docs": min_docs, "ok": False, "problem": None}
    if not rec["db_exists"]:
        rec["problem"] = "no index at %s" % db
        return rec
    rec["db_bytes"] = os.path.getsize(db)
    try:
        con = sqlite3.connect(db, timeout=30)
        try:
            rec["files_built"], rec["docs"], rec["last_file"] = con.execute(
                "SELECT COUNT(*), COALESCE(SUM(docs), 0) - COALESCE(SUM(replaced), 0), MAX(file) "
                "FROM built").fetchone()
        finally:
            con.close()
    except sqlite3.Error as e:
        rec["problem"] = "%s: %s" % (type(e).__name__, e)
        return rec
    rec["ok"] = rec["files_built"] >= min_built and rec["docs"] >= min_docs
    if not rec["ok"]:
        rec["problem"] = "index holds %d files and %d records, below %d and %d" % (
            rec["files_built"], rec["docs"], min_built, min_docs)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--min-built", type=int, required=True)
    ap.add_argument("--min-docs", type=int, default=0)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    rec = check(a.db, a.min_built, a.min_docs)
    with open(os.path.join(a.out_dir, "guard.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    return 0 if rec["ok"] else 3


if __name__ == "__main__":
    sys.exit(main())
