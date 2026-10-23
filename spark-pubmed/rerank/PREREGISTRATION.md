# Pre-registration: CPU benchmark of the stage-2 reranker (job `sparkrr-bench-v1`)

Written on 2026-10-23 at about 11:20 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why this job exists

MV2's SPARK PubMed/PMC Task 1 system is planned as BM25 over the whole corpus (index build in
progress, `../corpus_build/`), then a cross-encoder that rereads the top candidates, then a
small priority prior. The SPARK rules allow only open-weight models inside the Docker image, with
no network at run time, and break ties on compute time and memory. So before any reranker is
scored on the dev sets, we need to know whether the planned model loads exactly as published,
how many candidates per question it can afford on 2 CPUs, and whether int8 weights are a usable
cheaper variant.

Model: NCBI's MedCPT cross-encoder (`ncbi/MedCPT-Cross-Encoder`, commit
`71caf65d4927987813984f54c284405a13fcca49`, card licence "public-domain", a BERT model
initialised from PubMedBERT and trained on PubMed search logs; Jin et al. 2023, *Bioinformatics*
39(11) btad651). Its `LICENSE` file is empty (0 bytes); the licence is stated only in the card
metadata. Files and hashes were read from the Hugging Face API tree twice on 2026-10-23.

No corpus text and no question text is read by this job. The only text it uses is the model
card's own example (its query and six article strings).

## Fixed design

- Image `python:3.12`; torch 2.5.1 (CPU build) and transformers 4.46.3, version-asserted.
- Step 1: `python -m unittest -v test_rerank` (13 fake-data tests, tiny random BERT, no network).
- Step 2: `fetch_model.py`: 8 files (438,937,324 bytes), each checked against its git blob sha1
  or LFS sha256 before use.
- Step 3: `bench.py --threads 2 --batch 8 --batches 3`: the card's example rerun with the card's
  own tokenizer call; then model forward time per (query, article) pair at exactly 128, 256 and
  512 tokens (median of 3 timed batches of 8, after 1 warm-up batch); then dynamic int8
  quantisation of every Linear layer, in place, and the same two measurements again.
- Budget rule: rerank depth = pairs per question that fit 200 questions in 2 hours on 2 CPUs,
  with ms/pair interpolated at 320 tokens (a typical title + abstract).

## Predictions

Tests and download
- T0. All 13 tests pass.
- F1. All 8 files download and match their pinned hashes on the first attempt.

Card check (fp32)
- K1. All six logits are reproduced within 0.01 of the six values the card prints
  (6.9363, -8.2063, -8.7692, -12.3450, -10.4416, -15.8475). Risk stated in advance: the card's
  article strings end in "[...]"; if the printed values came from longer texts, K1 fails and
  that is a finding about the card, not about our loader.
- K2. The six articles come out in the card's order (1, 2, 3, 5, 4, 6, best first).

Speed (fp32, 2 threads)
- S1. 512 tokens: between 400 and 2,000 ms per pair.
- S2. 128 tokens: between 90 and 500 ms per pair.
- S3. The 512/256 ratio of ms per pair is between 1.9 and 2.6.
- S4. The 2-hour budget allows between 20 and 100 pairs per question (fp32).

int8
- Q1. Every int8 card logit is within 1.0 of its fp32 value, and the order of the six is
  unchanged.
- Q2. int8 is at least 1.4 times faster than fp32 at 256 tokens.

Memory
- M1. Peak RSS of the benchmark process stays under 2.0 GB.

## What the result decides

- The rerank depth for the first scoring job is the fp32 budget depth from S4, rounded down to
  20, 50 or 100 (and 20 if the budget allows fewer than 20).
- int8 stays a candidate only if Q1 holds. Whether the final system uses fp32 or int8 is decided
  later on dev-set MRR, not here.
- If K1 or K2 fails, the model is not used until the difference is explained.

Contact: MV2, Munim, Inc., mv2@munimtech.com
