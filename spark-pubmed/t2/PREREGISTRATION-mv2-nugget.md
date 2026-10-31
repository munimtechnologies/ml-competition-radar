# Pre-registration: MV2's extractive Task 2 answers against NLM's expert nuggets, at matched length (mv2-nugget-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Written 2026-10-31 (about 18:30 UTC), before this job ran and before `medaesqa-nugget-v2` (the
test of the nugget matcher itself, `PREREGISTRATION-medaesqa-nugget-v2.md`) has run. No nugget
text and no nugget score of any system has been seen.

## Question

MV2's NIH SPARK Task 2 composer (`t2dev-v1`: BM25 over the full SPARK corpus, then composer 0.2.0,
no reranker; `RESULTS-t2dev.md`) answers each BioGen 2024 question
with whole sentences from PubMed abstracts, about 250 words (11 sentences, median), about twice
the length of the longest TREC 2024 BioGen run. SPARK scores Task 2 by nugget F1, so what matters
is whether MV2's sentences carry the facts experts list, at a length a scorer would not penalise.
Using MedAESQA's expert nuggets (40 questions, CC0) and `medaesqa_nugget` 0.2.0's matcher
unchanged (word containment, bar 0.6), this job asks:

1. **As written:** cut to each run's own length, does MV2's answer cover more nuggets than that run?
2. **Ceiling:** if the best of MV2's own sentences were chosen (greedily, knowing the nuggets)
   within the same length, would it? This separates "the facts are not in MV2's sentences" from
   "they are there but not chosen or not first".

## Method (`mv2-nugget/mv2_nugget.py` 0.1.0, standard library only)

- Inputs: MV2's 65 `t2dev-v1` answers (local only; abstract text is never published), BioGen 2024
  topics and judged runs (NIST, sha256-pinned), MedAESQA (OSF, sha256-pinned), the official
  Table 3/4 numbers (published, sha256-pinned), `biogen_reuse.py` 0.1.0 (pinned) and
  `medaesqa_nugget.py` 0.2.0 (read at commit `5c2f2ca`).
- Each MV2 answer = its `responses` sentences in order (conflict and uncertainty notes are not
  included). Content words, scored sentences (3+ content words), nuggets (2+ content words), cover
  and recall at bar 0.6 are `medaesqa_nugget`'s, unchanged.
- **Cut:** the leading sentences whose content words add up to at most the budget; the first
  sentence is always kept (so MV2 can run slightly over a very short run's length; the mean
  shortfall is reported), and a budget of 0 keeps nothing.
- **Matched length (primary):** for each of the 30 runs and each of the 40 questions, MV2's answer is
  cut to that run's own content-word count on that question; MV2 "beats" the run if its mean nugget
  recall over the 40 questions is higher (ties are not wins).
- **Ceiling:** the same, but MV2's sentences are chosen greedily (most new nuggets covered first;
  ties: fewer words, then earlier) within the run's length.
- **Fixed budget (secondary):** every answer, runs and MV2, cut to 40 content words (20, 60 and the
  whole answer for sensitivity); MV2's rank among the 31 (1 = best; ties share the better rank).
- The yardstick checks of `medaesqa-nugget-v2` (expert-answer control, shuffled control, Kendall
  taus) are recomputed by the same code on the same data, as a cross-check.

## Checks (must hold for any prediction to count)

- C1: `fetch_public.py` exits 0 (two files at their sha256 pins; `medaesqa_nugget.py` at the commit
  declares 0.2.0).
- C2: `test_mv2_nugget` runs 7 tests, all pass.
- C3: `wait_public.py` exits 0 for this file (`match` recorded either way).
- C4: the run step exits 0 with `problem` null.
- C5: `mv2_answers` 65; `mv2_match` maps all 40 questions (`unmatched` 0); `mv2_answered` 40;
  `nugget_fields` `{"nuggets": 40}`.
- C6: if `medaesqa-nugget-v2` has run, its `control_expert_recall`, `control_shuffled_recall` and
  bar-0.6 `recall_vs_completeness_r` equal this job's `yardstick` values.
- K3 (MV2's own negative control): MV2's recall at 40 content words against the next question's
  nuggets (`mv2_shuffled_recall`) is at most 10.

## Predictions

- M1: as written, MV2 beats **fewer than 15** of the 30 runs at matched length. (About 70%: the
  runs are LLM answers written to the question; MV2's are abstract sentences.)
- M2: MV2's ceiling beats **at least 15** of the 30 runs at matched length. (About 60%.)
- M3: at the fixed 40-word budget MV2 ranks **16th or lower** of 31. (About 65%.)
- M4: whole answers, no cut: MV2 ranks **1st** of 31 (it has about twice the words). (About 40%.)
- R1: the run step takes at most 5 minutes.

## Decision rule

It applies only if the matcher is usable for equal-length comparisons: `medaesqa-nugget-v2`'s own
decision rule makes it "the development yardstick" or "equal-length only" (if v2 has not run when
this is graded, that rule is applied to this job's recomputed `yardstick` numbers), and K3 holds.
Otherwise the numbers are recorded and nothing is decided.

- **A**, MV2 as written beats at least 15 runs: the composer's sentence choice holds its own on
  recall; the next Task 2 work goes to precision and the conflict half of the score.
- **B**, it beats fewer than 15 but the ceiling beats at least 15: the facts are in MV2's sentences
  but not chosen or not first. Next: a sentence-selection stage that uses no nuggets, developed on
  the odd-numbered of these 40 questions and checked once on the even-numbered ones.
- **C**, the ceiling beats fewer than 15: selection cannot fix it; the facts are missing from MV2's
  candidate sentences. Next: the candidate pool (retrieval depth, more sentences per document) or
  abstractive rewriting, not selection.

## Limits, stated now

- MV2's composer was tuned on these 65 questions (judged precision, `spark36`), so it is not blind
  to them; the nuggets were not used.
- Word containment rewards shared terminology. If the experts wrote nuggets from the same abstracts
  MV2 quotes, verbatim sentences gain; paraphrasing runs lose. The ceiling inherits this.
- MV2 retrieves from the 2027 PubMed baseline files SPARK uses; the 2024 runs used the 2024
  baseline. Length is counted in content words, not words.
- 40 questions; 30 runs from 5 teams. The ceiling knows the nuggets and is a bound, not a system.
- No human has checked any count here.

Contact: MV2, Munim, Inc., mv2@munimtech.com
