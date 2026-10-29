# Pre-registration: spark47-immutable-v1 (does the whole system run with no write access to the index?)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-29, about
09:00 UTC, before the job runs.

## Question

`RESULTS-rodb1.md` showed that `ro_db.connect(..., immutable=True)` opens the real 92.5 GB WAL-mode
index for a process with no write access to it, and that a plain open from the same process fails.
`spark_t1.py` 0.2.0 adds `--immutable`, which opens the index through `ro_db.connect`. Does the
whole Task 1 system (BM25, then the MedCPT cross-encoder at depth 150) run end to end that way, and
give exactly the rankings it gave with write access?

## Job

`spark47-immutable-v1` (2 CPUs, 3 GB, 180 min; the `pubmed-baseline` volume). Code: `t1_runner`,
`rerank` and `system` at the commits `fetch_code.py` 0.2.0 pins, with this run's `spark_t1.py`
0.2.0, `test_spark_t1.py`, `ro_db.py` 0.1.0 and `nobody_run.py` 0.1.0 copied over them.
`nobody_run.py` runs one command as uid/gid 65534, which cannot write the index's folder (the way
the challenge's image sees a read-only mount), and records the index's `-wal`/`-shm` files before
and after. Steps: unit tests; `host_guard.py`; a control (the system on one L question, BM25 only,
**without** `--immutable`, as 65534, expected to fail); the system on the 43 L questions with
`--immutable` as 65534; `t1.py score`; `agree.py rank` against spark40's depth-300 rerank read at
depth 150 (the comparison spark43 matched 43 of 43).

## Checks (the job stops, rather than grades, if one is false)

- C1. `fetch_code.py` exits 0 (every pinned file has its recorded size).
- C2. `test_spark_t1.py`: 11 tests pass. `test_nobody_run.py`: 4 tests pass.
- C3. `host_guard.py` passes (1,306 built files, 39,167,523 documents).

## Predictions (graded to the letter in `RESULTS-spark47.md`)

- **P1.** The control exits non-zero and the last line of its stderr contains `readonly database`
  (graded only if its `before.beside` lists only `spark_full.db`, that is, no other process had the
  index open; otherwise recorded).
- **P2.** The `--immutable` run exits 0 as uid 65534: `run.json` shows version `0.2.0`,
  `immutable` true, `complete` true, 43 answered, no problems.
- **P3.** Top-5 MRR 0.1628 and top-1 MRR 0.0930 (exact to 4 decimals), as spark43 gave.
- **P4.** `agree.json`: `common` 43, `same_order` 43.
- **P5.** No `-wal` or `-shm` file beside the index after the run (`after.side_files` both null).
- **P6.** Median seconds per question between 60 and 150 (spark43 on L: 109.3).
- **P7.** Peak memory at most 3 GB (spark43 peaked at 2.65 GB over all three sets).

Recorded, not predicted: the BM25 and cross-encoder medians next to spark43's on the same
questions (51.0 s and 62.7 s). The host is shared, so a difference is not read as an effect of
`immutable`.

## Rules and what follows

Exit 3 (no index on this host) or 143/255 (host stopped): re-file unchanged. Exit 137: v2 at 4 GB.
If P2-P5 hold, the Docker image's entry point gets `--immutable` and the index is mounted
read-only (`Dockerfile` in this folder already says so; it is still not built). If P2 holds but
P3 or P4 fails, the system keeps the plain open until the difference is explained. Results are
published as counts only (no question text).

Contact: MV2, Munim, Inc., mv2@munimtech.com
