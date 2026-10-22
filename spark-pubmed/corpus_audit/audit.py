"""Conformance audit of the NLM SPARK PubMed/PMC Challenge Corpus (PubMed part), by sample.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

The challenge defines the PubMed corpus as the files at ftp.ncbi.nlm.nih.gov/pubmed/.pubmed-spark/,
"all citations with a publication date from January 1,1959 to July 31,2026", excluding publication
type "preprint" (MeSH UI D000076942). This job reads the live directory listing, streams the chosen
files (never kept on disk), checks each against its .md5, and counts per file: records, dates outside
the window (journal/print date, electronic date, PubMed date), preprints, DeleteCitation entries,
PMC ids, abstracts. PMIDs are checkpointed under --data-dir so a rerun resumes, and are then used for
duplicate checks and a cross-check against run 167's 2026-baseline files. Writes summary.json and
files.jsonl to --out-dir. Nothing downloaded is executed.
"""
import argparse
import gzip
import hashlib
import json
import multiprocessing
import os
import re
import shutil
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from array import array

BASE = "https://ftp.ncbi.nlm.nih.gov/pubmed/.pubmed-spark/"
UA = "MV2-Munim-spark-audit/0.1 (mv2@munimtech.com)"
NAME_RX = re.compile(r"pubmed27n(\d{4})\.xml\.gz(?!\.md5)")
MD5_RX = re.compile(r"\b([0-9a-f]{32})\b")
YM_RX = re.compile(r"(\d{4})(?:\s+([A-Za-z]{3}))?")
MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
PREPRINT = "D000076942"
START, END = (1959, 1, 1), (2026, 7, 31)


def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)


class HashingReader:
    """File-like wrapper that md5-hashes every byte read through it."""

    def __init__(self, raw):
        self.raw, self.md5, self.bytes = raw, hashlib.md5(), 0

    def read(self, n=-1):
        data = self.raw.read(n)
        self.md5.update(data)
        self.bytes += len(data)
        return data

    def drain(self):
        while self.read(1 << 20):
            pass


def list_files(opener=fetch):
    with opener(BASE) as resp:
        html = resp.read().decode("utf-8", "replace")
    return sorted(set("pubmed27n%s.xml.gz" % m.group(1) for m in NAME_RX.finditer(html)))


def pick(names, stride, also):
    chosen = set(names[::stride]) if stride else set(names)
    if names:
        chosen.add(names[-1])
    chosen.update(n for n in names if n[9:13] in also)
    return sorted(chosen)


def month_of(text):
    text = (text or "").strip()
    if text.isdigit():
        return int(text)
    return MONTHS.get(text[:3].lower())


def ymd(node):
    """(year, month or None, day or None) from a node with Year/Month/Day or MedlineDate."""
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
    """Count one PubMed XML stream. Returns (stats, pmids array, examples)."""
    st = {k: 0 for k in ("records", "with_abstract", "with_mesh", "with_pmcid", "preprint",
                         "journal_missing", "journal_before_1959", "journal_after_2026_07",
                         "journal_2026_no_month", "electronic_after_2026_07", "pubmed_after_2026_07",
                         "no_date_on_or_before_end", "deleted_pmids")}
    years, pmids, ex = {}, array("I"), {"journal_before_1959": [], "journal_after_2026_07": [],
                                        "no_date_on_or_before_end": [], "preprint": []}

    def note(key, pmid, date):
        st[key] += 1
        if key in ex and len(ex[key]) < 5:
            ex[key].append([pmid, list(date) if date else None])

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
            st["with_mesh"] += cit.find("MeshHeadingList") is not None
            st["with_pmcid"] += any(a.get("IdType") == "pmc" for a in el.iterfind(
                "PubmedData/ArticleIdList/ArticleId"))
            if any(p.get("UI") == PREPRINT for p in art.iterfind("PublicationTypeList/PublicationType")):
                note("preprint", pmid, None)
            j = ymd(art.find("Journal/JournalIssue/PubDate"))
            e = ymd(art.find("ArticleDate[@DateType='Electronic']"))
            p = ymd(el.find("PubmedData/History/PubMedPubDate[@PubStatus='pubmed']"))
            years[str(j[0]) if j else "none"] = years.get(str(j[0]) if j else "none", 0) + 1
            if j is None:
                st["journal_missing"] += 1
            else:
                if j[0] < START[0]:
                    note("journal_before_1959", pmid, j)
                late = after_end(j)
                if late:
                    note("journal_after_2026_07", pmid, j)
                elif late is None:
                    st["journal_2026_no_month"] += 1
            if e and after_end(e):  # END is the last day of its month, so the month decides
                st["electronic_after_2026_07"] += 1
            if p and after_end(p):
                st["pubmed_after_2026_07"] += 1
            in_window = [d for d in (j, e) if d and after_end(d) is False]
            if (j or e) and not in_window and not any(d and after_end(d) is None for d in (j, e)):
                note("no_date_on_or_before_end", pmid, j or e)
            el.clear()
    return st, pmids, ex, dict(sorted(years.items()))


