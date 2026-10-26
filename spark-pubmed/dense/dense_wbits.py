"""Weighted one-bit scoring for the one-bit MedCPT PubMed index of spark44 (job spark46-wbits,
first filed as -v1).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

spark44 kept one bit per dimension (bit_j = 1 where x_j > mu_j) and scored a query q as q . b.
That treats every dimension as if it moved by the same amount. On chunk 36 only 54% of the exact
float top 10 landed in the bit top 100 (RESULTS-spark44.md). The least-squares reading of one bit
is x_j ~ lo_j + b_j (hi_j - lo_j), with lo_j / hi_j the mean of x_j at or below / above mu_j, so

    q . x_hat = q . lo + (q * w) . b,    w = hi - lo,

and ranking by (q * w) . b needs no new index: dense_search.py's search, given the queries q * w,
scores exactly that (the asymmetric distance of Gordo et al. 2014 for this one-bit code).

This script downloads chunk 36's floats once more (size checked by dense_build.download), checks
that binarising them with the index's mu.npy gives the stored bits_36.npy, computes lo, hi and w,
and measures on chunk 36, against exact float search, three ways of scoring:

    plain     q . b                  (what spark44 used; must repeat its fidelity record)
    weighted  (q * w) . b            (same bits)
    two_bit   q . x_hat, x_hat = the mean of x_j within its quartile cell (thresholds from every
              STRIDE-th row of chunk 36); fidelity only, it would need a new 2-bit index

It then writes the weighted queries (OUT/wdense/queries.npy plus a copy of queries.json), so the
next job step searches the whole index with dense_search.py unchanged, and keeps lo, hi, w, the
thresholds and cell means in KEEP/wbits_36.npz. The floats are deleted at the end.

dense_build.py is loaded from --code-dir (fetch_code.py group "dense"), so the bits are unpacked
and the top-k and overlap measures computed by the same code spark44 ran.

  python dense_wbits.py --code-dir D --index-dir D --tmp-dir D --queries-dir D --out-dir D --keep-dir D
"""
import argparse
import importlib.util
import json
import os
import shutil
import sys
import time

import numpy as np

VERSION = "0.1.0"
CHUNK = 36
STRIDE = 10
QUARTILES = (0.25, 0.5, 0.75)
MIN_FREE = 8 * 1024 ** 3
VARIANTS = ("plain", "weighted", "two_bit")


