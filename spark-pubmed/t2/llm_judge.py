"""Can a small open-weight LLM pick out the contradicting citations a negation cue pre-marks?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

SPARK Task 2 scores conflict coverage. On the TREC 2024 BioGen assessors' passage labels, no NLI
cross-encoder met the bar (RESULTS-biogen-nli.md, RESULTS-biogen-nli-large.md), and half of the
contradicting passages carry a negation word against a tenth of the supporting ones
(RESULTS-biogen-cue.md). This tries the next candidate the decision rule named: an
instruction-tuned LLM, shown exactly what the assessors judged (the quoted passage of the cited
paper and the answer sentence), asked whether the passage supports the statement, contradicts it,
or neither, and read off the next-token probabilities of the three answer letters (renormalised
over the letters). It runs only on pairs whose passage has a negation cue (cue_check.py's
neg_passage: 1,432 of the 11,927 judgments, 140 of the 275 Contradicts), so CPU time stays in
hours; every other pair gets (0, 0, 1) and is never flagged.

Scoring is nli_check.py 0.2.0's run(), unchanged: same judgments, same pairs, same entry / slot /
topic-paper blocks and fusions, with the letter probabilities standing in for NLI's (contradiction,
entailment, neutral). So the Contradicts rows compare directly with the NLI rows in README.md; the
Supports rows do not (most Supports pairs are never shown to the model). `gate` adds the same
blocks over the gated judgments only. Outputs are counts and scores, never text.

Default model: Qwen/Qwen2.5-1.5B-Instruct (Apache-2.0) at a pinned revision, bf16 on CPU. After
the first --probe judged pairs, the run stops (exit 1) if the projected time exceeds --max-hours.
Everything but make_judge() and the model download is standard library, so the tests need no torch.

  python llm_judge.py fetch-model --model-dir DIR --out FILE
  python llm_judge.py run --data-dir DIR --model-dir DIR --out-dir DIR [--threads 4]
                          [--max-words 250 --probe 20 --max-hours 8]
"""
import argparse
import json
import math
import os
import sys
import time

import cue_check
import nli_check

VERSION = "0.1.0"
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_REV = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
MODEL_FILES = {"config.json": 660, "generation_config.json": 242, "merges.txt": 1671839,
               "model.safetensors": 3087467144, "tokenizer.json": 7031645, "tokenizer_config.json": 7305,
               "vocab.json": 2776833, "LICENSE": 11343}  # sizes from the HF API at MODEL_REV
SYSTEM = "You are a careful biomedical evidence assessor."
PROMPT = ("Passage from a cited paper:\n{passage}\n\nStatement:\n{sentence}\n\n"
          "Does the passage support the statement, contradict it, or neither? "
          "Answer with one letter: A = supports, B = contradicts, C = neither.")
LETTERS = ("B", "A", "C")  # in nli_check.NLI order: contradiction, entailment, neutral
OUTSIDE = (0.0, 0.0, 1.0)  # pairs the gate does not pass: never flagged


def rnd(x):
    return None if x is None else round(x, 4)


def clip(text, max_words):
    """The first max_words words of text, and whether anything was cut."""
    w = text.split()
    return (" ".join(w[:max_words]), True) if len(w) > max_words else (text, False)


def messages(passage, sentence, max_words=250):
    p, cut = clip(passage, max_words)
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": PROMPT.format(passage=p, sentence=sentence)}], cut


def letter_probs(logits):
    """Softmax over the three letters' logits (already in NLI order)."""
    m = max(logits)
    e = [math.exp(x - m) for x in logits]
    s = sum(e)
    return tuple(x / s for x in e)


def neg_gate(passage, sentence):
    return cue_check.features(passage, sentence)["neg_passage"]


def gated_scorer(pairs, judge, gate=neg_gate, max_words=250, probe=20, max_hours=8.0,
                 clock=time.time, log=print):
    """(p_c, p_e, p_n) per (passage, sentence) pair: judge(messages) -> (probs, letter mass) where
    gate passes, OUTSIDE elsewhere. Stops (SystemExit) if the first `probe` judged pairs project
    the whole run past max_hours."""
    todo = [k for k, (p, s) in enumerate(pairs) if gate(p, s)]
    out, masses, cut, t0 = [OUTSIDE] * len(pairs), [], 0, clock()
    for n, k in enumerate(todo, 1):
        msgs, c = messages(pairs[k][0], pairs[k][1], max_words)
        cut += c
        out[k], mass = judge(msgs)
        masses.append(mass)
        if n == probe:
            per = (clock() - t0) / n
            if per * len(todo) > 3600 * max_hours:
                raise SystemExit("probe: %.1f s per pair x %d pairs is more than %.1f h"
                                 % (per, len(todo), max_hours))
        if n % 100 == 0:
            log("judged %d/%d pairs, %.0f s" % (n, len(todo), clock() - t0))
    secs = clock() - t0
    return out, {"pairs": len(pairs), "judged": len(todo), "clipped": cut, "max_words": max_words,
                 "seconds": round(secs, 1), "ms_per_judged_pair": rnd(1000 * secs / max(1, len(todo))),
                 "letter_mass_mean": rnd(sum(masses) / len(masses)) if masses else None,
                 "letter_mass_min": rnd(min(masses)) if masses else None,
                 "letter_mass_below_half": sum(1 for m in masses if m < 0.5)}


