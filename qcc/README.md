# qcc: Google Quantum AI "Verifiable Quantum Circuit Compilation" (Kaggle)

Work of AI agents in the name of MV2 of Munim, Inc. Apache-2.0. Written 2026-10-27.

## The competition (read 2026-10-27, from Google's announcement, The Quantum Insider and two
participants' public repos; Kaggle's own pages need a browser and were not read)

- https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation
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
- Seen in public: one team 1.11751 (rank 710, Oct 25); another 1.54586 from invsqrt alone
  (3.694x); a reported top score near 13.7 (Oct 26); about 980 teams.
- The competition invites AI coding agents explicitly. Fuzz-test verification runs on CPU.

## Blockers

Kaggle needs MV2's account to accept the rules and, as found for CASMI on 2026-10-14, a Persona
live-selfie identity check before submitting. The data (reference circuits, verifiers, about
1 GB) download only after the rules are accepted. Both go to Sheehan.

## Job qcc-kickmix-v1 (toolchain probe; not an experiment)

Builds kickmix from Qualtran at 638777f (2026-10-22) in python:3.12 with its own g++, runs the
probe's 3 fake-data tests, records the Python API (`api.json`, `api.txt`) and runs kickmix's own
tests. What it should show: g++ 12 builds it (the C++20 feature that broke Apple clang 15,
P0960, is in GCC since 10), the build takes under 30 minutes on 2 CPUs, and the tests pass.
If the build fails on g++ 12, the next version uses a newer compiler image instead.
