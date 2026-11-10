"""embcheck-1: were the passages in GSMA's default TelcoRetrieve index embedded with the OTel
embedder's QUERY instruction?

GSMA/telco-retrieve-chunks ships prebuilt Chroma indexes for Zindi's TelcoRetrieve Challenge. The
default cell (text_baseline/otel-0.6b) was built with farbodtavakkoli/OTel-Embedding-0.6B (now
served as OTel-Embedding-600M), whose sentence-transformers config sets
default_prompt_name = "Retrieval-query". A plain model.encode(passages) therefore prefixes every
passage with the query instruction. This script reads a random sample of stored vectors straight
out of the HNSW file with HTTP range requests (no 10 GB download), finds each vector's chunk text
in the cell's FTS5 database, re-encodes the text both ways on CPU and reports which way matches.
A control cell (text_baseline/qwen3-embedding-0.6b, base model without a default prompt) is
checked the same way. Pre-registered in PREREGISTRATION-embcheck1.md before any vector was read.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python telco_embcheck.py --data-dir /data/telco --out-dir /out
"""
import argparse
import builtins
import collections
import copyreg
import gc
import hashlib
import json
import os
import pickle
import random
import sqlite3
import struct
import sys
import time

import numpy as np

VERSION = "0.1.0"
REPO = "GSMA/telco-retrieve-chunks"
BASE = "telcoretrievechallenge/fixed-grid/text_baseline"
CELLS = [
    ("otel", {"cell": "otel-0.6b", "model": "farbodtavakkoli/OTel-Embedding-600M", "n": 100}),
    ("control", {"cell": "qwen3-embedding-0.6b", "model": "Qwen/Qwen3-Embedding-0.6B", "n": 40}),
]
SEED = 20261110
THRESH = 0.99
CHUNKS = 1072821
UA = "MV2-Munim-Inc-research (mv2@munimtech.com)"

# hnswlib (chroma fork) persistent header.bin: PERSISTENCE_VERSION int, then size_t x6,
# maxlevel int, enterpoint tableint, size_t x3, mult double, ef_construction size_t = 100 bytes.
HEADER_FMT = "<i6Qii3QdQ"
HEADER_NAMES = ("version", "offset_level0", "max_elements", "cur_element_count",
                "size_data_per_element", "label_offset", "offset_data", "maxlevel",
                "enterpoint_node", "maxM", "maxM0", "M", "mult", "ef_construction")


def parse_header(b):
    if len(b) != struct.calcsize(HEADER_FMT):
        raise ValueError("header is %d bytes, expected %d" % (len(b), struct.calcsize(HEADER_FMT)))
    return dict(zip(HEADER_NAMES, struct.unpack(HEADER_FMT, b)))


def header_dim(hdr):
    return (hdr["label_offset"] - hdr["offset_data"]) // 4


def parse_element(b, hdr):
    """One level-0 element: [count:uint16, flags:uint8, pad, maxM0 x uint32][dim x float32][label:uint64]."""
    if len(b) != hdr["size_data_per_element"]:
        raise ValueError("element is %d bytes, expected %d" % (len(b), hdr["size_data_per_element"]))
    dim = header_dim(hdr)
    return {"links": struct.unpack_from("<H", b, 0)[0], "deleted": bool(b[2] & 1),
            "vector": np.frombuffer(bytes(b), dtype="<f4", count=dim, offset=hdr["offset_data"]).astype(np.float64),
            "label": struct.unpack_from("<Q", b, hdr["label_offset"])[0]}


# ---- restricted unpickler: index_metadata.pickle is untrusted data, so no arbitrary globals ----
class Stub:
    def __new__(cls, *a, **k):
        return object.__new__(cls)

    def __init__(self, *a, **k):
        pass

    def __setstate__(self, state):
        parts = state if isinstance(state, tuple) else (state,)
        for part in parts:
            if isinstance(part, dict):
                self.__dict__.update(part)


SAFE = {("builtins", n): getattr(builtins, n) for n in
        ("dict", "list", "set", "frozenset", "tuple", "int", "float", "str", "bytes", "bool", "object")}
