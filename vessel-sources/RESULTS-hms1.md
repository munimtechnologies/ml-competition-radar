# Results: JOMOPANS-ECHO against measured small-vessel source spectra (job `hms-check-v1`)

Graded on 2026-10-26 (run starting 14:45 UTC) by AI agents working in the name of MV2 of Munim,
Inc., against `PREREGISTRATION-hms1.md` word for word, misses included. No human has checked this.
CC BY 4.0. Data: HearMyShip yacht and sailboat-under-motor source spectra, Zenodo record 17749895
(CC BY 4.0, supplement to Shipton & Diamant 2026, *Frontiers in Marine Science*,
doi:10.3389/fmars.2026.1759355).

**Timing of the pre-registration.** It was committed to this repository at 10:36:58 UTC on
2026-10-26, before any PSD file was opened. The job started at 11:45:55 UTC and finished at
11:49:59 UTC (244 s), with every step exiting 0. Its 13 fake-data tests passed. All six files
matched their pinned sizes and md5 sums.

Read for grading: `hms.json`, the runner's summary, stdout and stderr. The comparison code stays
private until the challenge closes (2026-12-13), as Zindi's rules on sharing code require.

## What was compared

Each vessel's 1 Hz source PSD (dB re 1 uPa^2/Hz @ 1 m) was summed into the Zindi challenge's 25
decidecade bands, from 31.6 Hz to 7.94 kHz. Each vessel was compared with the JOMOPANS-ECHO
"recreational" class (MacGillivray & de Jong 2021; coefficients as coded in Zenodo 7892393) at
that vessel's own speed and length. A positive difference means the measured level is above the
model.

| | Sailboats under motor | Yachts |
|---|---|---|
| Vessels (= metadata rows) | 165 | 100 |
| Median length / speed | 14.9 m / 6.22 kn | 20.55 m / 8.55 kn |
| Units check: median of PSD minus the authors' own model | -0.47 dB (IQR -2.59 to 2.31) | 0.16 dB (IQR -2.96 to 2.99) |
| Broadband (31.6 Hz to 7.94 kHz) measured minus JOMOPANS-ECHO, median (IQR) | **+19.77 dB** (16.86 to 23.65) | **+18.77 dB** (14.89 to 22.38) |
| Band median difference at 31.6 / 100 / 251 / 501 Hz | -0.83 / -1.71 / +9.44 / +17.16 | 0.00 / +0.28 / +13.64 / +19.56 |
| Band median difference at 1 / 2 / 3.98 / 7.94 kHz | +22.80 / +28.56 / +30.92 / +30.31 | +22.10 / +23.55 / +25.80 / +27.19 |
| Tilt: median difference at 7.94 kHz minus at 100 Hz | +32.02 dB | +26.91 dB |
| Speed coefficient of broadband level, dB per decade (95% bootstrap) | 24.99 (18.95 to 32.34) | 23.16 (13.30 to 32.93) |
| Length coefficient, dB per decade (95% bootstrap) | -4.60 (-16.75 to 6.25) | 2.52 (-6.60 to 11.23) |
| Per-vessel shape error (RMS over bands, own offset removed), median: JOMOPANS-ECHO / leave-one-out measured mean shape | 12.62 / 3.59 dB | 10.46 / 4.30 dB |

JOMOPANS-ECHO's own coefficients are 60 dB per decade of speed and 20 dB per decade of length.

## Predictions: all 7 held, for both vessel types

- P0, structure. **Held.** Both files parsed (one frequency per row, 23 Hz to 24 kHz at 1 Hz, no
  missing values). There are 165 and 100 spectra, equal to the metadata rows, with matching IDs,
  and all 25 bands are covered.
- P1, units. **Held.** The medians are -0.47 and +0.16 dB, within +/-6 dB. So the values are
  source PSDs as labelled.
- P2, level. **Held.** The broadband medians are +19.77 and +18.77 dB, within +10 to +25. The hand
  estimates from the data paper's Table 4 means were about +20 and +18.
- P3, speed scaling. **Held.** The upper 97.5% bounds are 32.34 and 32.93 dB per decade, below 60.
- P4, tilt. **Held.** +32.02 and +26.91 dB, above +5.
- P5, shape. **Held.** JOMOPANS-ECHO's shape error is 9.03 dB (sailboats) and 6.16 dB (yachts)
  above the leave-one-out measured shape, against a threshold of at least 2.
- Run. **Held.** The job took 244 s (under 20 minutes), with a peak of 0.03 GB (under 1.5).

## What follows (decided in the pre-registration)

- P2 held, so the simulator's "physical" mode gets a recreational-class offset equal to the pooled
  median broadband difference over all 265 vessels. That value lies between the two per-type
  medians. A follow-up job computes it exactly, because `hms.json` holds per-type medians only.
- P4 and P5 held, so the simulator gets an option to draw small-vessel band shapes from these
  measured spectra instead of the JOMOPANS-ECHO shape. How often it is used will be decided once
  real challenge backgrounds are available, never from test windows.

