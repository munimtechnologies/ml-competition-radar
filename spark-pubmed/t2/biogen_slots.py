"""Citation-slot audit of the TREC 2024 BioGen judgments: when one answer sentence's citation list
holds the same PMID more than once, is that the run citing the paper twice, or the assessors
recording several evidence passages from one paper? And does counting each cited paper once per
sentence change the runs' citation scores, or the label agreement found by biogen_stance.py?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Job biogen-stance-v3 found that every repeated judgment inside one run is one citation slot
(topic, run, sentence, PMID) listed 2 to 7 times: 1,867 such slots, 567 of them with two
different labels. Each citation_assessment entry holds cited_pmid, evidence_relation and
evidence_support (the passage the assessor quoted, or null). This script:
  - classifies each repeated slot by its quoted passages: exact copies (two entries quote the
    identical passage), with null (some entry quotes none, the others all differ), or all
    distinct;
  - counts how often the PMID itself appears in the sentence text (runs that print citations);
  - recomputes each run's citation support and contradict rates (per question, then averaged
    over the run's questions, as in the track overview) three ways: per entry as released, per
    slot with each entry weighted 1/k, and per paper with one label per slot;
  - collapses each slot to that one paper-level label with the overview's definitions
    (Contradicts if any passage contradicts; Supports if one supports and none contradicts; then
    Neutral, Not relevant, Invalid) and re-measures agreement between slots of the identical
    (topic, sentence text, PMID).
Passages and sentences are hashed in memory and never written; the outputs are counts and run
names. Python standard library only; self-contained (the helpers match biogen_stance.py 0.3.0).
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from itertools import combinations

VERSION = "0.1.0"
ASSESS_URL = "https://trec.nist.gov/data/biogen/biogen_collection_v3.json"
ASSESS_SHA256 = "78449ef270e60abe0c268fa446ade23737164bba44c37308e216529fa63d066d"
LABELS = {"supporting": "supports", "contradicting": "contradicts", "neutral": "neutral",
          "notrelevant": "notrelevant", "invalidcitation": "invalid"}  # the file's own words, normalised
ORDER = ("supports", "contradicts", "neutral", "notrelevant", "invalid")
COLLAPSE = ("contradicts", "supports", "neutral", "notrelevant", "invalid")  # first present wins
PASSAGES = ("all_distinct", "with_null", "exact_copies")
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def label(v):
    return LABELS.get(re.sub(r"[\s_\-]+", "", v.lower())) if isinstance(v, str) else None


def pmid(v):
    s = str(v).strip() if isinstance(v, (int, str)) and not isinstance(v, bool) else ""
    return int(s) if s.isdigit() and 0 < len(s) <= 9 and int(s) > 0 else None


def text_key(s):
    """A short hash of the normalised text, or None for an empty one. Never written out."""
    t = " ".join(s.lower().split()) if isinstance(s, str) else ""
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16] if t else None


def entries(records):
    """(topic, run, sentence index, sentence key, pmid, label, passage key, times the PMID is
    printed in the sentence) per citation entry with a known label."""
    out = []
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
                text = s.get("answer_sentence") if isinstance(s.get("answer_sentence"), str) else ""
                tk = text_key(text)
                cites = s.get("citation_assessment")
                for c in (cites if isinstance(cites, list) else []):
                    if not isinstance(c, dict):
                        continue
                    lab = label(c.get("evidence_relation"))
                    if lab is None:
                        continue
                    p = pmid(c.get("cited_pmid"))
                    shown = len(re.findall(r"(?<!\d)%d(?!\d)" % p, text)) if p else 0
                    out.append((topic, str(run), j, tk, p, lab, text_key(c.get("evidence_support")), shown))
    return out


def shape(records):
    """Key sets of citation entries; per cited sentence, entries and distinct PMIDs."""
    keys, n_entries, n_pmids = Counter(), Counter(), Counter()
    for rec in records if isinstance(records, list) else []:
        runs = rec.get("machine_generated_answers") if isinstance(rec, dict) else None
        for ans in (runs.values() if isinstance(runs, dict) else []):
            sents = ans.get("answer_sentences") if isinstance(ans, dict) else None
            for s in sents if isinstance(sents, list) else []:
                cites = s.get("citation_assessment") if isinstance(s, dict) else None
                cs = [c for c in cites if isinstance(c, dict)] if isinstance(cites, list) else []
                if not cs:
                    continue
                for c in cs:
                    keys[",".join(sorted(str(k)[:40] for k in c))] += 1
                n_entries[len(cs)] += 1
                n_pmids[len({str(c.get("cited_pmid")) for c in cs})] += 1
    return keys, n_entries, n_pmids


def slots(es):
    """(topic, run, sentence, pmid) -> entries; an entry without a PMID is a slot of its own."""
    out = defaultdict(list)
    for n, e in enumerate(es):
        out[(e[0], e[1], e[2], e[4] if e[4] is not None else -n - 1)].append(e)
    return out


def passage_class(group):
    given = [e[6] for e in group if e[6] is not None]
    if len(set(given)) < len(given):
        return "exact_copies"
    return "with_null" if len(given) < len(group) else "all_distinct"


def same_passage_pairs(group):
    """(pairs of entries quoting the identical passage, how many of those differ in label)"""
    by = defaultdict(list)
    for e in group:
        if e[6] is not None:
            by[e[6]].append(e[5])
    pairs = differ = 0
    for labs in by.values():
        for a, b in combinations(labs, 2):
            pairs += 1
            differ += a != b
    return pairs, differ


def collapse(labels):
    """One paper-level label for a slot, from the track overview's definitions: Contradicts if any
    passage contradicts, Supports if one supports and none contradicts, then Neutral, Not
    relevant, Invalid."""
    return next(lab for lab in COLLAPSE if lab in labels)


def agreement(matrix, agree, pairs):
    """Specific agreement per label and Scott's pi from a pair matrix {"a|b": count}."""
    specific = {}
    for lab in ORDER[:4]:
        same = matrix.get("%s|%s" % (lab, lab), 0)
        other = sum(n for k, n in matrix.items() if lab in k.split("|") and k != "%s|%s" % (lab, lab))
        specific[lab] = round(2 * same / (2 * same + other), 4) if same or other else None
    occ = Counter()
    for k, n in matrix.items():
        a, b = k.split("|")
        occ[a] += n
        occ[b] += n
    tot = sum(occ.values())
    pe = sum((m / tot) ** 2 for m in occ.values()) if tot else 1.0
    pi = round((agree / pairs - pe) / (1 - pe), 4) if pairs and pe < 1 else None
    return specific, pi