SAFE[("copyreg", "_reconstructor")] = copyreg._reconstructor
SAFE[("collections", "OrderedDict")] = collections.OrderedDict
SAFE[("collections", "defaultdict")] = collections.defaultdict


class SafeUnpickler(pickle.Unpickler):
    def __init__(self, f):
        super().__init__(f)
        self.seen = []

    def find_class(self, module, name):
        self.seen.append("%s.%s" % (module, name))
        if (module, name) in SAFE:
            return SAFE[(module, name)]
        if module == "chromadb" or module.startswith("chromadb."):
            return type(name, (Stub,), {})
        raise pickle.UnpicklingError("global not allowed: %s.%s" % (module, name))


def safe_load(f):
    u = SafeUnpickler(f)
    return u.load(), sorted(set(u.seen))


def _kv_types(d):
    k, v = next(iter(d.items()))
    return type(k), type(v)


def find_label_map(obj):
    """Return (label->id dict, where it came from) from Chroma's PersistentData (or a plain dict)."""
    top = obj.__dict__ if isinstance(obj, Stub) else obj
    if not isinstance(top, dict):
        raise ValueError("unexpected pickle top type %s" % type(top).__name__)
    found = {}
    for name, v in top.items():
        if isinstance(v, dict) and v:
            kt, vt = _kv_types(v)
            found[str(name)] = (kt, vt, v)
    if "label_to_id" in found and found["label_to_id"][0] is int and found["label_to_id"][1] is str:
        return found["label_to_id"][2], "label_to_id"
    for name, (kt, vt, v) in found.items():
        if kt is int and vt is str:
            return v, name
    for name, (kt, vt, v) in found.items():
        if kt is str and vt is int and "label" in name:
            return {b: a for a, b in v.items()}, name + " (inverted)"
    raise ValueError("no label->id map among keys %s" % sorted(map(str, top)))


def pickle_summary(obj):
    top = obj.__dict__ if isinstance(obj, Stub) else obj
    out = {"type": type(obj).__name__}
    if isinstance(top, dict):
        for k, v in top.items():
            if isinstance(v, (int, float, str)) and not isinstance(v, bool):
                out[str(k)] = v
            elif isinstance(v, (dict, list, set)):
                out[str(k) + "_len"] = len(v)
    return out


# ---- chunk text lookup in the cell's FTS5 database (schema discovered, not assumed) ----
SHADOW = ("_data", "_idx", "_content", "_docsize", "_config")


def _preview(row):
    return [v[:120] if isinstance(v, str) else v for v in row] if row else None


def lookup_texts(conn, ids, probes=5):
    ids = list(ids)
    want = set(ids)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    tables = [t for t in tables if not t.startswith("sqlite_") and not t.endswith(SHADOW)]
    schema = {}
    for t in tables:
        cols = [r[1] for r in conn.execute('PRAGMA table_info("%s")' % t)]
        schema[t] = cols
        for c in cols:
            for pid in ids[:probes]:
                row = conn.execute('SELECT * FROM "%s" WHERE "%s" = ? LIMIT 1' % (t, c), (pid,)).fetchone()
                if row is None:
                    continue
                lens = {cols[i]: len(v) for i, v in enumerate(row) if isinstance(v, str) and cols[i] != c}
                if not lens:
                    continue
                txt = max(lens, key=lens.get)
                found = {}
                for k, v in conn.execute('SELECT "%s", "%s" FROM "%s"' % (c, txt, t)):
                    if k in want and k not in found:
                        found[k] = v
                return found, {"table": t, "id_column": c, "text_column": txt, "schema": schema}
    first = {t: _preview(conn.execute('SELECT * FROM "%s" LIMIT 1' % t).fetchone()) for t in tables}
    raise LookupError(json.dumps({"schema": schema, "first_rows": first, "probe_ids": ids[:probes]}))


