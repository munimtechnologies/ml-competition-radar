#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. (MV2). Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Where are NLM's expert nuggets for the TREC 2024 BioGen questions?

medaesqa-nugget-v1 found the `expert_curated_nuggets` value empty (None) in all 40 items of
MedAESQA's public medaesqa_v1.json. NLM's BioACE scorer downloads a data bundle
(bioace-data-models.zip) whose training split, per its paper (arXiv 2602.04982), "contains the
system-generated and ground-truth nuggets". This job:

- `zip`: lists that archive's members with HTTP range requests (the end-of-central-directory
  record, then the central directory), without downloading the whole archive, and unpacks only
  data files whose names mention nuggets or ground truth, or that sit in a data/ folder, up to
  fixed size caps. It saves them under --data-dir/bioace and describes their structure.
- `medaesqa`: lists the field names of every MedAESQA item and how often each is present, empty
  or null, so "the key is missing" and "the key holds null" can be told apart.

Made with AI agents working for MV2 of Munim, Inc. Output is names, sizes, field names, ids and
counts only, never question, answer or nugget text.
"""
import argparse
import binascii
import bz2
import hashlib
import json
import os
import re
import statistics
import struct
import sys
import time
import urllib.error
import urllib.request
import zlib

VERSION = "0.1.0"
URL = "http://bionlp.nlm.nih.gov/bioace-data-models.zip"  # as in BioACE's download_data_models.sh
MEDAESQA_URL = "https://osf.io/download/9d3qs/"
MEDAESQA_BYTES = 7276948
MEDAESQA_SHA = "a062742c1678b4379121ad030a06bda574afd376f331df41575938dd9849c383"  # medaesqa-nugget-v1
UA = "MV2-Munim-research/0.1 (mv2@munimtech.com)"
TAIL = 65536 + 22 + 20 + 1024  # longest zip comment + EOCD + zip64 locator, with room
MAX_CD = 32 << 20  # central directory bytes
MAX_MEMBER = 32 << 20  # compressed bytes of one unpacked member
MAX_UNPACKED = 64 << 20  # uncompressed bytes of one unpacked member
MAX_TOTAL = 128 << 20  # compressed bytes of all unpacked members
MAX_LISTED = 3000
DATA_EXT = (".json", ".jsonl", ".tsv", ".csv", ".txt")
PICK_RX = re.compile(r"nugget|ground[_ -]?truth|(^|[/_.-])gt([/_.-]|$)|qrel", re.I)
ID_RX = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,40}$")
NUM_RX = re.compile(r"^\d{1,8}$")
ID_KEYS = ("question_id", "id", "qid", "topic_id", "topic", "query_id")


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Remote:
    """Byte ranges of one URL over HTTP. Never reads a body the server sends in full."""

    def __init__(self, url, timeout=120):
        self.url, self.timeout = url, timeout
        self.requests = self.received = 0
        self.info = {}

    def _open(self, start, end):
        req = urllib.request.Request(self.url, headers={"User-Agent": UA, "Range": "bytes=%d-%d" % (start, end)})
        self.requests += 1
        return urllib.request.urlopen(req, timeout=self.timeout)

    def probe(self):
        """The archive's size, from a one-byte range request."""
        try:
            r = self._open(0, 0)
        except urllib.error.HTTPError as e:
            self.info["status"] = e.code
            raise
        with r:
            h = r.headers
            self.info.update(status=r.status, final_url=r.geturl(), content_range=h.get("Content-Range"),
                             content_length=h.get("Content-Length"), content_type=h.get("Content-Type"),
                             last_modified=h.get("Last-Modified"), etag=h.get("ETag"),
                             accept_ranges=h.get("Accept-Ranges"))
            if r.status != 206:
                raise RuntimeError("server ignored the Range header (status %s); nothing more read" % r.status)
            m = re.match(r"bytes\s+0-0/(\d+)$", (h.get("Content-Range") or "").strip())
            if not m:
                raise RuntimeError("no archive size in Content-Range")
            self.received += len(r.read(2))
        self.url = self.info["final_url"] or self.url
        return int(m.group(1))

    def read(self, start, n):
        if n <= 0:
            return b""
        with self._open(start, start + n - 1) as r:
            if r.status != 206:
                raise RuntimeError("range request answered with status %s" % r.status)
            data = r.read(n + 1)
        self.received += len(data)
        if len(data) != n:
            raise RuntimeError("asked for %d bytes at %d, got %d" % (n, start, len(data)))
        return data

    def summary(self):
        return dict(self.info, requests=self.requests, received_bytes=self.received)


