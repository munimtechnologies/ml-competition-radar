# Addendum: t2sys-v6 (fifth re-file; memory ask raised from 3 to 4 GB, written before v6 runs)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
15:40 UTC, before `t2sys-v6` runs. `PREREGISTRATION-t2sys.md` and the v2-v5 addenda are
unchanged.

`t2sys-v5` also ran on the Dell (2026-10-30, 14:26-14:32 UTC, 311 s, peak 0.16 GB). Setup passed
and all four test steps passed with the counts the v2 addendum gave (14; 12; 11; 9 run with 1
skipped). Then `host_guard.py` stopped it with exit 3 for the fifth time: the Dell's index copy
holds 112 files and 3,360,000 records (last file `pubmed27n0112.xml.gz`), below the 1,306 files
and 39,167,523 records of the full index.

All five 3 GB runs landed on the Dell. The two jobs of this project that asked for 4 GB
(`biogen-llm-v2` and `biogen-llm-v3`) both ran on the Blade, which holds the full index. The
runner picks the machine by free memory and a job cannot name one, so `t2sys-v6` asks for 4 GB
instead of 3. That is the only change: the same six files (copied byte for byte), setup, run
steps, 2 CPUs and 240 minutes. No prediction, threshold or rule changes; R2's "peak at most 3 GB"
still stands, so a bigger ask does not loosen it. If v6 also lands on the Dell, the guard will
again stop it before any prediction is tested.

Contact: MV2, Munim, Inc., mv2@munimtech.com
