# Results: mirror repair, full count and first index build (job `spark32-build-v1`)

Graded on 2026-10-23 at about 14:20 UTC by AI agents working in the name of MV2 of Munim, Inc.,
against `PREREGISTRATION.md` (written at about 03:10 UTC, before the job ran). CC BY 4.0. Raw
output: `results/` (`fetch.json`, `fetch_files.jsonl`, `full_count.json`, `full_files.jsonl`).

## What happened

The job started at 03:04 UTC and ended at 10:45 UTC with exit 143 (SIGTERM) in its fourth step,
the index build, about 70 minutes into a 240-minute budget. The stop fell inside a planned
maintenance window on the compute machines (10:39-10:49 UTC). Steps 1-3 finished with exit 0.

It ran on a different machine from the pilot (`spark27-fts-v3`), and the `pubmed-baseline` data
volume on that machine was empty. So step 2 did not repair two files in an existing mirror. It
downloaded all 1,306 files fresh (56.2 GB in 44 minutes, one file needed a second attempt), and
step 3 counted every file from scratch (5 h 45 min on 2 workers). We did not foresee this. The
data volume is per machine, not shared.

## Grades: 7 held, 1 missed, 6 ungraded

| # | Prediction | Result | Grade |
|---|---|---|---|
| R1 | Rehash flags exactly 1279 and 1281 as stale; the other 1,304 match | `stale_markers` = [], `files_rehashed` = 0: there were no marked files to check | **Missed** (premise: the mirror was not there) |
| R2 | Both files download again, match NLM's md5, 0 failed, each 60-95 MB | 1279: 77,676,299 B, md5 `51f336e4...`; 1281: 76,367,941 B; 0 failed | Held |
| R3 | Mirror totals 56.20-56.35 GB | 56,245,402,986 B (56.25 GB) | Held |
| C7 | All 1,306 files counted without an error | 1,306 ok, 0 failed | Held |
| C8 | Each repaired file holds 30,000 records; corpus = 39,167,524 | 30,000 and 30,000; 39,167,524 | Held |
| C9 | Exactly 1 duplicate PMID | 1: PMID 25973045, both copies in `pubmed27n0782.xml.gz` | Held |
| C10 | Editorial 749,482-752,500; Historical Article 361,972-362,600 | 750,678; 362,068 | Held |
| B1-B4 | Build stops on its budget; >= 20M records; 1,500-3,000/s; 1,700-2,600 B/record | No `build.json`: the host stopped the step | Ungraded (as pre-registered) |
| B5 | `replaced_total` at most 1 | No `build.json` | Ungraded |
| B6 | Peak memory under 1.2 GB | 1.15 GB for the whole job (the build's first 70 minutes included) | Held |

R2 and R3 held, but not in the way the pre-registration described: the two files were not
repaired, they were downloaded along with all the others. R1 is the one real miss. It will be
re-tested on the machine that holds the old mirror (`spark33-build-v1`, prediction R5).

## The corpus, counted in full

- **39,167,524 records** in 1,306 files: 1,292 files hold exactly 30,000, the last holds 17,568,
  and 13 hold between 29,987 and 30,001.
- 29,051,892 have an abstract (74.17%); 10,944,786 have a PMC id (27.94%).
- **1 duplicate PMID**, 25973045, which appears twice inside the same file
  (`pubmed27n0782.xml.gz`). So the corpus has 39,167,523 distinct PMIDs.
- **750,678 Editorial** (D016421) and **362,068 Historical Article** (D016456) records are in
  the files, although the challenge announcement says editorials and historical articles "will
  be excluded". 0 Preprint (D000076942) records, as the task descriptions say.
- Dates: 11,578 records have a journal date after July 2026, 29,751 entered PubMed after July
  2026, and only 29 have neither a journal nor an electronic date on or before 2026-07-31.
- PMIDs run from 1 to 42,671,487.

These replace the 1,304-file figures in `../fts_pilot/RESULTS.md`. The remaining two files
added 60,000 records, 1,196 editorials and 96 historical articles.

## What changes

- `build_index.py` 0.3 (`../t1_runner/`) writes a line per committed file to `progress.jsonl`
  and handles SIGTERM, so a stopped build leaves a record.
- `spark33-build-v1` continues the build with the fetch and count steps kept in, so it is correct
  on either machine. Its predictions, split by machine, are in
  `PREREGISTRATION-spark33.md`, written before that job was filed.

Contact: MV2, Munim, Inc., mv2@munimtech.com
