"""Build the two development sets for SPARK Task 1 (known-item retrieval) from public NLM sources.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

L (landmarks): each pre-registered landmark in landmarks.json is looked up in PubMed through NCBI
E-utilities (title words + year first, then first author + year + journal, then title words
alone) and kept only if a record PubMed returns has a near-identical title and a year within one
of the expected year. Nothing is taken from memory: PMID, title, journal, year, publication types
and PMC id all come from PubMed's own summary.
R (random records): fixed-seed reservoir samples of eligible records (title, an abstract of at
least --min-words words, publication year 1959-2026, no excluded publication type) from evenly
spaced, md5-checked files of the SPARK PubMed corpus. Questions for R are written later from the
abstracts alone. Python standard library only. Writes landmarks_verified.json, r_pool.jsonl and
dev.json to --out-dir. Nothing downloaded is executed.
"""
import argparse
import difflib
import gzip
import hashlib
import json
import os
import random
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
CORPUS = "https://ftp.ncbi.nlm.nih.gov/pubmed/.pubmed-spark/"
UA = "MV2-Munim-spark-dev/0.1 (mv2@munimtech.com)"
TOOL = {"tool": "mv2-munim-spark-dev", "email": "mv2@munimtech.com"}
MD5_RX = re.compile(r"\b([0-9a-f]{32})\b")
WORD_RX = re.compile(r"[a-z0-9]+")
STOP = frozenset("a an and are as at be by for from has have in is it of on or that the this to was "
                 "were which with we our these those their its not but than into using used use upon "
                 "through within without during between among".split())
EXCLUDED_TYPES = frozenset(["Editorial", "Comment", "Letter", "News", "Historical Article",
                            "Published Erratum", "Retraction of Publication", "Retracted Publication",
                            "Biography", "Obituary", "Portrait", "Interview", "Preprint"])
TITLE_MIN = 0.85
WINDOW = (1959, 2026)


def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)


def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(WORD_RX.findall(t.lower()))


def title_ratio(a, b):
    return difflib.SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def title_term(title, year=None):
    """PubMed query: up to 10 distinct non-stop title words tagged [ti], plus [dp] if a year is given."""
    words = []
    for w in norm_title(title).split():
        if len(w) > 2 and w not in STOP and w not in words:
            words.append(w)
    term = " AND ".join("%s[ti]" % w for w in words[:10])
    return term + (" AND %d[dp]" % year if year else "")


def year_of_pubdate(pubdate):
    m = re.match(r"\s*(\d{4})", pubdate or "")
    return int(m.group(1)) if m else None


class Eutils:
    """Minimal E-utilities client: at most one call per `pause` seconds, three tries per call."""

    def __init__(self, opener=fetch, pause=0.4, sleep=time.sleep):
        self.opener, self.pause, self.sleep = opener, pause, sleep
        self.calls = 0

    def get(self, endpoint, **params):
        params.update(TOOL, db="pubmed", retmode="json")
        url = EUTILS + endpoint + "?" + urllib.parse.urlencode(params)
        last = None
        for attempt in range(1, 4):
            self.sleep(self.pause)
            self.calls += 1
            try:
                with self.opener(url) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as exc:  # retry, then give up on this call only
                last = exc
                self.sleep(2 * attempt)
        raise RuntimeError("%s: %s: %s" % (endpoint, type(last).__name__, str(last)[:120]))

    def search(self, term):
        return self.get("esearch.fcgi", term=term, retmax=20)["esearchresult"].get("idlist", [])

    def summary(self, pmids):
        if not pmids:
            return []
        res = self.get("esummary.fcgi", id=",".join(pmids))["result"]
        return [res[u] for u in res.get("uids", []) if u in res]


def strategies(item):
    out = [("title+year", title_term(item["title"], item["year"]))]
    if item.get("first_author") and item.get("journal"):
        out.append(("author+year+journal", '%s[1au] AND %d[dp] AND "%s"[ta]'
                    % (item["first_author"], item["year"], item["journal"])))
    out.append(("title", title_term(item["title"])))
    return out


