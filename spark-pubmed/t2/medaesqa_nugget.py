"""Do NLM's expert-written nuggets rank TREC 2024 BioGen runs better than answer length does?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

biogen-reuse-v1 found that a leave-one-team-out pool of other runs' Required sentences separates
Required sentences (AUROC 0.70) but ranks the 30 runs by official completeness less well than
answer length alone (Kendall tau 0.70 against 0.82). MedAESQA (NLM, CC0, osf.io/ydbzq) has, for
40 of the 65 BioGen 2024 questions, an expert-written answer and its key facts ("nuggets"), which
no run produced. This job scores each run's answer sentences against those nuggets by word
containment (the share of a nugget's content words found in one sentence) and asks whether that
recall ranks runs better than length, and whether it adds anything once length is held fixed
(Kendall's partial tau). It also checks that MedAESQA's anonymised runs (M1-M30) are the 30
BioGen runs.

0.2.0: the nuggets are read from the field `nuggets`, which is where medaesqa_v1.json keeps them
(bioace-zip-v1's field census: a list of strings in all 40 items). 0.1.0 read only
`expert_curated_nuggets`, the name in the dataset's README, which the file does not have. The
MedAESQA file is now pinned by sha256 as well as size. Nothing else changed.

Outputs (counts and scores only, never question, nugget or sentence text):
  nugget.json       totals, nugget value shapes, question and run mapping, controls, sentence
                    AUROC, Kendall taus against the official Table 3/4 numbers
  nugget_runs.json  per run: official numbers, nugget recall and precision per bar, length
Python standard library only; biogen_reuse.py 0.1.0 is imported unchanged.
"""
import argparse
import json
import os
import re
import statistics
import sys
import time

import biogen_reuse as br

VERSION = "0.2.0"
MEDAESQA_URL = "https://osf.io/download/9d3qs/"
MEDAESQA_BYTES = 7276948  # size OSF lists for medaesqa_v1.json (read 2026-10-31); no hash is published
MEDAESQA_SHA = "a062742c1678b4379121ad030a06bda574afd376f331df41575938dd9849c383"  # seen by medaesqa-nugget-v1
NUGGET_KEYS = ("nuggets", "expert_curated_nuggets")  # the file's name first, then the README's
BAR = 0.6  # fixed before any run; BARS are reported for sensitivity only
BARS = (0.4, 0.5, 0.6, 0.7, 0.8)
NUGGET_MIN = 2  # a nugget needs at least 2 content words to be scored
TEXT_KEYS = ("nugget", "text", "content", "statement", "fact")
SPLIT_RX = re.compile(r"(?<=[.!?])\s+")


def cover(nugget, sent):
    """Share of the nugget's content words found in the sentence."""
    return len(nugget & sent) / len(nugget) if nugget else 0.0


def avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def pct(v):
    return None if v is None else round(100.0 * v, 4)


def nugget_texts(v):
    """The strings inside a nuggets value, whatever its shape."""
    if isinstance(v, str):
        return [s.strip() for s in v.split("\n") if s.strip()]
    if isinstance(v, list):
        return [s for x in v for s in nugget_texts(x)]
    if isinstance(v, dict):
        named = [v[k] for k in v if br.norm(k) in TEXT_KEYS and isinstance(v[k], str)]
        if named:
            return [s.strip() for s in named if s.strip()]
        return [s for x in v.values() for s in nugget_texts(x)]
    return []


def shape(v, depth=0):
    """A text-free description of a value's type, e.g. list[dict{nugget,pmids}]."""
    if isinstance(v, list):
        return "list[%s]" % "|".join(sorted({shape(x, depth + 1) for x in v[:50]})) if depth < 3 else "list"
    if isinstance(v, dict):
        keys = sorted(str(k) for k in v)
        if depth < 3 and all(br.ID_RX.fullmatch(k) for k in keys):
            return "dict{%s}" % ",".join(keys[:12])
        return "dict(%d keys)" % len(keys)
    return type(v).__name__


def sentences(text):
    return SPLIT_RX.split(text.strip()) if isinstance(text, str) else []


def unwrap(obj):
    while isinstance(obj, dict) and len(obj) == 1 and isinstance(next(iter(obj.values())), (dict, list)):
        obj = next(iter(obj.values()))
    return obj


