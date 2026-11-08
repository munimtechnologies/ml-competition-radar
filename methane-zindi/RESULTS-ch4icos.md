# ch4icos-v1 results, graded (five-day methane baselines at ICOS towers, with data latency)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0.
Graded 2026-11-08 against [PREREGISTRATION-ch4icos.md](PREREGISTRATION-ch4icos.md). The public copy
matched the local one byte for byte before the analysis ran (`ch4icos-v1/prereg_public.json`:
match true, seen 2026-11-08 12:07:02 UTC).

The job ran on 2026-11-08 from 12:07 to 12:16 UTC (query time 12:07:02Z) on 1 CPU and 0.04 GB of
memory, after the offline unit tests passed. Machine output:
[ch4icos-v1/RESULTS-ch4icos-auto.md](ch4icos-v1/RESULTS-ch4icos-auto.md) and
[ch4icos-v1/results.json](ch4icos-v1/results.json), which include per-site RMSE, MAE and bias for
all six methods.

## Grades: 7 of 7 held

| # | prediction | result | grade |
|---|---|---|---|
| Q1 | at least 25 sites included (>= 200 scored origins) | 54 of 58 sites | **held** |
| Q2 | D0 beats P0 (persistence) at >= 80% of sites | 53 of 54 (not at Réunion, RUN) | **held** |
| Q3 | C (seasonal fit) beats P0 at more than half the sites | 52 of 54 (not at RUN or Station Nord, SNO) | **held** |
| Q4 | median D0 gain over C in [0, 0.10) | 0.0241 | **held** |
| Q5 | median of the sites' mean phi(5) in [0.1, 0.5] | 0.1641 | **held** |
| Q6 | median latency cost (two days stale) below 0.05 | 0.0140 | **held** |
| F1 | >= 25 sites' highest inlets at most 4 days old on the proxy | 40 sites; median lag 1.53 d | **held** |

Best method per included site: D0 at 48, D2 at 4 (CRA, HTM, IZO, WES, where D0 and D2 differ by
under 0.1%), and the 7-day mean M7 at 2 (GAT, RUN). Excluded: IVG and MHD (too little history for
a fit), JBO (85 origins) and TAC (189 origins; its data end 2025-07-13).

## Checked by hand

- **Truncation.** No query reported truncation. I don't rely on that flag alone, because the proxy's
  documentation says CSV responses don't carry the provenance record that states truncation. Three
  other checks agree. Cabauw's six years arrived as 50,891 hours, out of at most 51,264 possible
  from 2021-01-01 to 2026-11-06. The two all-inlet probes returned 2,886 and 2,017 rows, not round
  numbers. A manual NDJSON request for Cabauw's 2024 came back at about 1.3 MB, or about 8,400 rows
  at about 155 bytes per row. That is consistent with a full year, but I couldn't read that
  response's provenance line.
- **Cabauw newest hour.** The job saw 2026-11-06 23:30 UTC, a lag of 1.526 days at 12:07 UTC. A
  manual query at about 12:15 UTC also ended at 2026-11-06 23:30 (2183.77 ppb, flag U). The two
  agree. ch4lag-v1 found that ICOS publishes each day's NRT objects at about 11:10 UTC the
  next day, so the proxy probably runs about a day behind them. That gap was not re-measured
  today.
- **Stale sites.** The proxy has nothing after the Level 2 release (2026-03-31) for 14 sites, ends
  earlier for 2 (BRM 2026-02-28, SIS 2026-03-16), and ends 2026-08-27 for Station Nord (SNO,
  Greenland, 72.5 days old). Station Nord may be the "SNO" the contest lists among its data
  sources; if so, its newest public values are months old.

## Not pre-registered: the seasonal fit is biased high almost everywhere

Exploratory, seen only after the run, so it is not evidence for any prediction above. C's
mean error (forecast minus observed) is positive at 52 of the 54 included sites. The median is
+7.5 ppb; the exceptions are ARN (-1.6) and IPR (-2.9). At clean sites the bias accounts for a large
share of the squared error: 59% at Réunion (RMSE 10.4, bias +8.0), 41% at Station Nord (9.9, +6.3)
and 30% at Zeppelin (13.1, +7.1). At polluted towers it is a small share: 4% at Cabauw (63.4,
+13.0). D0 carries most of the bias with it (Cabauw +12.6, Station Nord +4.5), because phi(5) is
small.

The likely reason is the fit design, not the data. C fits a straight trend to the four calendar
years before the origin's year, then extrapolates up to a year past the window. Global methane
growth slowed from about 17 ppb/yr in 2021 to 8.0 in 2024 and 4.8 in 2025 (NOAA GML,
https://gml.noaa.gov/ccgg/trends_ch4/), so a 2021-2024 line overshoots 2025. The next study,
[PREREGISTRATION-ch4icos2.md](PREREGISTRATION-ch4icos2.md), tests two fixes, a monthly rolling
refit and a 30-day level anchor, with predictions written before it runs.

## What it means for the entry (decision rule)

Q4 and Q6 held. At ICOS sites, the entry's floor is the damped-anomaly forecast D built from
whatever the anonymous proxy has, so no ICOS account is needed. Two days of latency cost a median
1.4% of RMSE, so effort goes to weather-driven features (the contest names NOAA weather forecasts)
rather than fresher data. Q3 held, but persistence-type methods stay candidates at clean marine
sites (RUN, SNO), where they beat the seasonal fit. Because of the bias above, the floor gets a
fresher trend before anything else is added.

## Limits

ICOS only, highest inlet only, UTC daily means of all hours (the contest's definition of "daily" is
not yet published), and the contest's metric is unknown. Origins from 2025 onward include values
still flagged U (near-real-time, before manual QC). Proxy lags are for one query time. The proxy's
store is the European ObsPack compilation (obspack_466_GVeu_v12.0_20260806) plus its NRT tail.

Data: ICOS RI and many contributors, European ObsPack compilation, via the ICOS Carbon Portal Zarr
proxy, CC BY 4.0, https://doi.org/10.18160/JZ2X-GZGU (please cite the ICOS data providers).
