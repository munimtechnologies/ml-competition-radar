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

## Use

```
python t1.py devsets --r-questions ../dev_sets/r_questions/r_questions.jsonl \
    --r-titles ../dev_sets/r_questions/r_titles.jsonl \
    --landmarks ../dev_sets/results/landmarks_verified.json --out-dir dev
python t1.py run --db spark_full.db --needs dev/needs_l.jsonl --out-dir out_l --depth 100 --gold dev/gold.jsonl
python t1.py score --ranked out_l/ranked.jsonl --gold dev/gold.jsonl --out-dir out_l
python t1.py validate out_l/submission.jsonl
```

## Status (2026-10-23)

The whole-corpus index is complete (`../corpus_build/RESULTS-spark34.md`): 1,306 files and
39,167,523 records. A 20-question probe took a 6.1 s median at depth 50. The first dev-set
scoring job, `spark35-score-v1`, is queued with its predictions written first. Nothing here has
scored a real question yet. The submission format follows the task description, because the
official sample submission file was not posted on the challenge page as of 2026-10-23.

Contact: MV2, Munim, Inc., mv2@munimtech.com
