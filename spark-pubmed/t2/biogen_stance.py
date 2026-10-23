"""Stance census of the TREC 2024 BioGen citation judgments: when one paper is judged both
"supporting" and "contradicting" within a topic, is that two different claims, or one claim
judged two ways?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Job biogen-census-v2 found that 168 of the 202 topic-paper pairs judged "contradicting" are also
judged "supporting" in the same topic. This job splits those mixed pairs by where the two labels
meet:
  same_text  the same sentence text (identical after lower-casing and collapsing white space;
             repeats happen when runs share a generator) cites the paper under both labels,
             so one claim was judged two ways
  same_run   one run's answer cites the paper under both labels, in different sentences
  across     only different runs' different sentences
It also measures label agreement wherever the same sentence text citing the same PMID in the
same topic was judged more than once. Sentence text is hashed in memory and never written; the
outputs are counts, topic ids, run names and PMIDs. Python standard library only.

Reads biogen_collection_v3.json from the data volume that biogen_census.py fills
(/data/biogen2024/assessments.json), downloading it again only if it is missing, and stops unless
its sha256 is the one jobs biogen-census-v1 and -v2 recorded.
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
from collections import Counter, defaultdict

VERSION = "0.1.0"
ASSESS_URL = "https://trec.nist.gov/data/biogen/biogen_collection_v3.json"
ASSESS_SHA256 = "78449ef270e60abe0c268fa446ade23737164bba44c37308e216529fa63d066d"
LABELS = {"supporting": "supports", "contradicting": "contradicts", "neutral": "neutral",
          "notrelevant": "notrelevant", "invalidcitation": "invalid"}  # the file's own words, normalised
ORDER = ("supports", "contradicts", "neutral", "notrelevant", "invalid")
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def label(v):
    return LABELS.get(re.sub(r"[\s_\-]+", "", v.lower())) if isinstance(v, str) else None


def pmid(v):
    s = str(v).strip() if isinstance(v, (int, str)) and not isinstance(v, bool) else ""
    return int(s) if s.isdigit() and 0 < len(s) <= 9 and int(s) > 0 else None


def text_key(s):
    """A short hash of the normalised sentence, or None for an empty one. Never written out."""
    t = " ".join(s.lower().split()) if isinstance(s, str) else ""
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16] if t else None


def judgments(records):
    """(topic, run, sentence index, text key, pmid, label) per citation judgment, plus a Counter
    of evidence_relation values that are not label words (short strings, else the type name)."""
    out, unknown = [], Counter()
    for i, rec in enumerate(records if isinstance(records, list) else []):
        if not isinstance(rec, dict):
            continue
        topic = str(rec.get("question_id", i))
        runs = rec.get("machine_generated_answers")
        for run, ans in (runs.items() if isinstance(runs, dict) else []):
            sents = ans.get("answer_sentences") if isinstance(ans, dict) else None
            for j, s in enumerate(sents if isinstance(sents, list) else []):
                if not isinstance(s, dict):
                    continue
                tk = text_key(s.get("answer_sentence"))
                cites = s.get("citation_assessment")
                for c in (cites if isinstance(cites, list) else []):
                    if not isinstance(c, dict):
                        continue
                    v = c.get("evidence_relation")
                    lab = label(v)
                    if lab is None:
                        unknown[v if isinstance(v, str) and len(v) <= 30 else type(v).__name__] += 1
                        continue
                    out.append((topic, str(run), j, tk, pmid(c.get("cited_pmid")), lab))
    return out, unknown


def topic_order(t):
    return (len(t), t)


def analyse(js):
    labels = Counter(j[5] for j in js)
    usable = [j for j in js if j[5] != "invalid" and j[4] is not None]
    by_pair = defaultdict(list)  # (topic, pmid) -> judgments
    for j in usable:
        by_pair[(j[0], j[4])].append(j)
    contra = sorted(k for k, v in by_pair.items() if any(x[5] == "contradicts" for x in v))
    mixed = [k for k in contra if any(x[5] == "supports" for x in by_pair[k])]
    kinds, topics = Counter(), {}
    texts_sup, texts_con = [], []
    for k in contra:
        row = topics.setdefault(k[0], Counter())
        row["contradicting_pmids"] += 1
        row["contradicts_judgments"] += sum(1 for x in by_pair[k] if x[5] == "contradicts")
    for k in mixed:
        v = by_pair[k]
        sup = [x for x in v if x[5] == "supports"]
        con = [x for x in v if x[5] == "contradicts"]
        same_text = bool({x[3] for x in sup if x[3]} & {x[3] for x in con if x[3]})
        same_run = bool({x[1] for x in sup} & {x[1] for x in con})
        kinds["same_text"] += same_text
        kinds["same_run"] += same_run
        kinds["same_run_not_same_text"] += same_run and not same_text
        kinds["across_only"] += not same_text and not same_run
        kinds["supports_judgments"] += len(sup)
        kinds["contradicts_judgments"] += len(con)
        texts_sup.append(len({x[3] for x in sup}))
        texts_con.append(len({x[3] for x in con}))
        row = topics[k[0]]
        row["mixed_pmids"] += 1
        row["mixed_same_text"] += same_text
        row["mixed_same_run"] += same_run
    groups = defaultdict(list)  # (topic, text key, pmid) -> labels
    for j in usable:
        if j[3]:
            groups[(j[0], j[3], j[4])].append(j[5])
    rep = [v for v in groups.values() if len(v) >= 2]
    pairs = agree = 0
    confusion = Counter()
    for v in rep:
        c = Counter(v)
        n = len(v)
        pairs += n * (n - 1) // 2
        agree += sum(m * (m - 1) // 2 for m in c.values())
        labs = sorted(c)
        for a in range(len(labs)):
            for b in range(a + 1, len(labs)):
                confusion["%s|%s" % (labs[a], labs[b])] += c[labs[a]] * c[labs[b]]
    rep_con = [v for v in rep if "contradicts" in v]
    cols = ("contradicts_judgments", "contradicting_pmids", "mixed_pmids", "mixed_same_text",
            "mixed_same_run")
    return {
        "judgments": len(js), "labels": {lab: labels[lab] for lab in ORDER},
        "judgments_without_pmid": sum(1 for j in js if j[4] is None),
        "topics": len({j[0] for j in js}), "runs": len({j[1] for j in js}),
        "contradicting_pairs": len(contra), "mixed_pairs": len(mixed),
        "contradiction_only_pairs": len(contra) - len(mixed),
        "mixed_same_text": kinds["same_text"], "mixed_same_run": kinds["same_run"],
        "mixed_same_run_not_same_text": kinds["same_run_not_same_text"],
        "mixed_across_only": kinds["across_only"],
        "contradicts_judgments_on_mixed_pairs": kinds["contradicts_judgments"],
        "supports_judgments_on_mixed_pairs": kinds["supports_judgments"],
        "mixed_supports_texts_median": statistics.median(texts_sup) if texts_sup else None,
        "mixed_contradicts_texts_median": statistics.median(texts_con) if texts_con else None,
        "repeated_groups": len(rep), "repeated_groups_all_agree": sum(1 for v in rep if len(set(v)) == 1),
        "repeated_judgment_pairs": pairs, "repeated_pairs_agree": agree,
        "repeated_pair_agreement": round(agree / pairs, 4) if pairs else None,
        "repeated_pair_confusion": dict(sorted(confusion.items())),
        "repeated_groups_with_contradicts": len(rep_con),
        "repeated_groups_with_contradicts_all_agree": sum(1 for v in rep_con if len(set(v)) == 1),
        "per_topic": [{"topic": t, **{c: topics.get(t, Counter())[c] for c in cols}}
                      for t in sorted({j[0] for j in js}, key=topic_order)],
    }


def fetch(url, dest, max_bytes=64 << 20):
    """Reuse dest if present, else stream url to it via .part (fsynced). Returns a record."""
    rec = {"url": url, "cached": os.path.exists(dest)}
    if not rec["cached"]:
        os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        n, tmp = 0, dest + ".part"
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            for b in iter(lambda: r.read(1 << 20), b""):
                n += len(b)
                if n > max_bytes:
                    raise ValueError("%s: over %d bytes" % (url, max_bytes))
                f.write(b)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dest)
    h, n = hashlib.sha256(), 0
    with open(dest, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
            n += len(b)
    rec.update(bytes=n, sha256=h.hexdigest())
    return rec


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--url", default=ASSESS_URL)
    ap.add_argument("--sha256", default=ASSESS_SHA256)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    res = {"version": VERSION, "problem": None}
    try:
        res["file"] = fetch(a.url, os.path.join(a.data_dir, "assessments.json"))
        if res["file"]["sha256"] != a.sha256.lower():
            raise ValueError("sha256 %s, expected %s" % (res["file"]["sha256"], a.sha256))
        t0 = time.time()
        with open(os.path.join(a.data_dir, "assessments.json"), encoding="utf-8-sig") as f:
            js, unknown = judgments(json.load(f))
        res["unknown_relations"] = dict(unknown)
        res.update(analyse(js))
        res["seconds"] = round(time.time() - t0, 1)
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    dump(os.path.join(a.out_dir, "stance.json"), res)
    print(json.dumps({k: v for k, v in res.items() if k != "per_topic"}, indent=1))
    return 1 if res["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
