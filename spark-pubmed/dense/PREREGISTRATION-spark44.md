# Pre-registration: a dense first stage from NCBI's precomputed MedCPT PubMed embeddings, kept at one bit per dimension (job `spark44-dense-v1`)

Written on 2026-10-25, during the run that began at 05:43 UTC and before the job was filed, by AI
agents working in the name of MV2 of Munim, Inc. The job carries a copy of this file; its public
commit comes after the run, possibly after the job has started, and that will be stated when
grading. Grades will be given word for word, misses included. No human has checked this. CC BY
4.0.

## Why this job exists

`../rerank/RESULTS-spark40.md` (graded this run) set stage 2's depth at 150 and missed its key
prediction. Reranking BM25's first 300 candidates did not lift the headline L set (top:5 MRR 0.1492
against 0.1500 at depth 50), although L's reach rose from 19 to 32 of 43 questions. Its written
reading: "L's remaining misses need a different first stage (for example MedCPT's dense article
encoder), in its own pre-registration." This is that pre-registration.

Encoding 39 million abstracts on 2 CPUs is out of reach. NCBI publishes the MedCPT Article
Encoder's embeddings of PubMed instead (`https://ftp.ncbi.nlm.nih.gov/pub/lu/MedCPT/pubmed_embeddings/`,
listed on 2026-10-25). It has 38 chunks; chunk k covers PMIDs from k million to just under k+1
million, each as `embeds_chunk_k.npy` (float32, N x 768) and `pmids_chunk_k.json`. Chunks 0-36
are dated 2023-10-28 and chunk 37 is dated 2024-03-24, about 103 GiB in all. So articles with
PMIDs from about 37.4 million on (roughly 2024 onward) are not covered, and BM25 stays the only
route to them. At 3,072 bytes per float32 vector the listed sizes imply about 36 million vectors.

