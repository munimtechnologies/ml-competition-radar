"""Do negation cues mark the passages the TREC 2024 BioGen assessors judged Contradicts?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

compose.py 0.2.0 flags a conflict with negation and null-finding cues, and in t2dev-v1 that flag
fired on no answer. A TREC 2025 BioGen system (arXiv 2603.17580) keeps only sentences with
negation cues before its NLI step, on the view that contradicting evidence is mostly negation.
This checks that view on human labels: for each judged citation it applies compose.py 0.2.0's own
cue patterns (copied verbatim) to the quoted passage of the cited paper (evidence_support) and to
the answer sentence, and reports how often each cue fires per label and how well each separates
Contradicts, per judgment (entry) and per citation slot (topic, run, sentence, PMID; Contradicts
if any entry is, the overview's rule).

Outputs are counts and rates only, never question, sentence or passage text. Standard library
only.

  python cue_check.py --data-dir DIR --out-dir DIR
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from collections import Counter

VERSION = "0.1.0"
ASSESS_URL = "https://trec.nist.gov/data/biogen/biogen_collection_v3.json"
ASSESS_SHA256 = "78449ef270e60abe0c268fa446ade23737164bba44c37308e216529fa63d066d"
LABELS = {"supporting": "supports", "contradicting": "contradicts", "neutral": "neutral",
          "notrelevant": "notrelevant", "invalidcitation": "invalid"}  # the file's own words, normalised
ORDER = ("supports", "contradicts", "neutral", "notrelevant", "invalid")
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"

# compose.py 0.2.0's patterns, verbatim (spark-pubmed/t2/compose.py)
NEG_RX = re.compile(r"\b(?:no|not|did not|does not|do not|was not|were not|failed to|neither|nor|"
                    r"without|lack of|absence of|ineffective|unaffected|unchanged|similar)\b", re.I)
NULL_RX = re.compile(r"\b(?:no (?:significant|statistically significant|clear|consistent) "
                     r"(?:difference|effect|association|benefit|improvement|change|reduction|increase)s?|"
                     r"not (?:significantly )?(?:associated|different|effective|improve[ds]?|reduce[ds]?|"
                     r"increase[ds]?)|did not (?:differ|improve|reduce|increase|change|affect)|"
                     r"no evidence|failed to (?:show|demonstrate|improve|reduce))\b", re.I)
POS_RX = re.compile(r"\b(?:significant(?:ly)?|associated with|improve[ds]?|reduce[ds]?|increase[ds]?|"
                    r"effective|benefit(?:s|ed)?|lower(?:ed)? risk|higher risk)\b", re.I)
HEDGE_RX = re.compile(r"\b(?:conflicting|controvers(?:y|ial)|inconsistent|mixed (?:results|evidence|"
                      r"findings)|remains? (?:unclear|uncertain|debated|controversial)|debate[ds]?|"
                      r"insufficient evidence|limited evidence|evidence is (?:weak|limited|lacking))\b", re.I)
FEATURES = ("neg_passage", "null_passage", "hedge_passage", "neg_sentence", "neg_mismatch",
            "polarity_clash")


def label(v):
    return LABELS.get(re.sub(r"[\s_\-]+", "", v.lower())) if isinstance(v, str) else None


def pmid(v):
    s = str(v).strip() if isinstance(v, (int, str)) and not isinstance(v, bool) else ""
    return int(s) if s.isdigit() and 0 < len(s) <= 9 and int(s) > 0 else None


def norm_text(v):
    """Collapse white space; a list of strings is joined first; anything else is empty."""
    if isinstance(v, list):
        v = " ".join(x for x in v if isinstance(x, str))
    return " ".join(v.split()) if isinstance(v, str) else ""


def rnd(x):
    return None if x is None else round(x, 4)


def fetch(url, dest, max_bytes):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    n, tmp = 0, dest + ".part"
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        for b in iter(lambda: r.read(1 << 20), b""):
            n += len(b)
            if n > max_bytes:
                raise ValueError("%s: more than %d bytes" % (url, max_bytes))
            f.write(b)
    os.replace(tmp, dest)
    return {"url": url, "bytes": n}


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def entries(records):
    """One tuple per labelled citation judgment: (topic, run, sentence index, pmid or None, label,
    passage, sentence), plus a Counter of judgments whose label is not one of the file's words."""
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
                sent = norm_text(s.get("answer_sentence"))
                cites = s.get("citation_assessment")
                for c in (cites if isinstance(cites, list) else []):
                    if not isinstance(c, dict):
                        continue
                    lab = label(c.get("evidence_relation"))
                    if lab is None:
                        unknown["unknown_label"] += 1
                        continue
                    out.append((topic, str(run), j, pmid(c.get("cited_pmid")), lab,
                                norm_text(c.get("evidence_support")), sent))
    return out, unknown


def census(ents):
    """Topic-paper counts over every labelled judgment with a valid PMID (biogen-census-v2's 202
    contradicting papers, 168 of them also supporting)."""
    tp = {}
    for topic, _, _, pm, lab, _, _ in ents:
        if pm is not None:
            tp.setdefault((topic, pm), set()).add(lab)
    return {"topic_papers": len(tp),
            "topic_papers_contradicts": sum(1 for v in tp.values() if "contradicts" in v),
            "topic_papers_mixed": sum(1 for v in tp.values() if {"contradicts", "supports"} <= v)}


