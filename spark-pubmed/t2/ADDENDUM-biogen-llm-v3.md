# Addendum: biogen-llm-v3 (re-file after a host stop; v2's completed steps recorded)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
13:45 UTC, before `biogen-llm-v3` runs. `PREREGISTRATION-biogen-llm-v2.md` is unchanged and
governs v3.

## What happened to v2

`biogen-llm-v2` ran on the Blade (2026-10-30, 07:41-08:22 UTC). Its last step, the judge, was cut
off with exit 143 (SIGTERM from outside the job) at 600 of the 1,389 judged pairs, with peak
memory at 3.21 of 4 GB, so this was not an out-of-memory kill (that would be 137). The
pre-registration's rule for 143 is "re-file unchanged", so `biogen-llm-v3` has the same six code
files (copied byte for byte), setup, run steps, 2 CPUs, 4 GB and 480 minutes. v2 wrote no
`llm.json`, so G1-G7 and the decision rule are graded on v3 only.

## v2's finished steps (recorded now, regraded on v3)

These steps finished before the stop. Their predictions are graded here against v2's own outputs
(`results-biogen-llm-v2/bench.json`, `model.json`). `RESULTS-biogen-llm-v2.md` will give both v2's
and v3's readings.

- **C1.** `fetch_code.py` exit 0; the five test modules ran 31 tests, OK. Held.
- **C2.** `model.json`: all 8 pinned files present at their pinned sizes (`model.safetensors`
  988,097,824 bytes), `problems` empty. Held.
- **B1.** float32 at 2 threads: median pass 3.25 s (passes 3.25, 3.36, 3.03; warm-up 5.67 s),
  inside 1-15 s. Held.
- **B2.** bfloat16 at 2 threads: median 91.75 s (warm-up 95.21 s, under the 120 s cap), 28.2 times
  the float32 median. The prediction was at least 3 times. Held.
- **B3.** float32 at 4 threads: median 3.74 s, which is 1.15 times the 2-thread median. The bar
  was at least 0.9 times, so 4 threads were not faster on a 2-CPU limit. Held.

The prompt was 335 tokens and the container saw a 2.0-CPU limit. bfloat16 at 4 threads took a
median of 102.71 s. So v1's 189.1 s per pair came mostly from bfloat16, not from thread
oversubscription. By the fixed rule (B2 holds), every later CPU job in this project loads weights
in float32. This describes one shared host and one 335-token prompt. It is not a general claim
about CPUs.

Before the stop, the judge's probe measured 2.3 s per pair over 1,389 pairs. Its log read 600
pairs at 1,320 s (2.2 s per pair), so v3 should finish the judge in about an hour. These are
progress lines only; G7 is graded on v3's `ms_per_judged_pair`.

Contact: MV2, Munim, Inc., mv2@munimtech.com