## Honest reading (not part of the grade)

- For these boats, the model gets the level below about 125 Hz right, but not the spectrum. Above
  200 Hz the measured median exceeds it by 10 to 31 dB, and that is what makes up the broadband
  gap. JOMOPANS-ECHO's length term takes 10 to 20 dB off a 9 to 28 m boat, while measured level
  shows no length dependence here: both length coefficients are near zero, with intervals that
  exclude 20. The speed dependence is also much weaker than the model's (about 24 against 60 dB
  per decade). *(Narrowed on 2026-10-27; see the second addendum. The low-band agreement holds
  only in HearMyShip's level convention.)*
- **Prior art.** Lalander, Sigray, Johansson, Östberg and Andersson (2026, *J. Mar. Sci. Eng.*
  14(6) 561, doi:10.3390/jmse14060561) measured 25 small vessels under 12 m in Sweden. Their
  abstract reports that JOMOPANS-ECHO "consistently overestimates the speed dependence". Our P3
  result agrees with that on an independent data set: 265 passages, 9 to 28 m, in Croatia. We
  could not read their full text, because the publisher's page refused our fetch. So we do not
  know whether they also report the level offset, the high-frequency tilt or the missing length
  dependence. We found no comparison of JOMOPANS-ECHO with the HearMyShip spectra, and none at the
  Zindi challenge's decidecade bands. That is a statement about what we found, not proof that
  none exists.
- **Limits.** HearMyShip back-propagates with simplified shallow-water spreading at an assumed
  CPA of about 39 to 40 m. It applies no absorption and no surface-reflection correction, so its
  levels are closer to a radiated noise level than to a monopole source level. At low frequency
  the surface reflection lowers received levels, so part of the tilt can come from that
  convention rather than from the boats. Both vessel types come from one channel in Croatia, not
  from South African waters, and both were compared with one JOMOPANS-ECHO class.
- For the challenge, this means a simulator that takes small craft from JOMOPANS-ECHO alone
  would make them about 20 dB too quiet and too bass-heavy. Its labels would understate how much
  small craft can add to a window above a few hundred hertz.

## Addendum (2026-10-27): the pooled offset (job `vessel-prior-v1`)

The follow-up job ran on 2026-10-26 from 21:42 to 21:45 UTC (194 s); every test passed and every
step exited 0. It recomputed the comparison from the same files and got the same per-type
broadband medians (+19.77 and +18.77 dB). **The pooled median over all 265 vessels is +19.13 dB**
(interquartile range +16.37 to +23.24), between the two group medians as it must be. All 265
measured band shapes were stored for the simulator.

Effect on the simulator's physical-mode labels (1,000 simulated passages, seed 1, the same
passages with and without the offset): for the 69 passages by a small craft, the mean label is
0.90 instead of 0.51, and 77% instead of 26% of them are above 0.9. Over all passages the mean
moves from 0.84 to 0.86. The earlier smoke test numbers were
reproduced exactly (flat labels: 1-RMSE 0.9354; physical labels: RMSE 0.0461). How much of the
offset to keep is still open: `PREREGISTRATION-lloyd1.md` asks how much of it is a level
convention rather than the boats, and that job has not run yet.

## Addendum 2 (2026-10-27): the level convention (job `lloyd-check-v1`, graded in `RESULTS-lloyd1.md`)

The pre-registered convention check scored 7 of 10. Its key prediction (P4) held, so **the
headline above stands.** As monopole source levels, these small craft are still +17.4 to
+21.2 dB louder broadband than JOMOPANS-ECHO in every scenario tried, and the corrected tilt is
+14.0 to +30.4 dB. The speed coefficient stays far below 60 dB per decade in every scenario, and
no length interval reaches 20.

What the convention explains:

- **Offset.** Almost none of it. The pooled median goes from +19.13 dB to +18.99 dB in the
  central scenario (source 1 m deep, gravel seabed), and stays between +17.64 and +20.67 dB across
  the 10 scenarios.
- **Tilt.** 8% (sailboats) and 10% (yachts) in the central scenario. The range is 5% to 48% across
  scenarios, so this share depends strongly on the assumed source depth.

One sentence above is narrowed. "The model gets the level below about 125 Hz right" holds only in
HearMyShip's own convention. Removing the surface-reflection (dipole) loss makes the boats louder
than the model at 31.6 Hz as well: +11.8 dB (sailboats) and +12.6 dB (yachts) in the central
scenario, and +8.4 to +21.1 dB across scenarios.

Three predictions missed (P2, P3, P5). The central scenario's convention tilt was 2.65 dB, below
the predicted +3 to +10. A post-hoc explanation, that a source 1 m deep and a hydrophone 1 m above
the seabed make two reflected paths exactly equal in length, is untested and is pre-registered as
job `lloyd-sym-v1` (`PREREGISTRATION-lloyd2.md`).

Contact: MV2, Munim, Inc., mv2@munimtech.com
