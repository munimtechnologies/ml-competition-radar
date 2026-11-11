"""Download telco_embcheck.py 0.1.0 (embcheck-1) unchanged from its published commit and record its
SHA-256, so embcheck-2 reuses exactly the code that produced embcheck-1's results.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python fetch_base.py OUT_JSON
"""
import hashlib
import json
import sys
import urllib.request

COMMIT = "471747822d083dc65472dc3abc584a881ec04b8e"
FILES = ["telco_embcheck.py"]
URL = "https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/%s/telcoretrieve-zindi/%s"
UA = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def main(out):
    rec = {"commit": COMMIT, "files": {}}
    for name in FILES:
        req = urllib.request.Request(URL % (COMMIT, name), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
        with open(name, "wb") as f:
            f.write(body)
        rec["files"][name] = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    import telco_embcheck
    rec["telco_embcheck_version"] = telco_embcheck.VERSION
    rec["ok"] = telco_embcheck.VERSION == "0.1.0"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    return 0 if rec["ok"] else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
