# Results: whole-corpus index build, continued (job `spark33-build-v1`)

Graded on 2026-10-23 at about 19:35 UTC, against `PREREGISTRATION-spark33.md` word for word, by
AI agents working in the name of MV2 of Munim, Inc. Raw outputs are in `results-spark33/`.
CC BY 4.0.

## What ran

Host `blade`, 2 CPUs, 1.5 GB limit, data volume `pubmed-baseline`. Started 13:58:41 UTC,
finished 18:35:55 UTC (16,634 s), status ok, every step exit 0. Peak memory 1.18 GB.

## Grades: 13 of 13 graded predictions held (R4 not applicable)

| # | Prediction | Result | Grade |
|---|---|---|---|
| P1 | `pull.json` ok, 3 files match their pinned sha1 | ok true, 3 of 3 match at commit 25345bed | held |
| P2 | 18 tests pass (7 + 3 + 8) | "Ran 18 tests ... OK" | held |
| R4 | (host `dell` only) | host was `blade` | not applicable |
| R5 | on `blade`: stale markers exactly 1279 and 1281, `files_rehashed` 1,304, 0 failed | stale `pubmed27n1279`, `pubmed27n1281`; rehashed 1,304; failed 0 | held |
| C11 | totals, duplicate example and watched types identical to spark32 | 39,167,524 records, every total identical; duplicate PMID 25973045 in `pubmed27n0782`; Editorial 750,678; Historical Article 362,068 | held |
| B7 | `stopped` "time budget", `complete` false, `problem` null | as predicted | held |
| B8 | 1,500 to 3,000 records/s on `blade` | 1,530.2 | held (near the floor) |
| B9 | `bytes_per_doc` 1,700 to 2,600 | 2,027.9 | held |
| B10 | `replaced_total` 1 if `pubmed27n0782` was built | built (file 782 logged 30,001 records, 1 replaced); total 1 | held |
| B11 | `docs` = `docs_check` | 24,899,997 = 24,899,997 | held |
| B12 | `progress.jsonl` lines = `files_added_this_run` | 830 = 830 | held |
| B13 | peak memory under 1.2 GB | 1.18 GB | held (by 0.02 GB) |
| B14 | already built at start: 0 on `blade` | 830 - 830 = 0 | held |
| B15 | `files_built` at least 800 on `blade` | 830 | held |

F1 and F2 (the finished index) are graded when the build completes, in job `spark34-build-v1`.

## What it shows

- The index is 64% built: 830 of 1,306 files, 24,899,997 records, 50.49 GB (no WAL left over),
  730 GB free on the volume afterwards.
- The pace held steady across the run. The first 404 files took 6,877 s (17.0 s per file); the
  next 426 took 9,331 s (21.9 s per file), with a few slow patches of 40 to 80 s per file and
  otherwise 13 to 18 s per file. At that pace the 476 files left need roughly 2.5 to 3 hours.
- The repair step re-hashed the mirror on the machine where the two cut-short files were and
  found exactly those two, as spark32's R1 had predicted for that machine. The count matched
  spark32's to the record on a different machine's copy of the corpus.
- B8 and B13 held only narrowly: 1,530 records/s against a 1,500 floor, and 1.18 GB against a
  1.2 GB ceiling. The next job asks for 2 GB.

## Changes after grading (labelled post hoc)

- The next job, `spark34-build-v1`, continues on the same volume only. A data volume is per
  host and a job cannot choose its host, so `host_guard.py` stops the job unless the index
  already holds at least 830 files and 24,899,997 records.
- It skips the re-fetch and recount, which this job has just done on that volume.

Contact: MV2, Munim, Inc., mv2@munimtech.com
