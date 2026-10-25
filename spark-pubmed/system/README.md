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
    --scorer medcpt --model-dir medcpt-ce --depth 150 --team-id TEAM
python spark_t1.py ... --scorer none      # BM25 only, no torch needed
```

`agree.py` checks that the system reproduces an earlier ranking and that a resumed run writes
byte-identical submission files. `Dockerfile` is the planned image.

| File | What it is |
|---|---|
| `PREREGISTRATION-spark41.md` | Predictions for job `spark41-system-v1`, written before it ran |
| `RESULTS-spark41.md` | Grades: 3 of 3 checks and 7 of 8 predictions held |
| `results-spark41/` | That job's run, score, agreement and resume-check counts (no question text) |

## Status (2026-10-25)

- `RESULTS-spark41.md`: on the 90 R questions at depth 50, the whole system reproduced spark39's
  graded ranking exactly (same top five on 90 of 90; top:5 MRR 0.8981, top:1 0.8333). A second run
  on the same folder resumed all 90 answers in 6 s and wrote byte-identical submission files.
  Median time per question was 75.0 s on 2 CPUs (BM25 43.4 s, cross-encoder 31.3 s), on a host
  shared with another job. Peak memory was 2.67 GB against a predicted 1.5 GB (the only miss).
  So **`spark_t1.py` is the Task 1 entry point.**
- Depth: **150**, set by `../rerank/RESULTS-spark40.md`. The code's default is still 50 until the
  whole-pipeline timing job at depth 150 (`spark43`, after the cheaper-scorer test
  `../quant/PREREGISTRATION-spark42.md` is graded) confirms it.
- **The Docker image has not been built or run yet.** Open items: whether the challenge mounts
  the corpus or expects it inside the image (the index is about 92.5 GB); the index uses SQLite's
  WAL journal, so its folder must be writable unless it is converted first; the challenge has not
  published how wrong citations are penalised, so the `top:1` / `top:5` choice may change.

Contact: MV2, Munim, Inc., mv2@munimtech.com
