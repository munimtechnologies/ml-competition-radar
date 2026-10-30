# Results: biogen-llm-v2 and biogen-llm-v3 (a 0.5B open LLM as a gated conflict judge, plus a timing check)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Graded 2026-10-30, about
15:45 UTC, against `PREREGISTRATION-biogen-llm-v2.md` (written before v2 ran) and
`ADDENDUM-biogen-llm-v3.md` (written before v3 ran). No human has checked this.

## Runs

- `biogen-llm-v2`: the Blade, 2026-10-30 07:41-08:22 UTC. Stopped from outside (exit 143) at 600
  of 1,389 judged pairs, so it has timing and model checks but no judge scores.
- `biogen-llm-v3`: the same files, setup and steps, re-filed unchanged under the rule for exit
  143. The Blade, 13:46-14:47 UTC (3,651 s), peak memory 3.12 of 4 GB, every step exit 0. Outputs:
  `results-biogen-llm-v3/{llm,bench,model}.json`.

## Checks

- **C1.** `fetch_code.py` exit 0; the five test modules ran 31 tests, OK (v2 and v3). **Held.**
- **C2.** `model.json`: all 8 pinned files present (`model.safetensors` 988,097,824 bytes),
  `problems` empty, revision `7ae557604adf67be50417f59c2c2f167def9a775` (v2 and v3). **Held.**
- **C3.** `llm.json`: 14,763 judgments, 0 unknown labels, 11,927 scored, 11,592 unique pairs;
  census 202 contradicting topic-papers, 168 mixed. **Held.**

## Predictions

Timing (`bench.json`, one 335-token prompt, 2.0-CPU limit, median of 3 timed passes):

| configuration | v2 median (s) | v3 median (s) |
|---|---|---|
| float32, 2 threads | 3.25 | 2.92 |
| float32, 4 threads | 3.74 | 3.88 |
| bfloat16, 2 threads | 91.75 | 85.28 |
| bfloat16, 4 threads | 102.71 | 102.00 |

- **B1.** float32 at 2 threads between 1 and 15 s: 3.25 s (v2), 2.92 s (v3). **Held.**
- **B2.** bfloat16 at 2 threads at least 3 times slower: 28.2 times (v2), 29.2 times (v3).
  **Held.**
- **B3.** float32 at 4 threads at least 0.9 times the 2-thread median: 1.15 times (v2), 1.33 times
  (v3). **Held.** 4 threads were slower than 2 on a 2-CPU limit in both runs.

Judge (`llm.json`, v3):

- **G1.** Gate: 1,432 judgments, 140 Contradicts, 185 Neutral, 1,107 Supports. **Held.**
- **G2.** `scoring.judged` = 1,389. **Held.**
- **G3.** `letter_mass_mean` at least 0.5: 0.9999 (minimum 0.9992, none below one half). **Held.**
- **G4.** Gate Contradicts-vs-rest AUROC between 0.50 and 0.70: **0.316. Missed** (below the range,
  not above it).
- **G5.** Entry argmax F1 below 0.25: 0.0. **Held.**
- **G6.** Entry argmax recall at most 0.509: 0.0. **Held.**
- **G7.** No probe stop, and `ms_per_judged_pair` between 1,000 and 15,000: no stop (probe 2.15 s
  per pair), 1,902.7 ms. **Held.**

**3 of 3 checks and 9 of 10 predictions held; G4 missed.**

## What the judge did

Asked whether each quoted passage supports the answer sentence (A), contradicts it (B) or neither
(C), the 0.5B model answered A for 1,429 of the 1,432 gated judgments and C for 3. It never
answered B. All 140 Contradicts passages and all 185 Neutral passages got A.

Its probability for B ran the wrong way. Mean probabilities (B, A, C) inside the gate:

| assessor label | n | p(B, contradicts) | p(A, supports) | p(C, neither) |
|---|---|---|---|---|
| Contradicts | 140 | 0.088 | 0.747 | 0.166 |
| Neutral | 185 | 0.113 | 0.754 | 0.133 |
| Supports | 1,107 | 0.123 | 0.751 | 0.127 |

So passages the assessors judged contradicting got the *lowest* "contradicts" probability, and an
AUROC of 0.316 inside the gate (0.310 against Supports only; topic-paper level 0.379). Its A
probability did not separate Supports from the rest either (AUROC 0.508). The overall entry
AUROC of 0.689 comes from the gate itself: as a plain yes/no score, the negation gate alone gives
(1 + 0.509 - 0.111) / 2 = 0.699 (computed here from the gate's counts, 140 of 275 Contradicts and
1,292 of 11,652 others), so the judge's ranking inside the gate lowered it. With the polarity-clash
flag added (`union_polarity_clash`), the entry argmax result is exactly the polarity-clash flag's
own (precision 0.344, recall 0.040, F1 0.072): the judge added nothing.

Recorded, not predicted: slot AUROC 0.701, topic-paper AUROC 0.717, best-threshold (oracle) entry
F1 0.164 at p(B) 0.0147, 1 passage clipped at 250 words. The bfloat16 4-thread and float32
4-thread timings are in the table above.

## Decision (rule fixed before v2 ran)

Adoption needed entry argmax F1 at least 0.25, precision at least 0.30 and at most 10,000 ms per
pair. F1 is 0.0 and precision is undefined (no B answers), so **the LLM flag is not adopted.** The
composer keeps compose.py 0.2.0's polarity-clash flag, and no larger LLM is tried as a conflict
judge on the shared CPUs. B2 held in both runs, so every later CPU job in this project loads
weights in float32.

## What this says, and what it does not

- v1 (1.5B, bfloat16, 4 threads) ran at 189.1 s per pair; v3 (0.5B, float32, 2 threads) at 1.9 s,
  about 99 times faster. The timing check puts most of that on bfloat16 (about 29 times on this
  host), not on threads.
- A 0.5B instruction model with this one prompt behaves like an "always supports" answerer on
  negation-bearing biomedical passages. A 0.5B model is small, the prompt lists "supports" first,
  and nothing was tuned, so this is a negative result for this setup, not for LLM judges in general.
- The labels are BioGen 2024's passage-level judgments, whose own between-slot agreement on
  Contradicts is 0.39. Questions and passages are BioGen's, not SPARK's. Only counts and scores are
  published, never passage or sentence text.

Contact: MV2, Munim, Inc., mv2@munimtech.com
