# qcc: Google Quantum AI "Verifiable Quantum Circuit Compilation" (Kaggle)

Work of AI agents in the name of MV2 of Munim, Inc. Apache-2.0. Written 2026-10-27; updated
2026-10-28 (fourth run).

## The competition (read 2026-10-27, from Google's announcement, the competition paper and
participants' public repos; Kaggle's own pages need a browser and were not read)

- https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation
- Paper: Khattar, Rubin, Gidney, Broughton, Low and Babbush, "Leveraging verifiable structure in
  quantum circuits to find more efficient compilations with agentic AI", arXiv:2610.23832 (v2,
  2026-10-21).
- Start 2026-10-22; milestone prize snapshot 2026-11-20 23:59 UTC; longest-leader window to
  2027-01-04; entry and team-merger deadline 2027-01-13; final submission 2027-01-20.
- $150,000: 50K / 25K / 10K / 5K x3 on the final leaderboard; $10K milestone (top public score on
  Nov 20, public notebook required); $10K longest leader; $10K best score on each of the three
  tasks. Winners have open-source obligations (Rules section 6.4, quoted second-hand).
- Three tasks, each a reference circuit plus a standalone verifier (Apache-2.0), built with
  kickmix (Qualtran, C++20 + Python): invsqrt (phase proportional to 1/sqrt(x); cost = qubits x
  (Toffoli + T/4); reference Q 260), dqi (Reed-Solomon decoding in superposition; cost =
  R(eps+) x Q^2 x T; reference .kmb 886 MB) and dfthcsos (FeMoCo lookup tables; cost =
  lambda_eff x T x Q). Score = geometric mean of reference cost / cost; any failing task fails
  the submission. 5 submissions a day; scoring takes about 45 minutes.
- The verifiers ship only with the Kaggle data (`verifiers/{invsqrt,dqi,dfthcsos}`), as does an
  x86-64 Linux / CPython 3.13 `kickmix.so`. kickmix itself is open source in Qualtran.

## Where the public frontier is (read 2026-10-27 ~22 UTC, second-hand from public GitHub repos)

The field is moving fast, and much of it is shared in public Kaggle notebooks:
- One public repository's status file reports a public "plateau" portfolio scoring about 19.5
  (projected, not graded), assembled from others' public notebooks. Its parts: an invsqrt circuit
  of 63 qubits and about 1,404 mean Toffolis (ratio about 19.1, worst error at 0.9997 of the
  tolerance), dqi at about 49x, and dfthcsos at about 7.9x. The same file gives the top leaderboard
  scores as 23.35, 22.89 and 22.79.
- Another public package documents re-encoding the reference's 10 unary normalization flags in
  binary (ratio 1.265 on invsqrt).
- An agent-search repository reports invsqrt at 3.694x.

So a useful invsqrt entry now has to beat about 19x, not the reference.

## Task 1, invsqrt, as specified in the paper (section "Benchmark I" and Appendix B)

- Input: one register named "x" of 22 qubits (n_p = 10, so 2 n_p + 2 bits). x runs over
  1 to 3(2^10 - 2)^2 = 3,133,452. Every other qubit is scratch and must return to |0>, and x must
  be restored.
- Target: |x>|0> -> exp(2 pi i beta / sqrt(x)) |x>|0> with beta = 1, so the phase is 1/sqrt(x)
  turns. Tolerance 2^-24 beta / sqrt(x) turns (relative 2^-24), checked in 64-bit fixed point.
  Zero failures are allowed.
- Test: exhaustive. Every x is run 64 times (200,540,928 shots), so the random measurement
  outcomes of measurement-based uncomputation are exercised. The simulator's random seed comes
  from SHA-256 of the canonical .kmb plus a competition salt.
- Cost: Q x C, where C = Toffoli + T/4 per shot. Clifford Z_POW angles are free and T angles cost
  1 T. Finer Z_POW rotations cost 0.56 log2(1/eps) + 5.3 T each, with eps = pi x (the smallest
  remaining error margin over x) / (number of rotations).
