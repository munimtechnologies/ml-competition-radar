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
  pre-registered predictions and graded results (`corpus_build/RESULTS*.md`).
- `dev_sets/` holds two practice question sets, because no SPARK questions are public yet:
  - L: well-known first reports since 1959, each matched to PubMed's own record. 46 of 47 were
    found automatically, and a hand check confirmed every match.
  - R: 90 questions written from a fixed-seed sample of corpus abstracts. All 90 titles were
    checked against NCBI's records.
- `t1_runner/` holds the Task 1 pipeline: the resumable index builder, BM25 candidates, ten
  fixed cutoff policies (the task penalises wrong citations), the submission JSONL, a format
  validator and a scorer. Its predictions were pre-registered before any score existed.
- `rerank/` is the second stage: NCBI's public-domain MedCPT cross-encoder rereads the top BM25
  candidates on CPU. Its card check, CPU benchmark, whole-corpus scoring and cut-off counts are
  graded (`rerank/RESULTS.md`, `rerank/RESULTS-spark36.md`, `rerank/RESULTS-spark39.md`);
  `rerank/depth_curve.py` measures how deep to rerank.
- `system/` joins the stages into the one command the challenge's no-network Docker image runs:
  `spark_t1.py` turns a questions file into the two planned submission files, resumes after a
  stop and times every question (`system/README.md`; the image itself is not built yet).
- `speed/` tested leaving very common words out of the BM25 query (`speed/RESULTS-spark37.md`).
- `prf/` tested pseudo-relevance feedback fused with the BM25 list as a recall stage
  (`prf/RESULTS-spark38.md`; not adopted).
- `t2/` starts Task 2. `compose.py` is an extractive baseline that copies every sentence from a
  cited abstract and flags conflicting findings. `biogen_census.py` and `biogen_stance.py` turn
  NIST's TREC 2024 BioGen judgments (65 health questions, citations judged Supports /
  Contradicts / Neutral / Not Relevant) into development data and measure how repeatable each
  label is. Every job was pre-registered.
- `sparkdocs/` fetches the documents attached to the two challenge pages and extracts their text
  (`sparkdocs/README.md` quotes the Task 1 rules that shape the pipeline and summarises the
  announcement).

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
- **Index.** The whole-corpus FTS5 index at `detail=full` is built: 39,167,523 records, 92.5 GB
  (2,362 bytes per record, above the pilot's 2.26 KB because later files carry more abstracts).
  Whole-corpus BM25 is slow: a 6.1 s median per short question at depth 50 on a warm pass, and a
  35.4 s median on R's full-length questions at depth 100, against 30 ms on the 1.2-million-record
  pilot.
- **Whole-corpus Task 1 baseline.** BM25 alone scores top-5 MRR 0.793 on R but 0.086 on headline
  L, where the target is in the first 100 candidates for only 20 of 43 questions. L is the hard
  set and the one that guides the next stages.
- **Dropping common words is fast but costly.** Leaving out words found in over 400,000 records
  made queries 9 to 14 times faster but cut top-5 MRR from 0.793 to 0.538 on R; such words still
  carry a large BM25 weight. The Task 1 query stays unpruned (`speed/RESULTS-spark37.md`).
- **Reranking works on the whole corpus, on every dev set.** MedCPT's cross-encoder (fp32, about
  0.4-0.5 s per question-article pair on 2 CPUs) reranking BM25's first 50 raised top-5 MRR on L
  from 0.086 to 0.150 (hits 6 to 13 of 43), on the 65 BioGen questions from 0.317 to 0.432, and
  on R from 0.793 to 0.898 (hits 79 to 87 of 90). Task 2 answers built from reranked papers had
  more citations judged Supports (judged precision 0.817 vs 0.757). Fusing its ranks with BM25's
  did worse on all three sets (`rerank/RESULTS-spark36.md`, `rerank/RESULTS-spark39.md`).
- **The cross-encoder's score cannot say when its first answer is wrong.** All 198 first answers
  across the three dev sets scored above 0.9 (sigmoid), and that score separates right from wrong
  first answers barely better than chance on R (AUROC 0.57) and BioGen (0.54), and worse than
  chance on L (0.19). So a cut to fewer than five items cannot rest on it.
- **L's targets are deep, not missing.** Plain BM25 reaches a target for 19 of L's 43 questions
  in its first 50 candidates, 26 in 200, 32 in 300 and 36 in 1,000, at about the same query time
  as depth 100. Pseudo-relevance feedback reached 24 in its first 100 but lowered precision on
  BioGen and R, so it was dropped (`prf/RESULTS-spark38.md`).
- **BioGen's Contradicts label is the least repeatable.** Where the identical sentence citing the
  same paper was judged more than once, specific agreement is 0.85 for Supports and 0.22 for
  Contradicts (Scott's pi 0.23 overall). 92 of the 168 papers judged both ways in one topic got
  both labels on the identical sentence (`t2/RESULTS-biogen-stance*.md`).

## Status (2026-10-24, night)

Graded: corpus audit (10 of 11 predictions held), dev sets (10 of 11), FTS5 pilot and count
(11 of 16), mirror repair and full count (7 of 8 graded), index build continued (13 of 13) and
finished (14 of 16), reranker check (10 of 11), BioGen census (5 of 10, then 9 of 10), BioGen
stance (8 of 9, then 5 of 8, then 9 of 9), query pruning (5 of 10), whole-corpus reranking (10 of
10), pseudo-relevance feedback (6 of 11), reranking R with cut-off counts (7 of 10). Queued with
predictions written first: reranking BM25's first 300 on L and first 200 on BioGen and R, to set
the rerank depth (`rerank/PREREGISTRATION-spark40.md`), and the whole Task 1 system on R, which
should reproduce the graded R result exactly and time every question
(`system/PREREGISTRATION-spark41.md`). Planned submissions: `top:5`, and `top:1` as a second.

## Limits

- No SPARK questions have been published, so nothing here measures retrieval quality on them.
  The dev sets are AI-written proxies, not NLM's expert questions. BioGen's questions are
  consumer and clinician health questions, and its judgments cover only what 2024 runs cited.
- This covers only the PubMed part. The PMC part is defined by a `Challenge_PMCIDs.txt` list,
  which was not on the challenge page as of 2026-10-24.
- NIH's general challenge page describes the PMC part as about 50,000 CC0 articles. The task
  descriptions describe a Creative Commons, NIH-funded subset. Only the task descriptions were
  used here.

Contact: MV2, Munim, Inc., mv2@munimtech.com
