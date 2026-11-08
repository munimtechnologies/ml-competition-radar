"""Download ch4_icos.py 0.1.0 from its pinned public commit (the code ch4icos-v1 ran).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Writes ./ch4_icos.py, or /tmp/ch4base/ch4_icos.py if the working folder is read-only.
"""
import hashlib
import os
import sys
import urllib.request

URL = ("https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/"
       "481e0091660f6341bac0fd57fde219b836fd1e51/methane-zindi/ch4_icos.py")


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "MV2-Munim-Inc-research (mv2@munimtech.com)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if b'VERSION = "0.1.0"' not in data:
        print("unexpected file at", URL)
        return 3
    for folder in (".", "/tmp/ch4base"):
        try:
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "ch4_icos.py")
            with open(path, "wb") as f:
                f.write(data)
            print(path, len(data), hashlib.sha256(data).hexdigest())
            return 0
        except OSError as e:
            print("cannot write in", folder, e)
    return 4


if __name__ == "__main__":
    sys.exit(main())
