# Addendum: t2sys-v5 (fourth re-file, written before v5 runs)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
13:45 UTC, before `t2sys-v5` runs. `PREREGISTRATION-t2sys.md` and the v2, v3 and v4 addenda are
unchanged.

`t2sys-v4` also ran on the Dell (2026-10-30, 09:43-09:48 UTC, 315 s, peak 0.35 GB). Setup passed
and all four test steps passed with the counts the v2 addendum gave (14; 12; 11; 9 run with 1
skipped). Then `host_guard.py` stopped it with exit 3 for the same reason as v1, v2 and v3: the
Dell's index copy holds 112 files and 3,360,000 records (last file `pubmed27n0112.xml.gz`), below
the 1,306 files and 39,167,523 records of the full index.

All four runs landed on the same machine (01:33, 04:58, 07:56 and 09:43 UTC on 2026-10-30). The
runner chooses the machine by free memory, and a job cannot name one. The guard did its job each
time: it stopped the run within a few seconds of the tests and before any prediction could be
tested on the wrong index. `t2sys-v5` therefore has the same files, setup and run steps, 2 CPUs,
3 GB and 240 minutes. MV2 has asked for a way to pin a job to the machine that holds the full
index. No prediction, threshold or rule changes.

Contact: MV2, Munim, Inc., mv2@munimtech.com