def kendall(xs, ys):
    """Kendall's tau-b of two equal-length lists, or None when undefined."""
    conc = disc = tx = ty = 0
    for i, j in combinations(range(len(xs)), 2):
        dx, dy = xs[i] - xs[j], ys[i] - ys[j]
        if dx == 0 and dy == 0:
            continue
        if dx == 0:
            tx += 1
        elif dy == 0:
            ty += 1
        elif (dx > 0) == (dy > 0):
            conc += 1
        else:
            disc += 1
    d = math.sqrt((conc + disc + tx) * (conc + disc + ty))
    return round((conc - disc) / d, 4) if d else None


def rates(sl):
    """Per run: citation support and contradict rates per question, averaged over the run's
    questions; per entry as released, per slot (entries weighted 1/k) and per paper (one
    collapsed label per slot)."""
    per = defaultdict(lambda: defaultdict(lambda: [0.0] * 8))
    for k, g in sl.items():
        n = len(g)
        s = sum(e[5] == "supports" for e in g)
        c = sum(e[5] == "contradicts" for e in g)
        p = collapse({e[5] for e in g})
        row = per[k[1]][k[0]]
        for i, v in enumerate((n, s, c, 1, s / n, c / n, p == "supports", p == "contradicts")):
            row[i] += v
    out = {}
    for run in sorted(per):
        rows = list(per[run].values())

        def mean(i, d):
            return round(sum(r[i] / r[d] for r in rows) / len(rows), 4)
        out[run] = {"questions": len(rows), "entries": int(sum(r[0] for r in rows)),
                    "slots": int(sum(r[3] for r in rows)),
                    "support_rate_entries": mean(1, 0), "support_rate_slots": mean(4, 3),
                    "support_rate_papers": mean(6, 3), "contradict_rate_entries": mean(2, 0),
                    "contradict_rate_slots": mean(5, 3), "contradict_rate_papers": mean(7, 3)}
    return out


def compare(rt, a, b):
    runs = sorted(rt)
    xs, ys = [rt[r][a] for r in runs], [rt[r][b] for r in runs]

    def rank(m):
        return {r: i for i, r in enumerate(sorted(runs, key=lambda r: (-rt[r][m], r)))}
    ra, rb = rank(a), rank(b)
    return {"kendall_tau_b": kendall(xs, ys),
            "max_abs_change": round(max((abs(x - y) for x, y in zip(xs, ys)), default=0.0), 4),
            "runs_rank_changed": sum(ra[r] != rb[r] for r in runs)}


