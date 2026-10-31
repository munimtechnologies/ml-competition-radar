"""The biogen-reuse test again, with sentence embeddings in place of word overlap.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

biogen_reuse.py 0.1.0 asks whether TREC 2024 BioGen's sentence judgments can grade a run left out
of the pool: drop the run's whole team, hide its labels, and match its sentences against the other
teams' Required sentences by Dice over content words. This job runs the same test with cosine
similarity of all-mpnet-base-v2 embeddings (Apache-2.0, one of the two models the BioGen 2024
overview, arXiv 2411.18069, names for its completeness clustering). Runs, topics, labels, the
3-content-word floor, the pools and the official numbers are the same, and the word-overlap
proxy is recomputed on the same sentences so the two are compared pair by pair (topic bootstrap).
biogen_reuse.analyse is also run unchanged, as a check that the shared parts agree.

A sentence is keyed by its content-word set, as in biogen_reuse.py: sentences with the same set
are one pool item, embedded once from the alphabetically first of their cleaned texts (citation
markers removed, whitespace collapsed).

  python biogen_reuse_emb.py fetch-model --model-dir DIR --out JSON
  python biogen_reuse_emb.py run --data-dir DIR --official JSON --model-dir DIR --out-dir DIR [--threads 2]

Outputs (counts and scores only, never sentence or question text):
  emb.json       totals, sentence AUROC for both similarities, paired topic bootstrap, run-level
                 Kendall tau against the official Table 3/4 numbers, baselines, agreement check
  emb_runs.json  per run: proxy recall and precision for both similarities at every bar
"""
import argparse
import hashlib
import json
import os
import random
import sys
import time
import urllib.request

import biogen_reuse as br

VERSION = "0.1.0"
MODEL = "sentence-transformers/all-mpnet-base-v2"
REVISION = "e8c3b32edf5434bc2275fc9bab85f82640a19130"
MODEL_FILES = ("config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
               "vocab.txt", "model.safetensors")
WEIGHTS_SHA = "78c0197b6159d92658e319bc1d72e4c73a9a03dd03815e70e555c5ef05615658"
MAX_TOKENS = 384  # the model's sentence_bert_config max_seq_length
BARS = {"lex": br.BARS, "emb": (0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9)}
PRIMARY = {"lex": 0.5, "emb": 0.7}  # fixed before any run; the other bars are sensitivity only
BOOT = 1000
SEED = 20261031


def load_texts(assess):
    """{topic id: {run: [(label or None, content words, cleaned text), ...]}} in file order,
    walked exactly as biogen_reuse.load_runs walks it."""
    obj = assess
    while isinstance(obj, dict) and len(obj) == 1 and isinstance(next(iter(obj.values())), (dict, list)):
        obj = next(iter(obj.values()))
    pairs = list(obj.items()) if isinstance(obj, dict) else list(enumerate(obj))
    data = {}
    for k, unit in pairs:
        runs = br.get(unit, "machine_generated_answers")
        if not isinstance(runs, dict):
            continue
        t = data.setdefault(br.topic_id(unit, k), {})
        for run, ans in runs.items():
            sents = br.get(ans, "answer_sentences")
            rows = t.setdefault(str(run), [])
            for s in sents if isinstance(sents, list) else []:
                lab = br.get(s, "answer_sentence_relevance")
                lab = br.norm(lab) if isinstance(lab, str) and br.norm(lab) in br.LABELS else None
                raw = br.get(s, "answer_sentence")
                text = " ".join(br.CITE_RX.sub(" ", raw).split()) if isinstance(raw, str) else ""
                rows.append((lab, br.content(raw), text))  # words from the raw text, as load_runs does
    return data


def keys_of(topic):
    """Distinct content-word sets (3+ words) in the topic, in biogen_reuse's pool order, and the
    alphabetically first cleaned text of each."""
    rep = {}
    for rows in topic.values():
        for _, w, text in rows:
            if len(w) >= br.MIN_WORDS:
                rep[w] = min(rep.get(w, text), text)
    keys = sorted(rep, key=lambda w: (-len(w), sorted(w)))
    return keys, [rep[w] for w in keys]


def lex_matrix(keys):
    return [[br.dice(a, b) for b in keys] for a in keys]


def cos_matrix(vecs):
    """Cosine similarities of unit vectors, as nested lists."""
    import numpy as np
    v = np.asarray(vecs, dtype=np.float64)
    return (v @ v.T).tolist()


