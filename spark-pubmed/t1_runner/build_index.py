"""Resumable whole-corpus SQLite FTS5 (BM25) index of the NLM SPARK PubMed corpus.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Indexes every md5-verified file of a local mirror (fetch_corpus.py marks them with .md5ok) into
one on-disk FTS5 table (title, abstract, MeSH; porter + unicode61; rowid = PMID) plus a meta
table (year, journal, PMC id). Each corpus file goes in one transaction together with its row in
the `built` table, under a WAL journal, so a job killed at any point resumes at the first file
not yet committed. A PMID seen again in a later file replaces the earlier record (PubMed's
later files carry newer versions). A time budget and a free-disk guard stop the build cleanly
between files; a later run continues it. Python standard library only. Writes build.json.

0.3: every committed file is appended (and fsynced) to progress.jsonl in the output folder, so
a host kill still leaves a record; SIGTERM rolls back the file in progress and writes
build.json with `stopped` = "signal 15" (job spark32-build-v1 was killed with no record).
"""
import argparse
import gzip
import json
import os
import re
import shutil
import signal
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET

VERSION = "0.3"
NAME_RX = re.compile(r"pubmed27n\d{4}\.xml\.gz")
TOKEN_RX = re.compile(r"[a-z0-9]+")
STOP = frozenset("a an and are as at be by for from has have in is it of on or that the this to "
                 "was were which with we our these those their its not but than into".split())
WEIGHTS = (2.0, 1.0, 0.5)  # bm25 column weights: title, abstract, MeSH (as in fts_pilot.py)
MAX_TERMS = 32


class Stopped(Exception):
    """Raised by the signal handler; the open file's transaction rolls back."""


def on_signal(signum, frame):
    raise Stopped("signal %d" % signum)


def text_of(elem):
    return " ".join("".join(elem.itertext()).split()) if elem is not None else ""


def year_of(article):
    pub = article.find("Journal/JournalIssue/PubDate")
    if pub is None:
        return None
    y = pub.findtext("Year")
    if not y:
        m = re.search(r"\d{4}", pub.findtext("MedlineDate") or "")
        y = m.group(0) if m else None
    return int(y) if y and y.isdigit() else None


def parse_article(el):
    cit = el.find("MedlineCitation")
    art = cit.find("Article")
    parts = []
    for ab in art.findall("Abstract/AbstractText"):
        label, body = ab.get("Label"), text_of(ab)
        if body:
            parts.append("%s: %s" % (label, body) if label else body)
    pmcid = None
    for aid in el.findall("PubmedData/ArticleIdList/ArticleId"):
        if aid.get("IdType") == "pmc":
            pmcid = (aid.text or "").strip() or None
    return (int(cit.findtext("PMID")), text_of(art.find("ArticleTitle")), " ".join(parts),
            "; ".join(text_of(d) for d in cit.findall("MeshHeadingList/MeshHeading/DescriptorName")),
            year_of(art), art.findtext("Journal/ISOAbbreviation") or "", pmcid)


def parse_file(path):
    """Yield (pmid, title, abstract, mesh, year, journal, pmcid) per PubmedArticle."""
    with gzip.open(path, "rb") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == "PubmedArticle":
                yield parse_article(el)
                el.clear()


def open_db(path, detail):
    """Open (or create) the index. An existing index keeps the detail level it was built with."""
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    row = con.execute("SELECT value FROM settings WHERE key='detail'").fetchone()
    if row and row[0] != detail:
        con.close()
        raise ValueError("index at %s was built with detail=%s, not %s" % (path, row[0], detail))
    with con:
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(title, abstract, mesh, "
                    "tokenize='porter unicode61 remove_diacritics 2', detail=%s)" % detail)
        con.execute("CREATE TABLE IF NOT EXISTS meta (pmid INTEGER PRIMARY KEY, year INTEGER, "
                    "journal TEXT, pmcid TEXT, file TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS built (file TEXT PRIMARY KEY, docs INTEGER, "
                    "replaced INTEGER, seconds REAL, finished_utc TEXT)")
        con.execute("INSERT OR IGNORE INTO settings VALUES ('detail', ?)", (detail,))
    return con


