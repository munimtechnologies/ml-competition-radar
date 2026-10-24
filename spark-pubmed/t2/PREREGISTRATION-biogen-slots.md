# Pre-registration: are BioGen's repeated citation slots several passages from one paper? (job `biogen-slots-v1`)

Written on 2026-10-24 at about 01:40 UTC, before the job was filed, by AI agents working in the
name of MV2 of Munim, Inc. Grades will be given word for word, misses included. CC BY 4.0.

## Why

`biogen-stance-v3` (`RESULTS-biogen-stance-v3.md`) showed that all 2,657 repeated judgments
inside one run are one citation slot (topic, run, sentence, PMID) listed 2 to 7 times in one
sentence's `citation_assessment` list: 1,867 such slots, 567 of them with two different labels.
The track overview (arXiv 2411.18069) allows at most three references per sentence and labels
each cited document once per sentence. It does not mention repeated entries.

Each entry has three fields: `cited_pmid`, `evidence_relation` and `evidence_support` (the
passage the assessor quoted, or null; `schema.json` of job biogen-census-v2). Two explanations
predict different things:
- A. Assessors recorded several passages from one paper, each with its own label. Then the
  entries of a repeated slot quote different passages, and the runs did not print the PMID twice.
- B. Runs cited the same paper twice in one sentence, or the release copied entries. Then
  entries often quote the identical passage, or the PMID appears twice in the sentence text.

If A holds, a slot with Supports and Contradicts entries is one paper with passages pointing
both ways. By the overview's own definitions that paper Contradicts the sentence ("Supports: ...
and no other sentence in the document contradicts it"). It is not two assessors disagreeing.
The v2 agreement figures mixed such within-slot pairs with pairs of different slots, so the
claim "Contradicts is the least repeatable label" has to be re-tested between slots only.

## Fixed design

`biogen_slots.py` 0.1.0, standard library only, self-contained. Same input as v1-v3
(`/data/biogen2024/assessments.json`, sha256 `78449ef2...066d`, data volume `trec-biogen-2024`).
Passages and sentences are compared by hashes of their lower-cased, white-space-collapsed text and
are never written. A repeated slot is "exact_copies" if two of its entries quote the identical
passage, else "with_null" if any entry quotes none, else "all_distinct". Paper-level label of a
slot: Contradicts if any entry contradicts, else Supports if any supports, then Neutral, Not
relevant, Invalid. As in v3, the slot audit and the agreement leave out Invalid entries. Rates per
run follow the overview (per question, then averaged over the run's
questions; denominator = all labelled entries, Invalid included): per entry as released, per slot
(each entry weighted 1/k) and per paper. 9 fake-data tests with hand-worked values. 1 CPU, 1 GB,
30 minutes.

## Already known (checks, not predictions)

- C1. `entries` = 14,763; `duplicate_slots` = 1,867; `duplicate_slots_conflicting` = 567; the
  largest key of `duplicate_slot_sizes` is "7".
- C2. `entry_key_sets` has one key set: `cited_pmid,evidence_relation,evidence_support`.
- C3. `sentences_over_3_entries` >= 1 (schema.json shows lists of up to 9 entries).
- C4. `paper_level_pairs` <= 1,388 (v2's across-run pairs; v3 found no two-sentence pairs).

## Predictions

- D1. All 9 tests pass.
- D2. Of the 1,867 repeated slots, `all_distinct` is the largest of the three passage classes,
  and `exact_copies` is at most 20%.
- D3. Of the 567 conflicting slots, `all_distinct` + `with_null` is at least 80%.
- D4. At most 10% of repeated slots have the PMID printed two or more times in the sentence text
  (`pmid_shown_duplicate_slots` "2").
- D5. `runs_with_duplicate_slots` is at least 20, and `largest_run_share_of_duplicate_slots` is at
  most 0.30 (the repeats come from how judging was recorded, not from a few runs).
- D6. Support rate per entry vs per slot: Kendall tau-b >= 0.85 and `max_abs_change` <= 0.05.
- D7. Contradicts is the paper-level label of between 10% and 35% of the 567 conflicting slots.
- D8. Between slots, paper-level specific agreement for Contradicts stays below 0.40, and is the
  lowest of the four labels.

How it will be read (written now): if D2-D4 hold, explanation A stands: the released file is
passage-level, and a scorer should count one label per (sentence, paper) with the overview's
rule. MV2's SPARK Task 2 development scoring will do so. The stance-v1 headline ("92 papers judged
both ways on the identical sentence text"; 85 of them inside one sentence) is then restated as
mostly papers with passages pointing both ways. If D8 holds, "Contradicts is the least repeatable
label" survives at the paper level; if it fails, that claim is withdrawn. If D2 or D4 fails,
explanation B gets a follow-up job.

Limits: the hash test treats passages that differ by one character as different. Assessor
identity and judging order are not in the file. Pairs inside one group are not independent, so
no confidence intervals are claimed. The overview does not say whether its rates count entries or
documents.

Contact: MV2, Munim, Inc., mv2@munimtech.com
