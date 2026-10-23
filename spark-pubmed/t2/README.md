# t2: groundwork for SPARK Task 2 (open-ended biomedical questions)

MV2 of Munim, Inc. (made with AI agents working in his name). Code Apache-2.0; notes CC BY 4.0.

## The task, as published (challenge page /challenges/199, read 2026-10-23)

- About 1,000 natural-language questions, released "shortly before the end of the challenge
  period" (the challenge runs 2027-01-15 to 2027-02-01). Prize $100,000 + $25,000.
- Responses must be "concise, objective, evidence-grounded responses with valid citations and
  relevant passages", scored on Grounded Nugget F1 and Conflict/Controversy Coverage. "T2QS"
  decides the ranking but is not defined yet. Ease of use, compute time, compute effort and
  memory in NIH's cloud are the tie-breakers.
- No output format, length limit or sample files are published yet ("Challenge Materials" is
  empty).

## Development data: TREC 2024 BioGen

No SPARK Task 2 questions are public. The closest public data we found is NIST's TREC 2024
BioGen track (overview: https://arxiv.org/abs/2411.18069). It has 65 health questions with
every PubMed citation from 30 runs judged Supports, Contradicts, Neutral or Not Relevant, and
every answer sentence judged Required, Unnecessary, Borderline or Inappropriate. The 2025 track
recommends these assessments for development (https://trec-biogen.github.io/docs/). Its
answers are at most 250 words, with at most 3 PMIDs per sentence and 30 per answer.

`biogen_census.py` downloads the topics and assessments, hashes them, and writes counts and
PMIDs only, never text. It produces label totals, per-topic contradiction counts, and the PMIDs
judged under each label per topic (`gold_t2.jsonl`). Its predictions were written before
anyone opened the file (`PREREGISTRATION-biogen.md`). The data is used to develop and evaluate
only. Nothing from it goes into a submitted system. NIST states no licence for it, so the
judged-PMID file is not republished here until that is clear.

## Baseline: `compose.py` 0.1.0 (extractive, cited, standard library only)

It writes no new prose. Every answer sentence is copied from a cited abstract, so every claim
is grounded by construction, and an answer takes milliseconds on a CPU. Steps: split the
abstracts of the top Task 1 candidates into sentences. Score each sentence by BM25 against the
question, plus a prior for the article's rank. Choose sentences by MMR up to 250 words, at most
2 per article; a near-copy of a chosen sentence becomes an extra citation instead of a repeat.
Flag a conflict when two chosen sentences from different articles share content words but one
reports a finding and the other reports none (negation cues). Flag uncertainty when a sentence
says the evidence is mixed or unclear. `score` measures citations against the BioGen
judgments: the share of citations judged Supports, Contradicts or unjudged, and the recall of
judged Supports PMIDs.

Pooled judgments only cover what 2024 runs cited, so an unjudged PMID is unknown, not wrong.
A BioGen 2025 paper reports that contradicting evidence is rarer and often expressed through
negation, hedging or population-specific conditions (arXiv 2603.17580). Negation cues alone will
miss many conflicts. This baseline is the floor that a later open-weight rewriting stage must
beat.

## Next

1. Grade `biogen-census-v1` against its predictions.
2. Once the whole-corpus index is complete: run t1.py BM25 (then MedCPT rerank) on the 65
   BioGen questions, run `compose`, and run `score`, with predictions written first.

Contact: MV2, Munim, Inc., mv2@munimtech.com
