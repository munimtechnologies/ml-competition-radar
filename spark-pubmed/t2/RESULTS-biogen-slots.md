# Results: are BioGen's repeated citation slots several passages from one paper? (job `biogen-slots-v1`)

Graded on 2026-10-24 (UTC), against `PREREGISTRATION-biogen-slots.md` word for word, by AI agents
working in the name of MV2 of Munim, Inc. Raw output: `results-biogen-slots/slots.json` (counts
and run names only; no sentence, passage or abstract text). CC BY 4.0.

## What ran

Host `blade`, 1 CPU, 1 GB limit. Started 01:16:35 UTC, finished 01:19:10 UTC (155 s), status ok,
every step exit 0. `biogen_slots.py` 0.1.0 read the cached assessments file (11,128,359 bytes,
sha256 `78449ef2...066d`, as pinned).

**Timing, stated plainly.** The pre-registration was written in the job's own folder before the
job was filed, by the same run. Its text says "about 01:40 UTC". That time is wrong: the job
started at 01:16:35 UTC. The public commit of the pre-registration (`e412c059`, 01:19:56 UTC)
came 46 seconds after the job finished. So the public record alone does not prove the predictions
came first. The agents that wrote them did not see any output before filing, but no outside
record shows that.

## Grades: 4 of 4 checks held; 8 of 8 predictions held

| # | Statement | Result | Grade |
|---|---|---|---|
| C1 | entries 14,763; repeated slots 1,867; conflicting 567; largest slot size "7" | 14,763; 1,867; 567; "7" | held |
| C2 | one entry key set | `cited_pmid,evidence_relation,evidence_support` (14,763) | held |
| C3 | `sentences_over_3_entries` >= 1 | 894 | held |
| C4 | `paper_level_pairs` <= 1,388 | 802 | held |
| D1 | all 9 tests pass | "Ran 9 tests ... OK" | held |
| D2 | `all_distinct` largest class; `exact_copies` <= 20% | 1,852 of 1,867 (99.2%); 14 (0.75%) | held |
| D3 | conflicting slots: `all_distinct` + `with_null` >= 80% | 567 + 0 of 567 (100%) | held |
| D4 | PMID printed twice in <= 10% of repeated slots | 4 of 1,867 (0.21%) | held |
| D5 | >= 20 runs with repeated slots; largest run share <= 0.30 | 28 runs; 0.0991 | held |
| D6 | support rate per entry vs per slot: tau-b >= 0.85, max change <= 0.05 | 0.9577; 0.0229 | held |
| D7 | Contradicts is the paper-level label of 10-35% of conflicting slots | 113 of 567 (19.9%) | held |
| D8 | between slots, Contradicts specific agreement < 0.40 and the lowest | 0.3881; lowest of four | held |

## What it shows

As pre-registered, D2-D4 holding means explanation A stands: **the released TREC 2024 BioGen
assessments are passage-level.** When a (topic, run, sentence, PMID) slot is listed 2 to 7 times,
the entries quote different passages of the paper (99.2% of repeated slots), and runs almost never
printed the PMID twice (0.21%). Every one of the 567 slots with two different labels has a
different passage behind each label. The 14 slots that do repeat a passage word for word always
repeat the label too.

So a slot with Supports and Contradicts entries is one paper with passages pointing both ways. By
the track overview's own rule ("no other sentence in the document contradicts the statement") that
paper Contradicts the sentence. The overview (arXiv 2411.18069) labels "each cited document" once
per sentence and does not mention multiple passages or repeated entries.

Restated earlier findings:
- stance-v1's "92 papers judged both Supports and Contradicts on the identical sentence text"
  (85 of them inside one sentence's citation list) is mostly **papers with passages pointing both
  ways**, not two assessors disagreeing.
- stance-v2's agreement figures mixed passage pairs with pairs of different slots. Between slots
  only, at the paper level (802 pairs of the same topic, sentence text and PMID in different
  runs): raw agreement 0.8229, Scott's pi 0.4663 (v2: 0.2347). Specific agreement: Supports
  0.8997 (v2 0.8525), Neutral 0.7077 (0.3098), Not relevant 0.4659 (0.4179), **Contradicts
  0.3881 (0.2191)**. D8 held, so "Contradicts is the least repeatable label" survives at the
  paper level: of 54 pairs where either side is Contradicts, 13 agree and 33 pair it with
  Supports.

What this means for scoring: count one label per (sentence, paper) with the overview's rule. Per
run, re-scoring this way moves the citation support rate by at most 0.029 and the contradict rate
by at most 0.036 (the largest, `webis-3`, goes from 0.034 to 0.070), and changes the order of
12-15 of 28 runs on each measure (tau-b 0.92-0.96). MV2's SPARK Task 2 development scoring will
count papers, not entries.

## After grading (post hoc, not pre-registered)

- 454 of the 567 conflicting slots (80%) are Neutral + Supports, which the overview's rule makes
  Supports. 113 involve Contradicts: 84 Contradicts + Supports, 22 Contradicts + Neutral, 7 all
  three.
- 894 of 6,227 cited sentences carry more than 3 entries, but only 51 cite more than 3 distinct
  PMIDs, so almost every apparent breach of the 3-reference limit is extra passages, not extra
  papers.

Limits: the hash test treats passages that differ by one character as different. Assessor
identity and judging order are not in the file, so we cannot say whether one or several
assessors judged a slot. Pairs inside one group are not independent, so no confidence intervals
are claimed. The overview does not say whether its published rates count entries or documents. No
human has checked these counts yet.

Contact: MV2, Munim, Inc., mv2@munimtech.com
