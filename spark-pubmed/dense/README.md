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
| `NOTE-spark44-v2.md` to `NOTE-spark44-v5.md` | Why the job was filed again four times: a host stop during the build (`-v1`, one code change in `-v2`), then three placements on a machine without the whole index (no code change) |
| `RESULTS-spark44.md` | The graded result: 4 of 4 checks, 9 of 13 predictions; the dense stage is not adopted |
| `dense_wbits.py` | 0.1.0. Weighted one-bit scoring, (q * w) . b with w = hi - lo per dimension (no new index), measured on chunk 36 against plain q . b and a two-bit code; writes the weighted queries for `dense_search.py` |
| `test_wbits.py` | 9 fake-data tests for `dense_wbits.py`, expected values worked out by hand |
| `fetch_code.py`, `test_fetch_code.py` | The job's code fetcher, with a `dense` group pinned to the commit `spark44-dense-v5` ran |
| `PREREGISTRATION-spark46.md` | Predictions for job `spark46-wbits-v1`, written before it was filed |

The tests run inside the sealed job (python 3.12, numpy 2.1.3, torch 2.5.1+cpu, transformers
4.46.3). They are not re-run when these files are committed.

## Status (2026-10-26, about 15:30 UTC)

`spark44-dense-v5` ran on the machine holding the whole index and was graded
(`RESULTS-spark44.md`). One bit per dimension, scored as q . b, kept only 53.7% of the exact top 10
inside its top 100 on chunk 36. BM25's first 100 plus dense's first 50 reached 23 of 43 L
questions, against 25 for BM25's first 150. **By the pre-registered rule the dense stage is not
used in Task 1.** Dense search alone did slightly better than BM25 at the top of L (7 against 6
questions with a target in the top five), and it is far behind on BioGen and R.

`spark46-wbits-v1` was filed at about 15:30 UTC on October 26. It tests whether weighting each
bit by how far that dimension moves recovers the ranking, using the same bits. If the rule still
does not adopt dense search, the dense line closes for Task 1.

Prior art: MedCPT and NCBI's released embeddings; binary embedding retrieval (for example BPR,
Yamada et al. 2021) and asymmetric distances for binary codes (Gordo et al. 2014); hybrid BM25 +
dense candidate sets. New here is only the measurement: one bit per dimension of the published
PubMed embeddings, combined with BM25 on the whole SPARK corpus.

Contact: MV2, Munim, Inc., mv2@munimtech.com
