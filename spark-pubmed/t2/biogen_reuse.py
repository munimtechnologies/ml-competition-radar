"""Can TREC 2024 BioGen's sentence judgments grade an answer that was not in the pool?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

SPARK Task 2 answers will be new runs that no BioGen assessor ever read. TREC 2024 BioGen
judged every answer sentence of 30 runs (Required, Unnecessary, Borderline, Inappropriate) and
scored completeness by clustering the Required sentences of all runs (overview, arXiv
2411.18069, Table 4), with the scored run inside the pool and its own labels used. The overview
reports no leave-out test. This job asks whether the judgments still work when the run is
outside the pool: for each run it drops the run's whole team from the pool (leave-one-team-out,
as TREC NeuCLIR does for retrieval judgments) and scores the run's sentences, labels unseen, by
word overlap (Dice over content-word sets) with the other teams' Required sentences.

Outputs (counts and scores only, never sentence or question text):
  reuse.json  totals, sentence-level AUROC of the proxy against each sentence's own label, run-level
              Kendall tau against the official Table 3/4 numbers, baselines, bar sensitivity
  runs.json   per run: official numbers, reproduced precision, proxy numbers, sentence counts
Python standard library only.
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

VERSION = "0.1.0"
TOPICS_URL = "https://trec.nist.gov/data/biogen/BioGen2024topics-json.txt"
ASSESS_URL = "https://trec.nist.gov/data/biogen/biogen_collection_v3.json"
TOPICS_SHA = "d456904111ed963552eda412c224107dccf632fc54d04d23b47f9b8878374774"
ASSESS_SHA = "78449ef270e60abe0c268fa446ade23737164bba44c37308e216529fa63d066d"
BAR = 0.5  # fixed before any run; BARS are reported for sensitivity only
BARS = (0.3, 0.4, 0.5, 0.6, 0.7)
MIN_WORDS = 3  # a sentence with fewer content words ("..", "[PMID1]") is not scored
LABELS = ("required", "unnecessary", "borderline", "inappropriate")
TOPIC_KEYS = ("question_id", "topic_id", "qid", "id")
ID_RX = re.compile(r"[A-Za-z0-9_\-]{1,40}")
STOP = frozenset("""a about above after again against all also an and any are as at be because
been before being between both but by can could did do does doing during each few for from further
had has have having he her here hers him his how i if in into is it its itself may might more most
must no nor not of off on once only or other our out over own same she should so some such than
that the their them then there these they this those through to too under until up very was we
were what when where which while who whom why will with would you your""".split())
CITE_RX = re.compile(r"\[[^\]]*\]|\(\s*pmids?[^)]*\)|\bpmids?\s*:?\s*\d+", re.I)
TOKEN_RX = re.compile(r"[a-z0-9]+")
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"


def norm(s):
    return re.sub(r"[\s_\-]+", "", str(s).strip().lower())


def content(text):
    """Set of content words: citation markers, stop words and long digit strings removed."""
    if not isinstance(text, str):
        return frozenset()
    text = CITE_RX.sub(" ", text.lower())
    return frozenset(w for w in TOKEN_RX.findall(text)
                     if w not in STOP and not (w.isdigit() and len(w) >= 5))


def dice(a, b):
    return 2 * len(a & b) / (len(a) + len(b)) if a and b else 0.0


def get(d, *names):
    """d's value under the first of names (compared normalised), else None."""
    if isinstance(d, dict):
        for n in names:
            for k, v in d.items():
                if norm(k) == norm(n):
                    return v
    return None


def topic_id(unit, fallback):
    v = get(unit, *TOPIC_KEYS)
    if isinstance(v, (int, str)) and not isinstance(v, bool) and ID_RX.fullmatch(str(v)):
        return str(v)
    return str(fallback)


