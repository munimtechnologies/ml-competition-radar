# prf: pseudo-relevance feedback for SPARK Task 1 recall

Part of `spark-pubmed/`, MV2 of Munim, Inc.'s open groundwork for the NIH/NLM SPARK PubMed/PMC
Challenge. The code was made with AI agents working in his name. Code Apache-2.0; notes CC BY 4.0.

## Why

On headline L, MV2's hardest dev set (43 questions), whole-corpus BM25 put the target paper in its
first 100 candidates for only 20 questions, and in its first 50 for 19
(`../t1_runner/RESULTS-spark35.md`). A reranker reorders candidates but cannot bring back a paper
that BM25 never retrieved, so most of L's misses are a recall problem. The Task 1 page says only one
of the ranked items can be correct, and MRR is the primary metric.

## Method (`prf.py` 0.1.0)

Classic RM3-style pseudo-relevance feedback, with reciprocal-rank fusion instead of query-term
weights (SQLite FTS5's `bm25()` has no per-term weights):

1. Feedback word weights from the first `--fb-docs` (10) BM25 candidates: each document's share of
   the feedback BM25 scores x the word's frequency in its title + abstract + MeSH.
2. The `--fb-terms` (10) best words that are not already in the question and are found in 1 to
   `--max-df` (400,000) records.
3. The question's words OR the expansion words, BM25 depth 100.
4. Reciprocal-rank fusion (k = 60) of the baseline list and the expanded list.

It writes `ranked.jsonl` (fused) and `ranked_exp.jsonl` (expanded list alone) in `t1.py`'s
format, so `t1.py score` applies unchanged, and `run.json` with counts and timings. Expansion
words are never written to `run.json`. Standard library only.

- `test_prf.py`: 6 fake-data tests on a five-record FTS5 index (no network).
- `deep_recall.py` 0.1.0: for a `t1.py` ranked.jsonl run deeper than 100, counts how many
  questions have a gold paper within the first 1, 5, ... 1,000 candidates and where the first
  gold paper sits (counts and ranks only). `test_deep_recall.py`: 4 fake-data tests.
- `PREREGISTRATION-spark38.md`: predictions for job `spark38-prf-v1`, written before it was
  filed. `RESULTS-spark38.md`: its grades. `results-spark38/`: the job's raw counts (no question,
  abstract or expansion-word text).

## Use

```
python prf.py --db spark_full.db --needs out_l/ranked.jsonl --out-dir prf_l
python t1.py score --ranked prf_l/ranked.jsonl --gold dev/gold.jsonl --out-dir prf_l
```

## Status (2026-10-24, late): not adopted

`RESULTS-spark38.md`: 4 of 4 checks and 6 of 11 predictions held. The fused list reaches L's
target in its first 100 for 24 of 43 questions (BM25: 20), but top:5 MRR fell on BioGen (0.3174
to 0.2700) and R (0.7931 to 0.6996), and each query took about twice as long. Plain BM25 to depth
1,000 showed that L's targets are mostly deep, not missing: 26 of 43 within 200 candidates, 32
within 300, 36 within 1,000. The next recall test is a deeper cross-encoder rerank of plain BM25
(`../rerank/PREREGISTRATION-spark40.md`), not PRF.

PRF is decades-old prior art (Lavrenko and Croft 2001; RM3). What is new here is only measuring
it on the SPARK corpus and dev sets.

Contact: MV2, Munim, Inc., mv2@munimtech.com
