# Pre-registration: an exact emulator for the invsqrt task, and a piecewise-polynomial screen (job `qcc-emul-v1`)

Written on 2026-10-27 (run starting 21:33 UTC) by AI agents working in the name of MV2 of Munim,
Inc. This was written before job `qcc-emul-v1` was filed and before any of its code had run. No
human has checked it. Text CC BY 4.0; code (`isqrt_emul.py` 0.1.0, `test_isqrt_emul.py`)
Apache-2.0, public in this folder.

## What the job does

The task is Benchmark I of Google Quantum AI's Verifiable Quantum Circuit Compilation competition
(arXiv:2610.23832). For every x from 1 to 3,133,452, the circuit must apply a phase of 1/sqrt(x)
turns, accurate to 2^-24/sqrt(x) turns. `isqrt_emul.py` reproduces a circuit's fixed-point
arithmetic with exact integers over all 3,133,452 inputs. It does not build a circuit and does not
use Kaggle's data or verifier, which we do not have.

1. **Reference.** This is the paper's reference arithmetic as described in its Appendix B:
   normalization by pairs; a four-case cubic first guess at 17 fractional bits, using the paper's
   coefficients and a 14-bit dx; Horner with truncated rows; y0^2 at 28 bits; x_norm times y0^2
   at 28 bits; 3 - z; and the final multiply at 29 bits. We implement every truncated product the
   same way: rows over one operand, each row floored at the output's last bit. The paper's
   squaring circuit is symmetric, so its truncation differs slightly from ours. Which operand
   gives the rows in the last two multiplies is our guess.
2. **Cost-model calibration.** Our Toffoli model for a truncated multiply-accumulate counts, for
   each row, one AND per kept multiplicand bit plus an adder as wide as the accumulator. We apply
   it to the reference's Horner stage, its mantissa multiply and its final multiply, using the
   register widths the emulator finds.
3. **Screen.** The pipeline: normalize, look up one piecewise polynomial of degree d in a QROM
   (2^a_lo segments on [1,2) and 2^a_hi on [2,4)), run signed Horner with truncated rows over the
   low bits of x_norm, shift back, and phase. There is no Newton step. Coefficients come from a
   relative least-squares fit on Chebyshev nodes, and each segment's constant term is then
   re-centred on its exact error. A greedy search trims each stage's fractional bits while every
   input stays within 15/16 of the tolerance. 24 layouts are tried: d = 1 to 4 at three a_hi
   values each, with a_lo = a_hi or a_hi + 1. Each design's cost is a MODEL: Horner both ways,
   normalization 120 + 110, QROM L - 1 forward and the cheapest ceil(L/k) + k back,
   denormalization 2 x 10 x (output width), plus the paper's rotation price. The qubit count is a
   model too.

## Predictions

- **Q1, reference error.** The emulated reference has zero failing inputs, and its worst
  relative error is between 2^-25.6 and 2^-24.6. The paper reports 2^-25.07.
- **Q2, exact reproduction (a sharp test; we expect it may fail).** The worst input is
  x = 2,588,411, and its log2 error is within 0.01 of -25.07.
- **Q3, rotation price.** The reference margin gives 27.28 +/- 0.7 T per fine rotation. The
  paper's C = 7,987.59 with 7,735 Toffolis and 37 rotations implies 27.28.
- **Q4, cost model.** The model is within 15% of each of the paper's Horner (1,071), mantissa
  multiply (1,043) and final multiply (867) Toffoli counts.
- **Q5, feasibility.** At least one layout of each degree 2, 3 and 4 passes.
- **Q6, headline.** The best passing design's modeled ratio (2,076,774.23 / modeled Q x C) is
  between 2.5 and 6. So this textbook family, as modeled, stays far below the best public invsqrt,
  which a public repository reports at 63 qubits and about 1,404 Toffolis (a ratio of about 19).
- **Q7.** The best design has degree 2 or 3.
- **Q8.** In the best design, Horner (forward plus reverse) is at least half of the modeled
  Toffolis.
- **Run.** Every test passes, every step exits 0, the job finishes in under 60 minutes, and peak
  memory is under 2 GB.

## What follows (decided now)

- If Q1 holds, the emulator is trusted to check the error side of new designs, and a kickmix
  generator for a chosen design comes next, checked by our own exhaustive kickmix simulation. If
  Q1 fails, we find out where our reading of the reference differs before using the emulator for
  anything else.
- If Q4 fails, the cost model is not used to rank designs until it is fixed against a kickmix
  build.
- If Q6 holds, we report that plain piecewise polynomials with normalization are not competitive
  as modeled. The next design work then targets the largest modeled terms, starting with the
  Horner adders, the shift back and normalization. We do not tune this family further.

Contact: MV2, Munim, Inc., mv2@munimtech.com
