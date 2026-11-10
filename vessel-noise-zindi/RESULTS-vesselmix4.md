# Results: vesselmix-v4 (graded by hand, 2026-11-10)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0; code Apache-2.0.
Pre-registration: [PREREGISTRATION-vesselmix4.md](PREREGISTRATION-vesselmix4.md). Code:
`vessel_mix4.py` 0.4.0, running v3's analysis function unchanged on `vessel_mix.py` 0.1.0,
`vessel_mix2.py` 0.2.0 and `vessel_mix3.py` 0.3.0, downloaded from commit 2c4e55b
(`fetch_base4.py`; the first two matched the SHA-256 recorded by the v3 run, see
`base_files4.json`). Machine output: [RESULTS-vesselmix4-auto.md](RESULTS-vesselmix4-auto.md) and
[results4.json](results4.json). Run: 2026-11-10 13:15-13:25 UTC in a sealed container. All 12
offline tests passed, including the check that shifting the absolute level by +10 dB leaves both
new learners' predictions bit-for-bit unchanged. The pre-registration was public on GitHub before
the analysis started, and the public copy matched the local one byte for byte
(`prereg_public4.json`).

**Headline: 5 of 7 predictions held, and the mechanism I guessed after v3 was wrong.** Removing
the absolute level, the one input a gain offset moves, did *not* rescue the 132-feature learner on
an unseen recorder: G1TI, gain-invariant by construction, scored 0.372 against G1T's 0.374 and a
constant's 0.294. So the collapse is not a gain problem. The recorders differ in the *shape and
variability* of their backgrounds, and the 131 gain-free features read an unfamiliar background
as vessel energy (mean error +0.41 on windows with nothing added). The one-feature learner G1F (a
learned calibration of the floor share) was robust (OUT/IN 1.05) but did not beat the untrained
floor share on the unseen recorder (0.277 vs 0.272). Across seven estimators, the untrained floor
share F1 still has the best worst case.

## Gates

| gate | rule | result |
|---|---|---|
| GA | all three sites give 12 days, each with >= 1,000 complete minutes | **pass** (1,440 of 1,440 minutes at SB01, SB03, GR01) |
| GB | >= 2 vessel sites with >= 6 passages in each pool, >= 2 background sites | **pass** |
| GD | IN G1L and G1T reproduce v2 within 1e-6 | **pass** (difference 0.0) |
| GE | C0, G1L, G1T and B reproduce v3's pooled IN and OUT RMSE within 1e-6 | **pass** (difference 0.0 for all eight) |

## Estimators (pooled over vessel folds SB01 and SB03; the same 3,000 test mixtures as v1 to v3)

IN: training backgrounds from all three recorders. OUT: each test window's recorder is left out
of training. G1F and G1TI are trained on exactly the mixtures G1L and G1T were trained on.

| estimator | features | IN RMSE | OUT RMSE | OUT vs constant | OUT/IN | worst case | OUT RMSE share = 0 (bias) | OUT RMSE share > 0.5 |
|---|---|---|---|---|---|---|---|---|
| C0 constant | 0 | 0.2943 | 0.2944 | - | 1.000 | 0.2944 | 0.356 (+0.356) | 0.366 |
| **F1 untrained floor share** | 1 | 0.2722 | **0.2722** | **-7.5%** | 1.000 | **0.2722** | 0.266 (+0.224) | 0.371 |
| G1L level + floor share | 2 | 0.2342 | 0.3587 | +21.9% | 1.532 | 0.3587 | 0.495 (+0.427) | **0.273** |
| G1T randomised spectra | 132 | 0.2463 | 0.3744 | +27.2% | 1.520 | 0.3744 | 0.518 (+0.454) | 0.316 |
| B = (G1L + G1T) / 2 | - | **0.2251** | 0.3592 | +22.0% | 1.596 | 0.3592 | 0.503 (+0.441) | 0.282 |
| **G1F = G1L - level** | 1 | 0.2647 | 0.2770 | -5.9% | **1.046** | 0.2770 | 0.333 (+0.285) | 0.319 |
| **G1TI = G1T - level** | 131 | 0.2885 | 0.3719 | +26.3% | 1.289 | 0.3719 | 0.453 (+0.407) | 0.430 |

### By background recorder, OUT (RMSE)

