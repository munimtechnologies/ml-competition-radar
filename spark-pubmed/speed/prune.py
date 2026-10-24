"""SPARK Task 1 speed fix: leave very common words out of the BM25 query (job spark37-speed-v1).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

On the whole 39,167,523-record index, t1.py's query (every distinct non-stop word of the
question, up to 32, joined by OR) took a median 35.4 s per question on the R dev set
(spark35-score-v2). FTS5 scores every record that matches any of the words, so a word found in
millions of records costs the most time while BM25 gives it almost no weight. This keeps only the
words found in 1 to --max-df records. Each word's record count is probed once per run and capped
(SELECT rowid ... LIMIT max_df + 1), so a common word costs at most max_df + 1 rows to count.
If fewer than --min-terms words survive, the question is queried with all its words, exactly as
t1.py does ("fallback").

Input is a t1.py ranked.jsonl (the BM25 baseline): its info_need text is queried again, and its
candidates and ms are kept to compare against. Output is ranked.jsonl in t1.py's format, so
`t1.py score` applies unchanged, plus run.json with timings, fallbacks and agreement with the
baseline. Tokens, stop words, column weights and the 32-word limit are build_index.py 0.3's.
Standard library only.

  python prune.py --db DB --needs RANKED --out-dir D [--depth 100] [--max-df 400000] [--min-terms 2]
"""
import argparse
import json
import os
import re
import sqlite3
import statistics
import sys
import time

VERSION = "0.1.0"
TOKEN_RX = re.compile(r"[a-z0-9]+")  # as build_index.py 0.3
STOP = frozenset("a an and are as at be by for from has have in is it of on or that the this to "
                 "was were which with we our these those their its not but than into".split())
WEIGHTS = (2.0, 1.0, 0.5)  # bm25 column weights: title, abstract, MeSH
MAX_TERMS = 32


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def tokens(text):
    """The words t1.py queries: distinct, longer than one character, not stop words, first 32."""
    seen, toks = set(), []
    for t in TOKEN_RX.findall(text.lower()):
        if len(t) > 1 and t not in STOP and t not in seen:
            seen.add(t)
            toks.append(t)
    return toks[:MAX_TERMS]


def match_expr(toks):
    return " OR ".join('"%s"' % t for t in toks)


class DocFreq:
    """Records holding a word, counted up to cap + 1 and cached; probe time is summed."""

    def __init__(self, con, cap):
        self.con, self.cap, self.cache, self.seconds = con, cap, {}, 0.0

    def __call__(self, term):
        if term not in self.cache:
            t0 = time.perf_counter()
            self.cache[term] = self.con.execute(
                "SELECT count(*) FROM (SELECT rowid FROM docs WHERE docs MATCH ? LIMIT ?)",
                ('"%s"' % term, self.cap + 1)).fetchone()[0]
            self.seconds += time.perf_counter() - t0
        return self.cache[term]


def prune(toks, df, max_df, min_terms=2):
    """(words to query, fallback): the words found in 1 to max_df records, or every word if
    fewer than min_terms of them are. A word in no record matches nothing, so dropping it is
    lossless."""
    kept = [t for t in toks if 0 < df(t) <= max_df]
    if len(kept) < min_terms:
        return list(toks), True
    return kept, False


def compare(new, base):
    """(same first item, share of the baseline's first five also in the new first five);
    the share is None when the baseline has no candidates."""
    a = [p for p, _ in new[:5]]
    b = [p for p, _ in base[:5]]
    same = bool(a and b and a[0] == b[0])
    return same, (len(set(a) & set(b)) / len(b) if b else None)


def pct(values, q):
    srt = sorted(values)
    return round(srt[min(len(srt) - 1, int(q * len(srt)))], 1) if srt else None


def run(db, needs_path, out_dir, depth=100, max_df=400000, min_terms=2):
    """Query every need with the pruned words; write ranked.jsonl and run.json."""
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    os.makedirs(out_dir, exist_ok=True)
    needs = load_jsonl(needs_path)
    con = sqlite3.connect(db)
    df = DocFreq(con, max_df)
    rows, ms, q_ms, df_ms, base_ms, speedup, same, overlap = [], [], [], [], [], [], [], []
    for nd in needs:
        toks = tokens(nd["info_need"])
        d0, t0 = df.seconds, time.perf_counter()
        kept, fallback = prune(toks, df, max_df, min_terms)
        t1 = time.perf_counter()
        cands = []
        if kept:
            cands = [[int(p), round(-s, 6)] for p, s in con.execute(
                "SELECT rowid, bm25(docs, ?, ?, ?) FROM docs WHERE docs MATCH ? ORDER BY 2 LIMIT ?",
                WEIGHTS + (match_expr(kept), depth)).fetchall()]
        t2 = time.perf_counter()
        ms.append((t2 - t0) * 1000)
        q_ms.append((t2 - t1) * 1000)
        df_ms.append((df.seconds - d0) * 1000)
        rows.append({"info_need_id": nd["info_need_id"], "info_need": nd["info_need"],
                     "candidates": cands, "depth": depth, "ms": round(ms[-1], 1),
                     "query_ms": round(q_ms[-1], 1), "df_ms": round(df_ms[-1], 1),
                     "terms": len(toks), "kept": len(kept), "fallback": fallback})
        base = nd.get("candidates") or []
        if base:
            s, o = compare(cands, base)
            same.append(s)
            overlap.append(o)
        if nd.get("ms"):
            base_ms.append(nd["ms"])
            speedup.append(nd["ms"] / max(ms[-1], 0.001))
    con.close()
    write_jsonl(os.path.join(out_dir, "ranked.jsonl"), rows)
    n = len(rows)
    summary = {"version": VERSION, "needs": n, "depth": depth, "max_df": max_df,
               "min_terms": min_terms,
               "no_candidates": sum(1 for r in rows if not r["candidates"]),
               "fallbacks": sum(1 for r in rows if r["fallback"]),
               "mean_terms": round(sum(r["terms"] for r in rows) / n, 2) if n else None,
               "mean_kept": round(sum(r["kept"] for r in rows) / n, 2) if n else None,
               "median_ms": round(statistics.median(ms), 1) if ms else None,
               "p95_ms": pct(ms, 0.95),
               "median_query_ms": round(statistics.median(q_ms), 1) if q_ms else None,
               "median_df_ms": round(statistics.median(df_ms), 1) if df_ms else None,
               "probed_terms": len(df.cache), "probe_seconds": round(df.seconds, 1),
               "baseline_median_ms": round(statistics.median(base_ms), 1) if base_ms else None,
               "median_speedup": round(statistics.median(speedup), 2) if speedup else None,
               "top1_same": round(sum(same) / len(same), 4) if same else None,
               "mean_top5_overlap": round(sum(overlap) / len(overlap), 4) if overlap else None}
    with open(os.path.join(out_dir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--needs", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--depth", type=int, default=100)
    ap.add_argument("--max-df", type=int, default=400000)
    ap.add_argument("--min-terms", type=int, default=2)
    a = ap.parse_args(argv)
    s = run(a.db, a.needs, a.out_dir, a.depth, a.max_df, a.min_terms)
    print(json.dumps(s, indent=1))
    return 0 if s["needs"] else 1


if __name__ == "__main__":
    sys.exit(main())