def nugget_field(unit):
    """(key name, value) of the first NUGGET_KEYS field the item has, else (None, None)."""
    for name in NUGGET_KEYS:
        for k, v in unit.items():
            if br.norm(k) == br.norm(name):
                return name, v
    return None, None


def load_expert(items):
    """{MedAESQA question id: question, nuggets and expert answer sentences as content-word sets},
    how often each nugget value shape was seen, and how often each nugget field name was used."""
    obj = unwrap(items)
    pairs = list(obj.items()) if isinstance(obj, dict) else list(enumerate(obj))
    out, shapes, fields = {}, {}, {}
    for k, unit in pairs:
        if not isinstance(unit, dict):
            continue
        name, raw = nugget_field(unit)
        fields[str(name)] = fields.get(str(name), 0) + 1
        s = shape(raw)
        shapes[s] = shapes.get(s, 0) + 1
        texts = nugget_texts(raw)
        out[br.topic_id(unit, k)] = {
            "question": br.content(br.get(unit, "question")),
            "nuggets": [w for w in map(br.content, texts) if len(w) >= NUGGET_MIN],
            "nugget_texts": len(texts),
            "expert": [w for w in map(br.content, sentences(br.get(unit, "expert_curated_answer")))
                       if len(w) >= br.MIN_WORDS]}
    return out, shapes, fields


def topic_questions(topics):
    """{BioGen topic id: content words of the question alone}."""
    obj = unwrap(topics)
    return {str(r["id"]): br.content(r.get("question") or "") for r in (obj if isinstance(obj, list) else [])
            if isinstance(r, dict) and r.get("id") is not None}


def match_questions(expert, data, tq):
    """{MedAESQA id: BioGen topic id}: the same id when BioGen has it with the same question
    (Dice >= 0.9 on content words), else the BioGen question with the highest Dice (>= 0.9)."""
    out, how = {}, {"by_id": 0, "by_text": 0, "unmatched": 0, "id_text_differs": 0}
    for qid, e in sorted(expert.items()):
        same = qid in data and (qid not in tq or br.dice(e["question"], tq[qid]) >= 0.9)
        if qid in data and not same:
            how["id_text_differs"] += 1
        if same:
            out[qid] = qid
            how["by_id"] += 1
            continue
        best = max(((br.dice(e["question"], w), t) for t, w in tq.items() if t in data), default=(0.0, None))
        if best[0] >= 0.9:
            out[qid] = best[1]
            how["by_text"] += 1
        else:
            how["unmatched"] += 1
    return out, how


def map_runs(med, data, qmap):
    """Each MedAESQA run -> the BioGen run sharing most of its scored sentences (content-word
    sets) on the matched questions."""
    topics = set(qmap.values())
    bio_runs = sorted({r for t in topics for r in data[t]})
    sets = {(t, r): {w for _, w in data[t][r] if len(w) >= br.MIN_WORDS} for t in topics for r in data[t]}
    out = {}
    for m in sorted({m for q in qmap if q in med for m in med[q]}):
        mine = [(qmap[q], w) for q in qmap if q in med for _, w in med[q].get(m, []) if len(w) >= br.MIN_WORDS]
        hits = sorted(((sum(1 for t, w in mine if w in sets.get((t, r), ())), r) for r in bio_runs),
                      key=lambda x: (-x[0], x[1]))
        top = hits[0] if hits else (0, None)
        out[m] = {"run": top[1], "share": br.r4(top[0] / len(mine)) if mine else None,
                  "runner_up_share": br.r4(hits[1][0] / len(mine)) if mine and len(hits) > 1 else None}
    return out


def label_agreement(med, data, qmap, runmap):
    """Over sentences paired by position with the same content words, how often both files give
    the same label, and how often only one of them gives a label."""
    same = differ = med_null = bio_null = 0
    for q, t in qmap.items():
        for m, rows in med.get(q, {}).items():
            r = runmap.get(m, {}).get("run")
            for (lm, wm), (lb, wb) in zip(rows, data[t].get(r, [])):
                if wm != wb:
                    continue
                if lm and lb:
                    same, differ = same + (lm == lb), differ + (lm != lb)
                elif lb:
                    med_null += 1
                elif lm:
                    bio_null += 1
    return {"same": same, "differ": differ, "medaesqa_null_biogen_labelled": med_null,
            "biogen_null_medaesqa_labelled": bio_null}


