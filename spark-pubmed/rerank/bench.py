"""CPU benchmark of the stage-2 reranker (job sparkrr-bench-v1): card check, speed, int8, memory.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

1. Card check: rerun the MedCPT model card's own example (its query, its six article strings,
   its tokenizer call) and compare with the six logits the card prints.
2. Speed: model forward time per (query, article) pair at 128, 256 and 512 tokens, batch 8,
   fixed thread count, token ids taken from the card text (no corpus text is read).
3. int8: quantise the Linear layers in place (dynamic int8) and repeat 1 and 2.
4. Peak RSS and the rerank depth that fits 200 questions in a 2-hour, 2-CPU budget.
Writes bench.json to --out-dir. Grades are given in PREREGISTRATION.md.
"""
import argparse
import ast
import json
import os
import re
import resource
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LENGTHS = (128, 256, 512)
QUERY_TOKENS = 16


def parse_card(text):
    """(query, articles, printed logits) from the card's example, or None for a missing part."""
    q = re.search(r'query\s*=\s*"([^"]*)"', text)
    articles = None
    start = text.find("articles = [")
    if start >= 0:
        start += len("articles = ")
        end = text.find("]", start)
        while end >= 0 and articles is None:
            try:
                val = ast.literal_eval(text[start:end + 1])
                if isinstance(val, list) and all(isinstance(s, str) for s in val):
                    articles = val
            except (SyntaxError, ValueError):
                pass
            end = text.find("]", end + 1)
    m = re.search(r"tensor\(\[([^\]]*)\]\)", text)
    printed = [float(x) for x in m.group(1).split(",")] if m else None
    return (q.group(1) if q else None), articles, printed


def card_check(enc, query, articles, printed):
    if not (query and articles and printed) or len(articles) != len(printed):
        return {"graded": False, "reason": "card example not parsed"}
    got = enc._logits([[query, a] for a in articles])
    diffs = [abs(g - p) for g, p in zip(got, printed)]
    order = lambda v: sorted(range(len(v)), key=lambda i: -v[i])  # noqa: E731
    return {"graded": True, "query": query, "n": len(articles), "printed": printed,
            "got": [round(g, 4) for g in got], "max_abs_diff": round(max(diffs), 5),
            "order_printed": order(printed), "order_got": order(got),
            "same_order": order(printed) == order(got)}


def id_pool(tokenizer, articles, need):
    ids = []
    if articles:
        ids = tokenizer(" ".join(articles), add_special_tokens=False)["input_ids"]
    if not ids:
        ids = list(range(1000, 1100))
    while len(ids) < need:
        ids = ids + ids
    return ids[:need]


def make_batch(tokenizer, pool, length, batch):
    """Inputs of exactly `length` tokens: [CLS] query [SEP] article [SEP]."""
    import torch
    cls, sep = tokenizer.cls_token_id, tokenizer.sep_token_id
    q = pool[:QUERY_TOKENS]
    d = pool[QUERY_TOKENS:QUERY_TOKENS + length - QUERY_TOKENS - 3]
    row = [cls] + q + [sep] + d + [sep]
    types = [0] * (len(q) + 2) + [1] * (len(d) + 1)
    assert len(row) == length == len(types)
    return {"input_ids": torch.tensor([row] * batch),
            "token_type_ids": torch.tensor([types] * batch),
            "attention_mask": torch.ones(batch, length, dtype=torch.long)}


def time_forward(model, inputs, batches):
    """Median ms per pair over `batches` timed batches, after one untimed warm-up batch."""
    import torch
    n = inputs["input_ids"].shape[0]
    per = []
    with torch.no_grad():
        model(**inputs)
        for _ in range(batches):
            t0 = time.perf_counter()
            model(**inputs)
            per.append((time.perf_counter() - t0) * 1000.0 / n)
    return round(statistics.median(per), 3)


def speed(enc, pool, batch, batches):
    return {str(L): time_forward(enc.model, make_batch(enc.tokenizer, pool, L, batch), batches)
            for L in LENGTHS}


def depth_for_budget(ms_by_len, tokens=320, questions=200, seconds=7200.0):
    """Pairs per question that fit the budget, ms/pair interpolated at `tokens`."""
    lo, hi = ms_by_len["256"], ms_by_len["512"]
    ms = max(lo + (hi - lo) * (tokens - 256) / 256.0, 1e-6)
    return {"ms_per_pair_at": tokens, "ms_per_pair": round(ms, 1),
            "depth": int(seconds / questions / (ms / 1000.0))}


def peak_rss_gb():
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0, 3)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--batches", type=int, default=3)
    a = ap.parse_args(argv)

    import torch
    import transformers
    from rerank import CrossEncoder, VERSION

    rep = {"rerank_version": VERSION, "torch": torch.__version__, "transformers": transformers.__version__,
           "threads": a.threads, "batch": a.batch, "batches": a.batches, "cpu_count": os.cpu_count()}
    try:
        rep["cpu_capability"] = torch.backends.cpu.get_cpu_capability()
    except AttributeError:
        rep["cpu_capability"] = None
    with open(os.path.join(a.model_dir, "README.md"), encoding="utf-8") as f:
        query, articles, printed = parse_card(f.read())
    t0 = time.time()
    enc = CrossEncoder(a.model_dir, threads=a.threads, batch_size=a.batch)
    rep["load_seconds"] = round(time.time() - t0, 1)
    rep["torch_threads"] = torch.get_num_threads()
    rep["rss_after_load_gb"] = peak_rss_gb()
    pool = id_pool(enc.tokenizer, articles, max(LENGTHS))

    rep["fp32"] = {"card": card_check(enc, query, articles, printed), "ms_per_pair": speed(enc, pool, a.batch, a.batches)}
    rep["fp32"]["budget"] = depth_for_budget(rep["fp32"]["ms_per_pair"])
    rep["rss_after_fp32_gb"] = peak_rss_gb()

    enc.quantize()
    rep["int8"] = {"card": card_check(enc, query, articles, printed), "ms_per_pair": speed(enc, pool, a.batch, a.batches)}
    rep["int8"]["budget"] = depth_for_budget(rep["int8"]["ms_per_pair"])
    rep["int8"]["speedup"] = {L: round(rep["fp32"]["ms_per_pair"][L] / max(rep["int8"]["ms_per_pair"][L], 1e-6), 2)
                              for L in rep["fp32"]["ms_per_pair"]}
    if rep["fp32"]["card"].get("graded") and rep["int8"]["card"].get("graded"):
        rep["int8"]["max_abs_diff_vs_fp32"] = round(max(
            abs(x - y) for x, y in zip(rep["fp32"]["card"]["got"], rep["int8"]["card"]["got"])), 4)
    rep["peak_rss_gb"] = peak_rss_gb()

    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "bench.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
