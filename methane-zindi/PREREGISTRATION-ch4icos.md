# Pre-registration: ch4icos-v1 (five-day methane baselines at ICOS towers, with data latency)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0, code Apache-2.0.
Written 2026-11-08, before the job ran and before any of its forecast numbers were seen.

## Why

Zindi's Green Rising Methane Innovation Challenge ($10,000; opens 2026-11-13 12:00 UTC; open to all)
asks for daily methane five days ahead at 59 stations (ICOS, AGAGE, SNO, NOAA, JMA), scored against
measurements made after submission. Its data, metric and rules were still "coming soon" on
2026-11-08 (the listing's metric field reads "f1", probably a placeholder). MV2's earlier studies:

- ch4base-v1 (NOAA BRW, MKO, MLO, SMO): seasonal fit + damped anomaly ("D") beat persistence.
- ch4lag-v1 (graded 2026-11-08): 40 of 41 ICOS stations had near-real-time CH4 metadata less than
  7 days old, median lag 0.93 days. But the job could not download the files: ICOS now requires a
  logged-in account (cpauthToken) for scripted downloads of data objects.

ICOS's public Zarr proxy (https://zarr.icos-cp.eu, ObsPack store, CC BY 4.0) answers anonymous
`/query` requests with hourly CH4 including the NRT tail, so a forecasting pipeline can use ICOS data
without an account. This study asks what that route is worth at the contest's horizon: on ICOS
towers, where daily methane swings with weather far more than at NOAA's remote sites, how much do
recent anomalies add over a seasonal fit five days ahead, and how much is lost when the newest usable
day is two days old? It is preparation for the entry. Copernicus CAMS publishes evaluations of its
model forecasts against ICOS stations; this is not a claim that station forecasting is new, only a
dated, open set of simple statistical baselines with latency.

## What was already seen before writing this (disclosed)

- `/variables?domain=atmosphere`: the ObsPack store has `icos-obspack.ch4.ch4` (ppb) with QC flags
  (U = NRT before manual QC, O = after manual QC; `apply_qc=true` keeps U and O).
- CBW207, 2026-11-01 to 2026-11-09: 120 hourly rows, flag U, newest hour 2026-11-05 23:30
  (seen about 2026-11-08 02:40 UTC, so about 2.1 days old; ICOS's own NRT object for Cabauw then
  ended 2026-11-06 23:00). Values about 2080-2146 ppb.
- CBW207, 2020-01-01: 22 hourly rows, flag O. MHD24 returned only a header (the inlet IDs use whole
  metres, e.g. MHD10).
- All inlets on 2026-11-05: at least 66 inlet IDs (my reader saw only the first 100,000 characters).
- `/openapi.json`: `max_rows` defaults to a server cap whose value is not stated; truncated
  selections keep the head and "the response says so". The job splits a truncated year into
  quarters, then months, and records it.
- No forecast, residual or phi value from ICOS data has been computed or seen.

## Method (fixed in `ch4_icos.py` 0.1.0)

1. Inlets: two one-day all-inlet queries (2025-06-01, and the day three days before the run); each
   site's highest inlet is used (site = the letters of the inlet ID).
2. Per inlet: hourly CH4 with `apply_qc=true` from 2021-01-01, one query per calendar year (split if
   truncated); UTC daily means of days with at least 12 valid hours. Proxy lag = run time minus the
   newest hour.
3. Origins t from 2025-01-01 to (last day - 5); scored when the target day t+5 has a value and all six
   methods are defined. P0 = value on t, else t-1, else t-2. M7 = mean of [t-6, t] (at least 3).
   C = least squares on trend + 2 annual harmonics over the 4 calendar years before t's year (at least
   500 days), at t+5. D0 = C + phi(gap) x anomaly of the P0 value, gap = days from it to t+5,
   phi(k) = lag-k regression of the fit's residuals on themselves in the training years, clipped to
   [0, 1]. P2 / D2 = the same with the newest usable day t-2 (value on t-2, t-3 or t-4).
4. A site is included with at least 200 scored origins. Per site: RMSE, MAE, bias; D0 gain =
   1 - RMSE(D0)/RMSE(C); latency cost = RMSE(D2)/RMSE(D0) - 1; mean phi(5) over the fits used.

## Predictions (graded automatically in results.json "checks", then by hand)

- **Q1** At least 25 sites are included.
- **Q2** D0 has a lower RMSE than P0 at no fewer than 80% of included sites.
- **Q3** C has a lower RMSE than P0 at more than half of included sites (five-day persistence of a
  noisy daily mean is worse than the seasonal fit).
- **Q4** The median D0 gain over C across included sites is at least 0 and below 0.10 (anomalies
  add a little, not much, at five days).
- **Q5** The median of the sites' mean phi(5) lies in [0.1, 0.5].
- **Q6** The median latency cost is below 0.05 (two days of latency costs under 5% RMSE).
- **F1** At least 25 sites' highest inlets have a proxy lag of at most 4 days at run time.

## Decision rule

- If Q4 and Q6 hold, the entry's floor at ICOS sites is D computed from whatever the proxy has (no
  ICOS account needed); effort goes to weather-driven features (the contest names NOAA weather
  forecasts), not to faster data.
- If Q4 fails high (median gain of 0.10 or more), recent data matter: refresh daily and look at the
  NRT objects (account) or contest-provided data for fresher values.
- If Q3 fails, persistence-type methods stay in the candidate set at those sites.
- Per-site best method from this study is reported; it does not replace a held-out check on the
  contest's own data and metric once they are published.

## Limits stated in advance

ICOS only (no AGAGE, SNO, NOAA or JMA sites); highest inlet only; UTC daily means of all hours,
which may not be how the contest defines "daily"; the contest's metric is unknown. Origins
2025-01-01 onward include values still flagged U (NRT) for recent months. Lags depend on when the job
runs. MV2 has no Zindi account yet, so nothing is submitted.
