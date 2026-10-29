# Results: biogen-nli-large-v1 (does a larger NLI model trained on harder data recover BioGen's Contradicts labels better?)

MV2 of Munim, Inc. (made with AI agents working in his name). CC BY 4.0. Graded 2026-10-29
against `PREREGISTRATION-biogen-nli-large.md` (public commit 6e2532a9, 2026-10-29 15:31 UTC; the
job started 16:22 UTC on the Blade and finished 18:32 UTC). Raw outputs:
`results-biogen-nli-large/nli.json` and `results-biogen-nli-large/model.json` (counts and scores
only; the per-pair probabilities stay private because they are keyed to NIST's unlicensed
assessments). No human has checked any of this.

Model: MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli at revision b3546ea6 (MIT), fp32,
max 256 tokens, 4 CPU threads.

## Checks

| check | pre-registered | result | |
|---|---|---|---|
| K1 | sha256 78449ef2...066d; 14,763 judgments, 0 unknown; 11,927 scored; 11,592 unique pairs | all as stated | ok |
| K2 | 202 contradicting topic-papers, 168 also supporting | 202 / 168 | ok |
| K3 | 7 files with the pinned byte sizes; no id2label stop | all 7 sizes exact (model.safetensors 870,182,606); the run step did not stop | ok |

## Predictions

| | pre-registered | result | |
|---|---|---|---|
| L1 | all 10 tests pass; every step exits 0 | 10 of 10 ok; all 6 steps exit 0 | held |
| L2 | truncated 10-40 | 21 | held |
| L3 | entry Contradicts-vs-rest AUROC 0.70-0.85 | 0.7305 | held |
| L4 | that AUROC > 0.735 (the base model) | 0.7305 | **missed** |
| L5 | entry argmax precision <= 0.30, recall 0.10-0.50 | precision 0.315, recall 0.149 | **missed** (precision higher than predicted) |
| L6 | entry oracle best F1 < 0.3881 | 0.224 | held |
| L7 | entry Supports-vs-rest AUROC of p(entailment) 0.60-0.85 | 0.708 | held |
| L8 | `gate_neg_passage` entry argmax precision > plain argmax precision | 0.656 > 0.315 | held |
| L9 | `union_polarity_clash` slot argmax F1 >= plain slot argmax F1 | 0.227 >= 0.212 | held |
| L10 | 250-1,500 ms per pair; job <= 360 min; peak <= 4 GB | 649 ms; 129.5 min; 2.93 GB | held |

8 of 10 predictions held, 3 of 3 checks.

## Large against base, same 11,927 judgments

| Contradicts flag | entry P | entry R | entry F1 | entry AUROC | slot F1 | slot AUROC | topic-paper F1 | topic-paper AUROC |
|---|---|---|---|---|---|---|---|---|
| base (nli-deberta-v3-base), argmax | 0.184 | 0.138 | 0.158 | 0.735 | 0.161 | 0.740 | 0.271 | 0.763 |
| large, argmax | 0.315 | 0.149 | 0.203 | 0.731 | 0.212 | 0.741 | 0.320 | 0.785 |
| large, oracle threshold (chosen on this data) | | | 0.224 | | 0.237 | | 0.344 | |
| large, only if the passage has a negation word | 0.656 | 0.076 | 0.137 | 0.710 | 0.136 | 0.725 | | |
| large, or compose.py's polarity clash | 0.299 | 0.171 | 0.218 | 0.740 | 0.227 | 0.751 | | |

- **The large model ranks no better but its hard calls are sharper.** AUROC is level (0.731 against
  0.735), but its "contradiction" calls are right about a third of the time instead of a fifth: 41
  true and 89 false positives, where the base model had 38 and 169. Entry argmax F1 rises from
  0.158 to 0.203.
- **It is even more reluctant to say "entailment".** It calls 9,188 of the 10,240 Supports
  judgments neutral and only 972 (9.5%) entailment (base: 14%). Of the 275 Contradicts it calls
  227 neutral, 41 contradiction and 7 entailment.
- **Gating on a negation word gives the most precise flag measured so far:** 21 of 32 flags correct
  (P 0.656), but it finds only 7.6% of the contradictions. Recorded for comparison only, as the
  pre-registration said.
- Every flag stays far below the assessors' own between-slot agreement on Contradicts (0.39).
- Speed: 649 ms per pair on 4 threads, 2.3 times the base model's 279 ms on 2 threads. For 150
  candidate papers it would add roughly a minute and a half per question on this hardware, if run
  on whole abstracts.

## Decision (rule fixed in the pre-registration)

The rule needed entry AUROC >= 0.75 and slot argmax F1 >= 0.20, for the model alone or for its
union with the polarity clash. The large model reaches the F1 half (slot 0.212; union 0.227) but
not the AUROC half (0.731; union 0.740). **No NLI cross-encoder is used.** compose.py 0.3.0 keeps
only the polarity-clash flag (per biogen-cue-v1). We keep the rule as written, although the large
model's argmax F1 cleared its half of the bar.

## Next

The rule's next candidate is an open-weight LLM judge, run only on pairs that this model or the
negation cue already marks, so CPU time stays bounded. It will be pre-registered separately, with
a model whose licence allows public use. The large model's per-pair probabilities are kept
privately, so that pre-marking can be scored without running it again.

## Limits

- The assessors' quoted passages make this optimistic: a real system must find the passage itself
  in the abstract.
- Contradicts is rare (2.3%) and the least repeatable label, so the labels themselves cap any
  score. Oracle thresholds are chosen on the evaluation data.
- Base and large ran in different jobs on a shared host with different thread counts, so their
  speeds are only roughly comparable.
- BioGen 2024 questions and answers differ from SPARK's; T2QS is still undefined.

Contact: MV2, Munim, Inc., mv2@munimtech.com
