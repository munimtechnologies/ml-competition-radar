"""SPARK Task 2 baseline: extractive, cited answers from Task 1 candidates, with conflict flags.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Task 2 asks for "concise, objective, evidence-grounded responses with valid citations and
relevant passages" and scores Grounded Nugget F1 and Conflict/Controversy Coverage; compute
time and memory break ties. This first stage writes no new prose: every answer sentence is a
sentence from a cited abstract, so each claim is grounded by construction and runs in
milliseconds on a CPU. A later stage (an open-weight model) may rewrite it; this one is the
floor it has to beat.

  1. split the title + abstract of the first --depth candidates (t1.py or rerank_run.py
     ranked.jsonl) into sentences;
  2. score each sentence with BM25 over that sentence pool plus a prior for its article's rank;
  3. pick sentences by maximal marginal relevance (MMR) up to a word budget, at most
     --per-doc from one article;
  4. cite each sentence's own article, plus up to two other articles that hold a near-copy
     of it (corroboration), never more than 3 PMIDs per sentence;
  5. flag a conflict when two chosen sentences from different articles share content words
     but one reports a finding and the other reports its absence (negation cues), and flag
     uncertainty when a chosen sentence says the evidence is mixed or unclear. Cue words miss
     conflicts stated through hedging or population limits (arXiv 2603.17580).

Output (answers.jsonl): one row per need, {info_need_id, responses: [{text, citations,
role}], conflicts: [{pmids, sentences}], uncertain: [sentence index], words}. `biogen` writes
the TREC BioGen 2025 Task B run format; SPARK's own format is not published yet. `score`
measures citations against judged PMIDs (biogen_census.py's gold_t2.jsonl). Each cited PMID
gets exactly one class; 0.2.0 adds `mixed` for a paper judged both Supports and Contradicts in
the topic (168 of BioGen 2024's 202 contradicting papers, mostly one claim judged two ways:
job biogen-stance-v1), which 0.1.0 counted under both. Standard library only.

Commands:
  needs   --topics F --out F                          BioGen topics JSON -> needs JSONL
  compose --db DB --ranked F --out-dir D [--depth 20] [--words 250] [--per-doc 2]
  biogen  --answers F --team-id T --run-id R --out F
  score   --answers F --gold F --out-dir D
"""
import argparse
import json
import math
import os
import re
import sqlite3
import statistics
import sys
import time
from collections import Counter

VERSION = "0.2.0"
TOKEN_RX = re.compile(r"[a-z0-9]+")
STOP = frozenset("a an and are as at be by for from has have in is it of on or that the this to "
                 "was were which with we our these those their its not but than into".split())
ABBREV = ("e.g.", "i.e.", "et al.", "vs.", "fig.", "figs.", "approx.", "ca.", "no.", "dr.", "cf.")
SPLIT_RX = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])")
LABEL_RX = re.compile(r"^(?:[A-Z][A-Z /&-]{2,40}):\s*")  # BACKGROUND: METHODS: ...
NEG_RX = re.compile(r"\b(?:no|not|did not|does not|do not|was not|were not|failed to|neither|nor|"
                    r"without|lack of|absence of|ineffective|unaffected|unchanged|similar)\b", re.I)
NULL_RX = re.compile(r"\b(?:no (?:significant|statistically significant|clear|consistent) "
                     r"(?:difference|effect|association|benefit|improvement|change|reduction|increase)s?|"
                     r"not (?:significantly )?(?:associated|different|effective|improve[ds]?|reduce[ds]?|"
                     r"increase[ds]?)|did not (?:differ|improve|reduce|increase|change|affect)|"
                     r"no evidence|failed to (?:show|demonstrate|improve|reduce))\b", re.I)
POS_RX = re.compile(r"\b(?:significant(?:ly)?|associated with|improve[ds]?|reduce[ds]?|increase[ds]?|"
                    r"effective|benefit(?:s|ed)?|lower(?:ed)? risk|higher risk)\b", re.I)
