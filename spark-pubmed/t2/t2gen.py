"""Can a small, openly licensed instruction model write a cited answer from given PubMed abstracts
on a CPU, and do its sentences stay with the abstracts they cite?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

SPARK Task 2 asks for written answers with citations. MV2's extractive composer copies abstract
sentences, and against NLM's expert nuggets those carried far fewer of the experts' facts than the
LLM-written TREC 2024 BioGen answers (RESULTS-mv2-nugget.md). Before building a written stage,
this job measures only feasibility, format and lexical grounding, with no nugget or pool scoring:

  questions  the 40 MedAESQA questions (NLM, CC0, osf.io/ydbzq)
  evidence   up to K=8 abstracts per question: first the PMIDs cited in the expert-written answer
             (in order), then papers the BioGen assessors judged Supports in the 30 runs (most
             often first); title + the first 160 abstract words, fetched from NCBI E-utilities.
             This is an easy, oracle-style setting, not MV2's own retrieval.
  writer     Qwen/Qwen2.5-0.5B-Instruct (Apache-2.0, pinned revision), float32, greedy, at most
             400 new tokens, one fixed prompt asking for <= 200 words and [n] citations
  measures   seconds per answer, prompt and new tokens, words (<= 250 is BioGen's limit),
             sentences carrying a valid [n], out-of-range numbers, lexical grounding (share of a
             sentence's content words found in the abstracts it cites), whether a sentence's
             citations include the shown abstract it overlaps most, 8-word verbatim spans,
             answers that decline
  references the expert answers' own sentences against the full abstracts they cite; and the
             model's sentences against the next question's abstracts (a negative control)

Outputs: t2gen.json and per_question.json (counts and scores, never text) and answers.jsonl (the
generated text, for inspection only; never published, since it is derived from abstracts).

  python t2gen.py fetch-model --model-dir DIR --out FILE
  python t2gen.py run --medaesqa-dir DIR --model-dir DIR --out-dir DIR [--threads 2 --k 8
                      --abstract-words 160 --max-new-tokens 400 --probe 3 --max-hours 4]
Everything but make_writer() is standard library, so the tests need no torch.
"""
import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

VERSION = "0.1.0"
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"
MEDAESQA_URL = "https://osf.io/download/9d3qs/"
MEDAESQA_SHA = "a062742c1678b4379121ad030a06bda574afd376f331df41575938dd9849c383"  # medaesqa-nugget-v1
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
HF = "https://huggingface.co/%s/resolve/%s/%s"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
MODEL_REV = "7ae557604adf67be50417f59c2c2f167def9a775"  # as in llm_judge 0.2.0 (biogen-llm-v3)
MODEL_FILES = {"config.json": 659, "generation_config.json": 242, "merges.txt": 1671839,
               "model.safetensors": 988097824, "tokenizer.json": 7031645, "tokenizer_config.json": 7305,
               "vocab.json": 2776833, "LICENSE": 11343}
K = 8  # abstracts shown per question
ABSTRACT_WORDS = 160  # abstract words shown (after the title)
ANSWER_WORDS = 200  # asked for in the prompt
LIMIT_WORDS = 250  # BioGen's answer limit, used for compliance
MAX_NEW = 400
FETCH_PER_Q = 20  # candidate PMIDs fetched per question (all expert PMIDs are always fetched)
MIN_WORDS = 3  # a sentence needs 3 content words to be scored
NGRAM = 8  # verbatim span length, in words
WEAK = 0.5  # a cited sentence below this grounding is "weak"