def load_runs(assess):
    """{topic id: {run: [(label or None, content words), ...]}} in file order."""
    obj = assess
    while isinstance(obj, dict) and len(obj) == 1 and isinstance(next(iter(obj.values())), (dict, list)):
        obj = next(iter(obj.values()))
    pairs = list(obj.items()) if isinstance(obj, dict) else list(enumerate(obj))
    data = {}
    for k, unit in pairs:
        runs = get(unit, "machine_generated_answers")
        if not isinstance(runs, dict):
            continue
        t = data.setdefault(topic_id(unit, k), {})
        for run, ans in runs.items():
            sents = get(ans, "answer_sentences")
            rows = t.setdefault(str(run), [])
            for s in sents if isinstance(sents, list) else []:
                lab = get(s, "answer_sentence_relevance")
                lab = norm(lab) if isinstance(lab, str) and norm(lab) in LABELS else None
                rows.append((lab, content(get(s, "answer_sentence"))))
    return data


def load_questions(topics):
    """{topic id: content words of question + narrative}."""
    obj = topics
    while isinstance(obj, dict) and len(obj) == 1 and isinstance(next(iter(obj.values())), (dict, list)):
        obj = next(iter(obj.values()))
    out = {}
    for r in obj if isinstance(obj, list) else []:
        if isinstance(r, dict) and r.get("id") is not None:
            out[str(r["id"])] = content("%s %s" % (r.get("question") or "", r.get("narrative") or ""))
    return out


def pool(topic, exclude):
    """Distinct content-word sets of the Required sentences of runs not in exclude."""
    seen = set()
    for run, rows in topic.items():
        if run not in exclude:
            seen.update(w for lab, w in rows if lab == "required" and len(w) >= MIN_WORDS)
    return sorted(seen, key=lambda w: (-len(w), sorted(w)))


def score_topic(topic, run, exclude):
    """(best match of each scored sentence of run in the pool, best match of each pool item
    among those sentences, pool size)."""
    p = pool(topic, exclude)
    sents = [w for _, w in topic.get(run, []) if len(w) >= MIN_WORDS]
    m = [[dice(s, q) for q in p] for s in sents]
    by_sent = [max(row) if row else 0.0 for row in m]
    by_item = [max(m[i][j] for i in range(len(sents))) if sents else 0.0 for j in range(len(p))]
    return by_sent, by_item, len(p)


def clusters(items, bar=BAR):
    """Greedy leader clustering: an item joins the first leader it matches at >= bar."""
    leaders = []
    for w in sorted(items, key=lambda w: (-len(w), sorted(w))):
        if not any(dice(w, l) >= bar for l in leaders):
            leaders.append(w)
    return len(leaders)