def find_eocd(tail, base):
    """(end-of-central-directory fields, its absolute offset) from the archive's last bytes."""
    i = tail.rfind(b"PK\x05\x06")
    while i >= 0:
        if i + 22 <= len(tail):
            f = struct.unpack("<IHHHHIIH", tail[i:i + 22])
            if i + 22 + f[7] <= len(tail):
                return {"entries": f[4], "cd_size": f[5], "cd_offset": f[6], "comment_bytes": f[7]}, base + i
        i = tail.rfind(b"PK\x05\x06", 0, i)
    raise ValueError("no end-of-central-directory record in the last %d bytes" % len(tail))


def zip64_eocd(read, at):
    """(entries, central directory size, offset) from the zip64 records before the EOCD at `at`."""
    sig, _, off, _ = struct.unpack("<IIQI", read(at - 20, 20))
    if sig != 0x07064B50:
        raise ValueError("no zip64 locator before the end record")
    f = struct.unpack("<IQHHIIQQQQ", read(off, 56))
    if f[0] != 0x06064B50:
        raise ValueError("no zip64 end record at the located offset")
    return f[7], f[8], f[9]


def zip64_extra(extra, usize, csize, off):
    """Sizes and offset with any 0xFFFFFFFF placeholder replaced from the zip64 extra field."""
    j = 0
    while j + 4 <= len(extra):
        hid, hlen = struct.unpack("<HH", extra[j:j + 4])
        body = extra[j + 4:j + 4 + hlen]
        if hid == 1:
            vals, k = [], 0
            for v in (usize, csize, off):
                if v == 0xFFFFFFFF and k + 8 <= len(body):
                    v = struct.unpack("<Q", body[k:k + 8])[0]
                    k += 8
                vals.append(v)
            return tuple(vals)
        j += 4 + hlen
    return usize, csize, off


def parse_cd(cd):
    out, i = [], 0
    while i + 46 <= len(cd) and cd[i:i + 4] == b"PK\x01\x02":
        f = struct.unpack("<IHHHHHHIIIHHHHHII", cd[i:i + 46])
        flags, method, crc, csize, usize, nlen, elen, clen, off = f[3], f[4], f[7], f[8], f[9], f[10], f[11], f[12], f[16]
        name = cd[i + 46:i + 46 + nlen].decode("utf-8" if flags & 0x800 else "cp437", errors="replace")
        usize, csize, off = zip64_extra(cd[i + 46 + nlen:i + 46 + nlen + elen], usize, csize, off)
        out.append({"name": name, "size": usize, "compressed": csize, "method": method, "crc": crc,
                    "offset": off, "encrypted": bool(flags & 1)})
        i += 46 + nlen + elen + clen
    return out


def unpack(read, m):
    """One member's bytes, checked against the central directory's size and CRC."""
    if m["encrypted"]:
        raise ValueError("encrypted member")
    sig, _, _, _, _, _, _, _, _, nlen, elen = struct.unpack("<IHHHHHIIIHH", read(m["offset"], 30))
    if sig != 0x04034B50:
        raise ValueError("no local header at the listed offset")
    data = read(m["offset"] + 30 + nlen + elen, m["compressed"])
    if m["method"] == 0:
        raw = data
    elif m["method"] == 8:
        raw = zlib.decompressobj(-15).decompress(data, MAX_UNPACKED + 1)
    elif m["method"] == 12:
        raw = bz2.decompress(data)
    else:
        raise ValueError("compression method %d not supported" % m["method"])
    if len(raw) != m["size"] or (binascii.crc32(raw) & 0xFFFFFFFF) != m["crc"]:
        raise ValueError("size or CRC does not match the central directory")
    return raw


def picked(m):
    name = m["name"]
    if name.endswith("/") or not name.lower().endswith(DATA_EXT):
        return False
    return bool(PICK_RX.search(name)) or "/data/" in "/" + name.lower()


