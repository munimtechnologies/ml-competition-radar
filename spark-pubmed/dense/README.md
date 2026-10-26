# dense: a one-bit MedCPT index of PubMed as a first stage for SPARK Task 1

MV2 of Munim, Inc. Made with AI agents working in his name. Code Apache-2.0; notes CC BY 4.0.

BM25 over the whole 39.2-million-record corpus misses most targets of the hard headline set L:
even after reranking BM25's first 300 candidates, the cross-encoder's top five hold a target for
only 12 of 43 questions (`../rerank/RESULTS-spark40.md`). This folder tests a dense first stage
next to BM25. It does not embed PubMed itself, which is out of reach on 2 CPUs. It reuses the
MedCPT Article Encoder embeddings that NCBI publishes
(https://ftp.ncbi.nlm.nih.gov/pub/lu/MedCPT/pubmed_embeddings/; Jin et al. 2023, *Bioinformatics*
39(11) btad651): 38 chunks, about 36 million float32 vectors of 768 dimensions, 103 GiB, covering
PMIDs up to about 37.4 million (early 2024).

| File | What it does |
|---|---|
| `dense_build.py` | 0.1.1. Downloads each chunk (size checked), keeps one bit per dimension (value above that dimension's mean over chunk 36), deletes the floats; 96 bytes per article, about 3.5 GB in all; resumable; stops under 8 GiB free. On chunk 36 it measures what the bits lose against exact float search, and saves that record so a resumed build keeps it |
| `dense_search.py` | Fetches NCBI's MedCPT Query Encoder at a pinned commit (every file hash-checked), encodes questions as its card does (64 tokens, [CLS]), and scores them against the bits (q . b, which ranks exactly as q . (2b - 1)); writes `t1.py`-format candidate lists |
| `dense_eval.py` | Counts only: gold coverage of the index, reach of BM25 alone, dense alone and BM25 + dense unions, top-5 MRR of each list alone, and the pre-registered adoption rule |
| `test_dense.py` | 10 fake-data tests (numpy only, no torch, no network) |
| `PREREGISTRATION-spark44.md` | Predictions for job `spark44-dense`, written before it was first filed |
| `NOTE-spark44-v2.md` | Why the job was filed again as `-v2`, and the one code change that made |
| `NOTE-spark44-v3.md` | Why it was filed again as `-v3`: `-v2` was placed on a machine without the whole index, and its index check stopped it (no code change) |
| `NOTE-spark44-v4.md` | Why it was filed again as `-v4`: `-v3` was placed on that same machine and stopped the same way (no code change) |

The tests run inside the sealed job (python 3.12, numpy 2.1.3, torch 2.5.1+cpu, transformers
4.46.3). They are not re-run when these files are committed.

## Status (2026-10-26, about 01:00 UTC)

Nothing has been measured yet. `spark44-dense-v1` was stopped by its host during the index build,
after its first eight steps had exited 0. `spark44-dense-v2` and `spark44-dense-v3` were both
placed on the other machine, which holds only a partial copy of the data (112 of 1,306 files).
Each time, the index check stopped the job with exit 3 within four minutes, before any download or
build. `spark44-dense-v4` (same code, `NOTE-spark44-v4.md`) was also started on that machine, at
about 01:10 UTC on October 26, so the same check is expected to stop it. The runner has no way to
pin a job to the machine that holds its data; that fix has been asked for. The job measures, on L,
BioGen and R, whether BM25's first 100 plus dense's first 50 reach more targets than BM25's first
150 (the depth spark40 chose). The adoption rule is written in the pre-registration, which is
unchanged.

Prior art: MedCPT and NCBI's released embeddings; binary embedding retrieval (for example BPR,
Yamada et al. 2021); hybrid BM25 + dense candidate sets. New here is only the measurement: one bit
per dimension of the published PubMed embeddings, combined with BM25 on the whole SPARK corpus.

Contact: MV2, Munim, Inc., mv2@munimtech.com
