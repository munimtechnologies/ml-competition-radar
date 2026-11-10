"""Fetch the unchanged v1/v2 modules (vessel_mix.py 0.1.0, vessel_mix2.py 0.2.0) from the public
repository at a pinned commit, so vessel_mix3 runs on exactly the code that produced v1 and v2.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python fetch_base.py OUT_JSON   (exit 0 ok, 3 on any failure)
"""
import hashlib
import json
import sys
import time
import urllib.request

COMMIT = "9a2fb34d6496f22c588d28417ad822b561772be6"
BASE = "https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/%s/vessel-noise-zindi/" % COMMIT
FILES = ("vessel_mix.py", "vessel_mix2.py")
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def get(url, tries=4):
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # transient network errors
            last = e
            time.sleep(5 * (t + 1))
    raise last


def main(out):
    rec = {"commit": COMMIT, "files": {}, "ok": True}
    for name in FILES:
        try:
            b = get(BASE + name)
            with open(name, "wb") as f:
                f.write(b)
            rec["files"][name] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
        except Exception as e:
            rec["ok"] = False
            rec["files"][name] = {"error": "%s: %s" % (type(e).__name__, e)}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    return 0 if rec["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
