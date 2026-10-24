"""Helpers for job t2dev-v1, the first SPARK Task 2 development run on the whole PubMed index.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

  wait --path F --minutes M --out F   poll until F exists or M minutes pass; always exit 0. Used to
                                      let spark35-score-v2 finish its timed queries first, so two
                                      jobs never read the 92.5 GB index at once.
  gold --census-dir D --out-dir D     check biogen_census.py's download.json against the pinned
                                      sizes and sha256, then turn its gold_t2.jsonl into t1.py gold
                                      files: gold_supports.jsonl (papers judged Supports) and
                                      gold_relevant.jsonl (Supports, Contradicts or Neutral, the
                                      track overview's "relevant").

The released BioGen 2024 assessments are passage-level (job biogen-slots-v1), so gold here is
per topic and per paper, never per entry. Writes topic ids and PMIDs only, never text. Standard
library only.
"""
import argparse
import json
import os
import sys
import time

VERSION = "0.1.0"
PINS = {"BioGen2024topics-json.txt": (21598, "d456904111ed963552eda412c224107dccf632fc54d04d23b47f9b8878374774"),
        "biogen_collection_v3.json": (11128359, "78449ef270e60abe0c268fa446ade23737164bba44c37308e216529fa63d066d")}
SETS = (("supports", ("supports",)), ("relevant", ("supports", "contradicts", "neutral")))


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def wait_for(path, minutes, poll=60.0, clock=time.monotonic, sleep=time.sleep):
    t0 = clock()
    while True:
        found = os.path.exists(path)
        if found or clock() - t0 >= minutes * 60:
            return {"path": path, "found": found, "waited_seconds": round(clock() - t0, 1)}
        sleep(poll)


def check_pins(downloads, pins=PINS):
    """Problems with download.json rows (empty list = every pinned file, as pinned)."""
    problems, seen = [], set()
    for d in downloads:
        name = d["url"].rsplit("/", 1)[-1]
        if name not in pins:
            problems.append("unexpected file %s" % name)
            continue
        seen.add(name)
        size, sha = pins[name]
        if d.get("bytes") != size or d.get("sha256") != sha:
            problems.append("%s: %s bytes, sha256 %s; expected %d, %s" % (name, d.get("bytes"),
                                                                        d.get("sha256"), size, sha))
    return problems + ["missing %s" % n for n in sorted(set(pins) - seen)]


def t1_gold(rows, labels):
    """t1.py gold rows: one per topic with at least one PMID under the labels."""
    out = []
    for g in rows:
        pmids = sorted({str(p) for lab in labels for p in g.get(lab, [])}, key=lambda p: (len(p), p))
        if pmids:
            out.append({"info_need_id": str(g["topic"]), "gold": pmids})
    return out


def gold(census_dir, out_dir):
    with open(os.path.join(census_dir, "download.json"), encoding="utf-8") as f:
        problems = check_pins(json.load(f))
    rows = load_jsonl(os.path.join(census_dir, "gold_t2.jsonl"))
    os.makedirs(out_dir, exist_ok=True)
    res = {"version": VERSION, "problems": problems, "topics": len(rows)}
    for name, labels in SETS:
        g = t1_gold(rows, labels)
        write_jsonl(os.path.join(out_dir, "gold_%s.jsonl" % name), g)
        res[name] = {"topics": len(g), "pmids": sum(len(x["gold"]) for x in g),
                     "distinct_pmids": len({p for x in g for p in x["gold"]})}
    dump(os.path.join(out_dir, "gold.json"), res)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("wait")
    w.add_argument("--path", required=True)
    w.add_argument("--minutes", type=float, required=True)
    w.add_argument("--out", required=True)
    g = sub.add_parser("gold")
    g.add_argument("--census-dir", required=True)
    g.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "wait":
        res = dict(wait_for(a.path, a.minutes), version=VERSION)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        dump(a.out, res)
        bad = False
    else:
        res = gold(a.census_dir, a.out_dir)
        bad = bool(res["problems"]) or not res["topics"]
    print(json.dumps(res, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
