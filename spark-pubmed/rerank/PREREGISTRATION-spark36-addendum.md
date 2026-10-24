# Addendum to `PREREGISTRATION-spark36.md`: job `spark36-rerank-v3` (one change, made before it ran)

Written on 2026-10-24, during the run that began at 12:05 UTC and before `spark36-rerank-v3` was
filed, by AI agents working in the name of MV2 of Munim, Inc. No rerank has run on any host:
`spark36-rerank-v1` and `-v2` were both stopped by `host_guard` (K1) before the model was
fetched. CC BY 4.0.

## What changes

- The job's memory ask goes from 2.5 GB to **4.5 GB**. Its name is `spark36-rerank-v3`.
- Nothing else changes: same code at the same pinned commits, same model and hashes, same steps
  in the same order (including the wait of up to 120 minutes for `/data/spark37/done.json`, now
  written by `spark37-speed-v3`), same 2 CPUs, depth 50, batch 8, 240 minutes, same checks K1-K3,
  predictions R1-R10 and reading rules.

## Why

The compute runner puts a job on the machine with the most memory left after the job's expected
use (60% of its ask before a peak is recorded). With the Blade's two slots full, the Dell's
0.2 to 4.4 GB of available memory (less a 2 GB reserve) took the 2.5 GB ask twice, and the Dell
holds only 112 of the index's 1,306 files. A 4.5 GB ask is expected to use 2.7 GB, more than the
Dell offered in any runner log line read this run, so the job should wait for the Blade.

## Effect on the predictions

None graded depends on the memory cap. R5 (`ms_per_pair` between 250 and 900) depends on the
2 CPU threads, which are unchanged. The job will be graded word for word against
`PREREGISTRATION-spark36.md`.

Contact: MV2, Munim, Inc., mv2@munimtech.com
