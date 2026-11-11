# When you can't hear the organisers' ships: what carries over in the Underwater Vessel Noise Challenge

Version 3, 2026-11-11 (version 1 and 2 on 2026-11-10; version 3 adds study 5 in section 6 and
changes its recipe). MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0;
code Apache-2.0. Every number below comes from pre-registered studies on public NOAA/U.S. Navy
SanctSound data in
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
but "what does my model learn that still holds for vessels I have never heard?" Studies 3 to 5
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
prediction, but it explains the results of all five studies.

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

## 6. New recorders: train on many, and on similar sites

The loudness cue needs to know the background's usual level. In v1 and v2 the test backgrounds
came from the same three recorders as the training backgrounds (later days). The contest's levels
are uncalibrated, so a recorder or gain difference between its training and test windows is
plausible.

**Two training recorders are not enough (v3, v4).** Studies
[vesselmix-v3](https://github.com/munimtechnologies/ml-competition-radar/blob/main/vessel-noise-zindi/RESULTS-vesselmix3.md)
and [vesselmix-v4](https://github.com/munimtechnologies/ml-competition-radar/blob/main/vessel-noise-zindi/RESULTS-vesselmix4.md)
(5 of 7 pre-registered predictions held in each) scored every model on the same 3,000 test
windows: IN, with training backgrounds from all three recorders, and OUT, retrained without the
test window's recorder.

| estimator | IN RMSE | vs constant | OUT RMSE | vs constant |
|---|---|---|---|---|
| C0 constant | 0.2943 | - | 0.2944 | - |
| F1 untrained floor share | 0.2722 | -7.5% | **0.2722** | **-7.5%** |
| G1L level + floor share | 0.2342 | -20.4% | 0.3587 | +21.9% |
| G1T randomised spectra (132 features) | 0.2463 | -16.3% | 0.3744 | +27.2% |
| B = average of G1L and G1T | **0.2251** | **-23.5%** | 0.3592 | +22.0% |
| G1F = G1L without level (floor share only, learned) | 0.2647 | -10.1% | 0.2770 | -5.9% |
| G1TI = G1T without level (131 gain-free features) | 0.2885 | -2.0% | 0.3719 | +26.3% |

On the unseen recorder every multi-input model predicted a vessel where there was none (mean error
+0.41 to +0.45 on windows with nothing added). v4 showed this is **not a gain problem**: G1TI,
unaffected by a gain offset by construction (a unit test checks +10 dB), collapsed just as badly.
Recorders differ in the shape and variability of their backgrounds, not only in gain.

**Many recorders mostly fix it (v5).** Study
[vesselmix-v5](https://github.com/munimtechnologies/ml-competition-radar/blob/main/vessel-noise-zindi/RESULTS-vesselmix5.md)
(6 of 7 held) treated deployments 01-07 of the three sites as 21 recorders. For each held-out
recorder it retrained the same learners on n other recorders (Dn), on recorders of the other two
sites only (SALL), on the other deployments of the same site only (SAME), or on 15 others plus
the test recorder's own earlier days (IN16). 4,200 test mixtures:

| training backgrounds | C0 | F1 | G1F | G1L | B |
|---|---|---|---|---|---|
| D1 (1 other recorder) | 0.296 | 0.286 | 0.292 | 0.362 | 0.321 |
| D4 | 0.296 | 0.286 | 0.277 | 0.295 | 0.251 |
| D16 (16 other recorders) | 0.296 | 0.286 | 0.271 | 0.246 | **0.237** |
| SALL (14, other two sites only) | 0.296 | 0.286 | 0.276 | 0.308 | 0.307 |
| SAME (6, same site only) | 0.296 | 0.286 | 0.268 | 0.260 | 0.233 |
| IN16 (test recorder heard) | 0.297 | 0.286 | 0.269 | 0.244 | 0.230 |

- With 16 other recorders, B on an unseen recorder was 20.0% below the constant and close to its
  score with the test recorder heard (0.237 vs 0.230).
- Without the test recorder's site, it lost to the constant again (SALL 0.307). The failure sat at
  Gray's Reef (B 0.367 vs constant 0.293), whose backgrounds are about 10 dB louder than any
  Stellwagen recorder's. The Stellwagen recorders were fine under SALL (B 0.270 and 0.275 vs the
  floor's 0.308 and 0.294), because the other Stellwagen site was in training.
- The learned floor share G1F beat the untrained floor at every site under SALL (GR01 0.246 vs
  0.252), so it is the safest trained model found.

**What the contest page says (read 2026-11-10 through Zindi's public API):** the unlabelled
training release holds records from ten South African monitoring sites. The test file holds 1,500
synthetic examples of 375 values (25 bands x 15 minutes). "The background periods used for the
test are excluded from the training release." Test windows carry no station or timestamp, and
"absolute pressure calibration has not been independently verified". The page does not say whether
the test backgrounds come from the same ten sites. The rules forbid fitting or calibrating on test
inputs but allow fixed per-window transformations, so gain-free features such as the floor share
are allowed. About 30% of test examples score the public leaderboard and 70% the private one.

**Recipe:** pool backgrounds from all ten training sites and use the blend of the loudness and
randomised-spectrum learners. If the test backgrounds come from those sites, this proxy expects a
gain of about 20% over a constant even for unseen periods or deployments. If a test site may be
unlike every training site (much louder or quieter, a different habitat), a trained multi-input
model can still lose to a constant; keep the floor share (learned on all sites, or untrained) as
the fallback. Asking the organisers whether test backgrounds come from the ten training sites is
worth more than any further tuning.

## 7. Checklist for an entrant

1. Build mixtures with the contest's own target definition, then check s = 1 - E_bg/E_window
   on your mixtures as a unit test. The contest pools the share over all observed minute-band
   cells in linear energy, as the proxy does. Blank cells are missing, not silence, so sum only
   the observed ones.
2. Spend your modelling effort on the background: per-band floors, per-recorder typical levels,
   and level above floor. Treat vessel spectral detail as a nuisance and randomise it.
3. Validate three ways: leave one vessel source out, leave one recorder out, and leave one whole
   site out. Report RMSE and bias by target bin (s = 0, 0 to 0.5, s > 0.5), not just overall RMSE.
4. Train on backgrounds from as many recorders and sites as you have. In the proxy, two recorders
   gave models worse than a constant on a new one; sixteen gave a 20% gain. Gain-invariant
   features alone do not prevent the collapse.
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
- Only three sites, two on the same bank, so v5's "unseen site" case has little site diversity in
  training; ten contest sites likely cover more. Deployments differ in season as well as
  instrument, and the two cannot be separated.
- SanctSound vessel windows include their own site's ambient sound, so part of G0's advantage may
  be a site fingerprint.

Reproduce: each study's `vessel_mix*.py`, offline tests and `wait_public.py` (which refuses to run
an analysis before its pre-registration is public) are in the folder above. Later studies load
earlier code unchanged from a pinned commit and check it by SHA-256.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed.
