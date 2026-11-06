"""DSQA proxy retrieval study (dsqa-retrieval-v1).

For the IEEE CIS 2026 Technical Challenge on Domain-Specific Question Answering with LLMs (DSQA):
on a small public proxy corpus (open-access papers behind the organisers' public sample questions,
plus hard-negative look-alike papers), compare how fast two PDF text extractors run and how well
BM25, a MiniLM embedder and their reciprocal-rank fusion find the right paper for each question.

It never runs the contest's model and never touches the contest's hidden corpus. Only document ids
and scores are written out; no PDF text and no question or answer text.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python dsqa_retrieval.py --corpus corpus.json --data-dir /data --out-dir /out
"""
import argparse
import json
import math
import os
import platform
import re
import sys
import time
import urllib.request
from collections import Counter

USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"
TOKEN_RE = re.compile(r"\w+", re.UNICODE)


# ---------------------------------------------------------------- text and ranking helpers

def tokenize(text):
    return TOKEN_RE.findall(text.lower())


def chunk_text(text, size=800, overlap=150):
    """Split on blank lines, hard-split paragraphs longer than `size` at spaces, then pack pieces
    greedily into chunks of about `size` characters; each new chunk starts with the last `overlap`
    characters of the previous one (as in the organisers' RAG starter, which uses 800/150)."""
    pieces = []
    for para in re.split(r"\n\s*\n", text):
        p = " ".join(para.split())
        while len(p) > size:
            cut = p.rfind(" ", 0, size)
            if cut <= 0:
                cut = size
            pieces.append(p[:cut])
            p = p[cut:].strip()
        if p:
            pieces.append(p)
    chunks, cur = [], ""
    for piece in pieces:
        if cur and len(cur) + 1 + len(piece) > size:
            chunks.append(cur)
            tail = cur[-overlap:] if overlap else ""
            cur = (tail + " " + piece).strip() if tail else piece
        else:
            cur = (cur + " " + piece) if cur else piece
    if cur:
        chunks.append(cur)
    return chunks


class BM25:
    """Okapi BM25 with the always-positive idf ln((N - df + 0.5) / (df + 0.5) + 1)."""

    def __init__(self, docs_tokens, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.tfs = [Counter(d) for d in docs_tokens]
        self.lens = [len(d) for d in docs_tokens]
        self.n = len(docs_tokens)
        self.avgdl = (sum(self.lens) / self.n) if self.n else 0.0
        df = Counter()
        for tf in self.tfs:
            df.update(tf.keys())
        self.idf = {t: math.log((self.n - c + 0.5) / (c + 0.5) + 1.0) for t, c in df.items()}
        self.postings = {}
        for i, tf in enumerate(self.tfs):
            for t, f in tf.items():
                self.postings.setdefault(t, []).append((i, f))

    def scores(self, query_tokens):
        out = [0.0] * self.n
        for t in set(query_tokens):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i, f in self.postings[t]:
                denom = f + self.k1 * (1 - self.b + self.b * self.lens[i] / self.avgdl)
                out[i] += idf * f * (self.k1 + 1) / denom
        return out


def rank_desc(scores):
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))


def rrf(rankings, k=60):
    score = {}
    for r in rankings:
        for pos, i in enumerate(r):
            score[i] = score.get(i, 0.0) + 1.0 / (k + pos + 1)
    return sorted(score, key=lambda i: (-score[i], i))


def doc_order(chunk_ranking, chunk_doc):
    seen, out = set(), []
    for i in chunk_ranking:
        d = chunk_doc[i]
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def first_rank(seq, gold):
    for pos, x in enumerate(seq):
        if x in gold:
            return pos + 1
    return None


def context_take(chunk_ranking, chunk_len, budget):
    taken, total = [], 0
    for i in chunk_ranking:
        if total + chunk_len[i] > budget:
            break
        taken.append(i)
        total += chunk_len[i]
    return taken


def evaluate_question(chunk_ranking, chunk_doc, chunk_len, gold, budget):
    docs = doc_order(chunk_ranking, chunk_doc)
    ctx = context_take(chunk_ranking, chunk_len, budget)
    first_chunk = first_rank([chunk_doc[i] for i in chunk_ranking], gold)
    gold_chars = sum(chunk_len[i] for i in ctx if chunk_doc[i] in gold)
    total = sum(chunk_len[i] for i in ctx)
    return {
        "top1_gold": first_chunk == 1,
        "first_gold_chunk_rank": first_chunk,
        "gold_doc_rank": first_rank(docs, gold),
        "gold_in_context": gold_chars > 0,
        "gold_share": round(gold_chars / total, 4) if total else 0.0,
        "context_chunks": len(ctx),
        "top_doc": chunk_doc[chunk_ranking[0]] if chunk_ranking else None,
    }


