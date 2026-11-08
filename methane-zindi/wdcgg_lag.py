"""wdcgg_lag 0.1.0: a dated census of how far behind the run date each public CH4 dataset on WMO's
World Data Centre for Greenhouse Gases (WDCGG, gaw.kishou.go.jp) ends.

Why: Zindi's Green Rising Methane Innovation Challenge (opens 2026-11-13) scores five-day forecasts
of daily CH4 against measurements made after submission, at 59 stations from the ICOS, AGAGE, SNO,
NOAA and JMA networks. A live forecast can only use inputs that are already public. This census
records, for every CH4 dataset WDCGG lists, the last date its public files cover.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0. Standard library only.
Usage: python wdcgg_lag.py --out-dir /out [--delay 1.0] [--limit N]
"""
import argparse
import datetime as dt
import html as htmllib
import json
import os
import re
import statistics
import sys
import time
import urllib.request

VERSION = "0.1.0"
BASE = "https://gaw.kishou.go.jp"
LATEST = BASE + "/search/gas_species/ch4/latest"
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"

# WDCGG contributor numbers (first block of a file id, and the number after platform-type in a
# file name) for the networks Zindi's contest names; others are labelled from the page.
NETWORKS = {1: "JMA", 2: "NOAA", 4: "AGAGE", 162: "ICOS"}

ID_RE = re.compile(r"/search/file/([0-9]+(?:-[0-9]+){5})")
NAME_RE = re.compile(r"\bch4_([a-z0-9]{3})(\d{3,5})_([a-z]+)-([a-z]+)_(\d+)_(\d+)-(\d+)_([a-z]+(?:_[a-z]+)*)",
                     re.I)
RANGE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[ T]\d{2}:\d{2}(?::\d{2})?)?\s*[-~–]\s*"
                      r"(\d{4}-\d{2}-\d{2})(?:[ T]\d{2}:\d{2}(?::\d{2})?)?")
SUBMITTED_RE = re.compile(r"submitted by\s+([^\n]{1,80})", re.I)

ACTIVE_FROM = "2025-01-01"


def page_text(raw_html):
    """Visible text with every tag replaced by a line break, entities decoded."""
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", "\n", raw_html)
    s = re.sub(r"<[^>]+>", "\n", s)
    s = htmllib.unescape(s)
    s = re.sub(r"[ \t\r\f\v ]+", " ", s)
    s = re.sub(r"\n\s*", "\n", s)
    return s


def file_ids(raw_html):
    """Unique WDCGG file ids linked from a listing page, in page order."""
    seen, out = set(), []
    for m in ID_RE.finditer(raw_html):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(m.group(1))
    return out


def parse_name(name):
    m = NAME_RE.fullmatch(name)
    if not m:
        return None
    return {"station": m.group(1).upper(), "station_no": m.group(2), "platform": m.group(3).lower(),
            "type": m.group(4).lower(), "contributor_no": int(m.group(5)),
            "resolution": m.group(8).lower()}


def parse_file_page(raw_html):
    """Return (records, contributor). Each record: {name, start, end} (dates as YYYY-MM-DD).

    Each file name is paired with the date range between it and the next file name, unless the
    page's first date range comes before its first file name (range-first layout), in which case
    with the range between the previous file name and it."""
    text = page_text(raw_html)
    flat = re.sub(r"\s+", " ", text)
    names = list(NAME_RE.finditer(flat))
    # open-ended metadata spans (calibration scale, instrument, intake height) end in 9999
    ranges = [r for r in RANGE_RE.finditer(flat) if not r.group(2).startswith("9999")]
    contributor = None
    m = SUBMITTED_RE.search(text)
    if m:
        contributor = m.group(1).strip().rstrip(".").strip() or None
    if not names or not ranges:
        return [], contributor
    range_first = ranges[0].start() < names[0].start()
    records, seen = [], set()
    for i, nm in enumerate(names):
        if range_first:
            lo = names[i - 1].end() if i > 0 else 0
            hi = nm.start()
            cands = [r for r in ranges if r.start() >= lo and r.end() <= hi]
            r = cands[-1] if cands else None
        else:
            lo = nm.end()
            hi = names[i + 1].start() if i + 1 < len(names) else len(flat)
            cands = [r for r in ranges if r.start() >= lo and r.end() <= hi]
            r = cands[0] if cands else None
        name = nm.group(0)
        if r is None or name in seen:
            continue
        seen.add(name)
        records.append({"name": name, "start": r.group(1), "end": r.group(2)})
    return records, contributor


