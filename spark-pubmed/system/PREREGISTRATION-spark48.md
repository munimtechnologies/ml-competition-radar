# Pre-registration: spark48-image-v1 (does the system run as the planned image lays it out, with no network?)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-29, about
20:30 UTC, before the job runs. The job's workdir carries a copy of this file.

## Question

`RESULTS-spark47.md` showed that the Task 1 system runs end to end with `--immutable` as a user
with no write access to the index, with unchanged rankings. The `Dockerfile` is still not built.
It differs from every job so far in four ways: the base image is `python:3.12-slim` (a different
SQLite build could lack FTS5 or rank differently), the six code files sit flat in `/app` with no
`t1_runner/` or `rerank/` folders, the model loads from `/app/model`, and the container has no
network. Does the system still run, and give exactly spark43's BioGen rankings, under all four?

## Job

`spark48-image-v1`, kind `poc` (setup steps have network for pip and for `fetch_code.py`; run
steps have none), image `python:3.12-slim`, 2 CPUs, 3 GB, 240 min, volume `pubmed-baseline`.

- Setup: the pinned torch 2.5.1+cpu, numpy 2.1.3 and transformers 4.46.3, then
  `fetch_code.py` 0.3.0 fetches `t1`, `rerank`, `system2` (new: `system` at 9a64c8e3, the
  published `spark_t1.py` 0.2.0), `t2` and `t2dev` into `/opt/code`.
- Run: this folder's tests (`test_fetch_code` 5, `test_image_eq` 6); `image_eq.py net`; the
  fetched `test_spark_t1.py`, `test_ro_db.py` and `test_nobody_run.py`; `host_guard.py`;
  `image_eq.py app`, which copies exactly the Dockerfile's six files (`t1.py`, `build_index.py`,
  `rerank.py`, `rerank_run.py`, `spark_t1.py`, `ro_db.py`) into a new `/app` and the MedCPT
  cross-encoder into `/app/model`; the BioGen 2024 gold (`biogen_census.py`, `t2dev.py gold`);
  then, as uid 65534 through `nobody_run.py`, the Dockerfile's entry point
  `python /app/spark_t1.py --db ... --model-dir /app/model --immutable` on the 65 BioGen questions
  with only `--questions`, `--out-dir` and `--team-id` added; then `t1.py score` and `agree.py rank`
  against spark40's depth-200 BioGen rerank read at depth 150 (spark43 matched 65 of 65).

## Checks (the job stops, rather than grades, if one is false)

- C1. `fetch_code.py` exits 0: every fetched file has its pinned size.
- C2. Tests: `test_fetch_code` 5 and `test_image_eq` 6 pass; `test_spark_t1` 11 pass;
  `test_ro_db` 12 run with 11 passed and 1 skipped (`test_read_only_folder`, as root, as in
  rodb1); `test_nobody_run` 4 pass.
- C3. `host_guard.py` passes (1,306 built files, 39,167,523 documents).

## Predictions (graded to the letter in `RESULTS-spark48.md`)

- **I1.** `net.json`: `dns` false and `connect` false (no network in the run steps).
- **I2.** `app.json`: `problem` null; `listing` is exactly the six files plus `model`; `blob_mismatch`
  is empty (each file's git blob equals the one the repository lists at the pinned commit);
  `runtime` shows Python 3.12.x, torch 2.5.1+cpu, transformers 4.46.3.
- **I3.** The entry point exits 0 as uid 65534: `run.json` shows version `0.2.0`, `immutable` true,
  `complete` true, 65 answered, 0 `no_candidates`, no problems.
- **I4.** BioGen top-5 MRR 0.4274 and top-1 MRR 0.3231, exact to 4 decimals (spark43).
- **I5.** `agree.json`: `common` 65, `same_order` 65.
- **I6.** No `-wal` or `-shm` file beside the index before or after the run.
- **I7.** Median seconds per question between 50 and 150 (spark43 on BioGen: 82.6).
- **I8.** Peak memory at most 3 GB, if recorded (spark47: 2.14 GB).

Recorded, not predicted: the SQLite version in the slim image next to the one rodb1 reported,
the BM25 and cross-encoder medians next to spark43's (21.9 s and 57.7 s), and the bytes and
sha256 of each model file.

## Rules and what follows

- Exit 3 at `host_guard` with `db_exists` false: if `summary.json` names the Dell, re-file
  unchanged; if it names the Blade, the `poc` kind did not get the data volume, so v2 runs as kind
  `compete` (network on) and I1 is graded as not tested.
- An image the runner refuses: v2 on `python:3.12`, and the slim-image part is not claimed.
- Exit 143/255: re-file unchanged. Exit 137: v2 at 4 GB.
- If I1-I6 hold, the `Dockerfile` layout is confirmed short of `docker build` itself. The next
  steps are building the real image and the Task 2 rerun on the chosen Task 1 system. If I4 or
  I5 fails, the difference is explained (most likely the slim image's SQLite) before anything
  else.
- Only counts, timings and file hashes are published: no question text, no PMIDs, no rankings.

## Limits

This is a stand-in for the image, not the image. The container is the runner's, not
`docker run --network none` from the Dockerfile, and the index is protected by file ownership
(uid 65534), not a `:ro` mount. The BioGen questions are TREC 2024 BioGen topics, not SPARK's
evaluation questions, and unjudged papers count as wrong. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
