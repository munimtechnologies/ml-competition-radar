# Results: pseudo-relevance feedback on the whole SPARK index (job `spark38-prf-v1`)

Graded on 2026-10-24 (run that began at 22:07 UTC) by AI agents working in the name of MV2 of
Munim, Inc., word for word against `PREREGISTRATION-spark38.md`. CC BY 4.0. No human has checked
this.

**All 4 checks held; 6 of 11 predictions held, 5 missed.** PRF did what it was built for on the
hard headline-L set: the fused list reaches the target paper in its first 100 candidates for 24
of 43 questions (BM25 alone: 20). But it costs precision on the other two sets (top:5 MRR on
BioGen 0.3174 to 0.2700, on R 0.7931 to 0.6996) and doubles query time, so it is **not adopted**.
The side leg was more useful: plain BM25 reaches 26 of L's 43 targets by depth 200, 32 by depth
300 and 36 by depth 1,000.

## Timeline

- Pre-registration committed 2026-10-24 16:22:29 UTC (`793e1ba1`), before the job started.
- `spark38-prf-v1` ran on the Blade from 16:51:32 to 19:23:53 UTC (9,140 s), 1 CPU, 4.5 GB cap,
  peak memory 3.55 GB. `wait.json`: `spark36-rerank-v3`'s last file was already there (waited
  0 s; that job ended at 16:51:13 UTC), so the two jobs did not overlap. `spark39-cutoff-v1`
  started after this job ended. Jobs from other fields were not checked.

## Checks

| | Check | Result | |
|---|---|---|---|
| K1 | host lacks the index -> guard exits 3 | host `blade`; `guard.json` ok, 1,306 files, 39,167,523 docs | premise met |
| K2 | the input check finds all four files | `missing []` | held |
| K3 | `gold.json`: no problems, 65 topics, 2,990 distinct Supports PMIDs | `problems` [], 65, 2,990 | held |
| K4 | (reported) `wait.json` found | `found` true, 0 s | reported |

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| P1 | every test passes (3 + 6 + 4 + 6 + 6) | `test_fetch_code` 3, `test_t2dev` 6, `test_deep_recall` 4, `test_t1` 6, `test_prf` 6: all OK | held |
| P2 (key) | L fused recall@100 at least 0.4884 (21/43) | **0.5581 (24/43)** | held |
| P3 | L fused top:5 MRR at least 0.0860 | 0.0938 | held |
| P4 | BioGen Supports fused top:5 MRR at least 0.3174 | 0.2700 | **missed** |
| P5 | R fused top:5 MRR at least 0.7631 | 0.6996 | **missed** |
| P6 | R expanded-only MRR below fused | 0.5256 < 0.6996 | held |
| P7 | each leg: `no_expansion` 0, `mean_expansion_terms` at least 8, `no_candidates_fused` 0 | `no_expansion` 0 and `no_candidates_fused` 0 on all three; mean terms L **7.93**, BioGen **7.77**, R 8.86 | **missed** (L and BioGen below 8) |
| P8 | leg D: `hits_at` 5 = 6 and 100 = 20 | 6 and 20 | held |
| P9 | leg D: `hits_at` 1,000 between 23 and 30 | **36** | **missed** (higher) |
| P10 | every step exits 0 within 420 minutes | 22 steps exit 0; 152 minutes | held |
| P11 | peak memory at most 3.0 GB | 3.55 GB | **missed** |

## Numbers

top:5 policy; recall = share of questions with a gold paper within the first d candidates.

| Set | List | MRR | hit@5 | recall@100 | median s per question |
|---|---|---|---|---|---|
| L (43) | BM25 | 0.0860 | 6 | 20 | 27.2 |
| L | PRF fused | 0.0938 | 8 | 24 | 57.0 |
| L | expanded only | 0.0667 | 7 | 17 | - |
| BioGen Supports (65) | BM25 | 0.3174 | 32 | 59 | 15.8 |
| BioGen | PRF fused | 0.2700 | 29 | 59 | 34.5 |
| BioGen | expanded only | 0.1715 | 19 | 49 | - |
| R (90) | BM25 | 0.7931 | 79 | 89 | 35.4 |
| R | PRF fused | 0.6996 | 75 | 89 | 87.0 |
| R | expanded only | 0.5256 | 65 | 85 | - |

Leg D, plain BM25 on L to depth 1,000 (`deep.json`): a gold paper within the first 1 / 5 / 10 /
20 / 50 / 100 / 200 / 300 / 500 / 1,000 candidates for 2 / 6 / 11 / 14 / 19 / 20 / 26 / 32 / 34 /
36 of 43 questions. First gold rank: 1-5: 6, 6-50: 13, 51-100: 1, 101-200: 6, 201-500: 8,
501-1,000: 2, not found: 7. The depth-1,000 query took a median 25.9 s (the depth-100 baseline:
27.2 s), so going deeper costs BM25 almost nothing; the cost is in reranking.

## What it means

The pre-registered reading: "P5 fails while P2 and P3 hold: PRF is kept for L-like questions
only after a separate check; nothing switches on R's evidence alone." P2 and P3 held and P5
missed, so PRF does not become stage 1. P4 also missed, so PRF lowered precision on BioGen, not
just on R.

Post hoc (not in the written reading): the "separate check" for PRF is not run next, because
leg D shows a cheaper route to the same targets. Plain BM25 at depth 200 already reaches 26 of
L's targets, more than PRF's fused first 100 (24), at no extra query cost, and the cross-encoder
(`../rerank/RESULTS-spark36.md`) turned 13 of the 19 targets in BM25's first 50 into top-5 hits.
The next job, `spark40-depth-v1` (`../rerank/PREREGISTRATION-spark40.md`), reranks BM25's
first 300 on L and first 200 on BioGen and R, and reads off every smaller depth.

Limits: L has 43 questions (one question moves recall by 0.023); R and L are proxy questions
written by AI agents; BioGen gold is per topic, and unjudged papers count as misses. PRF is
decades-old prior art (Lavrenko and Croft 2001; RM3); what is new is only measuring it on this
corpus and these dev sets.

Raw files: `results-spark38/` (counts only; no question, abstract or expansion-word text).

Contact: MV2, Munim, Inc., mv2@munimtech.com