STOP = set("""a about above after again against all also am an and any are as at be because been before
being below between both but by can could did do does doing down during each few for from further had
has have having he her here hers him his how i if in into is it its itself just may me might more most
must my no nor not of off on once only or other our out over own same she should so some such than that
the their them then there these they this those through to too under until up very was we were what
when where which while who whom why will with would you your pmid pmids et al""".split())
WORD_RX = re.compile(r"[a-z0-9]+(?:['\-][a-z0-9]+)*")
PMID_RX = re.compile(r"(?<![\d.])\d{6,9}(?!\d)(?!\.\d)")
CITE_RX = re.compile(r"\[([^\[\]]*)\]")
SPLIT_RX = re.compile(r"(?<=[.!?])\s+")
LEAD_RX = re.compile(r"^(?:\s*(?:\[[^\[\]]*\]|\((?:PMIDs?:?\s*)?[\d,;\s]+\)))+", re.I)
BULLET_RX = re.compile(r"^\s*(?:[-*•]+|\d+[.)])\s+")
DECLINE_RX = re.compile(r"\b(?:cannot|can't|unable to|not possible to)\b|\bdo(?:es)? not (?:answer|address|provide"
                        r"|contain)\b|\bno (?:relevant )?information\b", re.I)
SYSTEM = "You are a careful biomedical writer. You answer health questions using only the evidence you are given."
PROMPT = ("Question: {question}\n\nNumbered PubMed abstracts:\n{evidence}\n\n"
          "Write a concise answer to the question in at most {words} words, using only facts stated in these "
          "abstracts. End every sentence with the number of each abstract that supports it in square brackets, "
          "for example [2] or [1][3]. If the abstracts disagree, say so. If they do not answer the question, "
          "say that.")


class Stop(Exception):
    """The speed probe projects the run past its time budget."""


def r4(x):
    return None if x is None else round(x, 4)


def share(a, b):
    return round(a / b, 4) if b else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 4) if xs else None


