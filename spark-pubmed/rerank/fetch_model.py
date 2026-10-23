"""Fetch NCBI's MedCPT cross-encoder at one pinned commit, every file checked against its hash.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

The model (huggingface.co/ncbi/MedCPT-Cross-Encoder, card licence "public-domain", NCBI/NLM;
cite Jin et al. 2023, Bioinformatics 39(11) btad651) is the planned stage-2 reranker for the
SPARK PubMed/PMC Task 1 system. Sizes and hashes below were read from the Hugging Face API tree
of commit 71caf65d4927987813984f54c284405a13fcca49 twice on 2026-10-23: small files are checked
by their git blob sha1 (the tree's "oid"), the weights by their LFS sha256. Each file goes to
<name>.part, is fsynced, checked, then renamed; a file already present and matching is kept, so
a rerun resumes. Nothing downloaded is executed (the weights are loaded later with
torch.load(weights_only=True) by transformers).
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request

REPO = "ncbi/MedCPT-Cross-Encoder"
COMMIT = "71caf65d4927987813984f54c284405a13fcca49"
BASE = "https://huggingface.co/%s/resolve/%s/" % (REPO, COMMIT)
UA = "MV2-Munim-spark-rerank/0.1 (mv2@munimtech.com)"

# name -> (bytes, kind, hex digest)
FILES = {
    "README.md": (4236, "git", "66c40e55c2b6ffacac881df8a0b282f831c4d432"),
    "added_tokens.json": (74, "git", "e97f8f93bfdfff48a98fde37a3cd61007272f226"),
    "config.json": (741, "git", "766e5596630ebbdbe72b10cc777a95bb749f2bc0"),
    "special_tokens_map.json": (228, "git", "8e5082c800f715935ea0eb822faad62f4fac1ada"),
    "tokenizer.json": (706277, "git", "e68fee3b6ebe7cc02f2b5f9753071bdf2c401ecf"),
    "tokenizer_config.json": (1556, "git", "85ae100df867ca6a1387ae02918eb02fdc03383e"),
    "vocab.txt": (226150, "git", "9d595d9c20feef7012f174efaaa5eb621910588e"),
    "pytorch_model.bin": (437998062, "sha256", "61d5ccd48869e03500544525fc231641d7daa9ba267b202c82724750038dc1e0"),
}


def digest(path, kind):
    """git blob sha1 ("blob <size>\\0" + content) or plain sha256 of a file."""
    if kind == "git":
        h = hashlib.sha1(b"blob %d\0" % os.path.getsize(path))
    else:
        h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def matches(path, size, kind, want):
    return os.path.isfile(path) and os.path.getsize(path) == size and digest(path, kind) == want


def opener(url, timeout=120):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout)


def get(name, spec, model_dir, base=BASE, open_url=opener, tries=3):
    size, kind, want = spec
    path = os.path.join(model_dir, name)
    rec = {"file": name, "bytes": size, "kind": kind, "want": want}
    if matches(path, size, kind, want):
        rec.update(status="kept", got=want)
        return rec
    part = path + ".part"
    for attempt in range(1, tries + 1):
        t0 = time.time()
        try:
            with open_url(base + name) as resp, open(part, "wb") as f:
                for chunk in iter(lambda: resp.read(1 << 20), b""):
                    f.write(chunk)
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            rec.update(status="error", error="%s: %s" % (type(e).__name__, e), attempts=attempt)
            continue
        got = digest(part, kind)
        rec.update(got=got, got_bytes=os.path.getsize(part), attempts=attempt,
                   seconds=round(time.time() - t0, 1))
        if rec["got_bytes"] == size and got == want:
            os.replace(part, path)
            rec["status"] = "downloaded"
            return rec
        rec["status"] = "mismatch"
    if os.path.exists(part):
        os.remove(part)
    return rec


def fetch_all(model_dir, files=FILES, base=BASE, open_url=opener):
    os.makedirs(model_dir, exist_ok=True)
    recs = [get(n, files[n], model_dir, base, open_url) for n in sorted(files)]
    ok = all(r["status"] in ("kept", "downloaded") for r in recs)
    return {"repo": REPO, "commit": COMMIT, "model_dir": model_dir, "ok": ok,
            "total_bytes": sum(s for s, _, _ in files.values()), "files": recs}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    rep = fetch_all(a.model_dir)
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "fetch_model.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
