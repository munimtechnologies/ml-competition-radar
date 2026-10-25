"""Dense first stage for SPARK Task 1 (job spark44-dense-v1): encode questions with NCBI's MedCPT
Query Encoder and score them against dense_build.py's one-bit index of NCBI's precomputed MedCPT
article embeddings.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

  fetch-model --code-dir D --model-dir D --out-dir D
      the query encoder at one pinned commit, every file checked against the Hugging Face tree
      (fetch_model.py from --code-dir, rerank @ 99ade999); writes OUT/fetch_qenc.json
  encode --model-dir D --out-dir D --leg NAME=F [--leg ...]
      every question of every leg (a t1.py ranked.jsonl: info_need_id, info_need) -> OUT/
      queries.npy (float32, one row per question, legs in order) and OUT/queries.json (ids,
      token counts and timing; never text)
  search --index-dir D --queries-dir D --out-dir D --leg NAME=F [--leg ...] [--depth 1000]
      every question's top --depth PMIDs by q . bits -> OUT/NAME/ranked.jsonl (t1.py format, so
      t1.py score and rerank_run.py read it) and OUT/search.json

The encoder follows the model card: tokenizer(..., truncation=True, padding=True,
max_length=64), embedding = the [CLS] row of the last hidden state. torch and transformers are
imported only inside QueryEncoder, so the tests need numpy alone.
"""
import argparse
import importlib.util
import json
import os
import statistics
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dense_build  # noqa: E402

VERSION = "0.1.0"
MAX_LENGTH = 64
QREPO = "ncbi/MedCPT-Query-Encoder"
QCOMMIT = "d83a36cc6b8e3a5c5e9d9d6ba156808c1643dcbc"
QBASE = "https://huggingface.co/%s/resolve/%s/" % (QREPO, QCOMMIT)
# Read from the Hugging Face API tree of that commit twice on 2026-10-25 (git blob sha1, or LFS
# sha256 for the weights). Card licence: "public-domain" (NCBI/NLM).
QFILES = {
    "README.md": (4121, "git", "e5b1daeaefc9dd5976023033e0e9d40de74211d1"),
    "added_tokens.json": (74, "git", "e97f8f93bfdfff48a98fde37a3cd61007272f226"),
    "config.json": (608, "git", "0fdb62e1e58c8ec1c979a498adb692476730afe8"),
    "special_tokens_map.json": (125, "git", "a8b3208c2884c4efb86e49300fdd3dc877220cdf"),
    "tokenizer.json": (706277, "git", "e68fee3b6ebe7cc02f2b5f9753071bdf2c401ecf"),
    "tokenizer_config.json": (1488, "git", "a2e9fe3b9f5f82565a81e85b686910b20f6ee126"),
    "vocab.txt": (226150, "git", "9d595d9c20feef7012f174efaaa5eb621910588e"),
    "pytorch_model.bin": (437993382, "sha256", "debe354238bfd65f4f059d37e9c49a41c0908a2584d7a9328fc3155865a0fe9b"),
}


