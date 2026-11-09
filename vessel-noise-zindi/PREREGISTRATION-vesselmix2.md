# Pre-registration: vesselmix-v2

Can an entrant close the vessel-source gap without knowing the organisers' vessels? A follow-up
to [vesselmix-v1](RESULTS-vesselmix.md), an account-free public proxy for Zindi's Underwater
Vessel Noise Challenge.

MV2 of Munim, Inc. (made with AI agents working in his name). Written 2026-11-09 after v1 was
graded and before this job ran. Code: `vessel_mix2.py` 0.2.0 plus v1's unchanged `vessel_mix.py`
0.1.0 (Apache-2.0). The job checks that this file is public on GitHub before the analysis starts.

## What I already know (all of v1)

v1 used the same data, folds and test mixtures. Pooled RMSE: constant C0 0.2943, untrained floor F1
0.2722, learner G1 trained on other-site vessels 0.2694, learner G0 trained on same-site vessels
0.1928. G1 underestimates vessel-dominated windows (share > 0.5: bias -0.359, RMSE 0.403, worse
than the constant's 0.365). 89% of G1's extra squared error over G0 comes from those windows. Fold
SB03: G1 0.276 is worse than F1 0.263. Nothing else has been run on these data.

## Question and why it matters

In the contest the organisers' vessel recordings are unknown. Every entrant is in G1's position,
not G0's. v1 suggests that a learner trained on synthetic mixtures mostly learns its training
vessels' own signature. Three cheap remedies an entrant could try:

- **G1S, no spectral shape**: drop the 25 per-band spectral-shape features and the absolute level
  (106 of 132 features left: per-band temporal range, SD and excess over the floor; the per-minute
  broadband profile, raw and sorted; the floor share F1). Idea: the site/vessel signature lives
  mostly in the average spectrum, so a learner without it must rely on how energy rises and falls.
- **G1T, randomised vessels**: train on the same backgrounds, shares and vessel draws as G1, but
  each drawn vessel window gets a random spectral tilt (uniform -6 to +6 dB per decade around
  1 kHz), an independent random gain per band (uniform -2 to +2 dB) and, with probability 0.5, is
  played backwards in time. This is domain randomisation of the vessel spectrum.
- **G1TS**: both.
- **G1L, loudness only** (a diagnostic): only the absolute level and F1. Mixing at share s raises
  the window's level by -10 log10(1 - s) dB over its background (10 dB at s = 0.9), whatever the
  vessel looks like.

All learners: scikit-learn HistGradientBoostingRegressor, 300 iterations, learning rate 0.05,
seed 0, the same as v1. Same folds (test vessels from SB01, then SB03), same 1,500 test mixtures per
fold, same 6,000 training mixtures per learner per fold (G1T and G1TS see the same backgrounds,
shares and vessel draws as G1, only augmented).

## Gates

- **GA, GB**: as in v1 (12 complete days at all three sites; at least two vessel sites).
- **GC**: G1 reproduces v1's pooled RMSE 0.2694491587478854 within 1e-6. This checks that data,
  code and seeds are unchanged. If GC fails, the predictions are still graded, because all of them
  compare learners within this run, but the results file says the run is not comparable to v1.

## Predictions (graded by `grade2()` on the pooled test mixtures)

| id | prediction | my confidence |
|---|---|---|
| Q1 | RMSE(G1T) < RMSE(G1) | 60% |
| Q2 | RMSE(G1S) < RMSE(G1) | 55% |
| Q3 | the best of G1T, G1S and G1TS closes at least 25% of the gap from G1 down to G0: (G1 - best) / (G1 - G0) >= 0.25 | 40% |
| Q4 | G0 still beats every G1 variant (G1T, G1S, G1TS, G1L) | 85% |
| Q5 | RMSE(G1L) < RMSE(C0) | 75% |
| Q6 | RMSE(G1L) < RMSE(G1) (loudness alone does at least as well as the full other-site learner) | 50% |
| Q7 | the best of G1T, G1S, G1TS still underestimates vessel-dominated windows: mean bias on share > 0.5 below -0.20 | 70% |

Q3 and Q6 are close to coin flips. I state them so that either answer is informative.

## Limits, stated before the run

- Same limits as v1: two Stellwagen Bank vessel sites, U.S. Atlantic calibrated data, one learner,
  one seed, one share distribution. The augmentation ranges are my guesses, not tuned. Only one
  setting is run, so a miss on Q1 says "this randomisation", not "randomisation never helps".
- G1L uses calibrated absolute levels. The contest's levels are uncalibrated, so loudness may be a
  weaker cue there unless backgrounds have consistent gain.
- No data from the Zindi challenge are used. Nothing here is a contest submission.

## Outputs

`results2.json` (per-fold and pooled RMSE and bias by share bin for all eight estimators, gates,
grades), `RESULTS-vesselmix2-auto.md`, `prereg_public.json`. A hand-read RESULTS file follows.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
