# Pre-registration: biogen-llm-v1 (a small open LLM as a gated conflict judge)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
01:30 UTC, before the job runs. The job's workdir carries a copy of this file.

## Question

SPARK Task 2 scores conflict coverage. On the 11,927 TREC 2024 BioGen judgments that quote a
passage, no NLI cross-encoder met the bar (base: AUROC 0.735, entry F1 0.158; large: AUROC 0.731,
entry F1 0.203; large or polarity clash: entry F1 0.218). Half of the contradicting passages
(140 of 275) carry a negation word, against about a tenth of the supporting ones. The rule in
`RESULTS-biogen-nli-large.md` named the next candidate: an open-weight LLM judge run only on
pre-marked pairs. Inside the negation gate (1,432 judgments: 140 Contradicts, 185 Neutral, 1,107
Supports), can Qwen2.5-1.5B-Instruct tell the contradicting passages apart well enough to beat the
best NLI flag overall?

## Job

`biogen-llm-v1`, kind `compete`, image `python:3.12`, 4 CPUs, 5 GB, 480 min, volume
`pubmed-baseline` (`/data/biogen2024/assessments.json`, downloaded and hash-checked if missing).

- Model: `Qwen/Qwen2.5-1.5B-Instruct` at revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`,
  licence Apache-2.0 (Hugging Face card and LICENSE file), 8 files with pinned sizes
  (`model.safetensors` 3,087,467,144 bytes), loaded in bfloat16 on the CPU with
  `low_cpu_mem_usage` (accelerate 1.1.1), torch 2.5.1+cpu, transformers 4.46.3.
- Prompt (chat template, system "You are a careful biomedical evidence assessor."): the quoted
  passage (first 250 words), the answer sentence, and "Does the passage support the statement,
  contradict it, or neither? Answer with one letter: A = supports, B = contradicts, C = neither."
  The next-token logits of B, A and C, softmaxed over the three letters, stand in for NLI's
  (contradiction, entailment, neutral). Pairs outside the gate get (0, 0, 1).
- Scoring: `nli_check.py` 0.2.0's `run()` unchanged (fetched at commit 29d7d00c with
  `cue_check.py` 0.1.0 by `fetch_code.py` 0.4.0), plus the same blocks over the gated judgments
  only (`gate`). After the first 20 judged pairs the run stops if the projected time is over 6 h.

## Checks (the job stops, rather than grades, if one is false)

- C1. `fetch_code.py` exits 0. Tests: `test_fetch_code` 6, `test_llm_judge` 6, `test_nli_check` 10,
  `test_cue_check` 6, all pass (28).
- C2. `model.json`: every pinned file present at its pinned size, `problems` empty.
- C3. `llm.json` counts equal biogen-nli-large-v1's: 14,763 judgments, 0 unknown labels, 11,927
  scored, 11,592 unique pairs, census 202 contradicting topic-papers, 168 mixed.

## Predictions (graded to the letter in `RESULTS-biogen-llm.md`)

- **G1.** `gate`: 1,432 judgments, labels exactly 140 Contradicts, 185 Neutral, 1,107 Supports.
- **G2.** `scoring.judged` (distinct gated pairs) between 1,300 and 1,432.
- **G3.** The model answers in the format: `letter_mass_mean` at least 0.5.
- **G4.** Inside the gate, Contradicts-vs-rest AUROC (`gate.entry.contradicts_vs_rest.auroc`) is
  above 0.60 (the gate's base rate is 9.8%).
- **G5.** Overall entry Contradicts-vs-rest argmax F1 (`entry.contradicts_vs_rest.argmax.f1`)
  between 0.10 and 0.30.
- **G6.** Its argmax recall is at most 0.509 (the gate's ceiling; a check of the plumbing).
- **G7.** `ms_per_judged_pair` between 1,500 and 15,000, or the probe stops the run (then G1-G6
  are not graded).

Recorded, not predicted: argmax precision, slot and topic-paper blocks, best-F1 oracle, the
`union_polarity_clash` fusion, the gate's confusion matrix, `clipped`, peak memory.

## Decision rule (fixed now)

The LLM flag is adopted as the Task 2 conflict-flag candidate (compose.py 0.3.0, run only where
the negation gate passes) only if all three hold: entry argmax F1 at least 0.25 (clearly above
the best NLI flag's 0.218), entry argmax precision at least 0.30, and `ms_per_judged_pair` at most
10,000. Otherwise compose.py keeps the polarity-clash flag, and the result is written up as found.
If the probe stops the run, v2 uses Qwen2.5-0.5B-Instruct (Apache-2.0) with its own
pre-registration. Exit 137: v2 at 6 GB. Exit 143/255: re-file unchanged.

## Limits

One prompt, one model, no tuning: a negative result says this setup fails, not that LLM judges
do. The labels are BioGen 2024's passage-level judgments, whose own between-slot agreement on
Contradicts is 0.39. The gate caps recall at 0.509. Questions and passages are BioGen's, not
SPARK's. Only counts and scores are published, never passage or sentence text. No human has
checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
