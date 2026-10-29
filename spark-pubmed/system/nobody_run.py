"""Run one command as uid/gid 65534 (no write access to the index), then copy its output to /out.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

For spark47-immutable-v1: the SPARK index sits on a volume that only root can write, so a
process running as 65534 sees it the way the challenge's image sees a read-only mount. The
command runs in a fresh work folder owned by 65534 (also its HOME); every {W} in the command
becomes that folder. Afterwards (as root) the folder's files are copied to --out-dir and
nobody.json records the exit code, the last stderr lines and the index's -wal/-shm files before
and after. Exit 0 if the outcome is the expected one (--expect ok: the command exited 0;
--expect fail: it did not), else 1, so a control that must fail does not stop the job.

  python nobody_run.py --work /tmp/w --out-dir /out/x --db INDEX --expect ok -- CMD ARG ...

Python standard library only.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ro_db  # noqa: E402

VERSION = "0.1.0"
NOBODY = 65534


def beside(db):
    folder, base = os.path.split(os.path.abspath(db))
    return sorted(n for n in os.listdir(folder) if n.startswith(base))


def as_user(cmd, env, uid):
    return subprocess.run(cmd, user=uid, group=uid, extra_groups=[], env=env, capture_output=True, text=True)


def run(cmd, work, out_dir, db, expect, runner=as_user, chown=os.chown, uid=NOBODY):
    os.makedirs(work, exist_ok=True)
    os.chmod(work, 0o700)
    chown(work, uid, uid)
    cmd = [c.replace("{W}", work) for c in cmd]
    env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": work,
           "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    rec = {"version": VERSION, "uid": uid, "cmd": cmd, "expect": expect,
           "before": {"side_files": ro_db.side_files(db), "beside": beside(db)}}
    p = runner(cmd, env, uid)
    err = (p.stderr or "").strip().splitlines()
    rec.update({"exit": p.returncode, "stderr_last": err[-3:], "stdout_tail": (p.stdout or "")[-2000:],
                "after": {"side_files": ro_db.side_files(db), "beside": beside(db)}})
    os.makedirs(out_dir, exist_ok=True)
    copied = []
    for root, _, files in os.walk(work):
        for name in files:
            src = os.path.join(root, name)
            rel = os.path.relpath(src, work)
            if rel.split(os.sep)[0].startswith("."):
                continue  # caches under HOME
            dst = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            copied.append(rel.replace(os.sep, "/"))
    rec["copied"] = sorted(copied)
    rec["as_expected"] = (p.returncode == 0) == (expect == "ok")
    with open(os.path.join(out_dir, "nobody.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    return rec


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--" not in argv:
        print("usage: nobody_run.py --work W --out-dir D --db DB --expect ok|fail -- CMD ...", file=sys.stderr)
        return 2
    i = argv.index("--")
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--expect", choices=("ok", "fail"), required=True)
    a = ap.parse_args(argv[:i])
    if not argv[i + 1:]:
        ap.error("no command after --")
    rec = run(argv[i + 1:], a.work, a.out_dir, a.db, a.expect)
    print(json.dumps({k: v for k, v in rec.items() if k != "stdout_tail"}, indent=1))
    return 0 if rec["as_expected"] else 1


if __name__ == "__main__":
    sys.exit(main())