def make_judge(model_dir, threads=4):
    """judge(messages) -> (letter probs in NLI order, total probability of the three letters)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(threads)
    tok = AutoTokenizer.from_pretrained(model_dir)
    # low_cpu_mem_usage (needs accelerate) keeps the peak near one copy of the 3.09 GB weights
    model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.bfloat16,
                                                 use_safetensors=True, low_cpu_mem_usage=True)
    model.eval()
    ids = []
    for letter in LETTERS:
        t = tok.encode(letter, add_special_tokens=False)
        if len(t) != 1:
            raise SystemExit("answer letter %r is %d tokens" % (letter, len(t)))
        ids.append(t[0])

    def judge(msgs):
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(text, return_tensors="pt")
        with torch.inference_mode():
            logits = model(**enc).logits[0, -1].float()
        mass = float(torch.softmax(logits, dim=-1)[ids].sum())
        return letter_probs([float(logits[i]) for i in ids]), mass

    return judge, {"dtype": "bfloat16", "threads": threads, "letter_ids": ids}


def check_model(rep, pins=MODEL_FILES):
    """Problems: a pinned file missing from a fetch_model report or of another size."""
    bad = []
    for name, size in sorted(pins.items()):
        got = rep.get("files", {}).get(name)
        if got is None:
            bad.append("%s: missing" % name)
        elif got["bytes"] != size:
            bad.append("%s: %d bytes, expected %d" % (name, got["bytes"], size))
    return bad


def big_get(url, dest, _max_bytes):
    return nli_check.fetch(url, dest, 4 << 30)  # model.safetensors is 3.09 GB, over fetch_model's 2 GiB


def gate_eval(path, probs_by_pair, gate=neg_gate):
    """nli_check.evaluate over the gated judgments only (same filter as nli_check.run)."""
    with open(path, encoding="utf-8-sig") as f:
        ents, _ = nli_check.entries(json.load(f))
    sub = [e for e in ents if e[3] is not None and e[5] and e[6] and gate(e[5], e[6])]
    res = {"judgments": len(sub),
           "labels": {l: sum(1 for e in sub if e[4] == l) for l in nli_check.ORDER}}
    if sub:
        res.update(nli_check.evaluate(sub, [probs_by_pair[(e[5], e[6])] for e in sub]))
    return res


def run(data_dir, model_dir, threads=4, max_words=250, probe=20, max_hours=8.0,
        judge_factory=make_judge, sha=nli_check.ASSESS_SHA256):
    judge, info = judge_factory(model_dir, threads)
    by_pair = {}

    def scorer(pairs):
        probs, rep = gated_scorer(pairs, judge, neg_gate, max_words, probe, max_hours)
        by_pair.update(zip(pairs, probs))
        rep.update(info)
        return probs, rep

    res = nli_check.run(data_dir, scorer, sha=sha, model=MODEL_ID, rev=MODEL_REV)
    res["llm_judge_version"] = VERSION
    if not res["problems"]:
        res["gate"] = gate_eval(os.path.join(data_dir, "assessments.json"), by_pair)
    return res


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
    r.add_argument("--threads", type=int, default=4)
    r.add_argument("--max-words", type=int, default=250)
    r.add_argument("--probe", type=int, default=20)
    r.add_argument("--max-hours", type=float, default=8.0)
    a = ap.parse_args(argv)
    if a.cmd == "fetch-model":
        rep = nli_check.fetch_model(a.model_dir, files=tuple(MODEL_FILES), rev=MODEL_REV, get=big_get,
                                    model=MODEL_ID)
        rep["problems"] = check_model(rep)
        nli_check.dump(a.out, rep)
        print(json.dumps(rep, indent=1))
        return 1 if rep["problems"] else 0
    os.makedirs(a.out_dir, exist_ok=True)
    res = run(a.data_dir, a.model_dir, a.threads, a.max_words, a.probe, a.max_hours)
    nli_check.dump(os.path.join(a.out_dir, "llm.json"), res)
    print(json.dumps({k: res.get(k) for k in ("problems", "counts", "census", "scoring")}, indent=1))
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
