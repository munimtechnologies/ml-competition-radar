"""Stand-in checks for the SPARK Task 1 Docker image (system/Dockerfile), for spark48-image-v1.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

The image is not built yet. A sealed python:3.12-slim job with no network in its run steps comes
close to it, if /app is laid out exactly as the Dockerfile's COPY lines lay it out:

  net  records whether this process can resolve a name or open a TCP connection (it should not).
       Always exits 0; the answer is in the JSON.
  app  copies the six files the Dockerfile copies (flat, no t1_runner/ or rerank/ folders) from
       a fetch_code.py folder into a new /app, and the model folder into /app/model, makes them
       readable by everyone, and records each file's bytes, sha256 and git blob sha (compared
       with the blob the repository listed at the pinned commits), plus the Python, SQLite,
       torch and transformers versions. Exit 1 if /app already exists, a file is missing or
       /app holds anything else.

  python image_eq.py net --out /out/net.json
  python image_eq.py app --code /tmp/code --model MODEL_DIR --app /app --out /out/app.json

Python standard library only (torch and transformers versions are read if installed).
"""
import argparse
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import sys

VERSION = "0.1.0"
# Dockerfile: COPY t1_runner/t1.py t1_runner/build_index.py rerank/rerank.py rerank/rerank_run.py
#             system/spark_t1.py system/ro_db.py /app/  and  COPY system/model/ /app/model/
# Git blob shas from the GitHub contents API at the fetch_code.py pins (read 2026-10-29).
APP_FILES = {
    "t1.py": "6de6de3f780e9eeb075322e5257d86959dce9e46",
    "build_index.py": "7211c27af5b07d8abb920b0610f24a39f165b167",
    "rerank.py": "0de02d8b84282fa6a12c248fbd65013d3cb7e3f0",
    "rerank_run.py": "e3265281535afc5800aa59972b6301469255f03b",
    "spark_t1.py": "ff8d03c46704b8b24fe3660ba31fca350692ee6c",
    "ro_db.py": "fb27ff93ef73b58e63ab7b365fd4422c71b06fea",
}


def git_blob(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def probe(host="pypi.org", ip="1.1.1.1", port=443, timeout=5,
          resolve=socket.getaddrinfo, connect=socket.create_connection):
    """dns: could host be resolved; connect: could ip:port be opened. reachable = either."""
    rec = {"version": VERSION, "host": host, "ip": ip, "port": port}
    try:
        resolve(host, port)
        rec["dns"], rec["dns_error"] = True, None
    except OSError as e:
        rec["dns"], rec["dns_error"] = False, "%s: %s" % (type(e).__name__, str(e)[:200])
    try:
        connect((ip, port), timeout).close()
        rec["connect"], rec["connect_error"] = True, None
    except OSError as e:
        rec["connect"], rec["connect_error"] = False, "%s: %s" % (type(e).__name__, str(e)[:200])
    rec["reachable"] = rec["dns"] or rec["connect"]
    return rec


def file_rec(path):
    with open(path, "rb") as f:
        data = f.read()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "git_blob": git_blob(data)}


def runtime():
    rec = {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version}
    for mod in ("torch", "transformers"):
        try:
            rec[mod] = __import__(mod).__version__
        except ImportError:
            rec[mod] = None
    return rec


def build_app(code, model, app, files=APP_FILES):
    """Lay out app as the Dockerfile does; return the record (problem None if the layout is exact)."""
    rec = {"version": VERSION, "app": app, "files": {}, "model": {}, "blob_mismatch": []}
    if os.path.exists(app):
        rec["problem"] = "%s already exists" % app
        return rec
    missing = [n for n in sorted(files) if not os.path.isfile(os.path.join(code, n))]
    if not os.path.isdir(model):
        missing.append(model)
    if missing:
        rec["problem"] = "missing: " + ", ".join(missing)
        return rec
    os.makedirs(app)
    for name in sorted(files):
        shutil.copyfile(os.path.join(code, name), os.path.join(app, name))
    shutil.copytree(model, os.path.join(app, "model"))
    for root, dirs, names in os.walk(app):
        os.chmod(root, 0o755)
        for n in names:
            os.chmod(os.path.join(root, n), 0o644)
    for name in sorted(files):
        rec["files"][name] = file_rec(os.path.join(app, name))
        if rec["files"][name]["git_blob"] != files[name]:
            rec["blob_mismatch"].append(name)
    mdir = os.path.join(app, "model")
    for root, _, names in os.walk(mdir):
        for n in sorted(names):
            p = os.path.join(root, n)
            r = file_rec(p)
            del r["git_blob"]
            rec["model"][os.path.relpath(p, mdir).replace(os.sep, "/")] = r
    rec["listing"] = sorted(os.listdir(app))
    want = sorted(list(files) + ["model"])
    rec["problem"] = None if rec["listing"] == want else "app holds %s, expected %s" % (rec["listing"], want)
    rec["runtime"] = runtime()
    return rec


def write(path, rec):
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser(description="SPARK image stand-in checks (MV2 of Munim, Inc.)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("net")
    n.add_argument("--out", required=True)
    a = sub.add_parser("app")
    a.add_argument("--code", required=True)
    a.add_argument("--model", required=True)
    a.add_argument("--app", required=True)
    a.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "net":
        rec = probe()
        write(args.out, rec)
        print(json.dumps(rec, indent=1))
        return 0
    rec = build_app(args.code, args.model, args.app)
    write(args.out, rec)
    print(json.dumps({k: v for k, v in rec.items() if k != "model"}, indent=1))
    return 1 if rec["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
