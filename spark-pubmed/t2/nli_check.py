"""Can an off-the-shelf NLI cross-encoder recover the TREC 2024 BioGen assessors' passage labels?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

SPARK Task 2 is scored partly on conflict coverage, and compose.py 0.2.0's negation-cue conflict
flag fired on no answer in t2dev-v1. Before building a model-based flag, this measures how well a
general NLI model separates the assessors' labels when it sees exactly what they judged: the
quoted passage of the cited paper (evidence_support, premise) and the answer sentence
(answer_sentence, hypothesis). Default model: cross-encoder/nli-deberta-v3-base (Apache-2.0) at a
pinned revision; --model/--revision pick another three-way NLI model. CPU only. Scored three ways:
per judgment (entry), per citation slot (topic, run, sentence, PMID; Contradicts if any entry is,
the overview's rule) and per topic-paper. Each level reports AUROC and average precision of
p(contradiction) for Contradicts, the argmax prediction's precision/recall/F1, and the best F1 over
thresholds (an oracle, chosen on the same data). It also reports p(entailment) for Supports, the
gold-by-argmax confusion matrix, and (0.2.0) two fixed combinations with cue_check.py's cues.

Outputs are counts and scores only, never question, sentence or passage text. --pairs-out keeps
each distinct pair's probabilities keyed by a SHA-1 of the pair, so later combinations need no
rescoring. Everything but nli_scores() and fetch_model()'s download is standard library, so the
tests need no torch.

  python nli_check.py fetch-model --model-dir DIR --out FILE [--model ID --revision SHA]
  python nli_check.py run --data-dir DIR --model-dir DIR --out-dir DIR [--threads 2 --batch 16]
                          [--model ID --revision SHA --pairs-out FILE]
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

import cue_check

VERSION = "0.2.0"
ASSESS_URL = "https://trec.nist.gov/data/biogen/biogen_collection_v3.json"
ASSESS_SHA256 = "78449ef270e60abe0c268fa446ade23737164bba44c37308e216529fa63d066d"
MODEL_ID = "cross-encoder/nli-deberta-v3-base"
MODEL_REV = "6c749ce3425cd33b46d187e45b92bbf96ee12ec7"
MODEL_FILES = ("config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
               "special_tokens_map.json", "added_tokens.json", "spm.model")
HF = "https://huggingface.co/%s/resolve/%s/%s"
LABELS = {"supporting": "supports", "contradicting": "contradicts", "neutral": "neutral",
          "notrelevant": "notrelevant", "invalidcitation": "invalid"}  # the file's own words, normalised
ORDER = ("supports", "contradicts", "neutral", "notrelevant", "invalid")
NLI = ("contradiction", "entailment", "neutral")
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


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


def fetch_model(model_dir, files=MODEL_FILES, rev=MODEL_REV, get=fetch, model=MODEL_ID):
    """Download each pinned model file once (kept on the data volume); report bytes and sha256."""
    os.makedirs(model_dir, exist_ok=True)
    rep = {"version": VERSION, "model": model, "revision": rev, "files": {}}
    for name in files:
        dest = os.path.join(model_dir, name)
        if not (os.path.exists(dest) and os.path.getsize(dest) > 0):
            get(HF % (model, rev, name), dest, 2 << 30)
        rep["files"][name] = {"bytes": os.path.getsize(dest), "sha256": file_sha(dest)}
    return rep


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


def auroc(scores, pos):
    """Mann-Whitney AUROC with average ranks for ties; None without both classes."""
    n1 = sum(1 for p in pos if p)
    n0 = len(pos) - n1
    if not n1 or not n0:
        return None
    order = sorted(range(len(scores)), key=lambda k: scores[k])
    ranks, i = [0.0] * len(scores), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        for k in order[i:j + 1]:
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    s = sum(r for r, p in zip(ranks, pos) if p)
    return (s - n1 * (n1 + 1) / 2) / (n1 * n0)


def average_precision(scores, gold):
    pos = sum(1 for g in gold if g)
    if not pos:
        return None
    tp, s = 0, 0.0
    for i, (_, g) in enumerate(sorted(zip(scores, gold), key=lambda t: -t[0]), 1):
        if g:
            tp += 1
            s += tp / i
    return s / pos


def prf(pred, gold):
    tp = sum(1 for p, g in zip(pred, gold) if p and g)
    fp = sum(1 for p, g in zip(pred, gold) if p and not g)
    fn = sum(1 for p, g in zip(pred, gold) if g and not p)
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": rnd(tp / (tp + fp)) if tp + fp else None,
            "recall": rnd(tp / (tp + fn)) if tp + fn else None,
            "f1": rnd(2 * tp / (2 * tp + fp + fn)) if tp else 0.0}


def best_f1(scores, gold):
    """Oracle: the threshold with the highest F1 (optimistic: chosen on the same data)."""
    pos = sum(1 for g in gold if g)
    if not pos:
        return None
    ranked = sorted(zip(scores, gold), key=lambda t: -t[0])
    best, raw, tp, fp, k = None, -1.0, 0, 0, 0
    while k < len(ranked):
        t = ranked[k][0]
        while k < len(ranked) and ranked[k][0] == t:
            tp, fp, k = tp + (1 if ranked[k][1] else 0), fp + (0 if ranked[k][1] else 1), k + 1
        f1 = 2 * tp / (tp + fp + pos)
        if f1 > raw:
            raw, best = f1, {"f1": round(f1, 4), "threshold": rnd(t), "tp": tp, "fp": fp,
                             "fn": pos - tp}
    return best


def block(gold, score, pred):
    n1 = sum(1 for g in gold if g)
    return {"n": len(gold), "positives": n1, "prevalence": rnd(n1 / len(gold)) if gold else None,
            "auroc": rnd(auroc(score, gold)), "average_precision": rnd(average_precision(score, gold)),
            "argmax": prf(pred, gold), "best_f1": best_f1(score, gold)}


def grouped(keys, gold, score, pred):
    """Collapse rows by key: positive if any row is, score the max, predicted if any row is."""
    g = {}
    for k, y, s, p in zip(keys, gold, score, pred):
        a = g.setdefault(k, [False, float("-inf"), False])
        a[0], a[1], a[2] = a[0] or y, max(a[1], s), a[2] or p
    v = list(g.values())
    return [a[0] for a in v], [a[1] for a in v], [a[2] for a in v]


def evaluate(ents, probs):
    """ents: scored entry tuples; probs: (p_contradiction, p_entailment, p_neutral) per entry."""
    labs = [e[4] for e in ents]
    pc, pe = [p[0] for p in probs], [p[1] for p in probs]
    am = [NLI[max(range(3), key=lambda i: p[i])] for p in probs]
    is_c, pred_c = [l == "contradicts" for l in labs], [a == "contradiction" for a in am]
    res = {"entry": {"contradicts_vs_rest": block(is_c, pc, pred_c),
                     "supports_vs_rest": block([l == "supports" for l in labs], pe,
                                               [a == "entailment" for a in am])}}
    cs = [k for k, l in enumerate(labs) if l in ("contradicts", "supports")]
    res["entry"]["contradicts_vs_supports"] = block([is_c[k] for k in cs], [pc[k] for k in cs],
                                                    [pred_c[k] for k in cs])
    conf = {l: Counter() for l in ORDER}
    for l, a in zip(labs, am):
        conf[l][a] += 1
    res["entry"]["confusion"] = {l: {a: conf[l][a] for a in NLI} for l in ORDER}
    res["entry"]["mean_p"] = {l: [rnd(sum(p[i] for p, x in zip(probs, labs) if x == l)
                                      / max(1, labs.count(l))) for i in range(3)] for l in ORDER}
    res["slot"] = block(*grouped([e[:4] for e in ents], is_c, pc, pred_c))
    res["topic_paper"] = block(*grouped([(e[0], e[3]) for e in ents], is_c, pc, pred_c))
    return res


def fusion(ents, probs):
    """Two fixed model x cue combinations (cue_check.py's cues on the same pair), Contradicts vs
    rest per entry and per slot. gate_neg_passage: argmax contradiction only where the passage has
    a negation cue (score p_c there, else 0). union_polarity_clash: argmax contradiction or
    compose.py's polarity_clash (score p_c, plus 1 where the clash fires)."""
    is_c = [e[4] == "contradicts" for e in ents]
    feats = [cue_check.features(e[5], e[6]) for e in ents]
    pc = [p[0] for p in probs]
    am_c = [max(range(3), key=lambda i: p[i]) == 0 for p in probs]
    neg = [f["neg_passage"] for f in feats]
    clash = [f["polarity_clash"] for f in feats]
    combos = {"gate_neg_passage": ([s if g else 0.0 for s, g in zip(pc, neg)],
                                   [a and g for a, g in zip(am_c, neg)]),
              "union_polarity_clash": ([s + (1.0 if c else 0.0) for s, c in zip(pc, clash)],
                                       [a or c for a, c in zip(am_c, clash)])}
    keys = [e[:4] for e in ents]
    return {name: {"entry": block(is_c, sc, pr), "slot": block(*grouped(keys, is_c, sc, pr))}
            for name, (sc, pr) in combos.items()}


def nli_scores(pairs, model_dir, threads=2, batch=16, max_length=256, log=print):
    """(p_contradiction, p_entailment, p_neutral) per (premise, hypothesis) pair, CPU, fp32."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.set_num_threads(threads)
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir, use_safetensors=True)
    model.eval()
    col = {str(v).lower(): int(i) for i, v in model.config.id2label.items()}
    if set(col) != set(NLI):
        raise SystemExit("unexpected id2label %r" % model.config.id2label)
    order = sorted(range(len(pairs)), key=lambda k: len(pairs[k][0]) + len(pairs[k][1]))
    out, truncated, t0 = [None] * len(pairs), 0, time.time()
    with torch.inference_mode():
        for b in range(0, len(order), batch):
            ks = order[b:b + batch]
            prem, hyp = [pairs[k][0] for k in ks], [pairs[k][1] for k in ks]
            truncated += sum(1 for ids in tok(prem, hyp)["input_ids"] if len(ids) > max_length)
            enc = tok(prem, hyp, truncation=True, max_length=max_length, padding=True,
                      return_tensors="pt")
            p = torch.softmax(model(**enc).logits.float(), dim=-1).tolist()
            for k, row in zip(ks, p):
                out[k] = tuple(row[col[n]] for n in NLI)
            if (b // batch) % 50 == 0:
                log("scored %d/%d pairs, %.0f s" % (b + len(ks), len(pairs), time.time() - t0))
    secs = time.time() - t0
    return out, {"pairs": len(pairs), "truncated": truncated, "max_length": max_length,
                 "batch": batch, "threads": threads, "seconds": round(secs, 1),
                 "ms_per_pair": rnd(1000 * secs / max(1, len(pairs)))}


def pair_key(premise, hypothesis):
    return hashlib.sha1((premise + "\n" + hypothesis).encode("utf-8")).hexdigest()


def run(data_dir, scorer, sha=ASSESS_SHA256, get=fetch, model=MODEL_ID, rev=MODEL_REV,
        pairs_path=None):
    t0 = time.time()
    res = {"version": VERSION, "model": model, "revision": rev, "problems": []}
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
    uniq, idx = {}, []
    for e in scored:
        idx.append(uniq.setdefault((e[5], e[6]), len(uniq)))
    res["counts"]["unique_pairs"] = len(uniq)
    if not scored:
        res["problems"].append("no scorable judgments")
        return res
    probs_u, res["scoring"] = scorer(list(uniq))
    if pairs_path:
        with open(pairs_path, "w", encoding="utf-8") as f:
            for (prem, hyp), p in zip(uniq, probs_u):
                f.write(json.dumps({"pair": pair_key(prem, hyp), "p": [round(x, 6) for x in p]})
                        + "\n")
    probs = [probs_u[i] for i in idx]
    res.update(evaluate(scored, probs))
    res["fusion"] = fusion(scored, probs)
    res["seconds"] = round(time.time() - t0, 1)
    return res


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    fm = sub.add_parser("fetch-model")
    fm.add_argument("--model-dir", required=True)
    fm.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--data-dir", required=True)
    r.add_argument("--model-dir", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--threads", type=int, default=2)
    r.add_argument("--batch", type=int, default=16)
    r.add_argument("--max-length", type=int, default=256)
    r.add_argument("--pairs-out")
    for p in (fm, r):
        p.add_argument("--model", default=MODEL_ID)
        p.add_argument("--revision", default=MODEL_REV)
    a = ap.parse_args(argv)
    if a.cmd == "fetch-model":
        rep = fetch_model(a.model_dir, rev=a.revision, model=a.model)
        dump(a.out, rep)
        print(json.dumps(rep, indent=1))
        return 0
    os.makedirs(a.out_dir, exist_ok=True)
    res = run(a.data_dir, lambda pairs: nli_scores(pairs, a.model_dir, a.threads, a.batch,
                                                   a.max_length),
              model=a.model, rev=a.revision, pairs_path=a.pairs_out)
    dump(os.path.join(a.out_dir, "nli.json"), res)
    print(json.dumps({k: res.get(k) for k in ("problems", "counts", "census", "scoring")}, indent=1))
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
