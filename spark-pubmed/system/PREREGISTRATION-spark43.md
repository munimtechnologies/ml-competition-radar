# Pre-registration: spark43-system-v1 (written 2026-10-28, committed before the job runs)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0.

## What runs

The whole SPARK Task 1 system (`spark-pubmed/system/spark_t1.py` 0.1.1 at commit 4765a24, BM25 over
the full-PubMed FTS5 index, then NCBI's MedCPT cross-encoder, fp32, 512 tokens) at its chosen depth
of 150, on all three development question sets: L (43 hard proxy questions), BioGen (65 questions,
gold = papers judged Supports) and R (90 proxy questions). 2 CPUs, 4.5 GB, one sealed job. The code
is fetched from the public repository at pinned commits (`fetch_code.py` 0.2.0, in this folder),
not copied.

## Why

spark40 chose depth 150 from a depth curve read off deeper reranks (L at 300, BioGen and R at 200).
spark41 timed the whole system only at depth 50 on R. Compute time breaks ties in the challenge,
so the system must be timed end to end at its final setting before the Docker image is built.
The dense first stage this job used to wait for was rejected (`../dense/RESULTS-spark46.md`), so
BM25 stays the first stage and the candidate set is final.

## Predictions (graded to the letter; misses are recorded, not explained away)

- P1. Top-5 MRR from `t1.py score` matches spark40's depth-150 reading within +/-0.005 on each set:
  L 0.1628, BioGen 0.4274, R 0.9130.
- P2. `agree.py rank --b-depth 150` against spark40's reranks: same top-5 order on at least 95% of
  common questions in each set, and `common` = 43, 65 and 90 (no question lost).
- P3. Whole job wall time <= 540 minutes (198 questions at about 70-120 s each, from spark40's
  351-508 ms per cross-encoder pair and BM25's 17-43 s median).
- P4. Median seconds per question (system `run.json`, all three sets) between 60 and 150.
- P5. Peak memory <= 4.5 GB (spark40 peaked at 3.15 GB, spark41 at 2.67 GB).

## Checks (the job fails, rather than grades, if any is false)

- C1. Every fetched file's size matches the pinned GitHub tree (`fetch_code.py` exit 0).
- C2. All unit tests pass (fetch_code, spark_t1, agree, t1, rerank_run, t2dev).
- C3. host_guard passes (full index present: 1,306 built files, 39,167,523 documents).

## Limits

L and R are proxy questions written by AI agents; BioGen counts unjudged papers as wrong. The
timing is on one shared 2-CPU container slot, not the challenge's hardware.

Contact: MV2, Munim, Inc., mv2@munimtech.com
