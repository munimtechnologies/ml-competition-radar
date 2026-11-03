# Pre-registration: ch4base-v1 (five-day-ahead daily methane baselines on NOAA in-situ records)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0, code Apache-2.0.
Written 2026-11-03, before the job ran and before any of its numbers were seen.

## Why

Zindi's Green Rising Methane Innovation Challenge ($10,000; opens 2026-11-13 12:00 UTC, closes
2027-02-14; open to all) asks for daily methane concentrations five days ahead at 59 stations
(ICOS, AGAGE, SNO, NOAA, JMA), scored against measurements made after submission. Its data, metric
and rules were still "coming soon" on 2026-11-03. Before they appear, this job measures how far five
simple forecasts get on NOAA GML's public daily in-situ CH4 records, so that any learned model in
MV2's entry has an honest floor to beat. It is preparation, not a discovery claim.

## Data

NOAA GML in-situ surface CH4 DailyData.txt for BRW, MKO, MLO and SMO
(https://gml.noaa.gov/aftp/data/greenhouse_gases/ch4/in-situ/surface/txt/, version 2026-08-11,
CC0 1.0; Petron et al. 2026, doi:10.15138/ve0c-be70). Values <= -900 are missing; a qcflag whose first
character is not "." is dropped. The job records each file's size and SHA-256.

## Methods (fixed in `ch4_baselines.py` 0.1.0)

Horizon 5 days. Origins t from 2021-01-01 to (last day in the file - 5); an origin is scored when the
target day has a value and every method below is defined. Each method uses only data on or before t.

- **P** persistence: the value on t, else t-1, else t-2.
- **M7** mean of the values in [t-6, t], at least 3.
- **C** seasonal fit: least squares on linear trend + 2 annual harmonics, fitted on the 4 calendar
  years before t's year (at least 500 values), evaluated at t+5.
- **S** C plus the latest anomaly (value used by P minus the fit at that day).
- **D** C plus phi times that anomaly; phi = lag-5 regression of the fit's residuals on themselves in
  the same 4 training years, clipped to [0, 1].

A site is included when it has at least 365 scored origins. Metrics per site: RMSE, MAE, bias, and
skill vs P = 1 - RMSE/RMSE(P).

## Predictions (graded automatically in results.json "checks", then by hand)

- **P1** At least 2 of the 4 sites are included.
- **P2** At every included site, D has a lower RMSE than P.
- **P3** At every included site, D's RMSE is at most C's.
- **P4** At every included site, D has the lowest RMSE of the five methods.
- **P5** At every included site, D's RMSE is at least 10% below P's.
- **P6** The mean phi over the fits that scored origins at included sites lies in [0.2, 0.8].

## Decision rule

- If P2 and P3 hold, D (seasonal fit + damped anomaly) is the floor every learned model in MV2's
  Zindi methane entry must beat on a held-out block before it is submitted.
- Otherwise the per-site best method in this study becomes that floor, and the failure is reported.
- If fewer than 2 sites are included, no floor is set from this study.

## Limits stated in advance

Four remote NOAA sites only; the contest's 59 stations include continental sites with far larger
day-to-day swings, where weather forecasts matter more. The daily files may average all hours, not
only background air, and recent values are preliminary. The contest's metric is not yet known
(its listing shows a placeholder), so RMSE and MAE are both reported. MV2 has no Zindi account yet,
so nothing is submitted.
