"""One-bit index of NCBI's precomputed MedCPT PubMed embeddings, for a dense first stage in SPARK
Task 1 (job spark44-dense, first filed as -v1).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

NCBI publishes MedCPT Article Encoder embeddings of PubMed (ftp.ncbi.nlm.nih.gov/pub/lu/MedCPT/
pubmed_embeddings/; Jin et al. 2023): chunk k holds the articles whose PMIDs run from k million to
just under k+1 million, as embeds_chunk_k.npy (float32, N x 768, about 2.8 GB) and
pmids_chunk_k.json (N PMIDs, same order). The 38 chunks (0-37) take about 103 GiB as float32.
This keeps one bit per dimension instead (96 bytes per article):

    bit_j = 1 if x_j > mu_j else 0,   mu = per-dimension mean of the first chunk built (36)

dense_search.py scores a query q against bits b as q . b, which ranks articles exactly as
q . (2b - 1) does (the two differ by sum(q), a per-query constant). Each chunk is downloaded to a
.part file (size checked against Content-Length), checked (float32, N x 768, N PMIDs), binarised
in blocks, written as bits_k.npy (uint8, N x 96) and pmids_k.npy (int64), and the download is
deleted, so at most one chunk's floats are on disk at a time. A chunk whose two outputs exist is
kept, so a rerun resumes. The build stops if the index folder has under 8 GiB free.

With --queries Q.npy, the first chunk also measures what one bit per dimension loses: for each
query, the exact float top-k within that chunk against the bit-score top-k (overlap@10,
overlap@100, and the share of the exact top 10 / top 100 inside the bit top 100 / top 1,000).

0.1.1 (after spark44-dense-v1 was stopped by its host during the build): the fidelity record is
saved next to the index (fidelity_k.json, with the sha256 of the queries). When the first chunk
is kept from a stopped run, its saved record is reused if the queries match; otherwise its floats
are downloaded once more and compared with the kept bits. Kept chunks now count towards
pmid_max and out_of_span, files left in the download folder by a stopped run are removed first,
and one progress line per chunk goes to stderr.

  python dense_build.py --index-dir D --tmp-dir D --out-dir D [--queries Q.npy]
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request

import numpy as np

VERSION = "0.1.1"
BASE = "https://ftp.ncbi.nlm.nih.gov/pub/lu/MedCPT/pubmed_embeddings/"
CHUNKS = tuple(range(38))
FIRST = 36
DIM = 768
SPAN = 1000000
BLOCK = 50000
MIN_FREE = 8 * 1024 ** 3
UA = "MV2-Munim-spark-dense/0.1 (mv2@munimtech.com)"


def opener(url, timeout=300):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout)


def download(url, path, open_url=opener, tries=3):
    """url -> path through path + '.part'; the size must equal Content-Length when one is sent."""
    part = path + ".part"
    rec = {"url": url}
    for attempt in range(1, tries + 1):
        t0 = time.time()
        try:
            with open_url(url) as resp, open(part, "wb") as f:
                want = resp.headers.get("Content-Length")
                for block in iter(lambda: resp.read(1 << 23), b""):
                    f.write(block)
        except OSError as e:
            rec.update(status="error", error="%s: %s" % (type(e).__name__, e), attempts=attempt)
            continue
        got = os.path.getsize(part)
        rec.update(bytes=got, content_length=int(want) if want else None, attempts=attempt,
                   seconds=round(time.time() - t0, 1))
        if want is None or got == int(want):
            os.replace(part, path)
            rec["status"] = "ok"
            return rec
        rec["status"] = "short"
    if os.path.exists(part):
        os.remove(part)
    return rec


def remove(*paths):
    for p in paths:
        if os.path.exists(p):
            os.remove(p)


def binarise(x, mu):
    """One bit per dimension, 1 where x > mu, packed 8 to a byte (np.packbits order)."""
    return np.packbits(np.asarray(x, dtype=np.float32) > mu, axis=1)


def unpack(bits, dim=DIM):
    """Packed bits -> float32 matrix of 0s and 1s, rows x dim."""
    return np.unpackbits(np.asarray(bits), axis=1, count=dim).astype(np.float32)


def mean_rows(emb, block=BLOCK):
    tot = np.zeros(emb.shape[1], dtype=np.float64)
    for s in range(0, emb.shape[0], block):
        tot += np.asarray(emb[s:s + block], dtype=np.float64).sum(axis=0)
    return (tot / max(1, emb.shape[0])).astype(np.float32)


class TopK:
    """Running top-k (largest score first) per query, fed one block of rows at a time."""

    def __init__(self, queries, k):
        self.k = k
        self.scores = np.zeros((queries, 0), dtype=np.float32)
        self.ids = np.zeros((queries, 0), dtype=np.int64)

    def add(self, block_scores, block_ids):
        """block_scores: rows x queries; block_ids: one id per row."""
        s = np.concatenate([self.scores, np.asarray(block_scores, dtype=np.float32).T], axis=1)
        ids = np.broadcast_to(np.asarray(block_ids, dtype=np.int64), (s.shape[0], len(block_ids)))
        i = np.concatenate([self.ids, ids], axis=1)
        if s.shape[1] > self.k:
            keep = np.argpartition(-s, self.k - 1, axis=1)[:, :self.k]
            s = np.take_along_axis(s, keep, axis=1)
            i = np.take_along_axis(i, keep, axis=1)
        self.scores, self.ids = s, i

    def result(self):
        """(ids, scores), each queries x k, best first; equal scores go to the smaller id."""
        order = np.lexsort((self.ids, -self.scores), axis=-1)
        return np.take_along_axis(self.ids, order, 1), np.take_along_axis(self.scores, order, 1)


def share(a, b, ka, kb):
    """Mean over rows of |a[:ka] & b[:kb]| / |a[:ka]|."""
    vals = [len(set(a[i, :ka].tolist()) & set(b[i, :kb].tolist())) / max(1, len(a[i, :ka]))
            for i in range(len(a))]
    return round(float(np.mean(vals)), 4) if vals else None


def fidelity(emb, bits, queries, dim=DIM, block=BLOCK, k_exact=100, k_bits=1000):
    """Exact float top-k against bit-score top-k within one chunk (row numbers as ids)."""
    q = np.asarray(queries, dtype=np.float32)
    qt = np.ascontiguousarray(q.T)
    ex, bt = TopK(len(q), k_exact), TopK(len(q), k_bits)
    for s in range(0, emb.shape[0], block):
        ids = np.arange(s, min(emb.shape[0], s + block))
        ex.add(np.asarray(emb[s:s + block], dtype=np.float32) @ qt, ids)
        bt.add(unpack(bits[s:s + block], dim) @ qt, ids)
    e, b = ex.result()[0], bt.result()[0]
    return {"queries": int(len(q)), "rows": int(emb.shape[0]),
            "overlap10": share(e, b, 10, 10), "overlap100": share(e, b, 100, 100),
            "exact10_in_bits100": share(e, b, 10, 100), "exact100_in_bits1000": share(e, b, 100, 1000)}


def qdigest(queries):
    return hashlib.sha256(np.ascontiguousarray(queries, dtype=np.float32).tobytes()).hexdigest()


def save_fidelity(index_dir, k, queries, fid):
    path = os.path.join(index_dir, "fidelity_%d.json" % k)
    with open(path + ".part", "w", encoding="utf-8") as f:
        json.dump({"queries_sha256": qdigest(queries), "fidelity": fid}, f)
    os.replace(path + ".part", path)


def pmid_stats(pmids, k):
    n = len(pmids)
    return {"n": n, "pmid_min": int(pmids.min()) if n else None, "pmid_max": int(pmids.max()) if n else None,
            "out_of_span": int(np.count_nonzero(pmids // SPAN != k))}


def kept_fidelity(k, index_dir, tmp_dir, queries, base=BASE, open_url=opener, dim=DIM, block=BLOCK):
    """Fidelity of a chunk an earlier, stopped run built: its saved record if the queries match,
    else the floats are downloaded once more and compared with the kept bits."""
    path = os.path.join(index_dir, "fidelity_%d.json" % k)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        if saved.get("queries_sha256") == qdigest(queries):
            return {"fidelity": saved["fidelity"], "fidelity_source": "saved"}
    emb_path = os.path.join(tmp_dir, "embeds_chunk_%d.npy" % k)
    got = download(base + os.path.basename(emb_path), emb_path, open_url)
    out = {"fidelity_download": got}
    if got["status"] != "ok":
        remove(emb_path)
        out["problems"] = ["fidelity: %s: %s" % (os.path.basename(emb_path), got.get("error") or got["status"])]
        return out
    emb = np.load(emb_path, mmap_mode="r")
    bits = np.load(os.path.join(index_dir, "bits_%d.npy" % k), mmap_mode="r")
    if emb.dtype != np.float32 or emb.shape != (bits.shape[0], dim):
        out["problems"] = ["fidelity: embeddings are %s %s, kept bits have %d rows"
                           % (emb.dtype, emb.shape, bits.shape[0])]
    else:
        out.update(fidelity=fidelity(emb, bits, queries, dim, block), fidelity_source="recomputed")
        save_fidelity(index_dir, k, queries, out["fidelity"])
    del emb, bits
    remove(emb_path)
    return out


def build_chunk(k, index_dir, tmp_dir, mu, queries=None, base=BASE, open_url=opener, dim=DIM,
                block=BLOCK):
    """Download, check and binarise chunk k. Returns (record, mu); mu is set from this chunk if None."""
    bits_path = os.path.join(index_dir, "bits_%d.npy" % k)
    pmids_path = os.path.join(index_dir, "pmids_%d.npy" % k)
    rec = {"chunk": k}
    if os.path.exists(bits_path) and os.path.exists(pmids_path):
        rec.update(pmid_stats(np.load(pmids_path), k), status="kept")
        if queries is not None:
            rec.update(kept_fidelity(k, index_dir, tmp_dir, queries, base, open_url, dim, block))
        return rec, mu
    emb_path = os.path.join(tmp_dir, "embeds_chunk_%d.npy" % k)
    ids_path = os.path.join(tmp_dir, "pmids_chunk_%d.json" % k)
    rec["downloads"] = [download(base + os.path.basename(p), p, open_url) for p in (ids_path, emb_path)]
    bad = ["%s: %s" % (d["url"].rsplit("/", 1)[-1], d.get("error") or d["status"])
           for d in rec["downloads"] if d["status"] != "ok"]
    if bad:
        remove(emb_path, ids_path)
        rec.update(status="error", problems=bad)
        return rec, mu
    t0 = time.time()
    emb = np.load(emb_path, mmap_mode="r")
    with open(ids_path, encoding="utf-8") as f:
        pmids = np.array([int(p) for p in json.load(f)], dtype=np.int64)
    problems = []
    if emb.dtype != np.float32 or emb.ndim != 2 or emb.shape[1] != dim:
        problems.append("embeddings are %s %s, expected float32 N x %d" % (emb.dtype, emb.shape, dim))
    elif emb.shape[0] != len(pmids):
        problems.append("%d vectors but %d PMIDs" % (emb.shape[0], len(pmids)))
    if problems:
        del emb
        remove(emb_path, ids_path)
        rec.update(status="error", problems=problems)
        return rec, mu
    n = len(pmids)
    rec.update(pmid_stats(pmids, k))
    if mu is None:
        mu = mean_rows(emb, block)
        np.save(os.path.join(index_dir, "mu.npy"), mu)
        rec["mu_from"] = k
    with open(pmids_path + ".part", "wb") as f:
        np.save(f, pmids)
    out = np.lib.format.open_memmap(bits_path + ".part", mode="w+", dtype=np.uint8, shape=(n, dim // 8))
    for s in range(0, n, block):
        out[s:s + block] = binarise(emb[s:s + block], mu)
    out.flush()
    del out
    os.replace(pmids_path + ".part", pmids_path)
    os.replace(bits_path + ".part", bits_path)
    if queries is not None:
        bits = np.load(bits_path, mmap_mode="r")
        rec["fidelity"] = fidelity(emb, bits, queries, dim, block)
        save_fidelity(index_dir, k, queries, rec["fidelity"])
        del bits
    del emb
    remove(emb_path, ids_path)
    rec.update(status="built", seconds=round(time.time() - t0, 1))
    return rec, mu


def clear_stale(index_dir, tmp_dir):
    """Remove what a stopped run left: every file in the download folder, and .part files in the
    index folder. Returns how many files were removed."""
    stale = [os.path.join(tmp_dir, n) for n in os.listdir(tmp_dir)]
    stale += [os.path.join(index_dir, n) for n in os.listdir(index_dir) if n.endswith(".part")]
    stale = [p for p in stale if os.path.isfile(p)]
    remove(*stale)
    return len(stale)


def build(index_dir, tmp_dir, chunks=CHUNKS, first=FIRST, queries=None, base=BASE, open_url=opener,
          dim=DIM, block=BLOCK, min_free=MIN_FREE, disk_free=lambda p: shutil.disk_usage(p).free):
    os.makedirs(index_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    stale = clear_stale(index_dir, tmp_dir)
    mu_path = os.path.join(index_dir, "mu.npy")
    mu = np.load(mu_path) if os.path.exists(mu_path) else None
    order = [first] + [k for k in chunks if k != first]
    recs, problems, t0 = [], [], time.time()
    for k in order:
        free = disk_free(index_dir)
        if free < min_free:
            problems.append("chunk %d not started: %d bytes free, need %d" % (k, free, min_free))
            break
        rec, mu = build_chunk(k, index_dir, tmp_dir, mu, queries if k == first else None, base,
                              open_url, dim, block)
        recs.append(rec)
        print(json.dumps({x: rec[x] for x in ("chunk", "status", "n", "seconds", "fidelity_source")
                          if x in rec}), file=sys.stderr, flush=True)
        problems += ["chunk %d: %s" % (k, p) for p in rec.get("problems", [])]
        if mu is None:
            problems.append("no mean vector: chunk %d failed, so no other chunk is built" % k)
            break
    done = [r for r in recs if r["status"] in ("built", "kept")]
    vectors = sum(r["n"] for r in done)
    fid = [r["fidelity"] for r in recs if "fidelity" in r]
    return {"version": VERSION, "base": base, "dim": dim, "mu_chunk": first, "chunks": len(order),
            "built": sum(r["status"] == "built" for r in recs),
            "kept": sum(r["status"] == "kept" for r in recs), "vectors": vectors,
            "bits_bytes": vectors * (dim // 8),
            "out_of_span": sum(r.get("out_of_span", 0) for r in done),
            "pmid_max": max((r["pmid_max"] for r in done if r.get("pmid_max") is not None), default=None),
            "fidelity": fid[0] if fid else None, "stale_files_removed": stale,
            "seconds": round(time.time() - t0, 1),
            "problems": problems, "ok": not problems and len(done) == len(order), "records": recs}


def main(argv=None, open_url=opener):
    ap = argparse.ArgumentParser()
    ap.add_argument("--index-dir", required=True)
    ap.add_argument("--tmp-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--queries")
    a = ap.parse_args(argv)
    q = np.load(a.queries) if a.queries else None
    rep = build(a.index_dir, a.tmp_dir, queries=q, open_url=open_url)
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "build.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "records"}, indent=1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
