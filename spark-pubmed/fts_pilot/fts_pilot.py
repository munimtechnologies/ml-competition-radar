"""SQLite FTS5 pilot for the NLM SPARK PubMed corpus: index size, build speed and query speed.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Builds an on-disk FTS5 index (title, abstract, MeSH; porter + unicode61 tokenizer, rowid = PMID)
over every --stride-th verified file of the mirrored corpus, and measures bytes per document,
documents per second and milliseconds per query. It then builds the same index on three files
with each FTS5 detail level (full, column, none) to compare size against ranking. The two query
checks (a paper's own title; the first sentence of its abstract) test the pipeline and set a
size/latency budget; they are not retrieval results. Python standard library only. Writes
pilot.json to --out-dir.
"""
import argparse
import gzip
import json
import os
import random
import re
import sqlite3
import statistics
import sys
import time
import xml.etree.ElementTree as ET

try:
    import resource
except ImportError:  # not on Windows; peak memory is then not reported
    resource = None

NAME_RX = re.compile(r"pubmed27n\d{4}\.xml\.gz")
TOKEN_RX = re.compile(r"[a-z0-9]+")
SENTENCE_RX = re.compile(r"(?<=[.!?])\s+")
STOP = frozenset("a an and are as at be by for from has have in is it of on or that the this to "
                 "was were which with we our these those their its not but than into".split())
WEIGHTS = (2.0, 1.0, 0.5)  # bm25 column weights: title, abstract, MeSH
MAX_TERMS = 32
CORPUS_DOCS = 39.17e6  # corpus-wide estimate from the run-168 audit (1,305 x 30,000 + 17,568)


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
    return {"pmid": int(cit.findtext("PMID")), "title": text_of(art.find("ArticleTitle")),
            "abstract": " ".join(parts),
            "mesh": "; ".join(text_of(d) for d in cit.findall("MeshHeadingList/MeshHeading/DescriptorName")),
            "year": year_of(art), "journal": art.findtext("Journal/ISOAbbreviation") or "",
            "pmcid": pmcid}


def parse_file(path):
    """Yield one record per PubmedArticle in a gzipped PubMed XML file."""
    with gzip.open(path, "rb") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == "PubmedArticle":
                yield parse_article(el)
                el.clear()


def open_db(path, detail):
    for p in (path, path + "-journal", path + "-wal"):
        if os.path.exists(p):
            os.remove(p)
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("CREATE VIRTUAL TABLE docs USING fts5(title, abstract, mesh, "
                "tokenize='porter unicode61 remove_diacritics 2', detail=%s)" % detail)
    con.execute("CREATE TABLE meta (pmid INTEGER PRIMARY KEY, year INTEGER, journal TEXT, pmcid TEXT)")
    return con


class Reservoir:
    """Fixed-size uniform sample of (pmid, title, abstract) for papers with both fields."""

    def __init__(self, k, seed):
        self.k, self.rng, self.seen, self.items = k, random.Random(seed), 0, []

    def offer(self, rec):
        if not (rec["title"] and rec["abstract"]):
            return
        self.seen += 1
        item = (rec["pmid"], rec["title"], rec["abstract"])
        if len(self.items) < self.k:
            self.items.append(item)
        else:
            j = self.rng.randrange(self.seen)
            if j < self.k:
                self.items[j] = item


def add_file(con, path, reservoir=None):
    """Index one file in one transaction. Returns (docs added, duplicate PMIDs skipped)."""
    n = dups = 0
    with con:
        for rec in parse_file(path):
            try:
                con.execute("INSERT INTO meta VALUES (?,?,?,?)",
                            (rec["pmid"], rec["year"], rec["journal"], rec["pmcid"]))
            except sqlite3.IntegrityError:
                dups += 1
                continue
            con.execute("INSERT INTO docs(rowid, title, abstract, mesh) VALUES (?,?,?,?)",
                        (rec["pmid"], rec["title"], rec["abstract"], rec["mesh"]))
            n += 1
            if reservoir is not None:
                reservoir.offer(rec)
    return n, dups


def compact(con, path):
    """Merge all FTS5 segments and VACUUM. Returns (bytes before, bytes after, seconds)."""
    before, t0 = os.path.getsize(path), time.time()
    con.execute("INSERT INTO docs(docs) VALUES('optimize')")
    con.commit()
    con.execute("VACUUM")
    return before, os.path.getsize(path), round(time.time() - t0, 1)


def parts(con):
    """Bytes of the inverted index and of the stored text (FTS5 shadow tables)."""
    index = con.execute("SELECT COALESCE(SUM(LENGTH(block)), 0) FROM docs_data").fetchone()[0]
    text = con.execute("SELECT COALESCE(SUM(LENGTH(CAST(c0 AS BLOB)) + LENGTH(CAST(c1 AS BLOB)) + "
                       "LENGTH(CAST(c2 AS BLOB))), 0) FROM docs_content").fetchone()[0]
    return index, text


def match_expr(text):
    seen, toks = set(), []
    for t in TOKEN_RX.findall(text.lower()):
        if len(t) > 1 and t not in STOP and t not in seen:
            seen.add(t)
            toks.append(t)
    return " OR ".join('"%s"' % t for t in toks[:MAX_TERMS])