def classify(cos_doc, cos_query, thresh=THRESH):
    d, q = cos_doc >= thresh, cos_query >= thresh
    return "both" if d and q else "document" if d else "query" if q else "neither"


def cell_summary(samples):
    res = [s for s in samples if s.get("verdict")]
    counts = collections.Counter(s["verdict"] for s in res)
    dq = [s["cos_doc_vs_query"] for s in res]
    return {"sampled": len(samples), "resolved": len(res), "verdicts": dict(counts),
            "median_cos_stored_doc": float(np.median([s["cos_doc"] for s in res])) if res else None,
            "median_cos_stored_query": float(np.median([s["cos_query"] for s in res])) if res else None,
            "median_cos_doc_vs_query": float(np.median(dq)) if dq else None}


def grade(res):
    g = {}
    h = res.get("otel", {}).get("header") or {}
    g["E1"] = bool(h) and h["version"] == 1 and h["size_data_per_element"] == 4236 and \
        header_dim(h) == 1024 and h["max_elements"] == 1064960 and \
        h["cur_element_count"] <= h["max_elements"] < CHUNKS
    so = res.get("otel", {}).get("summary") or {}
    sc = res.get("control", {}).get("summary") or {}
    g["E2"] = so.get("resolved", 0) >= 90
    ro = so.get("resolved", 0)
    g["E3"] = ro > 0 and so["verdicts"].get("query", 0) / ro >= 0.9
    rc = sc.get("resolved", 0)
    g["E4"] = rc >= 30 and sc["verdicts"].get("document", 0) / rc >= 0.9
    g["E5"] = so.get("median_cos_doc_vs_query") is not None and so["median_cos_doc_vs_query"] < 0.95
    return g


# ---- network (only used in the sealed job) ----
def _session():
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def _get(sess, url, **kw):
    last = None
    for attempt in range(4):
        try:
            r = sess.get(url, timeout=180, **kw)
            if r.status_code in (200, 206):
                return r
            last = "HTTP %d %s" % (r.status_code, r.text[:200])
        except Exception as e:  # network hiccup: retry
            last = "%s: %s" % (type(e).__name__, e)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("GET %s failed: %s" % (url, last))


def get_range(sess, url, start, length):
    r = _get(sess, url, headers={"Range": "bytes=%d-%d" % (start, start + length - 1)}, stream=True)
    if r.status_code == 206:
        data = r.content
    elif r.status_code == 200 and int(r.headers.get("Content-Length") or 0) <= (1 << 20):
        data = r.content[start:start + length]  # small file served whole
    else:
        r.close()
        raise RuntimeError("range %d+%d of %s: HTTP %d without a usable range" % (start, length, url, r.status_code))
    if len(data) != length:
        raise RuntimeError("range %d+%d of %s: got %d bytes" % (start, length, url, len(data)))
    return data


def download(sess, url, dest, size):
    if os.path.exists(dest) and os.path.getsize(dest) == size:
        return "cached"
    r = _get(sess, url, stream=True)
    with open(dest + ".part", "wb") as f:
        for block in r.iter_content(1 << 22):
            f.write(block)
    if os.path.getsize(dest + ".part") != size:
        raise RuntimeError("%s: got %d bytes, expected %d" % (url, os.path.getsize(dest + ".part"), size))
    os.replace(dest + ".part", dest)
    return "downloaded"


def _size(e):
    return (e.get("lfs") or {}).get("size", e.get("size"))


