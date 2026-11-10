# Results: vesselmix-v3 (graded by hand, 2026-11-10)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0; code Apache-2.0.
Pre-registration: [PREREGISTRATION-vesselmix3.md](PREREGISTRATION-vesselmix3.md). Code:
`vessel_mix3.py` 0.3.0, running on v1's `vessel_mix.py` 0.1.0 and v2's `vessel_mix2.py` 0.2.0,
both downloaded unchanged from commit 9a2fb34 (SHA-256 in `base_files.json`). Machine output:
[RESULTS-vesselmix3-auto.md](RESULTS-vesselmix3-auto.md) and [results3.json](results3.json). Run:
2026-11-10 05:04-05:08 UTC in a sealed container. All 12 offline tests passed, and the
pre-registration was public on GitHub before the analysis started. The public copy matched the
local copy byte for byte (`prereg_public.json`).

**Headline: 5 of 7 predictions held. On a background recorder the learners had never heard,
every trained learner did worse than a constant guess, and only the untrained floor estimator
kept its edge.** When the test recorder was one of the training recorders (IN), averaging the
loudness and randomised-spectrum learners gave the best score so far without same-site vessels:
RMSE 0.225, 23.5% below a constant. When the test recorder was held out (OUT), the same blend
scored 0.359, 22% *worse* than the constant (0.294). The untrained floor estimator F1 (0.272)
beat every trained model there. Absolute loudness carries the gain when the recorder is known
and causes the loss when it is not.

## Gates

| gate | rule | result |
|---|---|---|
| GA | all three sites give 12 days, each with >= 1,000 complete minutes | **pass**: 12 days at SB01, SB03 and GR01, 1,440 of 1,440 minutes each |
| GB | >= 2 vessel sites with >= 6 passages in each pool, >= 2 background sites | **pass**: vessel folds SB01 and SB03; background sites GR01, SB01, SB03 |
| GD | IN G1L and IN G1T reproduce v2's pooled RMSE within 1e-6 | **pass**: 0.23420903245117503 and 0.24633835050771377, difference 0.0 for both |

## Background levels by recorder (descriptive, not graded)