def paths(data_dir, name):
    return (os.path.join(data_dir, "files", name + ".json"), os.path.join(data_dir, "pmids", name + ".bin"))


def process(name, data_dir, opener=fetch, tries=3):
    """Stream one file, check its md5, checkpoint stats + PMIDs. Returns the stats dict."""
    jpath, bpath = paths(data_dir, name)
    if os.path.exists(jpath) and os.path.exists(bpath):
        with open(jpath, encoding="utf-8") as f:
            return json.load(f)
    info = {"file": name}
    for attempt in range(1, tries + 1):
        try:
            t0 = time.time()
            with opener(BASE + name + ".md5") as r:
                m = MD5_RX.search(r.read().decode("ascii", "replace").lower())
            want = m.group(1) if m else None
            with opener(BASE + name) as resp:
                reader = HashingReader(resp)
                st, pmids, ex, years = scan(gzip.GzipFile(fileobj=reader))
                reader.drain()
            got = reader.md5.hexdigest()
            info.update({"bytes": reader.bytes, "md5": got, "md5_ok": got == want, "attempts": attempt,
                         "seconds": round(time.time() - t0, 1), "problem": None})
            if got != want:
                info["problem"] = "md5 mismatch (want %s)" % want
                continue
            info.update(st)
            info["examples"], info["years"] = ex, years
            for p in (jpath, bpath):
                os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(bpath + ".part", "wb") as f:
                pmids.tofile(f)
            os.replace(bpath + ".part", bpath)
            with open(jpath + ".part", "w", encoding="utf-8") as f:
                json.dump(info, f)
            os.replace(jpath + ".part", jpath)
            return info
        except Exception as exc:  # record, retry, then give up on this file only
            info["problem"] = "attempt %d: %s: %s" % (attempt, type(exc).__name__, str(exc)[:120])
    return info


def _work(args):
    return process(*args)


def load_pmids(data_dir, name):
    a = array("I")
    with open(paths(data_dir, name)[1], "rb") as f:
        a.frombytes(f.read())
    return a


