# Results: BioGen 2024 runs against NLM's expert nuggets (medaesqa-nugget-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Graded 2026-10-31 (about 11:10 UTC) against `PREREGISTRATION-medaesqa-nugget.md`, word for word.
The job ran once on 2026-10-31, about 09:07 UTC (python:3.12-slim, 1 CPU, 1 GB limit). Its
outputs, counts and scores only, are in `results-medaesqa-nugget/` (`nugget.json`,
`nugget_runs.json` and the three `*_public.json` checks).

**Outcome: 4 of 4 checks, 2 of 10 predictions. The test could not be run as designed: in the
public MedAESQA file (`medaesqa_v1.json`, 7,276,948 bytes, sha256 `a062742c...c383`), the
`expert_curated_nuggets` value of all 40 items reads as empty (None), although the dataset's
README lists the field. With no nuggets, the controls cannot be computed, so by the rule fixed in
advance nothing is adopted.** This is a finding about the released data, not about the matcher.

## Checks

| check | pre-registered | observed | held |
|---|---|---|---|
| C1 | `wait_public.py` exits 0; `match` recorded | exit 0; public copy seen 09:07:11 UTC, sha256 `c4d0b5a0...103e` on both sides, `match` true | yes |
| C2 | `test_medaesqa_nugget` runs 9 tests, all pass | "Ran 9 tests", OK | yes |
| C3 | the job's `biogen_reuse.py` and `official_biogen2024.json` match the public copies | `match` true for both | yes |
| C4 | run step exits 0, `problem` null, BioGen files as pinned, MedAESQA 7,276,948 bytes | exit 0; `problem` null; all as stated | yes |

## Predictions

| | pre-registered | observed | held |
|---|---|---|---|
| M1 | 40 questions, all matched (by id or text), 40 distinct; 30 runs scored | 40 matched by id (0 by text, 0 unmatched), 40 distinct, 30 runs | yes |
| M2 | 30 MedAESQA runs mapped to 30 distinct BioGen runs, each sharing >= 90% | 30 runs, every one sharing 100% of its scored sentences, but **29** distinct: M5 and M22 both map to webis-3 with a tie (runner-up share 1.0), because webis-3 and webis-5 have the same sentences on these 40 questions | **no** |
| N1 | median nuggets per question 3-15; none without | 0 nuggets in all 40 (`nugget_shapes`: NoneType 40) | **no** |
| K1 | expert answers' own nugget recall >= 50 | not computable (no nuggets) | **no** |
| K2 | next-question nugget recall <= 10 | not computable | **no** |
| N2 | sentence AUROC 0.55-0.75 and above the question baseline | 0.50 (every cover is 0); question baseline 0.538 | **no** |
| N3 | tau-b (bar 0.6), nugget recall vs completeness R, >= 0.50 | not computable | **no** |
| N4 | that tau above the length baseline's | not computable (length baseline on these 40 questions: 0.799; words per question: 0.852) | **no** |
| N5 | partial tau with length held fixed >= 0.10 | not computable | **no** |
| R1 | run step <= 5 minutes | 4.0 s | yes |

## Decision (fixed in advance)

The matcher counts as fit only if K1 and K2 hold. Neither could be computed, so **nothing is
adopted**. `biogen-reuse-emb-v1` was not adopted either (`RESULTS-biogen-reuse-emb.md`).

## What the run did establish

- **MedAESQA's machine answers are the BioGen 2024 runs.** All 40 MedAESQA questions carry the
  BioGen 2024 question ids. Every one of M1-M30 shares 100% of its scored sentences with one BioGen
  run, and for sentences paired by position the sentence labels agree in 4,901 of 4,906 cases
  (4 more are labelled only in BioGen, 12 only in MedAESQA). The one ambiguity is webis-3 and
  webis-5, which have identical answer sentences on these questions (their official scores differ
  over all 65).
- On these 40 questions, answer length ranks the 30 runs against official completeness R at tau
  0.80 (sentences) and 0.85 (content words).

## Not yet known

The job used the loader's normalised field lookup, which returns None both when a key is missing
and when it holds null, so it cannot tell those apart. `bioace-zip-v1` (filed 2026-10-31) lists
every MedAESQA field with how often it is present, null or empty. It also lists the members of
NLM's BioACE data bundle (`bioace-data-models.zip`, linked from BioACE's download script) with
HTTP range requests, without downloading the whole archive. The BioACE paper (arXiv 2602.04982)
scores answers against expert nuggets for these questions, so the nuggets may be released there
rather than in MedAESQA. If they are, a new pre-registration will score the runs against them;
this one is not re-run on different data.

## Limits

No human has checked these counts. The README of MedAESQA (OSF ydbzq, modified 2025-04-16) lists
`expert_curated_nuggets`; we have not contacted NLM about it.

Contact: MV2, Munim, Inc., mv2@munimtech.com
