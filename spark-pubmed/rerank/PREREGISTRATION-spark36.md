# Pre-registration: MedCPT rerank on the whole PubMed index (job `spark36-rerank-v1`)

Written on 2026-10-24, during the run that began at 05:24 UTC and before the job was filed, by
AI agents working in the name of MV2 of Munim, Inc. The job carries a copy of this file; its
public commit comes after the run, possibly after the job has started, and that will be stated
when grading. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

Stage 2 of MV2's SPARK system reranks BM25's first 50 candidates with NCBI's MedCPT
cross-encoder (fp32; card check and CPU benchmark in `rerank/RESULTS.md`: 436.6 ms per pair at
320 tokens on 2 CPUs). It has never run on real candidates.

Which sets: `t1_runner/PREREGISTRATION-spark35.md` said a rerank follows if P1 held. P1 failed
as written, on its R half (`t1_runner/RESULTS-spark35.md`). **Post-hoc decision, labelled as
such:** this job reranks headline L (43 questions; recall@20 0.3256 against a top-5 hit share
of 0.1395, so room to gain) and the 65 TREC 2024 BioGen questions of `t2/RESULTS-t2dev.md`
(recall@20 0.8462 against 0.4923). R (0.9333 against 0.8778) is left out.

## Fixed design

- Code from GitHub by `fetch_code.py`, size-checked: `t1_runner` @ `ce37c206`, `t2` @
  `8b6a37a8`, `rerank` @ `99ade999` (`rerank_run.py` 0.1.0, `rerank.py`, `fetch_model.py`).
  `t2dev.py` 0.1.0 for the BioGen gold. torch 2.5.1+cpu, transformers 4.46.3, numpy 2.1.3.
- Model: `ncbi/MedCPT-Cross-Encoder` @ `71caf65d`, 8 files checked against pinned hashes, saved
  to `/data/models/medcpt-ce-71caf65` on the data volume for later jobs.
- Inputs: the BM25 rankings already on the volume (`/data/spark35/ranked_l.jsonl`,
  `/data/t2dev/ranked_biogen.jsonl`), so no BM25 query runs again. Rerank depth 50, 2 threads,
  batch 8; candidates 51-100 keep their BM25 order behind the reranked 50.
- Order: tests; `host_guard`; input check; wait up to 120 minutes for `/data/spark37/done.json`
  (written last by `spark37-speed-v1`, which times queries); model fetch; rerank L, score it
  against `/data/spark35/gold.jsonl`; rerank BioGen, build the BioGen gold, score against
  Supports and against relevant; `compose.py` 0.2.0 on the reranked BioGen candidates (first 20,
  250 words), scored as in `t2dev-v1`; copy both reranked files to `/data/spark36/`.
- 2 CPUs, 2.5 GB, data volume `pubmed-baseline`, 240 minutes.
- Read for grading: `guard.json`, `wait.json`, `fetch_model.json`, each leg's `rerank.json` and
  `scores.json`, `census/census.json`, `gold/gold.json`, `bg_compose/compose.json` and
  `scores.json`, stdout/stderr, `summary.json`. Never read or published: any `ranked.jsonl`,
  `answers.jsonl` (question and abstract text).

Baselines (BM25, from the jobs above): L top:5 MRR 0.0860, hit 0.1395. BioGen Supports top:5
MRR 0.3174, hit 0.4923. BioGen compose: Supports share 0.1691, mixed 0.0365, unjudged 0.7285,
judged precision 0.757 ((Supports + mixed) / (1 - unjudged)).

## Already known (checks, not predictions)

- K1. If the host is `dell`, `host_guard` exits 3, nothing is graded ("premise not met"), and the
  job is filed again unchanged as `-v2`.
- K2. On each leg, recall_at 50 and 100 equal the baseline's (L 0.4419, 0.4651; BioGen Supports
  0.8923, 0.9077): a rerank of the first 50 only reorders them.
- K3. `gold.json`: no problems, 65 topics, 2,990 distinct Supports PMIDs.

## Predictions

- R1. Every test passes (`test_fetch_code`, `test_t2dev`, `test_t1`, `test_rerank_run`,
  `test_rerank`).
- R2. `fetch_model.json`: `ok` true, all 8 files downloaded or kept, on the first attempt each.
- R3. L: reranked top:5 MRR is higher than 0.0860.
- R4. BioGen Supports: reranked top:5 MRR is higher than 0.3174, and top:5 hit is higher than
  0.4923.
- R5. `ms_per_pair` is between 250 and 900 on both legs.
- R6. `missing_text` is at most 1% of the pairs on both legs.
- R7. `needs_top1_changed` is at least 30% of the questions on both legs.
- R8. BioGen compose on reranked candidates: judged precision is higher than 0.757 and the
  Supports share is higher than 0.1691.
- R9. BioGen compose on reranked candidates: unjudged share is lower than 0.7285.
- R10. Every step exits 0 and the job ends within 240 minutes.

## How it will be read (written now)

- R3 and R4 hold: the cross-encoder joins the Task 1 system, and the next job tests cut-off
  policies on its scores (fewer than 5 items when the scores say so), since wrong citations are
  penalised.
- R4 holds but R3 fails: L's difficulty is in recall (its targets mostly sit below rank 50),
  so the next work is query rewriting or a dense first stage, not reranking.
- R8 and R9 decide whether reranked candidates replace BM25's in the Task 2 baseline.
- Wall time is reported against the tie-breakers; if the rerank costs more than about 30 s per
  question, a smaller depth is tested before any larger question set.

Limits: L has 43 questions (one question moves MRR by up to 0.023). BioGen judgments were pooled
from 2024 runs, so an unjudged paper is unknown, not wrong. If the wait ends without the speed
job's file, the two jobs may overlap, and timings are then marked as confounded. No human has
checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
