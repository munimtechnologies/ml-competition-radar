# ch4lag 0.1.0 results

Census of how fresh public station CH4 data were at 2026-11-07T21:18:28Z (query time).
Lag = query time minus the freshest end of data; live = lag <= 7 days; stale = lag > 30 days.

## ICOS NRT (124 current objects)

Summary: `{"stations": 41, "live": 40, "stale": 1, "lagging_7_to_30_days": 0, "median_lag_live_days": 0.929, "median_publish_delay_live_days": 0.507}`

| station | id | name | heights (m) | freshest end of data | submitted | delay (d) | lag (d) |
|---|---|---|---|---|---|---|---|
| AS_ARN | ARN | El Arenosillo | 10, 50, 95 | 2026-11-06T23:00:00Z | 2026-11-07T11:07:22Z | 0.505 | 0.929 |
| AS_BIR | BIR | Birkenes | 10, 50, 75 | 2026-11-06T23:00:00Z | 2026-11-07T11:07:31Z | 0.505 | 0.929 |
| AS_CBW | CBW | Cabauw | 27, 67, 127, 207 | 2026-11-06T23:00:00Z | 2026-11-07T11:07:42Z | 0.505 | 0.929 |
| AS_CMN | CMN | Monte Cimone | 8 | 2026-11-06T23:00:00Z | 2026-11-07T11:07:52Z | 0.505 | 0.929 |
| AS_GAT | GAT | Gartow | 30, 60, 132, 216, 341 | 2026-11-06T23:00:00Z | 2026-11-07T11:07:54Z | 0.505 | 0.929 |
| AS_HEL | HEL | Helgoland | 110 | 2026-11-06T23:00:00Z | 2026-11-07T11:08:15Z | 0.506 | 0.929 |
| AS_HPB | HPB | Hohenpeissenberg | 50, 93, 131 | 2026-11-06T23:00:00Z | 2026-11-07T11:08:20Z | 0.506 | 0.929 |
| AS_HTM | HTM | Hyltemossa | 30, 70, 150 | 2026-11-06T23:00:00Z | 2026-11-07T11:08:34Z | 0.506 | 0.929 |
| AS_HUN | HUN | Hegyhátsál háttérszennyettség-mérő állomás | 10, 50, 82, 115 | 2026-11-06T23:00:00Z | 2026-11-07T11:08:45Z | 0.506 | 0.929 |
| AS_IPR | IPR | Ispra | 40, 60, 100 | 2026-11-06T23:00:00Z | 2026-11-07T11:08:52Z | 0.506 | 0.929 |
| AS_IZO | IZO | Izaña | 29 | 2026-11-06T23:00:00Z | 2026-11-07T11:09:01Z | 0.506 | 0.929 |
| AS_JFJ | JFJ | Jungfraujoch | 5, 13.9 | 2026-11-06T23:00:00Z | 2026-11-07T11:09:06Z | 0.506 | 0.929 |
| AS_JUE | JUE | Jülich | 50, 80, 120 | 2026-11-06T23:00:00Z | 2026-11-07T11:09:08Z | 0.506 | 0.929 |
| AS_KIT | KIT | Karlsruhe | 30, 60, 100, 200 | 2026-11-06T23:00:00Z | 2026-11-07T11:09:20Z | 0.506 | 0.929 |
| AS_KRE | KRE | Křešín u Pacova | 10, 50, 125, 250 | 2026-11-06T23:00:00Z | 2026-11-07T11:09:35Z | 0.507 | 0.929 |
| AS_LIN | LIN | Lindenberg | 2.5, 10, 40, 98 | 2026-11-06T23:00:00Z | 2026-11-07T11:09:50Z | 0.507 | 0.929 |
| AS_LMP | LMP | Lampedusa | 8 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:07Z | 0.507 | 0.929 |
| AS_LUT | LUT | Lutjewad | 60 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:10Z | 0.507 | 0.929 |
| AS_MHD | MHD | Mace Head | 6.5, 10, 24 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:12Z | 0.507 | 0.929 |
| AS_NOR | NOR | Norunda | 32, 58, 100 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:15Z | 0.507 | 0.929 |
| AS_OPE | OPE | Observatoire pérenne de l'environnement | 10, 50, 120 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:27Z | 0.507 | 0.929 |
| AS_OXK | OXK | Ochsenkopf | 23, 90, 163 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:37Z | 0.507 | 0.929 |
| AS_PAL | PAL | Pallas | 12 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:50Z | 0.508 | 0.929 |
| AS_PRS | PRS | Plateau Rosa | 10 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:52Z | 0.508 | 0.929 |
| AS_PUI | PUI | Puijo | 47, 84 | 2026-11-06T23:00:00Z | 2026-11-07T11:10:55Z | 0.508 | 0.929 |
| AS_PUY | PUY | Puy de Dôme | 10 | 2026-11-06T23:00:00Z | 2026-11-07T11:11:02Z | 0.508 | 0.929 |
| AS_RGL | RGL | Ridge Hill | 45, 90 | 2026-11-07T12:00:00Z | 2026-11-07T11:11:08Z | -0.034 | 0.388 |
| AS_RUN | RUN | La Réunion | 6 | 2026-11-06T23:00:00Z | 2026-11-07T11:11:12Z | 0.508 | 0.929 |
| AS_SAC | SAC | Saclay | 15, 60, 100 | 2026-11-06T23:00:00Z | 2026-11-07T11:11:15Z | 0.508 | 0.929 |
| AS_SMR | SMR | Hyytiälä | 16.8, 67.2, 125 | 2026-11-06T23:00:00Z | 2026-11-07T11:11:28Z | 0.508 | 0.929 |
| AS_SNO | SNO | Station Nord | 20, 50, 85 | 2026-09-29T23:00:00Z | 2026-10-15T10:11:25Z | 15.466 | 38.929 |
| AS_SSL | SSL | Schauinsland | 12, 35 | 2026-11-06T23:00:00Z | 2026-11-07T11:11:37Z | 0.508 | 0.929 |
| AS_STE | STE | Steinkimmen | 32, 82, 127, 187, 252 | 2026-11-06T23:00:00Z | 2026-11-07T11:11:43Z | 0.508 | 0.929 |
| AS_SVB | SVB | Svartberget | 35, 85, 150 | 2026-11-06T23:00:00Z | 2026-11-07T11:12:05Z | 0.508 | 0.929 |
| AS_TOH | TOH | Torfhaus | 10, 76, 110, 147 | 2026-11-06T23:00:00Z | 2026-11-07T11:12:17Z | 0.509 | 0.929 |
| AS_TRN | TRN | Trainou | 5, 50, 100, 180 | 2026-11-06T23:00:00Z | 2026-11-07T11:12:33Z | 0.509 | 0.929 |
| AS_UTO | UTO | Utö - Baltic sea | 57 | 2026-11-06T23:00:00Z | 2026-11-07T11:12:49Z | 0.509 | 0.929 |
| AS_WAO | WAO | Weybourne | 10 | 2026-11-05T23:00:00Z | 2026-11-06T11:13:28Z | 0.509 | 1.929 |
| AS_WES | WES | Westerland | 14 | 2026-11-07T12:00:00Z | 2026-11-07T11:12:52Z | -0.033 | 0.388 |
| AS_ZEP | ZEP | Zeppelin | 15 | 2026-11-06T23:00:00Z | 2026-11-07T11:12:54Z | 0.509 | 0.929 |
| AS_ZSF | ZSF | Zugspitze | 3 | 2026-11-06T23:00:00Z | 2026-11-07T11:12:58Z | 0.509 | 0.929 |

