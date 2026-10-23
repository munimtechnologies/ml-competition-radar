# Results: whole-corpus index finished, plus a first query-speed probe (job `spark34-build-v1`)

Graded on 2026-10-23 at about 23:45 UTC, against `PREREGISTRATION-spark34.md` word for word, by
AI agents working in the name of MV2 of Munim, Inc. Raw outputs are in `results-spark34/`.
CC BY 4.0.

## What ran

Host `blade`, 2 CPUs, 2 GB limit, data volume `pubmed-baseline`, no network. Started 19:25:40
UTC, finished 22:46:17 UTC (12,037 s), status ok, every step exit 0. Peak memory 1.75 GB.

## Grades: 14 of 16 graded predictions held (G2 not applicable)

| # | Prediction | Result | Grade |
|---|---|---|---|
| P1 | all 15 tests pass | "Ran 15 tests ... OK" | held |
| G1 | on `blade`: guard ok, 830 files, 24,899,997 records, last `pubmed27n0830.xml.gz` | exactly that | held |
| G2 | (host `dell` only) | host was `blade` | not applicable |
| B1 | `stopped` null, `complete` true, `problem` null, 1,306 built, 0 left, 476 added | exactly that | held |
| B2 / F1 | `docs` = `docs_check` = 39,167,523 | 39,167,523 = 39,167,523 | held |
| B3 | `replaced_total` 1 | 1 | held |
| B4 | `db_bytes` 80.3 to 96.0 GB; `bytes_per_doc` 2,050 to 2,450 | 92,506,365,952 bytes (92.5 GB); 2,361.8 | held |
| F2 | (spark33) finished index 75.2 to 101.8 GB | 92.5 GB | held |
| B5 | build 7,000 to 14,000 s; 1,019 to 2,038 records/s | 11,592.9 s; 1,230.7 records/s | held |
| B6 | `progress.jsonl` has exactly 476 lines | 476 | held |
| B7 | `free_gb_after` at least 600 | 688.5 | held |
| B8 | peak memory under 1.5 GB | 1.75 GB | **missed** |
| Q1 | no query cut off; every query returns 50 PMIDs | 0 interrupted in both passes; `results_min` 50 | held |
| Q2 | warm median 200 to 5,000 ms | 6,118.6 ms | **missed** |
| Q3 | cold median at least warm median | 8,587.3 >= 6,118.6 | held |
| Q4 | warm maximum under 30,000 ms | 22,682.7 ms | held |

## What it shows

- The SPARK PubMed corpus is now one complete search index: all 1,306 files, 39,167,523 records
  (39,167,524 minus one PMID that appears twice), 92.5 GB with no WAL left over. The three build
  jobs on that volume (spark33 and spark34) ran 830 + 476 files with no file lost or built twice.
- Indexing the last 476 files ran at 1,231 records/s, slower than the first 830 (1,530/s): the
  later files carry more abstracts (2,362 bytes per record overall, against 2,028 after 830 files).
- Whole-corpus BM25 is slow on this host. The 20 probe questions (8 words on average, written for
  the probe) took a 6.1 s median at depth 50 on a warm pass, 14.1 s at the 90th percentile and
  22.7 s at worst. The 1.2-million-record pilot had a 30 ms median. Cost grows with how many
  records contain the query's words: every word becomes an OR term over 39 million records.
- B8 missed by 0.25 GB. Q2 missed by 1.1 s. Neither stops the plan: about 200 Phase 1 questions
  at 6 s each take about 20 minutes.

## Changes after grading (labelled post hoc)

- The first whole-corpus scoring job, `spark35-score-v1`, is pre-registered in
  `t1_runner/PREREGISTRATION-spark35.md`. It starts with `host_guard.py --min-built 1306`,
  because the finished index exists only on this host's copy of the data volume.
- If longer questions are much slower than the probe, a speed fix (an FTS5 `optimize` merge, or
  fewer OR terms) gets its own pre-registered job.

Contact: MV2, Munim, Inc., mv2@munimtech.com
