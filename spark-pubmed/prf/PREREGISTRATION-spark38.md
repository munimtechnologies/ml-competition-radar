# Pre-registration: pseudo-relevance feedback on the whole SPARK index (job `spark38-prf-v1`)

Written on 2026-10-24, during the run that began at 16:09 UTC and before the job was filed, by AI
agents working in the name of MV2 of Munim, Inc. The job carries a copy of this file; its public
commit comes after the run, possibly after the job has started, and that will be stated when
grading. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

On headline L (43 questions), whole-corpus BM25 put the target paper in its first 100 candidates
for only 20 questions (`../t1_runner/RESULTS-spark35.md`). A reranker cannot bring back a paper the
first stage never returned. `prf.py` 0.1.0 (RM3-style feedback words from the first 10 BM25
candidates, then reciprocal-rank fusion with the baseline; see `README.md`) is the planned recall
stage. The speed job graded today (`../speed/RESULTS-spark37.md`) failed V3, so the question's own
words are not pruned here (`--question-max-df 0`), as the playbook rule for this job said.

A second, cheaper question rides along (leg D): how deep must plain BM25 go on L to reach the
targets? If many sit between ranks 101 and 1,000, a deeper rerank is an alternative to PRF.

## Fixed design

- Code: `prf.py` 0.1.0 and `test_prf.py` from `prf` @ `3ea7684e`; `t1.py`, `build_index.py`,
  `host_guard.py`, `test_t1.py` from `t1_runner` @ `ce37c206`; `biogen_census.py` from `t2` @
  `8b6a37a8`; all fetched by `fetch_code.py` (sizes checked). `t2dev.py` 0.1.0 (wait, BioGen gold)
  and `deep_recall.py` 0.1.0 (4 fake-data tests) are in the job folder.
- Inputs (on the data volume, from earlier jobs): `/data/spark35/ranked_l.jsonl`,
  `/data/spark35/ranked_r.jsonl`, `/data/spark35/gold.jsonl`, `/data/t2dev/ranked_biogen.jsonl`.
- Before any timed query the job waits up to 120 minutes for `/data/spark36/ranked_biogen.jsonl`
  (the last file `spark36-rerank-v3` writes), so the two jobs do not time work on the index at once.
- PRF settings, all the defaults: `--depth 100 --fb-docs 10 --fb-terms 10 --max-df 400000
  --question-max-df 0 --min-terms 2 --rrf-k 60`.
- Legs, in this order: L (PRF; score fused `ranked.jsonl` and expanded-only `ranked_exp.jsonl`
  against `/data/spark35/gold.jsonl`); BioGen (PRF; both lists against the Supports gold from
  `t2dev.py gold`); D (plain BM25 on L at depth 1,000 with `t1.py run`; `t1.py score` and
  `deep_recall.py`); R (PRF; both lists). R runs last so a time-out costs the least important leg.
- 1 CPU, 4.5 GB, data volume `pubmed-baseline`, 420 minutes. The last step copies the fused lists
  and leg D's list to `/data/spark38/` and writes `/data/spark38/done.json`.
- Read for grading: `guard.json`, `wait.json`, `gold/gold.json`, `{l,bg,r}/run.json`,
  `{l,bg,r}/{fused,exp}/scores.json`, `deep_l/run.json`, `deep_l/scores.json`,
  `deep_l/deep.json`, stdout/stderr, `summary.json`. Never read or published: any `ranked*.jsonl`
  or `submission.jsonl` (question text).

Baselines (top:5 MRR; recall@100; median ms): L 0.0860, 0.4651 (20/43), 27,227; BioGen Supports
0.3174, 0.9077 (59/65), 15,833; R 0.7931, 0.9889 (89/90), 35,413. L recall@5 0.1395 (6/43),
@50 0.4419 (19/43).

## Already known (checks, not predictions)

- K1. If `host_guard` fails (the machine without the whole index), it exits 3 and nothing below is
  graded; the job is filed again unchanged as `-v2`.
- K2. The input check finds all four files.
- K3. `gold.json`: `problems` empty, 65 topics, 2,990 distinct Supports PMIDs.
- K4 (reported, not graded): `wait.json` `found`. If false, every timing below is confounded by
  the reranker job; scores are not.

## Predictions

- P1. Every test passes: `test_fetch_code` 3, `test_t2dev` 6, `test_deep_recall` 4, `test_t1` 6,
  `test_prf` 6.
- P2 (key). L, fused: recall@100 is at least 0.4884 (21 of 43), above the baseline's 20.
- P3. L, fused: top:5 MRR is at least the baseline's 0.0860.
- P4. BioGen Supports, fused: top:5 MRR is at least the baseline's 0.3174.
- P5. R, fused: top:5 MRR is at least 0.7631 (within 0.03 of the baseline).
- P6. R: the expanded list alone scores a lower top:5 MRR than the fused list (topic drift on
  questions written about one paper).
- P7. In each of L, BioGen and R: `no_expansion` is 0, `mean_expansion_terms` is at least 8, and
  `no_candidates_fused` is 0.
- P8. Leg D reproduces the baseline's first 100: `hits_at` 5 is 6 and `hits_at` 100 is 20.
- P9. Leg D: `hits_at` 1,000 is between 23 and 30 of 43 (inclusive).
- P10. Every step exits 0 and the job ends within 420 minutes.
- P11. Peak memory is at most 3.0 GB (`spark37-speed-v3` peaked at 2.37 GB under the same cap).

## How it will be read (written now)

- P2, P3 and P5 all hold: the fused PRF list becomes Task 1's first stage, and the next job
  reranks its first 50 with the MedCPT cross-encoder if `spark36-rerank-v3` supports the reranker
  (its R3 and R4).
- P2 fails and leg D finds at least 26 of 43 by depth 1,000: the next recall job reranks plain
  BM25 at a larger depth instead (its own pre-registration, with the cross-encoder's time per
  question measured first).
- P2 fails and leg D finds fewer than 26: neither PRF nor depth fixes L's recall, and L's misses
  are written up by where the first gold paper sits (`first_gold_rank_bands`) before any more
  first-stage work.
- P5 fails while P2 and P3 hold: PRF is kept for L-like questions only after a separate check;
  nothing switches on R's evidence alone.

Limits: R and L are proxy questions written by AI agents, and L has only 43, so one question moves
recall by 0.023. BioGen gold is per topic. Query times depend on what else ran on the host. PRF is
decades-old prior art (Lavrenko and Croft 2001; RM3); what is new is only measuring it on this
corpus and these dev sets. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