def auroc(pos, neg):
    if not pos or not neg:
        return None
    vals = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    rank_sum, i = 0.0, 0
    while i < len(vals):
        j = i
        while j < len(vals) and vals[j][0] == vals[i][0]:
            j += 1
        rank_sum += (i + 1 + j) / 2 * sum(1 for k in range(i, j) if vals[k][1])
        i = j
    return (rank_sum - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def kendall(x, y):
    """Kendall's tau-b."""
    c = d = tie_x = tie_y = 0
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            a = (x[i] > x[j]) - (x[i] < x[j])
            b = (y[i] > y[j]) - (y[i] < y[j])
            if a and b:
                c, d = (c + 1, d) if a == b else (c, d + 1)
            elif a:
                tie_y += 1
            elif b:
                tie_x += 1
    den = ((c + d + tie_x) * (c + d + tie_y)) ** 0.5
    return (c - d) / den if den else None


def r4(v):
    return round(v, 4) if isinstance(v, float) else v


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def analyse(data, questions, official):
    topics = sorted(data, key=lambda k: (len(k), k))
    runs = sorted({r for t in data.values() for r in t})
    team = {r: (official.get(r) or {}).get("team", r) for r in runs}
    labs = [lab for t in data.values() for rows in t.values() for lab, _ in rows]
    valid = [(lab, w) for t in data.values() for rows in t.values() for lab, w in rows if len(w) >= MIN_WORDS]
    res = {"topics": len(topics), "runs": len(runs),
           "runs_matched_official": sum(1 for r in runs if r in official),
           "official_runs_missing": sorted(set(official) - set(runs)),
           "sentences": len(labs), "labelled": sum(1 for l in labs if l),
           "label_counts": {l: labs.count(l) for l in LABELS},
           "scored_sentences": len(valid),
           "scored_label_counts": {l: sum(1 for lab, _ in valid if lab == l) for l in LABELS},
           "bar": BAR, "min_words": MIN_WORDS}
    sizes = [len(pool(data[t], set())) for t in topics]
    res["pool_distinct_required_per_topic"] = {"median": statistics.median(sizes) if sizes else None,
                                               "min": min(sizes, default=None), "max": max(sizes, default=None)}
    cl = [clusters(pool(data[t], set())) for t in topics]
    res["greedy_clusters_per_topic"] = {"median": statistics.median(cl) if cl else None,
                                        "min": min(cl, default=None), "max": max(cl, default=None)}
    sent = []  # (label, best team-out, best run-out, question overlap)
    per = {}
    for r in runs:
        mates = {x for x in runs if team[x] == team[r]}
        acc = {"recall_team": {b: [] for b in BARS}, "recall_run": {b: [] for b in BARS},
               "precision_team": {b: [] for b in BARS}, "precision_run": {b: [] for b in BARS},
               "n": [], "n_scored": [], "qsim": [], "prec_all": [], "prec_labelled": [],
               "prec_answered": [], "pool_team": []}
        for t in topics:
            rows = data[t].get(r, [])
            req = sum(1 for lab, _ in rows if lab == "required")
            nlab = sum(1 for lab, _ in rows if lab)
            acc["prec_all"].append(100.0 * req / len(rows) if rows else 0.0)
            acc["prec_labelled"].append(100.0 * req / nlab if nlab else 0.0)
            if rows:
                acc["prec_answered"].append(100.0 * req / len(rows))
            acc["n"].append(len(rows))
            st, it, n_pool = score_topic(data[t], r, mates)
            sr, ir, _ = score_topic(data[t], r, {r})
            acc["pool_team"].append(n_pool)
            q = questions.get(t, frozenset())
            scored = [(lab, w) for lab, w in rows if len(w) >= MIN_WORDS]
            acc["n_scored"].append(len(scored))
            qs = [dice(w, q) for _, w in scored]
            acc["qsim"].extend(qs)
            for (lab, _), a, b, c in zip(scored, st, sr, qs):
                sent.append((lab, a, b, c))
            for bar in BARS:
                # precision counts every sentence, as the official one does: unscored ones never match
                for key, vals, n in (("recall_team", it, len(it)), ("recall_run", ir, len(ir)),
                                     ("precision_team", st, len(rows)), ("precision_run", sr, len(rows))):
                    if key.startswith("recall") and not n:
                        continue  # empty pool: nothing to recall
                    acc[key][bar].append(sum(1 for v in vals if v >= bar) / n if n else 0.0)
        o = official.get(r, {})
        per[r] = {"team": team[r], "official": {k: v for k, v in o.items() if k != "team"},
                  "repro_precision_all": r4(mean(acc["prec_all"])),
                  "repro_precision_labelled": r4(mean(acc["prec_labelled"])),
                  "repro_precision_answered": r4(mean(acc["prec_answered"])),
                  "sentences_per_topic": r4(mean(acc["n"])),
                  "scored_per_topic": r4(mean(acc["n_scored"])),
                  "team_out_pool_median": statistics.median(acc["pool_team"]) if acc["pool_team"] else None,
                  "question_overlap_mean": r4(mean(acc["qsim"])),
                  **{k: {str(b): r4(100.0 * mean(acc[k][b])) for b in BARS}
                     for k in ("recall_team", "recall_run", "precision_team", "precision_run")}}
    for i, key in ((1, "team_out"), (2, "run_out"), (3, "question")):
        pos = [s[i] for s in sent if s[0] == "required"]
        neg = [s[i] for s in sent if s[0] in LABELS[1:]]
        unn = [s[i] for s in sent if s[0] == "unnecessary"]
        res.setdefault("sentence_auroc", {})[key] = r4(auroc(pos, neg))
        res.setdefault("sentence_auroc_vs_unnecessary", {})[key] = r4(auroc(pos, unn))
    res["sentence_auroc_n"] = {"required": sum(1 for s in sent if s[0] == "required"),
                               "not_required": sum(1 for s in sent if s[0] in LABELS[1:])}
    ranked = [r for r in runs if r in official]
    off_r = [official[r]["completeness_r"] for r in ranked]
    off_p = [official[r]["precision"] for r in ranked]
    tau = {"n_runs": len(ranked)}
    for b in BARS:
        tau[str(b)] = {k: r4(kendall([per[r][k][str(b)] for r in ranked], off_p if k.startswith("precision") else off_r))
                       for k in ("recall_team", "recall_run", "precision_team", "precision_run")}
    tau["baseline_sentences_vs_completeness_r"] = r4(kendall([per[r]["sentences_per_topic"] for r in ranked], off_r))
    tau["baseline_scored_vs_completeness_r"] = r4(kendall([per[r]["scored_per_topic"] for r in ranked], off_r))
    tau["baseline_question_overlap_vs_precision"] = r4(kendall([per[r]["question_overlap_mean"] for r in ranked], off_p))
    res["run_tau"] = tau
    diffs = {r: abs(per[r]["repro_precision_all"] - official[r]["precision"]) for r in ranked}
    diffs_l = {r: abs(per[r]["repro_precision_labelled"] - official[r]["precision"]) for r in ranked}
    diffs_a = {r: abs(per[r]["repro_precision_answered"] - official[r]["precision"]) for r in ranked}
    res["repro_precision"] = {"within_1_all": sum(1 for v in diffs.values() if v <= 1.0),
                              "within_1_labelled": sum(1 for v in diffs_l.values() if v <= 1.0),
                              "within_1_answered": sum(1 for v in diffs_a.values() if v <= 1.0),
                              "misses_all": sorted(r for r, v in diffs.items() if v > 1.0),
                              "max_abs_diff_all": r4(max(diffs.values(), default=None))}
    return res, per


def download(url, dest, minutes=20, max_bytes=300 << 20):
    """Reuse dest if it exists, else stream url to it. Returns url, bytes, sha256, cached."""
    cached = os.path.exists(dest)
    if not cached:
        os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        t0, n = time.time(), 0
        with urllib.request.urlopen(req, timeout=60) as r, open(dest + ".part", "wb") as f:
            for b in iter(lambda: r.read(1 << 20), b""):
                n += len(b)
                if n > max_bytes or time.time() - t0 > minutes * 60:
                    raise ValueError("%s: over %d bytes or %d minutes" % (url, max_bytes, minutes))
                f.write(b)
        os.replace(dest + ".part", dest)
    h, n = hashlib.sha256(), 0
    with open(dest, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
            n += len(b)
    return {"url": url, "bytes": n, "sha256": h.hexdigest(), "cached": cached}


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--official", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    res, per, t0 = {"version": VERSION, "problem": None}, {}, time.time()
    try:
        dl = [download(TOPICS_URL, os.path.join(a.data_dir, "topics.json")),
              download(ASSESS_URL, os.path.join(a.data_dir, "assessments.json"))]
        res["download"] = dl
        for d, want in zip(dl, (TOPICS_SHA, ASSESS_SHA)):
            if d["sha256"] != want:
                raise ValueError("%s: sha256 %s, pinned %s" % (d["url"], d["sha256"], want))
        with open(os.path.join(a.data_dir, "topics.json"), encoding="utf-8-sig") as f:
            questions = load_questions(json.load(f))
        with open(os.path.join(a.data_dir, "assessments.json"), encoding="utf-8-sig") as f:
            data = load_runs(json.load(f))
        with open(a.official, encoding="utf-8") as f:
            official = json.load(f)["runs"]
        res["questions"] = len(questions)
        out, per = analyse(data, questions, official)
        res.update(out)
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    res["seconds"] = round(time.time() - t0, 1)
    dump(os.path.join(a.out_dir, "reuse.json"), res)
    dump(os.path.join(a.out_dir, "runs.json"), per)
    print(json.dumps(res, indent=1)[:6000])
    return 1 if res["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
