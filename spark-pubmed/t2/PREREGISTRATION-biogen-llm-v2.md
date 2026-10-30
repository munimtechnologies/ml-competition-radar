# Pre-registration: biogen-llm-v2 (a smaller open LLM as a gated conflict judge, plus a timing check)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
06:45 UTC, before the job runs. The job's workdir carries a copy of this file.

## Why there is a v2

`biogen-llm-v1` (Qwen2.5-1.5B-Instruct, bfloat16, 4 torch threads on a 2-CPU limit) stopped at
its speed probe: 189.1 s per judged pair, projecting far past 6 hours (`RESULTS-biogen-llm.md`).
Its fixed rule says v2 uses Qwen2.5-0.5B-Instruct. v2 also runs in float32 with 2 threads, and
first times those two choices on their own, because v1's slowness is more than model size alone
explains.

## Question

Same as v1. Inside the negation gate (1,432 judgments: 140 Contradicts, 185 Neutral, 1,107
Supports), can a small instruction-tuned LLM tell the contradicting passages apart well enough to
beat the best NLI flag overall (entry F1 0.218)? And, separately: was v1 slow because of
bfloat16, because of thread oversubscription, or neither?

## Job

`biogen-llm-v2`, kind `compete`, image `python:3.12`, 2 CPUs, 4 GB, 480 min, volume
`pubmed-baseline` (`/data/biogen2024/assessments.json`, as in v1).

- Model: `Qwen/Qwen2.5-0.5B-Instruct` at revision `7ae557604adf67be50417f59c2c2f167def9a775`,
  licence Apache-2.0 (Hugging Face card), 8 files with pinned sizes (`model.safetensors`
  988,097,824 bytes), float32 on the CPU, torch 2.5.1+cpu, transformers 4.46.3, accelerate 1.1.1.
- `llm_judge.py` 0.2.0: v1's prompt, letters, gate, probe and scoring, unchanged. Only the model
  (`--model qwen2.5-0.5b`), dtype (`--dtype float32`) and threads (`--threads 2`) differ. The
  report adds `probe_s_per_pair`, `cpu_limit` and `torch_threads`.
- `bench_dtype.py` 0.1.0 runs before the judge: one fixed made-up prompt (250-word passage), a
  warm-up and 3 timed forward passes for float32 and bfloat16 at 2 and 4 threads, each in turn. A
  configuration whose warm-up takes over 120 s gets no timed passes.
- Scoring: `nli_check.py` 0.2.0's `run()` unchanged (commit 29d7d00c, fetched by `fetch_code.py`
  0.4.0). The probe stops the run after 20 judged pairs if the projection is over 6 h.

## Checks (the job stops, rather than grades, if one is false)

- C1. `fetch_code.py` exits 0. Tests: `test_fetch_code` 6, `test_llm_judge` 7, `test_nli_check`
  10, `test_cue_check` 6, `test_bench_dtype` 2, all pass (31).
- C2. `model.json`: every pinned file present at its pinned size, `problems` empty.
- C3. `llm.json` counts equal v1's and biogen-nli-large-v1's: 14,763 judgments, 0 unknown labels,
  11,927 scored, 11,592 unique pairs, census 202 contradicting topic-papers, 168 mixed.

## Predictions (graded to the letter in `RESULTS-biogen-llm-v2.md`)

Timing (`bench.json`):

- **B1.** float32 at 2 threads: median pass between 1 and 15 s.
- **B2.** bfloat16 at 2 threads is at least 3 times slower than float32 at 2 threads (or its
  warm-up passes the 120 s cap).
- **B3.** float32 at 4 threads is not more than 10% faster than float32 at 2 threads (median at
  least 0.9 times the 2-thread median), since the container has 2 CPUs.

Judge (`llm.json`):

- **G1.** `gate`: 1,432 judgments, labels exactly 140 Contradicts, 185 Neutral, 1,107 Supports.
- **G2.** `scoring.judged` is exactly 1,389 (v1's probe counted it).
- **G3.** `letter_mass_mean` at least 0.5.
- **G4.** Inside the gate, Contradicts-vs-rest AUROC (`gate.entry.contradicts_vs_rest.auroc`)
  between 0.50 and 0.70 (a 0.5B model is expected to be weak).
- **G5.** Overall entry Contradicts-vs-rest argmax F1 below 0.25, so the adoption rule fails.
- **G6.** Its argmax recall is at most 0.509 (the gate's ceiling).
- **G7.** The probe does not stop the run, and `ms_per_judged_pair` is between 1,000 and 15,000.

Recorded, not predicted: argmax precision, slot and topic-paper blocks, best-F1 oracle, the
`union_polarity_clash` fusion, the gate's confusion matrix, `clipped`, `cpu_limit`, the bfloat16
and 4-thread timings, peak memory.

## Decision rule (fixed now, same bar as v1)

The LLM flag is adopted as the Task 2 conflict-flag candidate (run only where the negation gate
passes) only if all three hold: entry argmax F1 at least 0.25, entry argmax precision at least
0.30, and `ms_per_judged_pair` at most 10,000. Otherwise the composer keeps the polarity-clash
flag, the result is written up as found, and no larger LLM is tried on the shared CPUs. If B2
holds, every later CPU job in this project loads weights in float32. Exit 137: v3 at 6 GB.
Exit 143/255: re-file unchanged. Probe stop: no v3; written up as found.

## Limits

One prompt, one small model, no tuning: a negative result says this setup fails, not that LLM
judges do. The timing check uses one made-up prompt on whichever host runs the job, so it
describes that machine, not CPUs in general; and v1 and v2 differ in model size as well as dtype
and threads. The labels are BioGen 2024's passage-level judgments, whose own between-slot
agreement on Contradicts is 0.39. Questions and passages are BioGen's, not SPARK's. Only counts and
scores are published, never passage or sentence text. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
