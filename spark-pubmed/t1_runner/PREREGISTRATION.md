# SPARK Task 1 runner: pre-registration of the cutoff predictions (2026-10-23, about 01:35 UTC)

MV2 of Munim, Inc. Written by AI agents working in his name before `t1.py` had run on any real
index or any dev question. Text CC BY 4.0, code Apache-2.0.

## Why

SPARK Task 1 allows up to five ranked PMIDs/PMCIDs per question and scores them by MRR, but the
task description also says "submissions will be penalized if they include incorrect citations".
The size of that penalty is not published. So the number of items to return is a decision with
two sides: more items can only raise MRR, and every extra item is a likely wrong citation.
`t1.py score` reports both sides for ten fixed policies (`top:1`-`top:5`, and `ratio:r` for
r = 0.5, 0.6, 0.7, 0.8, 0.9: keep every item whose BM25 score is at least r times the best,
always at least one, never more than five). A search on 2026-10-23 found no published study of
how many items to return under an MRR-plus-wrong-citation rule for known-item search over PubMed.
These predictions are about where BM25 alone leaves room, before any reranker exists.

## Setting (fixed now)

- Index: `build_index.py` over all 1,306 SPARK PubMed files (detail level chosen from the FTS5
  pilot), BM25 title x2, abstract x1, MeSH x0.5, as in `dev_sets/PREREGISTRATION.md`.
- Questions: headline L (43: the 42 verified, in-window, non-contested landmarks with no excluded
  publication type, plus L37 hand-verified as PMID 8458085) and the 90 frozen R questions
  (`dev_sets/r_questions/`), built by `t1.py devsets` from the published files.
- `t1.py run --depth 100 --policy top:5`, then `t1.py score`, once per set, in one sealed job.

## Predictions (graded word for word from that job's scores.json and run.json)

- P1. On both L and R, recall@20 is at least 0.10 higher than the hit share of `top:5`
  (a reranker over the first 20 candidates has room).
- P2. On L, recall@100 is at least 0.05 higher than recall@20.
- P3. On both sets, `ratio:0.8` returns fewer than 3.0 items per question on average, and its
  MRR is within 0.05 of `top:5`'s MRR.
- P4. On both sets, `top:5` has a mean of more than 3.5 wrong citations per question.
- P5. On R, the median query time is under 500 ms and the 95th percentile under 3,000 ms.
- P6. At most 2 of the 43 headline L PMIDs are missing from the index's meta table.

## Limits stated in advance

AI-written proxy questions are not NLM's expert questions, and the penalty for wrong citations
is unknown, so no policy is "best" from these numbers alone; they show the trade-off. Query time
depends on the machine the job lands on (recorded in the job summary). The dev sets were also
used to set nothing in `t1.py`: the ten policies and the BM25 weights were fixed before any
score existed.
