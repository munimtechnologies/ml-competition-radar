"""Census of NIST's TREC 2024 BioGen assessments, as a development proxy for SPARK Task 2.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

SPARK Task 2 scores evidence-grounded answers with citations, including how well they cover
conflicting findings, but has published no development data. TREC 2024 BioGen judged every
PubMed citation that 30 runs attached to answer sentences for 65 health questions (Supports,
Contradicts, Neutral, Not Relevant) and labelled the sentences (Required, Unnecessary,
Borderline, Inappropriate). The 2025 track recommends these assessments for development.

This job downloads the topics and the assessments from trec.nist.gov, hashes them, and writes
counts only, never question, answer or abstract text:
  download.json  urls, bytes, sha256
  topics.json    number of topics, id range, keys
  schema.json    every key path (digit keys folded to {n}) with types, sizes and label values
  census.json    label totals, per-topic contradiction counts, judged PMIDs
  gold_t2.jsonl  per topic: the PMIDs judged under each citation label, plus sentence-label counts
The file's layout is not documented, so labels are found by value (the eight label words) and a
citation's PMID is a PMID-like sibling under a key naming a document ("record") or the digit key
the label sits under ("keyed"). Python standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import time
import urllib.request
from collections import Counter

VERSION = "0.1.0"
TOPICS_URL = "https://trec.nist.gov/data/biogen/BioGen2024topics-json.txt"
ASSESS_URL = "https://trec.nist.gov/data/biogen/biogen_collection_v3.json"
SENT_LABELS = ("required", "unnecessary", "borderline", "inappropriate")
CITE_LABELS = ("supports", "contradicts", "neutral", "notrelevant")
TOPIC_KEYS = ("topic_id", "topicid", "qid", "question_id", "id", "topic")  # first match wins
PMID_HINTS = ("pmid", "doc", "cit", "ref")
PMID_RX = re.compile(r"(?:pmid[:\s]*)?([1-9][0-9]{0,8})", re.I)
ID_RX = re.compile(r"[A-Za-z0-9_\-]{1,40}")  # an id, never a phrase: keys like this are kept
SPARK_MAX_PMID = 42671487  # highest PMID in the SPARK corpus (corpus_build/RESULTS.md)
MAX_PARSE_BYTES = 300 * 1024 * 1024  # json.load needs several times the file size in RAM
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def norm(s):
    return re.sub(r"[\s_\-]+", "", s.strip().lower())


def label_of(v):
    """('sent', label) or ('cite', label) if v is one of the eight label words, else None."""
    if isinstance(v, str) and len(v) <= 30:
        n = norm(v)
        if n in SENT_LABELS:
            return "sent", n
        if n in CITE_LABELS:
            return "cite", n
    return None


def pmid_of(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v if 0 < v < 10 ** 9 else None
    if isinstance(v, str):
        m = PMID_RX.fullmatch(v.strip())
        return int(m.group(1)) if m else None
    return None


def download(url, dest, max_bytes, minutes=20):
    """Stream url to dest (via .part, fsynced); reuse dest if it exists. Returns a record."""
    if os.path.exists(dest):
        h, n = hashlib.sha256(), 0
        with open(dest, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
                n += len(b)
        return {"url": url, "bytes": n, "sha256": h.hexdigest(), "cached": True}
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    tmp, h, n, t0 = dest + ".part", hashlib.sha256(), 0, time.time()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        want = r.headers.get("Content-Length")
        for b in iter(lambda: r.read(1 << 20), b""):
            n += len(b)
            if n > max_bytes:
                raise ValueError("%s: over %d bytes" % (url, max_bytes))
            if time.time() - t0 > minutes * 60:
                raise TimeoutError("%s: over %d minutes" % (url, minutes))
            h.update(b)
            f.write(b)
        f.flush()
        os.fsync(f.fileno())
    if want and int(want) != n:
        raise ValueError("%s: got %d bytes, Content-Length %s" % (url, n, want))
    os.replace(tmp, dest)
    return {"url": url, "bytes": n, "sha256": h.hexdigest(), "cached": False,
            "seconds": round(time.time() - t0, 1)}


def gen_key(k):
    k = str(k)
    if k.isdigit():
        return "{n}"
    return k if ID_RX.fullmatch(k) else "{text}"


def schema(obj, max_paths=2000, max_values=20):
    """Key paths with counts, types, size range and (for short strings) up to max_values
    distinct values; strings over 30 characters or 3 words are never kept."""
    paths, stack = {}, [("$", obj)]
    while stack:
        path, o = stack.pop()
        p = paths.get(path)
        if p is None:
            if len(paths) >= max_paths:
                continue
            p = paths[path] = {"count": 0, "types": Counter(), "min": None, "max": None,
                               "values": set(), "many_values": False}
        p["count"] += 1
        p["types"][type(o).__name__] += 1
        size = None
        if isinstance(o, dict):
            size = len(o)
            stack.extend((path + "." + gen_key(k), v) for k, v in o.items())
        elif isinstance(o, list):
            size = len(o)
            stack.extend((path + "[]", v) for v in o)
        elif isinstance(o, str):
            size = len(o)
            if len(o) <= 30 and len(o.split()) <= 3 and not p["many_values"]:
                p["values"].add(o)
                if len(p["values"]) > max_values:
                    p["values"], p["many_values"] = set(), True
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            size = o
        if size is not None:
            p["min"] = size if p["min"] is None else min(p["min"], size)
            p["max"] = size if p["max"] is None else max(p["max"], size)
    return {k: {"count": v["count"], "types": dict(v["types"]), "min": v["min"], "max": v["max"],
                "values": sorted(v["values"]) if v["values"] else None,
                "many_values": v["many_values"]} for k, v in sorted(paths.items())}


def unwrap(obj):
    while isinstance(obj, dict) and len(obj) == 1:
        v = next(iter(obj.values()))
        if not isinstance(v, (dict, list)):
            break
        obj = v
    return obj


def topic_key(unit, fallback):
    if isinstance(unit, dict):
        for want in TOPIC_KEYS:
            for k, v in unit.items():
                if (norm(str(k)) == norm(want) and isinstance(v, (int, str))
                        and not isinstance(v, bool) and ID_RX.fullmatch(str(v))):
                    return str(v)
    return str(fallback)


def units(obj):
    """(topic key, unit) pairs: list items (grouped by a topic-id field when one exists) or the
    items of a dict keyed by topic. A key that is not id-like becomes its position."""
    obj = unwrap(obj)
    if isinstance(obj, list):
        return [(topic_key(u, i), u) for i, u in enumerate(obj)]
    if isinstance(obj, dict):
        return [(str(k) if ID_RX.fullmatch(str(k)) else str(i), v)
                for i, (k, v) in enumerate(obj.items())]
    return []


def judgments(unit):
    """(kind, label, pmid or None, how) for every label word found in a unit."""
    out, stack = [], [(None, unit)]
    while stack:
        key, o = stack.pop()
        if isinstance(o, dict):
            pm = next((pmid_of(v) for k, v in o.items()
                       if any(h in str(k).lower() for h in PMID_HINTS) and pmid_of(v) is not None), None)
            how = "record" if pm is not None else None
            if pm is None and key is not None and str(key).isdigit():
                pm, how = int(key), "keyed"
            for k, v in o.items():
                lab = label_of(v)
                if lab and lab[0] == "cite" and pm is None and str(k).isdigit():
                    out.append(("cite", lab[1], int(k), "keyed"))
                elif lab:
                    cite = lab[0] == "cite"
                    out.append((lab[0], lab[1], pm if cite else None, how if cite else None))
                elif isinstance(v, (dict, list)):
                    stack.append((k, v))
        elif isinstance(o, list):
            for v in o:
                lab = label_of(v)
                if lab:
                    out.append((lab[0], lab[1], None, None))
                elif isinstance(v, (dict, list)):
                    stack.append((None, v))
    return out


def census(assess, topic_ids=None):
    """Returns (census dict, gold rows)."""
    us = units(assess)
    per, hows = {}, Counter()
    for key, u in us:
        t = per.setdefault(key, {"units": 0, "sent": Counter(), "cite": Counter(),
                                 "pmids": {lab: set() for lab in CITE_LABELS}, "cite_no_pmid": 0})
        t["units"] += 1
        for kind, lab, pm, how in judgments(u):
            t[kind][lab] += 1
            if kind == "cite":
                if pm is None:
                    t["cite_no_pmid"] += 1
                else:
                    t["pmids"][lab].add(pm)
                    hows[how] += 1
    sent, cite = Counter(), Counter()
    allp, both = set(), 0
    for t in per.values():
        sent.update(t["sent"])
        cite.update(t["cite"])
        for s in t["pmids"].values():
            allp |= s
        both += len(t["pmids"]["supports"] & t["pmids"]["contradicts"])
    n_cite = sum(cite.values())
    contra = [t["cite"]["contradicts"] for t in per.values()]
    contra_p = [len(t["pmids"]["contradicts"]) for t in per.values()]
    out = {"version": VERSION, "units": len(us), "topics": len(per),
           "units_per_topic_max": max((t["units"] for t in per.values()), default=0),
           "sentence_labels": {lab: sent[lab] for lab in SENT_LABELS},
           "citation_labels": {lab: cite[lab] for lab in CITE_LABELS},
           "citation_label_share": {lab: round(cite[lab] / n_cite, 4) if n_cite else None
                                    for lab in CITE_LABELS},
           "citations_without_pmid": sum(t["cite_no_pmid"] for t in per.values()),
           "pmid_pattern": dict(hows),
           "topics_with_contradicts": sum(1 for c in contra if c),
           "topics_with_contradicts_pmid": sum(1 for c in contra_p if c),
           "contradicts_per_topic_median": statistics.median(contra) if contra else None,
           "contradicts_per_topic_max": max(contra, default=None),
           "contradicts_pmids_per_topic_median": statistics.median(contra_p) if contra_p else None,
           "distinct_pmids": len(allp),
           "distinct_pmids_by_label": {lab: len(set().union(*(t["pmids"][lab] for t in per.values())))
                                       for lab in CITE_LABELS} if per else {},
           "topic_pmid_pairs_supports_and_contradicts": both,
           "pmid_min": min(allp, default=None), "pmid_max": max(allp, default=None),
           "pmids_over_spark_max": sum(1 for p in allp if p > SPARK_MAX_PMID)}
    if topic_ids is not None:
        ids = {str(i) for i in topic_ids}
        out["topic_keys_matching_topic_ids"] = sum(1 for k in per if k in ids)
    gold = [{"topic": k, **{lab: sorted(t["pmids"][lab]) for lab in CITE_LABELS},
             "sentence_labels": {lab: t["sent"][lab] for lab in SENT_LABELS},
             "citations_without_pmid": t["cite_no_pmid"]}
            for k, t in sorted(per.items(), key=lambda kv: (len(kv[0]), kv[0]))]
    return out, gold


def topics_summary(obj):
    rows = unwrap(obj)
    rows = rows if isinstance(rows, list) else []
    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    ints = sorted(i for i in ids if isinstance(i, int) and not isinstance(i, bool))
    return {"topics": len(rows), "ids_int": len(ints), "id_min": ints[0] if ints else None,
            "id_max": ints[-1] if ints else None,
            "contiguous": bool(ints) and ints == list(range(ints[0], ints[0] + len(ints))),
            "keys": sorted({k for r in rows if isinstance(r, dict) for k in r}), "ids": ints}


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--topics-url", default=TOPICS_URL)
    ap.add_argument("--assess-url", default=ASSESS_URL)
    ap.add_argument("--max-mb", type=int, default=1024)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    res = {"version": VERSION, "problem": None}
    try:
        dl = [download(a.topics_url, os.path.join(a.data_dir, "topics.json"), 5 << 20),
              download(a.assess_url, os.path.join(a.data_dir, "assessments.json"), a.max_mb << 20)]
        dump(os.path.join(a.out_dir, "download.json"), dl)
        with open(os.path.join(a.data_dir, "topics.json"), encoding="utf-8-sig") as f:
            ts = topics_summary(json.load(f))
        dump(os.path.join(a.out_dir, "topics.json"), ts)
        if dl[1]["bytes"] > MAX_PARSE_BYTES:
            raise ValueError("assessments are %d bytes, over the parse limit" % dl[1]["bytes"])
        t0 = time.time()
        with open(os.path.join(a.data_dir, "assessments.json"), encoding="utf-8-sig") as f:
            assess = json.load(f)
        res["parse_seconds"] = round(time.time() - t0, 1)
        dump(os.path.join(a.out_dir, "schema.json"), schema(assess))
        c, gold = census(assess, ts["ids"])
        res.update(c)
        with open(os.path.join(a.out_dir, "gold_t2.jsonl"), "w", encoding="utf-8") as f:
            for g in gold:
                f.write(json.dumps(g) + "\n")
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    dump(os.path.join(a.out_dir, "census.json"), res)
    print(json.dumps(res, indent=1)[:4000])
    return 1 if res["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
