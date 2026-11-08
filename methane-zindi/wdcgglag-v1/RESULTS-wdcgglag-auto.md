# wdcgg_lag 0.1.0 census (auto-written by the job)

Run at 2026-11-08T19:46:12Z UTC; lag = days from each dataset's last public date to 2026-11-08.

Listing: https://gaw.kishou.go.jp/search/gas_species/ch4/latest (337 file ids; 337 parsed into dated rows; 0 fetch errors).

## Gates and predictions

- **G1** HELD: listing page links at least 300 file ids
- **G2** HELD: at least 95% of listed ids fetched and parsed into a dated row
- **P1** HELD: at least 13 ICOS surface in-situ datasets; all but at most 2 end in Aug 2026
- **P2** FAILED: AGAGE in-situ datasets ending after 2024-01-01: at least 5, all end in Oct 2025
- **P3** HELD: NOAA surface in-situ datasets: at least 4, all end in Dec 2025
- **P4** HELD: no surface in-situ dataset (any contributor) ends after 2026-09-30
- **P5** HELD: median lag of surface in-situ datasets ending on/after 2025-01-01 > 120 days
- **P6** HELD: at least 90% of ICOS tower in-situ datasets end in Aug 2026

## By network and platform

| network | platform-type | datasets | ending 2025+ | newest end | min lag d | median lag d (2025+) |
|---|---|---|---|---|---|---|
| AEMET | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| AGAGE | surface-insitu | 13 | 7 | 2026-01-01 | 311 | 378 |
| AGH | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| ATOMKI | tower-insitu | 5 | 0 | 2023-12-31 | 1043 |  |
| BMKG | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| CAMS | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| CHMI | surface-flask | 1 | 0 | 2022-12-29 | 1410 |  |
| CMA | surface-insitu | 1 | 0 | 2023-12-31 | 1043 |  |
| CSIRO | aircraft-flask | 1 | 0 | 2000-09-28 | 9537 |  |
| CSIRO | surface-flask | 12 | 9 | 2025-12-31 | 312 | 324 |
| DMC | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| ECCC | surface-flask | 4 | 0 | 2018-03-03 | 3172 |  |
| ECCC | surface-insitu | 16 | 10 | 2025-12-31 | 312 | 312.0 |
| ENEA | surface-flask | 2 | 0 | 2022-12-30 | 1409 |  |
| ESNZ | ship-flask | 1 | 0 | 2011-12-03 | 5454 |  |
| ESNZ | surface-flask | 3 | 3 | 2025-12-20 | 323 | 388 |
| ESNZ | surface-insitu | 2 | 2 | 2025-12-31 | 312 | 317.5 |
| Empa | surface-insitu | 1 | 0 | 2024-12-31 | 677 |  |
| FMI | surface-insitu | 1 | 0 | 2022-04-09 | 1674 |  |
| GERC | surface-insitu | 1 | 0 | 2011-12-31 | 5426 |  |
| IAFMS | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| ICOS | surface-insitu | 15 | 15 | 2026-08-24 | 76 | 76 |
| ICOS | tower-insitu | 84 | 83 | 2026-08-25 | 75 | 77 |
| IIA | surface-insitu | 1 | 0 | 2017-12-31 | 3234 |  |
| INPE | aircraft-flask | 1 | 0 | 2009-12-31 | 6156 |  |
| INPE | surface-flask | 1 | 0 | 2009-12-22 | 6165 |  |
| INSTAAR | surface-insitu | 1 | 0 | 2016-12-31 | 3599 |  |
| ISAC | surface-insitu | 3 | 0 | 2023-12-31 | 1043 |  |
| JMA | aircraft-flask | 1 | 0 | 2024-03-21 | 962 |  |
| JMA | ship-bottle | 1 | 0 | 2017-02-11 | 3557 |  |
| JMA | ship-insitu | 2 | 2 | 2025-12-12 | 331 | 331.0 |
| JMA | surface-insitu | 3 | 2 | 2026-07-31 | 100 | 100.0 |
| KMA | surface-insitu | 3 | 3 | 2025-12-31 | 312 | 312 |
| KMD | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| KSNU | surface-remote | 1 | 0 | 2005-12-31 | 7617 |  |
| Kyrgyzhydromet | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| LSCE | aircraft-flask | 1 | 0 | 2009-02-19 | 6471 |  |
| LSCE | surface-flask | 7 | 0 | 2010-11-17 | 5835 |  |
| LSCE | surface-insitu | 3 | 0 | 2015-07-02 | 4147 |  |
| METRI | surface-flask | 1 | 0 | 1997-12-01 | 10569 |  |
| MGO | surface-flask | 2 | 1 | 2025-12-26 | 317 | 317 |
| MRI | aircraft-flask | 2 | 0 | 2000-02-19 | 9759 |  |
| MRI | ship-flask | 5 | 0 | 1993-02-22 | 12312 |  |
| MRI | surface-insitu | 1 | 0 | 2002-06-30 | 8897 |  |
| NIES | aircraft-flask | 1 | 1 | 2025-11-27 | 346 | 346 |
| NIES | surface-insitu | 2 | 2 | 2026-03-31 | 222 | 222.0 |
| NILU | surface-insitu | 2 | 1 | 2025-12-31 | 312 | 312 |
| NOAA | ship-flask | 6 | 1 | 2025-01-29 | 648 | 648 |
| NOAA | surface-flask | 81 | 50 | 2025-12-31 | 312 | 316.5 |
| NOAA | surface-insitu | 4 | 4 | 2025-12-31 | 312 | 312.0 |
| NPL | tower-insitu | 2 | 2 | 2026-04-01 | 221 | 221.5 |
| RIVM | surface-insitu | 1 | 0 | 2010-12-31 | 5791 |  |
| RSE | surface-insitu | 1 | 0 | 2018-12-31 | 2869 |  |
| SAWS | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| SMNA | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| TU | aircraft-flask | 2 | 0 | 2010-08-10 | 5934 |  |
| TU | ship-flask | 1 | 0 | 2017-06-05 | 3443 |  |
| TU | surface-flask | 1 | 0 | 2013-12-25 | 4701 |  |
| TU | surface-insitu | 1 | 1 | 2026-01-31 | 281 | 281 |
| UBAA | surface-insitu | 1 | 1 | 2025-01-01 | 676 | 676 |
| UBAG | surface-insitu | 7 | 0 | 2024-03-31 | 952 |  |
| UMLT | surface-insitu | 1 | 0 | 2019-12-31 | 2504 |  |
| UNIURB | surface-insitu | 1 | 0 | 2017-12-31 | 3234 |  |
| UNIVBRIS | tower-insitu | 6 | 3 | 2026-04-01 | 221 | 222 |
| UYRK | surface-insitu | 1 | 1 | 2025-12-31 | 312 | 312 |
| UoE | surface-insitu | 1 | 1 | 2026-05-11 | 181 | 181 |
| VNMHA | surface-insitu | 1 | 0 | 2022-12-31 | 1408 |  |

## Freshest 15 datasets

| station | network | platform | end | lag d | url |
|---|---|---|---|---|---|
| RGL | ICOS | tower-insitu | 2026-08-25 | 75 | https://gaw.kishou.go.jp/search/file/0162-6020-1002-02-01-6091 |
| KRE | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6379-1002-02-01-6126 |
| NOR | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6260-1002-02-01-6059 |
| RGL | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6020-1002-02-01-6046 |
| NOR | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6260-1002-02-01-6101 |
| PRS | ICOS | surface-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6039-1002-01-01-9999 |
| OXK | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6022-1002-02-01-6164 |
| OPE | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6437-1002-02-01-6011 |
| OPE | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6437-1002-02-01-6051 |
| HPB | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6028-1002-02-01-6132 |
| CBW | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6117-1002-02-01-6068 |
| KRE | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6379-1002-02-01-6251 |
| OXK | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6022-1002-02-01-6091 |
| KRE | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6379-1002-02-01-6011 |
| HUN | ICOS | tower-insitu | 2026-08-24 | 76 | https://gaw.kishou.go.jp/search/file/0162-6034-1002-02-01-6083 |
