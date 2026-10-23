"""Whole-corpus census of the NLM SPARK PubMed corpus from a local, md5-verified mirror.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Counts, for every verified pubmed27nNNNN.xml.gz under --raw-dir: records, abstracts, PMC ids,
every publication type (UI and name), dates outside the stated window (journal, electronic and
PubMed dates), and duplicate PMIDs across the whole corpus (a bitmap, not a set). Per-file counts
are checkpointed under --state-dir, so a rerun resumes. Writes full_count.json and
full_files.jsonl to --out-dir. Python standard library only; nothing is executed.

v0.2 (run 175): job spark27-fts-v3 found one duplicate PMID but did not say which. The summary
now lists up to 20 duplicate PMIDs with every file that holds each one (duplicate_examples).
Per-file checkpoints from v0.1 are still read as they are.
"""
import argparse
import gzip
import json
import multiprocessing
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from array import array

NAME_RX = re.compile(r"pubmed27n\d{4}\.xml\.gz")
YM_RX = re.compile(r"(\d{4})(?:\s+([A-Za-z]{3}))?")
MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
START_YEAR, END = 1959, (2026, 7, 31)
WATCH = {"D000076942": "Preprint", "D016421": "Editorial", "D016456": "Historical Article"}
KEYS = ("records", "with_abstract", "with_pmcid", "journal_missing", "journal_before_1959",
        "journal_after_2026_07", "journal_2026_no_month", "electronic_after_2026_07",
        "pubmed_after_2026_07", "no_date_on_or_before_end", "deleted_pmids")
MAX_DUP_EXAMPLES = 20


def month_of(text):
    text = (text or "").strip()
    if text.isdigit():
        return int(text)
    return MONTHS.get(text[:3].lower())


def ymd(node):
    if node is None:
        return None
    y = node.findtext("Year")
    if y and y.strip().isdigit():
        d = node.findtext("Day")
        return (int(y), month_of(node.findtext("Month")), int(d) if d and d.strip().isdigit() else None)
    m = YM_RX.search(node.findtext("MedlineDate") or "")
    return (int(m.group(1)), month_of(m.group(2)), None) if m else None


def after_end(d):
    """True / False, or None when the date is too coarse to tell (2026 without a month)."""
    if d[0] != END[0]:
        return d[0] > END[0]
    return None if d[1] is None else d[1] > END[1]


def scan(stream):
    """Count one PubMed XML stream. Returns (stats, pubtypes {ui: [name, n]}, watch examples, pmids)."""
    st = dict.fromkeys(KEYS, 0)
    types, ex, pmids = {}, {ui: [] for ui in WATCH}, array("I")
    for _, el in ET.iterparse(stream, events=("end",)):
        if el.tag == "DeleteCitation":
            st["deleted_pmids"] += len(el.findall("PMID"))
            el.clear()
        elif el.tag == "PubmedArticle":
            cit = el.find("MedlineCitation")
            art = cit.find("Article")
            pmid = int(cit.findtext("PMID"))
            pmids.append(pmid)
            st["records"] += 1
            st["with_abstract"] += art.find("Abstract/AbstractText") is not None
            st["with_pmcid"] += any(a.get("IdType") == "pmc" for a in el.iterfind(
                "PubmedData/ArticleIdList/ArticleId"))
            for p in art.iterfind("PublicationTypeList/PublicationType"):
                ui = p.get("UI") or "?"
                if ui not in types:
                    types[ui] = [(p.text or "").strip(), 0]
                types[ui][1] += 1
                if ui in ex and len(ex[ui]) < 5:
                    ex[ui].append(pmid)
            j = ymd(art.find("Journal/JournalIssue/PubDate"))
            e = ymd(art.find("ArticleDate[@DateType='Electronic']"))
            p = ymd(el.find("PubmedData/History/PubMedPubDate[@PubStatus='pubmed']"))
            if j is None:
                st["journal_missing"] += 1
            else:
                st["journal_before_1959"] += j[0] < START_YEAR
                late = after_end(j)
                st["journal_after_2026_07"] += late is True
                st["journal_2026_no_month"] += late is None
            st["electronic_after_2026_07"] += bool(e and after_end(e))
            st["pubmed_after_2026_07"] += bool(p and after_end(p))
            in_window = [d for d in (j, e) if d and after_end(d) is False]
            if (j or e) and not in_window and not any(d and after_end(d) is None for d in (j, e)):
                st["no_date_on_or_before_end"] += 1
            el.clear()
    return st, types, ex, pmids


