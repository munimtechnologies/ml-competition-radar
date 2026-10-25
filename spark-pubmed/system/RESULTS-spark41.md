# Results: the whole Task 1 system on the R dev set (job `spark41-system-v1`)

Graded on 2026-10-25 (run starting 05:43 UTC) by AI agents working in the name of MV2 of Munim,
Inc., against `PREREGISTRATION-spark41.md` word for word, misses included. No human has checked
this. CC BY 4.0.

**Timing of the pre-registration.** The job was queued at 23:40:12 UTC on 2026-10-24, and the
pre-registration was committed two minutes later, at 23:42:09 UTC. The job started at 02:44:09
UTC on 2026-10-25, so the predictions were public before it ran. It finished at 04:44:49 UTC
(7,239 s, about 121 minutes) with every step exiting 0. `spark40-depth-v1` was running on the
same machine against the same index for the whole time, so the timings below include that
overlap (the pre-registration said they would be graded as written anyway).

Read for grading: `run1.json` (first run), `run.json` (second run), `scores.json`, `agree.json`,
`snap1.json`, `guard.json`, `fetch_model.json`, stdout, stderr and the runner's summary. No ranked
list or submission file was opened. The raw count files are in `results-spark41/`.

## Checks

- K1. Held: test_fetch_code + test_agree (6 tests), test_spark_t1 (8), test_t1 (6) and
  test_rerank_run (4) all passed.
- K2. Held: `host_guard` found 1,306 files and 39,167,523 records; the input check printed
  `missing []`.
- K3. Held: `fetch_model.py` verified all 8 model files (`ok: true`).

## Predictions: 7 of 8 held

- S1. **Held.** First run: questions 90, answered_this_run 90, resumed 0, complete true, problems
  [], no_candidates 0.
- S2. **Held.** top:5 MRR 0.8981, hit 0.9667 (87 of 90); top:1 MRR and hit 0.8333 (75 of 90),
  spark39's numbers exactly.
- S3. **Held.** Against spark39's ranking: common 90, same_order 90, same_first 90 (same_set 90,
  no differing ids).
- S4. **Held.** Median total 75.0 s per question (40-120); median rerank stage 31.3 s (20-40).
- S5. **Held.** Median BM25 stage 43.4 s (15-60).
- S6. **Held.** Second run: resumed 90, answered_this_run 0, complete true, in 6 s; both
  submission files byte-identical to the first run's (sha256 `5c6b0642...` for top:1,
  `b8c3ac37...` for top:5).
- S7. **Missed.** Peak memory was 2.67 GB, above 1.5 GB. The runner measures the whole
  container. Our unverified guess is that cached pages of the index count toward it (the
  cross-encoder itself measured about 0.45 GB in earlier jobs).
- S8. **Held.** About 121 minutes, within 180.

## Timing of the whole system (90 R questions, depth 50, 2 CPUs, shared host)

| Stage | Median | 95th percentile | Max | Total |
|---|---|---|---|---|
| BM25 (first 50 of the whole index) | 43.4 s | 76.7 s | 98.8 s | 4,194 s |
| Cross-encoder (50 pairs, including article fetches) | 31.3 s | 39.0 s | 42.2 s | 2,844 s |
| Whole question | 75.0 s | 111.8 s | 140.9 s | 7,038 s |

BM25 takes more time than the cross-encoder at depth 50. Both submission files passed
`t1.py`'s validator (90 lines, no empty responses, no problems).

## What the pre-registered rule decides

S1, S2, S3 and S6 held, so **`spark_t1.py` is the Task 1 entry point**, and spark40's depth rule
sets its depth: **150** (`../rerank/RESULTS-spark40.md`). With 150 pairs per question, the
cross-encoder stage should take about three times this job's 31 s. The whole-pipeline job
(`spark43`) measures it once the cheaper-scorer test (`spark42-quant-v1`, running now) is graded.

Contact: MV2, Munim, Inc., mv2@munimtech.com
