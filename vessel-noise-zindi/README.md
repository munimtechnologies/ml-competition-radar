# vessel-noise-zindi

Open, account-free preparation by MV2 of Munim, Inc. for Zindi's
[Underwater Vessel Noise Challenge](https://zindi.africa/competitions/french-embassy-underwater-vessel-noise-challenge)
($5,000, including two $1,000 write-up prizes; closes 2026-12-13). Made with AI agents working in
his name. Code Apache-2.0; text CC BY 4.0.

The challenge asks what share of a 15-minute window's sound energy (25 third-octave bands, one
value per minute) comes from a vessel passage mixed into a real background. Its training data are
unlabelled, so entrants have to build their own labelled mixtures from vessel recordings the
organisers don't supply. Zindi's data need an account, which MV2 does not have yet. So this folder
asks the same question on NOAA/U.S. Navy SanctSound data, which anyone can download.

| study / note | question | status |
|---|---|---|
| [vesselmix-v1](PREREGISTRATION-vesselmix.md) | How well do a constant, an untrained background floor and a learner trained on synthetic mixtures recover the added-vessel share? How much does it cost when training vessels come from a different site than test vessels? | [graded 2026-11-09](RESULTS-vesselmix.md): 6 of 7 held. Other-site learner only 8.4% below a constant (RMSE 0.269 vs 0.294); same-site learner 34.5% below (0.193). The error sits in vessel-dominated windows |
| [vesselmix-v2](PREREGISTRATION-vesselmix2.md) | Can an entrant close that gap without knowing the organisers' vessels: no spectral-shape features, randomised vessel spectra, or loudness alone? | pre-registered 2026-11-09, 7 predictions; queued |
| [DATA-ACCESS.md](DATA-ACCESS.md) | Which vessel-recording sources can an entrant actually use? Access and licence for ONC, HearMyShip, SanctSound, DeepShip and ShipsEar | checked 2026-11-09: ONC needs a token (HTTP 401), HearMyShip's data licence unconfirmed, SanctSound open with no account |

Files:
- `vessel_mix.py` 0.1.0: downloads 12 days of 1-minute SanctSound HMD spectra and ship detections
  at SB01, SB03 and GR01, converts them to the contest's 25 bands, builds known-answer mixtures,
  and scores the four estimators leave-one-vessel-site-out. Needs numpy, scikit-learn and netCDF4
  (`requirements.txt`).
- `vessel_mix2.py` 0.2.0: reuses `vessel_mix.py` unchanged, reproduces v1's folds and test
  mixtures, and adds four learner variants (G1S, G1L, G1T, G1TS).
- `test_vessel_mix.py`, `test_vessel_mix2.py`: offline tests (band conversion, mixing, floor
  estimator, features, pools, augmentation, feature subsets, grading, a netCDF round trip, small
  synthetic end-to-end runs).
- `wait_public.py`: refuses to start an analysis until its pre-registration is public.
- `RESULTS-vesselmix-auto.md`, `results.json`: v1's machine output.

Run: `pip install -r requirements.txt && python -m unittest -v test_vessel_mix test_vessel_mix2 && python vessel_mix.py --data-dir data --out-dir out && python vessel_mix2.py --data-dir data --out-dir out`
(about 550 MB of downloads, reused by the second script).

**Lesson so far for entrants:** validate on a held-out vessel *source*, not on held-out passages
from your own training vessels. With a source mismatch, v1's learner gave up most of its gain.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here. Nothing in this folder
uses Zindi's data or is a contest submission.
