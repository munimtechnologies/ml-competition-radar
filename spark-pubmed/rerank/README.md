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
| `PREREGISTRATION.md` | Predictions for job `sparkrr-bench-v1`, written before it ran |
| `RESULTS.md` | Grades: 10 of 11 held |
| `results/` | The job's raw `bench.json` and `fetch_model.json` |
| `PREREGISTRATION-spark36.md` | Predictions for job `spark36-rerank-v1` (first rerank on real whole-corpus candidates: headline L and the 65 TREC 2024 BioGen questions), written before it was filed |
| `PREREGISTRATION-spark36-addendum.md` | The one change made for `spark36-rerank-v3` before it ran: memory ask 2.5 GB to 4.5 GB, nothing graded affected |
| `RESULTS-spark36.md` | Grades for `spark36-rerank-v3`: 3 of 3 checks and 10 of 10 predictions held |
| `results-spark36/` | That job's raw counts (no question or abstract text) |
| `PREREGISTRATION-spark39.md` | Predictions for job `spark39-cutoff-v1` (rerank R; cut-off, calibration and fusion counts on all three sets), written before it was filed |

The torch code needs torch 2.5.1 (CPU build) and transformers 4.46.3. Its tests run inside the
sealed jobs (13 of 13 passed in `sparkrr-bench-v1` and again in `spark36-rerank-v3`); they are not
re-run when files here are committed, because the publishing machine has no torch.
`test_cutoff.py` and `test_rerank_run.py` need only the standard library.

## Status (2026-10-24)

`RESULTS.md` (graded 2026-10-23): in fp32 the model reproduces its card's six scores to within
0.0001 and costs about 437 ms per question-article pair at 320 tokens on 2 CPUs, so scoring jobs
rerank the top **50** BM25 candidates. Dynamic int8 was dropped (it moved scores by 2.0-6.7 points).

`RESULTS-spark36.md` (graded 2026-10-24): on the whole 39.2-million-record index, reranking
BM25's first 50 raised top:5 MRR on headline L from 0.0860 to **0.1500** (hits 6 to 13 of 43) and
on BioGen Supports from 0.3174 to **0.4321** (hits 32 to 44 of 65), at a median 19-24 s per
question on 2 CPUs. Cited Task 2 answers built from reranked candidates had a judged precision of
0.817 (BM25 candidates: 0.757). The cross-encoder is now stage 2 of the Task 1 system.

Next: `spark39-cutoff-v1` checks that reranking does not hurt the easy R set, measures which cut
(fewer than five items) would pay if wrong citations are penalised, and tests rank fusion.

Contact: MV2, Munim, Inc., mv2@munimtech.com
