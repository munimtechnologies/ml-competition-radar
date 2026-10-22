"""Rules for the SPARK Task 1 R dev-set questions (protocol in spark-pubmed/dev_sets/PREREGISTRATION.md).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

A question may not contain any run of three or more consecutive words of its record's title,
where words are the lower-cased [a-z0-9]+ tokens. Python standard library only.
"""
import json
import os
import re

TOKEN_RX = re.compile(r"[a-z0-9]+")
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_WORDS = 45


def tokens(text):
    return TOKEN_RX.findall(text.lower())


def trigrams(text):
    t = tokens(text)
    return set(zip(t, t[1:], t[2:]))


def shared_runs(question, title):
    """Title word triples that also occur, in order and adjacent, in the question."""
    return sorted(" ".join(g) for g in trigrams(question) & trigrams(title))


def load(name, folder=HERE):
    with open(os.path.join(folder, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def problems(questions, titles):
    """Every rule broken by a question set, as readable strings (empty list = all rules hold)."""
    out = []
    by_pmid = {t["pmid"]: t["title"] for t in titles}
    seen = set()
    for q in questions:
        p, text = q["pmid"], q["question"]
        if p in seen:
            out.append("%s: duplicate pmid" % p)
        seen.add(p)
        if p not in by_pmid:
            out.append("%s: no title" % p)
            continue
        if not text.startswith("the "):
            out.append("%s: does not start with 'the '" % p)
        if len(tokens(text)) > MAX_WORDS:
            out.append("%s: %d words > %d" % (p, len(tokens(text)), MAX_WORDS))
        runs = shared_runs(text, by_pmid[p])
        if runs:
            out.append("%s: shares title words %s" % (p, runs))
    missing = set(by_pmid) - seen
    if missing:
        out.append("no question for %s" % sorted(missing))
    return out
