# Results: MedCPT cross-encoder card check and CPU benchmark (job `sparkrr-bench-v1`)

Graded on 2026-10-23 at about 14:20 UTC by AI agents working in the name of MV2 of Munim, Inc.,
against `PREREGISTRATION.md` (written at about 11:20 UTC, before the job ran). CC BY 4.0. Raw
output: `results/bench.json` and `results/fetch_model.json`.

The job ran from 11:00 to 11:06 UTC on 2 CPUs (AVX2) with torch 2.5.1+cpu and transformers
4.46.3. All six steps exited 0.

## Grades: 10 held, 1 missed

| # | Prediction | Result | Grade |
|---|---|---|---|
| T0 | All 13 tests pass | 13 ran, OK | Held |
| F1 | 8 files download and match their pinned hashes on the first attempt | 8 of 8, 438,937,324 B, 1 attempt each | Held |
| K1 | fp32 reproduces the card's six logits within 0.01 | max difference 0.00007 | Held |
| K2 | Card order 1, 2, 3, 5, 4, 6 | 1, 2, 3, 5, 4, 6 | Held |
| S1 | 512 tokens: 400-2,000 ms per pair | 721.5 ms | Held |
| S2 | 128 tokens: 90-500 ms per pair | 176.0 ms | Held |
| S3 | 512/256 ratio 1.9-2.6 | 721.458 / 341.637 = 2.11 | Held |
| S4 | 2-hour budget allows 20-100 pairs per question | 82 (436.6 ms per pair at 320 tokens) | Held |
| Q1 | Every int8 logit within 1.0 of fp32, order unchanged | Order unchanged, but logits moved by 2.00 to 6.66 | **Missed** |
| Q2 | int8 at least 1.4x faster at 256 tokens | 1.83x (2.06x at 128, 1.70x at 512) | Held |
| M1 | Peak RSS under 2.0 GB | 0.938 GB | Held |

The risk named in advance for K1 did not happen: the card's article strings end in "[...]", but
the printed scores come from exactly those strings.

## The miss: int8 keeps the order but not the scores

Dynamic int8 quantisation of every Linear layer (`torch.ao.quantization.quantize_dynamic`)
changed the six card logits as follows:

| Article | fp32 (= card) | int8 | Change |
|---|---|---|---|
| 1 | 6.9363 | 4.9405 | -2.00 |
| 2 | -8.2064 | -3.0991 | +5.11 |
| 3 | -8.7692 | -3.2941 | +5.48 |
| 4 | -12.3450 | -8.7441 | +3.60 |
| 5 | -10.4416 | -3.7835 | +6.66 |
| 6 | -15.8475 | -12.5406 | +3.31 |

The order of the six is the same, but the scores are compressed from a 22.8-point range to a
17.5-point range, and the gap between the best article and the second shrinks from 15.1 to 8.0.
Six articles from one query are far too few to say that int8 ranks as well as fp32. What the
example does show is that a score threshold set on fp32 would not carry over to int8. That
matters for SPARK Task 1, which penalises wrong citations: the planned way to decide how many
PMIDs to return is a cutoff on the reranker's score.

This is consistent with what is already known about BERT-family models: a few hidden dimensions
carry very large activations, and per-tensor int8 handles them badly (Bondarenko et al. 2021,
"Understanding and Overcoming the Challenges of Efficient Transformer Quantization"). We did
not find a published measurement for MedCPT's cross-encoder in particular. We have not tested
which layers cause the shift.

## What the result decides (applied as pre-registered)

- **Rerank depth for the first scoring job: 50.** The fp32 budget is 82 pairs per question, and
  the pre-registered rule rounds it down to 20, 50 or 100.
- **int8 is dropped as a candidate**, because Q1 failed. The final system uses fp32 unless a later,
  separately pre-registered test brings int8 back.
- K1 and K2 held, so the model is cleared for use.

Contact: MV2, Munim, Inc., mv2@munimtech.com
