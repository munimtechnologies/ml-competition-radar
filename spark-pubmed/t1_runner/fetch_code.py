"""Fetch the published SPARK Task 1 runner (spark-pubmed/t1_runner at a pinned commit) into a
folder and check each file's size and line count against the copy that job spark35-score-v1 ran.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

spark35-score-v1 landed on the host without the whole-corpus index and stopped at host_guard, as
its pre-registration planned. Its re-filing must have a workdir inside the new run's folder, so
this job runs the identical code fetched from the public repository instead of a local copy.
"""
import hashlib
import json
import os
import sys
import urllib.request

COMMIT = "ce37c206eb600473223b7773a9b11381dc7fb76b"
BASE = ("https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/%s/"
        "spark-pubmed/t1_runner/" % COMMIT)
WANT = {"t1.py": (12240, 280), "test_t1.py": (10451, 187), "build_index.py": (11071, 244),
        "host_guard.py": (2526, 63)}  # (bytes on GitHub, lines in spark35-score-v1's copy)
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def main(out):
    os.makedirs(out, exist_ok=True)
    rep, bad = {"commit": COMMIT, "files": {}}, []
    for name, want in sorted(WANT.items()):
        req = urllib.request.Request(BASE + name, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        got = (len(data), len(data.splitlines()))
        rep["files"][name] = {"bytes": got[0], "lines": got[1], "sha256": hashlib.sha256(data).hexdigest()}
        if got != want:
            bad.append("%s: %s, expected %s" % (name, got, want))
        with open(os.path.join(out, name), "wb") as f:
            f.write(data)
    rep["problem"] = "; ".join(bad) or None
    print(json.dumps(rep, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/out/code"))