## ICOS L2 (121 current objects)

Summary: `{"stations": 41, "live": 0, "stale": 41, "lagging_7_to_30_days": 0, "median_lag_live_days": null, "median_publish_delay_live_days": null}`

| station | id | name | heights (m) | freshest end of data | submitted | delay (d) | lag (d) |
|---|---|---|---|---|---|---|---|
| AS_ARN | ARN | El Arenosillo | 10, 50, 95 | 2026-03-31T23:00:00Z | 2026-07-01T13:48:59Z | 91.617 | 220.929 |
| AS_BIR | BIR | Birkenes | 10, 50, 75 | 2026-03-31T23:00:00Z | 2026-07-01T13:49:14Z | 91.618 | 220.929 |
| AS_CBW | CBW | Cabauw | 27, 67, 127, 207 | 2026-03-31T23:00:00Z | 2026-07-01T13:49:41Z | 91.618 | 220.929 |
| AS_CMN | CMN | Monte Cimone | 8 | 2026-03-31T23:00:00Z | 2026-07-01T13:50:31Z | 91.618 | 220.929 |
| AS_GAT | GAT | Gartow | 30, 60, 132, 216, 341 | 2026-03-31T23:00:00Z | 2026-07-01T13:50:42Z | 91.619 | 220.929 |
| AS_HEL | HEL | Helgoland | 110 | 2026-03-31T23:00:00Z | 2026-07-01T13:52:22Z | 91.620 | 220.929 |
| AS_HPB | HPB | Hohenpeissenberg | 50, 93, 131 | 2026-03-31T23:00:00Z | 2026-07-01T13:52:32Z | 91.620 | 220.929 |
| AS_HTM | HTM | Hyltemossa | 30, 70, 150 | 2026-03-31T23:00:00Z | 2026-07-01T13:53:38Z | 91.621 | 220.929 |
| AS_HUN | HUN | Hegyhátsál háttérszennyettség-mérő állomás | 10, 50, 82, 115 | 2026-03-31T23:00:00Z | 2026-07-01T13:54:16Z | 91.621 | 220.929 |
| AS_IPR | IPR | Ispra | 40, 60, 100 | 2026-03-31T23:00:00Z | 2026-07-01T13:54:34Z | 91.621 | 220.929 |
| AS_IZO | IZO | Izaña | 29 | 2026-03-31T23:00:00Z | 2026-07-01T13:55:11Z | 91.622 | 220.929 |
| AS_JFJ | JFJ | Jungfraujoch | 13.9 | 2026-03-31T23:00:00Z | 2026-07-01T13:55:24Z | 91.622 | 220.929 |
| AS_JUE | JUE | Jülich | 50, 80, 120 | 2026-03-31T23:00:00Z | 2026-07-01T13:55:39Z | 91.622 | 220.929 |
| AS_KIT | KIT | Karlsruhe | 30, 60, 100, 200 | 2026-03-31T23:00:00Z | 2026-07-01T13:56:23Z | 91.622 | 220.929 |
| AS_KRE | KRE | Křešín u Pacova | 10, 50, 125, 250 | 2026-03-31T23:00:00Z | 2026-07-01T13:57:31Z | 91.623 | 220.929 |
| AS_LIN | LIN | Lindenberg | 2.5, 10, 40, 98 | 2026-03-31T23:00:00Z | 2026-07-01T13:58:43Z | 91.624 | 220.929 |
| AS_LMP | LMP | Lampedusa | 8 | 2026-03-31T23:00:00Z | 2026-07-01T13:59:57Z | 91.625 | 220.929 |
| AS_LUT | LUT | Lutjewad | 60 | 2026-03-31T23:00:00Z | 2026-07-01T14:00:09Z | 91.625 | 220.929 |
| AS_MHD | MHD | Mace Head | 6.5, 24 | 2026-03-31T23:00:00Z | 2026-07-01T14:00:35Z | 91.625 | 220.929 |
| AS_NOR | NOR | Norunda | 32, 58, 100 | 2026-03-31T23:00:00Z | 2026-07-01T14:00:44Z | 91.626 | 220.929 |
| AS_OPE | OPE | Observatoire pérenne de l'environnement | 10, 50, 120 | 2026-03-31T23:00:00Z | 2026-07-01T14:01:34Z | 91.626 | 220.929 |
| AS_OXK | OXK | Ochsenkopf | 23, 90, 163 | 2026-03-31T23:00:00Z | 2026-07-01T14:02:42Z | 91.627 | 220.929 |
| AS_PAL | PAL | Pallas | 12 | 2026-03-31T23:00:00Z | 2026-07-01T14:03:21Z | 91.627 | 220.929 |
| AS_PRS | PRS | Plateau Rosa | 10 | 2026-03-31T23:00:00Z | 2026-07-01T14:03:30Z | 91.627 | 220.929 |
| AS_PUI | PUI | Puijo | 47, 84 | 2026-03-31T23:00:00Z | 2026-07-01T14:03:40Z | 91.628 | 220.929 |
| AS_PUY | PUY | Puy de Dôme | 10 | 2026-03-31T23:00:00Z | 2026-07-01T14:04:06Z | 91.628 | 220.929 |
| AS_RGL | RGL | Ridge Hill | 45, 90 | 2026-03-31T23:00:00Z | 2026-07-01T14:04:17Z | 91.628 | 220.929 |
| AS_RUN | RUN | La Réunion | 6 | 2026-03-31T23:00:00Z | 2026-07-01T14:04:36Z | 91.628 | 220.929 |
| AS_SAC | SAC | Saclay | 15, 60, 100 | 2026-03-31T23:00:00Z | 2026-07-01T14:04:49Z | 91.628 | 220.929 |
| AS_SMR | SMR | Hyytiälä | 16.8, 67.2, 125 | 2026-03-31T23:00:00Z | 2026-07-01T14:05:46Z | 91.629 | 220.929 |
| AS_SNO | SNO | Station Nord | 20, 50, 85 | 2026-03-31T23:00:00Z | 2026-07-01T14:06:29Z | 91.630 | 220.929 |
| AS_SSL | SSL | Schauinsland | 12, 35 | 2026-03-31T23:00:00Z | 2026-07-01T14:06:52Z | 91.630 | 220.929 |
| AS_STE | STE | Steinkimmen | 32, 82, 127, 187, 252 | 2026-03-31T23:00:00Z | 2026-07-01T14:07:19Z | 91.630 | 220.929 |
| AS_SVB | SVB | Svartberget | 35, 85, 150 | 2026-03-31T23:00:00Z | 2026-07-01T14:08:29Z | 91.631 | 220.929 |
| AS_TOH | TOH | Torfhaus | 10, 76, 110, 147 | 2026-03-31T23:00:00Z | 2026-07-01T14:09:09Z | 91.631 | 220.929 |
| AS_TRN | TRN | Trainou | 5, 50, 100, 180 | 2026-03-31T23:00:00Z | 2026-07-01T14:10:17Z | 91.632 | 220.929 |
| AS_UTO | UTO | Utö - Baltic sea | 57 | 2026-03-31T23:00:00Z | 2026-07-01T14:11:26Z | 91.633 | 220.929 |
| AS_WAO | WAO | Weybourne | 10 | 2026-03-31T23:00:00Z | 2026-07-01T14:11:37Z | 91.633 | 220.929 |
| AS_WES | WES | Westerland | 14 | 2026-03-31T23:00:00Z | 2026-07-01T14:11:47Z | 91.633 | 220.929 |
| AS_ZEP | ZEP | Zeppelin | 15 | 2026-03-31T23:00:00Z | 2026-07-01T14:11:54Z | 91.633 | 220.929 |
| AS_ZSF | ZSF | Zugspitze | 3 | 2026-03-31T23:00:00Z | 2026-07-01T14:12:11Z | 91.633 | 220.929 |

