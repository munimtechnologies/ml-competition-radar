# t1_runner: SPARK Task 1 runner (stage 1, BM25)

Part of `spark-pubmed/`, MV2 of Munim, Inc.'s open groundwork for the NIH/NLM SPARK PubMed/PMC
Challenge, Task 1 (Known-Item & Provenance Retrieval). The code was made with AI agents working
in his name. Code Apache-2.0; notes CC BY 4.0.

## Files

- `build_index.py`: resumable whole-corpus SQLite FTS5 (BM25) index of the SPARK PubMed files
  (title, abstract, MeSH; rowid = PMID; meta table with year, journal, PMC id). Python standard
  library only. Its fake-data tests (`test_build_index.py`) passed in the sealed job
  `spark28-test-v1` on 2026-10-22.
- `t1.py`: questions -> BM25 candidates -> cutoff policy -> Task 1 submission JSONL
  (`metadata`: team_id, submission_id, info_need_id, info_need; `response`: up to five PMIDs),
  a format validator, and a scorer (MRR@5, hit share, items returned and wrong citations for ten
  fixed cutoff policies, plus recall of the target in the first 1/5/10/20/50/100 candidates).
- `test_t1.py`: fake-data tests, with no network.
- `PREREGISTRATION.md`: predictions about the cutoff policies, written before any score existed.

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

The tests in `test_t1.py` were queued as the sealed job `spark30-t1-test-v1` when this folder
was published; their result had not been read yet. The whole-corpus index does not exist yet
(the corpus mirror and FTS5 pilot job is still running), so nothing here has scored a real
question. The submission format follows the task description; the official sample submission
file was not posted on the challenge page as of 2026-10-23.

Contact: MV2, Munim, Inc., mv2@munimtech.com
