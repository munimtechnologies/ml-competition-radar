# Pre-registration: biogen-nli-large-v1 (does a larger NLI model trained on harder data recover BioGen's Contradicts labels better?)

MV2 of Munim, Inc. (made with AI agents working in his name). CC BY 4.0. Written 2026-10-29
between 15:20 and 16:10 UTC, before the job was filed and before any of its output existed. The
job's workdir carries a copy of this file, so the copy is on disk when the job starts, whether or
not this public commit has landed by then.

## Why

biogen-nli-v1 (`RESULTS-biogen-nli.md`) found that cross-encoder/nli-deberta-v3-base separates the
TREC 2024 BioGen assessors' Contradicts judgments only at entry AUROC 0.735 and slot argmax F1
0.161. That is below the decision bar (0.75 and 0.20), and level with a one-line negation regular
expression (`RESULTS-biogen-cue.md`). The rule's next candidates were a biomedical NLI model or an
open-weight LLM judge. The two public MedNLI models we checked declare no licence on Hugging Face
(read 2026-10-29), so they cannot go into a public SPARK system. This job tries
MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli instead (MIT; 435M parameters). It is
trained on MNLI, FEVER-NLI, ANLI, LingNLI and WANLI, the last three built from harder,
adversarial examples. The base model was trained on SNLI and MNLI. It is the largest model that
fits a CPU-only, 4 GB job on these 11,592 pairs in a few hours.

Prior art (searched 2026-10-28/29): the TREC 2025 BioGen overview (arXiv 2603.21582) reports that
teams used MNLI-style models and LLM prompting for contradicting citations; its best Contradicts F1
is 15.67 against LLM-judged labels. We found no published measure of an NLI model against the
2024 assessors' passage-level labels other than biogen-nli-v1. This is a development measurement
for MV2's system, not a new method.

## What runs

`nli_check.py` 0.2.0 (in this folder; 0.1.0 plus `--model/--revision`, two fixed cue
combinations, and `--pairs-out`), with `cue_check.py` 0.1.0 (unchanged, public at 69119036) beside
it. Job `biogen-nli-large-v1`, CPU only, 4 CPUs, 4 GB limit, data volume pubmed-baseline:

1. `python -m unittest -v test_nli_check` (10 tests, fake data, no torch).
2. `fetch-model --model MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli --revision
   b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`: the same 7 file names as biogen-nli-v1, saved under
   /data/models/; bytes and sha256 of each recorded in model.json.
3. `run` with the same model and revision, max 256 tokens, fp32, batch 16, 4 threads, on the same
   pinned assessments (sha256 78449ef2...066d). Writes nli.json (counts and scores only) and
   pairs.jsonl (each distinct pair's three probabilities keyed by a SHA-1 of the pair; no text;
   kept for later combinations, not published).

Same levels and metrics as biogen-nli-v1. New in 0.2.0, per entry and per slot, Contradicts vs
rest:

- `gate_neg_passage`: argmax contradiction only where the passage has a negation cue.
- `union_polarity_clash`: argmax contradiction, or compose.py's polarity_clash rule.

## Checks (if one fails, the predictions are not graded until the cause is known)

- K1: sha256 matches; `judgments` = 14,763, `unknown_label` = 0, `scored` = 11,927,
  `unique_pairs` = 11,592 (all as in biogen-nli-v1).
- K2: `census` gives 202 topic-papers with a Contradicts judgment, 168 of them also Supports.
- K3: model.json lists the 7 files with exactly these bytes (Hugging Face tree at the pinned
  revision, read 2026-10-29): config.json 1,056; model.safetensors 870,182,606; spm.model
  2,464,616; tokenizer.json 8,648,889; tokenizer_config.json 395; special_tokens_map.json 156;
  added_tokens.json 18. The run step does not stop with "unexpected id2label".

## Predictions

- L1: all 10 tests pass; every step exits 0.
- L2: `truncated` is between 10 and 40 (biogen-nli-v1: 21, same DeBERTa-v3 vocabulary).
- L3: entry Contradicts-vs-rest AUROC of p(contradiction) is between 0.70 and 0.85.
- L4: that AUROC is higher than biogen-nli-v1's 0.735.
- L5: entry argmax contradiction: precision at most 0.30, recall between 0.10 and 0.50.
- L6: entry oracle best F1 for Contradicts is below 0.3881 (the assessors' between-slot
  specific agreement, biogen-slots-v1).
- L7: entry Supports-vs-rest AUROC of p(entailment) is between 0.60 and 0.85.
- L8: `gate_neg_passage` has a higher entry argmax precision than the plain argmax.
- L9: `union_polarity_clash` has a slot argmax F1 at least as high as the plain slot argmax F1.
- L10: `ms_per_pair` between 250 and 1,500; the whole job at most 360 minutes; peak memory at
  most 4 GB.

Slot and topic-paper numbers other than L9 are recorded, not predicted.

## Decision rule (fixed now)

- If the entry AUROC is at least 0.75 and the slot argmax F1 is at least 0.20, compose.py 0.3.0's
  conflict flag uses this model. Its threshold is fixed from this run's slot-level oracle, and the
  flag is tested on t2dev's conflict cases, pre-registered first. If the plain model misses the
  bar but `union_polarity_clash` reaches slot F1 0.20 with entry AUROC at least 0.75, the union is
  used the same way.
- Otherwise no NLI cross-encoder is used. compose.py 0.3.0 keeps only polarity_clash (per
  biogen-cue-v1). The next candidate is an open-weight LLM judge, run only on pairs this model or
  the negation cue already marks, to keep CPU time bounded. It is pre-registered separately.
- `gate_neg_passage` is recorded for comparison only. biogen-cue-v1's rule already rejected a
  negation gate, because it would drop about half of the contradictions.

## Limits

- The assessors' quoted passages make this optimistic: a real system must find the passage
  itself in the abstract.
- Contradicts is rare (2.3% of scored judgments) and the least repeatable label, so the labels
  themselves cap any score. The oracle F1 is chosen on the evaluation data.
- WANLI and ANLI differ from biomedical text; no domain-specific training is involved.
- BioGen 2024 questions and answers differ from SPARK's; T2QS is still undefined.
- NIST states no licence for the assessments, so only counts and scores are published.
- No human has checked any of this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
