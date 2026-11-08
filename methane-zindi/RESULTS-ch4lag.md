# ch4lag-v1 results, graded (how fresh is public station methane data?)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0.
Graded 2026-11-08 against [PREREGISTRATION-ch4lag.md](PREREGISTRATION-ch4lag.md) (public copy matched
the local one byte for byte before the analysis ran: `prereg_public.json`, match true).

Job ran 2026-11-07 21:16-21:19 UTC (query time 21:18:28Z), 16 offline tests passed first.
Machine output: [ch4lag-v1/RESULTS-ch4lag-auto.md](ch4lag-v1/RESULTS-ch4lag-auto.md) and
[ch4lag-v1/results.json](ch4lag-v1/results.json).

## Grades: 3 held, 1 failed, 1 ungraded; C1 waits for the contest data

| # | prediction | result | grade |
|---|---|---|---|
| I1 | at least 25 ICOS stations live (NRT CH4 lag <= 7 d) | 40 of 41 live | **held** |
| I2 | median lag over live stations <= 2.0 d | 0.929 d | **held** |
| I3 | at least 5 stations with a current NRT object are stale (> 30 d) | 1 (Station Nord, SNO: data end 2026-09-29, lag 38.9 d) | **failed** |
| I4 | median publish delay over live stations <= 0.6 d | 0.507 d (objects for day D published about 11:07-11:13 UTC on D+1) | **held** |
| I5 | at least 3 of the parsed sample downloads end within 2 d of the metadata end | 0 of 5 downloads parsed | **ungraded** |
| C1 | fewer than half of the contest's 59 stations have data within 7 d of opening | contest data not published yet (opens 2026-11-13) | pending |

ICOS Level 2 (the quality-controlled release): all 41 stations end 2026-03-31, released 2026-07-01
(lag 220.9 d at query time). NOAA GML in-situ DailyData files (BRW, MKO, MLO, SMO; Last-Modified
2026-08-11) end 2025-12-24 (BRW) and 2025-12-31 (others), 311-318 days old.

## Why I5 is ungraded

All five sample downloads returned an HTML page, not data. The job used ICOS's licence-accept link
without a login. ICOS's data service README (github.com/ICOS-Carbon-Portal/data) now describes
scripted downloads of data objects (and of its `/csv/` endpoint) as needing a logged-in account that
has accepted the data licence (`cpauthToken` cookie). A sealed job with no secrets cannot do that.
This is a fact about access, not about the data.

## Checked by hand (2026-11-08, meta.icos-cp.eu landing pages)

- El Arenosillo (ARN, 10 m, object `jgkmMUWQG_jKXOojbN6nONy9`): coverage 2026-04-01 00:00 to
  2026-11-06 23:00 UTC, 5,280 rows, published 2026-11-07 11:07:22 UTC. 5,280 = 220 days x 24 hours, so
  the object has one row per hour up to its stated end. Matches the census.
- Ridge Hill (RGL, 90 m, object `Xn5zkImJ5ki2HPel1SeHoXmg`): coverage ends 2026-11-07 **12:00** UTC,
  5,293 rows (= 5,280 + 13 hours of 7 November), but the object was produced and published at
  11:11 UTC that day. Its last row is stamped 49 minutes after the file was made, so it cannot be a
  measurement. The census's negative publish delays for RGL and Westerland (WES) come from this:
  for some stations the metadata end of data is not the last measured hour. That is exactly what I5
  was meant to test, and it remains open.

## What it means for the entry (decision rule)

- I1 and I2 held: ICOS NRT metadata are almost all less than a day old, so the entry's daily
  pipeline should refresh ICOS data each day and use the damped-anomaly forecast where a station's
  newest value is at most 7 days old.
- The I5 failure mode is real (RGL, WES), so the pipeline reads the last valid value from the data
  itself, never the metadata end.
- New route found while grading: ICOS's public Zarr proxy (https://zarr.icos-cp.eu, ObsPack store,
  CC BY 4.0) serves hourly CH4 with the NRT tail anonymously through `/query`. For Cabauw on
  2026-11-08 about 02:40 UTC its newest hour was 2026-11-05 23:30, about a day behind ICOS's own NRT
  object. The next study, [PREREGISTRATION-ch4icos.md](PREREGISTRATION-ch4icos.md), uses that
  route to measure what five-day forecasts gain from recent data and what two days of latency cost.

## Limits

One query time. ICOS NRT is Level 1 (automated QC only). Public data only: the organisers may have
faster feeds. NOAA, JMA and AGAGE facts in the pre-registration were hand-read, not re-measured here
(except NOAA's files).

Data: ICOS Carbon Portal metadata (CC BY 4.0); NOAA GML in-situ CH4 (CC0 1.0).
