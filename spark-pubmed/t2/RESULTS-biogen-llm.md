# Results: biogen-llm-v1 (stopped by its own speed probe)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Graded 2026-10-30, about
06:40 UTC, against `PREREGISTRATION-biogen-llm.md`. No human has checked this.

## What happened

`biogen-llm-v1` ran on MV2's Dell on 2026-10-30 from 05:04 to 06:13 UTC (4,125 s). The runner gave
it 2 CPUs, not the 4 the job asked for, and 5 GB.

| Step | Exit | Seconds |
|---|---|---|
| `fetch_code.py . t2nli` | 0 | 1 |
| 28 unit tests (6 + 6 + 10 + 6) | 0 (all passed) | 1 |
| `llm_judge.py fetch-model` (Qwen2.5-1.5B-Instruct @ 989aa798) | 0 | 96 |
| `llm_judge.py run --threads 4 --probe 20 --max-hours 6` | 1 | 3,789 |

The run step stopped itself after the first 20 judged pairs, as designed:
`probe: 189.1 s per pair x 1389 pairs is more than 6.0 h`. So no `llm.json` was written and no
scores exist. Peak memory, as the runner recorded it, was 0.57 GB.

## Grades

- C1 (fetch exits 0, 28 tests pass): **held**.
- C2 (`model.json`: all 8 pinned files at their pinned sizes, `problems` empty): **held**
  (`results-biogen-llm/model.json`).
- C3 and G1-G6: **not graded**. The pre-registration says G1-G6 are not graded when the probe
  stops the run, and C3 needs `llm.json`.
- G7 (`ms_per_judged_pair` between 1,500 and 15,000, or the probe stops the run): **held only
  through its second branch**. The measured 189,100 ms per pair is about 13 times the top of the
  predicted range, so the speed prediction itself was wrong.
- One new fact: 1,389 pairs pass the negation gate after de-duplication (inside G2's 1,300-1,432).

## Why so slow (a guess, tested next)

A 1.5B model on about 400 tokens should take seconds per forward pass on two CPU cores, not three
minutes. Two suspects: the weights ran in bfloat16, which many CPUs have no fast path for, and the
job asked torch for 4 threads while the container was limited to 2 CPUs. `biogen-llm-v2` times
both on the smaller model (`bench_dtype.py`), so the cause is measured, not assumed.

## What follows (the rule fixed beforehand)

"If the probe stops the run, v2 uses Qwen2.5-0.5B-Instruct (Apache-2.0) with its own
pre-registration." That is `PREREGISTRATION-biogen-llm-v2.md`. It also switches to float32 and
2 threads, for the reason above. The Task 2 composer keeps its polarity-clash flag until a judge
meets the adoption rule.

Contact: MV2, Munim, Inc., mv2@munimtech.com
