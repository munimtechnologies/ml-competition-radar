# Results: BioGen 2024 runs against NLM's expert nuggets (medaesqa-nugget-v2)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Graded 2026-11-01 (about 09:45 UTC) word for word against `PREREGISTRATION-medaesqa-nugget-v2.md`,
which was public before the job read any data (`results-medaesqa-nugget-v2/prereg_public.json`:
seen 2026-11-01 06:09:28 UTC, sha256 `adeb497b...`, match true). No human has checked these numbers.

The job ran on 2026-11-01 from 06:02:59 to 06:11:03 UTC (python:3.12-slim, 1 CPU, 1 GB). Outputs are
counts and scores only (`results-medaesqa-nugget-v2/`); no nugget, question or sentence text is published.

## Checks: 5 of 5 held

| check | result |
|---|---|
| C1 `fetch_public.py` exits 0, both files at their pins | exit 0; `biogen_reuse.py` and `official_biogen2024.json` match |
| C2 `test_medaesqa_nugget`: 10 tests, all pass | "Ran 10 tests", OK |
| C3 `wait_public.py` exits 0 | exit 0, match true |
| C4 run step exits 0, `problem` null, MedAESQA 7,276,948 bytes at its pin | exit 0, null, 7,276,948 bytes, sha256 `a0627421...` |
| C5 `nugget_fields` `{"nuggets": 40}`; match, run map, label agreement as in v1 | `{"nuggets": 40}`; 40 of 40 by id; 30 runs, 29 distinct, every share 1.0; 4,901 same, 5 differ |

## Predictions: 6 of 9 held

| prediction | result | held? |
|---|---|---|
| N1 median nuggets per question 3-15; none without | median 11.5 (min 3, max 31); 0 without; 498 nuggets | yes |
| K1 expert answers' nugget recall >= 50 (positive control) | 89.52 | yes |
| K2 recall against the next question's nuggets <= 10 (negative control) | 0.08 | yes |
| N2 sentence AUROC 0.55-0.75 and above the question baseline (0.538) | 0.645 (question baseline 0.538; 3,956 Required, 956 other) | yes |
| N3 Kendall tau-b, recall (bar 0.6) vs completeness R, >= 0.50 | **0.405** | **no** |
| N4 that tau above sentence length's (0.799) | 0.405 < 0.799 | no |
| N5 partial tau holding length fixed >= 0.10 | 0.299 | yes |
| N6 that tau above content words' (0.852) | 0.405 < 0.852 | no |
| R1 run step at most 5 minutes | 3.1 s (step 4 s) | yes |

## Decision (the rule fixed in advance)

The matcher is **fit**: K1 and K2 hold, so it reads the experts' facts and does not match
unrelated questions. N3 failed, and both the "development yardstick" and the "equal-length only"
outcomes require N3, so **expert-nugget recall is not used** as a Task 2 yardstick, and by the
same rule a rewriting stage waits for the TREC 2025 BioGen judgments.

## What the numbers say (descriptive; nothing below changes the decision)

- **On these 40 questions the official completeness R mostly tracks answer length.** Content
  words per question rank the 30 runs at tau 0.852 and sentences at 0.799. Recall of the experts'
  own facts ranks them at 0.405, and holding length fixed still leaves a partial tau of 0.299.
  The two scores agree only in part, which is what the controls cannot tell apart: either the word
  matcher misses facts that assessors credit, or completeness R credits things the experts did
  not list.
- Sensitivity bars, reported in advance as not decisive: tau 0.573 at bar 0.4, 0.606 at 0.5,
  0.414 at 0.7, 0.276 at 0.8; the continuous "soft" recall reaches 0.675. Every one is below both
  length baselines.
- Nugget precision (share of a run's sentences that cover a nugget) ranks runs against official
  precision at tau 0.410 at bar 0.6.
- The expert answers cover 89.5% of their own nuggets at bar 0.6. That control is easy if the
  nuggets were drawn from those answers, and MedAESQA does not say how they were written.

## Limits

40 questions; 30 runs from 5 teams, so tau mostly reflects gaps between teams. Completeness R is
averaged over all 65 questions, recall here over 40. Word containment misses paraphrase. We do not
know whether the experts saw the runs. No language model is involved anywhere.

## Files

`results-medaesqa-nugget-v2/`: `nugget.json` (totals, controls, taus), `nugget_runs.json` (per run:
official scores, recall and precision per bar, length), `fetch_public.json`, `prereg_public.json`.

Contact: MV2, Munim, Inc., mv2@munimtech.com