def search(con, text, k=5):
    q = match_expr(text)
    if not q:
        return []
    rows = con.execute("SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY bm25(docs, ?, ?, ?) LIMIT ?",
                       (q,) + WEIGHTS + (k,)).fetchall()
    return [r[0] for r in rows]


def first_sentence(abstract):
    s = SENTENCE_RX.split(abstract, 1)[0]
    if len(TOKEN_RX.findall(s.lower())) < 5:
        s = " ".join(abstract.split()[:25])
    return s


def evaluate(con, items, kind):
    rrs, ms = [], []
    for pmid, title, abstract in items:
        text = title if kind == "title" else first_sentence(abstract)
        t0 = time.perf_counter()
        ranked = search(con, text)
        ms.append(1000 * (time.perf_counter() - t0))
        rrs.append(next((1.0 / i for i, d in enumerate(ranked, 1) if d == pmid), 0.0))
    if not rrs:
        return None
    srt = sorted(ms)
    return {"n": len(rrs), "mrr_at_5": round(sum(rrs) / len(rrs), 4),
            "hit_at_1": round(sum(r == 1.0 for r in rrs) / len(rrs), 4),
            "ms_median": round(statistics.median(ms), 1), "ms_p90": round(srt[int(0.9 * (len(srt) - 1))], 1),
            "ms_max": round(srt[-1], 1)}


def peak_rss_mb():
    if resource is None:
        return None
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def build(raw_dir, names, path, detail, reservoir=None):
    con = open_db(path, detail)
    t0, docs, dups, per_file = time.time(), 0, 0, []
    for name in names:
        t1 = time.time()
        n, d = add_file(con, os.path.join(raw_dir, name), reservoir)
        docs, dups = docs + n, dups + d
        per_file.append({"file": name, "docs": n, "seconds": round(time.time() - t1, 1)})
    secs = round(time.time() - t0, 1)
    before, after, opt_secs = compact(con, path)
    index, text = parts(con)
    rec = {"detail": detail, "files": len(names), "docs": docs, "duplicate_pmids": dups,
           "build_seconds": secs, "docs_per_second": round(docs / secs, 1) if secs else None,
           "bytes_built": before, "bytes_compacted": after, "compact_seconds": opt_secs,
           "bytes_per_doc": round(after / docs, 1) if docs else None,
           "index_bytes": index, "text_bytes": text, "per_file": per_file}
    return con, rec


def run(raw_dir, db_dir, out_dir, stride, sample, seed):
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(raw_dir)
                   if NAME_RX.fullmatch(n) and os.path.exists(os.path.join(raw_dir, n + ".md5ok")))
    picked = names[::stride]
    summary = {"verified_files": len(names), "stride": stride, "seed": seed, "sqlite": sqlite3.sqlite_version,
               "pilot_files": picked, "problem": None, "pilot": None, "compare": []}
    out = os.path.join(out_dir, "pilot.json")
    if not picked:
        summary["problem"] = "no verified corpus files under %s" % raw_dir
    else:
        res = Reservoir(sample, seed)
        con, rec = build(raw_dir, picked, os.path.join(db_dir, "pilot_full.db"), "full", res)
        if rec["bytes_per_doc"]:
            rec["extrapolated_gb_full_corpus"] = round(rec["bytes_per_doc"] * CORPUS_DOCS / 1e9, 1)
        rec["queries"] = {"title": evaluate(con, res.items, "title"),
                          "first_sentence": evaluate(con, res.items, "first_sentence")}
        con.close()
        summary["pilot"] = rec
        trio = []
        for n in (picked[0], picked[len(picked) // 2], picked[-1]):
            if n not in trio:
                trio.append(n)
        summary["compare_files"] = trio
        cres = Reservoir(sample, seed + 1)
        for i, detail in enumerate(("full", "column", "none")):
            path = os.path.join(db_dir, "compare_%s.db" % detail)
            try:
                con, rec = build(raw_dir, trio, path, detail, cres if i == 0 else None)
            except sqlite3.Error as exc:
                rec = {"detail": detail, "error": "%s: %s" % (type(exc).__name__, str(exc)[:200])}
            else:
                rec.pop("per_file")
                try:
                    rec["queries"] = {"title": evaluate(con, cres.items, "title"),
                                      "first_sentence": evaluate(con, cres.items, "first_sentence")}
                except sqlite3.Error as exc:  # e.g. bm25 refused at one detail level: record it
                    rec["queries_error"] = "%s: %s" % (type(exc).__name__, str(exc)[:200])
                con.close()
            summary["compare"].append(rec)
            if os.path.exists(path):
                os.remove(path)
        if not summary["pilot"]["docs"]:
            summary["problem"] = "nothing indexed"
    summary["peak_rss_mb"] = peak_rss_mb()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--db-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--stride", type=int, default=33)
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--seed", type=int, default=169)
    args = ap.parse_args(argv)
    s = run(args.raw_dir, args.db_dir, args.out_dir, args.stride, args.sample, args.seed)
    brief = {k: s.get(k) for k in ("problem", "verified_files", "sqlite", "peak_rss_mb")}
    if s.get("pilot"):
        brief["pilot"] = {k: v for k, v in s["pilot"].items() if k != "per_file"}
    brief["compare"] = s.get("compare")
    print(json.dumps(brief, indent=1)[:6000])
    return 1 if s["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
