# Pre-registration: whole-corpus index build, continued (job `spark33-build-v1`)

Written on 2026-10-23 at about 14:30 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

Job `spark32-build-v1` (graded in `RESULTS.md`) repaired the mirror and counted the whole
corpus: 39,167,524 records in 1,306 files. Its fourth step, the first 240 minutes of the index
build, was stopped by the host after about 70 minutes (exit 143, SIGTERM, at 10:45 UTC, during a
planned maintenance window). `build_index.py` 0.2 writes `build.json` only at the end, so that
step left no record of how far it got.

That job also showed something we had not planned for. It ran on a different machine from the
pilot, and its `pubmed-baseline` data volume there was empty. It downloaded all 1,306 files again
instead of repairing two. So the machine that runs this job decides what is already on disk.
The predictions below are split by the `host` field of the job's `summary.json`.

## Fixed design

- `build_index.py` 0.3 (in `../t1_runner/`): same index, same SQL, same BM25 weights. Changes:
  every committed file is appended and fsynced to `progress.jsonl`; SIGTERM rolls back the file
  in progress and writes `build.json` with `stopped` = "signal 15"; `docs` is now summed from the
  `built` table, with the old `COUNT(*)` kept as `docs_check`; `bytes_per_doc` now counts the
  WAL file too. 7 fake-data tests (2 new).
- `pull_pinned.py` fetches `fetch_corpus.py` 0.2.2, `full_count.py` 0.2 and
  `test_corpus_build.py` from this repository at commit `25345bed` and writes each one only if
  its git blob sha1 matches. 3 tests.
- Steps (2 CPUs, 1.5 GB, data volume `pubmed-baseline`):
  1. `pull_pinned.py`
  2. `python -m unittest -v test_pull_pinned test_build_index test_corpus_build`
  3. `fetch_corpus.py --rehash` with the same arguments as `spark32-build-v1`
  4. `full_count.py` with the same checkpoint folder
  5. `build_index.py --detail full --max-minutes 270 --min-free-gb 100`

## Predictions

Code
- P1. `pull.json` reports `ok` true, and all 3 files match their pinned sha1.
- P2. All 18 tests pass (7 + 3 + 8).

Repair (by host)
- R4. If the host is `dell` (where `spark32-build-v1` left a fresh mirror): 0 stale markers,
  `files_rehashed` = 1,306, 0 failed files.
- R5. If the host is `blade` (where the pilot's mirror should still be): the stale markers are
  exactly `pubmed27n1279` and `pubmed27n1281` (spark32's R1, retested where those files are),
  `files_rehashed` = 1,304, 0 failed files. If the volume there turns out not to hold the old
  mirror, R5 is reported as "premise not met", not as held or missed.

Count
- C11. The `totals`, `duplicate_examples` and both watched-type totals in `full_count.json` are
  identical to `spark32-build-v1`'s: 39,167,524 records, duplicate PMID 25973045, 750,678
  Editorial, 362,068 Historical Article.

Build (first 270 minutes)
- B7. `stopped` = "time budget", `complete` false, `problem` null.
- B8. `docs_per_second_this_run`: 400 to 1,500 on `dell`; 1,500 to 3,000 on `blade`. (The pilot
  built 2,500 records/s on `blade`; `spark32-build-v1`'s count on `dell` read about 945 records/s
  per worker.)
- B9. `bytes_per_doc` is between 1,700 and 2,600.
- B10. `replaced_total` is 1 if `pubmed27n0782.xml.gz` (the file that holds PMID 25973045 twice)
  has been built by the end, and 0 otherwise.
- B11. `docs` equals `docs_check`.
- B12. `progress.jsonl` has exactly `files_added_this_run` lines.
- B13. The job's peak memory stays under 1.2 GB.
- B14. Files already built when this run started (`files_built` - `files_added_this_run`): between
  60 and 250 on `dell` (what `spark32-build-v1`'s 70 minutes committed), and 0 on `blade`.
- B15. `files_built` at the end is at least 300 on `dell` and at least 800 on `blade`.

If the host stops the job again, B7, B8 and B15 are ungraded. B9-B12 and B14 are graded from
the `build.json` the signal handler writes. If no `build.json` exists at all, that is a miss
for the 0.3 change, reported as such.

## For the finished index (graded when `complete` is true, in a later job)

- F1. `docs` = 39,167,523 (39,167,524 records minus the 1 replaced duplicate).
- F2. The database is between 75.2 and 101.8 GB (88.5 GB from the pilot, +-15%).

Query speed on the whole corpus will be pre-registered before the scoring job, as planned.

Contact: MV2, Munim, Inc., mv2@munimtech.com