def process(args):
    """Scan one file (or load its checkpoint). Returns the per-file record."""
    name, raw_dir, state_dir = args
    jpath, bpath = os.path.join(state_dir, name + ".json"), os.path.join(state_dir, name + ".pmids")
    if os.path.exists(jpath) and os.path.exists(bpath):
        with open(jpath, encoding="utf-8") as f:
            return json.load(f)
    t0 = time.time()
    try:
        with gzip.open(os.path.join(raw_dir, name), "rb") as f:
            st, types, ex, pmids = scan(f)
    except Exception as exc:  # record this file and go on
        return {"file": name, "problem": "%s: %s" % (type(exc).__name__, str(exc)[:160])}
    info = {"file": name, "problem": None, "seconds": round(time.time() - t0, 1), "types": types,
            "examples": ex}
    info.update(st)
    with open(bpath + ".part", "wb") as f:
        pmids.tofile(f)
    os.replace(bpath + ".part", bpath)
    with open(jpath + ".part", "w", encoding="utf-8") as f:
        json.dump(info, f)
    os.replace(jpath + ".part", jpath)
    return info


def load_pmids(state_dir, name):
    a = array("I")
    with open(os.path.join(state_dir, name + ".pmids"), "rb") as f:
        a.frombytes(f.read())
    return a


def run(raw_dir, state_dir, out_dir, workers):
    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(raw_dir)
                   if NAME_RX.fullmatch(n) and os.path.exists(os.path.join(raw_dir, n + ".md5ok")))
    jobs = [(n, raw_dir, state_dir) for n in names]
    t0, results = time.time(), []
    if workers > 1 and len(jobs) > 1:
        with multiprocessing.Pool(workers) as pool:
            for info in pool.imap_unordered(process, jobs):
                results.append(info)
                if len(results) % 50 == 0:
                    print("counted %d/%d %.0fs" % (len(results), len(jobs), time.time() - t0), flush=True)
    else:
        results = [process(j) for j in jobs]
    results.sort(key=lambda i: i["file"])
    good = [i for i in results if not i.get("problem")]
    tot, types, ex = dict.fromkeys(KEYS, 0), {}, {ui: [] for ui in WATCH}
    for i in good:
        for k in KEYS:
            tot[k] += i[k]
        for ui, (label, n) in i["types"].items():
            types.setdefault(ui, [label, 0])[1] += n
        for ui in WATCH:
            ex[ui] = (ex[ui] + i["examples"].get(ui, []))[:10]
    seen, dups, lo, hi, dup_ids = bytearray(), 0, None, None, []
    for i in good:
        for p in load_pmids(state_dir, i["file"]):
            if p >> 3 >= len(seen):
                seen.extend(bytes((p >> 3) + 1 - len(seen) + (1 << 20)))
            bit = 1 << (p & 7)
            if seen[p >> 3] & bit:
                dups += 1
                if len(dup_ids) < MAX_DUP_EXAMPLES and p not in dup_ids:
                    dup_ids.append(p)
            seen[p >> 3] |= bit
            lo, hi = (p if lo is None else min(lo, p)), (p if hi is None else max(hi, p))
    where = {p: [] for p in dup_ids}
    if dup_ids:
        want = set(dup_ids)
        for i in good:
            for p in want.intersection(load_pmids(state_dir, i["file"])):
                where[p].append(i["file"])
    n = tot["records"]
    summary = {
        "verified_files": len(names), "files_ok": len(good),
        "files_failed": [i["file"] for i in results if i.get("problem")], "problem": None,
        "seconds": round(time.time() - t0, 1), "totals": tot,
        "shares": {k: round(tot[k] / n, 6) for k in ("with_abstract", "with_pmcid", "journal_after_2026_07",
                                                    "pubmed_after_2026_07")} if n else {},
        "records_per_file": {str(c): sum(1 for i in good if i["records"] == c)
                             for c in sorted(set(i["records"] for i in good))},
        "duplicate_pmids": dups, "duplicate_examples": [{"pmid": p, "files": where[p]} for p in dup_ids],
        "pmid_min": lo, "pmid_max": hi,
        "watched_types": {ui: {"name": WATCH[ui], "records": types.get(ui, ["", 0])[1], "examples": ex[ui]}
                          for ui in WATCH},
        "publication_types": {ui: {"name": v[0], "records": v[1]}
                              for ui, v in sorted(types.items(), key=lambda kv: -kv[1][1])}}
    if summary["files_failed"]:
        summary["problem"] = "%d file(s) failed (see full_files.jsonl)" % len(summary["files_failed"])
    elif not good:
        summary["problem"] = "no verified corpus files under %s" % raw_dir
    with open(os.path.join(out_dir, "full_files.jsonl"), "w", encoding="utf-8") as f:
        for i in results:
            f.write(json.dumps({k: v for k, v in i.items() if k != "types"}) + "\n")
    with open(os.path.join(out_dir, "full_count.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--state-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args(argv)
    s = run(args.raw_dir, args.state_dir, args.out_dir, args.workers)
    brief = {k: s.get(k) for k in ("problem", "verified_files", "files_ok", "totals", "duplicate_pmids",
                                   "duplicate_examples", "pmid_min", "pmid_max", "records_per_file",
                                   "watched_types")}
    print(json.dumps(brief, indent=1)[:6000])
    return 1 if s["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
