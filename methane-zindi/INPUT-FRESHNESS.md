# Which public methane inputs are live? (status on 2026-11-08)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0.

Zindi's Green Rising Methane challenge scores five-day-ahead daily CH4 forecasts against
measurements made after each submission, at 59 stations from five networks. A forecast can only use
data that are public when it is made. This note sums up what MV2's pre-registered censuses found
about each network. It will be revised once Zindi publishes its own data, station list and rules
(expected 2026-11-13).

| network | best public source found | newest public data (on 2026-11-07/08) | days behind | usable as a live input? | evidence |
|---|---|---|---|---|---|
| ICOS (Europe) | ICOS near-real-time data, via the anonymous ICOS Zarr proxy | the previous day (40 of 41 stations) | median 0.93 | **yes** | [RESULTS-ch4lag.md](RESULTS-ch4lag.md), [RESULTS-ch4icos.md](RESULTS-ch4icos.md) |
| ICOS (Europe) | ICOS Level 2 / WDCGG copy | 2026-03-31 (L2), 2026-08-25 (WDCGG) | 222 / 75+ | history only | [RESULTS-wdcgglag.md](RESULTS-wdcgglag.md) |
| JMA (Japan) | WDCGG | 2026-07-31 (Minamitorishima, Ryori) | 100 | history only | [RESULTS-wdcgglag.md](RESULTS-wdcgglag.md) |
| NOAA (US) | NOAA GML files; WDCGG copy | 2025-12-31 | 312 | history only | [RESULTS-ch4lag.md](RESULTS-ch4lag.md), [RESULTS-wdcgglag.md](RESULTS-wdcgglag.md) |
| AGAGE (global) | WDCGG copy | 2025-10-25 to 2026-01-01 (Ragged Point, Barbados: 2025-10-26) | 311 to 379 | history only | [RESULTS-wdcgglag.md](RESULTS-wdcgglag.md) |
| "SNO" | not identified yet: the listing does not say whether it means a French national observation service (Service National d'Observation) or ICOS Station Nord (code SNO) | if Station Nord: its ICOS feed was 72.7 days old on 2026-11-08 | 73 if Station Nord | unclear | [RESULTS-ch4icos2.md](RESULTS-ch4icos2.md) |

## What follows for a forecast

- At ICOS stations a forecast can use yesterday's value. MV2's damped-anomaly floor beat persistence
  at 53 of 54 towers, and two days of latency cost only about 1% of RMSE.
- At AGAGE, NOAA and JMA stations, the newest public values are 3 to 12 months old. Unless Zindi
  supplies recent values, a live forecast there rests on a station's history, a trend and weather
  forecasts. MV2's studies found that a straight trend fitted over four years runs high (median +4.8
  to +7.5 ppb at ICOS towers) because methane growth slowed in 2025, so the trend choice will matter
  most at exactly these stations.
- Not yet checked: AGAGE's own data portal, which redirects to a NASA Langley server our page
  reader cannot open, and any NRT feed for SNO.

Nothing has been entered: the contest has not opened and MV2 has no Zindi account yet.