def run_scores(rows, nuggets):
    """Per bar: share of nuggets covered by one scored sentence (None without nuggets), and share
    of all sentences covering a nugget (unscored sentences never do); soft recall (mean best
    cover); each scored sentence's best cover."""
    sents = [w for _, w in rows if len(w) >= br.MIN_WORDS]
    m = [[cover(n, s) for s in sents] for n in nuggets]
    by_nug = [max(row) if row else 0.0 for row in m]
    by_sent = [max(m[i][j] for i in range(len(nuggets))) if nuggets else 0.0 for j in range(len(sents))]
    rec = {b: sum(1 for v in by_nug if v >= b) / len(nuggets) if nuggets else None for b in BARS}
    prec = {b: sum(1 for v in by_sent if v >= b) / len(rows) if rows else 0.0 for b in BARS}
    return rec, prec, avg(by_nug), by_sent


def partial_tau(xy, xz, yz):
    """Kendall's partial tau of x and y with z held fixed."""
    if None in (xy, xz, yz) or abs(xz) >= 1 or abs(yz) >= 1:
        return None
    return (xy - xz * yz) / ((1 - xz ** 2) * (1 - yz ** 2)) ** 0.5


def tau_of(xs, ys):
    return None if None in xs or None in ys else br.r4(br.kendall(xs, ys))