def encode_modes(model_id, revision, texts, threads=2):
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(threads)
    m = SentenceTransformer(model_id, revision=revision, device="cpu")
    m.max_seq_length = 1024
    prompts = dict(getattr(m, "prompts", None) or {})
    qname = "Retrieval-query" if "Retrieval-query" in prompts else "query"
    qprompt = prompts[qname]
    dprompt = prompts.get("Retrieval-document", prompts.get("document", ""))
    default_name = getattr(m, "default_prompt_name", None)
    m.default_prompt_name = None  # so that "no prompt" really means no prefix, in every library version
    kw = dict(batch_size=4, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    out = {"document": m.encode(texts, prompt=dprompt, **kw) if dprompt else m.encode(texts, **kw),
           "query": m.encode(texts, prompt=qprompt, **kw)}
    out = {k: np.asarray(v, dtype=np.float64) for k, v in out.items()}
    import sentence_transformers
    info = {"default_prompt_name": default_name, "query_prompt_name": qname, "query_prompt": qprompt,
            "document_prompt": dprompt, "prompt_names": sorted(prompts),
            "sentence_transformers": sentence_transformers.__version__, "torch": torch.__version__}
    del m
    gc.collect()
    return out, info


def run_cell(sess, key, spec, rev, data_dir, fts_conns, log):
    api = "https://huggingface.co/api/datasets/%s/tree/%s/" % (REPO, rev)
    res_url = "https://huggingface.co/datasets/%s/resolve/%s/" % (REPO, rev)
    cell = {"cell": spec["cell"], "model": spec["model"]}
    entries = _get(sess, api + BASE + "/" + spec["cell"] + "/db").json()
    dirs = [e["path"] for e in entries if e.get("type") == "directory"]
    files = {e["path"].rsplit("/", 1)[-1]: e for e in entries if e.get("type") == "file"}
    if len(dirs) != 1:
        raise RuntimeError("%s: expected one segment folder, got %s" % (spec["cell"], dirs))
    seg = dirs[0]
    seg_files = {e["path"].rsplit("/", 1)[-1]: _size(e) for e in _get(sess, api + seg).json() if e.get("type") == "file"}
    cell["segment_files"] = seg_files
    hdr = parse_header(get_range(sess, res_url + seg + "/header.bin", 0, 100))
    cell["header"] = hdr
    cell["data_level0_slots_from_size"] = seg_files.get("data_level0.bin", 0) / hdr["size_data_per_element"]
    log("%s header %s" % (key, hdr))
    # 1. stored vectors at random internal positions
    rng = random.Random("%d-%s" % (SEED, key))
    iids = sorted(rng.sample(range(hdr["cur_element_count"]), min(spec["n"], hdr["cur_element_count"])))
    samples = []
    for iid in iids:
        el = parse_element(get_range(sess, res_url + seg + "/data_level0.bin",
                                     iid * hdr["size_data_per_element"], hdr["size_data_per_element"]), hdr)
        samples.append({"internal_id": iid, "label": el["label"], "deleted": el["deleted"],
                        "_vec": el["vector"]})
    # 2. label -> chunk id from index_metadata.pickle (restricted unpickler)
    meta = os.path.join(data_dir, spec["cell"] + "_index_metadata.pickle")
    cell["metadata_fetch"] = download(sess, res_url + seg + "/index_metadata.pickle", meta, seg_files["index_metadata.pickle"])
    with open(meta, "rb") as f:
        obj, seen = safe_load(f)
    cell["pickle_globals"] = seen
    cell["pickle_summary"] = pickle_summary(obj)
    lmap, cell["label_map_source"] = find_label_map(obj)
    for s in samples:
        s["chunk_id"] = lmap.get(s["label"])
    del obj, lmap
    gc.collect()
    log("%s labels mapped: %d of %d" % (key, sum(1 for s in samples if s["chunk_id"]), len(samples)))
    # 3. chunk text from an FTS5 database (reuse an earlier cell's first; chunk text is shared per strategy)
    ids = [s["chunk_id"] for s in samples if s["chunk_id"] and not s["deleted"]]
    texts, how = {}, None
    for name, conn in fts_conns:
        try:
            texts, how = lookup_texts(conn, ids)
            how["db"] = name
        except LookupError as e:
            how = {"db": name, "error": str(e)[:4000]}
        if len(texts) >= 0.5 * max(1, len(ids)):
            break
    if len(texts) < 0.5 * max(1, len(ids)):
        fts_name = [n for n in files if n.endswith("_fts.db")][0]
        path = os.path.join(data_dir, spec["cell"] + "_fts.db")
        cell["fts_fetch"] = download(sess, res_url + BASE + "/" + spec["cell"] + "/db/" + fts_name, path, _size(files[fts_name]))
        conn = sqlite3.connect(path)  # our own copy in the job's data volume
        fts_conns.append((fts_name, conn))
        texts, how = lookup_texts(conn, ids)
        how["db"] = fts_name
    cell["text_lookup"] = {k: v for k, v in how.items() if k != "schema"}
    cell["fts_schema"] = how.get("schema")
    for s in samples:
        s["text"] = texts.get(s["chunk_id"]) if s["chunk_id"] else None
    # 4. re-encode both ways and compare
    todo = [s for s in samples if s["text"] and not s["deleted"]]
    mrev = _get(sess, "https://huggingface.co/api/models/" + spec["model"]).json()["sha"]
    cell["model_revision"] = mrev
    t0 = time.time()
    enc, cell["prompts"] = encode_modes(spec["model"], mrev, [s["text"] for s in todo]) if todo else ({}, {})
    cell["encode_seconds"] = round(time.time() - t0, 1)
    for i, s in enumerate(todo):
        v = s["_vec"] / np.linalg.norm(s["_vec"])
        d, q = enc["document"][i], enc["query"][i]
        s["cos_doc"], s["cos_query"] = float(v @ d), float(v @ q)
        s["cos_doc_vs_query"] = float(d @ q)
        s["verdict"] = classify(s["cos_doc"], s["cos_query"])
    for s in samples:
        s["vector_norm"] = float(np.linalg.norm(s.pop("_vec")))
        t = s.pop("text", None)
        if t is not None:
            s["text_sha256"] = hashlib.sha256(t.encode("utf-8")).hexdigest()
            s["text_chars"] = len(t)
    cell["samples"] = samples
    cell["summary"] = cell_summary(samples)
    log("%s summary %s" % (key, cell["summary"]))
    return cell


def write_md(res, path):
    g = res.get("grades", {})
    lines = ["# embcheck-1 automatic summary (grade by hand before trusting)", "",
             "Dataset revision: `%s`; script %s; finished %s." % (res.get("dataset_revision"), VERSION, res.get("finished_utc")), ""]
    for key in ("otel", "control"):
        c = res.get(key)
        if not c:
            continue
        h = c.get("header", {})
        lines += ["## %s (%s, %s)" % (key, c["cell"], c["model"]), "",
                  "- header: max_elements %s, cur_element_count %s, size_data_per_element %s, M %s, maxM0 %s" %
                  (h.get("max_elements"), h.get("cur_element_count"), h.get("size_data_per_element"), h.get("M"), h.get("maxM0")),
                  "- pickle: %s" % json.dumps(c.get("pickle_summary")),
                  "- prompts: %s" % json.dumps(c.get("prompts")),
                  "- summary: %s" % json.dumps(c.get("summary")), ""]
    lines += ["## Predictions (automatic)", ""] + ["- %s: %s" % (k, "held" if v else "failed") for k, v in sorted(g.items())]
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
    out_json = os.path.join(a.out_dir, "embcheck1.json")
    t0 = time.time()

    def log(msg):
        print("[%7.1fs] %s" % (time.time() - t0, msg), flush=True)

    sess = _session()
    res = {"version": VERSION, "seed": SEED, "threshold": THRESH, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    res["dataset_revision"] = _get(sess, "https://huggingface.co/api/datasets/" + REPO).json()["sha"]
    fts_conns = []
    status = 0
    for key, spec in CELLS:
        try:
            res[key] = run_cell(sess, key, spec, res["dataset_revision"], a.data_dir, fts_conns, log)
        except Exception as e:
            res[key + "_error"] = "%s: %s" % (type(e).__name__, str(e)[:4000])
            log("%s failed: %s" % (key, res[key + "_error"]))
            status = 3
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
    res["grades"] = grade(res)
    res["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    write_md(res, os.path.join(a.out_dir, "RESULTS-embcheck1-auto.md"))
    log("grades %s" % res["grades"])
    return status


if __name__ == "__main__":
    sys.exit(main())
