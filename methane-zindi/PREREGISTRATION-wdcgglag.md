# Pre-registration: wdcgglag-v1 — how stale is each public CH4 record on WMO's WDCGG?

MV2 of Munim, Inc. Written 2026-11-08 (about 16:00 UTC) by AI agents working in his name, before
the job that tests it ran. Code: `wdcgg_lag.py` 0.1.0 (standard library only, Apache-2.0), tests
`test_wdcgg_lag.py`. Text CC BY 4.0.

## Why

Zindi's Green Rising Methane Innovation Challenge (USD 10,000; opens 2026-11-13 12:00 UTC; closes
2027-02-14) asks for five-day-ahead forecasts of daily CH4 at 59 stations from the ICOS, AGAGE,
SNO, NOAA and JMA networks, scored against measurements made after submission. Its data, rules and
metric were still "coming soon" on 2026-11-08. A live forecast can only use inputs that are already
public, so it matters how far behind real time each network's public data are. Our earlier census
(`RESULTS-ch4lag.md`) found ICOS near-real-time data about one day behind and NOAA's own public
in-situ daily files about 10 months behind. WMO's World Data Centre for Greenhouse Gases (WDCGG,
https://gaw.kishou.go.jp) is the one archive that carries all of these networks, so this job
measures, for every CH4 dataset its "latest" listing links, the last date its public files cover.

## What the job does

1. Fetch https://gaw.kishou.go.jp/search/gas_species/ch4/latest and collect every linked
   `/search/file/<id>` page (one per dataset).
2. Fetch each page (one request per second, identifying User-Agent), pair each file name
   (`ch4_<stn><no>_<platform>-<type>_<contributor>_..._<resolution>`) with its period, and take the
   dataset's end as the latest end over its non-meteorological files. Open-ended metadata spans
   ending in 9999 are ignored.
3. Lag = days from that end date to the run date (UTC). Network = WDCGG contributor number
   (1 JMA, 2 NOAA, 4 AGAGE, 162 ICOS), else the contributor named on the page.

## Gates (if either fails, P1-P6 are reported but ungraded)

- **G1** The listing links at least 300 file ids.
- **G2** At least 95% of listed ids are fetched and parsed into a dated row.

## Predictions

- **P1** At least 13 ICOS surface in-situ datasets are listed, and all but at most 2 of them end
  between 2026-08-01 and 2026-08-31.
- **P2** At least 5 AGAGE in-situ datasets end after 2024-01-01, and every one of those ends between
  2025-10-01 and 2025-10-31.
- **P3** At least 4 NOAA surface in-situ datasets are listed, and every one ends between 2025-12-01
  and 2025-12-31.
- **P4** No surface in-situ CH4 dataset from any contributor ends after 2026-09-30 (so none is
  fresher than about 39 days on the run date).
- **P5** Over surface in-situ datasets ending on or after 2025-01-01, the median lag is more than 120
  days.
- **P6** At least 90% of ICOS tower in-situ datasets end between 2026-08-01 and 2026-08-31.

## What we saw before writing this (disclosed)

All read through a web page reader on 2026-11-08, not by this code:
- The listing page itself, including each row's version and submission date (ICOS rows version
  2026-08-27-0001 dated 2026-09-24; JMA 2026-09-07; AGAGE 2026-08-10; NOAA 2026-08-12; ECCC
  2026-08-11; KMA 2026-08-18) and a hand count of about 337 rows, 99 of them surface in-situ.
- Eight file pages: JMA Minamitorishima and Ryori end 2026-07-31 (Yonagunijima ended March 2024);
  ICOS La Réunion ends 2026-08-23; AGAGE Ragged Point (Picarro) 2025-10-26, Ragged Point (GC-MD)
  2017-02-15, Mace Head (GC-MD) 2025-10-25, Cape Grim (Picarro) 2025-10-26; NOAA Mauna Loa
  2025-12-31.
- From our ch4lag census: NOAA's own in-situ daily files end 2025-12-24 (BRW) and 2025-12-31 (MKO,
  MLO, SMO).
So P3 is largely known in advance, and P2 is half-known (3 of its roughly 6 active datasets were
seen); they are kept as checks of the parser. P1, P4, P5 and P6 cover datasets not opened by hand.

## How it will be used

The job does not change any forecast. If P4 holds, the contest notes will say that WDCGG is a
history source only, and that live inputs must come from ICOS near-real-time data (or whatever feed
Zindi provides). Stations whose public data end months ago can then only be forecast from history
and weather forecasts unless Zindi supplies recent values. Whatever happens, the full per-dataset
table is published.

Limits: WDCGG's file periods describe its copies, not each network's own servers (ICOS
near-real-time and AGAGE's own releases can be newer or older); "latest" lists one version per
dataset; a dataset's period end is when its record stops, which for a closed station is not a lag.
