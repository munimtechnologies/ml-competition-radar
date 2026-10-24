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
  candidates on CPU. Its card check and CPU benchmark are graded (`rerank/RESULTS.md`).
- `speed/` tested leaving very common words out of the BM25 query (`speed/RESULTS-spark37.md`).
- `prf/` is a recall stage: pseudo-relevance feedback fused with the BM25 list. Its first job is
  pre-registered (`prf/PREREGISTRATION-spark38.md`).
- `t2/` starts Task 2. `compose.py` is an extractive baseline that copies every sentence from a
  cited abstract and flags conflicting findings. `biogen_census.py` and `biogen_stance.py` turn
  NIST's TREC 2024 BioGen judgments (65 health questions, citations judged Supports /
  Contradicts / Neutral / Not Relevant) into development data and measure how repeatable each
  label is. Every job was pre-registered.
- `sparkdocs/` fetches the documents attached to the two challenge pages and extracts their text
  (`sparkdocs/README.md` quotes the Task 1 rules that shape the pipeline).

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
- **Reranker.** MedCPT's cross-encoder reproduces its model card's scores in fp32 and costs about
  437 ms per pair at 320 tokens on 2 CPUs. That allows about 82 candidates per question if 200
  questions must run in 2 hours, so the first scoring job reranks 50. Dynamic int8 is 1.7-2.1x
  faster and kept the card's order, but it shifted the six card scores by 2.0-6.7 points, so a
  score cutoff set in fp32 would not carry over. int8 is dropped.
- **BioGen's Contradicts label is the least repeatable.** Where the identical sentence citing the
  same paper was judged more than once, specific agreement is 0.85 for Supports and 0.22 for
  Contradicts (Scott's pi 0.23 overall). 92 of the 168 papers judged both ways in one topic got
  both labels on the identical sentence (`t2/RESULTS-biogen-stance*.md`).

## Status (2026-10-24)

Graded: corpus audit (10 of 11 predictions held), dev sets (10 of 11), FTS5 pilot and count
(11 of 16), mirror repair and full count (7 of 8 graded), index build continued (13 of 13) and
finished (14 of 16), reranker check (10 of 11), BioGen census (5 of 10, then 9 of 10), BioGen
stance (8 of 9, then 5 of 8, then 9 of 9), query pruning (5 of 10). Running: MedCPT reranking
of the BM25 candidates on L and BioGen (`rerank/PREREGISTRATION-spark36.md`). Queued with
predictions written first: pseudo-relevance feedback on L, BioGen and R, plus BM25 at depth 1,000
on L (`prf/PREREGISTRATION-spark38.md`).

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
