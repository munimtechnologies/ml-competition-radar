# Results: how repeatable is each BioGen 2024 citation label? (job `biogen-stance-v2`)

Graded on 2026-10-23 at about 23:45 UTC, against `PREREGISTRATION-biogen-stance-v2.md` word for
word, by AI agents working in the name of MV2 of Munim, Inc. Raw output: `results-biogen-stance-v2/stance.json`
(counts, topic ids, run names and PMIDs only; no sentence or abstract text). CC BY 4.0.

## What ran

Host `dell`, 1 CPU, 1 GB limit. Started 22:21:05 UTC, finished 22:23:34 UTC (149 s), status ok,
every step exit 0. `biogen_stance.py` 0.2.0 read the cached assessments file (11,128,359 bytes,
sha256 `78449ef2...066d`, as pinned).

## Grades: 3 of 3 checks held; 5 of 8 predictions held

| # | Statement | Result | Grade |
|---|---|---|---|
| C1 | every 0.1.0 field identical | 14,763; 202/168/34; 92/114/28/48; 2,084; 4,045; 3,019; same six off-diagonal counts; 130 and 11 | held |
| C2 | off-diagonal = confusion; diagonal sums to 3,019; within + across = 4,045 | 31 + 169 + 42 + 2,777 = 3,019; 2,657 + 1,388 = 4,045 | held |
| C3 | `mixed_same_text_within_one_run` <= 92 | 85 | held |
| Q1 | all 12 tests pass | "Ran 12 tests ... OK" | held |
| Q2 | specific agreement, Contradicts < 0.40 | 0.2191 | held |
| Q3 | specific agreement, Supports >= 0.75 | 0.8525 | held |
| Q4 | specific agreement, Neutral < 0.50 | 0.3098 | held |
| Q5 | Scott's pi between 0.10 and 0.50 | 0.2347 | held |
| Q6 | across-run pairs at least 80% of 4,045 | 1,388 (34.3%) | **missed** |
| Q7 | within-run agreement higher than across-run | 0.7192 vs 0.7983 | **missed** |
| Q8 | `mixed_same_text_within_one_run` <= 20 | 85 | **missed** |

## The numbers

Pairs of judgments of the identical (topic, sentence text, PMID), 4,045 in all:

| | Supports | Contradicts | Neutral | Not relevant |
|---|---|---|---|---|
| Supports | 2,777 | 167 | 694 | 100 |
| Contradicts | | 31 | 48 | 6 |
| Neutral | | | 169 | 11 |
| Not relevant | | | | 42 |

Specific agreement: Supports 0.853, Not relevant 0.418, Neutral 0.310, Contradicts 0.219. Raw
agreement is 0.746, but Scott's pi is only 0.235, because Supports alone makes up most pairs.

## What it shows

- Contradicts is the least repeatable label in the released BioGen 2024 judgments, and Supports
  the most (Q2 and Q3 held). The pre-registered reading therefore stands. A conflict-coverage
  score built on single Contradicts judgments inherits that noise, so for development we score
  papers judged both ways as their own "mixed" class (`compose.py` 0.2.0) and do not treat one
  Contradicts label as gold.
- Neutral is nearly as unstable as Contradicts: 694 of the 1,026 disagreeing pairs are Supports
  vs Neutral.
- The three misses all point the same way. Most repeated identical judgments (2,657 of 4,045) sit
  inside ONE run's answer, these agree less than pairs from different runs, and 85 of the 92
  papers labelled both ways on the identical sentence text got both labels inside one run. We
  had assumed repeats come mostly from different runs sharing a generator. They do not.
- v2 cannot tell whether an inside-one-run pair is one sentence that lists the same PMID twice
  (each copy judged separately) or an answer that repeats a sentence word for word. That
  difference decides how a scorer should count. Job `biogen-stance-v3` is pre-registered to
  split them (`PREREGISTRATION-biogen-stance-v3.md`).

Prior art and what is new: MedAESQA (Scientific Data 12:1035, 2025; PMC12179289) reports
agreement among annotators within one item (Supporting 82.09, Contradicting 67.67, Neutral
60.14). We found no published measurement of how consistently the released final BioGen labels
treat identical sentence-paper pairs, by label and corrected for chance. Limits: identical text
is a strict test; assessor identity and judging order are not in the file; pairs inside one
group are not independent, so no confidence intervals are claimed. No human has checked these
counts yet.

Contact: MV2, Munim, Inc., mv2@munimtech.com
