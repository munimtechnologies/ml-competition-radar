# Pre-registration: vesselmix-v4

Do gain-free learners keep their gain on a background recorder they have never heard? A follow-up
to [vesselmix-v3](RESULTS-vesselmix3.md) in an account-free public proxy for Zindi's Underwater
Vessel Noise Challenge.

MV2 of Munim, Inc. (made with AI agents working in his name). Written 2026-11-10, after v3 was
graded and before this job ran. Code: `vessel_mix4.py` 0.4.0 (Apache-2.0). It runs v3's own
analysis function unchanged and only adds two learners. The job downloads `vessel_mix.py` 0.1.0,
`vessel_mix2.py` 0.2.0 and `vessel_mix3.py` 0.3.0 from this repository at commit 2c4e55b
(`fetch_base.py`; the first two must match the SHA-256 recorded by the v3 run). The job checks that
this file is public on GitHub before the analysis starts.

## What I already know (all of v1 to v3)

Same data, folds and 3,000 pooled test mixtures as v1 to v3. IN means training backgrounds come
from all three recorders. OUT means each test window's recorder is left out of training.

| estimator | IN RMSE | OUT RMSE |
|---|---|---|
| C0 constant | 0.2943 | 0.2944 |
| F1 untrained floor share | 0.2722 | 0.2722 |
| G1L absolute level + floor share | 0.2342 | 0.3587 |
| G1T 132 features, randomised vessel spectra | 0.2463 | 0.3744 |
| B average of G1L and G1T | 0.2251 | 0.3592 |

F1 by background site (IN = OUT): GR01 0.246, SB01 0.281, SB03 0.287. C0 OUT by site: 0.294, 0.296,
0.293. F1's bias is +0.224 on windows with nothing added and -0.343 on windows with share > 0.5.
In v2, learners without the absolute level *and* without spectral shape (G1S 0.319, G1TS 0.306 IN)
did worse than the constant. Nothing else has been run.

## Why

In the proxy's mixing rule (also the contest's target), share = 1 - E_background / E_window. Of the
132 features, only one, the window's absolute level (feature 130), moves under a constant gain
offset; the other 131, including the floor share (feature 131), do not. The recorders differ in
more than gain, though, so v3 could not tell whether the absolute level alone caused the OUT
collapse. Removing it from each learner answers that, and gives an entrant a model to use when
the contest's test recorders or gains may differ from training.

## Design (fixed in code)

- **G1F** = G1L without the absolute level: the same learner on the floor share alone, trained on
  G1L's exact training mixtures. It is a learned calibration of F1.
- **G1TI** = G1T without the absolute level: the same learner on the other 131 features, trained on
  G1T's exact (augmented) training mixtures.
- Both are fitted in IN and in OUT on the identical training sets that v3 used for G1L and G1T
  (same seeds), and scored on the identical 3,000 test windows. Learner: scikit-learn
  HistGradientBoostingRegressor, 300 iterations, learning rate 0.05, seed 0, as before.
- A unit test checks that shifting only feature 130 by +10 dB leaves G1F's and G1TI's predictions
  bit-for-bit unchanged.
- Descriptive, not graded: each estimator's worst case, max(IN RMSE, OUT RMSE).

## Gates

- **GA, GB**: as in v3. **GD**: as in v3 (IN G1L and G1T reproduce v2).
- **GE**: C0, G1L, G1T and B reproduce v3's pooled IN and OUT RMSE within 1e-6. If GE fails, the
  predictions are still graded (each compares estimators within this run), but the results file
  must say so.

## Predictions (graded by `grade4()` on the pooled 3,000 test windows unless stated)

| id | prediction | my confidence |
|---|---|---|
| S1 | IN: RMSE(G1F) < RMSE(F1) (calibrating the floor share helps) | 75% |
| S2 | OUT: RMSE(G1F) < RMSE(F1) (and still helps on an unseen recorder) | 60% |
| S3 | OUT: RMSE(G1F) < RMSE(G1L) (dropping the absolute level helps on an unseen recorder) | 85% |
| S4 | OUT: RMSE(G1TI) < RMSE(G1T) | 75% |
| S5 | IN: RMSE(G1TI) > RMSE(G1T) (the absolute level helps when the recorder is known) | 70% |
| S6 | RMSE_OUT(G1F) / RMSE_IN(G1F) < 1.10 | 55% |
| S7 | OUT: on every background site, RMSE(G1F) < RMSE(C0) | 50% |

If S2 and S3 hold, an entrant unsure about the test recorders has a model that beats both the
constant and the untrained floor without relying on calibrated levels. If S2 fails, the plain
floor share is the safer choice. If S4 fails, G1T's relative features also break across
recorders, not just its level.

## Limits, stated before the run

- OUT holds out one of three U.S. Atlantic recorders, which differ in more than gain, and trains on
  two recorders' backgrounds instead of three. It is a harsh stand-in for the contest's unknown
  shift, not a measurement of it.
- Two vessel folds, one learner, one seed, one share distribution, calibrated levels, v2's untuned
  augmentation. No other feature subsets are tried.
- No data from the Zindi challenge are used. Nothing here is a contest submission.

## Outputs

`results4.json` (gates, per-fold, pooled and per-background-site RMSE and bias by share bin for IN
and OUT, worst cases, grades), `RESULTS-vesselmix4-auto.md`, `prereg_public.json`,
`base_files.json`. A hand-read RESULTS file follows.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
