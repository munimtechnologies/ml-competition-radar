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
every PubMed citation from 30 runs judged by assessors. The file's own labels are "supporting",
"contradicting", "neutral", "not relevant" and "invalid citation", and every answer sentence is
judged Required, Unnecessary, Borderline or Inappropriate. The 2025 track recommends these
assessments for development (https://trec-biogen.github.io/docs/). Its answers are at most 250
words, with at most 3 PMIDs per sentence and 30 per answer.

`biogen_census.py` downloads the topics and assessments, hashes them, and writes counts and
PMIDs only, never text: label totals, per-topic contradiction counts, per-run label shares, and
the PMIDs judged under each label per topic (`gold_t2.jsonl`). The data is used to develop and
evaluate only. Nothing from it goes into a submitted system. NIST states no licence for it, so
the judged-PMID file is not republished here until that is clear.

Every job was pre-registered before it ran and graded word for word:

| job | pre-registration | results | outcome |
|---|---|---|---|
| biogen-census-v1 | `PREREGISTRATION-biogen.md` | `RESULTS-biogen.md`, `results-biogen/` | 5 of 10; all misses one label-word defect in 0.1.0 |
| biogen-census-v2 | `PREREGISTRATION-biogen-v2.md` | `RESULTS-biogen-v2.md`, `results-biogen-v2/` | 9 of 10 |
| biogen-stance-v1 | `PREREGISTRATION-biogen-stance.md` | `RESULTS-biogen-stance.md`, `results-biogen-stance/` | 3 of 3 checks, 8 of 9 |
| biogen-stance-v2 | `PREREGISTRATION-biogen-stance-v2.md` | `RESULTS-biogen-stance-v2.md`, `results-biogen-stance-v2/` | 3 of 3 checks, 5 of 8 |
| biogen-stance-v3 | `PREREGISTRATION-biogen-stance-v3.md` | `RESULTS-biogen-stance-v3.md`, `results-biogen-stance-v3/` | 3 of 3 checks, 6 of 6 |
| biogen-slots-v1 | `PREREGISTRATION-biogen-slots.md` | pending | queued |

What v2 counted: 14,763 citation judgments (69.4% supporting, 1.9% contradicting, 4.3% invalid);
55 of 65 topics have a contradicting judgment; 3,858 distinct PMIDs, all inside the SPARK
corpus's PMID range. Of the 202 papers judged contradicting an answer sentence, 168 (83%) are
also judged supporting another sentence in the same topic, and none is judged contradicting in
two topics.

What stance-v1 found: for 92 of those 168 papers (55%), the identical sentence text citing the
paper was judged both Supports and Contradicts. Only 28 were different sentences in one run's
answer, and 48 were only different runs' different sentences.

What stance-v2 added: over the 4,045 pairs of judgments of an identical (topic, sentence, PMID),
specific agreement is 0.85 for Supports but 0.22 for Contradicts (Neutral 0.31, Not relevant
0.42), and Scott's pi is 0.23. Most of those pairs (2,657) sit inside one run's answer.

What stance-v3 settled: **all 2,657 inside-one-run pairs are one PMID listed 2 to 7 times in one
sentence's citation list** (1,867 such slots; 567 of them, 30.4%, with different labels), and
all 85 inside-one-run both-ways papers are of this kind. The overview allows at most 3 references
per sentence, and each entry carries its own quoted evidence passage. So a repeated slot may be
several passages from one paper, each labelled separately. If it is, a Supports + Contradicts
slot is one paper with passages pointing both ways, and the stance-v1/v2 figures above are partly
passage-level. `biogen-slots-v1` tests this and re-measures agreement between slots only. Until it
is graded, do not read 0.22 as assessor disagreement about one paper.

MedAESQA (Scientific Data 2025, PMC12179289), which releases 40 of these questions, already
reports lower annotator agreement within one item for Contradicting (67.67) than for Supporting
(82.09). No human has checked our counts yet.

## Baseline: `compose.py` 0.2.0 (extractive, cited, standard library only)

It writes no new prose. Every answer sentence is copied from a cited abstract, so every claim
is grounded by construction, and an answer takes milliseconds on a CPU. Steps: split the
abstracts of the top Task 1 candidates into sentences. Score each sentence by BM25 against the
question, plus a prior for the article's rank. Choose sentences by MMR up to 250 words, at most
2 per article; a near-copy of a chosen sentence becomes an extra citation instead of a repeat.
Flag a conflict when two chosen sentences from different articles share content words but one
reports a finding and the other reports none (negation cues). Flag uncertainty when a sentence
says the evidence is mixed or unclear.

`score` puts every cited PMID into exactly one class against the BioGen judgments: supports,
**mixed** (judged both Supports and Contradicts in the topic), contradicts (only), other (only
Neutral / Not Relevant), or unjudged. It reports each class's share of the citations, the recall
of all Supports papers and of Supports-only papers, how many mixed and contradicts-only papers an
answer cites, and how many of them its conflict flags hit. 0.1.0 counted a mixed paper as both
supporting and contradicting. That double-counted 168 of the 202 contradicting papers.

Pooled judgments only cover what 2024 runs cited, so an unjudged PMID is unknown, not wrong.
A BioGen 2025 paper reports that contradicting evidence is rarer and often expressed through
negation, hedging or population-specific conditions (arXiv 2603.17580). Negation cues alone will
miss many conflicts. This baseline is the floor that a later open-weight rewriting stage must
beat.

## Next

1. Grade `biogen-slots-v1`.
2. The whole-corpus index is complete (`corpus_build/RESULTS-spark34.md`). The first
   whole-corpus Task 1 scoring job is re-filed as `spark35-score-v2`. After it: run t1.py BM25
   (then MedCPT rerank) on the 65 BioGen questions, run `compose`, and run `score`, with
   predictions written first.

Contact: MV2, Munim, Inc., mv2@munimtech.com
