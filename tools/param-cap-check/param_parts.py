# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Split each open model's stored parameters into parts by reading only its safetensors headers.

Made with AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com).

Contests that cap model size ("one generative model with no more than 3 billion
parameters") rarely say whether a vision or audio tower, a multi-token-prediction
(MTP) head or per-layer embedding tables count. This script reads the JSON header
at the start of each safetensors file with two small HTTP range requests (no
weights are downloaded), sums the parameters of every tensor, and splits them into:

  vision, audio, mtp, per_layer_embed, embed, lm_head, quant_scale, text_core

It then reports the count under four readings of a cap:
  A stored          every stored tensor (what the Hugging Face API reports)
  B no_towers       A minus vision and audio towers
  C no_towers_mtp   B minus MTP heads
  D text_effective  C minus per-layer embedding tables (Gemma "effective" style)

File choice follows huggingface_hub.get_safetensors_metadata: model.safetensors if
present, else the files named in model.safetensors.index.json, else every
root-level *.safetensors file (flagged). Gated models are skipped (no token used).
The parts come from tensor names, so a new naming scheme can land in text_core;
the per-model tensor-name prefixes are written out so this can be checked.

Stdlib only. Usage:
    python param_parts.py --models models.txt --out-dir out [--cap 3e9]
"""
import argparse
import json
import os
import struct
import time
import urllib.error
import urllib.request

API = "https://huggingface.co/api/models/{}"
RESOLVE = "https://huggingface.co/{}/resolve/{}/{}"
USER_AGENT = "mv2-param-parts/0.1 (+mv2@munimtech.com)"
MAX_HEADER = 100 * 1024 * 1024
PARTS = ("vision", "audio", "mtp", "per_layer_embed", "embed", "lm_head", "quant_scale", "text_core")
VISION = {"visual", "vision_tower", "vision_model", "vision_encoder", "embed_vision",
          "multi_modal_projector", "mm_projector", "image_newline", "vision_embed_tokens"}
AUDIO = {"audio_tower", "audio_model", "audio_encoder", "embed_audio"}
PLE = {"embed_tokens_per_layer"}
EMBED = {"embed_tokens", "wte", "word_embeddings", "tok_embeddings"}
SCALES = {"weight_scale", "weight_scale_inv", "input_scale", "activation_scale"}
RULES = ("stored", "no_towers", "no_towers_mtp", "text_effective")


def classify(name):
    """Part of the model a tensor belongs to, from its dotted name."""
    parts = name.lower().split(".")
    s = set(parts)
    if s & VISION:
        return "vision"
    if s & AUDIO:
        return "audio"
    if "mtp" in s:
        return "mtp"
    if s & PLE:
        return "per_layer_embed"
    if s & EMBED:
        return "embed"
    if "lm_head" in s:
        return "lm_head"
    if parts[-1] in SCALES:
        return "quant_scale"
    return "text_core"


def numel(shape):
    n = 1
    for d in shape:
        n *= int(d)
    return n


def prefix(name, depth=3):
    """First components of a tensor name with layer numbers folded, e.g. model.layers.*."""
    out = []
    for p in name.split(".")[:depth]:
        out.append("*" if p.isdigit() else p)
    return ".".join(out)


def http_range(url, start, end, timeout=60):
    """Bytes start..end (inclusive). Copes with servers that ignore Range (status 200)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Range": "bytes={}-{}".format(start, end)})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if getattr(resp, "status", 206) == 206:
            return resp.read(end - start + 1)
        return resp.read(end + 1)[start:]


def read_header(url, getter=http_range):
    """The JSON header of one safetensors file at url, via two range reads."""
    first = getter(url, 0, 7)
    if len(first) != 8:
        raise ValueError("short read of header length")
    (n,) = struct.unpack("<Q", first)
    if n <= 0 or n > MAX_HEADER:
        raise ValueError("implausible header length {}".format(n))
    raw = getter(url, 8, 8 + n - 1)
    if len(raw) != n:
        raise ValueError("short read of header")
    return json.loads(raw.decode("utf-8"))


def fetch_json(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def pick_files(filenames, load_index):
    """(files, how). load_index(name) returns the parsed index JSON."""
    names = set(filenames)
    if "model.safetensors" in names:
        return ["model.safetensors"], "model.safetensors"
    if "model.safetensors.index.json" in names:
        idx = load_index("model.safetensors.index.json")
        return sorted(set(idx.get("weight_map", {}).values())), "index"
    root = sorted(n for n in names if n.endswith(".safetensors") and "/" not in n)
    return root, "all-root-safetensors"


def split_parts(headers):
    """Sum parameters per part over a list of parsed headers."""
    sums = {p: 0 for p in PARTS}
    prefixes = {}
    tensors = 0
    for header in headers:
        for name, info in header.items():
            if name == "__metadata__" or not isinstance(info, dict) or "shape" not in info:
                continue
            k = numel(info["shape"])
            part = classify(name)
            sums[part] += k
            tensors += 1
            key = prefix(name)
            entry = prefixes.setdefault(key, {"part": part, "params": 0})
            entry["params"] += k
    return sums, tensors, prefixes


def readings(sums):
    stored = sum(sums.values())
    no_towers = stored - sums["vision"] - sums["audio"]
    no_towers_mtp = no_towers - sums["mtp"]
    text_effective = no_towers_mtp - sums["per_layer_embed"]
    return {"stored": stored, "no_towers": no_towers, "no_towers_mtp": no_towers_mtp,
            "text_effective": text_effective}


def assess(model_id, meta, headers, how, files, cap):
    sums, tensors, prefixes = split_parts(headers)
    counts = readings(sums)
    api_total = (meta.get("safetensors") or {}).get("total")
    return {
        "model": model_id,
        "sha": meta.get("sha"),
        "files": files,
        "file_choice": how,
        "tensors": tensors,
        "api_total": api_total,
        "matches_api": api_total == counts["stored"],
        "parts": sums,
        "counts": counts,
        "fits": {r: counts[r] <= cap for r in RULES},
        "prefixes": prefixes,
    }


def check_model(model_id, cap, api=None, header=None, index=None):
    api = api or (lambda m: fetch_json(API.format(m)))
    meta = api(model_id)
    if meta.get("gated"):
        return {"model": model_id, "skipped": "gated (no token used)", "sha": meta.get("sha"),
                "api_total": (meta.get("safetensors") or {}).get("total")}
    sha = meta.get("sha") or "main"
    names = [s.get("rfilename", "") for s in meta.get("siblings") or []]
    if header is None:
        header = lambda m, rev, f: read_header(RESOLVE.format(m, rev, f))
    if index is None:
        index = lambda m, rev, f: fetch_json(RESOLVE.format(m, rev, f))
    files, how = pick_files(names, lambda f: index(model_id, sha, f))
    if not files:
        return {"model": model_id, "skipped": "no safetensors files", "sha": sha}
    headers = [header(model_id, sha, f) for f in files]
    return assess(model_id, meta, headers, how, files, cap)


def read_models(text):
    seen, out = set(), []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line and line not in seen:
            seen.add(line)
            out.append(line)
    return out


def fmt_b(n):
    return "{:.3f}".format(n / 1e9)


def to_markdown(rows, cap):
    lines = [
        "Parameters in billions. A = every stored tensor; B = A minus vision/audio towers; "
        "C = B minus MTP heads; D = C minus per-layer embedding tables. "
        "Bold = over the cap of {:,}.".format(int(cap)),
        "",
        "| Model | Vision | Audio | MTP | Per-layer emb. | A stored | B | C | D | A = HF API |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        if "error" in r or "skipped" in r:
            lines.append("| {} | - | - | - | - | - | - | - | - | {} |".format(
                r["model"], r.get("error") or r.get("skipped")))
            continue
        p, c = r["parts"], r["counts"]
        cells = []
        for rule in RULES:
            v = fmt_b(c[rule])
            cells.append(v if r["fits"][rule] else "**{}**".format(v))
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            r["model"], fmt_b(p["vision"]), fmt_b(p["audio"]), fmt_b(p["mtp"]),
            fmt_b(p["per_layer_embed"]), " | ".join(cells),
            "yes" if r["matches_api"] else "NO (API {})".format(r["api_total"])))
    return "\n".join(lines) + "\n"


def main(argv=None, api=None, header=None, index=None, pause=0.5):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--models", required=True)
    ap.add_argument("--cap", type=float, default=3e9)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    with open(args.models, encoding="utf-8") as fh:
        models = read_models(fh.read())
    rows = []
    for i, model_id in enumerate(models):
        if i and pause:
            time.sleep(pause)
        try:
            rows.append(check_model(model_id, args.cap, api=api, header=header, index=index))
        except urllib.error.HTTPError as exc:
            rows.append({"model": model_id, "error": "HTTP {}".format(exc.code)})
        except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
            rows.append({"model": model_id, "error": "{}: {}".format(type(exc).__name__, exc)[:200]})
    os.makedirs(args.out_dir, exist_ok=True)
    done = [r for r in rows if "counts" in r]
    report = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cap": int(args.cap),
        "rows": rows,
        "summary": {
            "models": len(rows),
            "read": len(done),
            "matches_api": sum(1 for r in done if r["matches_api"]),
            "fits": {rule: sum(1 for r in done if r["fits"][rule]) for rule in RULES},
        },
    }
    with open(os.path.join(args.out_dir, "param-parts.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(args.out_dir, "param-parts.md"), "w", encoding="utf-8") as fh:
        fh.write("Checked {}.\n\n".format(report["checked_at"]))
        fh.write(to_markdown(rows, args.cap))
    print(json.dumps(report["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
