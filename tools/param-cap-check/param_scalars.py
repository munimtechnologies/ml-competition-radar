# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Explain gaps between our safetensors parameter counts and the Hugging Face API's.

Made with AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com).

param_parts.py (same folder) sums numel(shape) over every tensor in a model's
safetensors headers and counts a zero-dimensional tensor (shape []) as 1 parameter.
On 2026-11-06 two models did not match the API's safetensors.total:
Ministral-3-3B-Instruct-2512 (ours 364 higher) and gemma-4-E2B-it (ours 928 higher).
This script re-reads the same headers and reports, per model: parameters per dtype,
the API's parameters per dtype, how many zero-dimensional tensors there are (by
dtype, by part and by last name component), and whether the gap equals that number.

Stdlib only. Usage:
    python param_scalars.py --models models.txt --out-dir out
"""
import argparse
import json
import os
import time
import urllib.error

import param_parts as pp


def dtype_sums(headers):
    """(params per dtype, zero-dim tensors per dtype, names of zero-dim tensors)."""
    params, zero, zero_names = {}, {}, []
    for header in headers:
        for name, info in header.items():
            if name == "__metadata__" or not isinstance(info, dict) or "shape" not in info:
                continue
            dt = info.get("dtype", "?")
            params[dt] = params.get(dt, 0) + pp.numel(info["shape"])
            if len(info["shape"]) == 0:
                zero[dt] = zero.get(dt, 0) + 1
                zero_names.append(name)
    return params, zero, zero_names


def explain(model_id, meta, headers, files):
    params, zero, zero_names = dtype_sums(headers)
    st = meta.get("safetensors") or {}
    api_params = st.get("parameters") or {}
    api_total = st.get("total")
    ours = sum(params.values())
    n_zero = len(zero_names)
    by_part, by_leaf = {}, {}
    for name in zero_names:
        part = pp.classify(name)
        by_part[part] = by_part.get(part, 0) + 1
        leaf = name.split(".")[-1]
        by_leaf[leaf] = by_leaf.get(leaf, 0) + 1
    dtypes = sorted(set(params) | set(api_params))
    return {
        "model": model_id,
        "sha": meta.get("sha"),
        "files": files,
        "ours_total": ours,
        "api_total": api_total,
        "gap": None if api_total is None else ours - api_total,
        "zero_dim_tensors": n_zero,
        "gap_equals_zero_dim": api_total is not None and ours - api_total == n_zero,
        "params_by_dtype": params,
        "api_params_by_dtype": api_params,
        "zero_dim_by_dtype": zero,
        "dtype_match_counting_zero_dim_as_1": all(
            params.get(d, 0) == api_params.get(d, 0) for d in dtypes),
        "dtype_match_counting_zero_dim_as_0": all(
            params.get(d, 0) - zero.get(d, 0) == api_params.get(d, 0) for d in dtypes),
        "dtypes_missing_from_api": sorted(d for d in params if params[d] and d not in api_params),
        "zero_dim_by_part": by_part,
        "zero_dim_by_leaf": by_leaf,
    }


def load(model_id, api, header, index):
    meta = api(model_id)
    if meta.get("gated"):
        return meta, None, None
    sha = meta.get("sha") or "main"
    names = [s.get("rfilename", "") for s in meta.get("siblings") or []]
    files, _how = pp.pick_files(names, lambda f: index(model_id, sha, f))
    headers = [header(model_id, sha, f) for f in files]
    return meta, files, headers


def to_markdown(rows):
    lines = [
        "| Model | Ours | HF API | Gap | Zero-dim tensors | Gap = zero-dim | Zero-dim by part | Dtypes missing from API |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for r in rows:
        if "ours_total" not in r:
            lines.append("| {} | - | - | - | - | - | - | {} |".format(
                r["model"], r.get("error") or r.get("skipped")))
            continue
        lines.append("| {} | {:,} | {} | {} | {} | {} | {} | {} |".format(
            r["model"], r["ours_total"],
            "-" if r["api_total"] is None else "{:,}".format(r["api_total"]),
            "-" if r["gap"] is None else r["gap"], r["zero_dim_tensors"],
            "yes" if r["gap_equals_zero_dim"] else "no",
            ", ".join("{} {}".format(k, v) for k, v in sorted(r["zero_dim_by_part"].items())) or "-",
            ", ".join(r["dtypes_missing_from_api"]) or "-"))
    return "\n".join(lines) + "\n"


def main(argv=None, api=None, header=None, index=None, pause=0.5):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--models", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    api = api or (lambda m: pp.fetch_json(pp.API.format(m)))
    header = header or (lambda m, rev, f: pp.read_header(pp.RESOLVE.format(m, rev, f)))
    index = index or (lambda m, rev, f: pp.fetch_json(pp.RESOLVE.format(m, rev, f)))
    with open(args.models, encoding="utf-8") as fh:
        models = pp.read_models(fh.read())
    rows = []
    for i, model_id in enumerate(models):
        if i and pause:
            time.sleep(pause)
        try:
            meta, files, headers = load(model_id, api, header, index)
            if headers is None:
                rows.append({"model": model_id, "skipped": "gated (no token used)"})
            elif not files:
                rows.append({"model": model_id, "skipped": "no safetensors files"})
            else:
                rows.append(explain(model_id, meta, headers, files))
        except urllib.error.HTTPError as exc:
            rows.append({"model": model_id, "error": "HTTP {}".format(exc.code)})
        except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
            rows.append({"model": model_id, "error": "{}: {}".format(type(exc).__name__, exc)[:200]})
    done = [r for r in rows if "ours_total" in r]
    report = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": rows,
        "summary": {
            "models": len(rows),
            "read": len(done),
            "gap_zero": sum(1 for r in done if r["gap"] == 0),
            "gap_equals_zero_dim": sum(1 for r in done if r["gap_equals_zero_dim"]),
            "with_zero_dim": sum(1 for r in done if r["zero_dim_tensors"]),
        },
    }
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "param-scalars.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(args.out_dir, "param-scalars.md"), "w", encoding="utf-8") as fh:
        fh.write("Checked {}.\n\n".format(report["checked_at"]))
        fh.write(to_markdown(rows))
    print(json.dumps(report["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