def analyse(expert, qmap, data, official):
    qs = sorted(qmap, key=lambda k: (len(k), k))
    runs = sorted({r for q in qs for r in data[qmap[q]]})
    nug = {q: expert[q]["nuggets"] for q in qs}
    sizes = [len(nug[q]) for q in qs]
    res = {"questions": len(qs), "runs": len(runs),
           "nugget_strings": sum(expert[q]["nugget_texts"] for q in qs), "nuggets": sum(sizes),
           "nuggets_per_question": {"median": statistics.median(sizes) if sizes else None,
                                    "min": min(sizes, default=None), "max": max(sizes, default=None)},
           "questions_without_nuggets": sum(1 for n in sizes if not n),
           "expert_sentences": sum(len(expert[q]["expert"]) for q in qs),
           "bar": BAR, "nugget_min_words": NUGGET_MIN}
    # positive control: the expert answer the nuggets were written from
    res["control_expert_recall"] = pct(avg([run_scores([(None, w) for w in expert[q]["expert"]], nug[q])[0][BAR]
                                            for q in qs]))
    per, sent = {}, []  # sent: (label, best nugget cover, question overlap)
    for r in runs:
        acc = {"recall": {b: [] for b in BARS}, "precision": {b: [] for b in BARS}, "soft": [], "n": [],
               "words": [], "shuffled": []}
        for i, q in enumerate(qs):
            rows = data[qmap[q]].get(r, [])
            rec, prec, soft, by_sent = run_scores(rows, nug[q])
            for b in BARS:
                acc["recall"][b].append(rec[b])
                acc["precision"][b].append(prec[b])
            acc["soft"].append(soft)
            acc["n"].append(len(rows))
            acc["words"].append(sum(len(w) for _, w in rows))
            # negative control: the next question's nuggets
            acc["shuffled"].append(run_scores(rows, nug[qs[(i + 1) % len(qs)]])[0][BAR])
            scored = [(lab, w) for lab, w in rows if len(w) >= br.MIN_WORDS]
            for (lab, w), v in zip(scored, by_sent):
                sent.append((lab, v, br.dice(w, expert[q]["question"])))
        o = official.get(r, {})
        per[r] = {"team": o.get("team", r), "official": {k: v for k, v in o.items() if k != "team"},
                  "sentences_per_question": br.r4(avg(acc["n"])),
                  "content_words_per_question": br.r4(avg(acc["words"])),
                  "recall": {str(b): pct(avg(acc["recall"][b])) for b in BARS},
                  "precision": {str(b): pct(avg(acc["precision"][b])) for b in BARS},
                  "soft_recall": pct(avg(acc["soft"])),
                  "shuffled_recall": pct(avg(acc["shuffled"]))}
    res["control_shuffled_recall"] = br.r4(avg([per[r]["shuffled_recall"] for r in runs]))
    for i, key in ((1, "nugget"), (2, "question")):
        pos = [s[i] for s in sent if s[0] == "required"]
        neg = [s[i] for s in sent if s[0] in br.LABELS[1:]]
        res.setdefault("sentence_auroc", {})[key] = br.r4(br.auroc(pos, neg))
    res["sentence_auroc_n"] = {"required": sum(1 for s in sent if s[0] == "required"),
                               "not_required": sum(1 for s in sent if s[0] in br.LABELS[1:])}
    ranked = [r for r in runs if r in official]
    comp = [official[r]["completeness_r"] for r in ranked]
    length = [per[r]["sentences_per_question"] for r in ranked]
    tau = {"n_runs": len(ranked)}
    for b in BARS:
        tau[str(b)] = {"recall_vs_completeness_r": tau_of([per[r]["recall"][str(b)] for r in ranked], comp),
                       "precision_vs_precision": tau_of([per[r]["precision"][str(b)] for r in ranked],
                                                        [official[r]["precision"] for r in ranked])}
    rec = [per[r]["recall"][str(BAR)] for r in ranked]
    xy, xz, yz = tau_of(rec, comp), tau_of(rec, length), tau_of(length, comp)
    tau["length_vs_completeness_r"] = yz
    tau["words_vs_completeness_r"] = tau_of([per[r]["content_words_per_question"] for r in ranked], comp)
    tau["recall_vs_length"] = xz
    tau["partial_recall_vs_completeness_r_given_length"] = br.r4(partial_tau(xy, xz, yz))
    tau["recall_vs_completeness_rb"] = tau_of(rec, [official[r]["completeness_rb"] for r in ranked])
    tau["soft_recall_vs_completeness_r"] = tau_of([per[r]["soft_recall"] for r in ranked], comp)
    res["run_tau"] = tau
    return res, per


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)  # BioGen 2024 topics.json and assessments.json
    ap.add_argument("--medaesqa-dir", required=True)
    ap.add_argument("--official", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    res, per, t0 = {"version": VERSION, "biogen_reuse_version": br.VERSION, "problem": None}, {}, time.time()
    try:
        topics_path = os.path.join(a.data_dir, "topics.json")
        assess_path = os.path.join(a.data_dir, "assessments.json")
        med_path = os.path.join(a.medaesqa_dir, "medaesqa_v1.json")
        dl = [br.download(br.TOPICS_URL, topics_path), br.download(br.ASSESS_URL, assess_path),
              br.download(MEDAESQA_URL, med_path)]
        res["download"] = dl
        for d, want in zip(dl, (br.TOPICS_SHA, br.ASSESS_SHA, MEDAESQA_SHA)):
            if d["sha256"] != want:
                raise ValueError("%s: sha256 %s, pinned %s" % (d["url"], d["sha256"], want))
        if dl[2]["bytes"] != MEDAESQA_BYTES:
            raise ValueError("%s: %d bytes, OSF lists %d" % (MEDAESQA_URL, dl[2]["bytes"], MEDAESQA_BYTES))
        with open(topics_path, encoding="utf-8-sig") as f:
            tq = topic_questions(json.load(f))
        with open(assess_path, encoding="utf-8-sig") as f:
            data = br.load_runs(json.load(f))
        with open(med_path, encoding="utf-8-sig") as f:
            items = json.load(f)
        with open(a.official, encoding="utf-8") as f:
            official = json.load(f)["runs"]
        expert, shapes, fields = load_expert(items)
        med = br.load_runs(items)
        qmap, how = match_questions(expert, data, tq)
        runmap = map_runs(med, data, qmap)
        shares = [v["share"] for v in runmap.values() if v["share"] is not None]
        res.update({"medaesqa_items": len(expert), "nugget_fields": fields, "nugget_shapes": shapes,
                    "medaesqa_runs": len({m for q in med.values() for m in q}),
                    "question_match": how, "matched_topics_distinct": len(set(qmap.values())),
                    "run_map": runmap, "run_map_distinct": len({v["run"] for v in runmap.values()}),
                    "run_map_min_share": min(shares, default=None),
                    "label_agreement": label_agreement(med, data, qmap, runmap)})
        out, per = analyse(expert, qmap, data, official)
        res.update(out)
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    res["seconds"] = round(time.time() - t0, 1)
    br.dump(os.path.join(a.out_dir, "nugget.json"), res)
    br.dump(os.path.join(a.out_dir, "nugget_runs.json"), per)
    print(json.dumps(res, indent=1)[:6000])
    return 1 if res["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
