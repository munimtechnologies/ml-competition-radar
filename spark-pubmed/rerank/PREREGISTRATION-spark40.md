# Pre-registration: how deep should the cross-encoder rerank? (job `spark40-depth-v1`)

Written on 2026-10-24, during the run that began at 22:07 UTC and before the job was filed, by AI
agents working in the name of MV2 of Munim, Inc. The job carries a copy of this file; its public
commit comes after the run, possibly after the job has started, and that will be stated when
grading. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

Two jobs were graded this run:

- `../prf/RESULTS-spark38.md`: pseudo-relevance feedback raised headline L's recall@100 from 20
  to 24 of 43 but lowered top:5 MRR on BioGen (0.3174 to 0.2700) and R (0.7931 to 0.6996), so it
  is not adopted. Its leg D ran plain BM25 on L to depth 1,000: a target paper is within the
  first 50 candidates for 19 questions, the first 200 for 26, the first 300 for 32 and the first
  1,000 for 36.
- `RESULTS-spark39.md`: the MedCPT cross-encoder on BM25's first 50 raised R's top:5 MRR from
  0.7931 to 0.8981, so it is Task 1's stage 2 on every question type.

So L's bottleneck is how many candidates the reranker sees. spark38's written reading only sent
the work to a deeper rerank if PRF had failed its key prediction (it did not); choosing depth
over PRF here is a post-hoc decision, made because plain BM25 at depth 200 already reaches more
L targets (26) than PRF's fused first 100 (24), with no PRF query cost.

This job reranks deeper on all three dev sets once, and `depth_curve.py` reads off what every
smaller depth would have scored: the cross-encoder scores each pair on its own and breaks ties by
BM25 order, so a depth-d rerank equals the deep rerank restricted to BM25 ranks 1 to d (up to
float noise from padded batches).

## Fixed design

- Code: `t1.py`, `host_guard.py`, `build_index.py`, `test_t1.py` (`t1_runner` @ `ce37c206`);
  `biogen_census.py` (`t2` @ `8b6a37a8`); `rerank_run.py`, `rerank.py`, `fetch_model.py` and
  tests (`rerank` @ `99ade999`), fetched by `fetch_code.py` with sizes checked. In the job folder:
  `depth_curve.py` 0.1.0 (new; 5 fake-data tests in `test_depth_curve.py`), `t2dev.py` 0.1.0.
  torch 2.5.1+cpu, transformers 4.46.3, numpy 2.1.3. Model `ncbi/MedCPT-Cross-Encoder` @
  `71caf65d` from the data volume; `fetch_model.py` re-checks every hash.
- Legs, in this order (L first, as it matters most):
  - L (43): rerank the first **300** of spark38's depth-1,000 BM25 list
    (`/data/spark38/bm25_l_d1000.jsonl`); gold `/data/spark35/gold.jsonl`.
  - BioGen (65): `t1.py run --depth 200` on the BioGen questions, rerank the first **200**; gold:
    Supports from `t2dev.py gold`.
  - R (90): `t1.py run --depth 200` on the R questions, rerank the first **200**; gold
    `/data/spark35/gold.jsonl`.
  - For each: `t1.py score` and `depth_curve.py` at depths 20, 50, 100, 150, 200, 300.
- 2 threads, batch 8, 2 CPUs, 4.5 GB (so it waits for the machine with the whole index), data
  volume `pubmed-baseline`, 660 minutes. About 43,900 pairs; at spark36/39's 376-527 ms per pair
  that is 4.6-6.4 hours plus about 70 minutes of BM25 queries.
- The last step copies the three reranked lists to `/data/spark40/` and writes
  `/data/spark40/done.json`.
- Read for grading: `guard.json`, `fetch_model.json`, `gold/gold.json`, `{l,bg,r}/rerank.json`,
  `{l,bg,r}/scores.json`, `{l,bg,r}/curve.json`, `bm_{bg,r}/run.json`, stdout/stderr,
  `summary.json`. Never read or published: any `ranked.jsonl` or `submission.jsonl` (question
  text).

Baselines at depth 50 (cross-encoder, top:5): L MRR 0.1500, hit@5 13, hit@1 3; BioGen Supports
0.4321, 44, 19; R 0.8981, 87, 75. BM25 reach (gold within the first d): L 19 / 20 / 26 / 32 at
50 / 100 / 200 / 300; BioGen 58 / 59 at 50 / 100; R 88 / 89 at 50 / 100.

## Already known (checks, not predictions)

- K1. If the host lacks the whole index, `host_guard` exits 3, nothing is graded, and the job is
  filed again unchanged as `-v2`.
- K2. The input check finds the gold file, the three question/candidate files and the weights.
- K3. `gold.json`: no problems, 65 topics, 2,990 distinct Supports PMIDs.
- K4. `curve.json` reach equals the BM25 reach above at the same depths (same index, same query
  code). If BioGen's or R's regenerated list differs, D1 is still graded, and the difference is
  reported.

## Predictions

- D1. Each leg's depth-50 point reproduces its depth-50 run: top:5 MRR within 0.01 of L 0.1500,
  BioGen 0.4321, R 0.8981.
- D2 (key). L: top:5 MRR at depth 300 is above 0.1500.
- D3. L: hit@5 at depth 300 is at least 15 of 43.
- D4. L: the share of reachable targets that reach the top five falls with depth: hit@5 / reach
  at depth 300 is below 13 / 19 (0.684).
- D5. R: top:5 MRR at depth 200 is at least 0.8681 (within 0.03 of depth 50).
- D6. BioGen: top:5 MRR at depth 200 is at least 0.4021 (within 0.03 of depth 50).
- D7. L: at most 3 questions lose a top-5 hit at depth 300 against depth 50.
- D8. Every leg: `ms_per_pair` between 250 and 900, and `missing_text` at most 1% of pairs.
- D9. Every test passes, every step exits 0, and the job ends within 660 minutes.
- D10. Peak memory is at most 2.0 GB.

## How it will be read (written now)

- A depth is eligible if, at that depth, BioGen and R each stay within 0.03 top:5 MRR of their
  depth-50 point. **Stage 2's depth is the eligible depth in {50, 100, 150, 200} with the highest
  unweighted mean top:5 MRR over L, BioGen and R** (ties go to the smaller depth). That depth goes
  into the Task 1 system (`spark-pubmed/system/`) and the next job times the whole pipeline.
- If L at 300 beats L at 200 by at least 0.02, a later job measures BioGen and R at 300 before any
  depth above 200 is used.
- D2 fails: more candidates do not help L even though the reach rises; L's remaining misses need
  a different first stage (for example MedCPT's dense article encoder), in its own
  pre-registration.
- Cut-offs stay as `RESULTS-spark39.md` set them: submission 1 `top:5`; `top:1` recorded for a
  second submission.

Limits: R and L are proxy questions written by AI agents; L has 43 questions, so one question
moves MRR by up to 0.023 and hit@5 by 1. On BioGen, gold is "judged Supports", and unjudged papers
count as misses, which penalises deeper candidates that the 2024 pools never judged. Timings
depend on what else runs on the host. Reranking depth is a standard knob (prior art: every
retrieve-then-rerank system tunes it); what is new is only measuring it on this corpus and these
dev sets. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