def polarity(text):
    """compose.py 0.2.0's rule: 'null' (reports no effect), 'finding', or None."""
    if NULL_RX.search(text):
        return "null"
    if POS_RX.search(text) and not NEG_RX.search(text):
        return "finding"
    return None


def features(passage, sentence):
    """Each cue on one (passage, answer sentence) pair. polarity_clash is compose.py 0.2.0's
    conflict rule (one side reports no effect, the other a finding) applied to the pair."""
    neg_p, neg_s = bool(NEG_RX.search(passage)), bool(NEG_RX.search(sentence))
    return {"neg_passage": neg_p, "null_passage": bool(NULL_RX.search(passage)),
            "hedge_passage": bool(HEDGE_RX.search(passage)), "neg_sentence": neg_s,
            "neg_mismatch": neg_p != neg_s,
            "polarity_clash": {polarity(passage), polarity(sentence)} == {"null", "finding"}}


def prf(pred, gold):
    tp = sum(1 for p, g in zip(pred, gold) if p and g)
    fp = sum(1 for p, g in zip(pred, gold) if p and not g)
    fn = sum(1 for p, g in zip(pred, gold) if g and not p)
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": rnd(tp / (tp + fp)) if tp + fp else None,
            "recall": rnd(tp / (tp + fn)) if tp + fn else None,
            "f1": rnd(2 * tp / (2 * tp + fp + fn)) if tp else 0.0}


def flag_block(gold, pred):
    """prf plus how often the flag fires and its lift (precision over prevalence)."""
    n1 = sum(1 for g in gold if g)
    r = prf(pred, gold)
    r.update({"n": len(gold), "positives": n1, "prevalence": rnd(n1 / len(gold)) if gold else None,
              "fires": r["tp"] + r["fp"],
              "lift": rnd(r["tp"] / (r["tp"] + r["fp"]) / (n1 / len(gold)))
              if r["tp"] + r["fp"] and n1 else None})
    return r


def grouped(keys, gold, pred):
    """Collapse rows by key: positive if any row is, flagged if any row is."""
    g = {}
    for k, y, p in zip(keys, gold, pred):
        a = g.setdefault(k, [False, False])
        a[0], a[1] = a[0] or y, a[1] or p
    v = list(g.values())
    return [a[0] for a in v], [a[1] for a in v]


def evaluate(ents):
    """ents: scored entry tuples. Per cue: fires and rate per label, the Contradicts/Supports rate
    ratio, and flag_block for Contradicts vs rest, vs Supports only, and per slot."""
    labs = [e[4] for e in ents]
    feats = [features(e[5], e[6]) for e in ents]
    is_c = [l == "contradicts" for l in labs]
    cs = [k for k, l in enumerate(labs) if l in ("contradicts", "supports")]
    keys = [e[:4] for e in ents]
    n = Counter(labs)
    res = {"fires_by_label": {}, "rate_by_label": {}, "ratio_c_to_s": {},
           "contradicts_vs_rest": {}, "contradicts_vs_supports": {}, "slot": {}}
    for f in FEATURES:
        fired = [x[f] for x in feats]
        fl = Counter(l for l, x in zip(labs, fired) if x)
        res["fires_by_label"][f] = {l: fl[l] for l in ORDER}
        res["rate_by_label"][f] = {l: rnd(fl[l] / n[l]) if n[l] else None for l in ORDER}
        c, s = n["contradicts"], n["supports"]
        res["ratio_c_to_s"][f] = (rnd((fl["contradicts"] / c) / (fl["supports"] / s))
                                  if c and s and fl["supports"] else None)
        res["contradicts_vs_rest"][f] = flag_block(is_c, fired)
        res["contradicts_vs_supports"][f] = flag_block([is_c[k] for k in cs], [fired[k] for k in cs])
        res["slot"][f] = flag_block(*grouped(keys, is_c, fired))
    return res


def run(data_dir, sha=ASSESS_SHA256, get=fetch):
    t0 = time.time()
    res = {"version": VERSION, "problems": []}
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "assessments.json")
    if not os.path.exists(path):
        res["download"] = get(ASSESS_URL, path, 64 << 20)
    res["file"] = {"bytes": os.path.getsize(path), "sha256": file_sha(path)}
    if sha and res["file"]["sha256"] != sha:
        res["problems"].append("assessments sha256 %s, expected %s" % (res["file"]["sha256"], sha))
        return res
    with open(path, encoding="utf-8-sig") as f:
        ents, unknown = entries(json.load(f))
    scored = [e for e in ents if e[3] is not None and e[5] and e[6]]
    res["counts"] = {"judgments": len(ents), "unknown_label": unknown["unknown_label"],
                     "labels": {l: sum(1 for e in ents if e[4] == l) for l in ORDER},
                     "no_pmid": sum(1 for e in ents if e[3] is None),
                     "empty_passage": {l: sum(1 for e in ents if e[4] == l and not e[5])
                                       for l in ORDER},
                     "empty_sentence": sum(1 for e in ents if not e[6]),
                     "scored": len(scored),
                     "scored_labels": {l: sum(1 for e in scored if e[4] == l) for l in ORDER}}
    res["census"] = census(ents)
    if not scored:
        res["problems"].append("no scorable judgments")
        return res
    res.update(evaluate(scored))
    res["seconds"] = round(time.time() - t0, 1)
    return res


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    res = run(a.data_dir)
    dump(os.path.join(a.out_dir, "cue.json"), res)
    print(json.dumps({k: res.get(k) for k in ("problems", "counts", "census", "seconds")}, indent=1))
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
