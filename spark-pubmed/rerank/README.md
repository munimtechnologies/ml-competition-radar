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
| `PREREGISTRATION.md` | Predictions for job `sparkrr-bench-v1`, written before it ran |
| `RESULTS.md` | Grades: 10 of 11 held |
| `results/` | The job's raw `bench.json` and `fetch_model.json` |
| `PREREGISTRATION-spark36.md` | Predictions for job `spark36-rerank-v1` (first rerank on real whole-corpus candidates: headline L and the 65 TREC 2024 BioGen questions), written before it was filed |
| `PREREGISTRATION-spark36-addendum.md` | The one change made for `spark36-rerank-v3` before it ran: memory ask 2.5 GB to 4.5 GB, nothing graded affected |

The code needs torch 2.5.1 (CPU build) and transformers 4.46.3. Its tests ran in the sealed job
`sparkrr-bench-v1` (13 of 13 passed on 2026-10-23). They are not re-run when files here are
committed, because the publishing machine has no torch.

## Status (2026-10-24)

`RESULTS.md` (graded 2026-10-23): in fp32 the model reproduces its card's six scores to within
0.0001 and costs about 437 ms per question-article pair at 320 tokens on 2 CPUs, so the first
scoring job reranks the top **50** BM25 candidates. Dynamic int8 is 1.7-2.1x faster and kept the
card's order, but it moved the scores by 2.0-6.7 points, so it is dropped as a candidate.

`PREREGISTRATION-spark36.md` was committed at 05:42:41 UTC on 2026-10-24 (commit `782abfa3`).
`spark36-rerank-v1` and `spark36-rerank-v2` were both placed on the Dell, which holds only a
partial copy of the index (112 of 1,306 files); their tests and code fetch ran, and `host_guard`
stopped each one with exit 3 before any rerank (v2 at 08:32 UTC): check K1, "premise not met", as
pre-registered. Nothing was graded. The compute runner picks the machine with the most memory left
after a job's expected use, and the Dell kept taking the 2.5 GB ask, so `spark36-rerank-v3` asks
for 4.5 GB with nothing else changed (`PREREGISTRATION-spark36-addendum.md`). It will be graded in
`RESULTS-spark36.md`. No reranker has been scored on the dev sets yet.

Contact: MV2, Munim, Inc., mv2@munimtech.com