Window energy over all 25 bands and 15 minutes, in dB (SanctSound's calibrated levels).

| site | training days, median (p10-p90) | test days, median (p10-p90) |
|---|---|---|
| GR01 (Gray's Reef) | 128.1 (126.2-129.7) | 126.5 (124.6-129.1) |
| SB01 (Stellwagen Bank) | 116.2 (113.1-120.0) | 118.2 (114.2-122.7) |
| SB03 (Stellwagen Bank) | 119.9 (115.4-124.5) | 120.5 (116.4-124.4) |

GR01's backgrounds are 6 to 12 dB louder than the Stellwagen sites'. I had not looked at these
levels before writing the predictions.

## Estimators (pooled over vessel folds SB01 and SB03; the same 3,000 test mixtures as v1 and v2)

IN: training backgrounds from all three recorders (days 1-8), as in v2. OUT: for each test
window, the models are retrained without any background from that window's recorder. F1 needs no
training, so it is the same in both.

| estimator | IN RMSE | IN vs constant | OUT RMSE | OUT vs constant | OUT bias | OUT RMSE share = 0 (bias) | OUT RMSE share > 0.5 |
|---|---|---|---|---|---|---|---|
| C0 constant | 0.2943 | - | 0.2944 | - | +0.003 | 0.356 (+0.356) | 0.366 |
| F1 untrained floor | 0.2722 | -7.5% | **0.2722** | **-7.5%** | -0.071 | 0.266 (+0.224) | 0.371 |
| G1L loudness + floor share | 0.2342 | -20.4% | 0.3587 | +21.8% | +0.127 | 0.495 (+0.427) | **0.273** |
| G1T randomised vessel spectra | 0.2463 | -16.3% | 0.3744 | +27.2% | +0.110 | 0.518 (+0.454) | 0.316 |
| **B = (G1L + G1T) / 2** | **0.2251** | **-23.5%** | 0.3592 | +22.0% | +0.118 | 0.503 (+0.441) | 0.282 |

On the held-out recorder, all three learners predict a vessel where there is none: on windows
with nothing added, their mean prediction is 0.43 to 0.45, against 0.13 to 0.23 in IN.

### By background recorder (RMSE)

| test background | n | IN C0 | IN F1 | IN G1L | IN G1T | IN B | OUT C0 | OUT G1L | OUT G1T | OUT B |
|---|---|---|---|---|---|---|---|---|---|---|
| GR01 | 973 | 0.2945 | 0.2459 | 0.1693 | 0.1414 | **0.1352** | 0.2945 | 0.4692 | 0.4830 | 0.4710 |
| SB01 | 1016 | 0.2955 | 0.2808 | 0.2527 | 0.2993 | 0.2656 | 0.2955 | **0.2715** | 0.3194 | 0.2862 |
| SB03 | 1011 | 0.2929 | 0.2871 | 0.2665 | 0.2661 | **0.2489** | 0.2931 | 0.3096 | 0.2981 | 0.2951 |

- **GR01 held out** (trained only on the 6-12 dB quieter Stellwagen backgrounds): every learner
  reads GR01's louder background as vessel energy. G1L's mean prediction on windows with nothing
  added is 0.71. RMSE 0.469, 59% worse than the constant.
- **The two Stellwagen recorders** are much closer in level, yet holding one out still removed
  nearly all of the gain. Pooled over SB01 and SB03 (2,027 windows, computed by hand from the
  per-site rows), G1L went from 0.260 (IN) to 0.291 (OUT). The constant is 0.294 and F1 is 0.284.
  So even between two recorders on the same bank, the trained loudness model ended up no better
  than the untrained floor.

## Predictions, graded by hand (the code's `grade3()` agrees on all seven)

| id | prediction | confidence | value | held |
|---|---|---|---|---|
| R1 | IN: RMSE(B) < min(RMSE(G1L), RMSE(G1T)) | 70% | 0.2251 < min(0.2342, 0.2463) | yes |
| R2 | IN: RMSE(B) <= 0.231114 (closes >= 50% of v2's G1 -> G0 gap) | 55% | 0.2251; (0.2694 - 0.2251) / (0.2694 - 0.1928) = 0.578 | yes |
| R3 | OUT/IN RMSE ratio of G1L > that of G1T | 75% | 0.3587 / 0.2342 = 1.532 vs 0.3744 / 0.2463 = 1.520 | yes, by a hair (0.012) |
| R4 | OUT: RMSE(G1L) > RMSE(G1T) | 55% | 0.3587 < 0.3744 | **no** |
| R5 | OUT: on at least one background site, RMSE(G1L) > RMSE(C0) | 50% | GR01 0.469 > 0.294; SB03 0.310 > 0.293 (SB01 0.272 < 0.296) | yes |
| R6 | IN: on every background site, RMSE(G1L) < RMSE(G1T) | 45% | GR01 0.169 > 0.141; SB03 0.2665 > 0.2661 (SB01 0.253 < 0.299) | **no** |
| R7 | RMSE(F1) < OUT RMSE(B) | 35% | 0.2722 < 0.3592 | yes |

## What it means for an entrant

1. **R4 and R3 together: the 132-feature learner is just as tied to loudness as the two-feature
   one.** I expected G1T, with 131 of its 132 features unaffected by a gain offset, to hold up
   better on an unseen recorder. It did not (OUT 0.374 vs 0.359), and the two lost almost the same
   share of their accuracy (R3 held by 0.012). The one input of either model that a gain offset
   moves is the window's absolute level, so both probably lean on it. The recorders also differ in
   more than gain, so this is a reading written after the run, not a result; the next study tests
   it.
2. **Whether the contest's test recorders appear in its training data decides the strategy.** If
   they do (IN), the blend B is the best model in these studies so far. If they might not (OUT),
   an absolute-level model can be worse than submitting the constant. Contest levels are
   uncalibrated, so a gain difference between recorders is plausible. The contest page (read
   2026-11-10) says the training release covers ten sites and that the test's background periods
   are excluded from it. It does not say whether the test backgrounds come from the same sites.
3. **The safe fallback is a floor-relative estimate.** F1 uses only the window's own floor, so a
   gain shift cannot move it, and it was the best model in OUT. Whether a *trained* model on
   gain-free inputs keeps F1's robustness and beats it is the next study.
4. The blend helped because the two learners err in opposite directions on windows with nothing
   added (IN bias +0.234 vs +0.126) and on vessel-dominated windows (-0.187 vs -0.298). R6's miss
   shows neither learner wins everywhere: G1T was better on GR01 in IN.

## Closest prior work found

Spadon, Renaud and Aravindan, "When Big Data Becomes a Curse: Spatial Heterogeneity and the Limits
of Learning from Passive Acoustic Monitoring Data" ([arXiv 2609.26125](https://arxiv.org/abs/2609.26125),
August 2026). It uses 20 Atlantic Canadian stations and finds that holding out whole stations
lowers AIS-based vessel-*presence* detection from ROC-AUC 0.661 (random windows) to 0.612. Our
result is about a different task: regressing a vessel's *energy share* on known-answer mixtures.
There, a held-out recorder pushed trained models below a constant guess while a gain-free floor
estimate kept its edge. A search on 2026-11-10 found no earlier open measurement of that.

## Caveats

- OUT holds out one of three U.S. Atlantic recorders. They differ in more than gain (depth, ships,
  biology, season), and OUT trains on two recorders' backgrounds instead of three. So OUT is a harsh
  stand-in for a gain shift, not a measurement of the contest's shift.
- Two vessel folds, one learner, one seed, one share distribution, calibrated levels, and v2's
  untuned augmentation. An equal average is the only blend tried. Nothing here used Zindi data or
  is a contest submission.

## Next

[PREREGISTRATION-vesselmix4.md](PREREGISTRATION-vesselmix4.md) removes one thing from each
learner: the absolute level. G1F is G1L without it (a learned calibration of the floor share), and
G1TI is G1T without it. Both are invariant to a gain offset by construction. The study asks
whether they keep their gain on an unseen recorder and what they give up when the recorder is
known.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