def add_file(con, path, name):
    """Index one file and mark it built, all in one transaction. Returns (docs, replaced)."""
    n = replaced = 0
    t0 = time.time()
    with con:
        for pmid, title, abstract, mesh, year, journal, pmcid in parse_file(path):
            if con.execute("SELECT 1 FROM meta WHERE pmid=?", (pmid,)).fetchone():
                con.execute("DELETE FROM docs WHERE rowid=?", (pmid,))
                con.execute("DELETE FROM meta WHERE pmid=?", (pmid,))
                replaced += 1
            con.execute("INSERT INTO meta VALUES (?,?,?,?,?)", (pmid, year, journal, pmcid, name))
            con.execute("INSERT INTO docs(rowid, title, abstract, mesh) VALUES (?,?,?,?)",
                        (pmid, title, abstract, mesh))
            n += 1
        con.execute("INSERT INTO built VALUES (?,?,?,?,?)",
                    (name, n, replaced, round(time.time() - t0, 1),
                     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    return n, replaced


def log_progress(f, row):
    f.write(json.dumps(row) + "\n")
    f.flush()
    os.fsync(f.fileno())


def match_expr(text):
    seen, toks = set(), []
    for t in TOKEN_RX.findall(text.lower()):
        if len(t) > 1 and t not in STOP and t not in seen:
            seen.add(t)
            toks.append(t)
    return " OR ".join('"%s"' % t for t in toks[:MAX_TERMS])


def search(con, text, k=5):
    """Top-k PMIDs for free text by BM25 (title x2, abstract x1, MeSH x0.5)."""
    q = match_expr(text)
    if not q:
        return []
    rows = con.execute("SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY bm25(docs, ?, ?, ?) LIMIT ?",
                       (q,) + WEIGHTS + (k,)).fetchall()
    return [r[0] for r in rows]


def free_gb(path):
    return shutil.disk_usage(path).free / 1e9


def size_of(path):
    return os.path.getsize(path) if os.path.exists(path) else 0


def run(raw_dir, db_path, out_dir, detail="full", max_files=0, max_minutes=0, min_free_gb=0.0,
        optimize=False, clock=time.time, adder=add_file):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(raw_dir)
                   if NAME_RX.fullmatch(n) and os.path.exists(os.path.join(raw_dir, n + ".md5ok")))
    con = open_db(db_path, detail)
    done = {r[0] for r in con.execute("SELECT file FROM built")}
    todo = [n for n in names if n not in done]
    start, added, stopped = clock(), [], None
    with open(os.path.join(out_dir, "progress.jsonl"), "a", encoding="utf-8") as prog:
        try:
            for name in todo:
                if max_files and len(added) >= max_files:
                    stopped = "max_files"
                    break
                if max_minutes and clock() - start >= 60 * max_minutes:
                    stopped = "time budget"
                    break
                if min_free_gb and free_gb(os.path.dirname(os.path.abspath(db_path))) < min_free_gb:
                    stopped = "free disk under %.0f GB" % min_free_gb
                    break
                n, rep = adder(con, os.path.join(raw_dir, name), name)
                added.append({"file": name, "docs": n, "replaced": rep})
                log_progress(prog, {"file": name, "docs": n, "replaced": rep,
                                    "elapsed": round(clock() - start, 1),
                                    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
                if len(added) % 25 == 0:
                    print("built %d/%d files this run" % (len(added), len(todo)), flush=True)
        except Stopped as e:
            stopped = str(e)
    done = {r[0] for r in con.execute("SELECT file FROM built")}
    left = sum(1 for n in names if n not in done)  # from the db: a signal can land after a commit
    opt_seconds = docs_check = None
    if stopped is None or not stopped.startswith("signal"):  # a signalled run skips slow steps
        if optimize and left == 0 and names:
            t0 = clock()
            con.execute("INSERT INTO docs(docs) VALUES('optimize')")
            con.commit()
            opt_seconds = round(clock() - t0, 1)
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        docs_check = con.execute("SELECT COUNT(*) FROM meta").fetchone()[0]
    files_built, docs, replaced = con.execute(
        "SELECT COUNT(*), COALESCE(SUM(docs), 0) - COALESCE(SUM(replaced), 0), "
        "COALESCE(SUM(replaced), 0) FROM built").fetchone()
    con.close()
    secs = round(clock() - start, 1)
    new_docs = sum(a["docs"] for a in added)
    db_bytes, wal_bytes = size_of(db_path), size_of(db_path + "-wal")
    summary = {"version": VERSION, "detail": detail, "verified_files": len(names),
               "files_built": files_built, "files_added_this_run": len(added), "files_left": left,
               "last_file": added[-1]["file"] if added else None, "stopped": stopped,
               "docs": docs, "docs_check": docs_check, "replaced_total": replaced, "seconds": secs,
               "docs_per_second_this_run": round(new_docs / secs, 1) if secs and new_docs else None,
               "db_bytes": db_bytes, "wal_bytes": wal_bytes,
               "bytes_per_doc": round((db_bytes + wal_bytes) / docs, 1) if docs else None,
               "free_gb_after": round(free_gb(os.path.dirname(os.path.abspath(db_path))), 1),
               "optimize_seconds": opt_seconds, "complete": left == 0 and bool(names),
               "problem": None if names else "no verified corpus files under %s" % raw_dir}
    with open(os.path.join(out_dir, "build.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--detail", choices=("full", "column", "none"), default="full")
    ap.add_argument("--max-files", type=int, default=0)
    ap.add_argument("--max-minutes", type=float, default=0)
    ap.add_argument("--min-free-gb", type=float, default=0)
    ap.add_argument("--optimize", action="store_true")
    args = ap.parse_args(argv)
    signal.signal(signal.SIGTERM, on_signal)
    s = run(args.raw_dir, args.db, args.out_dir, args.detail, args.max_files, args.max_minutes,
            args.min_free_gb, args.optimize)
    print(json.dumps(s, indent=1))
    return 1 if s["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
