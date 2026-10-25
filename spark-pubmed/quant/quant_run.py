"""Stage-2 speed variants for SPARK Task 1 (job spark42-quant-v1): rescore an earlier rerank's
candidates with the MedCPT cross-encoder at a chosen precision and input length.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Runs rerank_run.run (rerank @ 99ade999, fetched into --code-dir by fetch_code.py) with
rerank.CrossEncoder(max_length=--max-length, quantize=--quantize) and adds the variant to its
rerank.json. Fed a ranked.jsonl that rerank_run wrote at depth 50 with no missing text, depth 50
rescores exactly the 50 articles the fp32 run scored, so any change in the top five comes from
the variant alone. Modules are loaded from --code-dir by path, so the tests can use stand-ins.

  python quant_run.py --code-dir D --db F --ranked F --model-dir D --out-dir D
                      [--depth 50] [--quantize] [--max-length 512] [--threads 2] [--batch 8]
"""
import argparse
import importlib.util
import json
import os
import sys

VERSION = "0.1.0"


def variant(quantize, max_length):
    return "%s_%d" % ("int8" if quantize else "fp32", max_length)


def load(code_dir, name):
    path = os.path.join(code_dir, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cross_encoder(code_dir, model_dir, max_length, batch, threads, quantize):
    """The real scorer (torch); only built when the command runs."""
    return load(code_dir, "rerank").CrossEncoder(model_dir, max_length=max_length, batch_size=batch,
                                                 threads=threads, quantize=quantize)


def run(code_dir, db, ranked, out_dir, scorer, depth, quantize, max_length):
    s = load(code_dir, "rerank_run").run(db, ranked, out_dir, scorer, depth)
    s.update({"quant_run_version": VERSION, "variant": variant(quantize, max_length),
              "quantize": bool(quantize), "max_length": max_length})
    with open(os.path.join(out_dir, "rerank.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, indent=1)
    return s


def main(argv=None, make_scorer=cross_encoder):
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-dir", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--ranked", required=True)
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--depth", type=int, default=50)
    ap.add_argument("--quantize", action="store_true")
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--batch", type=int, default=8)
    a = ap.parse_args(argv)
    scorer = make_scorer(a.code_dir, a.model_dir, a.max_length, a.batch, a.threads, a.quantize)
    s = run(a.code_dir, a.db, a.ranked, a.out_dir, scorer, a.depth, a.quantize, a.max_length)
    print(json.dumps(s, indent=1))
    return 0 if s["needs"] else 1


if __name__ == "__main__":
    sys.exit(main())
