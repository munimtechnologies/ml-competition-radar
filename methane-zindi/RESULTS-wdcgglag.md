# wdcgglag-v1 results, graded (how far behind today does each public CH4 dataset on WMO's WDCGG end?)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0.
Graded 2026-11-08 (about 23:00 UTC) against [PREREGISTRATION-wdcgglag.md](PREREGISTRATION-wdcgglag.md).
The public copy matched the local one byte for byte before the census ran
(`wdcgglag-v1/prereg_public.json`: match true, sha256 8de8273f..., seen 2026-11-08 19:46:12 UTC).

The job ran on 2026-11-08 from 19:44 to 20:16 UTC on 1 CPU and 0.03 GB of memory, after its offline
unit tests passed. It fetched WDCGG's "latest" CH4 listing and all 337 file pages it links, one
request per second. Machine output: [wdcgglag-v1/RESULTS-wdcgglag-auto.md](wdcgglag-v1/RESULTS-wdcgglag-auto.md)
(table by network and platform, freshest datasets) and [wdcgglag-v1/results.json](wdcgglag-v1/results.json)
(one row per dataset, with start, end, lag and URL). Lag = days from a dataset's last date to 2026-11-08.

## Grades: both gates and 5 of 6 predictions held

| # | prediction | result | grade |
|---|---|---|---|
| G1 | listing links at least 300 file ids | 337 | **held** |
| G2 | at least 95% of ids fetched and parsed into a dated row | 337 of 337 (100%), 0 fetch errors | **held** |
| P1 | at least 13 ICOS surface in-situ datasets; all but at most 2 end in Aug 2026 | 15 datasets, all 15 end in Aug 2026 (newest 2026-08-24) | **held** |
| P2 | at least 5 AGAGE in-situ datasets end after 2024-01-01, all in Oct 2025 | 7 datasets; 6 end 2025-10-25 to 10-31, but Trinidad Head (Picarro) ends 2026-01-01 | **failed** |
| P3 | at least 4 NOAA surface in-situ datasets, all end in Dec 2025 | 4 of 4 end 2025-12 | **held** |
| P4 | no surface in-situ dataset from any contributor ends after 2026-09-30 | 0 of 99; the newest is ICOS 2026-08-24 (76 days) | **held** |
| P5 | median lag of surface in-situ datasets ending 2025 or later > 120 days | 312 days (60 datasets) | **held** |
| P6 | at least 90% of ICOS tower in-situ datasets end in Aug 2026 | 77 of 84 (91.7%) | **held** |

P2 failed on one dataset. AGAGE's Trinidad Head Picarro record (`0004-4022-1002-01-01-2024`) runs to
2026-01-01 00:00, so it covers all of 2025. The six other active AGAGE records end 2025-10-25 to
2025-10-31: Mace Head, Ragged Point (Barbados, Picarro), Cape Grim (three records) and Trinidad Head
(GC-MD). The prediction was too narrow, and the parser was right (checked by hand below).

The seven ICOS tower datasets outside August 2026 are Svartberget (SVB, three inlets, 2026-07-28),
Ispra (IPR, two inlets, 2026-07-24), Saclay (STE, 2026-03-16) and an old Hegyhátsál record (HUN, which
ended 2014-10-09; a newer HUN record ends 2026-08-24).

## How fresh each network is on WDCGG (surface and tower in-situ, records ending 2025 or later)

| network | datasets | newest end | median lag (days) |
|---|---|---|---|
| ICOS (towers) | 83 | 2026-08-25 | 77 |
| ICOS (surface) | 15 | 2026-08-24 | 76 |
| JMA | 2 (Minamitorishima, Ryori) | 2026-07-31 | 100 |
| NIES | 2 | 2026-03-31 | 222 |
| NOAA | 4 | 2025-12-31 | 312 |
| ECCC | 10 | 2025-12-31 | 312 |
| AGAGE | 7 | 2026-01-01 | 378 |

Most other contributors' active records also end on 2025-12-31 (312 days). Full table:
[wdcgglag-v1/RESULTS-wdcgglag-auto.md](wdcgglag-v1/RESULTS-wdcgglag-auto.md).

## Checked by hand

- **Trinidad Head, AGAGE Picarro** (the P2 failure), read through a web page reader after the run:
  both files on the page (`..._monthly`, `..._event`) end "2026-01-01 00:00:00". Version
  2026-08-10-0016, last updated 2026-09-01. This matches the parsed row.
- **Ridge Hill, ICOS 90 m tower** (the freshest dataset): hourly ends 2026-08-25 12:00, daily
  2026-08-25 and monthly 2026-08-01. Version 2026-08-27-0001, last updated 2026-09-24. This matches
  the parsed end of 2026-08-25.
- **Tacolneston, UNIVBRIS tower**, from the page the job saved (`wdcgglag-v1` pages/): the four
  file periods end 2026-03-31 23:00, 2026-03-31, 2026-03-01 and 2026-03-31 23:40. The parsed end is
  2026-03-31 (lag 222), which is right.
- **Arithmetic.** Mace Head ends 2025-10-25: 365 days to 2026-10-25 plus 14 is 379, as printed.

## What it means for the methane contest

- WDCGG is a **history** source. No network's copy there is less than 75 days old, so it cannot
  supply the last few days a five-day forecast needs.
- The only live public input found so far is **ICOS near-real-time data** (median 0.93 days behind,
  `RESULTS-ch4lag.md`), read through the anonymous ICOS Zarr proxy.
- For AGAGE, NOAA and JMA stations, the newest public values are 3 to 12 months old: JMA's on WDCGG
  end 2026-07-31, NOAA's own files 2025-12-31, and AGAGE's on WDCGG 2025-10-25 to 2026-01-01. Ragged
  Point, Barbados (the sponsor's country) ends 2025-10-26 on WDCGG. Unless Zindi supplies recent
  values, a live forecast at these stations can only use history, a trend and weather forecasts.
- **Not checked:** AGAGE's own data portal (agage.mit.edu) now redirects to a NASA Langley server
  that our page reader cannot open, so we could not see whether AGAGE has a newer public release
  than WDCGG's copy.

## Limits

One snapshot (2026-11-08). WDCGG's periods describe its own copies; each network's own servers can
be newer. WDCGG's home page (read the same day) mentions no near-real-time or provisional data
section; its only "preliminary" item is a set of summary figures for a forthcoming report. "Latest" lists one version per dataset. The end of a closed station's record is not a lag.
Network = WDCGG contributor, so ICOS data submitted by a university under its own name count under
that university (for example UNIVBRIS, NPL). Nothing has been submitted to the contest: MV2 has no
Zindi account yet.

Data: WMO GAW World Data Centre for Greenhouse Gases (https://gaw.kishou.go.jp), operated by the
Japan Meteorological Agency; listing metadata only, no measurement values were downloaded.