HEDGE_RX = re.compile(r"\b(?:conflicting|controvers(?:y|ial)|inconsistent|mixed (?:results|evidence|"
                      r"findings)|remains? (?:unclear|uncertain|debated|controversial)|debate[ds]?|"
                      r"insufficient evidence|limited evidence|evidence is (?:weak|limited|lacking))\b", re.I)
MAX_CITES = 3
MAX_DOCS = 30
CLASSES = ("supports", "mixed", "contradicts", "other", "unjudged")


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def tokens(text):
    return [t for t in TOKEN_RX.findall(text.lower()) if len(t) > 1 and t not in STOP]


def split_sentences(text):
    """Sentences of an abstract; common abbreviations do not end a sentence."""
    text = " ".join((text or "").split())
    if not text:
        return []
    masked = text
    for a in ABBREV:
        masked = re.sub(r"\b" + re.escape(a), lambda m: m.group(0).replace(".", "\x00"), masked,
                        flags=re.I)
    out = []
    for s in SPLIT_RX.split(masked):
        s = LABEL_RX.sub("", s.replace("\x00", ".").strip())
        if len(tokens(s)) >= 3:
            out.append(s)
    return out


def polarity(sentence):
    """'null' (reports no effect / no association), 'finding', or None."""
    if NULL_RX.search(sentence):
        return "null"
    if POS_RX.search(sentence) and not NEG_RX.search(sentence):
        return "finding"
    return None


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def bm25_scores(query, docs, k1=1.2, b=0.75):
    """BM25 of one query against a small pool of token lists."""
    n = len(docs)
    if not n:
        return []
    avg = sum(len(d) for d in docs) / n or 1.0
    df = Counter(t for d in docs for t in set(d))
    q = set(query)
    out = []
    for d in docs:
        tf = Counter(d)
        s = 0.0
        for t in q:
            if tf[t]:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avg))
        out.append(s)
    return out


def pool(docs):
    """[(pmid, doc rank, sentence, tokens)] for (pmid, title, abstract) in rank order."""
    out = []
    for rank, (pmid, title, abstract) in enumerate(docs, 1):
        for s in split_sentences(abstract):
            out.append((str(pmid), rank, s, tokens(s)))
    return out


def compose(question, docs, words=250, per_doc=2, lam=0.7, prior=0.3, min_rel=0.2,
            corroborate=0.6, conflict_overlap=0.2):
    """One answer from ranked (pmid, title, abstract) triples. Pure function; see module doc.
    A sentence is eligible if its BM25 is at least min_rel of the best one; a sentence at least
    `corroborate` (Jaccard) like one already chosen is left out (it becomes a citation)."""
    sents = pool(docs)
    q = tokens(question)
    raw = bm25_scores(q, [t for _, _, _, t in sents])
    top = max(raw, default=0.0) or 1.0
    rel = [r / top + prior / rank for r, (_, rank, _, _) in zip(raw, sents)]
    chosen, used, per = [], 0, Counter()
    left = [i for i in range(len(sents)) if raw[i] > 0 and raw[i] / top >= min_rel]
    while left:
        sims = {k: max((jaccard(sents[k][3], sents[j][3]) for j in chosen), default=0.0) for k in left}
        i = max(left, key=lambda k: (lam * rel[k] - (1 - lam) * sims[k], -k))
        left.remove(i)
        pmid, _, s, _ = sents[i]
        n = len(s.split())
        if sims[i] >= corroborate or per[pmid] >= per_doc or used + n > words:
            continue
        chosen.append(i)
        per[pmid] += 1
        used += n
    responses, cited = [], set()
    for i in chosen:
        pmid, _, s, t = sents[i]
        cites = [pmid]
        for j, (p2, _, _, t2) in enumerate(sents):
            if len(cites) >= MAX_CITES:
                break
            if p2 not in cites and j != i and jaccard(t, t2) >= corroborate:
                if len(cited | set(cites) | {p2}) <= MAX_DOCS:
                    cites.append(p2)
        cited |= set(cites)
        responses.append({"text": s, "citations": cites, "role": "evidence"})
    conflicts = []
    for a in range(len(chosen)):
        for b in range(a + 1, len(chosen)):
            sa, sb = sents[chosen[a]], sents[chosen[b]]
            if sa[0] == sb[0]:
                continue
            pa, pb = polarity(sa[2]), polarity(sb[2])
            if {pa, pb} == {"null", "finding"} and jaccard(sa[3], sb[3]) >= conflict_overlap:
                conflicts.append({"pmids": [sa[0], sb[0]], "sentences": [a, b]})
    uncertain = [k for k, i in enumerate(chosen) if HEDGE_RX.search(sents[i][2])]
    return {"responses": responses, "conflicts": conflicts, "uncertain": uncertain, "words": used}


