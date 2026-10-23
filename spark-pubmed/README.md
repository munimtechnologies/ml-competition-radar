# spark-pubmed: groundwork for the NIH/NLM SPARK PubMed/PMC Challenge

MV2 of Munim, Inc. is building this open groundwork for the NIH/NLM SPARK PubMed/PMC Challenge
(Task 1, Known-Item & Provenance Retrieval; Task 2, open-ended biomedical questions). The code
and notes were made with AI agents working in his name. Code is Apache-2.0 (the repository's
`LICENSE`); notes and data are CC BY 4.0.

This folder sits inside `ml-competition-radar`. It was planned as a separate repository, but
GitHub refused to create that repository twice on 2026-10-22 ("secondary rate limit").

## Folders

- `corpus_audit/` checks the PubMed part of the challenge corpus against the challenge's own
  definition. The definition reads: "all citations with a publication date from January 1,1959
  to July 31,2026", excluding publication type "preprint" (D000076942). The files are
  `pubmed27n0001`-`1306` under https://ftp.ncbi.nlm.nih.gov/pubmed/.pubmed-spark/, dated
  2026-08-31. It covers a 133-file sample, with pre-registered predictions and graded results.
- `fts_pilot/` mirrors the whole corpus (md5-checked, resumable), measures an on-disk SQLite
  FTS5 (BM25) index built with the standard library only, and counts every record of the corpus.
  It has pre-registered predictions and graded results (`fts_pilot/RESULTS.md`).
- `corpus_build/` holds the full count of all 1,306 files and the whole-corpus index build, with
  pre-registered predictions and graded results (`corpus_build/RESULTS.md`).
- `dev_sets/` holds two practice question sets, because no SPARK questions are public yet:
  - L: well-known first reports since 1959, each matched to PubMed's own record. 46 of 47 were
    found automatically, and a hand check confirmed every match.
  - R: 90 questions written from a fixed-seed sample of corpus abstracts. All 90 titles were
    checked against NCBI's records.
- `t1_runner/` holds the Task 1 pipeline: the resumable index builder, BM25 candidates, ten
  fixed cutoff policies (the task penalises wrong citations), the submission JSONL, a format
  validator and a scorer. Its predictions were pre-registered before any score existed.
- `rerank/` is the second stage: NCBI's public-domain MedCPT cross-encoder rereads the top BM25
  candidates on CPU. Its card check and CPU benchmark are graded (`rerank/RESULTS.md`).
- `t2/` starts Task 2. `compose.py` is an extractive baseline that copies every sentence from a
  cited abstract and flags conflicting findings. `biogen_census.py` turns NIST's TREC 2024
  BioGen judgments (65 health questions, citations judged Supports / Contradicts / Neutral /
  Not Relevant) into development data. Its predictions were pre-registered.

## Findings so far

- **Editorials and historical articles are in the corpus.** The challenge announcement says
  "Editorials, historical articles, and some content irrelevant to the task will be excluded".
  The published PubMed files hold 750,678 Editorial and 362,068 Historical Article records, out
  of 39,167,524 counted in all 1,306 files. They hold 0 Preprint records, as the task
  descriptions say.
- **The date window is not applied to one date field.** 11,578 records have a journal date after
  July 2026 and 29,751 entered PubMed after July 2026, but only 29 have neither a journal nor an
  electronic date on or before 2026-07-31. Reading the date rule this way is an inference from
  counts.
- **Corpus shape.** 39,167,524 records and 56.25 GB compressed. 74.2% of records have an abstract
  and 27.9% a PMC id. There is 1 duplicate PMID (25973045), and both copies sit in the same file,
  `pubmed27n0782.xml.gz`.
- **Index.** FTS5 at `detail=full` uses about 2.26 KB per record, about 88.5 GB for the whole
  corpus by extrapolation, and builds at about 2,500 records/s on one CPU. The `column` and
  `none` levels save only 13-22% and make queries 18-19 times slower, with the same ranking on
  the pilot's checks.
- **Reranker.** MedCPT's cross-encoder reproduces its model card's scores in fp32 and costs about
  437 ms per pair at 320 tokens on 2 CPUs. That allows about 82 candidates per question if 200
  questions must run in 2 hours, so the first scoring job reranks 50. Dynamic int8 is 1.7-2.1x
  faster and kept the card's order, but it shifted the six card scores by 2.0-6.7 points, so a
  score cutoff set in fp32 would not carry over. int8 is dropped.

## Status (2026-10-23)

Graded: corpus audit (10 of 11 predictions held), dev sets (10 of 11), FTS5 pilot and count
(11 of 16), mirror repair and full count (7 of 8 graded; the build part was stopped by the host,
so 6 are ungraded), reranker check (10 of 11). The runner's tests passed. The whole-corpus build
continues in job `spark33-build-v1`, with predictions in
`corpus_build/PREREGISTRATION-spark33.md`. Task 2: the BioGen census `biogen-census-v1` is
queued, with predictions in `t2/PREREGISTRATION-biogen.md`. Next steps: finish the index, score
the dev sets with the ten cutoff policies (pre-registered), score BM25 + rerank at depth 50, and
score the Task 2 baseline on the BioGen questions.

## Limits

- No SPARK questions have been published, so nothing here measures retrieval quality on them.
  The dev sets are AI-written proxies, not NLM's expert questions. BioGen's questions are
  consumer and clinician health questions, and its judgments cover only what 2024 runs cited.
- This covers only the PubMed part. The PMC part is defined by a `Challenge_PMCIDs.txt` list,
  which was not on the challenge page as of 2026-10-23.
- NIH's general challenge page describes the PMC part as about 50,000 CC0 articles. The task
  descriptions describe a Creative Commons, NIH-funded subset. Only the task descriptions were
  used here.

Contact: MV2, Munim, Inc., mv2@munimtech.com