def median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def unique(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def clean(text):
    """Text without [..] groups and 6-9 digit PMIDs."""
    return PMID_RX.sub(" ", CITE_RX.sub(" ", text or ""))


def tokens(text):
    return WORD_RX.findall((text or "").lower())


def content(text):
    return {w for w in tokens(text) if w not in STOP and (len(w) > 1 or w.isdigit())}


def ngrams(toks, n=NGRAM):
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def ground(words, source):
    """Share of a sentence's content words found in the source words (None for no words)."""
    return len(words & source) / len(words) if words else None


def split_sentences(text):
    """Sentences, one line at a time; bullets and ** dropped; citation groups that open a fragment
    (as in 'risk. [1] Next') are moved back to the sentence before."""
    out = []
    for line in (text or "").splitlines():
        line = BULLET_RX.sub("", line.replace("**", "")).strip()
        if not line:
            continue
        for part in SPLIT_RX.split(line):
            m = LEAD_RX.match(part)
            if m and out:
                out[-1] = out[-1] + " " + m.group(0).strip()
                part = part[m.end():]
            part = part.strip()
            if part:
                out.append(part)
    return out


def cites(sentence, k):
    """(sorted valid abstract numbers 1..k, list of out-of-range numbers) in the [..] groups."""
    nums = [int(x) for g in CITE_RX.findall(sentence) for x in re.findall(r"\d+", g)]
    return sorted({n for n in nums if 1 <= n <= k}), [n for n in nums if not 1 <= n <= k]


def expert_pmids(text):
    return unique(PMID_RX.findall(text or ""))


def supported_pmids(unit):
    """PMIDs the BioGen assessors judged Supports in this item's machine answers, most often first.
    Field names are not assumed: a PMID is a digit string under a key containing 'pmid', and the
    label is any string value equal to 'supports' / 'supporting' / 'support'."""
    counts = {}
    mga = unit.get("machine_generated_answers")
    answers = mga.values() if isinstance(mga, dict) else (mga if isinstance(mga, list) else [])
    for ans in answers:
        if not isinstance(ans, dict):
            continue
        for s in ans.get("answer_sentences") or []:
            if not isinstance(s, dict):
                continue
            for c in s.get("citation_assessment") or []:
                if not isinstance(c, dict):
                    continue
                pmid = next((str(v).strip() for k, v in c.items()
                             if "pmid" in str(k).lower() and str(v).strip().isdigit()), None)
                sup = any(isinstance(v, str) and v.strip().lower() in ("supports", "supporting", "support")
                          for v in c.values())
                if pmid and sup:
                    counts[pmid] = counts.get(pmid, 0) + 1
    return [p for p, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]


def load_items(obj):
    """MedAESQA items sorted by id: id, question, expert answer, its PMIDs, candidate PMIDs."""
    while isinstance(obj, dict) and len(obj) == 1 and isinstance(next(iter(obj.values())), (dict, list)):
        obj = next(iter(obj.values()))
    units = obj.values() if isinstance(obj, dict) else obj
    out = []
    for u in units:
        if isinstance(u, dict) and isinstance(u.get("question"), str):
            ans = u.get("expert_curated_answer") if isinstance(u.get("expert_curated_answer"), str) else ""
            exp = expert_pmids(ans)
            out.append({"id": str(u.get("question_id")), "question": u["question"], "expert": ans,
                        "pmids": exp, "candidates": unique(exp + supported_pmids(u))})
    out.sort(key=lambda r: (len(r["id"]), r["id"]))
    return out


def full_text(rec):
    return ("%s %s" % (rec.get("title", ""), rec.get("abstract", ""))).strip()


def evidence(pmids, abstracts, k=K, abstract_words=ABSTRACT_WORDS):
    """[(pmid, shown text)]: the first k PMIDs with a non-empty abstract; title + first words."""
    out = []
    for p in pmids:
        if len(out) >= k:
            break
        rec = abstracts.get(p)
        if rec and rec.get("abstract"):
            out.append((p, ("%s %s" % (rec.get("title", ""), " ".join(rec["abstract"].split()[:abstract_words]))).strip()))
    return out


def messages(question, ev, words=ANSWER_WORDS):
    lines = "\n".join("[%d] %s" % (i, t) for i, (_, t) in enumerate(ev, 1))
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": PROMPT.format(question=question, evidence=lines, words=words)}]


def analyse_answer(text, shown, other=None):
    """Per-sentence citation and grounding rows (no text) for an answer written from `shown`
    (texts numbered 1..k); `other` texts give the negative control."""
    k = len(shown)
    src = [content(t) for t in shown]
    allsrc = set().union(*src)
    grams = set().union(*(ngrams(tokens(t)) for t in shown))
    oth = set().union(*(content(t) for t in other)) if other else None
    rows = []
    for s in split_sentences(text):
        valid, invalid = cites(s, k)
        body = clean(s)
        w = content(body)
        row = {"valid": valid, "invalid": len(invalid), "content_words": len(w), "scored": len(w) >= MIN_WORDS}
        if row["scored"]:
            row["ground_any"] = r4(ground(w, allsrc))
            if valid:
                per = [ground(w, x) for x in src]
                row["ground_cited"] = r4(ground(w, set().union(*(src[i - 1] for i in valid))))
                row["cites_best"] = any(per[i - 1] == max(per) for i in valid)
            if oth is not None:
                row["ground_other"] = r4(ground(w, oth))
            row["verbatim"] = bool(ngrams(tokens(body)) & grams)
        rows.append(row)
    return {"words": len(tokens(clean(text))), "sentences": len(rows), "rows": rows,
            "declines": bool(DECLINE_RX.search(text or ""))}


def aggregate(per_q):
    qs = [q for q in per_q if not q.get("skipped")]
    rows = [r for q in qs for r in q["rows"]]
    scored = [r for r in rows if r["scored"]]
    cited = [r for r in scored if r["valid"]]
    secs = [q["seconds"] for q in qs]
    new = [q["new_tokens"] for q in qs]
    return {"answers": len(qs), "skipped": len(per_q) - len(qs),
            "empty": sum(1 for q in qs if q["sentences"] == 0),
            "seconds_median": r4(median(secs)), "seconds_max": r4(max(secs, default=None)),
            "seconds_total": r4(sum(secs)), "prompt_tokens_median": median([q["prompt_tokens"] for q in qs]),
            "new_tokens_median": median(new), "tokens_per_second": share(sum(new), sum(secs)),
            "truncated": sum(1 for q in qs if q["truncated"]),
            "words_median": median([q["words"] for q in qs]), "words_max": max((q["words"] for q in qs), default=None),
            "within_limit": sum(1 for q in qs if q["words"] <= LIMIT_WORDS),
            "sentences": len(rows), "scored": len(scored), "cited": len(cited),
            "cited_share": share(len(cited), len(scored)),
            "invalid_citation_sentences": sum(1 for r in rows if r["invalid"]),
            "invalid_citation_share": share(sum(1 for r in rows if r["invalid"]), len(rows)),
            "answers_without_valid_citation": sum(1 for q in qs if not any(r["valid"] for r in q["rows"])),
            "ground_cited_mean": mean([r["ground_cited"] for r in cited]),
            "ground_cited_weak_share": share(sum(1 for r in cited if r["ground_cited"] < WEAK), len(cited)),
            "ground_any_mean": mean([r["ground_any"] for r in scored]),
            "ground_other_mean": mean([r.get("ground_other") for r in scored]),
            "cites_best_share": share(sum(1 for r in cited if r["cites_best"]), len(cited)),
            "verbatim_share": share(sum(1 for r in scored if r["verbatim"]), len(scored)),
            "declines": sum(1 for q in qs if q["declines"])}


def expert_reference(items, abstracts):
    """The expert answers' sentences against the full abstracts of the PMIDs each one cites."""
    rows, n_sent, no_pmid = [], 0, 0
    for it in items:
        for s in split_sentences(it["expert"]):
            n_sent += 1
            ps = [p for p in expert_pmids(s) if abstracts.get(p, {}).get("abstract")]
            body = clean(s)
            w = content(body)
            if len(w) < MIN_WORDS:
                continue
            if not ps:
                no_pmid += 1
                continue
            texts = [full_text(abstracts[p]) for p in ps]
            src = set().union(*(content(t) for t in texts))
            grams = set().union(*(ngrams(tokens(t)) for t in texts))
            rows.append({"ground": ground(w, src), "verbatim": bool(ngrams(tokens(body)) & grams)})
    return {"sentences": n_sent, "scored": len(rows), "scored_without_fetched_pmid": no_pmid,
            "ground_mean": mean([r["ground"] for r in rows]),
            "weak_share": share(sum(1 for r in rows if r["ground"] < WEAK), len(rows)),
            "verbatim_share": share(sum(1 for r in rows if r["verbatim"]), len(rows)),
            "words_median": median([len(tokens(clean(it["expert"]))) for it in items]),
            "questions_with_pmid": sum(1 for it in items if it["pmids"]),
            "pmids_per_question_median": median([len(it["pmids"]) for it in items])}


def http_get(url, timeout=120, tries=3):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:  # retried, then raised
            if n == tries - 1:
                raise
            time.sleep(3)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def download(url, dest, get=http_get):
    """The file at dest (fetched if missing), its size and sha256."""
    cached = os.path.exists(dest)
    if cached:
        with open(dest, "rb") as f:
            body = f.read()
    else:
        body = get(url, timeout=300)
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with open(dest, "wb") as f:
            f.write(body)
    return {"url": url, "bytes": len(body), "sha256": sha256_bytes(body), "cached": cached}, body


def parse_pubmed(xml_bytes):
    """{pmid: {title, abstract}} from an efetch PubmedArticleSet."""
    out = {}
    root = ET.fromstring(xml_bytes)
    for art in root.iter("PubmedArticle"):
        pmid = (art.findtext("MedlineCitation/PMID") or "").strip()
        if not pmid:
            continue
        t = art.find(".//ArticleTitle")
        title = " ".join("".join(t.itertext()).split()) if t is not None else ""
        parts = [" ".join("".join(e.itertext()).split()) for e in art.iterfind(".//Abstract/AbstractText")]
        out[pmid] = {"title": title, "abstract": " ".join(p for p in parts if p)}
    return out


def efetch(pmids, get=http_get, pause=0.4, batch=100):
    """Titles and abstracts from NCBI E-utilities, at most 100 PMIDs per request, < 3 requests/s."""
    out = {}
    for i in range(0, len(pmids), batch):
        q = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids[i:i + batch]), "retmode": "xml",
                                    "tool": "mv2-munim-t2gen", "email": "mv2@munimtech.com"})
        out.update(parse_pubmed(get(EFETCH + "?" + q)))
        time.sleep(pause)
    return out


