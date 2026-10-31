"""Fetch the published biogen_reuse.py 0.1.0, official_biogen2024.json and medaesqa_nugget.py 0.2.0
into the working folder. The first two are checked against the sha256 (line endings ignored) that
medaesqa-nugget-v1 recorded; medaesqa_nugget.py is read at a fixed commit (an immutable URL) and
must declare VERSION 0.2.0. Its sha256 is recorded.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python fetch_public.py OUT_JSON  (exit 0 all match, 1 otherwise)
"""
import json
import sys
import urllib.request

from wait_public import USER_AGENT, digest

REPO = "https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/"
MAIN = REPO + "main/spark-pubmed/t2/"
COMMIT = "5c2f2caa7c2b6fd5f230b76850bc4234c2c9f2c7"  # "medaesqa_nugget 0.2.0 ..." (2026-10-31T12:38:18Z)
FILES = {"biogen_reuse.py": (MAIN, "e3c044d7dbbfd8f91f25f85ab631ef93781dd4e9419cf237f0c3e7db9e821529", None),
         "official_biogen2024.json": (MAIN, "504a548f15d7d109ba248f459f788f761c03c485c8a0031c9d5219e3d13bf0ec", None),
         "medaesqa_nugget.py": (REPO + COMMIT + "/spark-pubmed/t2/", None, b'VERSION = "0.2.0"')}


def check(body, pin, marker):
    got = digest(body)
    return got, (got == pin) if pin else (marker in body)


def main(out):
    rec, ok = {}, True
    for name, (base, pin, marker) in sorted(FILES.items()):
        try:
            req = urllib.request.Request(base + name, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            got, match = check(body, pin, marker)
            if match:
                with open(name, "wb") as f:
                    f.write(body)
            rec[name] = {"url": base + name, "bytes": len(body), "sha256": got, "pinned": pin,
                         "marker": marker.decode() if marker else None, "match": match}
        except Exception as e:  # recorded, never hidden
            rec[name] = {"url": base + name, "error": "%s: %s" % (type(e).__name__, e), "pinned": pin, "match": False}
        ok = ok and rec[name]["match"]
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
