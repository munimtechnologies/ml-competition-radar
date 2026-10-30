# Results: spark48-image-v1 (the system run as the planned image lays it out, with no network)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Graded 2026-10-30, about
03:40 UTC, against `PREREGISTRATION-spark48.md` (published before the job ran, commit c96bed0d).
Counts-only outputs are in `results-spark48/`.

## Verdict

**All 8 predictions held.** On `python:3.12-slim`, with the six code files laid out flat in `/app`
exactly as the `Dockerfile`'s `COPY` lines put them, the MedCPT cross-encoder loaded from
`/app/model`, no network in the container, and the index opened `--immutable` by a user (uid 65534)
with no write access to it, the Dockerfile's own entry point reproduced spark43's BioGen rankings
to the item on all 65 questions. One check (C2) was miscounted in the pre-registration; it is
explained below and changes nothing.

The job ran on the Blade from 23:51 UTC on 2026-10-29 to 01:19 UTC on 2026-10-30 (87.4 minutes,
kind `poc`, 2 CPUs, 3 GB). All 16 steps exited 0.

## Checks

| | Pre-registered | Found | |
|---|---|---|---|
| C1 | `fetch_code.py` exits 0 | exit 0 (setup step 4) | held |
| C2 | `test_fetch_code` 5 + `test_image_eq` 6; `test_spark_t1` 11; `test_ro_db` 12 run, 11 passed, 1 skipped; `test_nobody_run` 4 | 11 passed; 11 passed; **9 run, 8 passed, 1 skipped** (`test_read_only_folder`, as root); 4 passed | count miscounted, tests all pass |
| C3 | `host_guard.py` passes | 1,306 files, 39,167,523 records, 92,506,365,952 bytes | held |

C2: `test_ro_db.py` has 9 tests, not 12. The 12 was copied from rodb1, whose test step also ran
`test_probe`'s 3 tests. Every test that exists ran and passed, with exactly the predicted skip.
The same miscount sits in `t2/PREREGISTRATION-t2sys.md`; `t2/ADDENDUM-t2sys-v2.md` corrects it
before that job's re-run.

## Predictions

| | Pre-registered | Found | |
|---|---|---|---|
| I1 | `net.json`: `dns` false, `connect` false | `dns` false ("Temporary failure in name resolution"), `connect` false ("Network is unreachable") | held |
| I2 | `app.json`: `problem` null; listing = six files + `model`; `blob_mismatch` empty; Python 3.12.x, torch 2.5.1+cpu, transformers 4.46.3 | as predicted; Python 3.12.15 | held |
| I3 | exit 0 as uid 65534; `run.json` 0.2.0, `immutable` true, `complete` true, 65 answered, 0 `no_candidates`, no problems | exactly that; both submissions validate (65 lines, 0 empty, no problems) | held |
| I4 | top-5 MRR 0.4274, top-1 MRR 0.3231 | 0.4274, 0.3231 | held |
| I5 | `agree.json` common 65, same_order 65 | common 65, same_order 65, same_set 65, same_first 65, no differences | held |
| I6 | no `-wal`/`-shm` beside the index before or after | none before, none after; only `spark_full.db` in the folder | held |
| I7 | median seconds per question 50-150 | 71.3 s (p95 119.4 s, max 184.1 s) | held |
| I8 | peak memory at most 3 GB, if recorded | 2.15 GB | held |

## Recorded, not predicted

- SQLite in `python:3.12-slim`: 3.46.1, the same version rodb1 reported on `python:3.12`. So the
  slim image's SQLite build cannot explain any ranking difference; there was none.
- Medians per question: BM25 18.1 s (spark43 on BioGen: 21.9 s), cross-encoder 54.2 s (57.7 s),
  total 71.3 s (82.6 s). Total for 65 questions: 5,040.6 s, 29% BM25 and 71% cross-encoder. The
  difference from spark43 is most likely load on the shared machine, not the image.
- Code in `/app` (sha256 of each file, also checked as the git blob the repository lists):
  `t1.py` 12,240 bytes `eff77a88...`, `build_index.py` 11,071 `595909e1...`, `rerank.py` 2,961
  `2b5ccfa9...`, `rerank_run.py` 5,188 `25867eaf...`, `spark_t1.py` 11,414 `33de4884...`,
  `ro_db.py` 3,335 `2ca63c2a...` (full hashes in `results-spark48/app.json`).
- Model in `/app/model`: eight files; `pytorch_model.bin` 437,998,062 bytes, sha256
  `61d5ccd48869e03500544525fc231641d7daa9ba267b202c82724750038dc1e0`, the hash
  `../rerank/fetch_model.py` pins for MedCPT-Cross-Encoder at 71caf65d.
- Recall of a Supports-judged paper in the top k: 0.3231 at 1, 0.6000 at 5, 0.7692 at 10.

## What follows

Per the pre-registration's rule, the `Dockerfile` layout is confirmed short of `docker build`
itself. The two next steps are building and running the real image (`PREREGISTRATION-spark49.md`,
filed with this result) and the Task 2 rerun on this system (`t2sys-v2`).

## Limits

This was a stand-in for the image, not the image: the container was the job runner's, not
`docker run --network none` from the Dockerfile, and the index was protected by file ownership
(uid 65534), not a `:ro` mount. The BioGen questions are TREC 2024 BioGen topics, not SPARK's
evaluation questions, and unjudged papers count as wrong. Only counts, timings and hashes are
published here: no question text, PMIDs or rankings. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
