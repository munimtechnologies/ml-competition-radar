# Pre-registration: first BM25 scoring on the whole SPARK PubMed index (job `spark35-score-v1`)

Written on 2026-10-23 at about 23:50 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

Job `spark34-build-v1` (graded in `corpus_build/RESULTS-spark34.md`) finished the whole-corpus
index on the `blade` host: 1,306 of 1,306 files, 39,167,523 records, 92.5 GB. Its 20-question
probe measured a 6.1 s warm median at depth 50 (8.6 s cold, slowest 46.2 s). The index exists
only on that host's copy of the `pubmed-baseline` data volume.

This job runs, for the first time on the whole corpus, the two sets of predictions that were
registered before any index existed:
- `dev_sets/PREREGISTRATION.md` B1-B4 (2026-10-22), and
- `t1_runner/PREREGISTRATION.md` P1-P6 (2026-10-23, about 01:35 UTC).
Those are graded exactly as written there. This file adds predictions about the job itself.

## Fixed design

- Code: `t1.py` (280 lines, unchanged from `t1_runner/`), `build_index.py` 0.3 (the version that
  built the index), `host_guard.py` 0.1. Six fake-data tests (`test_t1`).
- Dev files downloaded inside the job from commit `5d8eb4735644b495354c9924f1100327339ddb1f`
  (`r_questions.jsonl`, `r_titles.jsonl`, `landmarks_verified.json`).
- Steps (1 CPU, 2 GB, data volume `pubmed-baseline`, 240 minutes): tests; `host_guard.py
  --min-built 1306 --min-docs 39167523`; download; `t1.py devsets`; L at depth 100 with the gold
  file (for P6); score L; R at depth 100; score R; RT (titles) at depth 20; score RT; then copy
  the three `ranked.jsonl` files to `/data/spark35/` so the reranking job can reuse the BM25
  candidates on the same volume without querying again.
- Grading map (from the scoring-job draft written on 2026-10-23 at about 01:30 UTC): B1 = RT `top:1` hit >= 0.90; B2 = L `top:5`
  MRR in [0.15, 0.50]; B3 = L `top:5` hit < 0.70; B4 = R `top:5` MRR in [0.20, 0.60]; P5 from
  R `run.json` (`median_ms`, `p95_ms`); P6 from L `run.json` `gold_missing_from_index`.

## Already known (checks, not predictions)

- K1. `t1.py devsets` gives r 90, rt 90, l 43 and `duplicate_ids` []. If l is not 43, nothing is
  graded until the cause is found.
- K2. P5 was written for a 1.2-million-record pilot. The spark34 probe already makes a median
  under 500 ms on the whole corpus very unlikely. P5 is still graded as written.

## New predictions

- S1. If the host is `blade`: `guard.json` has `ok` true, `files_built` 1,306, `docs`
  39,167,523. If the host is `dell`: exit 3, nothing below is graded ("premise not met"), and the
  job is filed again unchanged as `-v2`.
- S2. All 6 tests pass.
- S3. R `median_ms` is between 3,000 and 40,000 (longer questions than the probe's, so more
  OR terms).
- S4. RT `median_ms` is lower than R `median_ms`.
- S5. L `median_ms` is between 2,000 and 40,000.
- S6. `no_candidates` is 0 and `validate.problems` is empty for all three sets.
- S7. The job finishes with every step at exit 0 in under 180 minutes.
- S8. Peak memory stays under 1.5 GB.

## How it will be read (written now)

- If P1 holds (recall@20 at least 0.10 above `top:5` hit on L and R), the next job reranks the
  first 50 BM25 candidates with the MedCPT cross-encoder (fp32, graded in `rerank/RESULTS.md`)
  and scores again with the same `t1.py score`.
- If the R median is over 20 s, a separate job pre-registers a speed fix (an FTS5 `optimize`
  merge, or fewer OR terms) before any larger question set runs. Compute time is one of the
  challenge's tiebreakers.
- No dev number tunes BM25 here. The policies, weights and depths were fixed before this job.

Limits: AI-written proxy questions are not NLM's expert questions. Query time depends on the
host and on what else runs there. The penalty for wrong citations is unpublished.

Contact: MV2, Munim, Inc., mv2@munimtech.com