def paper_pairs(sl):
    """Pairs of slots with the identical (topic, sentence text, PMID), by collapsed label."""
    groups = defaultdict(list)
    for g in sl.values():
        e, lab = g[0], collapse({x[5] for x in g})
        if e[3] is not None and e[4] is not None and lab != "invalid":
            groups[(e[0], e[3], e[4])].append(lab)
    matrix, pairs, agree = Counter(), 0, 0
    for labs in groups.values():
        for a, b in combinations(labs, 2):
            matrix["|".join(sorted((a, b)))] += 1
            pairs += 1
            agree += a == b
    return dict(sorted(matrix.items())), pairs, agree


def counts(c):
    return {str(k): c[k] for k in sorted(c)}


def analyse(es, shp):
    keys, n_entries, n_pmids = shp
    sl = slots(es)  # rates count every labelled entry, Invalid included
    su = slots([e for e in es if e[5] != "invalid"])  # slot audit and agreement: as biogen_stance 0.3.0
    dup = {k: g for k, g in su.items() if len(g) >= 2}
    con = {k: g for k, g in dup.items() if len({e[5] for e in g}) > 1}
    cls = Counter(passage_class(g) for g in dup.values())
    cls_con = Counter(passage_class(g) for g in con.values())
    sp = [same_passage_pairs(g) for g in dup.values()]
    paper = Counter(collapse({e[5] for e in g}) for g in con.values())
    by_run = Counter(k[1] for k in dup)
    rt = rates(sl)
    matrix, pairs, agree = paper_pairs(su)
    specific, pi = agreement(matrix, agree, pairs)
    return {
        "entries": len(es),
        "entry_key_sets": dict(sorted(keys.items())),
        "cited_sentences": sum(n_entries.values()),
        "entries_per_cited_sentence": counts(n_entries),
        "pmids_per_cited_sentence": counts(n_pmids),
        "sentences_over_3_entries": sum(v for k, v in n_entries.items() if k > 3),
        "sentences_over_3_pmids": sum(v for k, v in n_pmids.items() if k > 3),
        "slots": len(sl),
        "slots_without_invalid": len(su),
        "duplicate_slots": len(dup),
        "duplicate_slots_conflicting": len(con),
        "duplicate_slot_sizes": counts(Counter(len(g) for g in dup.values())),
        "entries_in_duplicate_slots": sum(len(g) for g in dup.values()),
        "duplicate_slot_passages": {c: cls[c] for c in PASSAGES},
        "conflicting_slot_passages": {c: cls_con[c] for c in PASSAGES},
        "same_passage_pairs": sum(p for p, _ in sp),
        "same_passage_pairs_differ": sum(d for _, d in sp),
        # times the PMID is printed in the sentence text; "2" means 2 or more
        "pmid_shown_duplicate_slots": counts(Counter(min(g[0][7], 2) for g in dup.values())),
        "pmid_shown_single_slots": counts(Counter(min(g[0][7], 2) for g in su.values() if len(g) == 1)),
        "conflicting_slot_label_sets": dict(sorted(Counter(
            "+".join(sorted({e[5] for e in g})) for g in con.values()).items())),
        "conflicting_slot_paper_label": {lab: paper[lab] for lab in COLLAPSE if paper[lab]},
        "runs_with_entries": len(rt),
        "runs_with_duplicate_slots": len(by_run),
        "largest_run_share_of_duplicate_slots": round(max(by_run.values()) / len(dup), 4) if dup else None,
        "rank_compare": {
            "support_entries_vs_slots": compare(rt, "support_rate_entries", "support_rate_slots"),
            "support_entries_vs_papers": compare(rt, "support_rate_entries", "support_rate_papers"),
            "contradict_entries_vs_papers": compare(rt, "contradict_rate_entries", "contradict_rate_papers")},
        "paper_level_pairs": pairs,
        "paper_level_agree": agree,
        "paper_level_agreement": round(agree / pairs, 4) if pairs else None,
        "paper_level_pair_matrix": matrix,
        "paper_level_specific_agreement": specific,
        "paper_level_scotts_pi": pi,
        "per_run": rt,
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
            records = json.load(f)
        res.update(analyse(entries(records), shape(records)))
        res["seconds"] = round(time.time() - t0, 1)
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    dump(os.path.join(a.out_dir, "slots.json"), res)
    print(json.dumps(res, indent=1))
    return 1 if res["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