def dataset_row(file_id, records, contributor, as_of):
    """One row per WDCGG file id: data end = latest end over its non-meteorological files."""
    data = [r for r in records if not r["name"].lower().endswith("_met")]
    if not data:
        return None
    meta = parse_name(data[0]["name"]) or {}
    end = max(r["end"] for r in data)
    start = min(r["start"] for r in data)
    cno = meta.get("contributor_no")
    if cno is None:
        cno = int(file_id.split("-")[0])
    network = NETWORKS.get(cno) or (contributor or "contributor %d" % cno)
    lag = (as_of - dt.date.fromisoformat(end)).days
    return {"file_id": file_id, "station": meta.get("station"), "platform": meta.get("platform"),
            "type": meta.get("type"), "contributor_no": cno, "contributor": contributor,
            "network": network, "start": start, "end": end, "lag_days": lag,
            "resolutions": sorted(set(parse_name(r["name"])["resolution"] for r in data
                                      if parse_name(r["name"]))),
            "url": "%s/search/file/%s" % (BASE, file_id)}


def in_window(end, lo, hi):
    return lo <= end <= hi


def summarize(rows):
    groups = {}
    for r in rows:
        key = "%s | %s-%s" % (r["network"], r["platform"], r["type"])
        groups.setdefault(key, []).append(r)
    out = {}
    for key, g in sorted(groups.items()):
        active = [r for r in g if r["end"] >= ACTIVE_FROM]
        out[key] = {"n": len(g), "n_active": len(active),
                    "newest_end": max(r["end"] for r in g),
                    "min_lag_days": min(r["lag_days"] for r in g),
                    "median_lag_days_active": (statistics.median(r["lag_days"] for r in active)
                                               if active else None)}
    return out


def checks(rows, n_ids, n_fetched, n_parsed):
    """Gates G1-G2 and pre-registered predictions P1-P6 (see PREREGISTRATION-wdcgglag.md)."""
    res = {}
    res["G1"] = {"desc": "listing page links at least 300 file ids", "n_ids": n_ids,
                 "held": n_ids >= 300}
    frac = (n_parsed / n_fetched) if n_fetched else 0.0
    res["G2"] = {"desc": "at least 95% of listed ids fetched and parsed into a dated row",
                 "n_fetched": n_fetched, "n_parsed": n_parsed,
                 "fraction_of_ids": round(n_parsed / n_ids, 4) if n_ids else 0.0,
                 "held": bool(n_ids) and n_parsed >= 0.95 * n_ids}
    gated = res["G1"]["held"] and res["G2"]["held"]

    def sel(network=None, platform=None, typ="insitu"):
        return [r for r in rows if (network is None or r["network"] == network)
                and (platform is None or r["platform"] == platform) and r["type"] == typ]

    icos_s = sel("ICOS", "surface")
    in_aug = [r for r in icos_s if in_window(r["end"], "2026-08-01", "2026-08-31")]
    res["P1"] = {"desc": "at least 13 ICOS surface in-situ datasets; all but at most 2 end in Aug 2026",
                 "n": len(icos_s), "n_in_window": len(in_aug),
                 "outside": [(r["station"], r["end"]) for r in icos_s if r not in in_aug],
                 "held": len(icos_s) >= 13 and len(in_aug) >= len(icos_s) - 2}
    ag = [r for r in sel("AGAGE") if r["end"] > "2024-01-01"]
    ag_in = [r for r in ag if in_window(r["end"], "2025-10-01", "2025-10-31")]
    res["P2"] = {"desc": "AGAGE in-situ datasets ending after 2024-01-01: at least 5, all end in Oct 2025",
                 "n": len(ag), "n_in_window": len(ag_in),
                 "outside": [(r["station"], r["end"], r["file_id"]) for r in ag if r not in ag_in],
                 "held": len(ag) >= 5 and len(ag_in) == len(ag)}
    no = sel("NOAA", "surface")
    no_in = [r for r in no if in_window(r["end"], "2025-12-01", "2025-12-31")]
    res["P3"] = {"desc": "NOAA surface in-situ datasets: at least 4, all end in Dec 2025",
                 "n": len(no), "n_in_window": len(no_in),
                 "outside": [(r["station"], r["end"]) for r in no if r not in no_in],
                 "held": len(no) >= 4 and len(no_in) == len(no)}
    surf = sel(None, "surface")
    late = [r for r in surf if r["end"] > "2026-09-30"]
    res["P4"] = {"desc": "no surface in-situ dataset (any contributor) ends after 2026-09-30",
                 "n": len(surf), "n_after": len(late),
                 "after": [(r["network"], r["station"], r["end"]) for r in late],
                 "held": len(surf) > 0 and not late}
    act = [r for r in surf if r["end"] >= ACTIVE_FROM]
    med = statistics.median(r["lag_days"] for r in act) if act else None
    res["P5"] = {"desc": "median lag of surface in-situ datasets ending on/after 2025-01-01 > 120 days",
                 "n": len(act), "median_lag_days": med, "held": med is not None and med > 120}
    tow = sel("ICOS", "tower")
    tow_in = [r for r in tow if in_window(r["end"], "2026-08-01", "2026-08-31")]
    res["P6"] = {"desc": "at least 90% of ICOS tower in-situ datasets end in Aug 2026",
                 "n": len(tow), "n_in_window": len(tow_in),
                 "held": len(tow) > 0 and len(tow_in) >= 0.9 * len(tow)}
    for k in ("P1", "P2", "P3", "P4", "P5", "P6"):
        if not gated:
            res[k]["graded"] = False
            res[k]["note"] = "ungraded: a gate failed"
        else:
            res[k]["graded"] = True
    return res