def load(code_dir, name):
    path = os.path.join(code_dir, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def parse_legs(specs):
    legs = []
    for s in specs:
        name, path = s.split("=", 1)
        legs.append((name, path))
    return legs


class QueryEncoder:
    """texts -> (float32 array, token count of each text before truncation)."""

    def __init__(self, model_dir, threads=2, batch=16, max_length=MAX_LENGTH):
        import torch
        from transformers import AutoModel, AutoTokenizer
        torch.set_num_threads(threads)
        self.torch, self.batch, self.max_length = torch, batch, max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModel.from_pretrained(model_dir)
        self.model.eval()

    def __call__(self, texts):
        lens = [len(self.tokenizer(t)["input_ids"]) for t in texts]
        out = []
        with self.torch.no_grad():
            for s in range(0, len(texts), self.batch):
                enc = self.tokenizer(texts[s:s + self.batch], truncation=True, padding=True,
                                     return_tensors="pt", max_length=self.max_length)
                out.append(self.model(**enc).last_hidden_state[:, 0, :].float().numpy())
        return np.concatenate(out).astype(np.float32), lens


def fetch_model(code_dir, model_dir, out_dir):
    rep = load(code_dir, "fetch_model").fetch_all(model_dir, files=QFILES, base=QBASE)
    rep.update(repo=QREPO, commit=QCOMMIT)
    os.makedirs(out_dir, exist_ok=True)
    dump(os.path.join(out_dir, "fetch_qenc.json"), rep)
    return rep


def encode(legs, encoder, out_dir, max_length=MAX_LENGTH):
    os.makedirs(out_dir, exist_ok=True)
    texts, meta = [], {"version": VERSION, "max_length": max_length, "order": [], "legs": {}}
    for name, path in legs:
        rows = load_jsonl(path)
        meta["order"].append(name)
        meta["legs"][name] = {"needs": len(rows), "ids": [str(r["info_need_id"]) for r in rows]}
        texts += [r["info_need"] for r in rows]
    t0 = time.time()
    q, lens = encoder(texts) if texts else (np.zeros((0, 0), dtype=np.float32), [])
    secs = time.time() - t0
    np.save(os.path.join(out_dir, "queries.npy"), np.asarray(q, dtype=np.float32))
    i = 0
    for name in meta["order"]:
        n = meta["legs"][name]["needs"]
        part = lens[i:i + n]
        meta["legs"][name].update(truncated=sum(1 for x in part if x > max_length),
                                  median_tokens=statistics.median(part) if part else None)
        i += n
    meta.update(questions=len(texts), dim=int(q.shape[1]) if texts else None, seconds=round(secs, 2),
                ms_per_question=round(1000 * secs / len(texts), 1) if texts else None)
    dump(os.path.join(out_dir, "queries.json"), meta)
    return meta


def chunk_files(index_dir):
    """(chunk, bits path, pmids path) for every finished chunk, by chunk number."""
    out = []
    for name in os.listdir(index_dir):
        if name.startswith("bits_") and name.endswith(".npy"):
            k = int(name[len("bits_"):-len(".npy")])
            p = os.path.join(index_dir, "pmids_%d.npy" % k)
            if os.path.exists(p):
                out.append((k, os.path.join(index_dir, name), p))
    return sorted(out)


def search_index(index_dir, q, depth=1000, block=dense_build.BLOCK):
    """Top `depth` PMIDs per query row by q . bits over every chunk. Returns (ids, scores, info)."""
    q = np.asarray(q, dtype=np.float32)
    qt = np.ascontiguousarray(q.T)
    top, vectors, chunks = dense_build.TopK(len(q), depth), 0, chunk_files(index_dir)
    for _, bits_path, pmids_path in chunks:
        bits, pmids = np.load(bits_path, mmap_mode="r"), np.load(pmids_path)
        for s in range(0, len(pmids), block):
            top.add(dense_build.unpack(bits[s:s + block], q.shape[1]) @ qt, pmids[s:s + block])
        vectors += len(pmids)
        del bits
    ids, scores = top.result()
    return ids, scores, {"chunks": len(chunks), "vectors": vectors}


def search(index_dir, queries_dir, legs, out_dir, depth=1000):
    q = np.load(os.path.join(queries_dir, "queries.npy"))
    with open(os.path.join(queries_dir, "queries.json"), encoding="utf-8") as f:
        meta = json.load(f)
    t0 = time.time()
    ids, scores, info = search_index(index_dir, q, depth)
    secs = time.time() - t0
    problems, i = [], 0
    if [n for n, _ in legs] != meta["order"]:
        problems.append("legs %s, queries were encoded for %s" % ([n for n, _ in legs], meta["order"]))
    for name, path in legs:
        rows = load_jsonl(path)
        if name in meta["legs"] and [str(r["info_need_id"]) for r in rows] != meta["legs"][name]["ids"]:
            problems.append("%s: question ids differ from the encoded ones" % name)
        os.makedirs(os.path.join(out_dir, name), exist_ok=True)
        with open(os.path.join(out_dir, name, "ranked.jsonl"), "w", encoding="utf-8") as f:
            for j, r in enumerate(rows):
                cands = [[int(p), round(float(s), 4)] for p, s in zip(ids[i + j], scores[i + j])
                         if np.isfinite(s)]
                f.write(json.dumps({"info_need_id": r["info_need_id"], "info_need": r["info_need"],
                                    "candidates": cands, "depth": depth}, ensure_ascii=False) + "\n")
        i += len(rows)
    if i != len(q):
        problems.append("%d questions in the legs, %d encoded" % (i, len(q)))
    rep = dict(info, version=VERSION, depth=depth, questions=int(len(q)), seconds=round(secs, 1),
               ms_per_question=round(1000 * secs / len(q), 1) if len(q) else None, problems=problems)
    dump(os.path.join(out_dir, "search.json"), rep)
    return rep


def main(argv=None, make_encoder=QueryEncoder):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch-model")
    f.add_argument("--code-dir", required=True)
    f.add_argument("--model-dir", required=True)
    f.add_argument("--out-dir", required=True)
    e = sub.add_parser("encode")
    e.add_argument("--model-dir", required=True)
    e.add_argument("--out-dir", required=True)
    e.add_argument("--leg", action="append", required=True)
    e.add_argument("--threads", type=int, default=2)
    s = sub.add_parser("search")
    s.add_argument("--index-dir", required=True)
    s.add_argument("--queries-dir", required=True)
    s.add_argument("--out-dir", required=True)
    s.add_argument("--leg", action="append", required=True)
    s.add_argument("--depth", type=int, default=1000)
    a = ap.parse_args(argv)
    if a.cmd == "fetch-model":
        rep = fetch_model(a.code_dir, a.model_dir, a.out_dir)
        bad = not rep["ok"]
    elif a.cmd == "encode":
        rep = encode(parse_legs(a.leg), make_encoder(a.model_dir, threads=a.threads), a.out_dir)
        rep = dict(rep, legs={n: {k: v for k, v in x.items() if k != "ids"} for n, x in rep["legs"].items()})
        bad = not rep["questions"]
    else:
        rep = search(a.index_dir, a.queries_dir, parse_legs(a.leg), a.out_dir, a.depth)
        bad = bool(rep["problems"]) or not rep["vectors"]
    print(json.dumps(rep, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
