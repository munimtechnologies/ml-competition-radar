# SPARK Task 1 dev sets: pre-registration (2026-10-22, about 14:50 UTC)

MV2 of Munim, Inc. Written by AI agents working in his name before `dev_sets.py` ran
anywhere and before any landmark was looked up. Text CC BY 4.0, code Apache-2.0.

## Why

SPARK Task 1 (NIH/NLM, Known-Item & Provenance Retrieval) scores up to five ranked PMIDs/PMCIDs
per question by MRR. No questions have been published, and a search on 2026-10-22 found no
public known-item benchmark over PubMed. So MV2 builds two proxy dev sets to tune against:

- **L (landmarks):** 47 well-known first reports since 1959 (`landmarks.json`), each with a
  question written in plain words. Titles, years, journals and first authors were recalled,
  not looked up, and are only hints: an item counts only if PubMed's own summary has a title
  within difflib ratio 0.85 (lower-cased, alphanumeric words) and a year within one of the
  hint. Searches run in order: title words + year, first author + year + journal, title words
  alone. Four pre-1959 controls (C01-C04) test the corpus window. Four items (L24, L38,
  L40, L43) are marked `contested` (shared priority) and are left out of the headline score.
- **R (random records):** a fixed-seed reservoir sample of 15 eligible records from each of six
  evenly spaced SPARK corpus files (pubmed27n0001, 0262, 0523, 0784, 1045, 1306; seed
  20261022, per-file seed string "20261022-<file name>"). Eligible means: a title, an abstract
  of at least 80 words, journal year 1959-2026, and none of these publication types: Editorial,
  Comment, Letter, News, Historical Article, Published Erratum, Retraction of Publication,
  Retracted Publication, Biography, Obituary, Portrait, Interview, Preprint.

## Predictions graded from this job (spark29-dev-v1)

- A1. At least 44 of the 47 landmarks verify by some strategy.
- A2. At least 38 of the 47 verify by the first strategy (title words + year).
- A3. At least 90% of verified landmarks have the exact hinted year (year_diff 0).
- A4. Between 8 and 18 of the 47 verified landmarks carry a PMC id.
- A5. No verified landmark carries an excluded publication type (list above).
- A6. Controls: C01 (1953), C02 (1951) and C03 (1944) verify and fall outside the window;
  C04 (Kaplan and Meier 1958, a statistics journal) is not found.
- A7. No landmark ends with status `error`.
- R1. All six corpus files download and match NLM's md5.
- R2. pubmed27n0001's eligible share is under 0.25.
- R3. Pooled over the other five files, the eligible share is between 0.45 and 0.80.
- R4. The pool holds exactly 90 records with 90 distinct PMIDs.

## Predictions graded only once the whole-corpus index exists (not before)

Index = `spark28/build_index.py` over all 1,306 files, BM25 via its `search()` (title x2,
abstract x1, MeSH x0.5). Headline L = verified, in window, not contested, no excluded type.

- B1. Using each R record's own title as the query, the record ranks first for at least 90% of R.
- B2. On headline L, BM25 MRR@5 is between 0.15 and 0.50.
- B3. BM25 puts the target in its top 5 for fewer than 70% of headline L questions.
- B4. On R questions (protocol below), BM25 MRR@5 is between 0.20 and 0.60.

## R question protocol (fixed now, applied in a later run)

One question per pooled record, written by AI agents from the abstract alone (never the
title), asking for "the study that ..." in a researcher's words. No run of three or more
consecutive title words may appear in the question. Questions are frozen and published before
any retrieval is scored on them.

## Limits stated in advance

AI-written questions are not NLM's expert questions. Recalled landmark lists lean towards
famous molecular biology. A landmark can verify in PubMed and still be missing from the SPARK
snapshot; that is checked against the index's `meta` table when the index exists. MRR falls as
the corpus grows, so all B grades use the full corpus.
