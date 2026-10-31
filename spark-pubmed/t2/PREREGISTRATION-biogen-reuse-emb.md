# Pre-registration: the BioGen leave-out test again, with sentence embeddings (biogen-reuse-emb-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Written 2026-10-31 (about 00:45 UTC), before this job ran and **before biogen-reuse-v1 (the
word-overlap version) had run**: no number from either test had been seen. The job waits until
this file is public on GitHub and records whether the public copy matches the one it carries.

## Why

`PREREGISTRATION-biogen-reuse.md` asks whether TREC 2024 BioGen's sentence judgments can grade an
answer from outside the judged pool, using word overlap. Its decision rule names the next step if
word overlap fails: the same test with all-mpnet-base-v2 embeddings, one of the two models the
BioGen 2024 overview (arXiv 2411.18069) names for its completeness clustering. We pre-register
that test now, while both results are unknown, and run the two side by side. Fixing it before
seeing the word-overlap numbers means its bar and predictions cannot be fitted to them.

Prior art: as in `PREREGISTRATION-biogen-reuse.md` (checked 2026-10-30). We found no leave-out
test of BioGen's sentence judgments, with words or embeddings.

## Method (`biogen_reuse_emb.py` 0.1.0)

- Same data files and sha256 pins, same runs, topics, labels, team-out and run-out pools, the same
  3-content-word floor, and the same official Tables 3/4 (`official_biogen2024.json`) as
  `biogen_reuse.py` 0.1.0, which is imported unchanged. The job checks that its copies of
  `biogen_reuse.py` and `official_biogen2024.json` match the public ones.
- Model: `sentence-transformers/all-mpnet-base-v2` at commit `e8c3b32e...9130`; weights
  `model.safetensors` sha256 `78c0197b...5658`. Mean pooling over tokens, unit length, float32 on
  CPU, 2 threads, at most 384 tokens.
- Sentences are keyed by their content-word set, as in the word-overlap test, and each key is
  embedded once from the alphabetically first of its cleaned texts (citation markers removed).
- Similarity = cosine. **Primary bar = 0.7**, fixed now as a typical paraphrase-level cosine for
  this model, before any BioGen sentence was embedded. Bars 0.5, 0.6, 0.75, 0.8, 0.85 and 0.9
  are sensitivity only. Bar-free "soft" recall and precision (mean best similarity) are reported
  without predictions.
- In the same job, the word-overlap proxy (Dice, bar 0.5) is recomputed on the same sentences, so
  the two are compared pair by pair: the team-out sentence AUROC difference (embedding minus
  words) gets a 95% interval from 1,000 bootstrap resamples of the 65 topics (seed 20261031).
- `biogen_reuse.analyse` 0.1.0 is also run unchanged on the same data, and its team-out and
  run-out AUROC, its tau at bar 0.5, the length baseline and the counts must equal this job's
  word-overlap numbers (`agree`).
- Output is counts and scores only, never sentence or question text.

## Checks (must hold for any prediction to count)

- C1: `wait_public.py` exits 0 for this file (`match` recorded either way).
- C2: `test_biogen_reuse_emb` runs 7 tests, all pass.
- C3: the public `biogen_reuse.py` and `official_biogen2024.json` are fetched and match the job's
  copies (`match` true in both).
- C4: `fetch-model` exits 0: `problem` null, weights sha256 as pinned.
- C5: the run step exits 0: `problem` null, both data sha256 as pinned, and `agree` is true.

## Predictions

- E1 (counts, exact): 65 topics, 30 runs, 7,932 sentences, 30 runs ranked against the tables.
- E2: embedding sentence AUROC, team-out (Required vs the other three labels), is 0.60-0.80.
- E3: it is higher than the word-overlap team-out AUROC on the same sentences.
- E4: the bootstrap 95% interval of that difference lies wholly above 0. We rate this near a
  coin flip.
- E5: embedding run-out AUROC minus team-out AUROC is 0.00-0.05.
- E6: Kendall tau-b (bar 0.7), team-out embedding recall vs official completeness R, is >= 0.50.
- E7: that tau is higher than the length baseline's tau (sentences per topic vs completeness R).
  Also near a coin flip: in the 2024 runs, longer answers may simply cover more.
- E8: Kendall tau-b (bar 0.7), team-out embedding precision vs official precision, is >= 0.30.
- R1: embedding all distinct sentences takes at most 30 minutes on 2 threads; the run step's peak
  memory (`peak_rss_mb`) is at most 2,000 MB.

## Decision rule (fixed now)

- The embedding proxy passes if its team-out sentence AUROC is >= 0.60, E6 holds and E7 holds:
  the same rule as the word-overlap proxy's, at this test's primary bar.
- If only one of the two proxies passes, that one becomes MV2's development metric for a Task 2
  rewriting stage. If both pass, the one with the higher team-out AUROC is used (the word-overlap
  one if they are within 0.01, because it needs no model).
- If neither passes, no further variant of this proxy (other bars, the soft scores, other models)
  is tried on the 2024 judgments: a rewriting stage would then wait for the TREC 2025 BioGen
  judgments. Either way, both results are published.

## Limits, stated now

- 30 runs from 5 teams: tau mostly reflects the gaps between teams.
- The bar 0.7 is a judgement call, not tuned; the sensitivity bars show how much it matters.
- The official completeness uses k-means (k = 10) over the pooled Required sentences, including
  the scored run, so an in-pool official number and a leave-out proxy measure different things.
- Embedding one text per content-word set treats sentences that differ only in stop words,
  case or citations as one.
- No MV2 answers are scored here.

Contact: MV2, Munim, Inc., mv2@munimtech.com
