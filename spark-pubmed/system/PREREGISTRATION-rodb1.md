# Pre-registration: rodb-check-v1 (does `ro_db.py` open the real index read-only?)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-28, about
17:00 UTC, before the job runs.

**Question.** The SPARK Task 1 image may get the 92.5 GB whole-corpus FTS5 index on a read-only
mount. The index uses SQLite's WAL journal, which SQLite can read without write access only under
the conditions in [sqlite.org/wal.html](https://www.sqlite.org/wal.html), section 5. `ro_db.py`
0.1.0 opens it with `mode=ro&immutable=1`. Does that work on the real index, in the `python:3.12`
image the system runs in?

**Job.** `rodb-check-v1` (1 CPU, 1 GB, 30 min, no network; the `pubmed-baseline` volume). It runs
the unit tests (`test_ro_db.py`, `test_probe.py`), then `probe.py --db /data/spark28/spark_full.db`.
The probe reads the 20 header bytes and the schema table's object names through the immutable
connection as root. It then opens the index as uid/gid 65534, which has no write access to the
index folder, once with the immutable URI and once with a plain path. It writes nothing under
`/data`. The job may run while spark43 reads the same index; reading cannot disturb it.

**Predictions** (graded to the letter in `RESULTS-rodb1.md`):

- **P0.** `before.sqlite_version` is 3.22.0 or later.
- **P1.** `before.journal_mode` is `wal`.
- **P2.** `before.side_files.wal` is null or 0, so `ro_db` allows the immutable connection.
- **P3.** `immutable_root.ok` is true, with at least 2 schema objects, in under 5 s.
- **P4.** If `beside` lists only `spark_full.db`, `after` shows no `-wal` and no `-shm` either.
  (If side files already exist, for example because spark43 is reading the index, P4 is not graded.)
- **P5.** `nobody_immutable` exits 0 and prints the same object count as P3.
- **P6.** Every unit test passes. `test_fts5_bm25` runs (it is not skipped).
  `test_read_only_folder` is skipped, because the job runs as root.

**Recorded, not predicted:** `nobody_plain` (a plain open without write access). Its result depends
on whether spark43 has the index open at the same moment (SQLite's condition 1).

**Rules.** Exit 3 means the job landed on a host without the index: re-file it unchanged. Results
are published as counts and names of schema objects only, with no corpus text.

**What follows.** If P1-P5 hold, `spark_t1.py` 0.2.0 gets an `--immutable` flag that uses
`ro_db.connect`, and the Docker image mounts the index read-only. If P2 fails, the index has to be
checkpointed once (or converted with `PRAGMA journal_mode=DELETE`) while no job is reading it. If
P5 fails while P3 holds, the cause is recorded first and nothing changes in the system.