| test background | n | C0 | F1 | G1L | G1T | G1F | G1TI |
|---|---|---|---|---|---|---|---|
| GR01 (Gray's Reef) | 973 | 0.2945 | 0.2459 | 0.4692 | 0.4830 | **0.2420** | 0.4239 |
| SB01 (Stellwagen) | 1016 | 0.2955 | **0.2808** | 0.2715 | 0.3194 | 0.2812 | 0.3700 |
| SB03 (Stellwagen) | 1011 | 0.2931 | **0.2871** | 0.3096 | 0.2981 | 0.3029 | 0.3159 |

(SB01's best OUT model is G1L, 0.2715.) Pooled over the two Stellwagen recorders (2,027 windows,
computed by hand from these rows), G1F OUT is 0.292 against F1's 0.284 and the constant's 0.294.

## Predictions, graded by hand (the code's `grade4()` agrees on all seven)

| id | prediction | confidence | value | held |
|---|---|---|---|---|
| S1 | IN: RMSE(G1F) < RMSE(F1) | 75% | 0.2647 < 0.2722 | yes |
| S2 | OUT: RMSE(G1F) < RMSE(F1) | 60% | 0.2770 > 0.2722 | **no** |
| S3 | OUT: RMSE(G1F) < RMSE(G1L) | 85% | 0.2770 < 0.3587 | yes |
| S4 | OUT: RMSE(G1TI) < RMSE(G1T) | 75% | 0.3719 < 0.3744 | yes, by 0.0025 |
| S5 | IN: RMSE(G1TI) > RMSE(G1T) | 70% | 0.2885 > 0.2463 | yes |
| S6 | OUT RMSE(G1F) / IN RMSE(G1F) < 1.10 | 55% | 0.2770 / 0.2647 = 1.046 | yes |
| S7 | OUT: on every background site, RMSE(G1F) < RMSE(C0) | 50% | GR01 0.242 < 0.294, SB01 0.281 < 0.296, SB03 **0.303 > 0.293** | **no** |

## What it means

1. **Gain invariance is not recorder invariance (S4 held only nominally).** In v3 I wrote that the
   132-feature learner "probably leans on loudness". That reading was wrong. Without the level,
   G1TI is provably unaffected by a gain offset, yet on an unseen recorder it is as bad as G1T
   (0.372 vs 0.374) and 26% worse than a constant. Its 131 inputs (band shape, range, spread,
   excess over floor, time profile) are offset-free but not habitat-free: a background from a
   recorder the model has never heard looks like vessel energy to it. The level does carry the IN
   gain (S5: 0.246 with it, 0.289 without), so it is useful when the recorder is known.
2. **A learned calibration of the floor share is stable but adds nothing on a new recorder (S2,
   S7).** G1F moved F1's mean bias from -0.071 to about zero and cut the vessel-dominated error
   (0.371 to 0.319), but raised the error on windows with nothing added (0.266 to 0.333). The
   mapping from floor share to true share learned on two recorders overshot on the third
   Stellwagen recorder (SB03: bias +0.084, RMSE 0.303, worse than the constant). On the
   unseen recorder, the untrained F1 remains the safest estimate found.
3. **For an entrant, the decision is unchanged and sharper.** If the contest's test backgrounds
   come from its ten training sites (the page says the test's background *periods* are excluded
   from the training release, not its sites), recorder-aware models such as B are worth up to a
   23% gain in this proxy. If they might not, no trained model here beat F1. Stripping gain-sensitive
   inputs is not enough: a model must see enough recorders to learn what varies between them.
4. **What is left to test is the number of training recorders.** OUT here trains on two U.S.
   recorders' backgrounds. The contest offers ten sites. Whether the OUT penalty shrinks as more
   recorders are pooled is the question that decides whether a trained model is safe there.

## Closest prior work found

Spadon, Renaud and Aravindan ([arXiv 2609.26125](https://arxiv.org/abs/2609.26125), August 2026)
show that station-level held-out validation lowers vessel-*presence* detection across 20 Canadian
stations, and that the station and hydrophone model can be recovered from the acoustic features,
which fits G1TI's collapse here. Domain-shift work on underwater acoustic target recognition (for example ShipsEar to
DeepShip transfer) is about classifying vessel *type*. Neither isolates gain from non-gain recorder
differences for vessel *energy-share* regression with a gain-invariance test; a search on
2026-11-10 found no earlier open measurement of that.

## Caveats

- OUT holds out one of three U.S. Atlantic recorders and trains on the other two, which is harsher
  than a ten-site contest. Calibrated levels; the contest's are not verified.
- Two vessel folds, one learner, one seed, one share distribution, v2's untuned augmentation. S4
  held by 0.0025, which is well inside what a different seed could move; read it as a tie.
- No Zindi data were used, and nothing here is a contest submission.

## Next

A study that varies only the number of background recorders seen in training (more SanctSound
sites, leave one recorder out), to measure whether the unseen-recorder penalty shrinks toward the
contest's ten-site setting. It will be pre-registered before it runs.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