def verify(item, eu):
    """Look one landmark up in PubMed. Returns a record with status verified / not_found / error."""
    base = {k: item.get(k) for k in ("id", "question", "title", "year", "journal", "first_author",
                                     "contested", "control")}
    tried = []
    try:
        for name, term in strategies(item):
            ids = eu.search(term)
            tried.append({"strategy": name, "term": term, "hits": len(ids)})
            cands = []
            for s in eu.summary(ids):
                y = year_of_pubdate(s.get("pubdate"))
                cands.append((title_ratio(item["title"], s.get("title")), y, s))
            good = [c for c in cands if c[0] >= TITLE_MIN and c[1] is not None and abs(c[1] - item["year"]) <= 1]
            good.sort(key=lambda c: (c[0], -abs(c[1] - item["year"])), reverse=True)
            if not good:
                continue
            ratio, y, s = good[0]
            types = list(s.get("pubtype", []))
            pmc = [a.get("value") for a in s.get("articleids", []) if a.get("idtype") == "pmc"]
            authors = s.get("authors") or []
            base.update({
                "status": "verified", "strategy": name, "pmid": str(s.get("uid")),
                "pubmed_title": s.get("title"), "pubdate": s.get("pubdate"), "pubmed_year": y,
                "year_diff": y - item["year"], "pubmed_journal": s.get("source"),
                "pubmed_first_author": s.get("sortfirstauthor") or (authors[0].get("name") if authors else None),
                "pubtypes": types, "pmcid": pmc[0] if pmc else None, "title_ratio": round(ratio, 3),
                "runner_up": ({"pmid": str(good[1][2].get("uid")), "title_ratio": round(good[1][0], 3)}
                              if len(good) > 1 else None),
                "in_window": WINDOW[0] <= y <= WINDOW[1],
                "excluded_types": sorted(set(types) & EXCLUDED_TYPES), "tried": tried})
            return base
        base.update({"status": "not_found", "tried": tried})
    except RuntimeError as exc:
        base.update({"status": "error", "error": str(exc), "tried": tried})
    return base


def run_landmarks(path, out_dir, eu):
    with open(path, encoding="utf-8") as f:
        items = json.load(f)["landmarks"]
    recs = [verify(it, eu) for it in items]
    with open(os.path.join(out_dir, "landmarks_verified.json"), "w", encoding="utf-8") as f:
        json.dump(recs, f, indent=1, ensure_ascii=False)
    ver = [r for r in recs if r["status"] == "verified"]
    main = [r for r in recs if not r.get("control")]
    ctrl = [r for r in recs if r.get("control")]
    by = {}
    for r in ver:
        by[r["strategy"]] = by.get(r["strategy"], 0) + 1
    return {
        "landmarks": len(main), "controls": len(ctrl),
        "verified": sum(1 for r in main if r["status"] == "verified"),
        "verified_title_year": sum(1 for r in main if r.get("strategy") == "title+year"),
        "verified_exact_year": sum(1 for r in main if r.get("year_diff") == 0),
        "verified_by_strategy": by,
        "not_found": [r["id"] for r in recs if r["status"] == "not_found"],
        "errors": [r["id"] for r in recs if r["status"] == "error"],
        "verified_in_window": sum(1 for r in main if r.get("in_window")),
        "verified_with_pmcid": sum(1 for r in main if r.get("pmcid")),
        "verified_excluded_types": {r["id"]: r["excluded_types"] for r in ver if r.get("excluded_types")},
        "with_runner_up": [r["id"] for r in ver if r.get("runner_up")],
        "controls_found": [r["id"] for r in ctrl if r["status"] == "verified"],
        "controls_in_window": [r["id"] for r in ctrl if r.get("in_window")],
        "eutils_calls": eu.calls}


def text_of(elem):
    return " ".join("".join(elem.itertext()).split()) if elem is not None else ""


def year_of(article):
    pub = article.find("Journal/JournalIssue/PubDate")
    if pub is None:
        return None
    y = pub.findtext("Year")
    if not y:
        m = re.search(r"\d{4}", pub.findtext("MedlineDate") or "")
        y = m.group(0) if m else None
    return int(y) if y and y.isdigit() else None


def parse_record(el):
    cit = el.find("MedlineCitation")
    art = cit.find("Article")
    parts = []
    for ab in art.findall("Abstract/AbstractText"):
        label, body = ab.get("Label"), text_of(ab)
        if body:
            parts.append("%s: %s" % (label, body) if label else body)
    pmcid = None
    for aid in el.findall("PubmedData/ArticleIdList/ArticleId"):
        if aid.get("IdType") == "pmc":
            pmcid = (aid.text or "").strip() or None
    return {"pmid": int(cit.findtext("PMID")), "title": text_of(art.find("ArticleTitle")),
            "abstract": " ".join(parts), "year": year_of(art),
            "journal": art.findtext("Journal/ISOAbbreviation") or "",
            "mesh": [text_of(d) for d in cit.findall("MeshHeadingList/MeshHeading/DescriptorName")],
            "pubtypes": [text_of(p) for p in art.findall("PublicationTypeList/PublicationType")],
            "pmcid": pmcid}