def fetch_docs(con, cands, depth):
    out = []
    for pmid, _ in cands[:depth]:
        row = con.execute("SELECT title, abstract FROM docs WHERE rowid=?", (int(pmid),)).fetchone()
        if row and row[1]:
            out.append((str(pmid), row[0] or "", row[1]))
    return out


def run(db, ranked_path, out_dir, depth=20, words=250, per_doc=2):
    if not os.path.exists(db):
        raise FileNotFoundError(db)
    os.makedirs(out_dir, exist_ok=True)
    con = sqlite3.connect(db)
    rows, secs = [], []
    for nd in load_jsonl(ranked_path):
        t0 = time.perf_counter()
        docs = fetch_docs(con, nd["candidates"], depth)
        ans = compose(nd["info_need"], docs, words, per_doc)
        secs.append(time.perf_counter() - t0)
        rows.append({"info_need_id": nd["info_need_id"], "docs_with_abstract": len(docs), **ans})
    con.close()
    write_jsonl(os.path.join(out_dir, "answers.jsonl"), rows)
    summary = {"version": VERSION, "needs": len(rows), "depth": depth, "words": words,
               "per_doc": per_doc, "empty": sum(1 for r in rows if not r["responses"]),
               "median_sentences": statistics.median([len(r["responses"]) for r in rows]) if rows else None,
               "median_words": statistics.median([r["words"] for r in rows]) if rows else None,
               "needs_with_conflict": sum(1 for r in rows if r["conflicts"]),
               "needs_with_uncertainty": sum(1 for r in rows if r["uncertain"]),
               "median_ms": round(1000 * statistics.median(secs), 1) if secs else None,
               "max_ms": round(1000 * max(secs), 1) if secs else None,
               "validate": validate(rows, words)}
    with open(os.path.join(out_dir, "compose.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def validate(rows, words=250):
    """BioGen Task B limits: <= words per answer, <= 3 PMIDs per sentence, <= 30 per answer."""
    problems = []
    for r in rows:
        rid = r.get("info_need_id")
        n = sum(len(x["text"].split()) for x in r["responses"])
        if n > words:
            problems.append("%s: %d words > %d" % (rid, n, words))
        docs = set()
        for k, x in enumerate(r["responses"]):
            c = x["citations"]
            if len(c) > MAX_CITES or len(set(c)) != len(c):
                problems.append("%s: sentence %d citations %s" % (rid, k, c))
            docs |= set(c)
        if len(docs) > MAX_DOCS:
            problems.append("%s: %d documents > %d" % (rid, len(docs), MAX_DOCS))
    return problems


def biogen_rows(answers, team_id, run_id):
    """TREC BioGen 2025 Task B run lines (metadata + responses of text and citations)."""
    return [{"metadata": {"team_id": team_id, "run_id": run_id, "topic_id": a["info_need_id"]},
             "responses": [{"text": x["text"], "citations": x["citations"]} for x in a["responses"]]}
            for a in answers]


def needs_from_topics(obj):
    rows = obj.get("topics", obj) if isinstance(obj, dict) else obj
    return [{"info_need_id": str(t["id"]), "info_need": t["question"]} for t in rows]


def stance_class(p, sup, con, other):
    """One class per PMID: in both the topic's Supports and Contradicts sets -> 'mixed'; then
    'supports', 'contradicts', 'other' (only Neutral / Not Relevant), else 'unjudged'."""
    if p in sup:
        return "mixed" if p in con else "supports"
    if p in con:
        return "contradicts"
    return "other" if p in other else "unjudged"


def score(answers, gold):
    """Citations against judged PMIDs. Judgments are pooled from 2024 runs, so a PMID nobody
    cited then is 'unjudged', not wrong. Per answer: the share of citations in each class of
    CLASSES (they sum to 1), recall of all Supports PMIDs and of Supports-only PMIDs, mixed and
    contradicts-only papers cited and known, and conflict flags on them; then means."""
    by = {str(g["topic"]): g for g in gold}
    per = []
    for a in answers:
        g = by.get(str(a["info_need_id"]))
        if g is None:
            continue
        sup, con = set(map(str, g["supports"])), set(map(str, g["contradicts"]))
        other = set(map(str, g["neutral"])) | set(map(str, g["notrelevant"]))
        mixed, sup_only, con_only = sup & con, sup - con, con - sup
        cited = [str(p) for x in a["responses"] for p in x["citations"]]
        docs = set(cited)
        n = len(cited) or 1
        kinds = Counter(stance_class(p, sup, con, other) for p in cited)
        flagged = {str(p) for c in a.get("conflicts", []) for p in c["pmids"]}
        row = {"topic": g["topic"], "citations": len(cited)}
        row.update({k + "_share": kinds[k] / n for k in CLASSES})
        row.update({"supports_recall": len(docs & sup) / len(sup) if sup else None,
                    "supports_only_recall": len(docs & sup_only) / len(sup_only) if sup_only else None,
                    "mixed_found": len(docs & mixed), "mixed_known": len(mixed),
                    "contradicts_only_found": len(docs & con_only), "contradicts_only_known": len(con_only),
                    "conflict_flag_hits_mixed": len(flagged & mixed),
                    "conflict_flag_hits_contradicts_only": len(flagged & con_only)})
        per.append(row)
    out = {"version": VERSION, "answers_scored": len(per),
           "answers_without_gold": sum(1 for a in answers if str(a["info_need_id"]) not in by)}
    for k in [c + "_share" for c in CLASSES] + ["supports_recall", "supports_only_recall"]:
        vals = [p[k] for p in per if p[k] is not None]
        out["mean_" + k] = round(sum(vals) / len(vals), 4) if vals else None
    for k in ("mixed", "contradicts_only"):
        out["topics_with_%s_found" % k] = sum(1 for p in per if p[k + "_found"])
        out["topics_with_%s_known" % k] = sum(1 for p in per if p[k + "_known"])
    out["per_topic"] = per
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("needs")
    n.add_argument("--topics", required=True)
    n.add_argument("--out", required=True)
    c = sub.add_parser("compose")
    c.add_argument("--db", required=True)
    c.add_argument("--ranked", required=True)
    c.add_argument("--out-dir", required=True)
    c.add_argument("--depth", type=int, default=20)
    c.add_argument("--words", type=int, default=250)
    c.add_argument("--per-doc", type=int, default=2)
    b = sub.add_parser("biogen")
    b.add_argument("--answers", required=True)
    b.add_argument("--team-id", required=True)
    b.add_argument("--run-id", required=True)
    b.add_argument("--out", required=True)
    s = sub.add_parser("score")
    s.add_argument("--answers", required=True)
    s.add_argument("--gold", required=True)
    s.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "needs":
        with open(a.topics, encoding="utf-8-sig") as f:
            rows = needs_from_topics(json.load(f))
        write_jsonl(a.out, rows)
        res, bad = {"needs": len(rows)}, not rows
    elif a.cmd == "compose":
        res = run(a.db, a.ranked, a.out_dir, a.depth, a.words, a.per_doc)
        bad = bool(res["validate"])
    elif a.cmd == "biogen":
        rows = biogen_rows(load_jsonl(a.answers), a.team_id, a.run_id)
        write_jsonl(a.out, rows)
        res, bad = {"lines": len(rows)}, not rows
    else:
        res = score(load_jsonl(a.answers), load_jsonl(a.gold))
        os.makedirs(a.out_dir, exist_ok=True)
        with open(os.path.join(a.out_dir, "scores.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
        res = {k: v for k, v in res.items() if k != "per_topic"}
        bad = not res["answers_scored"]
    print(json.dumps(res, indent=1)[:6000])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
