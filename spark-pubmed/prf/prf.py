"""SPARK Task 1 recall stage: pseudo-relevance feedback (RM3-style) on the whole PubMed index.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

On headline L, BM25 put the target in its first 100 candidates for only 20 of 43 questions
(t1_runner/RESULTS-spark35.md), so a reranker of the first 50 cannot reach most targets. This adds
words from the first --fb-docs BM25 candidates to the query and fuses the new list with the
baseline:

  1. Feedback words (RM1): P(w) = sum over feedback documents i of s_i * tf_i(w) / len_i, where
     s_i is document i's share of the feedback BM25 scores (equal shares if none is positive).
     Words are title + abstract + MeSH, longer than one character, not stop words, not only
     digits.
  2. Expansion: the --fb-terms best words not already in the question and found in 1 to --max-df
     records (each probe capped at max-df + 1 rows, cached per run; at most 3 x fb-terms probes
     per question).
  3. Expanded query: the question's words (all of them, or with --question-max-df > 0 only those
     found in 1 to that many records, falling back to all if fewer than --min-terms survive, as
     prune.py does) OR the expansion words, BM25 depth --depth.
  4. Fusion: reciprocal-rank fusion (k = --rrf-k) of the baseline list and the expanded list.

Input is a t1.py ranked.jsonl (BM25 baseline with candidates and ms). Output: ranked.jsonl (the
fused list) and ranked_exp.jsonl (the expanded list alone), both in t1.py's format so `t1.py score`
applies unchanged, plus run.json with counts and timings (never the words). Tokens, stop words,
column weights and the 32-word limit are build_index.py 0.3's. Standard library only.

  python prf.py --db DB --needs RANKED --out-dir D [--depth 100] [--fb-docs 10] [--fb-terms 10]
                [--max-df 400000] [--question-max-df 0] [--min-terms 2] [--rrf-k 60]
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
RRF_K = 60
SQL = "SELECT rowid, bm25(docs, ?, ?, ?) FROM docs WHERE docs MATCH ? ORDER BY 2 LIMIT ?"


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


def words(text):
    """Every word of a feedback document, repeats kept: longer than one character, not a stop
    word, not only digits."""
    return [t for t in TOKEN_RX.findall(text.lower()) if len(t) > 1 and t not in STOP and not t.isdigit()]


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


def feedback_weights(docs):
    """RM1 word weights from [(bm25 score, text)]; documents without words are skipped."""
    rows = [(s, w) for s, w in ((s, words(x)) for s, x in docs) if w]
    if not rows:
        return {}
    pos = [max(float(s), 0.0) for s, _ in rows]
    total = sum(pos)
    shares = [p / total for p in pos] if total > 0 else [1.0 / len(rows)] * len(rows)
    out = {}
    for share, ws in zip(shares, rows):
        each = share / len(ws[1])
        for t in ws[1]:
            out[t] = out.get(t, 0.0) + each
    return out


def expansion(weights, exclude, df, max_df, n_terms, max_probes):
    """Up to n_terms words, best weight first (ties by word), skipping excluded words and words
    found in no record or in more than max_df; at most max_probes words are probed."""
    picked, probes = [], 0
    for t, _ in sorted(weights.items(), key=lambda kv: (-kv[1], kv[0])):
        if len(picked) >= n_terms or probes >= max_probes:
            break
        if t in exclude:
            continue
        probes += 1
        if 0 < df(t) <= max_df:
            picked.append(t)
    return picked


def rrf(lists, k=RRF_K, depth=100):
    """Reciprocal-rank fusion of [pmid, score] lists: [[pmid, fused score]], best first; ties go
    to the item seen first (the baseline's list comes first)."""
    score, order = {}, {}
    for lst in lists:
        for rank, (p, _) in enumerate(lst, 1):
            p = int(p)
            score[p] = score.get(p, 0.0) + 1.0 / (k + rank)
            order.setdefault(p, len(order))
    best = sorted(score, key=lambda p: (-score[p], order[p]))
    return [[p, round(score[p], 6)] for p in best[:depth]]


def query(con, toks, depth):
    if not toks:
        return []
    return [[int(p), round(-s, 6)] for p, s in con.execute(SQL, WEIGHTS + (match_expr(toks), depth)).fetchall()]


def text_of(con, pmid):
    row = con.execute("SELECT title, abstract, mesh FROM docs WHERE rowid=?", (int(pmid),)).fetchone()
    return " ".join(x or "" for x in row).strip() if row else ""


def pct(values, q):
    srt = sorted(values)
    return round(srt[min(len(srt) - 1, int(q * len(srt)))], 1) if srt else None


def run(db, needs_path, out_dir, depth=100, fb_docs=10, fb_terms=10, max_df=400000,
        question_max_df=0, min_terms=2, k=RRF_K):
    """Expand and fuse every need; write ranked.jsonl, ranked_exp.jsonl and run.json."""
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    os.makedirs(out_dir, exist_ok=True)
    needs = load_jsonl(needs_path)
    con = sqlite3.connect(db)
    df = DocFreq(con, max(max_df, question_max_df))
    fused_rows, exp_rows, ms, total_ms, base_ms, n_extra, missing = [], [], [], [], [], [], 0
    for nd in needs:
        t0 = time.perf_counter()
        base = [[int(p), s] for p, s in (nd.get("candidates") or [])]
        toks = tokens(nd["info_need"])
        kept = list(toks)
        if question_max_df > 0:
            kept = [t for t in toks if 0 < df(t) <= question_max_df]
            if len(kept) < min_terms:
                kept = list(toks)
        docs = []
        for p, s in base[:fb_docs]:
            x = text_of(con, p)
            if x:
                docs.append((s, x))
            else:
                missing += 1
        extra = expansion(feedback_weights(docs), set(toks), df, max_df, fb_terms, 3 * fb_terms)
        exp = query(con, kept + extra, depth)
        fused = rrf([base[:depth], exp], k, depth)
        ms.append((time.perf_counter() - t0) * 1000)
        if nd.get("ms"):
            base_ms.append(nd["ms"])
            total_ms.append(nd["ms"] + ms[-1])
        n_extra.append(len(extra))
        common = {"info_need_id": nd["info_need_id"], "info_need": nd["info_need"], "depth": depth,
                  "ms": round(ms[-1], 1), "kept": len(kept), "expansion_terms": len(extra)}
        exp_rows.append(dict(common, candidates=exp))
        fused_rows.append(dict(common, candidates=fused))
    con.close()
    write_jsonl(os.path.join(out_dir, "ranked.jsonl"), fused_rows)
    write_jsonl(os.path.join(out_dir, "ranked_exp.jsonl"), exp_rows)
    n = len(needs)
    summary = {"version": VERSION, "needs": n, "depth": depth, "fb_docs": fb_docs, "fb_terms": fb_terms,
               "max_df": max_df, "question_max_df": question_max_df, "min_terms": min_terms, "rrf_k": k,
               "no_candidates_fused": sum(1 for r in fused_rows if not r["candidates"]),
               "no_candidates_exp": sum(1 for r in exp_rows if not r["candidates"]),
               "no_expansion": sum(1 for x in n_extra if not x),
               "mean_expansion_terms": round(sum(n_extra) / n, 2) if n else None,
               "missing_text": missing,
               "median_ms": round(statistics.median(ms), 1) if ms else None, "p95_ms": pct(ms, 0.95),
               "baseline_median_ms": round(statistics.median(base_ms), 1) if base_ms else None,
               "median_total_ms": round(statistics.median(total_ms), 1) if total_ms else None,
               "probed_terms": len(df.cache), "probe_seconds": round(df.seconds, 1)}
    with open(os.path.join(out_dir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--needs", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--depth", type=int, default=100)
    ap.add_argument("--fb-docs", type=int, default=10)
    ap.add_argument("--fb-terms", type=int, default=10)
    ap.add_argument("--max-df", type=int, default=400000)
    ap.add_argument("--question-max-df", type=int, default=0)
    ap.add_argument("--min-terms", type=int, default=2)
    ap.add_argument("--rrf-k", type=int, default=RRF_K)
    a = ap.parse_args(argv)
    s = run(a.db, a.needs, a.out_dir, a.depth, a.fb_docs, a.fb_terms, a.max_df, a.question_max_df,
            a.min_terms, a.rrf_k)
    print(json.dumps(s, indent=1))
    return 0 if s["needs"] else 1


if __name__ == "__main__":
    sys.exit(main())