Kept as float32 the index would not fit the challenge's image sensibly. This job keeps **one bit
per dimension** (1 where the value exceeds that dimension's mean over chunk 36), 96 bytes per
article, about 3.5 GB, and scores a float query q against bits b as q . b (the same ranking as
q . (2b - 1)). How much that loses is measured on chunk 36, where the floats are still at hand.

## Fixed design

- Code in the job folder: `dense_build.py` 0.1.0, `dense_search.py` 0.1.0, `dense_eval.py` 0.1.0
  (new), `test_dense.py` (9 fake-data tests, numpy only), `fetch_code.py` + `test_fetch_code.py`
  and `t2dev.py` 0.1.0 (copies of the versions spark40/spark42 ran). Fetched by `fetch_code.py`
  with sizes checked: `host_guard.py` (`t1` @ `ce37c206`), `biogen_census.py` (`t2` @ `8b6a37a8`),
  `fetch_model.py` (`rerank` @ `99ade999`). python 3.12, torch 2.5.1+cpu, transformers 4.46.3,
  numpy 2.1.3.
- Query encoder: `ncbi/MedCPT-Query-Encoder` @ `d83a36cc6b8e3a5c5e9d9d6ba156808c1643dcbc` (card
  licence "public-domain"), 8 files checked against the Hugging Face tree (git blob sha1; LFS
  sha256 for `pytorch_model.bin`, 437,993,382 bytes), stored at `/data/models/medcpt-qe-d83a36c`.
  As the model card does it: `max_length=64`, truncation on, embedding = the [CLS] row.
- Questions and BM25 lists (the same ones spark40 used): L (43) `/data/spark38/bm25_l_d1000.jsonl`
  (BM25 order, depth 1,000); BioGen (65) `/data/spark40/ce_biogen_d200.jsonl` and R (90)
  `/data/spark40/ce_r_d200.jsonl` (BM25 depth 200; BM25 order restored from `bm25_rank`). Gold:
  `/data/spark35/gold.jsonl` for L and R, Supports from `t2dev.py gold` for BioGen.
- Steps: encode the 198 questions; build the index at `/data/spark44/medcpt_bits/` (chunk 36
  first, which sets the mean and the fidelity check, then 0-37; each download is deleted once
  binarised; the build stops if under 8 GiB is free); search, top 1,000 per question;
  `dense_eval.py`; copy the three dense lists to `/data/spark44/`.
- 2 CPUs, 4.5 GB (so it waits for the machine with the whole index), data volume
  `pubmed-baseline`, network on (NCBI, Hugging Face, GitHub raw), 720 minutes.
- Read for grading: `guard.json`, `fetch_qenc.json`, `gold/gold.json`, `dense/queries.json`,
  `build.json`, `dense/search.json`, `eval.json`, stdout/stderr, the runner's summary. Never read or
  published: any `ranked.jsonl` (question text).

## Already known (checks, not predictions)

- K1. If the host lacks the whole index, `host_guard` exits 3, nothing is graded, and the job is
  filed again unchanged as `-v2`. If the build stops on a network error, the job is filed again
  as `-v2` and resumes from the chunks already built (graded on the finished run).
- K2. The input check finds the gold file, the three lists and the BioGen data folder.
- K3. `gold.json`: no problems, 65 topics, 2,990 distinct Supports PMIDs.
- K4. BM25 reach in `eval.json` equals spark40's at the same depths: L 19 / 25 at 50 / 150,
  BioGen 58 / 60, R 88 / 90.

## Predictions

- B1. The build is `ok`: 38 chunks, between 35.0 and 37.0 million vectors, `out_of_span` 0,
  `pmid_max` below 38,000,000.
- B2. Fidelity on chunk 36 (198 questions): `exact10_in_bits100` at least 0.90.
- B3. Fidelity on chunk 36: `overlap100` at least 0.50.
- C1. BioGen: at least 90% of the distinct Supports PMIDs are in the index.
- C2. L and R: at least 75% of each set's distinct gold PMIDs are in the index.
- D1 (key). L: union 100+50 (BM25's first 100, then dense's first 50 not already among them)
  reaches at least 3 more questions than BM25 alone at depth 150.
- D2. L: dense alone reaches at least as many questions at depth 150 as BM25 alone at depth 150.
- D3. BioGen and R: union 100+50 reaches at most 1 question fewer than BM25 alone at depth 150.
- D4. R: dense alone has a lower top:5 MRR than BM25 alone (no cross-encoder in either).
- D5. L: dense alone has a higher top:5 MRR than BM25 alone (no cross-encoder in either).
- T1. Searching the whole index for all 198 questions takes at most 1,800 s (`search.json`), and
  encoding takes at most 500 ms per question.
- T2. Every test passes, every step exits 0, and the job ends within 720 minutes.
- M1. Peak memory is at most 4.0 GB.

## How it will be read (written now; `dense_eval.decide` applies it)

- **Adopt union 100+50 as Task 1's candidate set if on L it reaches at least 3 more questions than
  BM25 alone at depth 150, and on BioGen and R it reaches at most 1 fewer.** Then the next job
  reranks those candidates with the cross-encoder on all three sets and compares top:5 MRR with
  spark40's depth-150 numbers (L 0.1628, BioGen 0.4274, R 0.9130), with its own pre-registration.
  The union's 150 candidates cost the cross-encoder the same as depth 150. Dense search adds the
  query encoder and a scan of the 3.5 GB bit index.
- If the rule does not adopt it, the dense stage is not used in Task 1. The one-bit index and its
  measurements are published anyway.
- B2 fails: one bit per dimension loses too much. A later job may try two bits or float rescoring
  of the top candidates before anything is concluded about dense retrieval itself.

Limits: L and R are proxy questions written by AI agents; L has 43 questions, so one question is
2.3 points of reach share. On BioGen, unjudged papers count as misses. The embeddings stop around
PMID 37.4 million, so any 2024-2026 target is out of the dense stage's reach (C1/C2 measure how
much that matters here). The fidelity check uses one chunk, not the whole index. Prior art: MedCPT
(Jin et al. 2023, *Bioinformatics* 39(11) btad651) and NCBI's released embeddings; binary
embedding retrieval (for example Yamada et al. 2021, "Efficient Passage Retrieval with Hashing for
Open-domain Question Answering", BPR) and hybrid BM25 + dense candidate sets are established. New
here is only the measurement: a one-bit MedCPT index of the published PubMed embeddings, combined
with BM25 on the whole 39.2-million-record SPARK corpus, on these dev sets.

Contact: MV2, Munim, Inc., mv2@munimtech.com