def check_model_dir(model_dir, files=MODEL_FILES):
    bad = []
    for name, size in sorted(files.items()):
        p = os.path.join(model_dir, name)
        if not os.path.exists(p):
            bad.append("%s: missing" % name)
        elif os.path.getsize(p) != size:
            bad.append("%s: %d bytes, expected %d" % (name, os.path.getsize(p), size))
    return bad


def fetch_model(model_dir, files=MODEL_FILES, rev=MODEL_REV):
    """Each pinned file from the Hugging Face hub at the pinned revision, unless already there at
    the pinned size."""
    os.makedirs(model_dir, exist_ok=True)
    rep = {"model": MODEL_ID, "revision": rev, "files": {}}
    for name, size in sorted(files.items()):
        dest = os.path.join(model_dir, name)
        cached = os.path.exists(dest) and os.path.getsize(dest) == size
        if not cached:
            req = urllib.request.Request(HF % (MODEL_ID, rev, name), headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            os.replace(dest + ".part", dest)
        rep["files"][name] = {"bytes": os.path.getsize(dest), "cached": cached}
    rep["problems"] = check_model_dir(model_dir, files)
    return rep


def cpu_limit(path="/sys/fs/cgroup/cpu.max"):
    try:
        with open(path, encoding="ascii") as f:
            quota, period = f.read().split()[:2]
        return None if quota == "max" else round(int(quota) / int(period), 2)
    except (OSError, ValueError):
        return None


def peak_rss_gb():
    try:
        import resource
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2), 3)  # KiB on Linux
    except Exception:  # not on every platform
        return None


