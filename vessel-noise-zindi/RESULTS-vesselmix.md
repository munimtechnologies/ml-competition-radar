# Results: vesselmix-v1 (graded by hand, 2026-11-09)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0; code Apache-2.0.
Pre-registration: [PREREGISTRATION-vesselmix.md](PREREGISTRATION-vesselmix.md). Code: `vessel_mix.py`
0.1.0. Machine output: [RESULTS-vesselmix-auto.md](RESULTS-vesselmix-auto.md) and
[results.json](results.json). Run: 2026-11-09 10:25-10:29 UTC, sealed container, 14 of 14 offline
tests passed, and the pre-registration was public on GitHub before the analysis started
(`prereg_public.json`).

**Headline: 6 of 7 predictions held, but the one I was most confident about failed.** A learner
trained on synthetic mixtures whose vessel passages come from a *different* site than the test
passages (an entrant's position, since the organisers' vessel recordings are unknown) cut RMSE
only **8.4%** below a constant. The same learner trained on passages from the test vessels' own
site cut it **34.5%**. Almost all of the difference (89% of the extra squared error) comes from
windows where the vessel carries more than half of the energy.

## Gates

| gate | rule | result |
|---|---|---|
| GA | all three sites give 12 days, each with >= 1,000 complete minutes | **pass**: 12 days at SB01, SB03 and GR01, all 1,440 of 1,440 minutes complete; spectra read from the `psd` variable, times from the file's `time` variable |
| GB | >= 2 vessel sites with >= 6 passages in each pool | **pass**: SB01 (26 train / 26 test) and SB03 (33 / 32). GR01 has 2 / 2 and serves only as a background site and a source of G1 training vessels, as the pre-registration expected |

Counts: 1,152 grid windows per site (768 training and 384 test backgrounds). SanctSound's ship
labels touch 898 of SB01's 1,152 windows, 821 of SB03's and 34 of GR01's: Stellwagen Bank
backgrounds mostly contain some ship sound, as the contest warns its own backgrounds may.

## Estimators (pooled over folds SB01 and SB03, 3,000 test mixtures)

| estimator | RMSE | score (1 - RMSE) | vs constant | bias | RMSE, share > 0.5 | bias, share > 0.5 |
|---|---|---|---|---|---|---|
| C0 constant | 0.2943 | 0.7057 | - | +0.004 | 0.365 | -0.346 |
| F1 untrained floor | 0.2722 | 0.7278 | -7.5% | -0.071 | 0.371 | -0.343 |
| G1 learner, other-site vessels | 0.2694 | 0.7306 | -8.4% | -0.115 | **0.403** | **-0.359** |
| G0 learner, same-site vessels | **0.1928** | **0.8072** | **-34.5%** | -0.046 | 0.265 | -0.210 |

By fold (RMSE): SB01 C0 0.293, F1 0.281, G1 0.263, G0 0.210; SB03 C0 0.295, F1 0.263, G1 0.276,
G0 0.174. In the SB03 fold the other-site learner is *worse* than the untrained floor.

## Predictions, graded by hand (the code's `grade()` agrees on all seven)

| id | prediction | confidence | value | held |
|---|---|---|---|---|
| P1 | RMSE(G1) <= 0.6 x RMSE(C0) | 70% | ratio 0.916 | **no** |
| P2 | RMSE(F1) < RMSE(C0) | 50% | 0.2722 < 0.2943 | yes |
| P3 | RMSE(G1) < RMSE(F1) | 90% | 0.2694 < 0.2722 (pooled only; not in fold SB03) | yes, narrowly |
| P4 | RMSE(G0) < RMSE(G1) in every fold, pooled ratio >= 1.10 | 55% | both folds; ratio 1.398 | yes |
| P5 | mean F1 on share-0 windows > 0.05 | 85% | 0.224 | yes |
| P6 | mean (F1 - share) on share >= 0.5 windows < 0 | 75% | -0.343 | yes |
| P7 | on share-0 windows, G1 higher when the background has a labelled ship (most eligible sites) | 70% | SB01 0.178 vs 0.158, SB03 0.173 vs 0.128; GR01 not eligible (5 ship windows) | yes, 2 of 2 |

Check by hand: 0.2694 / 0.2943 = 0.916 > 0.6, so P1 fails; 0.2694 / 0.1928 = 1.398 >= 1.10, so P4
holds. P6's value uses share >= 0.5 and the bin table uses share > 0.5; with shares drawn from a
continuous distribution these are the same windows.

## What it means for an entrant

1. **The learner learns the vessel source, not "vessels".** With passages from a different site,
   gradient boosting barely beats a hand-made floor estimator. With passages from the same site it
   cuts error four times as much. In the contest the organisers' vessel recordings are unknown, so
   an entrant's training vessels will not match them. The v1 numbers suggest the true gain from
   synthetic mixtures could be much smaller than an entrant's own validation (which uses their own
   vessels) shows. **A held-out vessel *source* is the honest validation split.**
2. **The error sits in vessel-dominated windows.** Every estimator underestimates shares above
   0.5. The other-site learner is worse there than the constant (0.403 vs 0.365). This is where a
   SanctSound passage window fills the whole 15 minutes, so a floor method treats much of the
   vessel as background (P6). Of G1's extra squared error over G0, 89% comes from these windows
   (post hoc: 165.9 vs 71.6 of 217.8 vs 111.5 summed squared error).
3. **Backgrounds with ships read as vessel.** On windows with nothing added, the learner predicts
   more vessel when SanctSound labels a ship in the background (P7). The contest says a zero target
   "does not mean the original background is vessel-free", so some error of this kind cannot be
   removed.

## Caveats

- **G0's advantage may partly be a site fingerprint.** A SanctSound passage window includes its
  site's own ambient sound. So G0 may partly recognise "SB01-like" or "SB03-like" spectra rather
  than the vessel itself. The follow-up (vesselmix-v2) tests learners without spectral-shape
  features and with randomised vessel spectra. Those learners cannot use that cue as easily.
- Two Stellwagen Bank sites only, one learner, one seed, one share distribution; GR01 had too few
  passages to be a fold. U.S. Atlantic data with calibrated levels, while the contest's are South
  African and uncalibrated. Nothing here used Zindi data or is a contest submission.

## Next

[PREREGISTRATION-vesselmix2.md](PREREGISTRATION-vesselmix2.md) asks whether an entrant can close
part of the gap without knowing the organisers' vessels: drop spectral-shape features, randomise
the training vessels' spectra, or rely on loudness alone.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