## NRT sample downloads

| station | object | rows | valid | last valid | gap to metadata end (d) | flags | error |
|---|---|---|---|---|---|---|---|
| AS_RGL | Xn5zkImJ5ki2HPel1SeHoXmg |  |  |  |  | {} | ValueError: got an HTML page, not data: '\n<!DOCTYPE html>\n<html lang="en">\n<head>\n\t<link rel="shortcut icon" type="image/png" href="https://static.icos-cp.eu/ima' |
| AS_WES | PRn4qkNF92h2FNG6h46T8i2L |  |  |  |  | {} | ValueError: got an HTML page, not data: '\n<!DOCTYPE html>\n<html lang="en">\n<head>\n\t<link rel="shortcut icon" type="image/png" href="https://static.icos-cp.eu/ima' |
| AS_ARN | jgkmMUWQG_jKXOojbN6nONy9 |  |  |  |  | {} | ValueError: got an HTML page, not data: '\n<!DOCTYPE html>\n<html lang="en">\n<head>\n\t<link rel="shortcut icon" type="image/png" href="https://static.icos-cp.eu/ima' |
| AS_BIR | -yOh3g08PLdjzGI28fuZoqjX |  |  |  |  | {} | ValueError: got an HTML page, not data: '\n<!DOCTYPE html>\n<html lang="en">\n<head>\n\t<link rel="shortcut icon" type="image/png" href="https://static.icos-cp.eu/ima' |
| AS_CBW | zBN6UH_exe6Q2oFAkIoDf_pE |  |  |  |  | {} | ValueError: got an HTML page, not data: '\n<!DOCTYPE html>\n<html lang="en">\n<head>\n\t<link rel="shortcut icon" type="image/png" href="https://static.icos-cp.eu/ima' |

## NOAA GML in-situ CH4 DailyData files

| file | last valid day | lag (d) | Last-Modified | error |
|---|---|---|---|---|
| ch4_brw_surface-insitu_1_ccgg_DailyData.txt | 2025-12-24 | 317.888 | Tue, 11 Aug 2026 17:44:17 GMT |  |
| ch4_mko_surface-insitu_1_ccgg_DailyData.txt | 2025-12-31 | 310.888 | Tue, 11 Aug 2026 17:44:18 GMT |  |
| ch4_mlo_surface-insitu_1_ccgg_DailyData.txt | 2025-12-31 | 310.888 | Tue, 11 Aug 2026 17:44:17 GMT |  |
| ch4_smo_surface-insitu_1_ccgg_DailyData.txt | 2025-12-31 | 310.888 | Tue, 11 Aug 2026 17:44:18 GMT |  |

Checks: `{"I1_at_least_25_live": true, "I2_median_lag_live_le_2d": true, "I3_at_least_5_stale": false, "I4_median_publish_delay_le_0.6d": true, "sample_parsed": 0, "sample_within_gap": 0, "I5_sample_last_valid_within_2d": null}`
