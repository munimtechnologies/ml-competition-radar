# Pre-registration: are BioGen's within-run disagreements one citation judged twice? (job `biogen-stance-v3`)

Written on 2026-10-23 at about 23:55 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why

`biogen-stance-v2` (`RESULTS-biogen-stance-v2.md`) missed three of its own predictions in the
same direction. 2,657 of the 4,045 repeated identical sentence-paper judgments sit inside one
run's answer (predicted: at most 20% of them). Their agreement, 0.7192, is lower than across
runs, 0.7983 (predicted: higher). And 85 of the 92 papers judged both Supports and Contradicts on
the identical sentence text carry both labels inside one run (predicted: at most 20).

A run's answer repeating one sentence word for word is one way to get there. A second way is a
single sentence that lists the same PMID twice in its citations, with each copy judged
separately. v2 cannot tell these apart. `biogen_stance.py` 0.3.0 splits within-run pairs into
"one sentence" (same run, same sentence position) and "two sentences" (same run, different
positions). It counts citation slots (topic, run, sentence position, PMID) judged more than once,
and how many of those carry two different labels. It also counts mixed papers with both labels
inside one sentence.

## Fixed design

Standard library only. Every 0.2.0 output is unchanged and the new fields are added. Same input
(`/data/biogen2024/assessments.json`, sha256 `78449ef2...066d`, on the `trec-biogen-2024` data
volume of both hosts). 13 fake-data tests: the 12 earlier ones, some extended with hand-computed
values for the new fields, plus a duplicate-slot fixture. 1 CPU, 1 GB, 30 minutes.

## Already known (checks, not predictions)

- C1. Every field printed by 0.2.0 is identical to v2's output.
- C2. One-sentence pairs + two-sentences pairs = 2,657, and their agreeing pairs sum to 1,911.
- C3. `mixed_one_sentence` <= 114 (`mixed_same_run`).

## Predictions

- R1. All 13 tests pass.
- R2. One-sentence pairs are at least half of the 2,657 within-run pairs.
- R3. One-sentence agreement is lower than across-run agreement (0.7983).
- R4. `mixed_one_sentence` is at least 60.
- R5. `duplicate_citation_slots` is at least 1,000, and between 15% and 45% of them carry two
  different labels.
- R6. `duplicate_citation_slots_max_judgments` is at least 3.

How it will be read (written now): if R2 and R4 hold, most of the "one claim judged two ways"
pattern is one citation slot judged twice. Anyone scoring against these labels should then count
each (sentence, PMID) slot once, and we will do so for T2 development scoring. A slot judged
twice with two labels is still a disagreement on one item, so the v1/v2 conclusion that
Contradicts is the least repeatable label would stand. If R2 fails, the within-run repeats come
mainly from answers repeating a sentence.

Limits: sentence position is the index in the released file's sentence list. Assessor identity
and judging order are not in the file. Pairs inside one group are not independent, so no
confidence intervals are claimed.

Contact: MV2, Munim, Inc., mv2@munimtech.com
