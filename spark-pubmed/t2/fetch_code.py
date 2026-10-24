"""Fetch published SPARK code (spark-pubmed/<folder> at pinned commits) into one folder and check
every file's size against the GitHub tree, so a job runs exactly the public code.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

A job's workdir must sit inside the run that files it, so jobs that reuse earlier code fetch it
from the public repository instead of copying it (spark35v2/fetch_code.py did this for t1_runner
alone). Groups: t1 = t1_runner @ ce37c206 (the code spark35-score-v2 runs), t2 = t2 @ 8b6a37a8
(compose.py 0.2.0, biogen_census.py), rerank = rerank @ 99ade999 (MedCPT cross-encoder stage).
Sizes are the blob sizes the GitHub contents API listed on 2026-10-24.

  python fetch_code.py OUT GROUP [GROUP ...]
"""
import hashlib
import json
import os
import sys
import urllib.request

RAW = "https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/%s/spark-pubmed/%s/"
GROUPS = {
    "t1": ("ce37c206eb600473223b7773a9b11381dc7fb76b", "t1_runner",
           {"t1.py": 12240, "test_t1.py": 10451, "build_index.py": 11071, "host_guard.py": 2526}),
    "t2": ("8b6a37a82f7e717cad982adc94b106c47b1d2b01", "t2",
           {"compose.py": 16730, "test_compose.py": 9949, "biogen_census.py": 17656,
            "test_biogen_census.py": 14400}),
    "rerank": ("99ade99976454f499af8f1ea2092083fd6d14b0f", "rerank",
               {"rerank.py": 2961, "rerank_run.py": 5188, "fetch_model.py": 4739, "bench.py": 6994,
                "test_rerank.py": 9949, "test_rerank_run.py": 4484}),
}
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def read_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fetch(out, groups, raw=RAW, read=read_url, table=GROUPS):
    """Write every file of the named groups into out; report bytes, lines and sha256 of each."""
    os.makedirs(out, exist_ok=True)
    rep, bad = {"groups": {}, "files": {}}, []
    for g in groups:
        if g not in table:
            bad.append("unknown group %s" % g)
            continue
        commit, folder, want = table[g]
        rep["groups"][g] = {"commit": commit, "folder": folder}
        for name, size in sorted(want.items()):
            if name in rep["files"]:
                bad.append("%s in two groups" % name)
                continue
            data = read(raw % (commit, folder) + name)
            rep["files"][name] = {"group": g, "bytes": len(data), "lines": len(data.splitlines()),
                                  "sha256": hashlib.sha256(data).hexdigest()}
            if len(data) != size:
                bad.append("%s: %d bytes, expected %d" % (name, len(data), size))
            with open(os.path.join(out, name), "wb") as f:
                f.write(data)
    rep["problem"] = "; ".join(bad) or None
    return rep


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        print("usage: fetch_code.py OUT GROUP [GROUP ...]")
        return 2
    rep = fetch(argv[0], argv[1:])
    print(json.dumps(rep, indent=1))
    return 1 if rep["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
