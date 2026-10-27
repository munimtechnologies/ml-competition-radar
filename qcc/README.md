# qcc: Google Quantum AI "Verifiable Quantum Circuit Compilation" (Kaggle)

Work of AI agents in the name of MV2 of Munim, Inc. Apache-2.0. Written 2026-10-27, updated the
same day (second run).

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
- Seen in public: one team 1.11751 (rank 710, Oct 25); another 1.54586 from invsqrt alone
  (3.694x); a public log reaching 13.725, with invsqrt at 78 qubits and 1,696 Toffoli-equivalents;
  about 980 teams.

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
  relative error 2^-25.07):
  1. Normalize x by pairs of leading zeros (unary shift register, CSWAP lanes; n_p(n_p+2)
     Toffoli-equivalents forward).
  2. Piecewise cubic first guess from a 4-way QROM, 17 fractional bits.
  3. One Newton step, p = y0(3 - x_norm y0^2)/2, with truncated multipliers (Horner 1,071,
     squaring 442, mantissa multiply 1,043, final multiply 867 Toffolis).
  4. Denormalize with 30 n_p CSWAPs, apply one Z_POW per bit of y1 (F = 30 + n_p = 40 fractional
     bits), then uncompute everything in reverse.
- The relative tolerance is the hard part. At x near 3.1 million the absolute tolerance is about
  2^-34.8 turns, so the phase needs about 35 correct fractional bits. The reference uses about
  1 bit of slack.

## Blockers

Kaggle needs MV2's account to accept the rules and, as found for CASMI on 2026-10-14, a Persona
live-selfie identity check before submitting. The data (reference circuits, verifiers, about
1 GB) can be downloaded only after the rules are accepted. Both go to Sheehan.

## Toolchain jobs (probes, not experiments)

- `qcc-kickmix-v1` (2026-10-27 15:32 UTC, 165 s): **failed in the build**. The image has g++
  14.2.0 (not 12). pip, the clone and the checkout of Qualtran at 638777f worked. About 75 of the
  translation units compiled, then cc1plus processes were killed for lack of memory under the
  3 GB cap. Cause: kickmix's `setup.py` calls pybind11's `ParallelCompile()` without an
  environment variable, so it starts one compiler per host CPU, whatever the container's CPU
  limit.
- `qcc-kickmix-v2` (filed 2026-10-27): the same job, with one setup line that changes the
  checkout's `ParallelCompile()` to `ParallelCompile(default=1)` (serial compilation) and a
  `grep` that confirms the change. Timeout 150 minutes.
- The Python API reference is also published in Qualtran at `docs/kickmix/api_reference.md`. It
  shows `CircuitBuilder` (alloc_qubits, create_quantum_register, ccx, cswap, init_and/del_and,
  hmr, iadd/isub, init_lookup/del_lookup, z_pow, finish_circuit), `Circuit.from_file/to_file`
  (kmx/kmb) with `operation_statistics()`, and a `Simulator`.

## Next

Once kickmix builds: a fixed-point emulator for the invsqrt pipeline in numpy (bit widths,
segments, truncation) that checks all 3,133,452 inputs against the tolerance and counts Toffolis
with the paper's cost formulas. Variants can then be screened before any circuit is written. No
submission is possible until the Kaggle account exists.
