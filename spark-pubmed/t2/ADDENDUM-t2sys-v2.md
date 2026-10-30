# Addendum: t2sys-v2 (re-file of t2sys-v1, written before v2 runs)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
03:40 UTC, before `t2sys-v2` runs. `PREREGISTRATION-t2sys.md` is unchanged; this note adds two
facts that came in after it was written.

## Why there is a v2

`t2sys-v1` ran on the Dell on 2026-10-30 (01:33-01:42 UTC). Its tests passed and then
`host_guard.py` stopped it with exit 3: the Dell's copy of the index holds 112 files and 3,360,000
records, not 1,306 and 39,167,523. That is the case the pre-registration names ("Exit 3 at
`host_guard`: the job landed on the Dell; re-file unchanged"). The runner runs each job name only
once, so the re-file is `t2sys-v2`: the same seven files, the same setup and run steps, the same
2 CPUs, 3 GB and 240 minutes. No prediction, threshold or rule changes.

## One check was miscounted

C2 says `test_ro_db.py` runs 12 tests (11 passed, 1 skipped). It has 9 (8 passed, 1 skipped,
`test_read_only_folder` as root). The 12 came from rodb1, whose test step also ran `test_probe`'s
3 tests. t2sys-v1 and spark48-image-v1 both ran 9 with exactly that skip. For v2, C2 is graded with
9 run, 8 passed, 1 skipped; every other count in C2 is unchanged (t2sys-v1 confirmed 14, 12 and 11).

Contact: MV2, Munim, Inc., mv2@munimtech.com
