# t1_runner: SPARK Task 1 runner (stage 1, BM25)

Part of `spark-pubmed/`, MV2 of Munim, Inc.'s open groundwork for the NIH/NLM SPARK PubMed/PMC
Challenge, Task 1 (Known-Item & Provenance Retrieval). The code was made with AI agents working
in his name. Code Apache-2.0; notes CC BY 4.0.

## Files

- `build_index.py` 0.3: resumable whole-corpus SQLite FTS5 (BM25) index of the SPARK PubMed
  files (title, abstract, MeSH; rowid = PMID; meta table with year, journal, PMC id). Python
  standard library only. Each corpus file is one transaction, so a stopped build resumes at the
  first file not yet committed. New in 0.3: every committed file is logged to `progress.jsonl`,
  and SIGTERM rolls back the file in progress and still writes `build.json` (a host stop of job
  `spark32-build-v1` left no record of the build). Fake-data tests: `test_build_index.py`.
- `host_guard.py`: stops a job (exit 3) unless the index on its data volume already holds a
  given number of files and records. A data volume is per host and a job cannot choose its host.
- `fetch_code.py`: fetches `t1.py`, `test_t1.py`, `build_index.py` and `host_guard.py` from a
  pinned commit of this folder and checks each file's size and line count. A re-filed job runs
  the identical published code this way.
- `query_probe.py`: times 20 fixed general health questions (written for the probe) on a cold
  and a warm pass. Tests for both: `test_spark34.py`.
- `t1.py`: questions -> BM25 candidates -> cutoff policy -> Task 1 submission JSONL
  (`metadata`: team_id, submission_id, info_need_id, info_need; `response`: up to five PMIDs),
  a format validator, and a scorer (MRR@5, hit share, items returned and wrong citations for ten
  fixed cutoff policies, plus recall of the target in the first 1/5/10/20/50/100 candidates).
- `test_t1.py`: fake-data tests, with no network.
- `PREREGISTRATION.md`: predictions about the cutoff policies, written before any score existed.
- `PREREGISTRATION-spark35.md`: predictions for `spark35-score-v1`, the first scoring job on the
  whole-corpus index. It also grades `PREREGISTRATION.md` and `../dev_sets/PREREGISTRATION.md`
  B1-B4.
- `RESULTS-spark35.md`, `results-spark35/`: the graded first whole-corpus scoring.

## Use

```
python t1.py devsets --r-questions ../dev_sets/r_questions/r_questions.jsonl \
    --r-titles ../dev_sets/r_questions/r_titles.jsonl \
    --landmarks ../dev_sets/results/landmarks_verified.json --out-dir dev
python t1.py run --db spark_full.db --needs dev/needs_l.jsonl --out-dir out_l --depth 100 --gold dev/gold.jsonl
python t1.py score --ranked out_l/ranked.jsonl --gold dev/gold.jsonl --out-dir out_l
python t1.py validate out_l/submission.jsonl
```

## Status (2026-10-24)

The whole-corpus index is complete (`../corpus_build/RESULTS-spark34.md`): 1,306 files and
39,167,523 records.

First whole-corpus scores (`RESULTS-spark35.md`, job `spark35-score-v2`; 12 of 18 predictions
held), BM25 alone, top 5 returned:

| set | questions | MRR@5 | target in top 5 | in top 20 | in top 100 | median query |
|---|---|---|---|---|---|---|
| R (AI-written from one abstract) | 90 | 0.793 | 0.878 | 0.933 | 0.989 | 35.4 s |
| RT (the record's own title) | 90 | 0.959 | 0.989 | 1.000 | (depth 20) | 15.8 s |
| headline L (landmark papers) | 43 | 0.086 | 0.140 | 0.326 | 0.465 | 27.2 s |

R is easy for word overlap and L is hard. BM25 scores are too flat for a score cut-off to drop
wrong citations. Next: a query speed fix (`../speed/`, job `spark37-speed-v1`) and the MedCPT
rerank of L and BioGen (`../rerank/PREREGISTRATION-spark36.md`, job `spark36-rerank-v1`).

The submission format follows the task description, because the official sample submission
file was not posted on the challenge page as of 2026-10-24.

Contact: MV2, Munim, Inc., mv2@munimtech.com
