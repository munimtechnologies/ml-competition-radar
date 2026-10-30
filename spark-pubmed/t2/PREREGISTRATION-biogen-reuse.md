# Pre-registration: can TREC 2024 BioGen's sentence judgments grade an answer outside the pool? (biogen-reuse-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Written 2026-10-30 (about 21:30 UTC), before the job ran. The job's first step waits until this
file is public on GitHub and records whether the public copy matches the one it carries.

## Why

SPARK Task 2 (NIH/NLM) scores open-ended biomedical answers on Grounded Nugget F1. Its own
development data is not public, and the TREC 2025 BioGen judgments are still unreleased. The
closest public data is TREC 2024 BioGen: 65 questions, 30 runs from 5 teams, every answer sentence
labelled Required, Unnecessary, Borderline or Inappropriate. Its overview (arXiv 2411.18069)
scores completeness by k-means clustering (k = 10) of the Required sentences pooled across
**all** runs, with the scored run inside the pool and its own labels used. It reports no
leave-out test.

Any answer MV2's system writes is a new run: no assessor read it, and its sentences have no
labels. So before the 2024 judgments are used to develop a Task 2 rewriting stage, we test whether
they still rank runs when the scored run is outside the pool and its labels are hidden.

Prior art checked (2026-10-30): the BioGen 2024 overview (no leave-out analysis); TREC NeuCLIR
2022/2024 (leave-one-run-out and leave-one-team-out tests for retrieval judgments, Kendall tau
around 0.95-0.99); Rajput and Pavlu's nugget-based evaluation (inferring document relevance from
nuggets). We found no leave-out test of BioGen's sentence-level judgments or of a proxy built
from them. A web search is not proof that none exists.

## Method (`biogen_reuse.py` 0.1.0, standard library only)

- Data: NIST's `biogen_collection_v3.json` (sha256 78449ef2...066d, 11,128,359 bytes) and
  `BioGen2024topics-json.txt` (sha256 d4569041...4774), the files every earlier BioGen job here
  used. A different hash stops the job.
- Official per-run numbers: Table 3 (precision) and Table 4 (completeness R, S+R, R+B),
  transcribed into `official_biogen2024.json` with the teams from the tables' group headers
  (h2oloo 6 runs, ielab 10, ii_research 1, ur-iw 6, webis 7).
- Words: lower case, citation markers (`[...]`, `(PMID ...)`, `PMID 123`) removed, tokens
  `[a-z0-9]+`, a fixed list of 113 stop words and digit strings of 5+ characters dropped; a
  sentence is a **set** of content words. Sentences with fewer than 3 content words are not
  scored. Similarity = Dice (set F1). **Bar = 0.5**, fixed now; bars 0.3, 0.4, 0.6 and 0.7 are
  reported as sensitivity only.
- For run r and topic t, the **team-out pool** is the distinct word sets of the Required sentences
  of every run from other teams (the primary setting); the **run-out pool** drops only r.
- Proxy recall = share of pool items that some scored sentence of r matches at >= bar, averaged
  over the 65 topics (x 100). Proxy precision = share of r's sentences whose best pool match is
  >= bar; unscored sentences count as unmatched, because the official precision counts every
  sentence.
- Sentence level: each scored sentence's best team-out match, against its own label (Required vs
  Unnecessary + Borderline + Inappropriate; unlabelled sentences left out), as an AUROC. Baseline:
  Dice with the question + narrative.
- Run level: Kendall tau-b over the 30 runs between proxy recall and official completeness R, and
  between proxy precision and official precision. Baseline: mean sentences per topic (length).
- Reproduction check: precision recomputed from the labels as the official one is defined
  (Required / all sentences, per question, averaged over the 65 questions; a question with no
  sentences counts 0). Two variants are reported too: labelled sentences only, and answered
  questions only.
- Output is counts and scores only, never sentence or question text.

## Checks (must hold for any prediction to count)

- C1: `wait_public.py` exits 0 (this file public); `match` is recorded either way.
- C2: `test_biogen_reuse` runs 8 tests, all pass.
- C3: both sha256 match; `problem` is null.

## Predictions

- P1 (counts, exact): 65 topics, 30 runs, all 30 matched to the official tables, none missing;
  7,932 sentences, 7,585 labelled (6,227 Required, 1,032 Unnecessary, 302 Borderline,
  24 Inappropriate). From the earlier census and the schema's per-run counts.
- P2: at least 6,100 Required sentences are scored (3+ content words).
- P3: the median number of distinct Required word sets per topic is 70-100.
- P4: sentence AUROC, team-out, is 0.55-0.75.
- P5: sentence AUROC, team-out, is higher than the question-overlap baseline's.
- P6: run-out AUROC minus team-out AUROC is 0.00-0.05 (same-team runs share wording).
- P7: Kendall tau-b (bar 0.5), team-out proxy recall vs official completeness R, is >= 0.50.
- P8: that tau is higher than the length baseline's tau (sentences per topic vs completeness R).
  We put this near a coin flip: answer length alone may already rank runs well.
- P9: Kendall tau-b (bar 0.5), team-out proxy precision vs official precision, is >= 0.30.
- P10: the reproduced precision (primary definition) is within 1.0 point of Table 3 for at least
  20 of the 30 runs.
- R1: the analysis step takes at most 10 minutes; peak memory at most 1 GB.

## Decision rule (fixed now)

The team-out lexical proxy becomes MV2's development metric for a Task 2 rewriting stage only if
the team-out sentence AUROC is >= 0.60, P7 holds and P8 holds. Otherwise it is not used, and the
next step is the same test with sentence embeddings (all-mpnet-base-v2, Apache-2.0, one of the two
models the overview names), pre-registered separately. Either way the result is published.

## Limits, stated now

- 30 runs from 5 teams: tau over 30 runs mostly reflects the gaps between teams.
- Word overlap misses paraphrase and counts topic words; the official metric uses embeddings and
  k-means with k = 10, so the two measure different things even in-pool.
- The official numbers are a transcription from the overview's HTML tables.
- No MV2 answers are scored here. They are new runs, and scoring them is what this test is for.

Contact: MV2, Munim, Inc., mv2@munimtech.com
