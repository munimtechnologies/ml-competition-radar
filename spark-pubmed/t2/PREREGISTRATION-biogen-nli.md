# Pre-registration: biogen-nli-v1 (does an off-the-shelf NLI model recover BioGen's passage labels?)

MV2 of Munim, Inc. (made with AI agents working in his name). CC BY 4.0. Written 2026-10-28
between 20:40 and 21:20 UTC, before the job was filed and before any of its output existed. The
job's workdir carries a copy of this file, so the copy is on disk when the job starts, whether or
not this public commit has landed by then.

## Why

SPARK Task 2 is scored partly on conflict/controversy coverage. In t2dev-v1, compose.py 0.2.0's
negation-cue conflict flag fired on no answer, although 10 answers cited a paper the BioGen
assessors judged contradicting (`RESULTS-t2dev.md`). Before building a model-based flag, this job
measures how well a general NLI model separates the assessors' labels when it sees exactly what
they judged: the quoted passage of the cited paper (`evidence_support`, as premise) and the answer
sentence (`answer_sentence`, as hypothesis). biogen-slots-v1 showed the released labels are
passage-level, so this is a like-for-like test.

Prior art (searched 2026-10-28): the TREC 2025 BioGen overview says its organizers' baseline used
SciFive, a MedNLI-trained NLI model, to label document-sentence pairs, and teams used MNLI models
and LLM prompting for contradicting citations; its 2025 judgments are not public (the TREC 2025
BioGen data page lists no qrels). We found no published measure of an NLI model against the
2024 assessors' passage-level labels. This is a development measurement for MV2's system, not a
new method.

## What runs

`nli_check.py` 0.1.0 (in this folder), job `biogen-nli-v1`, CPU only, 2 CPUs, 2.5 GB limit:

1. `python -m unittest -v test_nli_check` (7 tests, fake data, no torch).
2. `fetch-model`: cross-encoder/nli-deberta-v3-base (Apache-2.0) at revision
   6c749ce3425cd33b46d187e45b92bbf96ee12ec7, 7 files, saved under /data/models/; bytes and sha256
   of each file recorded in model.json.
3. `run`: reads /data/biogen2024/assessments.json (downloaded from NIST only if missing; stops
   unless sha256 = 78449ef2...066d, the value every earlier BioGen job pinned). Scores each
   distinct (passage, sentence) pair once, max 256 tokens, fp32, batch 16, 2 threads.

Levels: entry (one judgment), slot (topic, run, sentence, PMID; Contradicts if any entry is, the
overview's rule; score = max p(contradiction)) and topic-paper. Per level: AUROC and average
precision of p(contradiction) for Contradicts, the argmax prediction's precision/recall/F1, and
the best F1 over thresholds (an oracle chosen on the same data, so optimistic). Also p(entailment)
for Supports, Contradicts against Supports only, and the gold-by-argmax confusion matrix. Outputs
are counts and scores only, never text.

## Checks (if one fails, the predictions are not graded until the cause is known)

- K1: sha256 matches; `judgments` = 14,763 and `unknown_label` = 0; label shares within 0.1
  points of biogen-census-v2's 69.4% supports, 1.9% contradicts, 4.3% invalid.
- K2: `census` gives 202 topic-papers with a Contradicts judgment, 168 of them also Supports.
- K3: model.json lists all 7 files with nonzero bytes, and the id2label check passes (the run
  step does not stop with "unexpected id2label").

## Predictions

- N1: all 7 tests pass; every step exits 0.
- N2: at least 95% of Supports judgments and at least 95% of Contradicts judgments are scored
  (valid PMID, nonempty passage and sentence). Other labels are recorded only.
- N3: `truncated` is at most 5% of unique pairs.
- N4: entry level, Contradicts vs rest: AUROC of p(contradiction) between 0.60 and 0.85.
- N5: entry level, Supports vs rest: AUROC of p(entailment) between 0.60 and 0.85.
- N6: entry level, argmax contradiction: precision at most 0.30, recall between 0.10 and 0.70.
- N7: entry level, oracle best F1 for Contradicts below 0.3881, the assessors' own between-slot
  specific agreement for Contradicts (biogen-slots-v1). (A model scored against one assessor
  rarely beats two assessors' agreement with each other.)
- N8: Contradicts vs Supports only has a higher AUROC than Contradicts vs rest (entry level).
- N9: `ms_per_pair` between 20 and 400; the whole job at most 120 min; peak memory at most 2.5 GB.

Slot and topic-paper numbers are recorded, not predicted.

## Decision rule (fixed now)

- If N4's AUROC is at least 0.75 and the slot-level argmax F1 is at least 0.20: the next step
  builds compose.py 0.3.0's conflict flag on this model (each chosen sentence against the other
  cited articles' sentences), with its threshold fixed from this run's slot-level oracle, and tests
  it on t2dev's conflict cases, pre-registered first.
- Otherwise this model is not used. The next candidate is a biomedical NLI model (SciFive MedNLI,
  the 2025 organizers' baseline) or an open-weight LLM judge, pre-registered separately.

## Limits

- The assessors' chosen passages make this optimistic: a real system must find the passage
  itself in the abstract.
- Contradicts is rare (about 1.9% of judgments) and the least repeatable label (specific
  agreement 0.39 between slots), so the labels themselves cap any score.
- BioGen 2024 questions and answers differ from SPARK's; T2QS is still undefined.
- NIST states no licence for the assessments, so only counts and scores are published.
- No human has checked any of this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
