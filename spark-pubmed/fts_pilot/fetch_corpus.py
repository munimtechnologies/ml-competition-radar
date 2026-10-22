"""Mirror the NLM SPARK PubMed corpus (.pubmed-spark) into --data-dir, md5-checked and resumable.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Reads the live directory listing, downloads each pubmed27nNNNN.xml.gz to <name>.part, checks it
against NLM's .md5 file, then renames it and writes a <name>.md5ok marker. A file that already
has its marker is skipped, so a rerun resumes. Stops before downloading anything if the disk has
less than --min-free-gb free. Writes fetch.json and fetch_files.jsonl to --out-dir. Nothing
downloaded is executed.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://ftp.ncbi.nlm.nih.gov/pubmed/.pubmed-spark/"
UA = "MV2-Munim-spark-fetch/0.1 (mv2@munimtech.com)"
NAME_RX = re.compile(r"pubmed27n(\d{4})\.xml\.gz(?!\.md5)")
MD5_RX = re.compile(r"\b([0-9a-f]{32})\b")


def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)


def list_files(opener=fetch):
    with opener(BASE) as resp:
        html = resp.read().decode("utf-8", "replace")
    return sorted(set("pubmed27n%s.xml.gz" % m.group(1) for m in NAME_RX.finditer(html)))


def get(name, data_dir, opener=fetch, tries=3):
    """Download one file (once), check its md5, mark it verified. Returns a per-file record."""
    path = os.path.join(data_dir, name)
    marker = path + ".md5ok"
    if os.path.exists(path) and os.path.exists(marker):
        with open(marker, encoding="ascii") as f:
            return {"file": name, "bytes": os.path.getsize(path), "md5": f.read().strip(),
                    "skipped": True, "problem": None}
    info = {"file": name, "skipped": False}
    for attempt in range(1, tries + 1):
        try:
            t0 = time.time()
            with opener(BASE + name + ".md5") as r:
                m = MD5_RX.search(r.read().decode("ascii", "replace").lower())
            want = m.group(1) if m else None
            h, n = hashlib.md5(), 0
            with opener(BASE + name) as resp, open(path + ".part", "wb") as f:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    h.update(chunk)
                    f.write(chunk)
                    n += len(chunk)
            got = h.hexdigest()
            info.update({"bytes": n, "md5": got, "attempts": attempt,
                         "seconds": round(time.time() - t0, 1), "problem": None})
            if got != want:
                info["problem"] = "md5 mismatch (want %s)" % want
                os.remove(path + ".part")
                continue
            os.replace(path + ".part", path)
            with open(marker, "w", encoding="ascii") as f:
                f.write(got)
            return info
        except Exception as exc:  # record, retry, then give up on this file only
            info["problem"] = "attempt %d: %s: %s" % (attempt, type(exc).__name__, str(exc)[:120])
    return info


def run(data_dir, out_dir, workers, min_free_gb, opener=fetch):
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    free = shutil.disk_usage(data_dir).free / 1e9
    summary = {"free_gb_before": round(free, 1), "min_free_gb": min_free_gb, "problem": None}
    results = []
    if free < min_free_gb:
        summary["problem"] = "not enough free disk (%.1f GB < %s GB); nothing downloaded" % (free, min_free_gb)
    else:
        names = list_files(opener)
        summary["listing_files"] = len(names)
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            for info in pool.map(lambda n: get(n, data_dir, opener), names):
                results.append(info)
                if len(results) % 50 == 0:
                    print("done %d/%d %.0fs" % (len(results), len(names), time.time() - t0), flush=True)
        good = [i for i in results if not i.get("problem")]
        summary.update({
            "files_ok": len(good), "files_resumed": sum(1 for i in good if i["skipped"]),
            "files_failed": [i["file"] for i in results if i.get("problem")],
            "bytes_total": sum(i["bytes"] for i in good),
            "seconds": round(time.time() - t0, 1),
            "free_gb_after": round(shutil.disk_usage(data_dir).free / 1e9, 1)})
        if summary["files_failed"]:
            summary["problem"] = "%d file(s) failed (see fetch_files.jsonl)" % len(summary["files_failed"])
        elif not good:
            summary["problem"] = "nothing listed"
    with open(os.path.join(out_dir, "fetch_files.jsonl"), "w", encoding="utf-8") as f:
        for info in results:
            f.write(json.dumps(info) + "\n")
    with open(os.path.join(out_dir, "fetch.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--min-free-gb", type=float, default=170)
    args = ap.parse_args(argv)
    s = run(args.data_dir, args.out_dir, args.workers, args.min_free_gb)
    print(json.dumps(s, indent=1)[:4000])
    return 1 if s["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
