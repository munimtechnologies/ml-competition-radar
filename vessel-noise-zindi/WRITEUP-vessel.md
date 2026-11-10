# When you can't hear the organisers' ships: what carries over in the Underwater Vessel Noise Challenge

Version 2, 2026-11-10 (version 1 the same day; version 2 adds study 4 in section 6). MV2 of
Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0; code Apache-2.0. Every
number below comes from pre-registered studies on public NOAA/U.S. Navy SanctSound data in
[vessel-noise-zindi](https://github.com/munimtechnologies/ml-competition-radar/tree/main/vessel-noise-zindi).
No Zindi data were used, and nothing here is a contest submission.

## 1. The problem every entrant has

Zindi's [Underwater Vessel Noise Challenge](https://zindi.africa/competitions/french-embassy-underwater-vessel-noise-challenge)
asks, for each 15-minute window (25 third-octave bands, one value per minute), what share of the
window's sound energy comes from a vessel passage mixed into a real South African background. The
training windows are unlabelled and the organisers supply no vessel recordings. So every entrant
builds labelled mixtures from vessel audio of their own, and the organisers' vessels will differ
from those.

The question that decides the leaderboard is therefore not "which model fits my mixtures best?"
but "what does my model learn that still holds for vessels I have never heard?" Studies 3 and 4
add a second question: what still holds on a recorder I have never heard?

## 2. An identity that changes the problem

With background energy E_bg and added vessel energy E_v, each summed over the window's bands and
minutes (as in the proxy's mixing code, `vessel_mix.mix`), the target is
s = E_v / (E_bg + E_v). Rearranged:

    s = 1 - E_bg / E_window

E_window is observed. So **the whole task reduces to estimating the background's energy under the
vessel**. The vessel's spectrum enters only through E_window, which you measure directly. Three
consequences:

1. A model that leans on the training vessels' spectral signature learns something the identity
   says it does not need, and that something changes with the vessel source.
2. The useful features describe the background: its floor, its usual level for this recorder,
   band and time of day, and how far the window's level rises above that.
3. Errors are largest where the vessel dominates (s > 0.5). There E_window is mostly vessel, so
   the background must be inferred from context, and a floor estimate taken inside the window
   absorbs vessel energy.

I worked this out after the second study, from the mixing code. It was not a pre-registered
prediction, but it explains the results of all four studies.

## 3. Validate on a held-out vessel source

Study [vesselmix-v1](https://github.com/munimtechnologies/ml-competition-radar/blob/main/vessel-noise-zindi/RESULTS-vesselmix.md)
built 3,000 known-answer test mixtures from SanctSound backgrounds (Stellwagen Bank SB01 and SB03,
Gray's Reef GR01) and vessel passages from SB01 and SB03. A gradient-boosting learner with 132
features was trained twice:

| training vessels | RMSE | vs constant (0.2943) |
|---|---|---|
| same site as the test vessels (G0) | 0.1928 | -34.5% |
| other site (G1, the entrant's real situation) | 0.2694 | -8.4% |

Validating on held-out passages from your own vessel source overstated the gain about fourfold. In
one fold the other-site learner was worse than an untrained floor estimator. 89% of G1's extra
squared error came from windows with s > 0.5.

**Recipe:** hold out a whole vessel source (a site, recorder or dataset), never just passages.

## 4. Fewer, mechanism-chosen features beat many

Study [vesselmix-v2](https://github.com/munimtechnologies/ml-competition-radar/blob/main/vessel-noise-zindi/RESULTS-vesselmix2.md)
kept v1's test mixtures and changed only the learner's inputs or training vessels:

| learner (other-site vessels) | features | RMSE | vs constant | RMSE s = 0 | RMSE s > 0.5 |
|---|---|---|---|---|---|
| G1 (v1) | 132 | 0.2694 | -8.4% | 0.173 | 0.403 |
| G1L: window level + floor share | 2 | **0.2342** | **-20.4%** | 0.285 | **0.250** |
| G1T: G1 with randomised vessel spectra | 132 | 0.2463 | -16.3% | 0.193 | 0.350 |
| G0 (same-site, ceiling) | 132 | 0.1928 | -34.5% | 0.171 | 0.265 |

The two-feature learner beat the 132-feature learner, as section 2 predicts: level relative to
the floor is the cue that carries over between vessel sources. Randomising the training vessels'
spectra (a random tilt of up to ±6 dB per decade, an independent ±2 dB gain per band, and random
time reversal) also helped, because it stops the learner keying on one fleet's signature. The two
fail on different windows: loudness over-predicts on windows with nothing added (bias +0.234),
while the randomised learner under-predicts on vessel-dominated ones.

## 5. A failed ablation, and why it can't be read

v2 also tried dropping spectral-shape features (G1S, RMSE 0.319, worse than the constant). But
the variant also dropped the absolute level, so it removed two things at once. G1L shows level is
the best cue that carries over between vessel sources, so G1S lost it along with the shape. The
result says nothing about shape on its own. **An ablation must remove one thing.** Study 4 does
that (section 6).

## 6. Every trained model breaks on a recorder you have never heard

The loudness cue needs to know the background's usual level. In v1 and v2 the test backgrounds
came from the same three recorders as the training backgrounds (later days). The contest's levels
are uncalibrated, so a recorder or gain difference between its training and test windows is
plausible. Studies [vesselmix-v3](https://github.com/munimtechnologies/ml-competition-radar/blob/main/vessel-noise-zindi/RESULTS-vesselmix3.md)
(5 of 7 pre-registered predictions held) and
[vesselmix-v4](https://github.com/munimtechnologies/ml-competition-radar/blob/main/vessel-noise-zindi/RESULTS-vesselmix4.md)
(5 of 7 held) scored every model twice on the same 3,000 test windows: IN, with training
backgrounds from all three recorders, and OUT, retrained without any background from the test
window's recorder. v4 added two learners that remove only the absolute level, the one input a gain
offset moves; a unit test confirms a +10 dB shift leaves their predictions bit-for-bit unchanged.

| estimator | IN RMSE | vs constant | OUT RMSE | vs constant |
|---|---|---|---|---|
| C0 constant | 0.2943 | - | 0.2944 | - |
| F1 untrained floor share | 0.2722 | -7.5% | **0.2722** | **-7.5%** |
| G1L level + floor share | 0.2342 | -20.4% | 0.3587 | +21.9% |
| G1T randomised spectra (132 features) | 0.2463 | -16.3% | 0.3744 | +27.2% |
| B = average of G1L and G1T | **0.2251** | **-23.5%** | 0.3592 | +22.0% |
| G1F = G1L without level (floor share only, learned) | 0.2647 | -10.1% | 0.2770 | -5.9% |
| G1TI = G1T without level (131 gain-free features) | 0.2885 | -2.0% | 0.3719 | +26.3% |

- **Recorder known:** averaging the two learners is the best model found without same-site
  vessels. It closes 58% of the gap between the other-site and same-site learners. The absolute
  level carries much of that: without it, the 131-feature learner falls from 0.246 to 0.289.
- **Recorder unseen:** every trained model with more than one input is worse than the constant.
  On windows with nothing added, they predict a vessel where there is none (mean error +0.41 to
  +0.45). Holding out Gray's Reef, whose backgrounds are 6-12 dB louder than Stellwagen's, was the
  worst case (G1L 0.469), but even between the two Stellwagen recorders G1L fell from 0.260 to
  0.291, against a constant at 0.294 and the floor at 0.284.
- **It is not a gain problem.** After v3 I guessed that the 132-feature learner failed because it
  leaned on loudness. v4 refuted that: the gain-invariant G1TI collapsed just as badly (0.372). Its
  inputs ignore gain but still describe the background's shape and variability, which differ
  between recorders, so an unfamiliar background looks like vessel energy.
- **Calibrating the floor share is stable but does not travel.** G1F lost only 5% between IN and
  OUT, but on the unseen recorder it did not beat the untrained floor (0.277 vs 0.272), and on one
  Stellwagen recorder it was worse than the constant (0.303 vs 0.293).

**What the contest page says (read 2026-11-10 through Zindi's public API):** the unlabelled
training release holds records from ten South African monitoring sites. The test file holds 1,500
synthetic examples of 375 values (25 bands x 15 minutes). "The background periods used for the
test are excluded from the training release." Test windows carry no station or timestamp, and
"absolute pressure calibration has not been independently verified". The page does not say whether
the test backgrounds come from the same ten sites. If they do, the contest is closer to IN (known
recorders, unseen days), with ten recorders instead of three and no site label at test time. The
rules forbid fitting or calibrating on test inputs but allow fixed per-window transformations, so
gain-free features such as the floor share are allowed. About 30% of test examples score the
public leaderboard and 70% the private one.

**Recipe:** find out whether the test windows come from the training recorders. If they do, use
loudness and the blend. If you cannot tell, removing gain-sensitive inputs is not enough: check
every model on a held-out recorder, and keep the untrained floor share as the fallback. With ten
training sites, pooling many recorders may shrink the unseen-recorder penalty; that is the next
study, not yet a result.

## 7. Checklist for an entrant

1. Build mixtures with the contest's own target definition, then check s = 1 - E_bg/E_window
   on your mixtures as a unit test. The contest pools the share over all observed minute-band
   cells in linear energy, as the proxy does. Blank cells are missing, not silence, so sum only
   the observed ones.
2. Spend your modelling effort on the background: per-band floors, per-recorder typical levels,
   and level above floor. Treat vessel spectral detail as a nuisance and randomise it.
3. Validate twice: leave one vessel source out, and leave one background recorder out. Report RMSE
   and bias by target bin (s = 0, 0 to 0.5, s > 0.5), not just overall RMSE.
4. Check whether the test windows' recorders match the unlabelled training windows' before
   trusting any trained model. A model can beat the constant by 20% on known recorders and lose to
   it by 20% on an unseen one, and gain-invariant features do not prevent that.
5. A zero target does not mean a vessel-free background. In v1, backgrounds with a labelled ship
   drew higher predictions on windows with nothing added. Some of that error cannot be removed.
6. Pre-register what you expect before each run, so a validation score you like can't quietly
   become your model choice. Two of my own post-hoc readings (v2's shape ablation, v3's loudness
   explanation) were wrong, and only a pre-registered follow-up showed it.

## 8. Limits

- U.S. Atlantic sites with calibrated levels. The contest's data are South African and
  uncalibrated.
- Two vessel folds, one learner (HistGradientBoostingRegressor), one seed, one share distribution,
  and augmentation ranges guessed rather than tuned. Tuning a proxy without contest data overfits
  the proxy.
- The held-out recorders differ in more than gain (depth, ships, biology, season), and the OUT
  models trained on two recorders' backgrounds instead of three, so OUT is harsher than a ten-site
  contest is likely to be.
- SanctSound vessel windows include their own site's ambient sound, so part of G0's advantage may
  be a site fingerprint.

Reproduce: each study's `vessel_mix*.py`, offline tests and `wait_public.py` (which refuses to run
an analysis before its pre-registration is public) are in the folder above. Later studies load
earlier code unchanged from a pinned commit, and each one first reproduces the previous study's
numbers exactly.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed.
