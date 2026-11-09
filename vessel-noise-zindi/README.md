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

| study | question | status |
|---|---|---|
| [vesselmix-v1](PREREGISTRATION-vesselmix.md) | How well do a constant, an untrained background floor and a learner trained on synthetic mixtures recover the added-vessel share? How much does it cost when training vessels come from a different site than test vessels? | pre-registered 2026-11-09, 7 predictions; queued |

Files:
- `vessel_mix.py` 0.1.0: downloads 12 days of 1-minute SanctSound HMD spectra and ship detections
  at SB01, SB03 and GR01, converts them to the contest's 25 bands, builds known-answer mixtures,
  and scores the four estimators leave-one-vessel-site-out. Needs numpy, scikit-learn and netCDF4
  (`requirements.txt`).
- `test_vessel_mix.py`: offline tests (band conversion, mixing, floor estimator, features, pools,
  grading, a netCDF round trip, a small synthetic end-to-end run).
- `wait_public.py`: refuses to start the analysis until the pre-registration is public.

Run: `pip install -r requirements.txt && python -m unittest -v test_vessel_mix && python vessel_mix.py --data-dir data --out-dir out`
(about 550 MB of downloads).

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here. Nothing in this folder
uses Zindi's data or is a contest submission.
