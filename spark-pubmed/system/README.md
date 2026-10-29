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
- **Read-only index (0.2.0).** `--immutable` opens the index through `ro_db.py` with
  `mode=ro&immutable=1`, so it can sit on a read-only mount. Without the flag it is opened as
  before. Rankings do not depend on the flag.
- **Input.** JSONL with `info_need_id` and `info_need` at the top level or under `metadata` (the
  submission format), or one JSON list. The id is echoed as given.

```
python spark_t1.py --db spark_full.db --questions questions.jsonl --out-dir out \
    --scorer medcpt --model-dir medcpt-ce --team-id TEAM --immutable   # depth 150 by default
python spark_t1.py ... --scorer none      # BM25 only, no torch needed
```

`agree.py` checks that the system reproduces an earlier ranking and that a resumed run writes
byte-identical submission files. Since 0.1.1, `agree.py rank --b-depth D` reads a deeper rerank the
way `../rerank/depth_curve.py` does (only reranked items whose BM25 rank is at most D), so the
system at depth 150 can be compared with spark40's depth-200 and depth-300 reranks. `Dockerfile`
is the planned image.

`fetch_code.py` (0.2.0, standard library only) lets a sealed job fetch this repository's published
code at pinned commits and checks each file's size against the git tree, so the job runs exactly
the public code. Its `system` and `t2dev` groups pin commit 4765a24.

`ro_db.py` (0.1.0, standard library only) opens the index read-only for a read-only mount. The
index uses SQLite's WAL journal, and SQLite 3.22.0 or later can read a WAL-mode database without
write access only if its `-shm` and `-wal` files already exist, its folder is writable, or the
connection uses the `immutable` URI parameter
([sqlite.org/wal.html](https://www.sqlite.org/wal.html), section 5). `connect(path,
immutable=True)` opens it with `mode=ro&immutable=1`, so no locks or side files are needed and
nothing can be written. An immutable connection ignores a `-wal` file, so a non-empty one is
refused rather than silently skipped. `python ro_db.py DB` prints the journal mode, the side-file
sizes and the SQLite version.

`nobody_run.py` (0.1.0, standard library only) runs one command as uid/gid 65534, which cannot
write the index's folder, and records the index's side files before and after; spark47 uses it
to stand in for a read-only mount.

| File | What it is |
|---|---|
| `PREREGISTRATION-spark41.md` | Predictions for job `spark41-system-v1`, written before it ran |
| `RESULTS-spark41.md` | Grades: 3 of 3 checks and 7 of 8 predictions held |
| `results-spark41/` | That job's run, score, agreement and resume-check counts (no question text) |
| `PREREGISTRATION-spark43.md` | Predictions for job `spark43-system-v1` (whole system at depth 150 on all 198 development questions), written before it ran |
| `RESULTS-spark43.md` | Grades: 3 of 3 checks and 5 of 5 predictions held |
| `results-spark43/` | Each set's scores, agreement and timing (counts only) |
| `fetch_code.py`, `test_fetch_code.py` | Fetches the pinned public code into a job |
| `ro_db.py`, `test_ro_db.py` | Opens the WAL-mode index read-only (`immutable`) for a read-only mount |
| `PREREGISTRATION-rodb1.md` | Predictions for job `rodb-check-v1` (does `ro_db.py` open the real index read-only?), written before it ran |
| `RESULTS-rodb1.md` | Grades: 7 of 7 predictions held |
| `results-rodb1/rodb.json` | That probe's output (schema object names and counts only) |
| `nobody_run.py`, `test_nobody_run.py` | Runs a command as a user with no write access to the index |
| `PREREGISTRATION-spark47.md` | Predictions for job `spark47-immutable-v1` (the whole system with `--immutable`, no write access), written before it ran |

## Status (2026-10-29, about 09:00 UTC)

- **`RESULTS-spark43.md`: the system at depth 150 reproduced its chosen rankings exactly.**
  Top-5 MRR was L 0.1628, BioGen 0.4274 and R 0.9130, the same as spark40's depth-150 reading,
  and the top five were in the same order on 43 of 43, 65 of 65 and 90 of 90 questions. The 198
  questions took 380.7 minutes on 2 CPUs on a shared host: a median of 109.3 s (L), 82.6 s
  (BioGen) and 135.2 s (R) per question, 39% of it BM25 and 61% the cross-encoder. Peak memory
  was 2.65 GB. **`spark_t1.py` at depth 150 is the Task 1 system.** The scorer stays fp32 with
  512-token inputs (`../quant/RESULTS-spark42.md`).
- **`RESULTS-rodb1.md`: the real index opens read-only.** It is in WAL mode with no `-wal` or
  `-shm` file. `ro_db.connect(immutable=True)` opened it as root and as uid 65534 (11 schema
  objects), while a plain open as uid 65534 failed with `attempt to write a readonly database`.
  So no conversion of the shared index is needed.
- **`spark_t1.py` 0.2.0 adds `--immutable`** (three new tests in `test_spark_t1.py`: the same
  submission files as a plain open, a non-empty `-wal` refused, and the flag through `main`). The
  `Dockerfile` now mounts the index read-only and passes `--immutable`. The 0.2.0 tests have been
  traced by hand only; **job `spark47-immutable-v1` is filed** and runs them, then runs the whole
  system on the 43 L questions as uid 65534 (`PREREGISTRATION-spark47.md`).
- **The Docker image has not been built or run yet.** Open items: whether the challenge mounts
  the corpus or expects it inside the image (the index is about 92.5 GB); the challenge has not
  published how wrong citations are penalised, so the `top:1` / `top:5` choice may change.

Contact: MV2, Munim, Inc., mv2@munimtech.com
