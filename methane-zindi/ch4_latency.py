#!/usr/bin/env python3
"""ch4lag: how fresh is public station methane data? A dated census for live five-day forecasting.

Prepares MV2's entry for Zindi's Green Rising Methane Innovation Challenge (daily CH4 five days
ahead at 59 stations from ICOS, AGAGE, SNO, NOAA and JMA, scored against measurements made after
submission). A five-day forecast can only lean on recent observations if a station's data are
public soon after they are measured. This job measures that, station by station, on the day it runs:

  ICOS   every current (not deprecated) "ICOS ATC NRT CH4 growing time series" object and every
         current "ICOS ATC CH4 Release" (Level 2) object, read from the ICOS Carbon Portal's
         public SPARQL endpoint: per station, the freshest end of data, the delay between that
         end and the object's submission, and the lag to the time of the query.
  sample the newest NRT objects of the SAMPLE_N freshest live stations are downloaded and parsed,
         to see whether the last valid CH4 value really sits at the metadata's end of data.
  NOAA   every CH4 in-situ DailyData.txt file in NOAA GML's public directory: last valid day.

Standard library only. Writes results.json, RESULTS-ch4lag.md (tables, no raw data) and
header-samples.txt (file headers, kept private: they can name people).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
Data: ICOS Carbon Portal metadata and ICOS ATC NRT data (ICOS CC BY 4.0 licence);
NOAA GML in-situ CH4 (CC0 1.0).
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from xml.etree import ElementTree
from datetime import datetime, timedelta, timezone

VERSION = "0.1.0"
SPARQL = "https://meta.icos-cp.eu/sparql"
NRT_SPEC = "http://meta.icos-cp.eu/resources/cpmeta/atcCh4NrtGrowingDataObject"
L2_SPEC = "http://meta.icos-cp.eu/resources/cpmeta/atcCh4L2DataObject"
DOWNLOAD = "https://data.icos-cp.eu/licence_accept?ids=%5B%22{h}%22%5D"
NOAA_DIR = "https://gml.noaa.gov/aftp/data/greenhouse_gases/ch4/in-situ/surface/txt/"
LIVE_DAYS = 7.0
STALE_DAYS = 30.0
SAMPLE_N = 5
SAMPLE_GAP_DAYS = 2.0
USER_AGENT = "MV2-Munim-Inc-research ch4lag/%s (mv2@munimtech.com)" % VERSION

QUERY = """prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
prefix prov: <http://www.w3.org/ns/prov#>
select ?dobj ?station ?stationId ?stationName ?samplingHeight ?timeStart ?timeEnd ?submTime ?fileName
where {
  VALUES ?spec {<%s>}
  ?dobj cpmeta:hasObjectSpec ?spec .
  FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
  ?dobj cpmeta:wasAcquiredBy ?acq .
  ?acq prov:wasAssociatedWith ?station .
  OPTIONAL {?station cpmeta:hasStationId ?stationId}
  OPTIONAL {?station cpmeta:hasName ?stationName}
  OPTIONAL {?acq cpmeta:hasSamplingHeight ?samplingHeight}
  OPTIONAL {?acq prov:startedAtTime ?timeStart}
  ?acq prov:endedAtTime ?timeEnd .
  ?dobj cpmeta:wasSubmittedBy/prov:endedAtTime ?submTime .
  OPTIONAL {?dobj cpmeta:hasName ?fileName}
}"""


def parse_time(s):
    """ISO 8601 text ('2023-07-02T23:00:00Z', '2023-07-03T10:15:17.325Z') -> aware UTC datetime."""
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def days(td):
    return round(td.total_seconds() / 86400.0, 3)


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    m = n // 2
    return xs[m] if n % 2 else (xs[m - 1] + xs[m]) / 2.0


def parse_sparql(body):
    """SPARQL results as JSON (application/sparql-results+json) or CSV -> list of {var: value}."""
    text = body.decode("utf-8") if isinstance(body, bytes) else body
    s = text.lstrip("﻿ \r\n\t")
    if s.startswith("{"):
        d = json.loads(s)
        names = d["head"]["vars"]
        return [{v: b[v]["value"] for v in names if v in b} for b in d["results"]["bindings"]]
    if s.startswith("<"):
        ns = "{http://www.w3.org/2005/sparql-results#}"
        root = ElementTree.fromstring(s)
        out = []
        for res in root.iter(ns + "result"):
            row = {}
            for b in res.findall(ns + "binding"):
                val = next(iter(b), None)
                if val is not None and val.text is not None:
                    row[b.get("name")] = val.text
            out.append(row)
        return out
    rows = list(csv.DictReader(io.StringIO(s)))
    return [{k: v for k, v in r.items() if k and v not in (None, "")} for r in rows]


def station_key(uri):
    return uri.rstrip("/").rsplit("/", 1)[-1]


def station_table(rows, now):
    """Per station: the freshest current object (by end of data) and lags relative to `now`."""
    st = {}
    for r in rows:
        key = station_key(r["station"])
        end = parse_time(r["timeEnd"])
        sub = parse_time(r["submTime"])
        e = st.setdefault(key, {"station": key, "station_id": r.get("stationId"),
                                "name": r.get("stationName"), "objects": 0, "heights": []})
        e["objects"] += 1
        h = r.get("samplingHeight")
        if h is not None and float(h) not in e["heights"]:
            e["heights"].append(float(h))
        if "time_end" not in e or end > parse_time(e["time_end"]):
            e["time_end"] = iso(end)
            e["subm_time"] = iso(sub)
            e["dobj"] = r["dobj"]
            e["file_name"] = r.get("fileName")
            e["height"] = float(h) if h is not None else None
    for e in st.values():
        e["heights"].sort()
        end = parse_time(e["time_end"])
        e["lag_days"] = days(now - end)
        e["publish_delay_days"] = days(parse_time(e["subm_time"]) - end)
        e["live"] = e["lag_days"] <= LIVE_DAYS
        e["stale"] = e["lag_days"] > STALE_DAYS
    return dict(sorted(st.items()))


def summarize(table):
    live = [e for e in table.values() if e["live"]]
    stale = [e for e in table.values() if e["stale"]]
    med_lag = median([e["lag_days"] for e in live])
    med_pub = median([e["publish_delay_days"] for e in live])
    return {"stations": len(table), "live": len(live), "stale": len(stale),
            "lagging_7_to_30_days": len(table) - len(live) - len(stale),
            "median_lag_live_days": None if med_lag is None else round(med_lag, 3),
            "median_publish_delay_live_days": None if med_pub is None else round(med_pub, 3)}


def pick_sample(table, n=SAMPLE_N):
    live = [e for e in table.values() if e["live"]]
    live.sort(key=lambda e: (-parse_time(e["time_end"]).timestamp(), e["station"]))
    return live[:n]


def _split(line, delim):
    return [t.strip() for t in (line.split(delim) if delim else line.split())]


def parse_atc(text):
    """Parse an ICOS ATC time series (semicolon text, '#' header lines; the column header may or
    may not start with '#'). Returns stats incl. the last time with a valid CH4 value."""
    cols = None
    delim = None
    out = {"rows": 0, "short": 0, "missing": 0, "valid": 0, "flags": {},
           "first_time": None, "last_time": None, "last_valid_time": None, "columns": None}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if cols is None:
            body = line.lstrip("#").strip()
            d = ";" if ";" in body else ("," if "," in body else None)
            toks = [t.lower() for t in _split(body, d)]
            if "ch4" in toks and ("year" in toks or "timestamp" in toks):
                cols, delim = toks, d
                out["columns"] = toks
            continue
        if line.startswith("#"):
            continue
        parts = _split(line, delim)
        if len(parts) < len(cols):
            out["short"] += 1
            continue
        row = dict(zip(cols, parts))
        out["rows"] += 1
        if "year" in row:
            t = datetime(int(row["year"]), int(row["month"]), int(row["day"]),
                         int(row.get("hour") or 0), int(row.get("minute") or 0), tzinfo=timezone.utc)
        else:
            t = parse_time(row["timestamp"])
        if out["first_time"] is None or t < parse_time(out["first_time"]):
            out["first_time"] = iso(t)
        if out["last_time"] is None or t > parse_time(out["last_time"]):
            out["last_time"] = iso(t)
        flag = row.get("flag", "")
        out["flags"][flag] = out["flags"].get(flag, 0) + 1
        try:
            v = float(row["ch4"])
        except ValueError:
            v = float("nan")
        if v != v or v <= 0:
            out["missing"] += 1
            continue
        out["valid"] += 1
        if out["last_valid_time"] is None or t > parse_time(out["last_valid_time"]):
            out["last_valid_time"] = iso(t)
    if cols is None:
        raise ValueError("no column header with a ch4 column found")
    return out


def read_payload(raw):
    """A zip (first member that looks like text data) or plain text -> (member name, text)."""
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names = [n for n in z.namelist() if not n.endswith("/")]
            if not names:
                raise ValueError("empty zip")
            names.sort(key=lambda n: (not n.lower().endswith((".csv", ".txt")), n))
            return names[0], z.read(names[0]).decode("utf-8", "replace")
    head = raw[:200].decode("utf-8", "replace")
    if head.lstrip().lower().startswith(("<!doctype", "<html")):
        raise ValueError("got an HTML page, not data: %r" % head[:120])
    return None, raw.decode("utf-8", "replace")


def grade(nrt_sum, samples):
    g = {"I1_at_least_25_live": nrt_sum["live"] >= 25,
         "I2_median_lag_live_le_2d": nrt_sum["median_lag_live_days"] is not None
         and nrt_sum["median_lag_live_days"] <= 2.0,
         "I3_at_least_5_stale": nrt_sum["stale"] >= 5,
         "I4_median_publish_delay_le_0.6d": nrt_sum["median_publish_delay_live_days"] is not None
         and nrt_sum["median_publish_delay_live_days"] <= 0.6}
    parsed = [s for s in samples if s.get("gap_days") is not None]
    g["sample_parsed"] = len(parsed)
    g["sample_within_gap"] = sum(1 for s in parsed if s["gap_days"] <= SAMPLE_GAP_DAYS)
    g["I5_sample_last_valid_within_2d"] = None if len(parsed) < 3 else g["sample_within_gap"] >= 3
    return g


NOAA_HREF = re.compile(r'href="(ch4_[a-z0-9]+_surface-insitu_[^"/]*DailyData\.txt)"')


def noaa_files(listing):
    seen = []
    for m in NOAA_HREF.finditer(listing):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def noaa_last_day(text):
    """Last day with a valid value (> -900, qcflag starting '.') in a NOAA GML DailyData file."""
    cols = None
    last = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            if body.lower().startswith("data_fields:"):
                cols = body.split(":", 1)[1].split()
            continue
        parts = line.split()
        if cols is None:
            if parts[0] == "site_code":
                cols = parts
            continue
        if parts == cols or len(parts) < len(cols):
            continue
        row = dict(zip(cols, parts))
        v = float(row["value"])
        if v != v or v <= -900.0 or row.get("qcflag", ".")[:1] != ".":
            continue
        d = "%04d-%02d-%02d" % (int(row["year"]), int(row["month"]), int(row["day"]))
        if last is None or d > last:
            last = d
    return last


def fetch(url, accept=None, tries=3):
    last = None
    for i in range(tries):
        try:
            h = {"User-Agent": USER_AGENT}
            if accept:
                h["Accept"] = accept
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read(), dict(r.headers)
        except Exception as e:  # retried, then reported
            last = e
            time.sleep(10 * (i + 1))
    raise last


def sparql(spec):
    url = SPARQL + "?" + urllib.parse.urlencode({"query": QUERY % spec})
    body, _ = fetch(url, accept="application/sparql-results+json, application/json;q=0.9, text/csv;q=0.5")
    return body


def to_markdown(rep):
    L = ["# ch4lag %s results" % rep["version"], "",
         "Census of how fresh public station CH4 data were at %s (query time)." % rep["icos"].get("queried_utc"),
         "Lag = query time minus the freshest end of data; live = lag <= %g days; stale = lag > %g days."
         % (LIVE_DAYS, STALE_DAYS), ""]
    for part in ("nrt", "l2"):
        p = rep["icos"].get(part)
        if not p:
            continue
        if "error" in p:
            L += ["## ICOS %s: error" % part.upper(), "", "`%s`" % p["error"], ""]
            continue
        L += ["## ICOS %s (%d current objects)" % (part.upper(), p["rows"]), "",
              "Summary: `%s`" % json.dumps(p["summary"]), "",
              "| station | id | name | heights (m) | freshest end of data | submitted | delay (d) | lag (d) |",
              "|---|---|---|---|---|---|---|---|"]
        for e in p["stations"].values():
            L.append("| %s | %s | %s | %s | %s | %s | %.3f | %.3f |" % (
                e["station"], e.get("station_id") or "", e.get("name") or "",
                ", ".join("%g" % h for h in e["heights"]), e["time_end"], e["subm_time"],
                e["publish_delay_days"], e["lag_days"]))
        L.append("")
    L += ["## NRT sample downloads", "", "| station | object | rows | valid | last valid | gap to metadata end (d) | flags | error |",
          "|---|---|---|---|---|---|---|---|"]
    for s in rep["icos"].get("samples", []):
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            s["station"], s["dobj"].rsplit("/", 1)[-1], s.get("rows", ""), s.get("valid", ""),
            s.get("last_valid_time") or "", "" if s.get("gap_days") is None else "%.3f" % s["gap_days"],
            json.dumps(s.get("flags", {})), s.get("error", "")))
    L += ["", "## NOAA GML in-situ CH4 DailyData files", "", "| file | last valid day | lag (d) | Last-Modified | error |",
          "|---|---|---|---|---|"]
    for f in rep["noaa"].get("files", []):
        L.append("| %s | %s | %s | %s | %s |" % (f["file"], f.get("last_day") or "", f.get("lag_days", ""),
                                               f.get("last_modified") or "", f.get("error", "")))
    if "error" in rep["noaa"]:
        L.append("| (directory) | | | | %s |" % rep["noaa"]["error"])
    L += ["", "Checks: `%s`" % json.dumps(rep["checks"])]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    rep = {"version": VERSION, "started_utc": iso(datetime.now(timezone.utc)),
           "config": {"live_days": LIVE_DAYS, "stale_days": STALE_DAYS, "sample_n": SAMPLE_N,
                      "sample_gap_days": SAMPLE_GAP_DAYS, "nrt_spec": NRT_SPEC, "l2_spec": L2_SPEC},
           "icos": {}, "noaa": {}}
    headers = []
    now = datetime.now(timezone.utc)
    rep["icos"]["queried_utc"] = iso(now)
    rep["icos"]["query"] = QUERY
    nrt_table = {}
    for part, spec in (("nrt", NRT_SPEC), ("l2", L2_SPEC)):
        p = {}
        try:
            body = sparql(spec)
            p["bytes"] = len(body)
            p["sha256"] = hashlib.sha256(body).hexdigest()
            rows = parse_sparql(body)
            p["rows"] = len(rows)
            table = station_table(rows, now)
            p["summary"] = summarize(table)
            p["stations"] = table
            if part == "nrt":
                nrt_table = table
        except Exception as ex:
            p["error"] = "%s: %s" % (type(ex).__name__, ex)
        rep["icos"][part] = p
        print("icos", part, json.dumps(p.get("summary") or p.get("error")))
    samples = []
    for e in pick_sample(nrt_table):
        s = {"station": e["station"], "dobj": e["dobj"], "time_end": e["time_end"]}
        try:
            raw, hdr = fetch(DOWNLOAD.format(h=e["dobj"].rsplit("/", 1)[-1]))
            s["bytes"] = len(raw)
            s["sha256"] = hashlib.sha256(raw).hexdigest()
            member, text = read_payload(raw)
            s["member"] = member
            headers.append("==== %s %s\n%s\n" % (e["station"], member, "\n".join(text.splitlines()[:60])))
            st = parse_atc(text)
            s.update(st)
            if st["last_valid_time"]:
                s["gap_days"] = days(parse_time(e["time_end"]) - parse_time(st["last_valid_time"]))
        except Exception as ex:
            s["error"] = "%s: %s" % (type(ex).__name__, ex)
        samples.append(s)
        print("sample", json.dumps({k: s.get(k) for k in ("station", "rows", "valid", "last_valid_time", "gap_days", "error")}))
        time.sleep(2)
    rep["icos"]["samples"] = samples
    try:
        listing, _ = fetch(NOAA_DIR)
        files = []
        for name in noaa_files(listing.decode("utf-8", "replace")):
            f = {"file": name}
            try:
                raw, hdr = fetch(NOAA_DIR + name)
                f["bytes"] = len(raw)
                f["sha256"] = hashlib.sha256(raw).hexdigest()
                f["last_modified"] = hdr.get("Last-Modified")
                f["last_day"] = noaa_last_day(raw.decode("utf-8", "replace"))
                if f["last_day"]:
                    end = datetime.strptime(f["last_day"], "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
                    f["lag_days"] = days(now - end)
            except Exception as ex:
                f["error"] = "%s: %s" % (type(ex).__name__, ex)
            files.append(f)
            print("noaa", json.dumps(f))
        rep["noaa"]["files"] = files
    except Exception as ex:
        rep["noaa"]["error"] = "%s: %s" % (type(ex).__name__, ex)
    nrt_sum = rep["icos"].get("nrt", {}).get("summary") or {"live": 0, "stale": 0,
                                                            "median_lag_live_days": None,
                                                            "median_publish_delay_live_days": None}
    rep["checks"] = grade(nrt_sum, samples)
    rep["finished_utc"] = iso(datetime.now(timezone.utc))
    with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    with open(os.path.join(a.out_dir, "RESULTS-ch4lag.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(rep))
    with open(os.path.join(a.out_dir, "header-samples.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(headers))
    print(json.dumps(rep["checks"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