def load_build(code_dir):
    spec = importlib.util.spec_from_file_location("dense_build", os.path.join(code_dir, "dense_build.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cond_means(emb, mu, block):
    """Per dimension: mean at or below mu (lo), mean above mu (hi), and the share above mu."""
    n, d = emb.shape
    s_hi, n_hi, s_all = np.zeros(d), np.zeros(d), np.zeros(d)
    for s in range(0, n, block):
        x = np.asarray(emb[s:s + block], dtype=np.float32)
        up = x > mu
        x = x.astype(np.float64)
        s_hi += np.where(up, x, 0.0).sum(axis=0)
        n_hi += up.sum(axis=0)
        s_all += x.sum(axis=0)
    hi = s_hi / np.maximum(n_hi, 1)
    lo = (s_all - s_hi) / np.maximum(n - n_hi, 1)
    return lo.astype(np.float32), hi.astype(np.float32), n_hi / max(1, n)


def quartile_thresholds(emb, stride=STRIDE, qs=QUARTILES):
    """3 x d thresholds: per-dimension quantiles of every stride-th row."""
    return np.quantile(np.asarray(emb[::stride], dtype=np.float32), qs, axis=0).astype(np.float32)


def codes(x, t):
    """Two-bit code of each value: how many of the three thresholds it exceeds (0-3)."""
    return (x > t[0]).astype(np.uint8) + (x > t[1]) + (x > t[2])


def code_means(emb, t, block):
    """4 x d cell means; an empty cell takes [t0, (t0+t1)/2, (t1+t2)/2, t2][cell]. Also the counts."""
    n, d = emb.shape
    sums, cnt = np.zeros((4, d)), np.zeros((4, d))
    for s in range(0, n, block):
        x = np.asarray(emb[s:s + block], dtype=np.float32)
        c = codes(x, t)
        x = x.astype(np.float64)
        for k in range(4):
            m = c == k
            sums[k] += np.where(m, x, 0.0).sum(axis=0)
            cnt[k] += m.sum(axis=0)
    fallback = np.stack([t[0], (t[0] + t[1]) / 2, (t[1] + t[2]) / 2, t[2]]).astype(np.float64)
    cm = np.where(cnt > 0, sums / np.maximum(cnt, 1), fallback)
    return cm.astype(np.float32), cnt


def fidelity(build, emb, bits, q, w, t, cm, block, k_exact=100, k_approx=1000):
    """Exact float top-k against each variant's top-k within one chunk (row numbers as ids), with
    the four measures dense_build.fidelity reports."""
    q = np.asarray(q, dtype=np.float32)
    n, d = emb.shape
    qt = np.ascontiguousarray(q.T)
    qwt = np.ascontiguousarray((q * np.asarray(w, dtype=np.float32)).T)
    idx = np.arange(d)
    ex = build.TopK(len(q), k_exact)
    tops = {v: build.TopK(len(q), k_approx) for v in VARIANTS}
    for s in range(0, n, block):
        ids = np.arange(s, min(n, s + block))
        x = np.asarray(emb[s:s + block], dtype=np.float32)
        b = build.unpack(bits[s:s + block], d)
        ex.add(x @ qt, ids)
        tops["plain"].add(b @ qt, ids)
        tops["weighted"].add(b @ qwt, ids)
        tops["two_bit"].add(cm[codes(x, t), idx] @ qt, ids)
    e = ex.result()[0]
    out = {}
    for v in VARIANTS:
        a = tops[v].result()[0]
        out[v] = {"overlap10": build.share(e, a, 10, 10), "overlap100": build.share(e, a, 100, 100),
                  "exact10_in_bits100": build.share(e, a, 10, 100),
                  "exact100_in_bits1000": build.share(e, a, 100, 1000)}
    return out


def bits_check(build, emb, bits, mu, block):
    """Rows whose stored bits differ from binarise(emb, mu)."""
    bad = 0
    for s in range(0, emb.shape[0], block):
        got = build.binarise(emb[s:s + block], mu)
        bad += int(np.count_nonzero(np.any(got != np.asarray(bits[s:s + block]), axis=1)))
    return bad


def stats(v):
    v = np.asarray(v, dtype=np.float64)
    return {"min": round(float(v.min()), 5), "median": round(float(np.median(v)), 5),
            "max": round(float(v.max()), 5)}


def run(code_dir, index_dir, tmp_dir, queries_dir, out_dir, keep_dir, chunk=CHUNK, stride=STRIDE,
        min_free=MIN_FREE, open_url=None, disk_free=lambda p: shutil.disk_usage(p).free):
    build = load_build(code_dir)
    open_url = open_url or build.opener
    t0 = time.time()
    for p in (tmp_dir, out_dir, keep_dir):
        os.makedirs(p, exist_ok=True)
    rep = {"version": VERSION, "dense_build": build.VERSION, "chunk": chunk, "stride": stride,
           "problems": []}
    free = disk_free(tmp_dir)
    if free < min_free:
        rep["problems"].append("not started: %d bytes free, need %d" % (free, min_free))
        return rep
    name = "embeds_chunk_%d.npy" % chunk
    emb_path = os.path.join(tmp_dir, name)
    rep["download"] = build.download(build.BASE + name, emb_path, open_url)
    if rep["download"]["status"] != "ok":
        build.remove(emb_path)
        rep["problems"].append("download: %s" % (rep["download"].get("error") or rep["download"]["status"]))
        return rep
    emb = np.load(emb_path, mmap_mode="r")
    bits = np.load(os.path.join(index_dir, "bits_%d.npy" % chunk), mmap_mode="r")
    mu = np.load(os.path.join(index_dir, "mu.npy"))
    q = np.load(os.path.join(queries_dir, "queries.npy"))
    d = build.DIM if emb.ndim != 2 else emb.shape[1]
    if (emb.dtype != np.float32 or emb.ndim != 2 or emb.shape[0] != bits.shape[0]
            or bits.shape[1] * 8 != d or mu.shape != (d,) or q.ndim != 2 or q.shape[1] != d):
        rep["problems"].append("shapes: embeddings %s %s, bits %s, mu %s, queries %s"
                               % (emb.dtype, emb.shape, bits.shape, mu.shape, q.shape))
    else:
        block = build.BLOCK
        rep.update(rows=int(emb.shape[0]), queries=int(q.shape[0]))
        rep["bits_mismatch_rows"] = bits_check(build, emb, bits, mu, block)
        if rep["bits_mismatch_rows"]:
            rep["problems"].append("%d rows of bits_%d.npy differ from binarising the floats with mu.npy"
                                   % (rep["bits_mismatch_rows"], chunk))
        lo, hi, share_hi = cond_means(emb, mu, block)
        w = hi - lo
        t = quartile_thresholds(emb, stride)
        cm, cnt = code_means(emb, t, block)
        order = np.argsort(-w)
        rep.update(w=stats(w), w_max_over_min=round(float(w.max() / w.min()), 3) if w.min() > 0 else None,
                   w_top5_dims=[int(i) for i in order[:5]], share_above_mu=stats(share_hi),
                   empty_code_cells=int(np.count_nonzero(cnt == 0)))
        rep["fidelity"] = fidelity(build, emb, bits, q, w, t, cm, block)
        np.savez(os.path.join(keep_dir, "wbits_%d.npz" % chunk), lo=lo, hi=hi, w=w, mu=mu, t=t, cm=cm)
        wq = os.path.join(out_dir, "wdense")
        os.makedirs(wq, exist_ok=True)
        np.save(os.path.join(wq, "queries.npy"), (q * w).astype(np.float32))
        shutil.copyfile(os.path.join(queries_dir, "queries.json"), os.path.join(wq, "queries.json"))
    del emb, bits
    build.remove(emb_path)
    rep["seconds"] = round(time.time() - t0, 1)
    return rep


def main(argv=None, open_url=None):
    ap = argparse.ArgumentParser()
    for a in ("--code-dir", "--index-dir", "--tmp-dir", "--queries-dir", "--out-dir", "--keep-dir"):
        ap.add_argument(a, required=True)
    a = ap.parse_args(argv)
    rep = run(a.code_dir, a.index_dir, a.tmp_dir, a.queries_dir, a.out_dir, a.keep_dir, open_url=open_url)
    rep["ok"] = not rep["problems"]
    with open(os.path.join(a.out_dir, "wbits.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
