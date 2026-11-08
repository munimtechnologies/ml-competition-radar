# ch4icos2-v1 results, graded (can the five-day seasonal floor's high bias at ICOS towers be fixed?)

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name. Text CC BY 4.0.
Graded 2026-11-08 against [PREREGISTRATION-ch4icos2.md](PREREGISTRATION-ch4icos2.md). The public
copy matched the local one byte for byte before the analysis ran (`ch4icos2-v1/prereg_public.json`:
match true, sha256 4fd96d12..., seen 2026-11-08 16:07:55 UTC).

The job ran on 2026-11-08 from 16:06 to 16:17 UTC (query time 16:07:56Z) on 1 CPU and 0.05 GB of
memory, after its 8 offline unit tests passed. It fetched the unchanged `ch4_icos.py` 0.1.0 from the
pinned commit 481e0091. Machine output:
[ch4icos2-v1/RESULTS-ch4icos2-auto.md](ch4icos2-v1/RESULTS-ch4icos2-auto.md) (per-site RMSE and bias
of all seven methods) and [ch4icos2-v1/results.json](ch4icos2-v1/results.json).

## Grades: 5 of 7 held

Methods: C = the v1 seasonal fit (straight trend + 2 annual harmonics on the four calendar years
before the origin's year); Cr = the same fit refitted every month on the 1,461 days ending two days
before the month starts; D0/Dr = damped anomaly on top of C/Cr; Dr2 = Dr with two days of data
latency; L30 = C shifted by its mean error over the last 30 days.

| # | prediction | result | grade |
|---|---|---|---|
| R1 | median Cr bias < half of median C bias | +4.83 vs +7.54 ppb (half = 3.77) | **failed** |
| R2 | Cr beats C at >= 75% of sites | 52 of 54 (96%; not BIK, IPR) | **held** |
| R3 | Dr beats D0 at >= 75% of sites | 52 of 54 (96%; not BIK, IPR) | **held** |
| R4 | median gain of Dr over D0 >= 0.02 | 0.0178 | **failed** |
| R5 | median Dr gain over D0 at the 10 clean sites >= 0.05 | 0.0599 | **held** |
| R6 | L30 beats C at more than half of sites | 39 of 54 (72%) | **held** |
| R7 | median latency cost RMSE(Dr2)/RMSE(Dr) - 1 < 0.05 | 0.0109 | **held** |

Context check (already seen in v1, not a prediction): median C bias +7.54 ppb, at least +5: true.
C's bias is positive at 52 of 54 sites, as in v1.

Included: 54 sites with at least 200 paired origins (origins from 2025-01-01). Excluded: IVG and MHD
(no scorable origins), JBO (85) and TAC (189). Best method per site: Dr at 39, L30 at 10 (BIK, HFD,
IZO, RGL, RUN, SIS, SNO, STE, WAO, ZEP), Dr2 at 3 (CMN, CRA, WES, all within 0.3% of Dr), Cr at 1
(OHP) and D0 at 1 (IPR).

## Checked by hand

- **Arithmetic.** Réunion (RUN, the cleanest marine site): C 10.29 -> Cr 7.21 gives 1 - 7.21/10.29 =
  0.299, D0 8.26 -> Dr 6.62 gives 0.199, and L30 6.40 gives 0.378 over C, all as printed. Zeppelin
  (ZEP): 1 - 12.02/13.12 = 0.084, as printed. Counting the per-site table by hand gives the same 52,
  52 and 39 sites as the automatic checks. The 10 clean sites (lowest C RMSE: SNO, RUN, ZEP, IZO,
  LMP, PDM, SVB, INE, FKL, SIS; next is NOR at 18.99) have Dr gains whose median is (0.055 +
  0.065) / 2 = 0.060.
- **Same data as v1.** Cabauw (CBW) again arrived as 50,891 hours ending 2026-11-06 23:30 UTC.
  No query reported truncation (`truncated_chunks` 0 at every site). Each fully covered site had 23
  monthly refits (January 2025 to November 2026), as designed.
- **Station Nord (SNO).** The newest value on the proxy is still 2026-08-27 (72.7 days old).

## What it means for the entry (decision rule)

- **R3 held, R4 failed**, so Dr does not automatically become the floor everywhere. The monthly
  refit helps almost everywhere, but only by a median 1.8% of RMSE.
- **R5 held and R4 failed**, so, as written in advance, the fix matters mainly at clean sites, where
  bias is a large share of error. The choice of method per site is made on held-out contest data.
- **R1 failed**: even a monthly refitted straight trend is still biased +4.8 ppb at the median
  site. The trend's shape is the problem, not only its age. A four-year straight line still leans on
  the fast growth of 2021-2022 (about 17 ppb/yr, NOAA GML) while growth in 2025 was 4.8. The next
  step is a damped or shorter-window trend, which needs its own pre-registration.
- **L30 stays a per-site candidate.** It beats Dr at 10 sites, 5 of them clean (RUN, SNO, ZEP, SIS,
  IZO).

## Not pre-registered (seen only after the run)

The 30-day level anchor nearly removes the bias: L30's median bias is +0.25 ppb, against +4.08 for
Dr and +7.54 for C. But at polluted towers it costs RMSE, because a 30-day mean of a noisy anomaly
adds variance (IPR 65.4 against 60.1 for D0; LUT 102.6 against 100.0 for Dr). Where noise is small, L30 wins by
a lot: 0.378 over C at RUN and 0.225 at SNO. An obvious combination is a damped anomaly on top of
L30's level instead of C's. It is not tested here, and per MV2's own rule no further baseline
variant will run until Zindi publishes the contest's target, "daily" definition and metric (the
contest opens 2026-11-13).

## Limits

ICOS only, highest inlet only, UTC daily means of all hours; the contest's metric and "daily"
definition are unknown. Origins from 2025 onward include near-real-time values flagged U. One query
time; recent days may differ slightly from v1, which ran four hours earlier. Nothing has been
submitted: MV2 has no Zindi account yet.

Data: ICOS RI and many contributors, European ObsPack compilation, via the ICOS Carbon Portal Zarr
proxy, CC BY 4.0, https://doi.org/10.18160/JZ2X-GZGU (please cite the ICOS data providers). Growth
rates: NOAA GML, https://gml.noaa.gov/ccgg/trends_ch4/.
