# Pre-registration: ch4lag-v1 (how fresh is public station methane data?)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0, code Apache-2.0.
Written 2026-11-07, before the job ran and before any of its census numbers were seen.

## Why

Zindi's Green Rising Methane Innovation Challenge ($10,000; opens 2026-11-13 12:00 UTC, closes
2027-02-14; open to all) asks for daily methane five days ahead at 59 stations whose data come from
ICOS, AGAGE, SNO, NOAA and JMA, scored against measurements made after submission. A five-day
forecast can only use recent anomalies (MV2's ch4base study: seasonal fit + damped anomaly beat
persistence) if a station's latest measurements are available when the forecast is made. This job
measures, station by station, how old the newest public CH4 data are on the day it runs. It is
preparation for the entry, plus a dated public census; it is not a claim that nobody knows ICOS
publishes near-real-time data (ICOS documents that, see below).

## What was already seen before writing this (disclosed)

- ICOS's product page says its Level 1 NRT CH4 series are "generated within 24 hours after
  measurement"; Level 2 releases come 6-12 months later
  (https://www.icos-cp.eu/data-products/ATM_NRT_CO2_CH4).
- Three single ICOS NRT CH4 objects found by web search (Zeppelin 2025-08, Birkenes and Pallas
  2026-07) were each produced about 10:10 UTC the day after their 23:00 UTC end of data.
- A two-row syntax test of the query below on the CO2 NRT spec returned two Jungfraujoch objects
  (ends 2023-07-02 and 2025-06-02), so non-deprecated objects include ended series.
- Hand-read facts (not part of the graded census; reported alongside it):
  - NOAA GML in-situ CH4 DailyData files (BRW, MKO, MLO, SMO; directory dated 2026-08-11) end on
    2025-12-31 (MV2's ch4base-v1 run, 2026-11-03).
  - JMA Minamitorishima in-situ CH4 at WDCGG (https://gaw.kishou.go.jp/search/file/0001-2029-1002-01-01-9999)
    ends 2026-07-31, version 2026-09-07, updated 2026-09-16. JMA says Yonagunijima stopped in March 2024.
  - AGAGE in-situ data come as dated releases (versions 20250123 and 20260716 are listed by the
    University of Bristol research portal); no public near-real-time AGAGE CH4 feed was found.
  - SNO: not checked.

## Method (fixed in `ch4_latency.py` 0.1.0)

1. One SPARQL query to https://meta.icos-cp.eu/sparql per spec: every current (no newer version)
   object of "ICOS ATC NRT CH4 growing time series" (atcCh4NrtGrowingDataObject) and of
   "ICOS ATC CH4 Release" (atcCh4L2DataObject), with station, sampling height, end of data and
   submission time.
2. Per station (all heights pooled): the object with the latest end of data. Lag = query time minus
   that end; publish delay = its submission time minus that end. Live = lag <= 7 days;
   stale = lag > 30 days; lagging = in between.
3. The newest NRT objects of the 5 live stations with the latest end of data (ties by station code)
   are downloaded through ICOS's public licence-accept link and parsed; gap = metadata end of data
   minus the last hour with a valid (positive, non-missing) CH4 value.
4. NOAA GML in-situ CH4 DailyData files: last day with a valid value (value > -900, qcflag starting
   ".").

## Predictions (graded automatically in results.json "checks", then by hand)

- **I1** At least 25 ICOS stations are live (NRT CH4 lag <= 7 days).
- **I2** The median lag over live stations is at most 2.0 days.
- **I3** At least 5 ICOS stations with a current NRT CH4 object are stale (lag > 30 days).
- **I4** The median publish delay over live stations is at most 0.6 days.
- **I5** Of the downloaded samples that parse (needs at least 3, else ungraded), at least 3 have
  their last valid CH4 hour within 2.0 days of the metadata end of data.
- **C1** (graded by hand once the contest data open, ungradable if they carry no dates per station):
  fewer than half of the contest's 59 stations have a measurement dated within 7 days of the
  contest's opening (2026-11-13) in the data Zindi provides.

## Decision rule

- If I1 and I2 hold, the entry's daily pipeline will (if the rules allow external public data)
  refresh ICOS NRT data each day, and use the damped-anomaly forecast only where a station's newest
  measurement is at most 7 days old; elsewhere it falls back to the seasonal fit, since an anomaly
  months old carries no five-day signal.
- If I5 fails, the metadata end of data is not trusted as the data's real end; the pipeline reads the
  last valid value from the files themselves.
- C1 tells us whether the contest is mostly a live forecasting problem (C1 fails) or mostly a
  seasonal one for stations without recent data (C1 holds).

## Limits stated in advance

Public data only; the organisers may receive faster private feeds. ICOS NRT is Level 1 with automated
quality control only. One query time; lags shift by up to a day depending on when the job runs
relative to ICOS's ~10:10 UTC daily publication. NOAA, JMA and AGAGE facts are hand-read or from an
earlier run, not re-measured by this job except NOAA's files.