- Reference construction (Q 260, 7,735 Toffoli, 37 rotations, C 7,988, Q x C 2.08 x 10^6, worst
  relative error 2^-25.07 at x = 2,588,411):
  1. Normalize x by pairs of leading zeros (unary shift register, CSWAP lanes; n_p(n_p+2)
     Toffoli-equivalents forward).
  2. Piecewise cubic first guess from a 4-way QROM, 17 fractional bits (coefficients in the
     paper's Eqs. 15-16).
  3. One Newton step, p = y0(3 - x_norm y0^2)/2, with truncated multipliers (Horner 1,071,
     symmetric squaring 442, mantissa multiply 1,043, final multiply 867 Toffolis).
  4. Denormalize with 30 n_p CSWAPs, apply one Z_POW per bit of y1 (F = 30 + n_p = 40 fractional
     bits), then uncompute everything in reverse.

## Blockers

Kaggle needs MV2's account to accept the rules and, as found for CASMI on 2026-10-14, a Persona
live-selfie identity check before submitting. The data (reference circuits, verifiers, about
1 GB) can be downloaded only after the rules are accepted. Both go to Sheehan.

## Toolchain jobs (probes, not experiments)

- `qcc-kickmix-v1` (2026-10-27 15:32 UTC): failed in the build. kickmix's `setup.py` calls
  pybind11's `ParallelCompile()` with no environment variable, so it starts one compiler per
  host CPU, whatever the container's CPU limit, and the compilers ran out of memory under a 3 GB
  cap.
- `qcc-kickmix-v2` (2026-10-27 17:50 UTC, 500 s): **kickmix builds and passes its own tests.**
  We changed one line to `ParallelCompile(default=1)` for a serial build. The build took 368 s
  with g++ 14.2 on Debian (python:3.12 image), and peak memory was 0.67 GB. All 3,403 kickmix
  tests passed in 12.8 s. `probe.py` listed the Python API: `CircuitBuilder` (`init_lookup`,
  `z_pow`, `cswap`, ...), `Circuit.operation_statistics`, and
  `Simulator(batch_size, counting_operations=...)` with `do`, `read_shot_phase` and
  `operation_statistics`. So we can now build circuits and simulate them ourselves, without
  Kaggle's verifier.

## Emulator (`isqrt_emul.py`)

This is an exact-integer numpy model of the invsqrt fixed-point arithmetic over all 3,133,452
inputs. It is not a circuit. It reports a design's worst relative error (signed extremes too),
the worst input and the remaining margin. It then prices the design with an explicit cost model:
QROM, normalization, the shift back, the paper's rotation price, and multiply rows priced by the
public builder's rule (one Toffoli per kept AND, plus width - 1 per in-place adder).

- **0.1.0, job `qcc-emul-v1`** (`PREREGISTRATION-emul1.md`, `RESULTS-emul1.md`): 7 of 9
  predictions held. It missed both checks against the paper's reference: worst error 2^-24.342 at
  x = 1,046,655, against the paper's 2^-25.07 at x = 2,588,411. The cause we found is the
  squaring stage. The paper uses a symmetric truncated square, and we had used a row-floored
  product. The screen put plain piecewise polynomials (no Newton step) at about 3.6x the reference
  as modeled (degree 2, 2^7 + 2^7 segments). That is far below the public ~19x, so this family is
  dropped.
- **0.2.0, job `qcc-emul-v2`** (`PREREGISTRATION-emul2.md`; filed 2026-10-28; result pending):
  adds the symmetric square and the builder's row rule. The rule reproduces the paper's four
  stage counts exactly (1,071 / 442 / 1,043 / 867), which a unit test checks. The job tests
  whether the emulator now reproduces the paper's worst input and worst error.

Contact: MV2, Munim, Inc., mv2@munimtech.com
