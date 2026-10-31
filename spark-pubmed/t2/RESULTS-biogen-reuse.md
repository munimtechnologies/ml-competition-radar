# Results: can TREC 2024 BioGen's sentence judgments grade an answer outside the pool? (biogen-reuse-v1)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0, code Apache-2.0.
Graded 2026-10-31 (about 06:10 UTC) against `PREREGISTRATION-biogen-reuse.md`, word for word.
The job ran once on 2026-10-31, 05:16-05:19 UTC (1 CPU, 1 GB limit). Its outputs, counts and
scores only, are in `results-biogen-reuse/` (`reuse.json`, `runs.json`, `prereg_public.json`).

**Outcome: 3 of 3 checks, 8 of 10 predictions. The word-overlap proxy separates Required
sentences (AUROC 0.70), but answer length alone ranks the 30 runs by official completeness better
than it does (Kendall tau 0.82 against 0.70). By the rule fixed in advance it is not used.**

## Checks

| check | pre-registered | observed | held |
|---|---|---|---|
| C1 | `wait_public.py` exits 0; `match` recorded | exit 0; public copy seen 05:17:48 UTC, sha256 `dcab5f38...744a` on both sides, `match` true | yes |
| C2 | `test_biogen_reuse` runs 8 tests, all pass | "Ran 8 tests", OK | yes |
| C3 | both sha256 match; `problem` null | both files as pinned (`d4569041...4774`, `78449ef2...066d`); `problem` null | yes |

## Predictions

| | pre-registered | observed | held |
|---|---|---|---|
| P1 | 65 topics, 30 runs, 30 matched, none missing; 7,932 sentences, 7,585 labelled (6,227 / 1,032 / 302 / 24) | exactly these | yes |
| P2 | at least 6,100 Required sentences scored | 6,223 | yes |
| P3 | median distinct Required word sets per topic 70-100 | 80 (min 36, max 117) | yes |
| P4 | sentence AUROC, team-out, 0.55-0.75 | 0.7023 | yes |
| P5 | higher than the question-overlap baseline | 0.7023 against 0.5603 | yes |
| P6 | run-out minus team-out AUROC 0.00-0.05 | 0.7124 - 0.7023 = 0.0101 | yes |
| P7 | Kendall tau-b (bar 0.5), team-out recall vs completeness R, >= 0.50 | 0.7030 | yes |
| P8 | that tau higher than the length baseline's | 0.7030 against **0.8186** | **no** |
| P9 | tau-b (bar 0.5), team-out precision vs official precision, >= 0.30 | 0.2552 | **no** |
| P10 | reproduced precision within 1.0 point of Table 3 for >= 20 runs | 30 of 30 (largest gap 0.0049) | yes |
| R1 | analysis <= 10 min; peak memory <= 1 GB | 2.3 s; the runner recorded no peak, but the container was capped at 1 GB and finished normally | yes (memory by the cap only) |

## Decision (fixed in advance)

The rule needed team-out AUROC >= 0.60 **and** P7 **and** P8. AUROC (0.70) and P7 (0.70) held;
P8 did not. **The lexical team-out proxy is not MV2's development metric.** The embedding version
(`biogen-reuse-emb-v1`, pre-registered before this job ran) is still queued and is graded on its
own rule, which also has to beat the same length baseline (0.8186).

## What the numbers show (no predictions; read with care)

- **Completeness R in 2024 follows answer length.** The mean number of sentences per question
  ranks the 30 runs against Table 4's completeness R at tau 0.82 (scored sentences only: 0.84).
  The webis runs give 1.7-2.7 sentences per question and score 7.7-20.2; the ielab runs give
  2.9-3.7 and score 22.8-27.1; the h2oloo and ur-iw runs give 5.4-8.2 and score 32.2-46.3. With
  5 teams, most of this is the gap between teams.
- **Bar sensitivity (not a result).** Team-out recall's tau is 0.84 at bar 0.3, 0.81 at 0.4, 0.70
  at 0.5, 0.50 at 0.6 and 0.43 at 0.7. Bar 0.3 edges past length, but picking it now would be
  fitting the bar to this data, so it is not used.
- **Keeping team mates in the pool hurts.** With only the scored run left out (its team mates'
  sentences kept), recall's tau falls to 0.39 at bar 0.5 (team-out 0.70). A likely reason, not
  tested: teams with many similar runs (ielab 10, webis 7) find their own near-copies in the pool.
  Leave-one-run-out is not a safe check for these judgments.
- **Table 3's precision is reproduced exactly from the released labels:** Required sentences over
  all sentences, per question, averaged over the 65 questions. All 30 runs are within 0.005 of the
  table under all three definitions tried.

## What this means for SPARK Task 2

On 2024 data a pool of other runs' Required sentences does not rank systems better than counting
sentences. Any yardstick for a rewriting stage therefore has to be compared at **equal answer
length**, or it may only be rewarding longer answers. The next test (`PREREGISTRATION-medaesqa-
nugget.md`) scores runs against NLM's expert-written nuggets (MedAESQA, CC0) instead of a pool of
other runs, and adds a partial tau that holds length fixed.

## Limits

30 runs from 5 teams; word overlap misses paraphrase; the official numbers are transcribed from the
overview's HTML tables; the official completeness uses embeddings and k-means over a pool that
contains the scored run, so it and a leave-out proxy measure different things. No human has
checked these counts.

Contact: MV2, Munim, Inc., mv2@munimtech.com
