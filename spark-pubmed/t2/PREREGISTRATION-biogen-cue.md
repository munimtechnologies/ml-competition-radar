# Pre-registration: biogen-cue-v1 (do negation cues mark the passages BioGen assessors judged Contradicts?)

MV2 of Munim, Inc. (made with AI agents working in his name). CC BY 4.0. Written 2026-10-29
between 00:45 and 01:15 UTC, before the job was filed and before any of its output existed. The
job's workdir carries a copy of this file, so the copy is on disk when the job starts, whether or
not this public commit has landed by then.

## Why

SPARK Task 2 is scored partly on conflict/controversy coverage. compose.py 0.2.0 flags a conflict
with negation and null-finding cues, and in t2dev-v1 that flag fired on no answer, although 10
answers cited a paper the assessors judged contradicting (`RESULTS-t2dev.md`). In TREC 2025
BioGen Task A, the GE HealthCare system (arXiv 2603.17580) kept only abstract sentences with
explicit negation cues (23 NegEx-derived patterns, not listed in the paper) before its MedNLI
step. That premise was tuned on SciFact, not on BioGen labels.

Prior art (searched 2026-10-29): the 2025 overview (arXiv 2603.21582) reports that systems
"struggle to identify contradictory citations". In its LLM-judged evaluation the best Contradicts
F1 is 15.67 (InfoLab task_a_run2) and the SciFive MedNLI baseline's is 4.67. In its expert
evaluation (10 topics) the baseline was the strongest on contradictions, at precision 8.33 and
recall 10. MedAESQA (Scientific Data 2025) reports lower annotator agreement for Contradicting
than for Supporting. We found no published count of how often negation cues appear in the
passages BioGen's assessors judged contradicting. This is a development measurement for MV2's
system, not a new method.

## What runs

`cue_check.py` 0.1.0 (in this folder), job `biogen-cue-v1`, standard library only, 1 CPU, 1 GB:

1. `python -m unittest -v test_cue_check` (6 tests, hand-made records).
2. `python cue_check.py --data-dir /data/biogen2024 --out-dir /out`: reads the 2024 assessments
   (downloaded from NIST only if missing; stops unless sha256 = 78449ef2...066d, the value every
   earlier BioGen job pinned) and keeps the judgments with a valid PMID, a nonempty passage and a
   nonempty answer sentence (the same set nli_check.py scores).

Cues, all compose.py 0.2.0's own regular expressions copied verbatim, applied to the whole
quoted passage (`evidence_support`) and the answer sentence:

- `neg_passage`: NEG_RX in the passage (no, not, did not, failed to, without, lack of, similar, ...).
- `null_passage`: NULL_RX in the passage (no significant difference, not associated, no evidence, ...).
- `hedge_passage`: HEDGE_RX in the passage (conflicting, remains unclear, limited evidence, ...).
- `neg_sentence`: NEG_RX in the answer sentence.
- `neg_mismatch`: NEG_RX in exactly one of the two.
- `polarity_clash`: compose.py's conflict rule on the pair (one side "null", the other "finding").

Per cue: fires and rate per label, the ratio of its rate among Contradicts to its rate among
Supports, and precision / recall / F1 / lift as a Contradicts flag at entry level (vs rest and vs
Supports only) and per citation slot (Contradicts if any entry is). Counts and rates only.

## Checks (if one fails, the predictions are not graded until the cause is known)

- K1: sha256 matches; `judgments` = 14,763 and `unknown_label` = 0; `scored` equals what
  biogen-nli-v1 scores if that job has finished (otherwise recorded only).
- K2: `census` gives 202 topic-papers with a Contradicts judgment, 168 of them also Supports.

## Predictions

- C1: all 6 tests pass; every step exits 0; the run step takes at most 10 minutes; peak memory
  at most 1 GB.
- C2 (the 2025 premise): `neg_passage` fires more often among Contradicts than among Supports
  (`ratio_c_to_s` above 1.0).
- C3: `neg_passage`'s `ratio_c_to_s` is between 1.2 and 3.0.
- C4: `neg_passage` fires on between 35% and 80% of Contradicts judgments.
- C5: `null_passage`'s `ratio_c_to_s` is at least 2.0.
- C6: no cue reaches entry-level Contradicts-vs-rest F1 of 0.15 or precision of 0.15.
- C7: `polarity_clash` has entry-level Contradicts-vs-rest recall at most 0.30.
- C8: `neg_mismatch` fires on at least 20% of Supports judgments.
- C9: `hedge_passage` fires on at most 5% of Supports judgments.

Slot-level numbers and the Contradicts-vs-Supports blocks are recorded, not predicted.

## Decision rule (fixed now)

- Gate: if `neg_passage` fires on at least 60% of Contradicts judgments and its `ratio_c_to_s`
  is at least 1.5, the next model-based conflict-flag job (whatever model biogen-nli-v1's rule
  picks) also reports its scores inside the `neg_passage` gate, pre-registered. Otherwise no
  negation gate is used: it would drop more than 40% of the contradictions, or would barely thin
  the Supports.
- compose.py's cue flag: if `polarity_clash` has slot-level precision of at least 0.10, compose.py
  0.3.0 keeps it as a cheap flag beside the model-based one. Otherwise 0.3.0 removes it.

## Limits

- The assessors' quoted passages make this optimistic: a real system must find the passage
  itself in the abstract.
- The cues are compose.py's, not the unpublished NegEx list of arXiv 2603.17580, so this tests
  MV2's flag and the premise in general, not that system exactly.
- Contradicts is rare (about 1.9% of judgments) and the least repeatable label (specific agreement
  0.39 between slots, biogen-slots-v1).
- BioGen 2024 questions and answers differ from SPARK's; T2QS is still undefined.
- NIST states no licence for the assessments, so only counts and rates are published.
- No human has checked any of this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
