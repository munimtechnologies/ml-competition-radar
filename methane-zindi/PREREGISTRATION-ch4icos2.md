# Pre-registration: ch4icos2-v1 (can the five-day seasonal floor's bias be fixed?)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0, code Apache-2.0.
Written 2026-11-08, before the job ran and before any of its numbers were seen.

## Why

ch4icos-v1 ([RESULTS-ch4icos.md](RESULTS-ch4icos.md), 7 of 7 predictions held) set the entry's floor at
ICOS towers for Zindi's Green Rising Methane Innovation Challenge (daily CH4 five days ahead at 59
stations; opens 2026-11-13). After grading, an unregistered look showed that its seasonal fit C was
biased high at 52 of 54 sites (median +7.5 ppb, origins 2025-01-01 to 2026-11-01). The bias was 59%
of C's squared error at Réunion, 41% at Station Nord and 4% at Cabauw. The likely cause is the fit
design. C fits a straight trend plus two annual harmonics on the four calendar years before the
origin's year and extrapolates up to a year. Global CH4 growth slowed to 8.0 ppb in 2024 and 4.8 ppb
in 2025, after about 17 in 2021 (NOAA GML), so the line overshoots. This study tests two fixes on
the same origins. It still runs before the contest has published its metric, which breaks a rule
MV2's agents set themselves (no more baseline variants until the metric is known). The reason: a
systematic bias of this size hurts any error metric.

Prior art: refitting or re-anchoring a climatology to recent data is standard forecasting practice,
and Copernicus CAMS evaluates model forecasts at ICOS stations. What's new here is only a dated,
open measurement for these sites and this horizon, with the predictions fixed in advance.

## What was already seen (disclosed)

All of ch4icos-v1's per-site output: RMSE, MAE and bias of P0, M7, C, D0, P2 and D2, and phi(5),
from data queried 2026-11-08 12:07 UTC. No rolling fit, level-anchored forecast or result of this
code has been computed or seen.

## Method (fixed in `ch4_icos2.py` 0.2.0)

The download, the daily means, C, D0 and D2 come unchanged from `ch4_icos.py` 0.1.0 at commit
481e0091660f6341bac0fd57fde219b836fd1e51, the code ch4icos-v1 ran. The job fetches it from that
pinned commit. The data are re-queried at run time, so recent days may differ a little from v1.

- **Cr**: the same trend + 2 annual harmonics, refitted for each calendar month on the 1,461 days
  ending (exclusive) 2 days before the first day of the origin's month. It never uses data newer than
  t - 2, and at least 500 daily values are required.
- **Dr**: Cr + phi_r(gap) x (P0 value - Cr at the P0 day), where phi_r is the lag regression of
  the rolling fit's residuals, clipped to [0, 1], as for D0.
- **Dr2**: Dr computed from the P2 value (newest usable day t - 2).
- **L30**: C + the mean of (value - C) over the 30 days ending on the P0 day, with at least 10 values.
- An origin is scored only if all of C, D0, D2, Cr, Dr, Dr2 and L30 are defined, so the comparisons
  are paired. A site is included with at least 200 scored origins. Gains are 1 - RMSE(new)/RMSE(old).
  "Clean sites" are the 10 included sites with the lowest RMSE of C.

## Predictions (graded automatically in results.json "checks", then by hand)

- **R1** The median (over included sites) of Cr's bias is less than half of the median of C's bias.
- **R2** Cr has a lower RMSE than C at no fewer than 75% of included sites.
- **R3** Dr has a lower RMSE than D0 at no fewer than 75% of included sites.
- **R4** The median gain of Dr over D0 is at least 0.02.
- **R5** Over the 10 clean sites, the median gain of Dr over D0 is at least 0.05.
- **R6** L30 has a lower RMSE than C at more than half of included sites.
- **R7** The median latency cost RMSE(Dr2)/RMSE(Dr) - 1 is below 0.05.

Context check, not a prediction, because it was already seen in v1: median C bias of at least +5 ppb
(`context_B0`).

## Decision rule

- If R3 and R4 hold, the entry's floor at ICOS sites becomes Dr, refitted on the newest data each
  day in production.
- If R1 fails, the straight trend itself is the problem, not just its age; the next step is a damped
  or shorter-window trend, which would need its own pre-registration.
- If R5 holds and R4 fails, the fix matters mainly at clean sites, and per-site choice is made on
  held-out contest data.
- L30 stays a per-site candidate wherever it beats Dr; the per-site table is published either way.

## Limits stated in advance

ICOS only; highest inlet only; UTC daily means of all hours; the contest's metric and "daily"
definition are unknown; origins from 2025 include near-real-time values flagged U; one query time.
MV2 has no Zindi account yet, so nothing is submitted.
