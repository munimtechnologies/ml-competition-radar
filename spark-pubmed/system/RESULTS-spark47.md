# Results: spark47-immutable-v1 (does the whole system run with no write access to the index?)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Graded 2026-10-29 against
`PREREGISTRATION-spark47.md` (public commit fdd0efe2, 08:39 UTC, before the job started).

**All 3 checks and all 7 predictions held.** Run as a user who cannot write the index's folder,
`spark_t1.py` 0.2.0 with `--immutable` answered all 43 L questions and gave exactly the rankings
it gave with write access. The same command without `--immutable` failed with `attempt to write a
readonly database`.

## Job

`spark47-immutable-v1` ran on the Blade from 2026-10-29 14:52 to 16:12 UTC (80.7 min), in one
sealed `python:3.12` container with 2 CPUs and a 3 GB limit, on a host shared with other jobs.
All 3 setup steps and 10 run steps exited 0. The code was fetched from this repository at pinned
commits, with this folder's `spark_t1.py` 0.2.0, `test_spark_t1.py`, `ro_db.py` 0.1.0,
`nobody_run.py` 0.1.0 and `test_nobody_run.py` copied over them (all published in commit
9a64c8e3). Both runs of the system went through `nobody_run.py` as uid/gid 65534.

## Checks

| | Check | Result |
|---|---|---|
| C1 | `fetch_code.py` exits 0 | held (14 files, all at their pinned sizes) |
| C2 | `test_spark_t1.py` 11 pass; `test_nobody_run.py` 4 pass | held (11 of 11; 4 of 4) |
| C3 | `host_guard.py` passes (1,306 files, 39,167,523 documents) | held |

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| P1 | the control (no `--immutable`, uid 65534) exits non-zero, last stderr line contains `readonly database` (graded because `before.beside` was only `spark_full.db`) | exit 1; `sqlite3.OperationalError: attempt to write a readonly database` | held |
| P2 | the `--immutable` run exits 0 as uid 65534; `run.json` version 0.2.0, immutable, complete, 43 answered, no problems | exit 0; all as stated; 0 questions without candidates | held |
| P3 | top-5 MRR 0.1628, top-1 MRR 0.0930 | 0.1628 and 0.0930 | held |
| P4 | `agree.json` common 43, same order 43 | common 43, same order 43, same set 43, same first 43 | held |
| P5 | no `-wal` or `-shm` beside the index after the run | both null before and after, for the control and the run | held |
| P6 | median seconds per question 60-150 | 107.1 | held |
| P7 | peak memory <= 3 GB | 2.14 GB | held |

## Timing, recorded not predicted

| L set, 43 questions | median total s | BM25 median s | cross-encoder median s | p95 total s | max total s | sum s |
|---|---|---|---|---|---|---|
| spark47 (`--immutable`, uid 65534) | 107.1 | 40.0 | 62.8 | 154.2 | 178.9 | 4,647.3 |
| spark43 (plain open, root) | 109.3 | 51.0 | 62.7 | 159.6 | 191.1 | 4,941.2 |

The cross-encoder took the same time. BM25 was 11 s faster at the median, but the host is shared
and the runs were on different days' loads, so this is not read as an effect of `immutable`
(which skips locking and could plausibly help slightly).

## What follows

- **The Task 1 system runs from a read-only index.** The `Dockerfile`'s read-only mount and
  `--immutable` entry point stand. No copy or conversion of the 92.5 GB index is needed.
- Next, job `spark48-image-v1` (`PREREGISTRATION-spark48.md`) runs the entry point on
  `python:3.12-slim` with `/app` laid out exactly as the `Dockerfile`'s COPY lines lay it out,
  with no network in its run steps, on the 65 BioGen questions.

## Files

`results-spark47/` holds the control's and the run's `nobody.json` (exit code, last stderr lines,
side files), and the run's `run.json`, `scores.json` and `agree.json`. These are counts, times and
command lines only, with no question text and no PMIDs.

## Limits

File ownership (uid 65534 on a root-owned volume) stands in for a `:ro` mount. The L questions
are proxy questions written by AI agents. The timing comes from one shared 2-CPU slot, not the
challenge's hardware. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
