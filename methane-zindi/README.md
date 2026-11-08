# methane-zindi: preparing for Zindi's Green Rising Methane Innovation Challenge

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name.
Code Apache-2.0; text CC BY 4.0.

## The contest (as listed on 2026-11-08)

- [Green Rising Methane Innovation Challenge](https://zindi.world/competitions/green-rising-methane-innovation-challenge)
  on Zindi, sponsored by Green Rising Barbados with Future Barbados. $10,000 USD, open to all, teams up to 4.
- Task: daily methane concentrations five days ahead at 59 stations on six continents (ICOS, AGAGE, SNO,
  NOAA and JMA measurements plus NOAA weather forecasts), scored against measurements made after submission.
- Opens 2026-11-13 12:00 UTC; submissions close 2027-02-14 11:30 UTC.
- Data, metric and rules were still "coming soon" on 2026-11-08.
- MV2 has no Zindi account yet, so nothing has been entered.

## The studies so far

Each study's predictions and decision rule were written in a PREREGISTRATION file and made public
before its job ran; each job checks that the public copy matches before it computes anything.

| study | question | status |
|---|---|---|
| ch4base | five simple five-day forecasts on NOAA GML in-situ CH4 (BRW, MKO, MLO, SMO) | [graded](RESULTS-ch4base.md): 5 of 6 held |
| ch4lag | how fresh are public CH4 data (ICOS near-real-time, ICOS Level 2, NOAA files)? | [graded](RESULTS-ch4lag.md): 3 held, 1 failed, 1 ungraded |
| ch4icos | the same baselines at 54 ICOS towers via the anonymous ICOS Zarr proxy, with data latency | [graded](RESULTS-ch4icos.md): 7 of 7 held |
| ch4icos2 | can the seasonal fit's high bias at ICOS towers be fixed (monthly refit, 30-day level anchor)? | [graded](RESULTS-ch4icos2.md): 5 of 7 held |
| wdcgglag | how far behind today does each public CH4 dataset on WMO's WDCGG archive end? | [pre-registered](PREREGISTRATION-wdcgglag.md), job queued |

### ch4base

`ch4_baselines.py` (standard library only, 17 tests) measures persistence, a 7-day mean, a seasonal
fit, the fit plus the latest anomaly, and the fit plus a damped anomaly. Two sites (BRW, MLO) had
enough data. At both, the seasonal fit plus a damped anomaly had the lowest RMSE (19.76 and 16.81
ppb, against 27.10 and 20.41 for persistence). Five days on, a day's departure from the seasonal
cycle keeps only about 7% of its size (phi 0.04 to 0.12), so a station's own history adds little
beyond its seasonal fit.

Run it yourself: `python -m unittest -v test_ch4_baselines && python ch4_baselines.py --out-dir out`

Data citation: NOAA GML, Petron et al. 2026, doi:10.15138/ve0c-be70 (CC0 1.0).

### ch4lag

`ch4_latency.py`. ICOS near-real-time data were live at 40 of 41 stations, with a median lag of
0.93 days; objects for day D appeared at about 11:10 UTC on D+1. ICOS Level 2 data end 2026-03-31.
NOAA GML's in-situ files end in December 2025 (311 to 318 days old on 2026-11-07). Scripted ICOS
file downloads need a signed-in account, so that check went ungraded.

### ch4icos and ch4icos2

`ch4_icos.py` 0.1.0 and `ch4_icos2.py` 0.2.0 (standard library only, offline tests) read hourly CH4
at each ICOS site's highest inlet from the public ICOS Zarr proxy, with no account. Results:

- The damped-anomaly forecast beat persistence at 53 of 54 sites. Two days of data latency cost a
  median 1.1 to 1.4% of RMSE.
- The seasonal fit was biased high at 52 of 54 sites (median +7.5 ppb), because a straight trend fitted
  on 2021-2024 overshoots the slower methane growth of 2025.
- Refitting monthly cut the bias to a median +4.8 ppb and improved RMSE at 52 of 54 sites, but only by
  a median 1.8%. A 30-day level anchor cut the median bias to +0.25 ppb and beat the plain fit at 39
  of 54 sites, but at noisy polluted towers its RMSE was worse.

The next baseline change waits for the contest's metric and its definition of "daily".

Run it yourself: `python fetch_base.py && python -m unittest -v test_ch4_icos2 && python ch4_icos2.py --out-dir out`

Data: ICOS RI and many contributors, European ObsPack compilation, via the ICOS Carbon Portal Zarr
proxy, CC BY 4.0, https://doi.org/10.18160/JZ2X-GZGU (please cite the ICOS data providers).

### wdcgglag

`wdcgg_lag.py` 0.1.0 (standard library only, offline tests) reads WMO WDCGG's public listing of the
latest CH4 datasets and records when each dataset ends, grouped by network (JMA, NOAA, AGAGE, ICOS).
The goal is to learn which of the contest's five data networks have public inputs fresh enough
for live five-day forecasts.
