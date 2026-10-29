# Results: rodb-check-v1 (does `ro_db.py` open the real index read-only?)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Graded 2026-10-29 against
`PREREGISTRATION-rodb1.md`, which was committed before the job ran.

**All 7 predictions held.** The 92.5 GB whole-corpus FTS5 index is in WAL mode with no `-wal`
or `-shm` file beside it, and `ro_db.connect(..., immutable=True)` opens it both as root and as a
user with no write access (uid 65534). A plain open by that same user fails.

## Job

`rodb-check-v1` ran on the Blade on 2026-10-29 from 02:54 to 02:57 UTC (205 s; 1 CPU, 1 GB, no
network), in `python:3.12` (Python 3.12.15, SQLite 3.46.1). spark43, the only other job that
reads the index, had finished at 01:48 UTC, so nothing else had it open.

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| P0 | SQLite 3.22.0 or later | 3.46.1 | held |
| P1 | `journal_mode` is `wal` | `wal` | held |
| P2 | `side_files.wal` null or 0 | null (and `shm` null) | held |
| P3 | immutable open as root works, >= 2 schema objects, < 5 s | ok, 11 objects, 0.001 s | held |
| P4 | (only `spark_full.db` beside it) no `-wal`/`-shm` afterwards | `beside` = `spark_full.db`; after: both null | held |
| P5 | `nobody_immutable` exits 0 with the same object count | exit 0, 11 | held |
| P6 | all unit tests pass; `test_fts5_bm25` runs; `test_read_only_folder` skipped (root) | 12 run, 11 passed, 1 skipped (`test_read_only_folder`); `test_fts5_bm25` ok | held |

**Recorded, not predicted:** `nobody_plain` (a plain `sqlite3.connect` by uid 65534) exited 1 with
`sqlite3.OperationalError: attempt to write a readonly database`. With no `-shm` file present and
no write access to the folder, SQLite cannot read the WAL-mode index without `immutable`
(condition 1 of [sqlite.org/wal.html](https://www.sqlite.org/wal.html), section 5, was not met).
So a read-only mount needs either the immutable open or a one-time conversion of the index.

The 11 schema objects are `built`, `docs`, `docs_config`, `docs_content`, `docs_data`,
`docs_docsize`, `docs_idx`, `meta`, `settings` and two automatic indexes
(`results-rodb1/rodb.json`).

## What follows

As pre-registered, `spark_t1.py` 0.2.0 gets `--immutable`, which opens the index with
`ro_db.connect(immutable=True)`, and the planned Docker image mounts the index read-only. No
conversion or checkpoint of the shared index is needed. Job `spark47-immutable-v1` checks that the
whole system runs that way (`PREREGISTRATION-spark47.md`).

Contact: MV2, Munim, Inc., mv2@munimtech.com
