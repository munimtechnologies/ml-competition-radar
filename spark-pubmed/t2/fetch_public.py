"""Fetch the published biogen_reuse.py 0.1.0 and official_biogen2024.json into the working folder,
and check each against the sha256 (line endings ignored) that medaesqa-nugget-v1 recorded for it.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python fetch_public.py OUT_JSON  (exit 0 all match, 1 otherwise)
"""
import json
import sys
import urllib.request

from wait_public import USER_AGENT, digest

BASE = "https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/main/spark-pubmed/t2/"
PINS = {"biogen_reuse.py": "e3c044d7dbbfd8f91f25f85ab631ef93781dd4e9419cf237f0c3e7db9e821529",
        "official_biogen2024.json": "504a548f15d7d109ba248f459f788f761c03c485c8a0031c9d5219e3d13bf0ec"}


def main(out):
    rec, ok = {}, True
    for name, want in sorted(PINS.items()):
        try:
            req = urllib.request.Request(BASE + name, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            got = digest(body)
            if got == want:
                with open(name, "wb") as f:
                    f.write(body)
            rec[name] = {"bytes": len(body), "sha256": got, "pinned": want, "match": got == want}
        except Exception as e:  # recorded, never hidden
            rec[name] = {"error": "%s: %s" % (type(e).__name__, e), "pinned": want, "match": False}
        ok = ok and rec[name]["match"]
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