def baseline_check(jsonl, spark_pmids):
    """How many of a 2026-baseline file's records (run 167 jsonl) are in the given SPARK PMID set."""
    out = {"before_1959": [0, 0], "1959_on": [0, 0], "no_year": [0, 0]}
    with open(jsonl, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            y = rec.get("year")
            key = "no_year" if y is None else ("before_1959" if y < START[0] else "1959_on")
            out[key][0] += 1
            out[key][1] += int(rec["pmid"]) in spark_pmids
    return {k: {"records": v[0], "in_spark_file": v[1]} for k, v in out.items()}


def run(data_dir, out_dir, stride, also, workers, baseline_dir, opener=fetch):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    disk = shutil.disk_usage(data_dir)  # sizes the later decision to keep the corpus on disk
    names = list_files(opener)
    chosen = pick(names, stride, also)
    summary = {"data_disk_gb": {"total": round(disk.total / 1e9, 1), "free": round(disk.free / 1e9, 1)},
               "listing_files": len(names), "first": names[0] if names else None,
               "last": names[-1] if names else None, "sample": {"stride": stride, "also": also,
               "files": len(chosen)}, "problem": None}
    jobs = [(n, data_dir) for n in chosen]
    t0, results = time.time(), []
    if workers > 1:
        with multiprocessing.Pool(workers) as pool:
            for info in pool.imap_unordered(_work, jobs):
                results.append(info)
                if len(results) % 10 == 0:
                    print("done %d/%d %.0fs" % (len(results), len(jobs), time.time() - t0), flush=True)
    else:
        results = [process(n, d, opener) for n, d in jobs]
    results.sort(key=lambda i: i["file"])
    with open(os.path.join(out_dir, "files.jsonl"), "w", encoding="utf-8") as f:
        for info in results:
            f.write(json.dumps(info) + "\n")
    good = [i for i in results if not i.get("problem")]
    tot = {}
    for i in good:
        for k, v in i.items():
            if isinstance(v, int) and not isinstance(v, bool) and k not in ("attempts",):
                tot[k] = tot.get(k, 0) + v
    years = {}
    for i in good:
        for y, c in i["years"].items():
            years[y] = years.get(y, 0) + c
    seen, dups, lo, hi = set(), 0, None, None
    for i in good:
        for p in load_pmids(data_dir, i["file"]):
            dups += p in seen
            seen.add(p)
            lo, hi = (p if lo is None else min(lo, p)), (p if hi is None else max(hi, p))
    n = tot.get("records", 0)
    last = names[-1] if names else None
    summary.update({
        "files_ok": len(good), "files_failed": [i["file"] for i in results if i.get("problem")],
        "seconds": round(time.time() - t0, 1), "totals": tot,
        "shares": {k: round(tot.get(k, 0) / n, 6) for k in ("with_abstract", "with_mesh", "with_pmcid",
                   "journal_before_1959", "journal_after_2026_07", "no_date_on_or_before_end")} if n else {},
        "records_per_file": sorted(set(i["records"] for i in good if i["file"] != last)),
        "last_file_records": next((i["records"] for i in good if i["file"] == last), None),
        "duplicate_pmids": dups, "pmid_min": lo, "pmid_max": hi, "journal_years": years,
        "examples": {k: [e for i in good for e in i["examples"][k]][:10] for k in
                     ("journal_before_1959", "journal_after_2026_07", "no_date_on_or_before_end", "preprint")},
        "baseline_crosscheck": {}})
    for num in ("0001", "0656"):
        jsonl = os.path.join(baseline_dir, "pubmed26n%s.jsonl" % num) if baseline_dir else ""
        spark = "pubmed27n%s.xml.gz" % num
        if jsonl and os.path.exists(jsonl) and any(i["file"] == spark for i in good):
            same = set(load_pmids(data_dir, spark))
            summary["baseline_crosscheck"][num] = {
                "same_numbered_file": baseline_check(jsonl, same),
                "anywhere_in_sample": baseline_check(jsonl, seen)}
    if summary["files_failed"]:
        summary["problem"] = "%d file(s) failed (see files.jsonl)" % len(summary["files_failed"])
    elif not good:
        summary["problem"] = "nothing scanned"
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--also", nargs="*", default=["0656"])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--baseline-dir", default="")
    args = ap.parse_args(argv)
    s = run(args.data_dir, args.out_dir, args.stride, args.also, args.workers, args.baseline_dir)
    print(json.dumps({k: s.get(k) for k in ("problem", "listing_files", "files_ok", "totals", "shares",
                                             "duplicate_pmids", "baseline_crosscheck")}, indent=1)[:6000])
    return 1 if s["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