def save(root, name, raw):
    """Write a member under root (never outside it); returns its relative path."""
    parts = [p for p in re.split(r"[\\/]+", name) if p not in ("", ".", "..")]
    path = os.path.join(root, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(raw)
    return "/".join(parts)


def shape(v, depth=0):
    """A text-free description of a value's structure; field names are kept, ids are counted."""
    if isinstance(v, list):
        if depth >= 4:
            return "list"
        return "list[%s]" % "|".join(sorted({shape(x, depth + 1) for x in v[:200]}))
    if isinstance(v, dict):
        keys = [str(k) for k in v]
        if keys and all(NUM_RX.match(k) for k in keys):
            inner = sorted({shape(x, depth + 1) for x in list(v.values())[:200]}) if depth < 4 else []
            return "dict{<%d numeric ids>: %s}" % (len(keys), "|".join(inner))
        if len(keys) <= 30 and all(ID_RX.match(k) for k in keys) and depth < 4:
            return "{%s}" % ", ".join("%s: %s" % (k, shape(v[k], depth + 1)) for k in sorted(keys))
        return "dict(%d keys)" % len(keys)
    return type(v).__name__


def records(obj):
    """(key, record) pairs of the per-question records in a parsed file, if it has any."""
    if isinstance(obj, list):
        return [(None, r) for r in obj if isinstance(r, dict)]
    if isinstance(obj, dict) and obj:
        vals = list(obj.values())
        wrapper = len(obj) == 1 and not NUM_RX.match(str(next(iter(obj))))
        if all(isinstance(v, dict) for v in vals):
            return records(vals[0]) if wrapper else list(obj.items())
        if all(isinstance(v, list) for v in vals):
            return records(vals[0]) if wrapper else [(k, {"_items": v}) for k, v in obj.items()]
        lists = [v for v in vals if isinstance(v, list) and v and all(isinstance(x, dict) for x in v)]
        if len(lists) == 1:
            return records(lists[0])
    return []


def describe(name, raw):
    text = raw.decode("utf-8-sig", errors="replace")
    out, obj = {"bytes": len(raw)}, None
    if name.lower().endswith((".json", ".jsonl")):
        try:
            obj = json.loads(text)
            out["format"] = "json"
        except ValueError:
            try:
                obj = [json.loads(line) for line in text.splitlines() if line.strip()]
                out["format"] = "jsonl"
            except ValueError as e:
                out["format"] = "unparsed"
                out["parse_error"] = str(e)[:200]
    if obj is None:
        lines = [line for line in text.splitlines() if line.strip()]
        out["lines"] = len(lines)
        if lines:
            head = lines[0].split("\t" if "\t" in lines[0] else ",")
            out["columns"] = len(head)
            if all(ID_RX.match(h.strip()) for h in head):
                out["header"] = [h.strip() for h in head]
        return out
    out["shape"] = shape(obj)[:3000]
    recs = records(obj)
    out["records"] = len(recs)
    ids, fields = [], {}
    for k, r in recs:
        q = str(k) if k is not None and NUM_RX.match(str(k)) else None
        if q is None:
            for f in ID_KEYS:
                v = r.get(f)
                if isinstance(v, (int, str)) and not isinstance(v, bool) and NUM_RX.match(str(v)):
                    q = str(v)
                    break
        if q is not None:
            ids.append(int(q))
        for f, v in r.items():
            if isinstance(v, list) and ID_RX.match(str(f)):
                s = fields.setdefault(str(f), {"lengths": [], "words": []})
                s["lengths"].append(len(v))
                s["words"].extend(len(x.split()) for x in v if isinstance(x, str))
    distinct = sorted(set(ids))
    out["ids"] = {"count": len(ids), "distinct": len(distinct), "min": distinct[0] if distinct else None,
                  "max": distinct[-1] if distinct else None, "list": distinct if len(distinct) <= 300 else None}
    out["list_fields"] = {f: {"records": len(s["lengths"]), "total": sum(s["lengths"]),
                              "median": statistics.median(s["lengths"]), "min": min(s["lengths"]),
                              "max": max(s["lengths"]), "empty": sum(1 for n in s["lengths"] if n == 0),
                              "mean_words": round(sum(s["words"]) / len(s["words"]), 2) if s["words"] else None}
                          for f, s in sorted(fields.items())}
    return out


def survey(remote, root, res):
    size = remote.probe()
    res["archive_bytes"] = size
    start = max(0, size - TAIL)
    eocd, at = find_eocd(remote.read(start, size - start), start)
    res["eocd"] = eocd
    n, cd_size, cd_off = eocd["entries"], eocd["cd_size"], eocd["cd_offset"]
    res["zip64"] = n == 0xFFFF or cd_size == 0xFFFFFFFF or cd_off == 0xFFFFFFFF
    if res["zip64"]:
        n, cd_size, cd_off = zip64_eocd(remote.read, at)
    if cd_size > MAX_CD:
        raise RuntimeError("central directory of %d bytes is over the %d-byte cap" % (cd_size, MAX_CD))
    members = parse_cd(remote.read(cd_off, cd_size))
    res["members_expected"], res["members_total"] = n, len(members)
    files = [m for m in members if not m["name"].endswith("/")]
    res["files"], res["files_bytes"] = len(files), sum(m["size"] for m in files)
    folders = {}
    for m in files:
        d = "/".join(m["name"].split("/")[:-1][:3])
        f = folders.setdefault(d, {"files": 0, "bytes": 0})
        f["files"] += 1
        f["bytes"] += m["size"]
    res["folders"] = folders
    res["members"] = [{k: m[k] for k in ("name", "size", "compressed", "method")} for m in members[:MAX_LISTED]]
    res["picked"], total = [], 0
    for m in (m for m in files if picked(m)):
        entry = {"name": m["name"], "size": m["size"], "compressed": m["compressed"]}
        res["picked"].append(entry)
        if m["compressed"] > MAX_MEMBER or m["size"] > MAX_UNPACKED or total + m["compressed"] > MAX_TOTAL:
            entry["skipped"] = "over the size caps"
            continue
        total += m["compressed"]
        try:
            raw = unpack(remote.read, m)
        except (ValueError, RuntimeError, OSError, zlib.error, struct.error) as e:
            entry["problem"] = "%s: %s" % (type(e).__name__, e)
            continue
        entry["sha256"] = hashlib.sha256(raw).hexdigest()
        entry["saved"] = save(root, m["name"], raw)
        entry["describe"] = describe(m["name"], raw)
    res["unpacked_compressed_bytes"] = total


def medaesqa_keys(items):
    """Per top-level field of the MedAESQA items: how often present, null, empty, and its shapes."""
    obj = items
    while isinstance(obj, dict) and len(obj) == 1 and isinstance(next(iter(obj.values())), (dict, list)):
        obj = next(iter(obj.values()))
    units = [u for u in (obj.values() if isinstance(obj, dict) else obj) if isinstance(u, dict)]
    fields = {}
    for u in units:
        for k, v in u.items():
            f = fields.setdefault(str(k), {"present": 0, "null": 0, "empty": 0, "shapes": {}})
            f["present"] += 1
            f["null"] += v is None
            f["empty"] += isinstance(v, (str, list, dict)) and len(v) == 0
            s = shape(v)[:400]
            f["shapes"][s] = f["shapes"].get(s, 0) + 1
    for f in fields.values():
        if len(f["shapes"]) > 5:
            f["shapes"] = {"<%d distinct shapes>" % len(f["shapes"]): sum(f["shapes"].values())}
    nested = {}
    for u in units:
        for m in (u.get("machine_generated_answers") or {}).values() if isinstance(u.get("machine_generated_answers"), dict) else []:
            if isinstance(m, dict):
                for k in m:
                    nested[str(k)] = nested.get(str(k), 0) + 1
    return {"items": len(units), "fields": fields, "machine_answer_fields": nested}


def get_medaesqa(path):
    if not (os.path.exists(path) and os.path.getsize(path) == MEDAESQA_BYTES):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        req = urllib.request.Request(MEDAESQA_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read(MEDAESQA_BYTES + 1)
        with open(path + ".part", "wb") as f:
            f.write(data)
        os.replace(path + ".part", path)
        cached = False
    else:
        cached = True
    with open(path, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    if len(data) != MEDAESQA_BYTES or sha != MEDAESQA_SHA:
        raise ValueError("medaesqa_v1.json: %d bytes, sha256 %s; pinned %d, %s" % (len(data), sha, MEDAESQA_BYTES, MEDAESQA_SHA))
    return data, {"bytes": len(data), "sha256": sha, "cached": cached}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("zip", "medaesqa"))
    ap.add_argument("--url", default=URL)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    res = {"version": VERSION, "started_utc": utc(), "problem": None}
    if a.what == "zip":
        res["url"] = a.url
        remote = Remote(a.url)
        try:
            survey(remote, os.path.join(a.data_dir, "bioace"), res)
        except Exception as e:  # recorded in the output, not hidden
            res["problem"] = "%s: %s" % (type(e).__name__, e)
        res["http"] = remote.summary()
        name, brief = "bioace_zip.json", ("problem", "archive_bytes", "files", "picked")
    else:
        try:
            data, res["file"] = get_medaesqa(os.path.join(a.data_dir, "medaesqa", "medaesqa_v1.json"))
            res.update(medaesqa_keys(json.loads(data.decode("utf-8-sig"))))
        except Exception as e:  # recorded in the output, not hidden
            res["problem"] = "%s: %s" % (type(e).__name__, e)
        name, brief = "medaesqa_keys.json", ("problem", "items", "fields")
    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res.get(k) for k in brief}, indent=1)[:20000])
    return 0 if res["problem"] is None else 1


if __name__ == "__main__":
    sys.exit(main())
