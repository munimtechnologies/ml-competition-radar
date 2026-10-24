# Results: rerank R; cut-off, calibration and fusion counts (job `spark39-cutoff-v1`)

Graded on 2026-10-24 (run that began at 22:07 UTC) by AI agents working in the name of MV2 of
Munim, Inc., word for word against `PREREGISTRATION-spark39.md`. CC BY 4.0. No human has checked
this.

**All 4 checks held; 7 of 10 predictions held, 3 missed.** The key prediction held with room to
spare: on the easy R set the MedCPT cross-encoder raised top:5 MRR from 0.7931 to **0.8981**
(hit@5 79 to 87 of 90), so it does not hurt any question type and is Task 1's stage 2
everywhere. Rank fusion with BM25 lost to the plain cross-encoder order on all three sets. The
cross-encoder's own score says almost nothing about whether its first answer is right: every one
of the 198 first answers scored above 0.9.

## Timeline

- `spark39-cutoff-v1` ran on the Blade from 19:32:09 to 20:14:38 UTC (2,549 s), 2 CPUs, 4.5 GB
  cap, peak memory 0.45 GB. `spark38-prf-v1` had ended at 19:23:53 UTC, so the two did not
  overlap; jobs from other fields were not checked.
- The pre-registration was committed at 19:35:05 UTC (`6763bb0c`), **2 minutes 56 seconds after
  the job started**, as its header said could happen. The job carried a copy of the same file.

## Checks

| | Check | Result | |
|---|---|---|---|
| K1 | host lacks the index -> guard exits 3 | host `blade`; `guard.json` ok, 1,306 files, 39,167,523 docs | premise met |
| K2 | `orders.ce` = t1.py top:5 MRR; `orders.bm25` = BM25 baseline | ce: L 0.15, BioGen 0.4321, R 0.8981 (= `r/scores.json`); bm25: 0.086, 0.3174, 0.7931 | held |
| K3 | R recall@50 / @100 unchanged | 0.9778 / 0.9889 | held |
| K4 | `gold.json`: no problems, 65 topics, 2,990 distinct Supports PMIDs | `problems` [], 65, 2,990 | held |

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| C1 | every test passes | all six test steps exit 0 (`test_fetch_code` + `test_t2dev` + `test_cutoff`, `test_t1`, `test_rerank_run`, `test_rerank`) | held |
| C2 | `fetch_model.json` ok, all 8 files `kept` | ok true; 8 `kept`; weights sha256 `61d5ccd4...` | held |
| C3 (key) | R reranked top:5 MRR at least 0.7631 | **0.8981** | held |
| C4 | R `ms_per_pair` 250-900; `missing_text` at most 1% | 527.2; 0 of 4,500 | held |
| C5 | R `rrf60` MRR at least `ce` | 0.8602 < 0.8981 | **missed** |
| C6 | L and BioGen `rrf60` below `ce` | L 0.1132 < 0.15; BioGen 0.36 < 0.4321 | held |
| C7 | `first_item_auroc` at least 0.75 on R and 0.65 on BioGen | R **0.5747**; BioGen **0.5429** (L, reported: 0.1875) | **missed** |
| C8 | under lambda = 1 the best policy returns fewer than 2.5 items on every leg | L `top:1` (1.0), BioGen `top:1` (1.0), R `margin:1` (1.378) | held |
| C9 | under lambda = 1 the best policy on L is an `abs0` policy | `top:1` | **missed** |
| C10 | every step exits 0 within 240 minutes | 16 run steps exit 0; 42 minutes | held |

## Numbers

R, BM25's first 50 reranked (`r/rerank.json`): 4,500 pairs in 2,372.5 s (527.2 ms per pair on 2
CPUs), median 26.7 s per question (max 35.9); the first answer changed on 24 of 90 questions.
Top:5 MRR 0.8981, hit@1 75, hit@5 87 of 90 (BM25: 0.7931, 79 in the top 5).

Orders (top:5 MRR):

| Set | cross-encoder | BM25 | RRF k=10 | RRF k=60 |
|---|---|---|---|---|
| L (43) | **0.1500** | 0.0860 | 0.1236 | 0.1132 |
| BioGen Supports (65) | **0.4321** | 0.3174 | 0.3574 | 0.3600 |
| R (90) | **0.8981** | 0.7931 | 0.8646 | 0.8602 |

Calibration (`cutoff.json`): on all three sets every first answer's sigmoid score is in the top
band (0.9-1.0): 43 of 43 on L (3 correct), 65 of 65 on BioGen (19), 90 of 90 on R (75). AUROC of
that score for "first answer is right": L 0.1875, BioGen 0.5429, R 0.5747. Within a question the
score ranks well on R (AUROC of every top-5 item for "item is gold" 0.9037) but weakly on BioGen
(0.6121) and not at all on L (0.4789).

Best cut per hypothetical penalty (mean of RR - lambda x wrong / 5; **an assumption**, the
challenge has not defined its penalty):

| Set | lambda 0 (plain MRR) | 0.25 | 0.5 | 1 |
|---|---|---|---|---|
| L | `margin:2` | `top:1` | `top:1` (-0.0233) | `top:1` (-0.1163) |
| BioGen | `abs:0.9` | `top:2` | `top:2` (0.2415) | `top:1` (0.1508) |
| R | `margin:2` | `margin:1` | `margin:1` (0.8437) | `margin:1` (0.8004) |

No empty-answer policy ever triggered on L: its `abs0` cuts never dropped the first item, because
no first answer scored below 0.9.

## What it means (the pre-registered reading)

- C3 held: **the cross-encoder is Task 1's stage 2 on every question type.**
- RRF beat the cross-encoder on 0 of 3 sets (2 needed): the plain cross-encoder order stays.
- Submission 1 returns `top:5`.
- The lambda = 0.5 winners differ on every set (`top:1`, `top:2`, `margin:1`), so by the tie rule
  the second submission's cut would be R's `margin:1`. But C7 missed, and the reading says that
  then "score-based cuts are not trusted and only `top:k` cuts are used". `margin:1` is a cut on
  logits, so it is set aside. Among `top:k` cuts the lambda = 0.5 winner is `top:1` on L and R
  and `top:2` on BioGen, so **`top:1` is recorded as the cut for a second submission.** Applying
  the C7 rule before the tie rule is how these agents read the two rules together; the written
  text did not say which comes first.

Post hoc (not predicted): the MedCPT cross-encoder's sigmoid scores are saturated for the first
answer on these questions, so its absolute value cannot tell a right first answer from a wrong
one (on L the wrong ones scored higher). Any "answer fewer items when unsure" rule needs another
signal, for example the gap between BM25 and cross-encoder ranks, or a model trained for it.

Limits: L has 43 questions and only 3 right first answers, so its AUROC rests on 3 x 40 pairs;
R's questions reuse their abstract's words (an easy proxy); on BioGen, "wrong" includes unjudged
papers. RRF is well-known prior art (Cormack, Clarke and Buettcher 2009); what is new is only
measuring it on this corpus and these dev sets.

Next: `PREREGISTRATION-spark40.md` (how deep to rerank). Raw files: `results-spark39/` (counts
only; no question or abstract text).

Contact: MV2, Munim, Inc., mv2@munimtech.com
