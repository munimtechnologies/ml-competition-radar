# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents working in his name.
"""Arithmetic of TelcoRetrieve's provisional overall score (Zindi, ITU and GSMA).

Mirrors the starter kit's open_telco_rag/challenge/metrics (Znbne/telco-retrieve,
commit 075feaa3, Apache-2.0), read 2026-11-11:

    TokenEfficiency = 100 * (2000 * N) / (2000 * N + sum of input_prompt tokens)
                    = 100 * 2000 / (2000 + mean input_prompt tokens)
    Overall         = 0.7 * Accuracy + 0.3 * TokenEfficiency     (weights "provisional")
    Accuracy below 80 is "not eligible for code evaluation"; any prompt over 4096 tokens
    invalidates the submission. The 2000 baseline is marked "proposed, not confirmed".

Standard library only. Run: python score_tradeoff.py [--json]
"""
from __future__ import annotations

import json
import sys

WEIGHT_ACCURACY = 0.7
WEIGHT_TOKEN_EFFICIENCY = 0.3
BASELINE_TOKENS_PER_QUESTION = 2000
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
    """Provisional overall score for an accuracy (0-100) and a mean prompt length."""
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


def report() -> dict:
    grid = [{"accuracy": a, "mean_tokens": t, "overall": round(overall(a, t), 3)}
            for a in ACCURACIES for t in TOKENS]
    effs = {t: round(token_efficiency(t), 3) for t in TOKENS}
    pairs = [(100, 300), (300, 600), (300, 1000), (300, 2000), (1000, 2000)]
    breakeven = [{"from": f, "to": t, "accuracy_points": round(breakeven_accuracy_gain(f, t), 3)}
                 for f, t in pairs]
    marginal = {t: round(marginal_cost_per_100_tokens(t), 3) for t in TOKENS}
    return {"weights": [WEIGHT_ACCURACY, WEIGHT_TOKEN_EFFICIENCY],
            "baseline_tokens_per_question": BASELINE_TOKENS_PER_QUESTION,
            "token_efficiency": effs, "overall_grid": grid,
            "breakeven_accuracy_gain": breakeven,
            "accuracy_points_per_100_more_tokens": marginal}


def main(argv) -> int:
    rep = report()
    if "--json" in argv:
        print(json.dumps(rep, indent=1))
        return 0
    print("mean prompt tokens -> token efficiency")
    for t, e in rep["token_efficiency"].items():
        print("  %5d -> %.3f" % (t, e))
    print("overall score (rows: accuracy; columns: mean prompt tokens)")
    print("  acc  " + " ".join("%8d" % t for t in TOKENS))
    for a in ACCURACIES:
        print("  %3d  " % a + " ".join("%8.3f" % overall(a, t) for t in TOKENS))
    print("accuracy points a longer prompt must add to break even")
    for row in rep["breakeven_accuracy_gain"]:
        print("  %5d -> %5d tokens: %.3f" % (row["from"], row["to"], row["accuracy_points"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