def score(topic, index, sim, run, exclude):
    """As biogen_reuse.score_topic, over keys: (best pool match of each scored sentence of run,
    best match of each pool item among them, pool size)."""
    pool = sorted({index[w] for r, rows in topic.items() if r not in exclude
                   for lab, w, _ in rows if lab == "required" and len(w) >= br.MIN_WORDS})
    sents = [index[w] for _, w, _ in topic.get(run, []) if len(w) >= br.MIN_WORDS]
    by_sent = [max((sim[i][j] for j in pool), default=0.0) for i in sents]
    by_item = [max((sim[i][j] for i in sents), default=0.0) for j in pool]
    return by_sent, by_item, len(pool)


def boot_diff(sent, topics, n=BOOT, seed=SEED):
    """Topic bootstrap of team-out AUROC, emb minus lex. sent rows: (topic, label, lex, emb)."""
    by_t = {t: [] for t in topics}
    for row in sent:
        by_t[row[0]].append(row)
    rng, diffs = random.Random(seed), []
    for _ in range(n):
        rows = [row for t in (rng.choice(topics) for _ in topics) for row in by_t[t]]
        pos = [r for r in rows if r[1] == "required"]
        neg = [r for r in rows if r[1] in br.LABELS[1:]]
        a = br.auroc([r[2] for r in pos], [r[2] for r in neg])
        b = br.auroc([r[3] for r in pos], [r[3] for r in neg])
        if a is not None and b is not None:
            diffs.append(b - a)
    diffs.sort()
    if not diffs:
        return {"n": 0}
    pick = lambda q: diffs[min(len(diffs) - 1, int(q * len(diffs)))]
    return {"n": len(diffs), "seed": seed, "lo_2_5": br.r4(pick(0.025)), "hi_97_5": br.r4(pick(0.975)),
            "median": br.r4(pick(0.5)), "share_above_0": br.r4(sum(1 for d in diffs if d > 0) / len(diffs))}


def analyse(data, sims, official, n_boot=BOOT):
    """sims: {method: {topic: (index of key, matrix)}} for "lex" and "emb"."""
    topics = sorted(data, key=lambda k: (len(k), k))
    runs = sorted({r for t in data.values() for r in t})
    team = {r: (official.get(r) or {}).get("team", r) for r in runs}
    res = {"topics": len(topics), "runs": len(runs),
           "sentences": sum(len(rows) for t in data.values() for rows in t.values()),
           "distinct_keys": sum(len(sims["emb"][t][0]) for t in topics),
           "primary_bar": PRIMARY, "bars": {m: list(b) for m, b in BARS.items()}}
    sent = []  # (topic, label, lex team-out, emb team-out, lex run-out, emb run-out)
    per = {}
    for r in runs:
        mates = {x for x in runs if team[x] == team[r]}
        acc = {m: {k: {b: [] for b in BARS[m]} for k in ("recall_team", "recall_run", "precision_team",
                                                         "precision_run")} for m in BARS}
        soft = {m: {"recall_team": [], "precision_team": []} for m in BARS}
        for t in topics:
            rows = data[t].get(r, [])
            labs = [lab for lab, w, _ in rows if len(w) >= br.MIN_WORDS]
            got = {}
            for m in BARS:
                index, sim = sims[m][t]
                st, it, _ = score(data[t], index, sim, r, mates)
                sr, ir, _ = score(data[t], index, sim, r, {r})
                got[m] = (st, sr)
                for bar in BARS[m]:
                    for key, vals, n in (("recall_team", it, len(it)), ("recall_run", ir, len(ir)),
                                         ("precision_team", st, len(rows)), ("precision_run", sr, len(rows))):
                        if key.startswith("recall") and not n:
                            continue  # empty pool: nothing to recall
                        acc[m][key][bar].append(sum(1 for v in vals if v >= bar) / n if n else 0.0)
                if it:
                    soft[m]["recall_team"].append(br.mean(it))
                soft[m]["precision_team"].append(sum(st) / len(rows) if rows else 0.0)
            for i, lab in enumerate(labs):
                sent.append((t, lab, got["lex"][0][i], got["emb"][0][i], got["lex"][1][i], got["emb"][1][i]))
        per[r] = {"team": team[r], "sentences_per_topic": br.r4(br.mean([len(data[t].get(r, [])) for t in topics]))}
        for m in BARS:
            per[r][m] = {k: {str(b): br.r4(100.0 * br.mean(acc[m][k][b])) for b in BARS[m]} for k in acc[m]}
            per[r][m]["soft"] = {k: br.r4(100.0 * br.mean(v)) for k, v in soft[m].items()}
    au = {}
    for m, (ti, ri) in (("lex", (2, 4)), ("emb", (3, 5))):
        for key, i in (("team_out", ti), ("run_out", ri)):
            pos = [s[i] for s in sent if s[1] == "required"]
            neg = [s[i] for s in sent if s[1] in br.LABELS[1:]]
            unn = [s[i] for s in sent if s[1] == "unnecessary"]
            au.setdefault(m, {})[key] = br.r4(br.auroc(pos, neg))
            au[m][key + "_vs_unnecessary"] = br.r4(br.auroc(pos, unn))
    res["sentence_auroc"] = au
    res["sentence_auroc_n"] = {"required": sum(1 for s in sent if s[1] == "required"),
                               "not_required": sum(1 for s in sent if s[1] in br.LABELS[1:])}
    res["bootstrap_team_out_emb_minus_lex"] = boot_diff([s[:4] for s in sent], topics, n_boot)
    ranked = [r for r in runs if r in official]
    off_r = [official[r]["completeness_r"] for r in ranked]
    off_p = [official[r]["precision"] for r in ranked]
    tau = {"n_runs": len(ranked)}
    for m in BARS:
        tau[m] = {str(b): {k: br.r4(br.kendall([per[r][m][k][str(b)] for r in ranked],
                                               off_p if k.startswith("precision") else off_r))
                           for k in ("recall_team", "recall_run", "precision_team", "precision_run")}
                  for b in BARS[m]}
        tau[m]["soft"] = {k: br.r4(br.kendall([per[r][m]["soft"][k] for r in ranked],
                                              off_p if k.startswith("precision") else off_r))
                          for k in ("recall_team", "precision_team")}
    tau["baseline_sentences_vs_completeness_r"] = br.r4(
        br.kendall([per[r]["sentences_per_topic"] for r in ranked], off_r))
    res["run_tau"] = tau
    return res, per


