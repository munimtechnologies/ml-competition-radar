# Copyright 2026 Munim, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Fetch param_parts.py and models.txt from ml-competition-radar and check their git blob hashes.

MV2 of Munim, Inc. (made with AI agents working in his name).
Usage: python fetch_dep.py  (exit 0 if both files match the expected blobs, 3 otherwise)
"""
import hashlib
import sys
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/main/tools/param-cap-check/"
WANT = {
    "param_parts.py": "d02b55050e6b908a6087191bd7b7f5099102d31b",
    "models.txt": "6cb8553e4790cfb397aa492d21e5ce5423ea5543",
}


def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main():
    ok = True
    for name, want in WANT.items():
        req = urllib.request.Request(BASE + name, headers={"User-Agent": "MV2-Munim-Inc-research (mv2@munimtech.com)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        got = blob_sha(data)
        print(name, len(data), got, "ok" if got == want else "MISMATCH (want %s)" % want)
        ok = ok and got == want
        with open(name, "wb") as fh:
            fh.write(data)
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