def make_writer(model_dir, threads=2, max_new_tokens=MAX_NEW):
    """write(messages) -> (answer text, prompt tokens, new tokens)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    t0 = time.time()
    torch.set_num_threads(threads)
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.float32, use_safetensors=True,
                                                 low_cpu_mem_usage=True)
    model.eval()

    def write(msgs):
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(text, return_tensors="pt")
        n_in = int(enc["input_ids"].shape[1])
        with torch.inference_mode():
            out = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False)
        new = out[0, n_in:]
        return tok.decode(new, skip_special_tokens=True).strip(), n_in, int(new.shape[0])

    return write, {"dtype": "float32", "threads": threads, "torch_threads": torch.get_num_threads(),
                   "cpu_limit": cpu_limit(), "load_seconds": round(time.time() - t0, 1),
                   "torch": torch.__version__, "decoding": "greedy", "max_new_tokens": max_new_tokens}


def run(medaesqa_dir, model_dir, out_dir, threads=2, k=K, abstract_words=ABSTRACT_WORDS, max_new_tokens=MAX_NEW,
        probe=3, max_hours=4.0, writer_factory=make_writer, get=http_get, sha=MEDAESQA_SHA, pause=0.4,
        clock=time.time):
    os.makedirs(out_dir, exist_ok=True)
    res = {"version": VERSION, "model": MODEL_ID, "revision": MODEL_REV, "k": k, "abstract_words": abstract_words,
           "answer_words_asked": ANSWER_WORDS, "limit_words": LIMIT_WORDS, "problem": None}
    per_q, t_start = [], clock()
    try:
        dl, body = download(MEDAESQA_URL, os.path.join(medaesqa_dir, "medaesqa_v1.json"), get)
        res["download"] = dl
        if dl["sha256"] != sha:
            raise ValueError("MedAESQA sha256 %s, pinned %s" % (dl["sha256"], sha))
        items = load_items(json.loads(body.decode("utf-8-sig")))
        res["items"] = len(items)
        want = unique([p for it in items for p in it["pmids"] + it["candidates"][:FETCH_PER_Q]])
        abstracts = efetch(want, get, pause)
        res["pmids"] = {"requested": len(want), "returned": sum(1 for p in want if p in abstracts),
                        "with_abstract": sum(1 for p in want if abstracts.get(p, {}).get("abstract"))}
        res["expert"] = expert_reference(items, abstracts)
        shown = {it["id"]: evidence(it["candidates"], abstracts, k, abstract_words) for it in items}
        res["evidence"] = {"questions_with_evidence": sum(1 for v in shown.values() if v),
                           "shown_median": median([len(v) for v in shown.values()]),
                           "expert_shown_median": median([sum(1 for p, _ in shown[it["id"]] if p in it["pmids"])
                                                          for it in items])}
        todo = [it for it in items if shown[it["id"]]]
        write, info = writer_factory(model_dir, threads, max_new_tokens)
        res["writer"] = info
        ids = [it["id"] for it in items]
        t0 = clock()
        with open(os.path.join(out_dir, "answers.jsonl"), "w", encoding="utf-8") as fa:
            for it in items:
                ev = shown[it["id"]]
                if not ev:
                    per_q.append({"id": it["id"], "skipped": True})
                    continue
                nxt = shown[ids[(ids.index(it["id"]) + 1) % len(ids)]]
                t1 = clock()
                text, n_in, n_new = write(messages(it["question"], ev, ANSWER_WORDS))
                secs = clock() - t1
                fa.write(json.dumps({"id": it["id"], "pmids": [p for p, _ in ev], "answer": text}) + "\n")
                fa.flush()
                per_q.append({"id": it["id"], "shown": len(ev),
                              "expert_shown": sum(1 for p, _ in ev if p in it["pmids"]),
                              "seconds": round(secs, 2), "prompt_tokens": n_in, "new_tokens": n_new,
                              "truncated": n_new >= max_new_tokens, **analyse_answer(text, [t for _, t in ev],
                                                                                    [t for _, t in nxt])})
                done = sum(1 for q in per_q if not q.get("skipped"))
                if done == probe:
                    per = (clock() - t0) / done
                    res["probe_seconds_per_answer"] = round(per, 2)
                    if per * len(todo) > 3600 * max_hours:
                        raise Stop("probe: %.1f s per answer x %d answers is more than %.1f h"
                                   % (per, len(todo), max_hours))
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    res["answers"] = aggregate(per_q)
    res["peak_rss_gb"] = peak_rss_gb()
    res["seconds"] = round(clock() - t_start, 1)
    with open(os.path.join(out_dir, "t2gen.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(out_dir, "per_question.json"), "w", encoding="utf-8") as f:
        json.dump(per_q, f, indent=1)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    fm = sub.add_parser("fetch-model")
    fm.add_argument("--model-dir", required=True)
    fm.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--medaesqa-dir", required=True)
    r.add_argument("--model-dir", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--threads", type=int, default=2)
    r.add_argument("--k", type=int, default=K)
    r.add_argument("--abstract-words", type=int, default=ABSTRACT_WORDS)
    r.add_argument("--max-new-tokens", type=int, default=MAX_NEW)
    r.add_argument("--probe", type=int, default=3)
    r.add_argument("--max-hours", type=float, default=4.0)
    a = ap.parse_args(argv)
    if a.cmd == "fetch-model":
        rep = fetch_model(a.model_dir)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=1)
        print(json.dumps(rep, indent=1))
        return 1 if rep["problems"] else 0
    res = run(a.medaesqa_dir, a.model_dir, a.out_dir, a.threads, a.k, a.abstract_words, a.max_new_tokens,
              a.probe, a.max_hours)
    print(json.dumps(res, indent=1)[:8000])
    return 1 if res["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
