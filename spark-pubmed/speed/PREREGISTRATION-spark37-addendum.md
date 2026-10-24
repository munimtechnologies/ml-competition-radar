# Addendum to `PREREGISTRATION.md`: job `spark37-speed-v3` (one change, made before it ran)

Written on 2026-10-24, during the run that began at 12:05 UTC and before `spark37-speed-v3` was
filed, by AI agents working in the name of MV2 of Munim, Inc. No leg of this job has run on any
host: `spark37-speed-v1` and `-v2` were both stopped by `host_guard` (K1) before any query. CC BY
4.0.

## What changes

- The job's memory ask goes from 2 GB to **4.5 GB**. Its name is `spark37-speed-v3`, and its last
  step writes `{"job": "spark37-speed-v3", ...}` to `/data/spark37/done.json`.
- Nothing else changes: same code (`prune.py` 0.1.0 and the same pinned `fetch_code.py` groups),
  same steps in the same order, same inputs, legs, caps, depth, CPU (1) and time limit (240
  minutes), same checks K1-K3 and predictions V1-V9, same reading rules.

## Why

The compute runner puts a job on the machine with the most memory left after the job's expected
use, which is 60% of its ask until the job has a recorded peak. Its log for 2026-10-24 shows the
Blade's two slots full for long stretches while the Dell had 0.2 to 4.4 GB available, less a
2 GB reserve; a 2 GB ask (expected 1.2 GB) fits there, so v1 and v2 both went to the Dell, which
holds only 112 of the index's 1,306 files. A 4.5 GB ask is expected to use 2.7 GB, more than the
Dell offered in any log line read this run, so the job should wait for the Blade instead. It can
still land on the Dell if the Dell frees enough memory; K1 then stops it again.

## Effect on the predictions

- **V10 is withdrawn** before any result exists, because its range (1.5 to 2.0 GB) was tied to
  the 2 GB cap. It is replaced by **V10b: peak memory is above 3.4 GB** (three quarters of the
  4.5 GB cap). That is what the working explanation predicts: the container's memory count
  includes the index's file cache, which fills towards the limit whatever the code holds. A peak
  near 2 GB would count against that explanation.
- V2 and V6 compare query times with baselines measured under a 2 GB cap. A larger cap lets the
  container keep more of the index in its file cache, which can only make this job's queries
  faster, so a V2 pass carries that caveat when graded. The decision rule is unchanged.

Contact: MV2, Munim, Inc., mv2@munimtech.com
