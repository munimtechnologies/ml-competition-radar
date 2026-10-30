"""Wait until a pre-registration is public on GitHub before an analysis runs, and record whether
the public copy matches the local one (line endings ignored).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Usage: python wait_public.py URL LOCAL_FILE MINUTES OUT_JSON  (exit 0 public, 4 never seen)
"""
import hashlib
import json
import sys
import time
import urllib.request

USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def digest(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def main(url, local, minutes, out):
    with open(local, "rb") as f:
        want = digest(f.read())
    t0, tries, got, last_error = time.time(), 0, None, None
    while True:
        tries += 1
        try:
            req = urllib.request.Request("%s?t=%d" % (url, int(time.time())), headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                got = digest(r.read())
            break
        except Exception as e:  # 404 until the commit lands
            last_error = "%s: %s" % (type(e).__name__, e)
        if time.time() - t0 > float(minutes) * 60:
            break
        time.sleep(120)
    rec = {"url": url, "public": got is not None, "local_sha256": want, "public_sha256": got,
           "match": got == want, "tries": tries, "waited_seconds": round(time.time() - t0),
           "seen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) if got else None,
           "last_error": last_error}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    return 0 if got is not None else 4


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
