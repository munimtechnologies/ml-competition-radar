"""embcheck-2: do the chunks that the query instruction dominates in TelcoRetrieve's default index
crowd the top of the ranking for real telecom questions?

embcheck-1 found that every sampled passage in GSMA's default cell (text_baseline/otel-0.6b) was
embedded WITH the OTel embedder's query instruction, and that for 16 of 100 passages (13 of them
exactly 254 characters long) the stored vector is far from the passage's plain encoding (cosine
0.51-0.67). This script reads 10,000 stored vectors from each of two cells in 40 contiguous blocks
(HTTP range requests), looks up each chunk's length in the cell's FTS5 database, encodes 3GPP
questions from GSMA's public Open Telco TeleQnA test set (MIT) with the cell's own model, and
measures how often 254-character chunks land in the top 10. Pre-registered in
PREREGISTRATION-embcheck2.md before any vector was read.

It reuses telco_embcheck.py 0.1.0 (embcheck-1) unchanged, downloaded from commit 4717478 by
fetch_base.py.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python telco_embcheck2.py --data-dir /data/telco --out-dir /out
"""
import argparse
import gc
import hashlib
import json
import os
import random
import re
import sqlite3
import sys
import time

import numpy as np

import telco_embcheck as e1

VERSION = "0.2.0"
SEED = 20261111
BLOCKS = 40
BLOCK_LEN = 250
K = 10
L254 = 254
LONG_MIN = 500
N_QUESTIONS = 300
DATA_REV = "2ec07608ee2a77a59a3f5995ca3c10e9cba4c976"  # the revision embcheck-1 read
CELLS = [
    ("otel", {"cell": "otel-0.6b", "model": "farbodtavakkoli/OTel-Embedding-600M",
              "rev": "f7755f8465599e0867a91a9c2d75a53d4f030ac8"}),
    ("control", {"cell": "qwen3-embedding-0.6b", "model": "Qwen/Qwen3-Embedding-0.6B",
                 "rev": "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"}),
]
QNA_REPO = "GSMA/ot-lite"
QNA_FILE = "test_teleqna.json"
TAG = re.compile(r"\s*\[([^\[\]]*)\]\s*$")
PREDICTIONS = ("P1", "P2", "P3", "P4", "P5", "P6")


