# spark-pubmed/rerank: stage-2 reranker for SPARK PubMed/PMC Task 1

Part of MV2 of Munim, Inc.'s open entry work for the NIH/NLM SPARK PubMed/PMC Challenge, made
with AI agents working in his name. Code Apache-2.0; text CC BY 4.0.

Stage 1 (BM25 over the whole corpus, `../corpus_build/`, `../t1_runner/`) finds candidates.
Stage 2 rereads the top candidates with a cross-encoder that sees the question and the article's
title + abstract together. The model is NCBI's MedCPT cross-encoder
(`ncbi/MedCPT-Cross-Encoder`, commit `71caf65`, card licence "public-domain"; Jin et al. 2023,
*Bioinformatics* 39(11) btad651), which runs on CPU inside the challenge's no-network Docker
image.

| File | What it does |
|---|---|
| `fetch_model.py` | Downloads the model's 8 files at the pinned commit; checks each against its git blob sha1 or LFS sha256 |
| `rerank.py` | `CrossEncoder`: fixed CPU threads, length-sorted batches, optional dynamic int8 |
| `bench.py` | Reruns the model card's example, times 128/256/512-token pairs, repeats in int8 |
| `test_rerank.py` | 13 fake-data tests (tiny random BERT, no network) |
| `rerank_run.py` | Reranks the first N BM25 candidates of `../t1_runner/t1.py run`'s `ranked.jsonl`, using title + abstract from the index; writes the same format (scores = sigmoid(logit), raw logits kept) so `t1.py score` applies unchanged |
| `test_rerank_run.py` | 4 fake-data tests with a fake scorer (standard library only) |
| `cutoff.py` | Counts only: MRR, hits, items returned and wrong items for top-k, absolute-score, empty-allowed and logit-margin cuts, with a hypothetical citation penalty; first-item calibration (AUROC); reciprocal-rank fusion of cross-encoder and BM25 ranks |
| `test_cutoff.py` | 8 fake-data tests (standard library only) |
| `depth_curve.py` | Counts only: from one deep rerank, what reranking BM25's first d candidates would have scored for every smaller d (reach, top:5 MRR, hits, questions gained or lost) |
| `test_depth_curve.py` | 5 fake-data tests (standard library only) |
| `PREREGISTRATION.md` | Predictions for job `sparkrr-bench-v1`, written before it ran |
| `RESULTS.md` | Grades: 10 of 11 held |
| `results/` | The job's raw `bench.json` and `fetch_model.json` |
| `PREREGISTRATION-spark36.md` | Predictions for job `spark36-rerank-v1` (first rerank on real whole-corpus candidates: headline L and the 65 TREC 2024 BioGen questions), written before it was filed |
| `PREREGISTRATION-spark36-addendum.md` | The one change made for `spark36-rerank-v3` before it ran: memory ask 2.5 GB to 4.5 GB, nothing graded affected |
| `RESULTS-spark36.md` | Grades for `spark36-rerank-v3`: 3 of 3 checks and 10 of 10 predictions held |
| `results-spark36/` | That job's raw counts (no question or abstract text) |
| `PREREGISTRATION-spark39.md` | Predictions for job `spark39-cutoff-v1` (rerank R; cut-off, calibration and fusion counts on all three sets), written before it was filed |
| `RESULTS-spark39.md` | Grades for `spark39-cutoff-v1`: 4 of 4 checks and 7 of 10 predictions held |
| `results-spark39/` | That job's raw counts (no question or abstract text) |
| `PREREGISTRATION-spark40.md` | Predictions for job `spark40-depth-v1` (rerank BM25's first 300 on L and first 200 on BioGen and R; depth curve), written before it was filed |
| `RESULTS-spark40.md` | Grades for `spark40-depth-v1`: 4 of 4 checks and 6 of 10 predictions held; stage-2 depth set to 150 |
| `results-spark40/` | That job's raw counts (no question or abstract text) |

The torch code needs torch 2.5.1 (CPU build) and transformers 4.46.3. Its tests run inside the
sealed jobs (13 of 13 passed in `sparkrr-bench-v1`, `spark36-rerank-v3`, `spark39-cutoff-v1` and
`spark40-depth-v1`); they are not re-run when files here are committed, because the publishing
machine has no torch. `test_cutoff.py`, `test_depth_curve.py` and `test_rerank_run.py` need only
the standard library.

## Status (2026-10-25)

`RESULTS.md` (graded 2026-10-23): in fp32 the model reproduces its card's six scores to within
0.0001 and costs about 437 ms per question-article pair at 320 tokens on 2 CPUs. Dynamic int8 was
dropped (it moved scores by 2.0-6.7 points).

`RESULTS-spark36.md`: on the whole 39.2-million-record index, reranking BM25's first 50 raised
top:5 MRR on headline L from 0.0860 to **0.1500** and on BioGen Supports from 0.3174 to
**0.4321**.

`RESULTS-spark39.md`: on the easy R set it raised top:5 MRR from 0.7931 to **0.8981**, so the
cross-encoder is stage 2 on every question type. Reciprocal-rank fusion with BM25 did worse than
the plain cross-encoder order on all three sets. The cross-encoder's sigmoid score was above 0.9
for every one of the 198 first answers, so it cannot tell a right first answer from a wrong one
(AUROC 0.19-0.57); cuts to fewer than five items use `top:k` only. Planned: submission 1 `top:5`,
a second submission `top:1`.

`RESULTS-spark40.md`: by the rule written in advance, **stage 2 reranks BM25's first 150
candidates** (mean top:5 MRR over L, BioGen and R 0.5011, against 0.4934 at depth 50; L 0.1628,
BioGen 0.4274, R 0.9130). The gain is small, under one L question, and it triples the
cross-encoder's work. Going deeper did not help L: at depth 300, 32 of 43 L questions have a
target among the candidates, but the cross-encoder puts only 12 in its top five (top:5 MRR
0.1492). The key prediction missed, so L's next step is a different first stage
(`../dense/PREREGISTRATION-spark44.md`).

Contact: MV2, Munim, Inc., mv2@munimtech.com
