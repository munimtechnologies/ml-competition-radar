# Results: vesselmix-v2 (graded by hand, 2026-11-10)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0; code Apache-2.0.
Pre-registration: [PREREGISTRATION-vesselmix2.md](PREREGISTRATION-vesselmix2.md). Code:
`vessel_mix2.py` 0.2.0 on top of v1's unchanged `vessel_mix.py` 0.1.0. Machine output:
[RESULTS-vesselmix2-auto.md](RESULTS-vesselmix2-auto.md) and [results2.json](results2.json). Run:
2026-11-09 21:26-21:31 UTC in a sealed container. All 15 offline tests passed, and the
pre-registration was public on GitHub before the analysis started (`prereg_public.json`).

**Headline: 6 of 7 predictions held, and the biggest gain came from the simplest model.** The
learner given only two numbers did best: the window's overall loudness and its floor share. It
cut RMSE 20.4% below a constant and 13.1% below v1's 132-feature learner (0.234 vs 0.269), both
trained on vessels from other sites. Randomising the training vessels' spectra helped (16.3% below
the constant). Dropping the spectral-shape features made things worse, which was my one miss
(Q2). None of the variants reached the same-site learner (0.193).

## Gates

| gate | rule | result |
|---|---|---|
| GA | all three sites give 12 days, each with >= 1,000 complete minutes | **pass**: 12 days at SB01, SB03 and GR01, 1,440 of 1,440 minutes each |
| GB | >= 2 vessel sites with >= 6 passages in each pool | **pass**: SB01 (26 train / 26 test passages) and SB03 (33 / 32), as in v1 |
| GC | G1 reproduces v1's pooled RMSE 0.2694491587478854 within 1e-6 | **pass**: identical, difference 0.0 |

## Estimators (pooled over folds SB01 and SB03, 3,000 test mixtures, the same ones as in v1)

| estimator | features | RMSE | score (1 - RMSE) | vs constant | bias | RMSE share = 0 | RMSE share > 0.5 | bias share > 0.5 |
|---|---|---|---|---|---|---|---|---|
| C0 constant | - | 0.2943 | 0.7057 | - | +0.004 | 0.356 | 0.365 | -0.346 |
| F1 untrained floor | - | 0.2722 | 0.7278 | -7.5% | -0.071 | 0.266 | 0.371 | -0.343 |
| G1 other-site vessels (v1) | 132 | 0.2694 | 0.7306 | -8.4% | -0.115 | 0.173 | 0.403 | -0.359 |
| G1S no spectral shape, no level | 106 | 0.3190 | 0.6810 | +8.4% | -0.162 | 0.176 | 0.489 | -0.457 |
| **G1L loudness + floor share only** | **2** | **0.2342** | **0.7658** | **-20.4%** | **+0.007** | 0.285 | **0.250** | **-0.187** |
| G1T randomised vessel spectra | 132 | 0.2463 | 0.7537 | -16.3% | -0.086 | 0.193 | 0.350 | -0.298 |
| G1TS both | 106 | 0.3060 | 0.6940 | +4.0% | -0.138 | 0.198 | 0.462 | -0.427 |
| G0 same-site vessels (v1) | 132 | **0.1928** | **0.8072** | -34.5% | -0.046 | **0.171** | 0.265 | -0.210 |

By fold (RMSE), SB01 / SB03: G1 0.263 / 0.276; G1L 0.241 / 0.227; G1T 0.238 / 0.255; G1S
0.313 / 0.325; G0 0.210 / 0.174. G1T and G1L both beat G1 in both folds. Neither beats the other
in both: G1T wins SB01 and G1L wins SB03.

## Predictions, graded by hand (the code's `grade2()` agrees on all seven)

| id | prediction | confidence | value | held |
|---|---|---|---|---|
| Q1 | RMSE(G1T) < RMSE(G1) | 60% | 0.2463 < 0.2694 (also in both folds) | yes |
| Q2 | RMSE(G1S) < RMSE(G1) | 55% | 0.3190 > 0.2694 | **no** |
| Q3 | the best of G1T, G1S, G1TS closes >= 25% of the G1 -> G0 gap | 40% | G1T: (0.2694 - 0.2463) / (0.2694 - 0.1928) = 0.0231 / 0.0767 = 0.301 | yes |
| Q4 | G0 beats every G1 variant | 85% | 0.1928 < G1L 0.2342, G1T 0.2463, G1TS 0.3060, G1S 0.3190 | yes |
| Q5 | RMSE(G1L) < RMSE(C0) | 75% | 0.2342 < 0.2943 | yes |
| Q6 | RMSE(G1L) < RMSE(G1) | 50% | 0.2342 < 0.2694 | yes |
| Q7 | the best of G1T/G1S/G1TS has mean bias below -0.20 on share > 0.5 | 70% | G1T: -0.298 (n = 1,019) | yes |

## What it means for an entrant

1. **Under this mixing rule, loudness is the cue that carries over between vessel sources.** v1 and
   the contest both define the target as the vessel's share of the window's total energy. When a
   vessel is scaled to carry share s, the window's energy becomes E_bg / (1 - s), whatever the
   vessel sounds like. So share = 1 - E_bg / E_window exactly, and the only unknown is the
   background's energy. A learner that sees only the overall level and the floor share hardly
   depends on which vessels it was trained with. That is why it beat the 132-feature learner, which
   also had both numbers but leaned on its training vessels' spectral signature instead. (This
   explanation was written after the run. It follows from the mixing code but was not
   pre-registered.)
2. **Randomising the training vessels' spectra also helps.** It closed 30% of the gap and was the
   better model in fold SB01. Its errors fall on different windows from the loudness model's. The
   loudness model over-predicts on windows with nothing added (bias +0.234; RMSE 0.285 vs 0.193)
   and is much better on vessel-dominated windows (0.250 vs 0.350). That suggests combining them.
   The next study tests this.
3. **Q2's miss is partly my design.** G1S removed the spectral shape *and* the absolute level,
   because both shift with a constant gain offset. G1L shows the level is the strongest feature
   that carries over between sites. So G1S lost its best cue along with the shape, and this run
   cannot separate the two effects. Treat "removing shape hurts" as unproven.

## Caveats

- **The loudness cue needs a predictable background level.** Here the test backgrounds come from
  the same three recorders (later days) as the training backgrounds, and SanctSound levels are
  calibrated. The contest's levels are uncalibrated. Its unlabelled training windows and its test
  windows are both "real South African background", but I have not seen whether they come from the
  same recorders. If test backgrounds come from a recorder or gain the entrant has never seen,
  loudness may fail. The next study measures exactly that.
- Two Stellwagen Bank vessel sites, one learner, one seed, one share distribution, and augmentation
  ranges I guessed and did not tune. Nothing here used Zindi data or is a contest submission.

## Next

[PREREGISTRATION-vesselmix3.md](PREREGISTRATION-vesselmix3.md) tests two things. First, whether
averaging the loudness and randomised-spectrum learners beats both. Second, how each holds up
when the test backgrounds come from a recorder site that no training background came from.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
