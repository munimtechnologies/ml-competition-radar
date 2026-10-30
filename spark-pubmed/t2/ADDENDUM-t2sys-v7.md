# Addendum: t2sys-v7 (sixth re-file; memory ask raised from 4 to 5 GB, written before v7 runs)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
19:30 UTC, before `t2sys-v7` runs. `PREREGISTRATION-t2sys.md` and the v2-v6 addenda are
unchanged.

`t2sys-v6` also ran on the Dell (2026-10-30, 15:34-15:43 UTC, 539 s), even with its 4 GB ask.
Setup passed and all four test steps passed. Then `host_guard.py` stopped it with exit 3 for the
sixth time: the Dell's index copy holds 112 files and 3,360,000 records (last file
`pubmed27n0112.xml.gz`), below the 1,306 files and 39,167,523 records of the full index
(`results-t2sys-v6/guard.json`).

So the 4 GB ask did not move the job, and the earlier 4 GB jobs that ran on the Blade did so
because of how much memory each machine had free at that moment, not because of the size of the
ask alone. `t2sys-v7` asks for 5 GB, once. This is a placement change only: the same six files
(copied byte for byte), setup, run steps, 2 CPUs and 240 minutes. No prediction, threshold or rule
changes; R2's "peak at most 3 GB" still stands. If v7 also lands on the Dell, the guard will stop
it again before any prediction is tested, and no further blind re-file follows: the job waits
until a run can be placed on the machine with the full index.

Contact: MV2, Munim, Inc., mv2@munimtech.com