def fetch_model(model_dir, read=None):
    """Download the pinned files into model_dir (kept if present); check the weights' sha256."""
    os.makedirs(model_dir, exist_ok=True)
    rep = {"version": VERSION, "model": MODEL, "revision": REVISION, "files": {}, "problem": None}
    for name in MODEL_FILES:
        dest = os.path.join(model_dir, name)
        if not os.path.exists(dest):
            url = "https://huggingface.co/%s/resolve/%s/%s" % (MODEL, REVISION, name)
            req = urllib.request.Request(url, headers={"User-Agent": br.USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as f:
                for b in iter(lambda: r.read(1 << 20), b""):
                    f.write(b)
            os.replace(dest + ".part", dest)
        h = hashlib.sha256()
        with open(dest, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        rep["files"][name] = {"bytes": os.path.getsize(dest), "sha256": h.hexdigest()}
    if rep["files"]["model.safetensors"]["sha256"] != WEIGHTS_SHA:
        rep["problem"] = "model.safetensors sha256 %s, pinned %s" % (
            rep["files"]["model.safetensors"]["sha256"], WEIGHTS_SHA)
    return rep


def embed(texts, model_dir, threads=2, batch=32):
    """Unit-length mean-pooled embeddings, float32 on CPU, in input order."""
    import numpy as np
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.set_num_threads(threads)
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModel.from_pretrained(model_dir, torch_dtype=torch.float32).eval()
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    out = np.zeros((len(texts), model.config.hidden_size), dtype=np.float32)
    with torch.inference_mode():
        for s in range(0, len(order), batch):
            idx = order[s:s + batch]
            enc = tok([texts[i] for i in idx], padding=True, truncation=True, max_length=MAX_TOKENS,
                      return_tensors="pt")
            h = model(**enc).last_hidden_state
            m = enc["attention_mask"].unsqueeze(-1).to(h.dtype)
            v = (h * m).sum(1) / m.sum(1).clamp(min=1e-9)
            out[idx] = torch.nn.functional.normalize(v, p=2, dim=1).numpy()
    return out


def peak_mb():
    try:
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    except Exception:  # not on Linux
        return None


def run(a):
    res, per, t0 = {"version": VERSION, "problem": None, "model": MODEL, "revision": REVISION}, {}, time.time()
    try:
        dl = [br.download(br.TOPICS_URL, os.path.join(a.data_dir, "topics.json")),
              br.download(br.ASSESS_URL, os.path.join(a.data_dir, "assessments.json"))]
        res["download"] = dl
        for d, want in zip(dl, (br.TOPICS_SHA, br.ASSESS_SHA)):
            if d["sha256"] != want:
                raise ValueError("%s: sha256 %s, pinned %s" % (d["url"], d["sha256"], want))
        with open(os.path.join(a.data_dir, "topics.json"), encoding="utf-8-sig") as f:
            questions = br.load_questions(json.load(f))
        with open(os.path.join(a.data_dir, "assessments.json"), encoding="utf-8-sig") as f:
            assess = json.load(f)
        with open(a.official, encoding="utf-8") as f:
            official = json.load(f)["runs"]
        t1 = time.time()
        ref, _ = br.analyse(br.load_runs(assess), questions, official)
        res["reference_seconds"] = round(time.time() - t1, 1)
        data = load_texts(assess)
        del assess
        topics = sorted(data, key=lambda k: (len(k), k))
        keyed = {t: keys_of(data[t]) for t in topics}
        texts = [x for t in topics for x in keyed[t][1]]
        t1 = time.time()
        vecs = embed(texts, a.model_dir, a.threads)
        res["embed"] = {"texts": len(texts), "seconds": round(time.time() - t1, 1), "threads": a.threads,
                        "max_tokens": MAX_TOKENS, "dtype": "float32"}
        sims, at = {"lex": {}, "emb": {}}, 0
        for t in topics:
            keys = keyed[t][0]
            index = {w: i for i, w in enumerate(keys)}
            sims["lex"][t] = (index, lex_matrix(keys))
            sims["emb"][t] = (index, cos_matrix(vecs[at:at + len(keys)]))
            at += len(keys)
        t1 = time.time()
        out, per = analyse(data, sims, official)
        res["analysis_seconds"] = round(time.time() - t1, 1)
        res.update(out)
        b = str(PRIMARY["lex"])
        res["agreement_with_biogen_reuse"] = {
            "sentence_auroc_team_out": [ref["sentence_auroc"]["team_out"], out["sentence_auroc"]["lex"]["team_out"]],
            "sentence_auroc_run_out": [ref["sentence_auroc"]["run_out"], out["sentence_auroc"]["lex"]["run_out"]],
            "tau_recall_team": [ref["run_tau"][b]["recall_team"], out["run_tau"]["lex"][b]["recall_team"]],
            "tau_precision_team": [ref["run_tau"][b]["precision_team"], out["run_tau"]["lex"][b]["precision_team"]],
            "baseline_tau": [ref["run_tau"]["baseline_sentences_vs_completeness_r"],
                             out["run_tau"]["baseline_sentences_vs_completeness_r"]],
            "sentences": [ref["sentences"], out["sentences"]],
            "sentence_auroc_n": [ref["sentence_auroc_n"], out["sentence_auroc_n"]]}
        res["agree"] = all(x == y for x, y in res["agreement_with_biogen_reuse"].values())
        res["reference"] = {k: ref.get(k) for k in ("sentence_auroc", "run_tau", "repro_precision",
                                                    "pool_distinct_required_per_topic")}
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    res["seconds"] = round(time.time() - t0, 1)
    res["peak_rss_mb"] = peak_mb()
    br.dump(os.path.join(a.out_dir, "emb.json"), res)
    br.dump(os.path.join(a.out_dir, "emb_runs.json"), per)
    print(json.dumps({k: v for k, v in res.items() if k not in ("reference", "run_tau")}, indent=1)[:6000])
    return 1 if res["problem"] else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch-model")
    f.add_argument("--model-dir", required=True)
    f.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--data-dir", required=True)
    r.add_argument("--official", required=True)
    r.add_argument("--model-dir", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--threads", type=int, default=2)
    a = ap.parse_args(argv)
    if a.cmd == "fetch-model":
        try:
            rep = fetch_model(a.model_dir)
        except Exception as e:  # recorded, never hidden
            rep = {"version": VERSION, "problem": "%s: %s" % (type(e).__name__, e)}
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        br.dump(a.out, rep)
        print(json.dumps(rep, indent=1))
        return 1 if rep["problem"] else 0
    os.makedirs(a.out_dir, exist_ok=True)
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
