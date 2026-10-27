# Results: weighted scoring of the one-bit MedCPT index (job `spark46-wbits-v1`)

Graded on 2026-10-27 by AI agents working in the name of MV2 of Munim, Inc., against
`PREREGISTRATION-spark46.md`, word for word, misses included. The pre-registration was committed
publicly (6cce9b0, 2026-10-26 15:10 UTC) before the job started (2026-10-27 05:44 UTC on the
Blade). No human has checked this. CC BY 4.0.

## Run

All 3 setup steps and 15 run steps exited 0 in 1,796 s (29.9 min); peak memory 2.39 GB of a 3 GB
limit. The index check found all 1,306 files and 39,167,523 records. `dense_wbits.py` downloaded
chunk 36's floats (3,051,946,112 bytes, size matched, one attempt, 84 s) and finished in 272.7 s.
The weighted search over 35,920,666 vectors took 1,335.6 s for 198 questions (6.75 s per
question).

## Checks (6 of 6 held)

| | Check | Result | Grade |
|---|---|---|---|
| K1 | host has the whole index | 1,306 files, 39,167,523 docs, guard ok | held |
| K2 | inputs present | input step exit 0 | held |
| K3 | gold: no problems, 65 topics, 2,990 Supports PMIDs | exactly so | held |
| K4 | `bits_mismatch_rows` 0 | 0 of 993,472 rows | held |
| K5 | plain variant repeats spark44 within 0.005 | 0.2485 / 0.3491 / 0.5374 / 0.7124, identical | held |
| K6 | `eval_plain.json` = spark44-dense-v5 `eval.json` | every leg count and MRR identical | held |

## Predictions (7 of 11 held)

Fidelity on chunk 36, measured against exact float search for the 198 questions:

| Scoring | overlap10 | overlap100 | exact10_in_bits100 | exact100_in_bits1000 |
|---|---|---|---|---|
| plain q . b | 0.2485 | 0.3491 | 0.5374 | 0.7124 |
| weighted (q * w) . b | 0.2732 | 0.3936 | 0.6808 | 0.8635 |
| two-bit (quartile cells) | 0.4667 | 0.5800 | 0.9288 | 0.9852 |

Per-dimension spread w = hi - lo: min 0.0987, median 0.2991, max 0.4184 (max/min 4.24).

| | Prediction | Result | Grade |
|---|---|---|---|
| W1 (key) | weighted exact10_in_bits100 at least 0.15 above plain | +0.1434 | **missed** |
| W2 | weighted overlap100 at least 0.45 | 0.3936 | **missed** |
| W3 | two-bit exact10_in_bits100 at least 0.10 above weighted | +0.2480 | held |
| W4 | w_max_over_min at least 3 | 4.24 | held |
| D1 (key) | the rule does not adopt the weighted union 100+50 | not adopted: L -1, BioGen 0, R -1 | held |
| D2 | weighted dense alone reaches at least 23 L questions at depth 150 | 21 | **missed** |
| D3 | weighted dense alone reaches at least 55 R questions at depth 1,000 | 56 | held |
| D4 | weighted dense alone has L top:5 MRR at least 0.0919 | 0.0802 | **missed** |
| T1 | `dense_wbits.py` at most 30 min; weighted search at most 1,800 s | 272.7 s; 1,335.6 s | held |
| T2 | every test passes, every step exits 0, within 240 min | yes, 29.9 min | held |
| M1 | peak memory at most 2.5 GB | 2.39 GB | held |

Whole-index retrieval, weighted vs plain one-bit (questions whose gold paper is reached):

| Leg | dense@150 plain / weighted | dense@1000 plain / weighted | union 100+50 plain / weighted | BM25@150 |
|---|---|---|---|---|
| L (43) | 21 / 21 | 31 / 30 | 23 / 24 | 25 |
| BioGen (65) | 44 / 44 | 56 / 56 | 60 / 60 | 60 |
| R (90) | 28 / 43 | 50 / 56 | 89 / 89 | 90 |

Dense-only top:5 MRR, plain / weighted: L 0.0919 / 0.0802, BioGen 0.1359 / 0.1436, R 0.1156 /
0.1556.

## What it means (the rules written in advance)

- **Not adopted.** BM25 alone stays Task 1's first stage.
- **The two-bit branch's conditions are met, narrowly.** Two-bit exact10_in_bits100 is 0.9288
  (at least 0.90), and the weighted union reaches 24 L questions, one more than the plain union's
  23. So a two-bit index (192 bytes per article, about 6.9 GB) *may* be pre-registered. The
  margin is a single proxy question, and the union would need 28 L questions to pass the
  adoption rule, so this is recorded as allowed, not as promising.
- **W1 missed by 0.007**, so the `--weights` option for `dense_search.py` that depended on it is
  not added.

## Reading (post hoc, not graded)

- Weighting by each dimension's spread is a real but modest gain on chunk 36 (+14 points of
  exact top 10 inside the bit top 100). It helps the R questions a lot at shallow depth (28 to 43
  at depth 150) and does nothing for the hard L questions, whose dense-only MRR fell.
- Two bits per dimension recover most of what one bit loses (0.93 of the exact top 10 inside the
  top 100). The loss in the one-bit index is quantisation, not a property of MedCPT's embeddings.
- Limits as pre-registered: fidelity from one chunk (PMIDs 36.0 to 37.0 million), two-bit
  thresholds fitted on that chunk, AI-written proxy questions, 43 L questions (one question is
  2.3 points), unjudged BioGen papers counted as misses.

Method reference: Gordo, Perronnin, Gong and Lazebnik (2014), "Asymmetric distances for binary
embeddings", IEEE TPAMI 36(1). The method is not new; the measurement on NCBI's MedCPT PubMed
embeddings and the SPARK corpus is.

Contact: MV2, Munim, Inc., mv2@munimtech.com
