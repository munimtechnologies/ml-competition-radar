# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name.
"""Arithmetic of TelcoRetrieve's overall score (Zindi, ITU and GSMA).

Version 2 (2026-11-11 ~18:30 UTC). The challenge docs in the starter kit
(Znbne/telco-retrieve, Apache-2.0, docs/challenge/README.md at commit a9b61be6,
2026-11-11 16:01 UTC) now state:

    Score = 0.7 x accuracy + 0.3 x token efficiency,
    token efficiency = 100 x B / (B + T), B = 850 tokens per question,
    T = total prompt tokens (cl100k_base); minimum accuracy 80%;
    every input_prompt at most 4,096 tokens.

The kit's own scorer code (open_telco_rag/challenge/metrics/token_efficiency.py)
still carries the earlier 2000 marked "proposed, not confirmed". With B and T both
taken over all questions, efficiency = 100 x B / (B + mean prompt tokens).
The default baseline here is 850; pass --baseline 2000 for the earlier value.

Standard library only. Run: python score_tradeoff.py [--json] [--baseline N]
"""
from __future__ import annotations

import json
import sys

WEIGHT_ACCURACY = 0.7
WEIGHT_TOKEN_EFFICIENCY = 0.3
BASELINE_TOKENS_PER_QUESTION = 850
EARLIER_BASELINE_TOKENS_PER_QUESTION = 2000
MAX_PROMPT_TOKENS = 4096
MIN_ACCURACY = 80.0


def token_efficiency(mean_tokens: float, baseline: float = BASELINE_TOKENS_PER_QUESTION) -> float:
    """Token efficiency (0-100] for a mean input_prompt length in cl100k_base tokens."""
    if mean_tokens < 0:
        raise ValueError("mean_tokens must be >= 0")
    if baseline <= 0:
        raise ValueError("baseline must be > 0")
    return 100.0 * baseline / (baseline + mean_tokens)


def token_efficiency_from_counts(counts, baseline: float = BASELINE_TOKENS_PER_QUESTION) -> float:
    """Same metric computed the organisers' way: totals over all questions."""
    counts = list(counts)
    if not counts:
        raise ValueError("no prompts")
    if any(c < 0 for c in counts):
        raise ValueError("token counts must be >= 0")
    if any(c > MAX_PROMPT_TOKENS for c in counts):
        raise ValueError("a prompt over %d tokens invalidates the submission" % MAX_PROMPT_TOKENS)
    total_baseline = baseline * len(counts)
    return 100.0 * total_baseline / (total_baseline + sum(counts))


def overall(accuracy: float, mean_tokens: float,
            w_acc: float = WEIGHT_ACCURACY, w_eff: float = WEIGHT_TOKEN_EFFICIENCY,
            baseline: float = BASELINE_TOKENS_PER_QUESTION) -> float:
    """Overall score for an accuracy (0-100) and a mean prompt length."""
    if not 0 <= accuracy <= 100:
        raise ValueError("accuracy is a percentage")
    return w_acc * accuracy + w_eff * token_efficiency(mean_tokens, baseline)


def breakeven_accuracy_gain(tokens_from: float, tokens_to: float,
                            w_acc: float = WEIGHT_ACCURACY, w_eff: float = WEIGHT_TOKEN_EFFICIENCY,
                            baseline: float = BASELINE_TOKENS_PER_QUESTION) -> float:
    """Accuracy points a longer prompt must add to keep the overall score unchanged."""
    return (w_eff / w_acc) * (token_efficiency(tokens_from, baseline) - token_efficiency(tokens_to, baseline))


def marginal_cost_per_100_tokens(mean_tokens: float,
                                 w_acc: float = WEIGHT_ACCURACY, w_eff: float = WEIGHT_TOKEN_EFFICIENCY,
                                 baseline: float = BASELINE_TOKENS_PER_QUESTION) -> float:
    """Accuracy points that 100 more mean prompt tokens cost at a given length."""
    return breakeven_accuracy_gain(mean_tokens, mean_tokens + 100, w_acc, w_eff, baseline)


ACCURACIES = (80, 85, 90, 95)
TOKENS = (100, 300, 600, 1000, 2000, 3000)


def report(baseline: float = BASELINE_TOKENS_PER_QUESTION) -> dict:
    grid = [{"accuracy": a, "mean_tokens": t, "overall": round(overall(a, t, baseline=baseline), 3)}
            for a in ACCURACIES for t in TOKENS]
    effs = {t: round(token_efficiency(t, baseline), 3) for t in TOKENS}
    pairs = [(100, 300), (300, 600), (300, 1000), (300, 2000), (1000, 2000)]
    breakeven = [{"from": f, "to": t,
                  "accuracy_points": round(breakeven_accuracy_gain(f, t, baseline=baseline), 3)}
                 for f, t in pairs]
    marginal = {t: round(marginal_cost_per_100_tokens(t, baseline=baseline), 3) for t in TOKENS}
    return {"weights": [WEIGHT_ACCURACY, WEIGHT_TOKEN_EFFICIENCY],
            "baseline_tokens_per_question": baseline,
            "token_efficiency": effs, "overall_grid": grid,
            "breakeven_accuracy_gain": breakeven,
            "accuracy_points_per_100_more_tokens": marginal}


def parse_baseline(argv) -> float:
    if "--baseline" in argv:
        i = argv.index("--baseline")
        if i + 1 >= len(argv):
            raise ValueError("--baseline needs a number")
        value = float(argv[i + 1])
        if value <= 0:
            raise ValueError("baseline must be > 0")
        return value
    return BASELINE_TOKENS_PER_QUESTION


def main(argv) -> int:
    baseline = parse_baseline(argv)
    rep = report(baseline)
    if "--json" in argv:
        print(json.dumps(rep, indent=1))
        return 0
    print("baseline B = %g tokens per question" % baseline)
    print("mean prompt tokens -> token efficiency")
    for t, e in rep["token_efficiency"].items():
        print("  %5d -> %.3f" % (t, e))
    print("overall score (rows: accuracy; columns: mean prompt tokens)")
    print("  acc  " + " ".join("%8d" % t for t in TOKENS))
    for a in ACCURACIES:
        print("  %3d  " % a + " ".join("%8.3f" % overall(a, t, baseline=baseline) for t in TOKENS))
    print("accuracy points a longer prompt must add to break even")
    for row in rep["breakeven_accuracy_gain"]:
        print("  %5d -> %5d tokens: %.3f" % (row["from"], row["to"], row["accuracy_points"]))
    print("accuracy points that 100 more mean tokens cost")
    for t, m in rep["accuracy_points_per_100_more_tokens"].items():
        print("  at %5d tokens: %.3f" % (t, m))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