def parse_file(path):
    with gzip.open(path, "rb") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == "PubmedArticle":
                yield parse_record(el)
                el.clear()


def eligible(rec, min_words):
    return bool(rec["title"]) and len(rec["abstract"].split()) >= min_words \
        and rec["year"] is not None and WINDOW[0] <= rec["year"] <= WINDOW[1] \
        and not set(rec["pubtypes"]) & EXCLUDED_TYPES


def sample_file(path, k, rng, min_words):
    """Reservoir-sample k eligible records in one pass. Returns (sample, total, eligible)."""
    sample, total, seen = [], 0, 0
    for rec in parse_file(path):
        total += 1
        if not eligible(rec, min_words):
            continue
        seen += 1
        if len(sample) < k:
            sample.append(rec)
        else:
            j = rng.randrange(seen)
            if j < k:
                sample[j] = rec
    return sample, total, seen


def get_file(name, raw_dir, opener=fetch, tries=3):
    """Download one corpus file once, check it against NLM's .md5, mark it verified."""
    path = os.path.join(raw_dir, name)
    marker = path + ".md5ok"
    if os.path.exists(path) and os.path.exists(marker):
        return {"file": name, "skipped": True, "problem": None}
    problem = None
    for attempt in range(1, tries + 1):
        try:
            with opener(CORPUS + name + ".md5") as r:
                m = MD5_RX.search(r.read().decode("ascii", "replace").lower())
            want = m.group(1) if m else None
            h = hashlib.md5()
            with opener(CORPUS + name) as resp, open(path + ".part", "wb") as f:
                for chunk in iter(lambda: resp.read(1 << 20), b""):
                    h.update(chunk)
                    f.write(chunk)
            got = h.hexdigest()
            if got != want:
                problem = "md5 mismatch (want %s, got %s)" % (want, got)
                os.remove(path + ".part")
                continue
            os.replace(path + ".part", path)
            with open(marker, "w", encoding="ascii") as f:
                f.write(got)
            return {"file": name, "skipped": False, "problem": None}
        except Exception as exc:  # record, retry, then give up on this file only
            problem = "attempt %d: %s: %s" % (attempt, type(exc).__name__, str(exc)[:120])
    return {"file": name, "skipped": False, "problem": problem}


def run_pool(numbers, raw_dir, out_dir, per_file, min_words, seed, opener=fetch):
    os.makedirs(raw_dir, exist_ok=True)
    files, pool = [], []
    for num in numbers:
        name = "pubmed27n%04d.xml.gz" % num
        info = get_file(name, raw_dir, opener)
        if not info["problem"]:
            rng = random.Random("%d-%s" % (seed, name))
            sample, total, n_ok = sample_file(os.path.join(raw_dir, name), per_file, rng, min_words)
            for rec in sample:
                rec["file"] = name
            pool.extend(sample)
            info.update({"records": total, "eligible": n_ok, "sampled": len(sample),
                         "eligible_share": round(n_ok / total, 4) if total else None})
        files.append(info)
    with open(os.path.join(out_dir, "r_pool.jsonl"), "w", encoding="utf-8") as f:
        for rec in pool:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    ok = [i for i in files if not i["problem"]]
    rest = [i for i in ok if i["file"] != "pubmed27n0001.xml.gz"]
    return {"files": files, "pool": len(pool), "unique_pmids": len({r["pmid"] for r in pool}),
            "eligible_share_excl_0001": (round(sum(i["eligible"] for i in rest) / sum(i["records"] for i in rest), 4)
                                         if rest and sum(i["records"] for i in rest) else None),
            "failed": [i["file"] for i in files if i["problem"]]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--landmarks", default="landmarks.json")
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--files", default="1,262,523,784,1045,1306")
    ap.add_argument("--per-file", type=int, default=15)
    ap.add_argument("--min-words", type=int, default=80)
    ap.add_argument("--seed", type=int, default=20261022)
    ap.add_argument("--skip-l", action="store_true")
    ap.add_argument("--skip-r", action="store_true")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    summary = {"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "problem": None}
    if not args.skip_l:
        summary["L"] = run_landmarks(args.landmarks, args.out_dir, Eutils())
    if not args.skip_r:
        numbers = [int(x) for x in args.files.split(",")]
        summary["R"] = run_pool(numbers, os.path.join(args.data_dir, "raw"), args.out_dir,
                                args.per_file, args.min_words, args.seed)
        if summary["R"]["failed"]:
            summary["problem"] = "corpus files failed: %s" % ", ".join(summary["R"]["failed"])
    summary["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(args.out_dir, "dev.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1)[:6000])
    return 1 if summary["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