def summarize(results):
    n = len(results)
    rr = [(1.0 / r["gold_doc_rank"]) if r["gold_doc_rank"] else 0.0 for r in results]
    return {
        "n": n,
        "hit1": sum(1 for r in results if r["top1_gold"]),
        "mrr_doc": round(sum(rr) / n, 4) if n else 0.0,
        "in_context": sum(1 for r in results if r["gold_in_context"]),
    }


# ---------------------------------------------------------------- I/O

def fetch_bytes(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_pdf(url, dest, tries=3):
    err = None
    for k in range(tries):
        try:
            data = fetch_bytes(url)
            if data[:5] != b"%PDF-":
                return "not a PDF (%d bytes)" % len(data)
            with open(dest + ".part", "wb") as f:
                f.write(data)
            os.replace(dest + ".part", dest)
            return None
        except Exception as e:  # network errors: retry with back-off
            err = "%s: %s" % (type(e).__name__, e)
            time.sleep(5 * (k + 1))
    return err


def is_pdf(path):
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def extract_pymupdf(path):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    t = time.perf_counter()
    doc = fitz.open(path)
    parts = []
    for page in doc:
        for blk in page.get_text("blocks"):
            if len(blk) >= 7 and blk[6] != 0:  # image block
                continue
            txt = blk[4].strip()
            if txt:
                parts.append(txt)
    pages = doc.page_count
    doc.close()
    return "\n\n".join(parts), pages, time.perf_counter() - t


def extract_pypdf(path):
    from pypdf import PdfReader
    t = time.perf_counter()
    reader = PdfReader(path)
    texts = [(p.extract_text() or "") for p in reader.pages]
    return "\n\n".join(texts), len(reader.pages), time.perf_counter() - t


def version_of(mod):
    try:
        m = __import__(mod)
        return getattr(m, "__version__", None) or getattr(m, "VersionBind", None) or "?"
    except Exception as e:
        return "not importable: %s" % type(e).__name__


# ---------------------------------------------------------------- grading (pre-registered P1-P7)

def grade(res):
    m = res["methods"]
    out = {}
    tot = res["extraction_totals"]
    out["P1"] = tot["pypdf_seconds"] >= 3 * tot["pymupdf_seconds"]
    b = m["bm25_pymupdf"]["summary"]
    n = b["n"]
    out["P2"] = n > 0 and b["hit1"] >= 0.75 * n
    if "dense_pymupdf" in m and "hybrid_pymupdf" in m:
        d = m["dense_pymupdf"]["summary"]
        h = m["hybrid_pymupdf"]["summary"]
        out["P3"] = b["hit1"] >= d["hit1"]
        out["P4"] = all(s["in_context"] * 9 >= 8 * s["n"] for s in (b, d, h))
        out["P5"] = h["hit1"] >= max(b["hit1"], d["hit1"]) - 1
    else:
        out["P3"] = out["P4"] = out["P5"] = "not gradable: dense step failed"
    q23 = m["bm25_pymupdf"]["per_question"].get("23")
    if q23 is None:
        out["P6"] = "not gradable: question 23 not evaluable"
    else:
        out["P6"] = res["roles"].get(q23["top_doc"]) == "hard"
    out["P7"] = (tot["pymupdf_seconds"] + m["bm25_pymupdf"]["index_seconds"]) < 60
    out["gradable"] = n >= 7
    return out


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--budget-chars", type=int, default=40000)
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    a = ap.parse_args(argv)

    with open(a.corpus, encoding="utf-8") as f:
        corpus = json.load(f)
    pdf_dir = os.path.join(a.data_dir, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(a.out_dir, exist_ok=True)

    downloads, roles = {}, {}
    for d in corpus["docs"]:
        roles[d["id"]] = d["role"]
        dest = os.path.join(pdf_dir, d["id"] + ".pdf")
        if is_pdf(dest):
            downloads[d["id"]] = "cached"
            continue
        err = "no url"
        for url in d["urls"]:
            err = fetch_pdf(url, dest)
            time.sleep(3)  # polite pacing for arXiv and publishers
            if err is None:
                break
        downloads[d["id"]] = "ok" if err is None else err
        print("download", d["id"], downloads[d["id"]], flush=True)

    qa = json.loads(fetch_bytes(corpus["questions_url"]).decode("utf-8"))
    qtext = {int(q["id"]): q["question"] for q in qa}

    have = [d for d in corpus["docs"] if is_pdf(os.path.join(pdf_dir, d["id"] + ".pdf"))]
    docs_info, texts = [], {"pymupdf": {}, "pypdf": {}}
    tot = {"pymupdf_seconds": 0.0, "pypdf_seconds": 0.0, "pages": 0, "docs_both_ok": 0}
    for d in have:
        path = os.path.join(pdf_dir, d["id"] + ".pdf")
        info = {"id": d["id"], "role": d["role"], "bytes": os.path.getsize(path)}
        ok = True
        for name, fn in (("pymupdf", extract_pymupdf), ("pypdf", extract_pypdf)):
            try:
                txt, pages, sec = fn(path)
                texts[name][d["id"]] = txt
                info["pages"] = pages
                info["chars_" + name] = len(txt)
                info["sec_" + name] = round(sec, 4)
            except Exception as e:
                info["error_" + name] = "%s: %s" % (type(e).__name__, e)
                ok = False
        if ok:
            tot["pymupdf_seconds"] += info["sec_pymupdf"]
            tot["pypdf_seconds"] += info["sec_pypdf"]
            tot["pages"] += info.get("pages", 0)
            tot["docs_both_ok"] += 1
        docs_info.append(info)
        print("extract", d["id"], {k: v for k, v in info.items() if k.startswith(("sec_", "pages", "error"))}, flush=True)
    tot = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in tot.items()}

    # evaluable questions: listed, present in the sample file, and with a gold paper we hold as text
    gold = {}
    for d in corpus["docs"]:
        for q in d.get("gold_for", []):
            if d["id"] in texts["pymupdf"]:
                gold.setdefault(int(q), set()).add(d["id"])
    qids = [q for q in corpus["questions"] if q in qtext and gold.get(q)]
    excluded = [q for q in corpus["questions"] if q not in qids]

    def build(name):
        t = time.perf_counter()
        cdoc, ctext = [], []
        for d in have:
            if d["id"] in texts[name]:
                for c in chunk_text(texts[name][d["id"]]):
                    cdoc.append(d["id"])
                    ctext.append(c)
        bm = BM25([tokenize(c) for c in ctext])
        return cdoc, ctext, bm, time.perf_counter() - t

    methods, rankings = {}, {}

    def record(method, cdoc, clen, ranks, index_seconds, extra=None):
        per = {}
        for q in qids:
            per[str(q)] = evaluate_question(ranks[q], cdoc, clen, gold[q], a.budget_chars)
        methods[method] = {"index_seconds": round(index_seconds, 3), "chunks": len(cdoc),
                           "per_question": per, "summary": summarize(list(per.values()))}
        if extra:
            methods[method].update(extra)
        print(method, methods[method]["summary"], flush=True)

    cdoc_m, ctext_m, bm_m, sec_m = build("pymupdf")
    clen_m = [len(c) for c in ctext_m]
    rankings["bm25_pymupdf"] = {q: rank_desc(bm_m.scores(tokenize(qtext[q]))) for q in qids}
    record("bm25_pymupdf", cdoc_m, clen_m, rankings["bm25_pymupdf"], sec_m)

    cdoc_p, ctext_p, bm_p, sec_p = build("pypdf")
    clen_p = [len(c) for c in ctext_p]
    rp = {q: rank_desc(bm_p.scores(tokenize(qtext[q]))) for q in qids}
    record("bm25_pypdf", cdoc_p, clen_p, rp, sec_p)

    res = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "python": platform.python_version(), "cpu_count": os.cpu_count(),
           "versions": {"pymupdf": version_of("pymupdf"), "pypdf": version_of("pypdf")},
           "budget_chars": a.budget_chars, "model": a.model,
           "downloads": downloads, "roles": roles, "docs": docs_info, "extraction_totals": tot,
           "questions_evaluated": qids, "questions_excluded": excluded,
           "gold": {str(q): sorted(gold[q]) for q in qids}, "methods": methods}

    def write():
        with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)

    write()  # BM25 results are safe even if the dense step fails

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
        res["versions"]["sentence_transformers"] = version_of("sentence_transformers")
        res["versions"]["torch"] = version_of("torch")
        t = time.perf_counter()
        model = SentenceTransformer(a.model, device="cpu")
        load_sec = time.perf_counter() - t
        t = time.perf_counter()
        emb = model.encode(ctext_m, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
        enc_sec = time.perf_counter() - t
        qemb = model.encode([qtext[q] for q in qids], normalize_embeddings=True, show_progress_bar=False)
        sims = qemb @ emb.T
        rankings["dense_pymupdf"] = {q: [int(i) for i in np.argsort(-sims[j], kind="stable")]
                                     for j, q in enumerate(qids)}
        record("dense_pymupdf", cdoc_m, clen_m, rankings["dense_pymupdf"], enc_sec,
               {"model_load_seconds": round(load_sec, 3)})
        hyb = {q: rrf([rankings["bm25_pymupdf"][q], rankings["dense_pymupdf"][q]]) for q in qids}
        record("hybrid_pymupdf", cdoc_m, clen_m, hyb, 0.0)
    except Exception as e:
        res["dense_error"] = "%s: %s" % (type(e).__name__, e)
        print("dense step failed:", res["dense_error"], flush=True)

    try:
        res["grades"] = grade(res)
    except Exception as e:
        res["grades"] = {"error": "%s: %s" % (type(e).__name__, e)}
    write()
    print(json.dumps({"grades": res["grades"], "extraction_totals": tot,
                      "summaries": {k: v["summary"] for k, v in methods.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
