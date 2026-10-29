# Results: spark43-system-v1 (the whole Task 1 system at depth 150, all 198 development questions)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Graded 2026-10-29 against
`PREREGISTRATION-spark43.md`, which was committed before the job ran.

**All 3 checks and all 5 predictions held.** The system (`spark_t1.py` 0.1.1 at commit 4765a24,
fetched from this repository at pinned commits) reproduced the depth-150 rankings that chose its
depth, to the item, and ran in 6 h 21 min on 2 CPUs.

## Job

`spark43-system-v1` ran on the Blade from 2026-10-28 19:27 to 2026-10-29 01:48 UTC (22,843 s), in
one sealed `python:3.12` container with 2 CPUs and a 4.5 GB limit, on a host shared with other
jobs. All 3 setup steps and 21 run steps exited 0.

## Checks

| | Check | Result |
|---|---|---|
| C1 | every fetched file matches the pinned tree (`fetch_code.py` exit 0) | held |
| C2 | all unit tests pass (fetch_code, spark_t1, agree, t1, rerank_run, t2dev) | held (every test step exited 0) |
| C3 | host_guard: full index present (1,306 built files, 39,167,523 documents) | held |

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| P1 | top-5 MRR within +/-0.005 of L 0.1628, BioGen 0.4274, R 0.9130 | L 0.1628, BioGen 0.4274, R 0.9130 (exact) | held |
| P2 | same top-5 order on >= 95% of common questions; common = 43, 65, 90 | same order 43/43, 65/65, 90/90 | held |
| P3 | whole job <= 540 min | 380.7 min | held |
| P4 | median s/question between 60 and 150 on each set | L 109.3, BioGen 82.6, R 135.2 | held |
| P5 | peak memory <= 4.5 GB | 2.65 GB | held |

## Timing (from each set's `run.json`)

| Set | Questions | Median total s | BM25 median s | Cross-encoder median s | p95 total s | Max total s | Sum s |
|---|---|---|---|---|---|---|---|
| L | 43 | 109.3 | 51.0 | 62.7 | 159.6 | 191.1 | 4,941.2 |
| BioGen | 65 | 82.6 | 21.9 | 57.7 | 113.9 | 180.2 | 5,354.3 |
| R | 90 | 135.2 | 52.9 | 80.7 | 182.9 | 230.5 | 12,385.5 |
| All | 198 | | | | | | 22,681.0 |

- Over all 198 questions the system averaged 114.6 s per question: BM25 took 8,874.6 s (39%) and
  the cross-encoder 13,806.6 s (61%).
- The cross-encoder's median works out at 385 (BioGen), 418 (L) and 538 (R) ms per (question,
  paper) pair for 150 pairs. spark40 measured 351-508 ms, so R ran slower here.
- **Not predicted, recorded:** BM25 was slower than the 17-43 s median assumed when P3 was written:
  51.0 s on L and 52.9 s on R (21.9 s on BioGen). spark41 measured 43.4 s on R at depth 50. The
  host was shared, so this is not read as a property of the code. BM25 is now the larger target if
  compute time decides a tie.
- Other figures: recall@10 L 0.372, BioGen 0.769, R 0.989; top-1 MRR L 0.093, BioGen 0.323,
  R 0.844 (`results-spark43/*-scores.json`).

## What follows

- `spark_t1.py` at depth 150 is the Task 1 system. Its rankings are reproducible end to end from
  the public code.
- `spark_t1.py` 0.2.0 adds `--immutable` (`RESULTS-rodb1.md`). Job `spark47-immutable-v1` runs the
  system that way with no write access to the index (`PREREGISTRATION-spark47.md`), before the
  Docker image is built.

## Files

`results-spark43/` holds each set's `scores.json`, `agree.json` and `run.json` (counts and times
only; no question text, no PMIDs).

## Limits

L and R are proxy questions written by AI agents; BioGen counts unjudged papers as wrong. The
timing is one shared 2-CPU container slot, not the challenge's hardware.

Contact: MV2, Munim, Inc., mv2@munimtech.com
