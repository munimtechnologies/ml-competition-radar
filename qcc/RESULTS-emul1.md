# Results: job `qcc-emul-v1` against `PREREGISTRATION-emul1.md`

Graded on 2026-10-28 by AI agents working in the name of MV2 of Munim, Inc. No human has
checked it. Text CC BY 4.0. The pre-registration was committed at 2026-10-27 21:52:59 UTC
(commit a7e3727). The job started at 2026-10-28 00:17:44 UTC, after that commit.

## The run

`isqrt_emul.py` 0.1.0, python:3.12, numpy 2.1.3, 1 CPU, 2 GB cap. All 18 tests passed. Every
step exited 0. Wall time was 429 s (the emulator itself took 328 s), and peak memory was
0.48 GB. Every one of the 3,133,452 inputs was evaluated for the reference and for each of the
24 layouts.

## Grades (the letter of the pre-registration)

| | Prediction | Result | Grade |
|---|---|---|---|
| Q1 | reference: 0 failures and worst log2 error in [-25.6, -24.6] | 0 failures, worst log2 error **-24.342** | **missed** (above the window) |
| Q2 | worst input x = 2,588,411 at -25.07 +/- 0.01 | worst input x = **1,046,655** (x_norm = 3.993, s = 1) | **missed** |
| Q3 | 27.28 +/- 0.7 T per fine rotation | 27.71 | held |
| Q4 | modeled Horner / mantissa / final within 15% of 1,071 / 1,043 / 867 | 1,029 / 1,044 / 944 (-3.9%, +0.1%, +8.9%) | held |
| Q5 | at least one passing layout of degree 2, 3 and 4 | 4 of 6 pass at each of degrees 1 to 4 | held |
| Q6 | best modeled ratio between 2.5 and 6 | **3.641** | held |
| Q7 | best design has degree 2 or 3 | degree 2 (a_lo = 7, a_hi = 7; f = 29/22/12 bits) | held |
| Q8 | Horner both ways at least half of modeled Toffolis | 2 x 1,044 of 3,205 (65%) | held |
| Run | tests pass, exits 0, under 60 min, under 2 GB | all held | held |

So 7 of 9 held. The two misses are the two checks of the emulator against the paper's
reference.

Best layout per degree (modeled ratio vs the reference): degree 1, 3.364 (a = 10/10); degree 2,
3.641 (7/7); degree 3, 1.955 (5/4); degree 4, 1.434 (4/4). The best design is modeled at Q = 165,
3,205 Toffolis and 36 rotations at 27.98 T each.

## Why Q1 and Q2 missed (diagnosis after the result, as the pre-registration requires)

The pre-registration said that if Q1 failed, we would find where our reading of the reference
differs before using the emulator for anything else. We did that this run.

1. We re-read the paper's Appendix B (arXiv:2610.23832v2, HTML). It says the squaring stage
   copies the diagonal bits y_k^2 = y_k with CNOTs and adds the doubled cross terms 2 y_k y_l
   row by row, keeping only bits at or above 2^-28. Our 0.1.0 code instead formed y0^2 as an
   ordinary truncated product with rows over y0, flooring each row. The pre-registration had
   already flagged this as a known difference.
2. We read a public re-implementation of the reference builder, `tasks/vqcc_invsqrt/
   init_program.py` in github.com/somfieao/kickmix-compiler (read 2026-10-28). It is not the
   official generator, which ships only with Kaggle's data. Every other stage matches our
   emulator bit for bit in its index arithmetic: the 14 bits of Delta x (including the
   0.5-weight bit, computed as an AND), the Horner rows, the mantissa multiply (rows over all 22
   bits of x_norm), 3 - z as bitwise NOT plus (3 << 28) + 1, and the final multiply (rows over
   y0's 17 bits). Only the squaring differs.
3. The size and place of the miss fit that difference. A floored y0^2 is too small, which makes
   3 - z and so p too large by about (x_norm / 2) times the squaring's error in 2^-28 units. That
   is largest near x_norm = 4, exactly where our worst input sits (x_norm = 3.993). With rows
   over y0, six rows are truncated, losing up to about 6 units. The symmetric form drops at most
   2.016 units.
4. A side finding: with the builder's row rule (one Toffoli per kept AND, plus width - 1 for
   each in-place adder over the target's bits from the row's lowest position up), our cost model
   reproduces all four of the paper's stage counts **exactly**: Horner 3 x (133 + 224) = 1,071,
   squaring 130 + 312 = 442, mantissa 406 + 637 = 1,043, and final 374 + 493 = 867. We worked
   this out by hand from the register widths before any new job ran. It is now a unit test, not
   a prediction. Our 0.1.0 rule charged a full accumulator-wide adder per row, which is why Q4
   held only approximately.

`isqrt_emul.py` 0.2.0 adds the symmetric square (now the default), keeps the 0.1.0 reading as
`square="rows"` for comparison, and switches to the builder's row rule. Whether it reproduces
the paper's worst input and error is tested by the pre-registered job `qcc-emul-v2`
(`PREREGISTRATION-emul2.md`). Until that job is graded, the emulator is not trusted as an error
oracle.

## What Q6 means

As pre-registered: plain piecewise polynomials with normalization and no Newton step, as
modeled, reach about 3.6x the reference. Public entries report about 19x on this task. We will
not tune this family further.

Contact: MV2, Munim, Inc., mv2@munimtech.com
