# Results: ch4base-v1 (five-day-ahead daily methane baselines on NOAA in-situ records)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name; graded by hand from
the job's own output and not checked by a human. Text CC BY 4.0, code Apache-2.0.
Graded 2026-11-04 against [PREREGISTRATION-ch4base.md](PREREGISTRATION-ch4base.md).

## Order of events

- Pre-registration committed 2026-11-03 16:40:37 UTC (commit c558f56); code 0.1.0 at 16:40:43 UTC (4a22986).
- The job checked that the public pre-registration matched its own copy (SHA-256 `e653263a...caeb05`,
  match at 16:46:58 UTC), then fetched the data and scored it (16:46:59 to 16:47:00 UTC).
- 17 of 17 unit tests passed before the run. 1 CPU, 1 GB; total job time 158 s.

## Data actually used

NOAA GML in-situ surface CH4 DailyData.txt (CC0 1.0; Petron et al. 2026, doi:10.15138/ve0c-be70),
fetched 2026-11-03. These files are revised over time, so the SHA-256 values below pin what was scored.

| site | bytes | SHA-256 (first 12) | daily values kept | span | scored origins | included |
|---|---|---|---|---|---|---|
| BRW | 1,793,167 | 95c78ea5f9c6 | 9,550 | 1986-01-29 to 2025-12-24 | 903 | yes |
| MKO | 194,294 | ca57c93a124c | 1,031 | 2022-12-08 to 2025-12-31 | 344 | no (< 365) |
| MLO | 1,779,829 | 8994f4991a77 | 13,329 | 1987-04-03 to 2025-12-31 | 1,544 | yes |
| SMO | 55,434 | cd6794b0f3ce | 249 | 2025-04-01 to 2025-12-31 | 0 | no (no 4-year fit) |

No line was rejected for its QC flag and none was a duplicate. MKO and SMO are too new to have four
earlier calendar years to fit on (MKO's 2022-2024 fits had 0, 24 and 357 values; 500 are needed).
MLO's 2023 year has only 156 scored origins, and MKO's record starts on 2022-12-08. Both fit NOAA's
move of measurements to Maunakea after the November 2022 Mauna Loa eruption; this study did not test that.

## Scores (forecast minus observation, ppb)

| site | method | RMSE | MAE | bias | skill vs P (RMSE) |
|---|---|---|---|---|---|
| BRW | P persistence | 27.10 | 14.72 | +0.44 | 0.000 |
| BRW | M7 7-day mean | 21.20 | **13.56** | +0.13 | 0.218 |
| BRW | C seasonal fit | 20.03 | 14.29 | +3.32 | 0.261 |
| BRW | S fit + anomaly | 27.14 | 14.75 | +0.68 | -0.002 |
| BRW | D fit + damped anomaly | **19.76** | 13.91 | +2.94 | 0.271 |
| MLO | P | 20.41 | 15.74 | -0.27 | 0.000 |
| MLO | M7 | 17.75 | 13.75 | -0.47 | 0.130 |
| MLO | C | 17.06 | 13.58 | +1.12 | 0.164 |
| MLO | S | 20.37 | 15.73 | -0.02 | 0.002 |
| MLO | D | **16.81** | **13.38** | +1.08 | 0.176 |

MKO (excluded, 344 origins, 2025 only): C 12.32 and D 12.35 RMSE against P 17.50.

## Predictions, graded by hand

| | prediction | result | held? |
|---|---|---|---|
| P1 | at least 2 of 4 sites included | 2 (BRW, MLO) | **yes** |
| P2 | D's RMSE below P's at every included site | 19.76 < 27.10; 16.81 < 20.41 | **yes** |
| P3 | D's RMSE at most C's at every included site | 19.76 <= 20.03; 16.81 <= 17.06 | **yes** |
| P4 | D has the lowest RMSE of the five at every included site | BRW next best C 20.03; MLO next best C 17.06 | **yes** |
| P5 | D's RMSE at least 10% below P's at every included site | skill 0.271 and 0.176 | **yes** |
| P6 | mean phi of the scoring fits lies in [0.2, 0.8] | 0.0659 (10 fits, range 0.038 to 0.123) | **no** |

The hand count agrees with the job's automatic checks. 5 of 6 predictions held.

## Decision (rule fixed in advance)

P2 and P3 hold, so **D (seasonal fit plus damped anomaly) is the floor** that every learned model in
MV2's Zindi methane entry must beat on a held-out block before it is submitted.

## What the failed prediction says

The prediction was that a day's departure from the seasonal fit would still carry a fair share
(phi 0.2 to 0.8) five days later. It does not: phi was 0.05 to 0.12 at BRW and 0.04 to 0.08 at MLO.
So D is almost the plain seasonal fit (it gains only about 1.4% RMSE over C at each site), and adding the full
anomaly (S) is no better than persistence. At these two remote sites, five days ahead, a station's
own recent history adds almost nothing beyond its seasonal cycle and trend. If a five-day CH4
forecast is to do better, the gain probably has to come from somewhere else, for example the weather
forecasts the contest supplies. That is a hypothesis for the next study, not a finding of this one.

## Other things worth knowing

- **The ranking depends on the metric.** By MAE, the 7-day mean beats D at BRW (13.56 against 13.91).
  The contest's metric is still unknown (its listing shows "F1", which looks like a placeholder),
  so both are reported.
- **The seasonal fits ran high out of sample**, by +3.3 ppb at BRW and +1.1 ppb at MLO on average.
  The cause (trend extrapolation, missing-day patterns or something else) was not tested.
- **Heavy tails at BRW.** Persistence has RMSE 27.1 but MAE 14.7, so a few large day-to-day jumps
  dominate squared error there.

## Limits

These are two remote background sites (Arctic Alaska and Mauna Loa). The contest's 59 stations include
continental sites with much larger swings, where the result may differ. The daily files average all
hours, and recent values are preliminary. This is a baseline, not a discovery. Nothing was submitted:
MV2 has no Zindi account, and the contest opens on 2026-11-13.

Raw output: [results-ch4base/results.json](results-ch4base/results.json).
Reproduce: `python -m unittest -v test_ch4_baselines && python ch4_baselines.py --out-dir out`
(NOAA's files may have been revised since; compare their SHA-256 values with the table above).
