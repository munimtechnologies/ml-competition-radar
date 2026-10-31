# Pre-registration: do NLM's expert nuggets rank BioGen 2024 runs better than answer length? (medaesqa-nugget-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Written 2026-10-31 (about 06:30 UTC), before this job ran. The job's first steps wait until this
file is public on GitHub and check that its copies of `biogen_reuse.py` and
`official_biogen2024.json` match the public ones.

## What we knew when writing this

- `biogen-reuse-v1` (`RESULTS-biogen-reuse.md`) was graded this morning: a pool of other teams'
  Required sentences separates Required sentences (AUROC 0.70), but answer length alone ranks the
  30 runs against official completeness R at Kendall tau 0.82, above the proxy's 0.70. This test
  was designed **after** seeing those numbers; that is why it adds a partial tau that holds
  length fixed.
- `biogen-reuse-emb-v1` (embeddings, pre-registered earlier) is still queued; its numbers are
  unknown. Its rule ("no further variant of this proxy on the 2024 judgments") is about proxies
  built from a pool of other runs' sentences. This test uses no such pool, so it is a different
  yardstick, not a variant; we say so openly so readers can judge.
- MedAESQA (NLM; Open Science Framework osf.io/ydbzq; licence CC0 1.0; `medaesqa_v1.json`,
  7,276,948 bytes, modified 2025-04-15) holds, per question, an expert-written answer, the
  expert's nuggets (`expert_curated_nuggets`), and machine answers labelled M1, M2, ... with
  sentence labels of the same kind as BioGen 2024's (README: 30 approaches). The BioACE paper (arXiv 2602.04982) says its 40 test
  questions are questions 1-40 of the 65 BioGen 2024 questions. **No nugget text had been seen
  when this was written** (the bar and predictions below are not fitted to it); we know the
  file's fields only from its README and a summary of its first record.

## Why

SPARK Task 2 (NIH/NLM) scores answers on Grounded Nugget F1. A yardstick that scores an answer
against expert nuggets needs no pool of other runs, so an answer from MV2's system is scored
exactly as a 2024 run is. The question is whether a cheap, model-free version of it tracks the
human judgments better than counting sentences does.

Prior art (checked 2026-10-31): BioACE (Gupta, Bartels, Demner-Fushman, NLM; arXiv 2602.04982,
code github.com/deepaknlp/BioACE) already matches answer nuggets to these expert nuggets: answer
nuggets are extracted by Llama-3.3-70B, matched with MiniLM or SimCSE embeddings and a fitted
two-component mixture, and the resulting recall ranks runs against human recall at Kendall 0.758
(MiniLM). What this test adds: a version with no language model at all (word containment,
standard library, seconds on one CPU), an explicit answer-length baseline and a partial tau with
length held fixed (we did not find either in the parts of the BioACE paper we read), and a check
that MedAESQA's anonymised runs are the 30 BioGen runs.

## Method (`medaesqa_nugget.py` 0.1.0, standard library only)

- Data: BioGen 2024 topics and `biogen_collection_v3.json` at the same sha256 pins as
  `biogen_reuse.py` 0.1.0 (imported unchanged); `medaesqa_v1.json` from OSF must be 7,276,948
  bytes, and its sha256 is recorded. Official per-run numbers: `official_biogen2024.json`
  (Tables 3 and 4, unchanged).
- Words: `biogen_reuse.content` (lower case, citation markers removed, 113 stop words, digit
  strings of 5+ characters dropped). A nugget needs 2+ content words; a sentence needs 3+.
- Nuggets: every string inside `expert_curated_nuggets` (a list, a dict with a text field, or
  newline-separated text); the value shapes seen are recorded without text.
- Questions: a MedAESQA id is used as the BioGen id when BioGen has it with the same question
  (Dice >= 0.9 on content words); otherwise the BioGen question with the highest Dice (>= 0.9).
- Cover of a nugget by a sentence = share of the nugget's content words in the sentence.
  **Bar = 0.6**, fixed now; bars 0.4, 0.5, 0.7 and 0.8 are sensitivity only.
- Per run and question, using the BioGen file's sentences: **nugget recall** = share of the
  question's nuggets covered at >= bar by at least one scored sentence (no answer = 0); nugget
  precision = share of all the answer's sentences that cover some nugget; soft recall = mean best
  cover (no bar). Each is averaged over the matched questions.
- Sentence level: each scored, labelled sentence's best nugget cover as an AUROC for Required vs
  the other three labels; baseline = Dice with the question.
- Run level: Kendall tau-b over the 30 runs between nugget recall and Table 4 completeness R
  (all 65 questions); length baseline = mean sentences per matched question; and Kendall's
  partial tau of recall and completeness R with length held fixed.
- Controls: the expert answer itself, split into sentences, scored against its own nuggets
  (positive); every run scored against the next question's nuggets (negative).
- Mapping check: each MedAESQA run M1-M30 is mapped to the BioGen run that shares most of its
  scored sentences (content-word sets) on the matched questions; label agreement is counted on
  sentences paired by position.
- Output is counts and scores only, never question, nugget or sentence text.

## Checks (must hold for any prediction to count)

- C1: `wait_public.py` exits 0 for this file (`match` recorded either way).
- C2: `test_medaesqa_nugget` runs 9 tests, all pass.
- C3: the job's `biogen_reuse.py` and `official_biogen2024.json` match the public copies
  (`match` true in both).
- C4: the run step exits 0: `problem` null (both BioGen sha256 as pinned, MedAESQA 7,276,948
  bytes).

## Predictions

- M1: 40 MedAESQA questions; all 40 matched to BioGen questions (by id or text), 40 distinct; 30
  BioGen runs scored.
- M2: 30 MedAESQA runs, mapped to 30 distinct BioGen runs, each sharing at least 90% of its scored
  sentences with its BioGen run.
- N1: median nuggets per question 3-15; no matched question without a nugget.
- K1 (positive control): the expert answers' nugget recall is at least 50.
- K2 (negative control): the mean nugget recall against the next question's nuggets is at most 10.
- N2: sentence AUROC (best nugget cover) is 0.55-0.75 and above the question baseline's.
- N3: Kendall tau-b (bar 0.6), nugget recall vs completeness R, is at least 0.50.
- N4: that tau is above the length baseline's on the same 40 questions. We rate this below a
  coin flip: in biogen-reuse-v1 length reached 0.82 on all 65.
- N5: the partial tau with length held fixed is at least 0.10. About a coin flip.
- R1: the run step takes at most 5 minutes.

## Decision rule (fixed now)

- The matcher is fit only if K1 and K2 hold. If not, nothing is adopted.
- Fit, N3 and N4: nugget recall at bar 0.6 becomes MV2's development yardstick for a Task 2
  rewriting stage.
- Fit, N3 and N5 but not N4: it is used only to compare answers of equal length (the same word
  budget), never across lengths.
- Otherwise it is not used, and a rewriting stage waits for the TREC 2025 BioGen judgments.
- `biogen-reuse-emb-v1` keeps its own rule. If both it and this test end in "used", this one is
  preferred, because it scores an outside answer with no other run's sentences.

## Limits, stated now

- 40 questions, 30 runs from 5 teams: tau mostly reflects gaps between teams.
- Table 4's completeness R covers all 65 questions; recall here covers 40.
- Word containment misses paraphrase and can be met by generic words; the controls bound this.
- We do not know whether the experts saw the runs before writing their answers and nuggets.
- No MV2 answers are scored here.

Contact: MV2, Munim, Inc., mv2@munimtech.com
