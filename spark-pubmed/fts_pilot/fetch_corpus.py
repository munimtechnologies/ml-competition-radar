"""Mirror the NLM SPARK PubMed corpus (.pubmed-spark) into --data-dir, md5-checked and resumable.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Reads the live directory listing, downloads each pubmed27nNNNN.xml.gz to <name>.part, checks it
against NLM's .md5 file, then renames it and writes a <name>.md5ok marker. A file that already
has its marker is skipped, so a rerun resumes. Stops before downloading anything if the disk has
less than --min-free-gb free. Writes fetch.json and fetch_files.jsonl to --out-dir. Nothing
downloaded is executed.

v0.2 (run 172): run 1 stalled for hours on one download (a socket that kept trickling bytes never
hit the 120 s read timeout). Each attempt now has a wall-clock limit (--file-minutes) and the
whole step has one too (--max-minutes); files still unfinished then are recorded as failed, and
the process exits without waiting for stuck threads, so the job's later steps still run.

v0.2.1 (run 173): v0.2 picked the read method with getattr(resp, "read1", resp.read), which
evaluates resp.read even when read1 exists, so a response with only read1 raised AttributeError
(two tests failed in the sealed job, before any download). --min-free-gb is now also a floor
checked before each file, so a host with less disk stops early instead of filling up.
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
from concurrent.futures import ThreadPoolExecutor, wait

BASE = "https://ftp.ncbi.nlm.nih.gov/pubmed/.pubmed-spark/"
UA = "MV2-Munim-spark-fetch/0.2.1 (mv2@munimtech.com)"
NAME_RX = re.compile(r"pubmed27n(\d{4})\.xml\.gz(?!\.md5)")
MD5_RX = re.compile(r"\b([0-9a-f]{32})\b")


def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)


def list_files(opener=fetch):
    with opener(BASE) as resp:
        html = resp.read().decode("utf-8", "replace")
    return sorted(set("pubmed27n%s.xml.gz" % m.group(1) for m in NAME_RX.finditer(html)))


def get(name, data_dir, opener=fetch, tries=3, file_seconds=900.0, min_free_bytes=0):
    """Download one file (once), check its md5, mark it verified. Returns a per-file record."""
    path = os.path.join(data_dir, name)
    marker = path + ".md5ok"
    if os.path.exists(path) and os.path.exists(marker):
        with open(marker, encoding="ascii") as f:
            return {"file": name, "bytes": os.path.getsize(path), "md5": f.read().strip(),
                    "skipped": True, "problem": None}
    info = {"file": name, "skipped": False}
    free = shutil.disk_usage(data_dir).free
    if free < min_free_bytes:
        info["problem"] = "disk floor: %.1f GB free < %.1f GB; not downloaded" % (free / 1e9, min_free_bytes / 1e9)
        return info
    for attempt in range(1, tries + 1):
        try:
            t0 = time.time()
            with opener(BASE + name + ".md5") as r:
                m = MD5_RX.search(r.read().decode("ascii", "replace").lower())
            want = m.group(1) if m else None
            h, n = hashlib.md5(), 0
            with opener(BASE + name) as resp, open(path + ".part", "wb") as f:
                read = resp.read1 if hasattr(resp, "read1") else resp.read  # read1: one socket read, never a long wait
                while True:
                    if time.time() - t0 > file_seconds:
                        raise TimeoutError("no complete download within %.0f s" % file_seconds)
                    chunk = read(1 << 16)
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


def run(data_dir, out_dir, workers, min_free_gb, opener=fetch, max_minutes=None, file_minutes=15.0):
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    free = shutil.disk_usage(data_dir).free / 1e9
    summary = {"free_gb_before": round(free, 1), "min_free_gb": min_free_gb, "max_minutes": max_minutes,
               "file_minutes": file_minutes, "problem": None}
    results = []
    if free < min_free_gb:
        summary["problem"] = "not enough free disk (%.1f GB < %s GB); nothing downloaded" % (free, min_free_gb)
    else:
        names = list_files(opener)
        summary["listing_files"] = len(names)
        t0 = time.time()
        pool = ThreadPoolExecutor(max_workers=max(1, workers))
        futs = {pool.submit(get, n, data_dir, opener, 3, 60.0 * file_minutes, min_free_gb * 1e9): n
                for n in names}
        pending, done_n = set(futs), 0
        deadline = None if max_minutes is None else t0 + 60.0 * max_minutes
        while pending:
            left = None if deadline is None else max(0.0, deadline - time.time())
            done, pending = wait(pending, timeout=60 if left is None else min(60, left))
            for fut in done:
                results.append(fut.result())
                done_n += 1
                if done_n % 50 == 0:
                    print("done %d/%d %.0fs" % (done_n, len(names), time.time() - t0), flush=True)
            if deadline is not None and time.time() >= deadline:
                break
        for fut in pending:
            results.append({"file": futs[fut], "skipped": False,
                            "problem": "not finished within --max-minutes %s" % max_minutes})
        summary["unfinished"] = len(pending)
        pool.shutdown(wait=False, cancel_futures=True)
        results.sort(key=lambda i: i["file"])
        good = [i for i in results if not i.get("problem")]
        summary.update({
            "files_ok": len(good), "files_resumed": sum(1 for i in good if i["skipped"]),
            "files_failed": [i["file"] for i in results if i.get("problem")],
            "files_disk_floor": sum(1 for i in results if (i.get("problem") or "").startswith("disk floor")),
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


def exit_code(summary, allow_failed):
    """0 when nothing failed, or only a few files failed (<= allow_failed) after a real listing."""
    if not summary["problem"]:
        return 0
    failed = summary.get("files_failed")
    if failed is not None and summary.get("files_ok") and len(failed) <= allow_failed:
        return 0
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--min-free-gb", type=float, default=170)
    ap.add_argument("--max-minutes", type=float, default=None)
    ap.add_argument("--file-minutes", type=float, default=15.0)
    ap.add_argument("--allow-failed", type=int, default=0)
    args = ap.parse_args(argv)
    s = run(args.data_dir, args.out_dir, args.workers, args.min_free_gb,
            max_minutes=args.max_minutes, file_minutes=args.file_minutes)
    print(json.dumps(s, indent=1)[:4000], flush=True)
    return exit_code(s, args.allow_failed)


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)  # never wait for a download thread that is still stuck in a socket read
