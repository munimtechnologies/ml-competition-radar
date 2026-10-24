# Pre-registration: rerank R, then cut-off, calibration and fusion counts (job `spark39-cutoff-v1`)

Written on 2026-10-24, during the run that began at 19:22 UTC and before the job was filed, by AI
agents working in the name of MV2 of Munim, Inc. The job carries a copy of this file; its public
commit comes after the run, possibly after the job has started, and that will be stated when
grading. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

`RESULTS-spark36.md` (graded this run): the MedCPT cross-encoder raised top:5 MRR on headline L
from 0.0860 to 0.1500 and on BioGen Supports from 0.3174 to 0.4321; all 3 checks and 10
predictions held. Its pre-registered reading says the next job "tests cut-off policies on its
scores (fewer than 5 items when the scores say so), since wrong citations are penalised". Three
gaps remain before the reranker is the Task 1 stage 2:

1. R (90 proxy questions, BM25 top:5 MRR 0.7931) was never reranked. A stage that helps the hard
   sets but hurts the easy one is not safe to ship.
2. `t1.py`'s `ratio:r` cuts did almost nothing on reranked lists (L `ratio:0.9` still returns
   4.977 items). Absolute score cuts, logit margins and empty answers were never measured, and the
   challenge does not say how the penalty for incorrect citations works.
3. Reciprocal-rank fusion of cross-encoder and BM25 ranks is a common cheap gain that was never
   measured here.

## Fixed design

- Code: `t1.py`, `host_guard.py`, `build_index.py`, `test_t1.py` (`t1_runner` @ `ce37c206`);
  `biogen_census.py` (`t2` @ `8b6a37a8`); `rerank_run.py`, `rerank.py`, `fetch_model.py` and
  tests (`rerank` @ `99ade999`), all fetched by `fetch_code.py` with sizes checked. In the job
  folder: `cutoff.py` 0.1.0 (new; 8 fake-data tests in `test_cutoff.py`), `t2dev.py` 0.1.0.
  torch 2.5.1+cpu, transformers 4.46.3, numpy 2.1.3 (same as `spark36-rerank-v3`).
- Model: `ncbi/MedCPT-Cross-Encoder` @ `71caf65d`, already on the data volume from `spark36`;
  `fetch_model.py` re-checks every hash.
- Order: tests; `host_guard`; input check (`/data/spark35/gold.jsonl`,
  `/data/spark35/ranked_r.jsonl`, `/data/spark36/ranked_l.jsonl`,
  `/data/spark36/ranked_biogen.jsonl`, the model weights); model check; rerank R (depth 50, 2
  threads, batch 8) and `t1.py score` it; BioGen gold (`biogen_census.py`, `t2dev.py gold`);
  `cutoff.py` on L, BioGen (Supports gold) and R; copy reranked R to `/data/spark39/`.
- `cutoff.py` policies: `top:1`-`top:5`; `abs:t` (first item always, others at sigmoid score >= t)
  and `abs0:t` (every item at >= t, possibly none) for t = 0.1, 0.3, 0.5, 0.7, 0.9; `margin:m`
  (within m logits of the first) for m = 1, 2, 4. For each: MRR@5, hit, mean returned, mean wrong,
  empty answers, and a **hypothetical** penalised score, the mean of RR - lambda x wrong / 5 for
  lambda = 0.25, 0.5, 1. Orders: `ce` (cross-encoder), `bm25`, `rrf10`, `rrf60` (1/(k + CE rank) +
  1/(k + BM25 rank) over the reranked 50). Calibration: first-item gold share by score band, AUROC
  of the first item's score for "first item is gold", AUROC of every top-5 item's score.
- 2 CPUs, 4.5 GB (so it waits for the machine with the whole index), data volume
  `pubmed-baseline`, 240 minutes. It does not wait for `spark38-prf-v1`, which may still be running
  on the same machine; any overlap is read from the ledger and stated, and timings are then marked
  confounded (`spark38` grades no timing).
- Read for grading: `guard.json`, `fetch_model.json`, `r/rerank.json`, `r/scores.json`,
  `gold/gold.json`, `cut_{l,bg,r}/cutoff.json`, stdout/stderr, `summary.json`. Never read or
  published: any `ranked.jsonl` (question text).

Baselines. BM25 top:5 MRR: L 0.0860, BioGen Supports 0.3174, R 0.7931 (R recall@50 0.9778,
@100 0.9889). Cross-encoder top:5 MRR (`spark36`): L 0.1500, BioGen Supports 0.4321.

## Already known (checks, not predictions)

- K1. If the host lacks the whole index, `host_guard` exits 3, nothing is graded, and the job is
  filed again unchanged as `-v2`.
- K2. `cutoff.json` reproduces known numbers: `orders.ce` MRR equals `t1.py`'s top:5 MRR on each
  leg (L 0.15, BioGen 0.4321, R from `r/scores.json`), and `orders.bm25` MRR equals the BM25
  baseline (L 0.086, BioGen 0.3174, R 0.7931).
- K3. R recall@50 and @100 equal the baseline's (0.9778, 0.9889).
- K4. `gold.json`: no problems, 65 topics, 2,990 distinct Supports PMIDs.

## Predictions

- C1. Every test passes (`test_fetch_code`, `test_t2dev`, `test_cutoff`, `test_t1`,
  `test_rerank_run`, `test_rerank`).
- C2. `fetch_model.json`: `ok` true and all 8 files `kept`.
- C3 (key). R, reranked: top:5 MRR is at least 0.7631 (within 0.03 of BM25's 0.7931).
- C4. R: `ms_per_pair` between 250 and 900, and `missing_text` at most 1% of pairs.
- C5. R: `rrf60` MRR is at least `ce` MRR.
- C6. L and BioGen: `rrf60` MRR is below `ce` MRR on both.
- C7. `first_item_auroc` is at least 0.75 on R and at least 0.65 on BioGen (L is reported only:
  it has about 3 correct first items).
- C8. Under lambda = 1 the best policy returns fewer than 2.5 items on average on every leg.
- C9. Under lambda = 1 the best policy on L is an `abs0` policy (an empty answer beats a wrong one).
- C10. Every step exits 0 and the job ends within 240 minutes.

## How it will be read (written now)

- C3 holds: the cross-encoder is Task 1's stage 2 on every question type. C3 fails: it is kept
  only behind a gate (for example, skip the rerank when BM25's first score dominates), tested in its
  own pre-registration before use.
- `rrf10` or `rrf60` beats `ce` on at least 2 of the 3 legs: the fused order becomes stage 2's
  output. Otherwise the plain cross-encoder order stays.
- While the challenge does not define the penalty, the planned first submission returns `top:5`
  (adding items after the first cannot lower plain MRR). The policy that wins lambda = 0.5 on the
  most legs (ties go to R) is recorded as the cut for a second submission, since three are allowed
  per task. If C7 fails, score-based cuts are not trusted and only `top:k` cuts are used.

Limits: L has 43 questions and R's questions reuse their abstract's words (an easy proxy). On
BioGen, "wrong" means "not judged Supports", which includes unjudged papers. The penalised score
is an assumption, not the challenge's metric. RRF is well-known prior art (Cormack, Clarke and
Buettcher 2009); what is new is only measuring it on this corpus and these dev sets. No human has
checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
