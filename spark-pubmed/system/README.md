# system: the SPARK Task 1 system (questions in, submission files out)

MV2 of Munim, Inc. Made with AI agents working in his name. Code Apache-2.0; notes CC BY 4.0.

`spark_t1.py` is the one command the challenge's no-network Docker image runs. Per question it
takes BM25's first `--depth` candidates from the whole-corpus FTS5 index (`../t1_runner/t1.py`),
rereads them with NCBI's MedCPT cross-encoder (`../rerank/rerank_run.py`), and writes one
submission file per cut-off policy (default `submission_top5.jsonl` and `submission_top1.jsonl`,
the two planned submissions), each checked with `t1.py`'s validator.

- **Resumable.** Each answered question goes to `ranked.jsonl` at once (flushed and fsynced), so
  a stopped run continues at the first unanswered question (`--max-minutes` stops it cleanly
  between questions; exit code 4). Rows are reused only if the question text, depths and scorer
  match.
- **Timed.** Every question records its BM25, rerank and total milliseconds; `run.json` gives the
  median, 95th percentile, maximum and total, because compute time breaks ties in the challenge.
- **No network.** The model loads from a local folder with `HF_HUB_OFFLINE=1` and
  `TRANSFORMERS_OFFLINE=1`; nothing opens a connection.
- **Input.** JSONL with `info_need_id` and `info_need` at the top level or under `metadata` (the
  submission format), or one JSON list. The id is echoed as given.

```
python spark_t1.py --db spark_full.db --questions questions.jsonl --out-dir out \
    --scorer medcpt --model-dir medcpt-ce --team-id TEAM          # depth 150 by default
python spark_t1.py ... --scorer none      # BM25 only, no torch needed
```

`agree.py` checks that the system reproduces an earlier ranking and that a resumed run writes
byte-identical submission files. Since 0.1.1, `agree.py rank --b-depth D` reads a deeper rerank the
way `../rerank/depth_curve.py` does (only reranked items whose BM25 rank is at most D), so the
system at depth 150 can be compared with spark40's depth-200 and depth-300 reranks. `Dockerfile`
is the planned image.

| File | What it is |
|---|---|
| `PREREGISTRATION-spark41.md` | Predictions for job `spark41-system-v1`, written before it ran |
| `RESULTS-spark41.md` | Grades: 3 of 3 checks and 7 of 8 predictions held |
| `results-spark41/` | That job's run, score, agreement and resume-check counts (no question text) |

## Status (2026-10-25, about 19:30 UTC)

- `RESULTS-spark41.md`: on the 90 R questions at depth 50, the whole system reproduced spark39's
  graded ranking exactly (same top five on 90 of 90; top:5 MRR 0.8981, top:1 0.8333). A second run
  on the same folder resumed all 90 answers in 6 s and wrote byte-identical submission files.
  Median time per question was 75.0 s on 2 CPUs (BM25 43.4 s, cross-encoder 31.3 s), on a host
  shared with another job. Peak memory was 2.67 GB against a predicted 1.5 GB (the only miss).
  So **`spark_t1.py` is the Task 1 entry point.**
- **`spark_t1.py` 0.1.1 defaults to depth 150**, the depth `../rerank/RESULTS-spark40.md` chose by
  its pre-registered rule (0.1.0 defaulted to 50). Nothing else in it changed. The scorer stays
  **fp32 with 512-token inputs** (`../quant/RESULTS-spark42.md`). The 0.1.1 tests (one changed
  assertion in `test_spark_t1.py`, one new test in `test_agree.py`) have been traced by hand only.
  They will first run in the next sealed job that uses this code; committing does not run them.
- The whole-pipeline timing at the final settings (`spark43`) is not filed yet. It waits for the
  dense first-stage test (`../dense/`), which may change the candidate set: timing the current
  system now would mostly repeat what spark40 and spark41 already measured (about 150 x 0.35-0.51 s
  of cross-encoder work plus BM25's 17-43 s median per question, on 2 CPUs).
- **The Docker image has not been built or run yet.** Open items: whether the challenge mounts
  the corpus or expects it inside the image (the index is about 92.5 GB); the index uses SQLite's
  WAL journal, so its folder must be writable unless it is converted first; the challenge has not
  published how wrong citations are penalised, so the `top:1` / `top:5` choice may change.

Contact: MV2, Munim, Inc., mv2@munimtech.com
