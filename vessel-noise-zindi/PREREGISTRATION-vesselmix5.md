# Pre-registration: vesselmix-v5

Does training on more recorders shrink the unseen-recorder penalty? A follow-up to
[vesselmix-v3](RESULTS-vesselmix3.md) and [vesselmix-v4](RESULTS-vesselmix4.md) in an account-free
public proxy for Zindi's Underwater Vessel Noise Challenge.

MV2 of Munim, Inc. (made with AI agents working in his name). Written 2026-11-10, after v4 was
graded and before this job ran. Code: `vessel_mix5.py` 0.5.0 (Apache-2.0). It reuses v1's
download, band conversion, mixing, features, background grid and test-set code, v2's vessel
augmentation and v3's learners unchanged. The job downloads `vessel_mix.py` 0.1.0,
`vessel_mix2.py` 0.2.0 and `vessel_mix3.py` 0.3.0 from this repository at commit 2c4e55b
(`fetch_base5.py`; all three must match the SHA-256 recorded by the v4 run), and checks that this
file is public on GitHub before the analysis starts.

## What I already know

- v3/v4 (three SanctSound recorders, 3,000 test mixtures): with the test recorder among the
  training recorders, the blend B scored RMSE 0.225 against a constant's 0.294. With it held out
  (training on the other two), every learner with more than one input was worse than the
  constant (G1L 0.359, G1T 0.374, B 0.359, G1TI 0.372), while the untrained floor share F1 scored
  0.272 and the learned floor share G1F 0.277.
- The contest's unlabelled training release covers ten South African sites; its page does not say
  whether the test backgrounds come from those sites.
- On 2026-11-10 I listed NOAA's public bucket: 1-minute HMD spectra exist for SanctSound
  deployments 01-21 at SB01 and SB03 and 01-07 at GR01. The five other sites I checked (CI01,
  GR02, HI01, MB01, SB02) have hourly products only. I opened one listing of SB03 deployment 04 (daily NetCDF files of
  15.7 MB). I have not read any spectrum from deployments 02-07, and I do not know how their
  levels differ.

## Why

The contest's models can be trained on ten sites, not two. If the unseen-recorder collapse comes
from having seen too few recorders, pooling many should shrink it, and a trained model becomes safe
to submit even when the test recorders are unknown. If it does not shrink, the untrained floor
share stays the safe choice. A separate question: is the shift mainly between *sites*
(habitat) or between *deployments* of the same site (instrument, season)?

## Design (fixed in code)

- **Recorders:** deployments 01-07 of GR01, SB01 and SB03 (21 recorders). Deployment 01 reuses
  v1's 12 downloaded days; deployments 02-07 use the 2nd to 6th daily file in name order. For
  every recorder, days 0-2 give training backgrounds and days 3-4 test backgrounds (v1's 15-minute
  grid, 96 windows a day). A recorder is usable with >= 150 training and >= 80 test windows.
- **Vessels:** exactly v1's passages from deployment 01 (vessel folds SB01 and SB03; train
  vessels from the other site, as in v1-v4). Only the backgrounds change.
- **For each usable held-out recorder t:** 100 test mixtures per vessel fold from t's test days.
  Learners are retrained on backgrounds from:
  - **Dn**, n = 1, 2, 4, 8, 16: n recorders other than t, any site, in one random order per t
    (nested, so D1 is inside D2 and so on);
  - **S1, S4, SALL**: recorders from the other two sites only (SALL = all of them);
  - **SAME**: the other deployments of t's own site only;
  - **IN16**: t's own training days plus the first 15 recorders of D16's order.
- **Estimators:** C0 (training mean share), F1 (untrained floor share), G1F (learned floor share),
  G1L (absolute level + floor share), G1T (132 features, randomised vessel spectra), B = (G1L +
  G1T) / 2. HistGradientBoostingRegressor, 300 iterations, learning rate 0.05, seed 0; 6,000
  training mixtures per learner, as before.
- **Gates:** GA: >= 15 usable recorders and >= 4 per site. GB: both vessel folds have >= 6
  passages in each pool. GC (reported): every condition exists for every usable recorder. A
  prediction that uses a condition missing for some recorder is not graded.
- Descriptive, not graded: per-recorder median training level, RMSE by site of t, and on how many
  recorders G1L's RMSE is lower at D16 than at D1.

## Predictions (graded by `grade5()` on all test mixtures pooled)

| id | prediction | my confidence |
|---|---|---|
| T1 | G1L: RMSE(D16) < RMSE(D1) (more training recorders help) | 80% |
| T2 | D16: RMSE(G1L) < RMSE(C0) (with 16 recorders, loudness beats the constant on an unseen one) | 50% |
| T3 | D16: RMSE(B) < RMSE(F1) (and the blend beats the untrained floor) | 40% |
| T4 | RMSE(D1) / RMSE(D16) is larger for G1T than for G1L (the 132-feature learner gains more from recorder diversity) | 55% |
| T5 | G1L: RMSE(SAME) < RMSE(SALL) (other deployments of the same site beat all recorders of the other sites) | 70% |
| T6 | G1L: RMSE(IN16) < RMSE(D16) (having heard the test recorder still helps) | 70% |
| T7 | D16: RMSE(G1F) < RMSE(F1) (with many recorders, a learned floor calibration beats the untrained one) | 50% |

If T1-T3 hold, an entrant can train on all ten contest sites and expect a gain even on an unseen
recorder. If T1 holds but T2 and T3 fail, more recorders help but not enough, and F1 remains the
safe fallback. If T5 holds, a recorder shift is mainly a site (habitat) shift, and the contest's
case depends on whether its test sites are among its ten.

## Limits, stated before the run

- Three U.S. Atlantic sites, two of them on the same bank; deployments differ in season as well
  as instrument, and I cannot separate the two. Calibrated levels.
- 3 training and 2 test days per recorder; one random order per held-out recorder; two vessel
  folds from deployment 01 only; one learner and seed; v2's untuned augmentation.
- In deployment 01, test backgrounds (days 3-4) and test vessel passages can come from the same
  days of the same recorder, as in v1.
- No data from the Zindi challenge are used. Nothing here is a contest submission.

## Outputs

`results5.json` (gates, recorders, conditions per held-out recorder, pooled and by-site RMSE and
bias by share bin per condition, per-recorder RMSE, trend, grades), `RESULTS-vesselmix5-auto.md`,
`prereg_public.json`, `base_files.json`. A hand-read RESULTS file follows.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
