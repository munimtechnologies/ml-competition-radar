"""Fetch the unchanged corpus_build scripts at a pinned commit and check their git blob sha1.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Job spark33-build-v1 reuses fetch_corpus.py 0.2.2, full_count.py 0.2 and their tests exactly as
published in munimtechnologies/ml-competition-radar at commit 25345bed (spark-pubmed/
corpus_build/). Each file is written only if its git blob sha1 matches the pinned one; any
mismatch exits 1 before the job touches the corpus. Python standard library only.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request

COMMIT = "25345bedb3498e02b689512d596051102dff9fd8"
BASE = ("https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/%s/"
        "spark-pubmed/corpus_build/" % COMMIT)
PINNED = {  # file: (bytes, git blob sha1), read twice from the GitHub contents API on 2026-10-23
    "fetch_corpus.py": (10604, "80ddc4aa61fe5d48e91d2d37af24381dd7c17983"),
    "full_count.py": (10100, "c05af323f7bf764a2b6d364511b8a6e55868702a"),
    "test_corpus_build.py": (14083, "b3a77b9addb62842c1f8d28e7126ae9c1b2038fd"),
}


def git_sha1(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def pull(dest, opener=fetch, pinned=PINNED):
    report, ok = [], True
    for name, (size, sha) in sorted(pinned.items()):
        data = opener(BASE + name)
        got = git_sha1(data)
        good = got == sha and len(data) == size
        report.append({"file": name, "bytes": len(data), "want": sha, "got": got, "ok": good})
        if good:
            with open(os.path.join(dest, name), "wb") as f:
                f.write(data)
        ok = ok and good
    return ok, report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=".")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    ok, report = pull(args.dest)
    with open(os.path.join(args.out_dir, "pull.json"), "w", encoding="utf-8") as f:
        json.dump({"commit": COMMIT, "ok": ok, "files": report}, f, indent=1)
    print(json.dumps(report, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
