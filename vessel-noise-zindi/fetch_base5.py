"""Fetch the unchanged v1/v2/v3 modules (vessel_mix.py 0.1.0, vessel_mix2.py 0.2.0,
vessel_mix3.py 0.3.0) from the public repository at a pinned commit, so vessel_mix5 runs on exactly
the code that produced v1 to v4. All three must match the SHA-256 recorded by the v4 run.

In the repository this file is fetch_base5.py, so earlier fetchers stay as they were.
MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python fetch_base5.py OUT_JSON   (exit 0 ok, 3 on any failure or hash mismatch)
"""
import hashlib
import json
import sys
import time
import urllib.request

COMMIT = "2c4e55bf731b32ee48ffe227e00e0d590271bc73"
BASE = "https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/%s/vessel-noise-zindi/" % COMMIT
FILES = ("vessel_mix.py", "vessel_mix2.py", "vessel_mix3.py")
EXPECT = {  # base_files.json of the vesselmix4-v1 run (2026-11-10)
    "vessel_mix.py": "9746ff3acaa5870bec408af167de70d7f20e697838a1043742eb55957ba8af2e",
    "vessel_mix2.py": "eec0cd9fc1ef0a3b4af722fdeed98fd02e12f653b7f9dc9d6a1d763e1ef82e46",
    "vessel_mix3.py": "0a133d4b9ff696bac4cbfa1a5b2bce500ee3908f68851dacc7fb3a1504254abb"}
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
            h = hashlib.sha256(b).hexdigest()
            rec["files"][name] = {"bytes": len(b), "sha256": h, "matches_v4_run": h == EXPECT[name]}
            if h != EXPECT[name]:
                rec["ok"] = False
        except Exception as e:
            rec["ok"] = False
            rec["files"][name] = {"error": "%s: %s" % (type(e).__name__, e)}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    return 0 if rec["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
