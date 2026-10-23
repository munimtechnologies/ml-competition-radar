# Pre-registration: finishing the whole-corpus index, plus a first query-speed probe (job `spark34-build-v1`)

Written on 2026-10-23 at about 19:40 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

Job `spark33-build-v1` (graded in `RESULTS-spark33.md`, 13 of 13 predictions held) indexed 830 of
the 1,306 SPARK PubMed files on the `blade` host: 24,899,997 records, 50.49 GB, 1,530 records/s,
stopped cleanly by its 270-minute budget. 476 files (14,267,526 records) are left.

The `pubmed-baseline` data volume exists separately on each host, and a job cannot choose its
host. On `dell` the volume holds only the partial index left by `spark32-build-v1` (killed after
about 70 minutes), so the same build step there would start a second index almost from scratch.
New in this job: `host_guard.py` reads the index's `built` table first and stops the job (exit 3)
unless at least 830 files and 24,899,997 records are already in it.

Also new: `query_probe.py` times 20 fixed general health questions (written for the probe, not
taken from any challenge or test set) at depth 50, a cold pass then a warm pass, with each query
cut off after 60 s. The pilot measured a 30 ms median at 1.2 million records; the scoring and
reranking jobs need the figure for the whole corpus.

## Fixed design

- `build_index.py` 0.3, unchanged from spark33 (same index, SQL and BM25 weights). No `--optimize`.
- Steps (2 CPUs, 2 GB, data volume `pubmed-baseline`, 340 minutes):
  1. `python -m unittest -v test_build_index test_spark34` (7 + 8 fake-data tests)
  2. `host_guard.py --min-built 830 --min-docs 24899997`
  3. `build_index.py --detail full --max-minutes 270 --min-free-gb 100`
  4. `query_probe.py --k 50 --query-seconds 60`
- The mirror is not re-fetched or recounted: spark33 re-verified all 1,306 files against their
  md5 files 0 to 5 hours earlier, and nothing else writes to that volume.

## Predictions

Code and host
- P1. All 15 tests pass.
- G1. If the host is `blade`: `guard.json` has `ok` true, `files_built` 830, `docs` 24,899,997,
  `last_file` `pubmed27n0830.xml.gz`.
- G2. If the host is `dell`: the guard stops the job with exit 3, and `guard.json` shows either
  no index or at most 250 built files. Steps 3 and 4 do not run, everything below is "premise
  not met", and the job is filed again unchanged as `-v2`.

Build (graded only if G1 holds)
- B1. `stopped` is null, `complete` true, `problem` null, `files_built` 1,306, `files_left` 0,
  `files_added_this_run` 476.
- B2. `docs` = `docs_check` = 39,167,523 (39,167,524 records minus the one replaced duplicate,
  PMID 25973045). This is F1 from the spark33 pre-registration.
- B3. `replaced_total` = 1.
- B4. `db_bytes` between 80.3 and 96.0 GB, so `bytes_per_doc` is between 2,050 and 2,450
  (spark33: 2,027.9 after 830 files; later files carry more abstracts). This is inside F2
  (75.2 to 101.8 GB) from the spark33 pre-registration, which is graded as well.
- B5. Build `seconds` between 7,000 and 14,000, so `docs_per_second_this_run` between 1,019 and
  2,038.
- B6. `progress.jsonl` has exactly 476 lines.
- B7. `free_gb_after` is at least 600.
- B8. The job's peak memory stays under 1.5 GB.

Query speed on the finished index (graded only if B1 holds)
- Q1. No query is cut off in either pass, and every query returns 50 PMIDs (`results_min` 50).
- Q2. Warm-pass median between 200 ms and 5,000 ms.
- Q3. The cold-pass median is at least the warm-pass median.
- Q4. Warm-pass maximum under 30,000 ms.

If the host stops the job (exit 143), B1, B5 and the Q predictions are ungraded; B2-B4, B6 and B7
are graded from the `build.json` that the signal handler writes, and the job is filed again
unchanged.

Contact: MV2, Munim, Inc., mv2@munimtech.com
