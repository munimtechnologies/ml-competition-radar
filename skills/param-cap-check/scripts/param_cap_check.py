# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Check open generative models against a parameter cap and a permissive-licence list.

Made with AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com).

Some competitions cap the generator size, e.g. "one generative model with no more
than 3 billion parameters" and require permissive open-source licences. Model
names are not parameter counts ("3B", "E2B", "micro"), so this script reads the
public Hugging Face model API (no token) and reports, for each model id:
the exact parameter count stored in its safetensors files, its declared licence,
and a verdict against the cap.

Counting notes (limits, stated honestly):
- The count is `safetensors.total` from the Hugging Face API: every tensor stored
  in the repo's safetensors files, counted once. Tied input/output embeddings are
  stored once, so they count once. Vision or audio towers shipped in the same
  files ARE counted. Quantised repos count stored elements, not original weights.
- A contest's own judges may count differently; this is evidence, not a ruling.

Stdlib only. Usage:
    python param_cap_check.py --models models.txt --out-dir out [--cap 3e9]
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request

API = "https://huggingface.co/api/models/{}"
USER_AGENT = "mv2-param-cap-check/0.1 (+mv2@munimtech.com)"
PERMISSIVE = {"apache-2.0", "mit", "bsd-2-clause", "bsd-3-clause"}


def fetch(model_id, timeout=30):
    """Return the Hugging Face API JSON for one model id."""
    req = urllib.request.Request(API.format(model_id), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def licence_of(meta):
    """Declared licence, lower-case. 'other' licences carry their name: 'other:<name>'."""
    card = meta.get("cardData") or {}
    lic = card.get("license")
    if isinstance(lic, list):
        lic = lic[0] if lic else None
    if not lic:
        for tag in meta.get("tags") or []:
            if isinstance(tag, str) and tag.startswith("license:"):
                lic = tag.split(":", 1)[1]
                break
    lic = (lic or "").strip().lower()
    if lic == "other":
        name = str(card.get("license_name") or "").strip().lower()
        return "other:" + name if name else "other"
    return lic or "unknown"


def params_of(meta):
    """(total, by_dtype) from safetensors metadata, or (None, {}) when absent."""
    st = meta.get("safetensors") or {}
    total = st.get("total")
    if isinstance(total, int) and not isinstance(total, bool) and total > 0:
        return total, dict(st.get("parameters") or {})
    return None, {}


def assess(model_id, meta, cap):
    total, by_dtype = params_of(meta)
    lic = licence_of(meta)
    permissive = lic in PERMISSIVE
    fits = None if total is None else total <= cap
    if total is None:
        verdict = "unknown-size"
    elif not fits and not permissive:
        verdict = "over-cap-and-licence"
    elif not fits:
        verdict = "over-cap"
    elif not permissive:
        verdict = "licence"
    else:
        verdict = "ok"
    return {
        "model": model_id,
        "params": total,
        "params_b": round(total / 1e9, 3) if total else None,
        "by_dtype": by_dtype,
        "licence": lic,
        "permissive": permissive,
        "fits_cap": fits,
        "verdict": verdict,
        "pipeline_tag": meta.get("pipeline_tag"),
        "gated": meta.get("gated"),
        "sha": meta.get("sha"),
        "last_modified": meta.get("lastModified"),
    }


def read_models(text):
    """Model ids, one per line; blank lines and '#' comments ignored; order kept, no repeats."""
    seen, out = set(), []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line and line not in seen:
            seen.add(line)
            out.append(line)
    return out


def to_markdown(rows, cap):
    lines = [
        "| Model | Parameters (exact) | Billions | Licence | Verdict at cap {:,} |".format(int(cap)),
        "|---|---:|---:|---|---|",
    ]
    for r in rows:
        if r.get("verdict") == "error":
            lines.append("| {} | - | - | - | error: {} |".format(r["model"], r.get("error", "")))
            continue
        params = "{:,}".format(r["params"]) if r["params"] else "-"
        billions = "{:.3f}".format(r["params_b"]) if r["params_b"] is not None else "-"
        lines.append("| {} | {} | {} | {} | {} |".format(
            r["model"], params, billions, r["licence"], r["verdict"]))
    return "\n".join(lines) + "\n"


def run(models, cap, fetcher=fetch, pause=0.5):
    rows = []
    for i, model_id in enumerate(models):
        if i and pause:
            time.sleep(pause)
        try:
            meta = fetcher(model_id)
        except urllib.error.HTTPError as exc:
            rows.append({"model": model_id, "verdict": "error", "error": "HTTP {}".format(exc.code)})
            continue
        except (urllib.error.URLError, OSError, ValueError) as exc:
            rows.append({"model": model_id, "verdict": "error", "error": type(exc).__name__})
            continue
        rows.append(assess(model_id, meta, cap))
    return rows


def main(argv=None, fetcher=fetch, pause=0.5):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--models", required=True, help="text file: one Hugging Face model id per line")
    ap.add_argument("--cap", type=float, default=3e9, help="parameter cap (default 3e9)")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    with open(args.models, encoding="utf-8") as fh:
        models = read_models(fh.read())
    rows = run(models, args.cap, fetcher=fetcher, pause=pause)
    os.makedirs(args.out_dir, exist_ok=True)
    report = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cap": int(args.cap),
        "source": API.format("<model id>"),
        "rows": rows,
        "counts": {v: sum(1 for r in rows if r["verdict"] == v)
                   for v in sorted({r["verdict"] for r in rows})},
    }
    with open(os.path.join(args.out_dir, "param-cap.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(args.out_dir, "param-cap.md"), "w", encoding="utf-8") as fh:
        fh.write("Checked {} against a cap of {:,} parameters.\n\n".format(report["checked_at"], int(args.cap)))
        fh.write(to_markdown(rows, args.cap))
    print(json.dumps(report["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
