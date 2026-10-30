# Addendum: t2sys-v4 (third re-file, written before v4 runs)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
08:20 UTC, before `t2sys-v4` runs. `PREREGISTRATION-t2sys.md`, `ADDENDUM-t2sys-v2.md` and
`ADDENDUM-t2sys-v3.md` are unchanged.

`t2sys-v3` also ran on the Dell (2026-10-30, 07:56-08:04 UTC). Setup passed and all four test
steps passed with the counts the v2 addendum gave (14; 12; 11; 9 run with 1 skipped), and `host_guard.py` stopped it with exit 3 for the same reason as v1 and v2: the Dell's
index copy holds 112 files and 3,360,000 records, below the 1,306 files and 39,167,523 records
the full index has. The runner picks the host by free memory, so where a job lands is outside the
job's control; v1, v2 and v3 all landed on the Dell. The rule says "re-file unchanged", so
`t2sys-v4` has the same files, setup and run steps, 2 CPUs, 3 GB and 240 minutes. No prediction,
threshold or rule changes.

Contact: MV2, Munim, Inc., mv2@munimtech.com
