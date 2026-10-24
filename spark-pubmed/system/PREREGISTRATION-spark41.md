# Pre-registration: spark41-system-v1 (the whole Task 1 system on the R dev set)

MV2 of Munim, Inc. Written by AI agents working in his name on 2026-10-24 (about 23:55 UTC),
before the job was filed. CC BY 4.0.

## Why

Every SPARK Task 1 result so far ran the two stages as separate jobs: BM25 lists from one job,
reranked by `rerank/rerank_run.py` in a later one. The challenge needs one no-network system that
turns a questions file into submission files and whose compute time can be stated. `system/spark_t1.py`
0.1.0 is that entry point (BM25 -> MedCPT cross-encoder -> `top:5` and `top:1` files, resumable,
timed per question). This job checks that it reproduces the graded spark39 result on R exactly,
measures whole-pipeline time per question for the first time, and checks that a stopped run
resumes without changing its output. It does not choose the rerank depth (spark40-depth-v1 does);
it uses depth 50, the depth spark39 used.

## Setup

- Blade volume `pubmed-baseline`: index `/data/spark28/spark_full.db` (host_guard: 1,306 files,
  at least 39,167,523 records); questions = the 90 R questions read from
  `/data/spark35/ranked_r.jsonl` (its candidates are ignored); gold `/data/spark35/gold.jsonl`;
  reference ranking `/data/spark39/ranked_r.jsonl` (spark39-cutoff-v1: rerank_run.py, depth 50,
  2 threads, batch 8); model `/data/models/medcpt-ce-71caf65`.
- Code: t1_runner @ ce37c206 and rerank @ 99ade999 (fetch_code.py, sizes checked), plus
  `system/spark_t1.py` 0.1.0 and `system/agree.py` 0.1.0 from this commit.
- Command: `spark_t1.py --scorer medcpt --depth 50 --threads 2 --batch 8 --team-id MV2`, then the
  same command again on the same output folder (resume), 2 CPUs, python:3.12, torch 2.5.1+cpu,
  transformers 4.46.3.
- spark40-depth-v1 (filed about 22:40 UTC) may be running on the same machine against the same
  index; if so, S4, S5 and S8 are graded as written anyway and the overlap is reported.

## Checks (must all pass, or nothing below is graded)

- K1 Unit tests pass: test_fetch_code, test_agree (job folder); test_spark_t1, test_t1,
  test_rerank_run (fetched code folder).
- K2 host_guard passes and every input above exists.
- K3 fetch_model.py verifies the model files.

## Predictions

- S1 First run's `run.json`: questions 90, answered_this_run 90, resumed 0, complete true,
  problems [], no_candidates 0.
- S2 `t1.py score` on its ranked.jsonl: top:5 MRR 0.8981 +/- 0.0005 with hit 0.9667 (87 of 90);
  top:1 MRR and hit 0.8333 (75 of 90). These are spark39's numbers.
- S3 `agree.py rank` (k = 5) against spark39's ranking: common 90, same_order >= 88,
  same_first >= 89.
- S4 Median total time per question 40-120 s; median rerank stage 20-40 s (spark39's
  cross-encoder median was 26.7 s per question, before article fetches).
- S5 Median BM25 stage 15-60 s (R's full-length questions; spark35 measured 35.4 s at depth 100).
- S6 The second run: resumed 90, answered_this_run 0, complete true, and `agree.py same` finds both
  submission files byte-identical to the first run's.
- S7 Peak memory <= 1.5 GB.
- S8 Job wall time <= 180 min.

## Decision rule

If S1, S2, S3 and S6 hold, `system/spark_t1.py` becomes the Task 1 entry point, and spark40's
depth rule sets its `--depth`. If S2 or S3 fails, the cause (BM25 ties at the depth boundary,
batching, a code difference) is found before any further SPARK job is filed.

## What gets published

`run.json` (first and second run), `scores.json`, `agree.json`, the resume check's output and the
job's step list: counts, timings and question ids only. The ranked lists and submission files
carry question text and are not published.