def fetch(url, tries=3, timeout=60):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace"), None
        except Exception as e:  # network errors are recorded, not fatal
            last = "%s: %s" % (type(e).__name__, e)
            time.sleep(5 * (k + 1))
    return None, last


def write_md(path, out):
    lines = ["# wdcgg_lag %s census (auto-written by the job)" % VERSION, "",
             "Run at %s UTC; lag = days from each dataset's last public date to %s." %
             (out["run_at_utc"], out["as_of"]), "",
             "Listing: %s (%d file ids; %d parsed into dated rows; %d fetch errors)." %
             (LATEST, out["n_ids"], out["n_rows"], len(out["fetch_errors"])), "",
             "## Gates and predictions", ""]
    for k, v in out["checks"].items():
        lines.append("- **%s** %s: %s" % (k, "HELD" if v["held"] else "FAILED", v["desc"]) +
                     ("" if v.get("graded", True) else " (ungraded)"))
    lines += ["", "## By network and platform", "",
              "| network | platform-type | datasets | ending 2025+ | newest end | min lag d | median lag d (2025+) |",
              "|---|---|---|---|---|---|---|"]
    for k, v in out["summary"].items():
        net, pt = k.split(" | ")
        lines.append("| %s | %s | %d | %d | %s | %d | %s |" % (
            net, pt, v["n"], v["n_active"], v["newest_end"], v["min_lag_days"],
            "" if v["median_lag_days_active"] is None else v["median_lag_days_active"]))
    lines += ["", "## Freshest 15 datasets", "", "| station | network | platform | end | lag d | url |",
              "|---|---|---|---|---|---|"]
    for r in sorted(out["rows"], key=lambda r: r["lag_days"])[:15]:
        lines.append("| %s | %s | %s-%s | %s | %d | %s |" % (r["station"], r["network"], r["platform"],
                                                          r["type"], r["end"], r["lag_days"], r["url"]))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    os.makedirs(os.path.join(a.out_dir, "pages"), exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    as_of = now.date()
    listing, err = fetch(LATEST)
    if listing is None:
        print("listing fetch failed: %s" % err)
        return 3
    with open(os.path.join(a.out_dir, "pages", "latest.html"), "w", encoding="utf-8") as f:
        f.write(listing)
    ids = file_ids(listing)
    todo = ids[:a.limit] if a.limit else ids
    print("file ids on listing: %d (fetching %d)" % (len(ids), len(todo)))
    rows, errors, unparsed, n_fetched = [], [], [], 0
    for i, fid in enumerate(todo):
        raw, err = fetch("%s/search/file/%s" % (BASE, fid))
        if raw is None:
            errors.append({"file_id": fid, "error": err})
        else:
            n_fetched += 1
            recs, contrib = parse_file_page(raw)
            row = dataset_row(fid, recs, contrib, as_of)
            if row is None:
                unparsed.append(fid)
                if len(unparsed) <= 10:
                    with open(os.path.join(a.out_dir, "pages", fid + ".html"), "w", encoding="utf-8") as f:
                        f.write(raw)
            else:
                rows.append(row)
            if i < 3:
                with open(os.path.join(a.out_dir, "pages", fid + ".html"), "w", encoding="utf-8") as f:
                    f.write(raw)
        if (i + 1) % 25 == 0:
            print("  %d/%d fetched, %d rows" % (i + 1, len(todo), len(rows)))
            sys.stdout.flush()
        time.sleep(a.delay)
    out = {"version": VERSION, "run_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "as_of": as_of.isoformat(), "listing_url": LATEST, "n_ids": len(ids),
           "n_fetched": n_fetched, "n_rows": len(rows), "unparsed": unparsed,
           "fetch_errors": errors, "summary": summarize(rows) if rows else {},
           "checks": checks(rows, len(ids), n_fetched, len(rows)), "rows": rows}
    with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    write_md(os.path.join(a.out_dir, "RESULTS-wdcgglag-auto.md"), out)
    print(json.dumps({k: (v["held"], v.get("graded", True)) for k, v in out["checks"].items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
