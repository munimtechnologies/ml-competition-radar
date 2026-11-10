# Pre-registration: vesselmix-v3

Does the loudness cue survive a background recorder the model has never heard, and does blending
it with the randomised-spectrum learner help? A follow-up to [vesselmix-v2](RESULTS-vesselmix2.md)
in an account-free public proxy for Zindi's Underwater Vessel Noise Challenge.

MV2 of Munim, Inc. (made with AI agents working in his name). Written 2026-11-10, after v2 was
graded and before this job ran. Code: `vessel_mix3.py` 0.3.0 (Apache-2.0). It reuses v1's
`vessel_mix.py` 0.1.0 and v2's `vessel_mix2.py` 0.2.0 unchanged; the job downloads both from
this repository at commit 9a2fb34 (`fetch_base.py`). The job checks that this file is public on
GitHub before the analysis starts.

## What I already know (all of v1 and v2)

Same data, folds and 3,000 pooled test mixtures as v1/v2. Pooled RMSE: constant C0 0.2943,
untrained floor F1 0.2722, G1 (132 features, other-site vessels) 0.2694, G1L (absolute level +
floor share only) 0.2342, G1T (G1 with randomised vessel spectra) 0.2463, G0 (same-site vessels)
0.1928. On windows with nothing added, G1L's RMSE is 0.285 (bias +0.234) and G1T's is 0.193
(+0.126). On windows with share > 0.5, G1L's is 0.250 (-0.187) and G1T's is 0.350 (-0.298). By
vessel fold, G1T wins SB01 (0.238 vs 0.241) and G1L wins SB03 (0.227 vs 0.255). I have never
broken results down by *background* site, and I have not looked at the sites' background levels.
Nothing else has been run.

## Why

The mixing rule used here and the contest's target are the same: the vessel's share of the
window's total energy. Under that rule, share = 1 - E_background / E_window exactly. So the
loudness learner only has to guess the background's energy, and it hardly depends on which vessels
it was trained with. But its guess comes from the background levels it saw in training. In v1/v2,
training and test backgrounds came from the same three recorders (days 1-8 vs 9-12). In the
contest, levels are uncalibrated, and I don't know whether test backgrounds come from the same
recorders as the unlabelled training windows. If a gain or recorder shift breaks the loudness cue,
an entrant should know before relying on it.

## Design (fixed in code)

- **IN** = v2's setting. Training backgrounds come from days 1-8 of all three sites (SB01, SB03,
  GR01). C0, G1L and G1T are refitted with v2's exact seeds and training sets.
- **B** = the average of G1L's and G1T's predictions, with no extra fitting.
- **OUT**: every test window has a background site h. For the windows with site h, C0, G1L and G1T
  are retrained on backgrounds from the other two sites only (days 1-8). They use the same other-
  site vessel passages as IN, and the shares and draws come from new fixed seeds (6000 + 10 x fold
  + site index; augmentation 7000 + ...). B is again their average. So OUT and IN are scored on the
  *identical* 3,000 test windows. F1 needs no training and is the same in both.
- Learner: scikit-learn HistGradientBoostingRegressor, 300 iterations, learning rate 0.05, seed 0,
  6,000 training mixtures per model, as in v1/v2.
- Descriptive output (not graded): each site's background window level in dB (median, 10th and 90th
  percentile, training and test days).

## Gates

- **GA, GB**: as in v1/v2. GB also needs at least two background sites.
- **GD**: IN G1L and IN G1T reproduce v2's pooled RMSE (0.23420903245117503 and
  0.24633835050771377) within 1e-6. If GD fails, the predictions are still graded, because each
  one compares estimators within this run, but the results file must say so.

## Predictions (graded by `grade3()` on the pooled 3,000 test windows unless stated)

| id | prediction | my confidence |
|---|---|---|
| R1 | IN: RMSE(B) < min(RMSE(G1L), RMSE(G1T)) | 70% |
| R2 | IN: RMSE(B) <= 0.231114 (closes >= 50% of v2's G1 -> G0 gap: 0.2694 - 0.5 x (0.2694 - 0.1928)) | 55% |
| R3 | the unseen recorder hurts loudness more: RMSE_OUT / RMSE_IN of G1L > that of G1T | 75% |
| R4 | OUT: RMSE(G1L) > RMSE(G1T) (loudness loses its lead on an unseen recorder) | 55% |
| R5 | OUT: on at least one background site, RMSE(G1L) > RMSE(C0) | 50% |
| R6 | IN: on every background site, RMSE(G1L) < RMSE(G1T) | 45% |
| R7 | RMSE(F1) < OUT RMSE(B) (the untrained floor beats the blend once the recorder is unseen) | 35% |

R4 and R5 are close to coin flips. Either answer tells an entrant something: whether to trust
loudness when the test recorder might differ.

## Limits, stated before the run

- OUT holds out one of three U.S. Atlantic sites. A site differs from the others in more than gain:
  depth, ships, biology and season (Stellwagen Bank vs Gray's Reef). So OUT is a harsh stand-in for
  a gain shift, not a measurement of the contest's real shift. If the contest's test and training
  backgrounds come from the same recorders, IN is the relevant case.
- Two vessel folds, one learner, one seed, one share distribution, calibrated levels, augmentation
  ranges from v2, untuned. An equal-weight average is the only blend tried.
- No data from the Zindi challenge are used. Nothing here is a contest submission.

## Outputs

`results3.json` (gates; per-fold, pooled and per-background-site RMSE and bias by share bin for
IN and OUT; site levels; grades), `RESULTS-vesselmix3-auto.md`, `prereg_public.json`,
`base_files.json` (SHA-256 of the fetched v1/v2 modules). A hand-read RESULTS file follows.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
