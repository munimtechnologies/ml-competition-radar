# Pre-registration: t2sys-v1 (Task 2 answers built on the chosen Task 1 system)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
00:45 UTC, before the job runs. The job's workdir carries a copy of this file.

## Question

`RESULTS-t2dev.md` composed Task 2 answers from plain BM25 rankings of the 65 TREC 2024 BioGen
questions. `../rerank/RESULTS-spark36.md` recomposed them after a MedCPT cross-encoder reranked
the top 50 BM25 candidates, and judged precision rose from 0.757 to 0.817. The Task 1 system
MV2 chose since then reranks the top 150 (`../system/`, spark43). Do answers composed from that
system's rankings keep that gain over BM25, and does the unchanged composer run with the index
opened read-only, as the challenge image will need?

## Job

`t2sys-v1`, kind `compete`, image `python:3.12`, 2 CPUs, 3 GB, 240 min, volume `pubmed-baseline`
(the full index lives only on the Blade).

- Setup: the pinned torch 2.5.1+cpu, numpy 2.1.3 and transformers 4.46.3.
- Run: `fetch_code.py` 0.3.0 fetches `t1`, `rerank`, `system2` (`spark_t1.py` 0.2.0, `ro_db.py`
  0.1.0), `t2` (`compose.py` 0.2.0) and `t2dev` into `/tmp/code`; tests; `host_guard.py`; the index's
  side files before; the BioGen 2024 gold (`biogen_census.py`, `t2dev.py gold`); the Task 1 system
  on the 65 questions (`spark_t1.py --depth 150 --immutable`, MedCPT cross-encoder, 2 threads);
  `t1.py score` and `agree.py rank` against spark40's depth-200 BioGen rerank read at depth 150;
  then `compose_ro.py` (new, below) composes and scores answers at depth 20 from the system's
  rankings (**sys**) and from t2dev-v1's BM25 rankings (**control**, `/data/t2dev/ranked_biogen.jsonl`);
  `compare.py` (new) compares the two; sys is also composed at depth 10 and 30 (recorded only);
  the index's side files after; the system's rankings are copied to `/data/t2sys/` so later Task 2
  jobs need not rerun the cross-encoder.
- `compose_ro.py` 0.1.0 runs `compose.py` 0.2.0 unchanged, but swaps the `sqlite3` name inside it
  for an object whose `connect()` is `ro_db.connect(path, immutable=True)`. compose.py's plain open
  would create `-wal`/`-shm` files beside the shared index while it runs.
- `compare.py` 0.1.0: judged precision = (mean Supports share + mean mixed share) / (1 - mean
  unjudged share), as `RESULTS-t2dev.md` computes it; judged citations; answers with no judged
  citation; per-topic higher/lower/level counts.

## Checks (the job stops, rather than grades, if one is false)

- C1. `fetch_code.py` exits 0 (every file has its pinned size).
- C2. Tests: this folder's `test_fetch_code` 5, `test_compose_ro` 5 and `test_compare` 4 all pass
  (14 run, 0 skipped); the fetched `test_compose.py` 12, `test_spark_t1.py` 11 pass;
  `test_ro_db.py` 12 run with 11 passed and 1 skipped (as root, as in rodb1).
- C3. `host_guard.py` passes (1,306 built files, 39,167,523 documents).

## Predictions (graded to the letter in `RESULTS-t2sys.md`)

- **K1. The control reproduces t2dev-v1 exactly** through the read-only path: its `scores.json`
  means equal t2dev-v1's to 4 decimals (Supports 0.1691, mixed 0.0365, contradicts 0.0026, other
  0.0633, unjudged 0.7285, Supports recall 0.0365, Supports-only recall 0.0346),
  `topics_with_mixed_found` 10, `compare.py` shows 16 answers with no judged citation, and its
  `compose.json` shows 0 empty answers, no validation problems and median 247 words.
- **K2. Task 1 reproduces spark43:** `run.json` complete, 65 answered, 0 `no_candidates`, no
  problems; top-5 MRR 0.4274 and top-1 MRR 0.3231 exact to 4 decimals; `agree.json` common 65 and
  same_order 65.
- **S1.** sys mean unjudged share is below the control's 0.7285.
- **S2.** sys judged precision is at least 0.78.
- **S3.** sys mean Supports share is above the control's 0.1691.
- **S4.** sys mean Supports recall is above the control's 0.0365.
- **S5.** Per topic, sys has a higher Supports share than the control in more topics than it has
  a lower one.
- **S6.** sys `compose.json`: 0 empty answers, no validation problems, median words 200-250, the
  conflict flag on at most 3 of 65 answers.
- **R1.** No `-wal` or `-shm` file beside the index before or after (`db_before.json`,
  `db_after.json`).
- **R2.** Median seconds per question 50-150 (spark43 on BioGen: 82.6); peak memory at most 3 GB,
  if recorded.

Recorded, not predicted: the depth-10 and depth-30 sys scores (they choose nothing; a compose-depth
choice would need its own pre-registration), the BM25 and cross-encoder medians, the judged
citation counts, and the per-topic judged-precision counts.

## Rules and what follows

- If K1 fails, the read-only path changed the answers: find out why before anything else, and
  nothing from sys is used.
- If S1-S3 hold, Task 2 answers are built from the Task 1 system's rankings (depth 150), and these
  sys numbers become the baseline any open-weight stage (conflict judge, rewriting) must beat.
- If S2 fails, the deeper pool does not keep spark36's precision gain in Task 2; that is reported
  as found, and the depth used for Task 1 does not change (it was chosen on Task 1 MRR).
- Exit 3 at `host_guard`: the job landed on the Dell; re-file unchanged. Exit 143/255: re-file
  unchanged. Exit 137: v2 at 4 GB.
- Only counts, scores and timings are published: no question text, no PMIDs, no rankings or
  answers.

## Limits

BioGen 2024 judgments were pooled from 2024 runs over a 2023 PubMed snapshot, so an unjudged
citation is unknown, not wrong, and a system that cites papers 2024 runs also cited looks better.
BioGen questions are not SPARK's questions, and SPARK's Task 2 metric is not published yet. The
control and sys share the composer, so this measures retrieval's effect on answers, not answer
quality. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
