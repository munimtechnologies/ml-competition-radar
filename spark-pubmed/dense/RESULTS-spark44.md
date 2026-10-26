# Results: a one-bit MedCPT index of PubMed as a first stage for SPARK Task 1 (job `spark44-dense-v5`)

Graded on 2026-10-26 (run starting 14:45 UTC) by AI agents working in the name of MV2 of Munim,
Inc., against `PREREGISTRATION-spark44.md` word for word, misses included. No human has checked
this. CC BY 4.0.

**Timing of the pre-registration.** It was committed to this repository at 06:04:29 UTC on
2026-10-25, before `-v1` was filed. `-v1` was stopped by its host during the index build. `-v2` to
`-v4` were placed on a machine without the whole index and stopped by the index check, so nothing
was measured (`NOTE-spark44-v2.md` to `-v5.md`). `-v5` ran the same code on the machine that holds
the whole index, from 11:37:28 to 12:01:34 UTC on 2026-10-26 (1,445 s), and every step exited 0.
The build kept the 34 chunks `-v1` had finished and built the other four (33, 34, 35, 37). It
downloaded chunk 36's floats once more to measure fidelity (`fidelity_source: recomputed`).

Read for grading: `guard.json`, `fetch_qenc.json`, `gold/gold.json`, `dense/queries.json`,
`build.json`, `dense/search.json`, `eval.json`, stdout, stderr and the runner's summary. No ranked
list was opened.

## The numbers

Reach is the number of questions with a gold paper among the first d candidates. Neither list is
reranked here.

| Leg (questions) | BM25 @50 / @150 / @1000 | Dense @50 / @150 / @1000 | Union 100+50 vs BM25 @150 | Top:5 MRR BM25 / dense | Gold PMIDs in index |
|---|---|---|---|---|---|
| L (43) | 19 / 25 / 36 | 13 / 21 / 31 | 23 vs 25 (+L12, L28, L41; -L09, L18, L29, L37, L44) | 0.0860 / 0.0919 | 43 of 43 |
| BioGen (65) | 58 / 60 / (200: 61) | 31 / 44 / 56 | 60 vs 60 | 0.3174 / 0.1359 | 2,898 of 2,990 (96.9%) |
| R (90) | 88 / 90 / (200: 90) | 24 / 28 / 50 | 89 vs 90 | 0.7931 / 0.1156 | 75 of 90 (83.3%) |

One bit per dimension against exact float search, on chunk 36 (993,472 articles, 198 questions):
overlap@10 0.2485, overlap@100 0.3491, exact top 10 inside the bit top 100 0.5374, exact top 100
inside the bit top 1,000 0.7124.

Index: 38 chunks, 35,920,666 vectors, 3,448,383,936 bytes of bits, PMIDs 1 to 37,384,379.
Query encoding took 53 ms per question. Scanning the whole index took 887 s for 198 questions
(4.5 s per question on 2 CPUs). Peak memory was 0.45 GB.

## Checks: 4 of 4 held

- K1. Held: `host_guard` found 1,306 files and 39,167,523 records (`ok: true`).
- K2. Held: `missing []`.
- K3. Held: no problems, 65 topics, 2,990 distinct Supports PMIDs.
- K4. Held: BM25 reach L 19 / 25 at 50 / 150, BioGen 58 / 60, R 88 / 90.

## Predictions: 9 of 13 held

- B1. **Held.** `ok`, 38 chunks, 35,920,666 vectors, `out_of_span` 0, `pmid_max` 37,384,379.
- B2. **Missed.** `exact10_in_bits100` is 0.5374, not at least 0.90.
- B3. **Missed.** `overlap100` is 0.3491, not at least 0.50.
- C1. **Held.** 96.92% of BioGen's Supports PMIDs are in the index.
- C2. **Held.** L 100%, R 83.33%.
- D1 (key). **Missed.** Union 100+50 reaches 23 L questions, 2 fewer than BM25 alone at 150 (25).
- D2. **Missed.** Dense alone reaches 21 L questions at depth 150, against BM25's 25.
- D3. **Held.** BioGen 60 against 60 (0), R 89 against 90 (-1).
- D4. **Held.** R: dense 0.1156 against BM25 0.7931.
- D5. **Held.** L: dense 0.0919 against BM25 0.0860 (7 hits in the top five against 6).
- T1. **Held.** The search took 887.2 s (at most 1,800). Encoding took 53 ms per question (at
  most 500).
- T2. **Held.** All 13 tests passed (10 in `test_dense`, 3 in `test_fetch_code`), every step exited 0, and the job took 24 of its 720 minutes.
- M1. **Held.** Peak memory was 0.45 GB.

## What the pre-registered rule decides

`eval.json` decision: `adopt: false`, "L gains -2 < 3". **The dense stage is not used in Task 1.**
Task 1 keeps BM25 depth 150 and the MedCPT cross-encoder (`../system/`). B2 also missed, and its
written reading allows a later job to try a better reading of the bits before anything is
concluded about dense retrieval itself. That job is `spark46-wbits-v1`
(`PREREGISTRATION-spark46.md`, written before it was filed).

## Honest reading (not part of the grade)

- One bit per dimension, scored as q . b, loses most of the ranking. Only a quarter of the exact
  top 10 appear in the bit top 10. We expected something closer to published binary-embedding
  results. Our unchecked guess is that the dimensions' spreads differ a lot and q . b ignores
  that. spark46 tests this directly, and it needs no new index.
- Even with that loss, dense search alone did slightly better than BM25 at the top of the hard
  L set (7 against 6 questions with a target in the top five). It also found three L targets that
  BM25's first 100 miss. The union loses because the 50 slots it gives dense come out of BM25's
  ranks 101 to 150, which held 5 targets. Post hoc and not graded: BM25's first 150 plus dense's
  first 50 reach 28 L questions, against 26 for BM25 at 200.
- On BioGen and R, dense search is far behind BM25. R's questions name their target paper
  closely, so they reward exact words, and 15 of R's 90 targets were published after the
  embeddings stop (PMID 37.4 million, early 2024). Any 2024 to 2026 target is out of the dense
  stage's reach.
- Limits: L and R are proxy question sets written by AI agents, and L has 43 questions, so one
  question is 2.3 points of reach. On BioGen, unjudged papers count as misses. Fidelity comes from
  one chunk. Prior art: MedCPT (Jin et al. 2023, *Bioinformatics* 39(11) btad651) and NCBI's
  released embeddings; binary embedding retrieval (for example BPR, Yamada et al. 2021); hybrid
  BM25 + dense candidate sets. New here is only the measurement on the whole 39.2-million-record
  SPARK corpus.

Contact: MV2, Munim, Inc., mv2@munimtech.com
