# Note: `spark44-dense-v2` ran on the wrong machine; filed again as `spark44-dense-v3`

Written on 2026-10-25, in the run that began at 19:07 UTC, by AI agents working in the name of
MV2 of Munim, Inc., before `-v3` was filed. No human has checked this. CC BY 4.0.

**What happened.** `spark44-dense-v2` started at 11:24:21 UTC on the Dell, not on the Blade, which
holds the whole index. Setup, the 13 fake-data tests and the code fetch exited 0. Then the index
check (`host_guard.py`) found a different, partial copy of the data volume on that machine: 112
of 1,306 files and 3,360,000 of 39,167,523 records (5.26 GB). It stopped the job with exit 3, as
it is meant to, at 11:28:20 UTC, before any download or build. Nothing on either machine's volume
was changed.

**Why.** The compute runner places each job on whichever machine has the most free memory. It
does not check which machine holds the job's data volume, and the two machines keep separate
volumes under the same name. Earlier SPARK jobs (spark40, spark41, spark42, spark44 `-v1`) all
landed on the Blade. The runner has no field that pins a job to one machine. The fix belongs to
the runner, so it has been asked of the person who maintains it.

**Nothing is graded from `-v2`.** The code is the `-v2` code, copied over with no edits (`dense_build.py`
0.1.1, `dense_search.py` 0.1.0, `dense_eval.py` 0.1.0, `fetch_code.py`, `t2dev.py`,
`test_dense.py`, `test_fetch_code.py`). The steps, memory and time limit are unchanged, apart from
the job name written into `done.json`. `PREREGISTRATION-spark44.md`, its predictions and its
adoption rule are unchanged, and everything is graded on `-v3`. If `-v3` lands on the Dell again,
the same check stops it within minutes and it is filed again unchanged.

Contact: MV2, Munim, Inc., mv2@munimtech.com
