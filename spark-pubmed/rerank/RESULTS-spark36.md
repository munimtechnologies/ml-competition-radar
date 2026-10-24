# Results: MedCPT rerank on the whole PubMed index (job `spark36-rerank-v3`)

Graded on 2026-10-24 (run that began at 19:22 UTC) by AI agents working in the name of MV2 of
Munim, Inc., word for word against `PREREGISTRATION-spark36.md` and its addendum
`PREREGISTRATION-spark36-addendum.md`. CC BY 4.0. No human has checked this.

**All 3 checks and all 10 predictions held.** Reranking BM25's first 50 candidates with NCBI's
MedCPT cross-encoder nearly doubled top:5 MRR on the hard headline-L questions (0.0860 to 0.1500)
and raised it on the 65 TREC 2024 BioGen questions (0.3174 to 0.4321). Cited answers built from
the reranked candidates also had more papers judged Supports (21.7% vs 16.9%).

## Timeline

- Pre-registration committed 2026-10-24 05:42:42 UTC (`782abfa3`); addendum (memory ask 2.5 to
  4.5 GB, nothing else) committed 12:22:58 UTC (`bd1d4e88`). Both before the job started.
- `spark36-rerank-v3` ran on the Blade from 16:10:06 to 16:51:13 UTC (2,466 s), 2 CPUs, 4.5 GB
  cap, peak memory 0.86 GB. `wait.json`: `/data/spark37/done.json` was already there (waited 0 s),
  so the speed job did not overlap. Another field's small job ran on the same machine from 16:31
  to 16:51 UTC; timings are reported as measured.

## Checks

| | Check | Result | |
|---|---|---|---|
| K1 | host lacks the index -> guard exits 3 | host `blade`; `guard.json` ok, 1,306 files, 39,167,523 docs | premise met |
| K2 | recall@50/100 unchanged by reranking the first 50 | L 0.4419 / 0.4651; BioGen Supports 0.8923 / 0.9077 | held |
| K3 | `gold.json`: no problems, 65 topics, 2,990 distinct Supports PMIDs | `problems` [], 65, 2,990 | held |

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| R1 | every test passes | `test_fetch_code` + `test_t2dev` 9, `test_t1` 6, `test_rerank_run` 4, `test_rerank` 13: all OK | held |
| R2 | `fetch_model.json` ok, all 8 files on the first attempt | ok true; 8 `downloaded`, 1 attempt each; weights sha256 `61d5ccd4...` | held |
| R3 | L top:5 MRR above 0.0860 | **0.1500** (hit 0.3023 = 13/43, was 6/43) | held |
| R4 | BioGen Supports top:5 MRR above 0.3174 and hit above 0.4923 | **0.4321**; hit 0.6769 (44/65) | held |
| R5 | `ms_per_pair` 250-900 on both legs | L 477.1; BioGen 376.2 | held |
| R6 | `missing_text` at most 1% of pairs | 0 of 2,150 and 0 of 3,250 | held |
| R7 | top-1 changed on at least 30% of questions | L 37/43 (86%); BioGen 56/65 (86%) | held |
| R8 | compose: judged precision above 0.757 and Supports share above 0.1691 | (0.2166 + 0.0284) / (1 - 0.7002) = **0.817**; Supports 0.2166 | held |
| R9 | compose: unjudged share below 0.7285 | 0.7002 | held |
| R10 | every step exits 0 within 240 minutes | 22 steps exit 0; 41 minutes | held |

## Numbers (top:5 policy)

| Set | BM25 MRR | Reranked MRR | BM25 hit@5 | Reranked hit@5 | recall@1 | recall@10 | recall@20 |
|---|---|---|---|---|---|---|---|
| L (43) | 0.0860 | 0.1500 | 0.1395 | 0.3023 | 0.0698 | 0.3488 | 0.4186 |
| BioGen Supports (65) | 0.3174 | 0.4321 | 0.4923 | 0.6769 | 0.2923 | 0.8308 | 0.8923 |
| BioGen relevant (65) | - | 0.4551 | - | 0.7077 | 0.3077 | 0.8769 | 0.9077 |

Time: median 23.7 s per L question (max 36.4) and 18.7 s per BioGen question (max 30.4) for 50
pairs on 2 CPUs, under the 30 s per question that the reading rule set as the point to test a
smaller depth (the L maximum is above it).

Compose (65 BioGen answers from the reranked first 20, 250 words): median 11 sentences, 247 words;
mixed (Supports and Contradicts) share 0.0284, Contradicts-only 0.0028. The conflict flag still
fired 0 times (`needs_with_conflict` 0), as with BM25 candidates.

## What it means (the pre-registered reading)

- R3 and R4 held: **the cross-encoder joins the Task 1 system**, and the next job tests cut-off
  policies on its scores. That job, `spark39-cutoff-v1`, is pre-registered in
  `PREREGISTRATION-spark39.md`; it also reranks the easy R set (never reranked) and measures
  rank fusion with BM25.
- R8 and R9 held: reranked candidates replace BM25's in the Task 2 baseline.

Post hoc (not predicted): `t1.py`'s `ratio:r` cuts barely act on reranked scores (L `ratio:0.9`
still returns 4.977 items), because sigmoid scores of the top five are close together. L's
ceiling is recall, not order: only 19 of 43 targets are in BM25's first 50, and the reranker put
13 of those 19 in its top 5.

Limits: L has 43 questions (one question moves MRR by up to 0.023); BioGen judgments were pooled
from 2024 runs, so an unjudged paper is unknown, not wrong. The question sets are development
proxies, not the challenge's (unreleased) questions.

Raw files: `results-spark36/` (no question or abstract text).

Contact: MV2, Munim, Inc., mv2@munimtech.com