# ---- pure functions (unit-tested offline) ----
def load_questions(raw):
    """TeleQnA JSON bytes -> question texts tagged '[3GPP ...]', tag removed, duplicates dropped."""
    data = json.loads(raw.decode("utf-8"))
    if isinstance(data, dict):
        for k in ("data", "rows", "test"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
    if not isinstance(data, list):
        raise ValueError("unexpected TeleQnA layout: %s" % type(data).__name__)
    out = []
    for r in data:
        q = r.get("question") if isinstance(r, dict) else None
        if not isinstance(q, str):
            continue
        m = TAG.search(q)
        if not m or "3GPP" not in m.group(1):
            continue
        text = q[:m.start()].strip()
        if text:
            out.append(text)
    return list(dict.fromkeys(out))


def pick_questions(questions, n, seed):
    if len(questions) <= n:
        return list(questions)
    rng = random.Random(seed)
    return [questions[i] for i in sorted(rng.sample(range(len(questions)), n))]


def block_starts(n_elements, blocks, block_len, seed):
    """Aligned, non-overlapping blocks of block_len internal ids inside [0, n_elements)."""
    slots = n_elements // block_len
    rng = random.Random(seed)
    return [p * block_len for p in sorted(rng.sample(range(slots), min(blocks, slots)))]


def parse_block(b, hdr, start, count):
    size = hdr["size_data_per_element"]
    if len(b) != size * count:
        raise ValueError("block is %d bytes, expected %d" % (len(b), size * count))
    out = []
    for i in range(count):
        el = e1.parse_element(b[i * size:(i + 1) * size], hdr)
        el["internal_id"] = start + i
        out.append(el)
    return out


def groups(chars):
    c = np.asarray(chars)
    return {"L254": c == L254, "SHORT": c <= L254, "LONG": c >= LONG_MIN}


def topk(qv, sv, k):
    """Indices of the k highest cosines per query row, best first (rows are unit vectors)."""
    s = qv @ sv.T
    idx = np.argpartition(-s, k - 1, axis=1)[:, :k]
    rows = np.arange(s.shape[0])[:, None]
    order = np.argsort(-s[rows, idx], axis=1, kind="stable")
    return idx[rows, order]


def skewness(x):
    x = np.asarray(x, dtype=np.float64)
    sd = x.std()
    return float(((x - x.mean()) ** 3).mean() / sd ** 3) if sd > 0 else 0.0


def hub_stats(top, n, mask):
    flat = top.ravel()
    counts = np.bincount(flat, minlength=n)
    base = float(mask.mean())
    share = float(mask[flat].mean())
    srt = np.sort(counts)[::-1]
    h = max(1, n // 100)
    return {"slots": int(flat.size), "base_rate": base, "topk_share": share,
            "ratio": share / base if base > 0 else None,
            "any_in_topk": float(mask[top].any(axis=1).mean()),
            "top1_share": float(mask[top[:, 0]].mean()),
            "n10_skew": skewness(counts), "n10_max": int(srt[0]),
            "top1pct_slot_share": float(srt[:h].sum() / flat.size),
            "never_retrieved": float((counts == 0).mean())}


def median_or_none(x, mask):
    v = np.asarray(x)[mask]
    return float(np.median(v)) if v.size else None


def grade(res):
    gates = res.get("gates") or {}
    if not (gates.get("GA") and gates.get("GQ")):
        return {p: None for p in PREDICTIONS}
    o, c = res["otel"], res["control"]

    def ratio(cell, mode):
        return cell["hubs"][mode]["L254"]["ratio"]

    g = {}
    g["P1"] = 0.05 <= o["base_rates"]["L254"] <= 0.25
    oq, od, cq = ratio(o, "Q"), ratio(o, "D"), ratio(c, "Q")
    g["P2"] = None if oq is None else oq >= 2.0
    g["P3"] = None if oq is None or cq is None else (cq <= 1.5 and cq < oq)
    g["P4"] = None if oq is None or od is None else od < oq
    ao, ac = o["affinity"], c["affinity"]
    if None in (ao["L254"], ao["LONG"], ac["L254"], ac["LONG"]):
        g["P5"] = None
    else:
        do, dc = ao["L254"] - ao["LONG"], ac["L254"] - ac["LONG"]
        g["P5"] = do >= 0.2 and do > dc
    g["P6"] = o["hubs"]["Q"]["L254"]["n10_skew"] > c["hubs"]["Q"]["L254"]["n10_skew"]
    return g


# ---- model (only in the sealed job) ----
def load_model(model_id, revision, threads=2):
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(threads)
    m = SentenceTransformer(model_id, revision=revision, device="cpu")
    m.max_seq_length = 1024
    prompts = dict(getattr(m, "prompts", None) or {})
    qname = "Retrieval-query" if "Retrieval-query" in prompts else "query"
    import sentence_transformers
    info = {"default_prompt_name": getattr(m, "default_prompt_name", None), "query_prompt_name": qname,
            "query_prompt": prompts[qname], "document_prompt": prompts.get("Retrieval-document", prompts.get("document", "")),
            "dtype": str(next(m.parameters()).dtype),
            "sentence_transformers": sentence_transformers.__version__, "torch": torch.__version__}
    m.default_prompt_name = None  # "no prompt" must really mean no prefix
    return m, info


def encode(m, texts, prompt):
    kw = dict(batch_size=16, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    v = m.encode(texts, prompt=prompt, **kw) if prompt else m.encode(texts, **kw)
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


# ---- one cell ----
def run_cell(sess, key, spec, data_dir, questions, log):
    api = "https://huggingface.co/api/datasets/%s/tree/%s/" % (e1.REPO, DATA_REV)
    res_url = "https://huggingface.co/datasets/%s/resolve/%s/" % (e1.REPO, DATA_REV)
    cell = {"cell": spec["cell"], "model": spec["model"], "model_revision": spec["rev"]}
    entries = e1._get(sess, api + e1.BASE + "/" + spec["cell"] + "/db").json()
    dirs = [x["path"] for x in entries if x.get("type") == "directory"]
    files = {x["path"].rsplit("/", 1)[-1]: x for x in entries if x.get("type") == "file"}
    if len(dirs) != 1:
        raise RuntimeError("%s: expected one segment folder, got %s" % (spec["cell"], dirs))
    seg = dirs[0]
    seg_files = {x["path"].rsplit("/", 1)[-1]: e1._size(x) for x in e1._get(sess, api + seg).json() if x.get("type") == "file"}
    hdr = e1.parse_header(e1.get_range(sess, res_url + seg + "/header.bin", 0, 100))
    cell["header"] = {k: hdr[k] for k in ("max_elements", "cur_element_count", "size_data_per_element")}
    size = hdr["size_data_per_element"]
    starts = block_starts(hdr["cur_element_count"], BLOCKS, BLOCK_LEN, SEED)
    cell["block_starts"] = starts
    els = []
    for st in starts:
        els.extend(parse_block(e1.get_range(sess, res_url + seg + "/data_level0.bin", st * size, BLOCK_LEN * size),
                               hdr, st, BLOCK_LEN))
    log("%s read %d stored vectors" % (key, len(els)))
    meta = os.path.join(data_dir, spec["cell"] + "_index_metadata.pickle")
    cell["metadata_fetch"] = e1.download(sess, res_url + seg + "/index_metadata.pickle", meta, seg_files["index_metadata.pickle"])
    with open(meta, "rb") as f:
        obj, _ = e1.safe_load(f)
    lmap, cell["label_map_source"] = e1.find_label_map(obj)
    for el in els:
        el["chunk_id"] = lmap.get(el["label"])
    del obj, lmap
    gc.collect()
    fts_name = [n for n in files if n.endswith("_fts.db")][0]
    path = os.path.join(data_dir, spec["cell"] + "_fts.db")
    cell["fts_fetch"] = e1.download(sess, res_url + e1.BASE + "/" + spec["cell"] + "/db/" + fts_name, path, e1._size(files[fts_name]))
    conn = sqlite3.connect(path)
    texts, how = e1.lookup_texts(conn, [el["chunk_id"] for el in els if el["chunk_id"] and not el["deleted"]])
    conn.close()
    cell["text_lookup"] = {k: v for k, v in how.items() if k != "schema"}
    keep = [el for el in els if el["chunk_id"] in texts and not el["deleted"]]
    cell["sampled"], cell["resolved"] = len(els), len(keep)
    log("%s resolved %d of %d" % (key, len(keep), len(els)))
    sv = np.stack([el["vector"] for el in keep])
    sv /= np.linalg.norm(sv, axis=1, keepdims=True)
    chars = [len(texts[el["chunk_id"]]) for el in keep]
    del texts
    gc.collect()
    grp = groups(chars)
    cell["base_rates"] = {g: float(v.mean()) for g, v in grp.items()}
    cell["chars_quantiles"] = {str(q): float(np.quantile(chars, q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)}
    t0 = time.time()
    m, cell["prompts"] = load_model(spec["model"], spec["rev"])
    qv = {"Q": encode(m, questions, cell["prompts"]["query_prompt"]),
          "D": encode(m, questions, cell["prompts"]["document_prompt"])}
    inst = encode(m, [""], cell["prompts"]["query_prompt"])[0]
    del m
    gc.collect()
    cell["encode_seconds"] = round(time.time() - t0, 1)
    aff = sv @ inst
    cell["affinity"] = {g: median_or_none(aff, grp[g]) for g in ("L254", "SHORT", "LONG")}
    cell["affinity"]["all"] = float(np.median(aff))
    cell["hubs"] = {}
    for mode in ("Q", "D"):
        top = topk(qv[mode], sv, K)
        cell["hubs"][mode] = {g: hub_stats(top, len(keep), grp[g]) for g in ("L254", "SHORT")}
        if mode == "Q":
            counts = np.bincount(top.ravel(), minlength=len(keep))
            cell["top_hubs_Q"] = [{"internal_id": keep[i]["internal_id"], "chunk_id": keep[i]["chunk_id"],
                                   "chars": chars[i], "n10": int(counts[i]), "instruction_cos": float(aff[i])}
                                  for i in np.argsort(-counts, kind="stable")[:20]]
    log("%s hubs %s" % (key, json.dumps({md: cell["hubs"][md]["L254"] for md in cell["hubs"]})))
    return cell


def write_md(res, path):
    lines = ["# embcheck-2 automatic summary (grade by hand before trusting)", "",
             "Script %s; dataset revision `%s`; questions %s; finished %s." %
             (VERSION, DATA_REV, res.get("questions", {}).get("used"), res.get("finished_utc")),
             "Gates: %s" % json.dumps(res.get("gates")), ""]
    for key, _ in CELLS:
        c = res.get(key)
        if not c:
            lines += ["## %s: %s" % (key, res.get(key + "_error")), ""]
            continue
        lines += ["## %s (%s)" % (key, c["cell"]), "",
                  "- resolved %d of %d; dtype %s; encode %.0f s" % (c["resolved"], c["sampled"], c["prompts"].get("dtype"), c["encode_seconds"]),
                  "- base rates %s" % json.dumps(c["base_rates"]),
                  "- instruction affinity (median cosine) %s" % json.dumps(c["affinity"]), ""]
        lines += ["| query mode | group | base rate | top-10 share | ratio | any in top-10 | top-1 share | N10 skew | N10 max |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for md in ("Q", "D"):
            for g in ("L254", "SHORT"):
                h = c["hubs"][md][g]
                lines.append("| %s | %s | %.4f | %.4f | %s | %.3f | %.3f | %.2f | %d |" % (
                    md, g, h["base_rate"], h["topk_share"], "%.2f" % h["ratio"] if h["ratio"] is not None else "-",
                    h["any_in_topk"], h["top1_share"], h["n10_skew"], h["n10_max"]))
        lines.append("")
    lines += ["## Predictions (automatic)", ""] + ["- %s: %s" % (k, {True: "held", False: "failed", None: "not graded"}[v])
                                                  for k, v in sorted((res.get("grades") or {}).items())]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.data_dir, exist_ok=True)
    os.makedirs(a.out_dir, exist_ok=True)
    os.environ.setdefault("HF_HOME", os.path.join(a.data_dir, "hf"))
    out_json = os.path.join(a.out_dir, "embcheck2.json")
    t0 = time.time()

    def log(msg):
        print("[%7.1fs] %s" % (time.time() - t0, msg), flush=True)

    sess = e1._session()
    res = {"version": VERSION, "base_version": e1.VERSION, "seed": SEED, "k": K, "dataset_revision": DATA_REV,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    qrev = e1._get(sess, "https://huggingface.co/api/datasets/" + QNA_REPO).json()["sha"]
    raw = e1._get(sess, "https://huggingface.co/datasets/%s/resolve/%s/%s" % (QNA_REPO, qrev, QNA_FILE)).content
    allq = load_questions(raw)
    questions = pick_questions(allq, N_QUESTIONS, SEED)
    res["questions"] = {"repo": QNA_REPO, "revision": qrev, "file": QNA_FILE, "sha256": hashlib.sha256(raw).hexdigest(),
                        "tagged_3gpp": len(allq), "used": len(questions)}
    log("questions %s" % res["questions"])
    status = 0
    for key, spec in CELLS:
        try:
            res[key] = run_cell(sess, key, spec, a.data_dir, questions, log)
        except Exception as e:
            res[key + "_error"] = "%s: %s" % (type(e).__name__, str(e)[:4000])
            log("%s failed: %s" % (key, res[key + "_error"]))
            status = 3
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
    res["gates"] = {"GA": all(res.get(k, {}).get("resolved", 0) >= 9000 for k, _ in CELLS),
                    "GQ": len(questions) >= N_QUESTIONS}
    res["grades"] = grade(res)
    res["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    write_md(res, os.path.join(a.out_dir, "RESULTS-embcheck2-auto.md"))
    log("grades %s" % res["grades"])
    return status


if __name__ == "__main__":
    sys.exit(main())
