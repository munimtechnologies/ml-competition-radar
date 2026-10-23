# spark-pubmed/rerank: stage-2 reranker for SPARK PubMed/PMC Task 1

Part of MV2 of Munim, Inc.'s open entry work for the NIH/NLM SPARK PubMed/PMC Challenge, made
with AI agents working in his name. Code Apache-2.0; text CC BY 4.0.

Stage 1 (BM25 over the whole corpus, `../corpus_build/`, `../t1_runner/`) finds candidates.
Stage 2 rereads the top candidates with a cross-encoder that sees the question and the article's
title + abstract together. The planned model is NCBI's MedCPT cross-encoder
(`ncbi/MedCPT-Cross-Encoder`, commit `71caf65`, card licence "public-domain"; Jin et al. 2023,
*Bioinformatics* 39(11) btad651), which runs on CPU inside the challenge's no-network Docker
image.

| File | What it does |
|---|---|
| `fetch_model.py` | Downloads the model's 8 files at the pinned commit; checks each against its git blob sha1 or LFS sha256 |
| `rerank.py` | `CrossEncoder`: fixed CPU threads, length-sorted batches, optional dynamic int8 |
| `bench.py` | Reruns the model card's example, times 128/256/512-token pairs, repeats in int8 |
| `test_rerank.py` | 13 fake-data tests (tiny random BERT, no network) |
| `PREREGISTRATION.md` | Predictions for job `sparkrr-bench-v1`, written before it ran |

Status (2026-10-23): pre-registered and queued. Results and grades will be added here as
`RESULTS.md`. No reranker has been scored on the dev sets yet.

Contact: MV2, Munim, Inc., mv2@munimtech.com
