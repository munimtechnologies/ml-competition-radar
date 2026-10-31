# Pre-registration: BioGen 2024 runs against NLM's expert nuggets, read from the right field (medaesqa-nugget-v2)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Written 2026-10-31 (about 12:50 UTC), before this job ran. The job first fetches the published
`biogen_reuse.py` and `official_biogen2024.json` and checks them against the sha256 values
`medaesqa-nugget-v1` recorded, then waits until this file is public on GitHub.

## Why there is a v2

`medaesqa-nugget-v1` (`PREREGISTRATION-medaesqa-nugget.md`, `RESULTS-medaesqa-nugget.md`) read the
experts' nuggets from `expert_curated_nuggets`, the name in MedAESQA's README, and found none. Its
results said that value "reads as empty (None)" in all 40 items. **That was wrong.**
`bioace-zip-v1` (`RESULTS-bioace-zip.md`) counted every field of `medaesqa_v1.json`: the file has no
`expert_curated_nuggets` key at all. Its nuggets sit under `nuggets`, a non-empty list of strings in
all 40 items. v1 tested a field name, not the nuggets.

v2 is the v1 design unchanged except for where the nuggets are read (`nuggets` first, then
`expert_curated_nuggets`) and a sha256 pin on the MedAESQA file. It is the same data, so this is
the test v1 meant to run, not a variant tried after seeing a score: v1 produced no nugget score.

## What we know now that v1 did not

- No nugget text has been seen. `bioace-zip-v1`'s output is text-free (field names, shapes,
  counts), and it did not count nuggets per question.
- From v1, on these 40 questions: answer length ranks the 30 runs against official completeness
  R at Kendall tau 0.799 (sentences per question) and 0.852 (content words per question); the
  question-overlap baseline's sentence AUROC is 0.538; MedAESQA's M1-M30 are the BioGen runs (29
  distinct, because webis-3 and webis-5 give the same sentences on these questions).
- NLM's BioACE bundle (`bioace-data-models.zip`) holds nuggets for only 2 questions (ids 181 and
  182), not for the 2024 questions, so MedAESQA is the only public source of these nuggets.

## Method (`medaesqa_nugget.py` 0.2.0, standard library only)

As in v1, word for word, except the nugget field. In short: content words by
`biogen_reuse.content`; a nugget needs 2+ content words, a sentence 3+; cover = share of a
nugget's content words found in one sentence; **bar 0.6**, fixed (0.4, 0.5, 0.7, 0.8 for
sensitivity only); per run and question, nugget recall = share of nuggets covered at >= bar by a
scored sentence (no answer = 0), averaged over the 40 questions; Kendall tau-b over the 30 runs
against Table 4 completeness R; length baseline = sentences per question; Kendall's partial tau
with length held fixed; positive control = the expert answer against its own nuggets; negative
control = every run against the next question's nuggets. Output is counts and scores only.

## Checks (must hold for any prediction to count)

- C1: `fetch_public.py` exits 0 (both published files match their pins).
- C2: `test_medaesqa_nugget` runs 10 tests, all pass.
- C3: `wait_public.py` exits 0 for this file (`match` recorded either way).
- C4: the run step exits 0: `problem` null (BioGen files and MedAESQA at their sha256 pins,
  MedAESQA 7,276,948 bytes).
- C5: `nugget_fields` is `{"nuggets": 40}`; question match, run map (30 runs, 29 distinct, every
  share 1.0) and label agreement (4,901 same, 5 differ) are as in v1.

## Predictions

The v1 predictions that depend on nuggets, unchanged (v1 could not test them), plus one new:

- N1: median nuggets per question 3-15; no matched question without a nugget.
- K1 (positive control): the expert answers' nugget recall is at least 50.
- K2 (negative control): the mean nugget recall against the next question's nuggets is at most 10.
- N2: sentence AUROC (best nugget cover) is 0.55-0.75 and above the question baseline's (0.538).
- N3: Kendall tau-b (bar 0.6), nugget recall vs completeness R, is at least 0.50.
- N4: that tau is above the sentence-length baseline's on the same 40 questions (0.799). Below a
  coin flip.
- N5: the partial tau with length held fixed is at least 0.10. About a coin flip.
- N6 (new): that tau is also above the content-word baseline's (0.852). Unlikely (about 1 in 4).
- R1: the run step takes at most 5 minutes.

## Decision rule (v1's, made stricter now that the word baseline is known)

- The matcher is fit only if K1 and K2 hold. If not, nothing is adopted.
- Fit, N3, N4 and N6: nugget recall at bar 0.6 becomes MV2's development yardstick for a Task 2
  rewriting stage.
- Fit, N3 and N5, but not both N4 and N6: it is used only to compare answers of equal length
  (the same word budget), never across lengths.
- Otherwise it is not used, and a rewriting stage waits for the TREC 2025 BioGen judgments.

## Limits, stated now

- 40 questions, 30 runs from 5 teams: tau mostly reflects gaps between teams.
- Table 4's completeness R covers all 65 questions; recall here covers 40.
- Word containment misses paraphrase and can be met by generic words; the controls bound this.
- We do not know whether the experts saw the runs before writing their answers and nuggets.
- No MV2 answers are scored here. No human has checked v1's or bioace-zip-v1's counts.

Contact: MV2, Munim, Inc., mv2@munimtech.com
