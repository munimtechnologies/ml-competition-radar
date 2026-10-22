"""Check r_titles.jsonl against PubMed's own titles (NCBI E-utilities esummary) and re-apply the
three-word rule to the official titles. MV2 of Munim, Inc. (made with AI agents working in his
name). Apache-2.0. Python standard library only; one esummary request for all PMIDs.
"""
import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rq_rules  # noqa: E402

ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id="
UA = "MV2-Munim-spark-rq/0.1 (mv2@munimtech.com)"


def fetch_titles(pmids, timeout=60):
    req = urllib.request.Request(ESUMMARY + ",".join(str(p) for p in pmids), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read().decode("utf-8"))["result"]
    return {int(u): result[u].get("title", "") for u in result.get("uids", [])}


def compare(questions, titles, official):
    """Per-PMID comparison of the local title with PubMed's, plus the rule on PubMed's title."""
    rows, local = [], {t["pmid"]: t["title"] for t in titles}
    for q in questions:
        p = q["pmid"]
        off = official.get(p)
        rows.append({"pmid": p, "found": off is not None,
                     "same_words": off is not None and rq_rules.tokens(off) == rq_rules.tokens(local[p]),
                     "official_runs": rq_rules.shared_runs(q["question"], off) if off else []})
    return {"records": len(rows), "found": sum(r["found"] for r in rows),
            "same_words": sum(r["same_words"] for r in rows),
            "official_rule_breaks": [r for r in rows if r["official_runs"]],
            "differs": [dict(r, local=local[r["pmid"]], official=official.get(r["pmid"]))
                        for r in rows if r["found"] and not r["same_words"]],
            "missing": [r["pmid"] for r in rows if not r["found"]]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    questions, titles = rq_rules.load("r_questions.jsonl"), rq_rules.load("r_titles.jsonl")
    s = compare(questions, titles, fetch_titles([q["pmid"] for q in questions]))
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "titles_check.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, indent=1)
    print(json.dumps(s, indent=1)[:6000])
    return 0 if s["found"] == s["records"] and not s["official_rule_breaks"] else 1


if __name__ == "__main__":
    sys.exit(main())
