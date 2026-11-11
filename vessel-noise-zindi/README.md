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

**Start here:** [WRITEUP-vessel.md](WRITEUP-vessel.md) pulls the studies below into one guide for
entrants (an identity that reduces the task to estimating the background, how to validate, and
which cues carry over to new vessels and new recorders).

| study / note | question | status |
|---|---|---|
| [vesselmix-v1](PREREGISTRATION-vesselmix.md) | How well do a constant, an untrained background floor and a learner trained on synthetic mixtures recover the added-vessel share? How much does it cost when training vessels come from a different site than test vessels? | [graded 2026-11-09](RESULTS-vesselmix.md): 6 of 7 held. Other-site learner only 8.4% below a constant (RMSE 0.269 vs 0.294); same-site learner 34.5% below (0.193). The error sits in vessel-dominated windows |
| [vesselmix-v2](PREREGISTRATION-vesselmix2.md) | Can an entrant close that gap without knowing the organisers' vessels: no spectral-shape features, randomised vessel spectra, or loudness alone? | [graded 2026-11-10](RESULTS-vesselmix2.md): 6 of 7 held. Loudness + floor share alone (2 features) 20.4% below a constant (0.234), beating the 132-feature learner; randomised vessel spectra 16.3% below (0.246); dropping spectral shape (and level) hurt (0.319) |
| [vesselmix-v3](PREREGISTRATION-vesselmix3.md) | Does the loudness cue survive a background recorder never seen in training, and does averaging the loudness and randomised-spectrum learners help? | [graded 2026-11-10](RESULTS-vesselmix3.md): 5 of 7 held. Known recorder: the average is best so far (0.225, 23.5% below a constant). Unseen recorder: every trained model is worse than the constant (0.359-0.374 vs 0.294); only the untrained floor keeps its edge (0.272) |
| [vesselmix-v4](PREREGISTRATION-vesselmix4.md) | Do the learners keep their gain on an unseen recorder once the absolute level, the one input a gain offset moves, is removed? | [graded 2026-11-10](RESULTS-vesselmix4.md): 5 of 7 held. No: the gain-invariant 131-feature learner still collapsed on the unseen recorder (0.372 vs constant 0.294), so the shift is not a gain shift. A learned floor-share calibration was stable (0.265 known, 0.277 unseen) but did not beat the untrained floor (0.272) |
| [vesselmix-v5](PREREGISTRATION-vesselmix5.md) | Does training on more recorders (up to 16 of 21 SanctSound deployments) shrink the unseen-recorder penalty, and is the shift mainly between sites or between deployments? | [graded 2026-11-11](RESULTS-vesselmix5.md): 6 of 7 held. Yes, if a similar site is among them: with 16 other recorders the blend scored 0.237 on an unseen recorder (20.0% below a constant, 17.1% below the untrained floor), and hearing the test recorder itself added little (0.230). Trained only on the other two sites, it lost to the constant again (0.307; Gray's Reef 0.367) |
| [DATA-ACCESS.md](DATA-ACCESS.md) | Which vessel-recording sources can an entrant actually use? Access and licence for ONC, HearMyShip, SanctSound, DeepShip, ShipsEar and the VTUAD rebuild | checked 2026-11-09: ONC needs a token (HTTP 401), HearMyShip's data licence unconfirmed, SanctSound open with no account; VTUAD rebuild (CC BY 4.0, 525 clips) open on Zenodo. Update 2026-11-10: VTUAD's vessel clips are short (median 5 min; AIS interval median 3 min; only 7 of 487 reach the contest's 15-minute window) |
| [WRITEUP-vessel.md](WRITEUP-vessel.md) | What should an entrant do, given all of the above? | version 3, 2026-11-11 |

Files:
- `vessel_mix.py` 0.1.0: downloads 12 days of 1-minute SanctSound HMD spectra and ship detections
  at SB01, SB03 and GR01, converts them to the contest's 25 bands, builds known-answer mixtures,
  and scores the four estimators leave-one-vessel-site-out. Needs numpy, scikit-learn and netCDF4
  (`requirements.txt`).
- `vessel_mix2.py` 0.2.0: reuses `vessel_mix.py` unchanged, reproduces v1's folds and test
  mixtures, and adds four learner variants (G1S, G1L, G1T, G1TS).
- `vessel_mix3.py` 0.3.0: reuses both unchanged (`fetch_base.py` downloads them from commit
  9a2fb34), reproduces v2's G1L and G1T, and adds their average and a held-out background-site
  setting.
- `vessel_mix4.py` 0.4.0: runs v3's analysis function unchanged (`fetch_base4.py` downloads v1-v3
  from commit 2c4e55b), reproduces v3's IN and OUT numbers, and adds two learners without the
  absolute level (G1F, G1TI).
- `vessel_mix5.py` 0.5.0: treats deployments 01-07 of GR01, SB01 and SB03 as 21 background
  recorders and retrains the v3/v4 learners on 1 to 16 of them for each held-out recorder
  (`fetch_base5.py` downloads v1-v3 from commit 2c4e55b). About 1.4 GB of extra downloads.
- `test_vessel_mix.py` to `test_vessel_mix5.py`:
  offline tests (band conversion, mixing, floor estimator, features, pools, augmentation, feature
  subsets, gain invariance, grading, a netCDF round trip, small synthetic end-to-end runs).
- `wait_public.py`: refuses to start an analysis until its pre-registration is public.
- `RESULTS-vesselmix-auto.md`, `results.json`, and the same pair for v2 to v5
  (`RESULTS-vesselmix5-auto.md`, `results5.json`): machine output. `base_files4.json`,
  `base_files5.json`, `prereg_public4.json` and `prereg_public5.json`: each run's hash check of
  the downloaded earlier code and its proof that the pre-registration was public first.

Run: `pip install -r requirements.txt && python -m unittest -v test_vessel_mix test_vessel_mix2 test_vessel_mix3 test_vessel_mix4 && python vessel_mix.py --data-dir data --out-dir out && python vessel_mix2.py --data-dir data --out-dir out && python vessel_mix3.py --data-dir data --out-dir out && python vessel_mix4.py --data-dir data --out-dir out`
(about 550 MB of downloads, reused by the later scripts). v5 runs on its own:
`python fetch_base5.py base_files5.json && python -m unittest -v test_vessel_mix5 && python vessel_mix5.py --data-dir data --out-dir out`
(about 1.4 GB more).

**Lessons so far for entrants:**
1. Validate on a held-out vessel *source*, not on held-out passages from your own training
   vessels. With a source mismatch, v1's learner gave up most of its gain.
2. When the target is the vessel's share of the window's energy, the window's loudness relative to
   its expected background carries over between vessel sources better than spectral detail does
   (v2).
3. Trained on only two recorders, every trained model lost to the constant on a third (v3), and
   removing gain-sensitive inputs did not help (v4): recorders differ in background shape and
   variability, not only in gain.
4. Pool many recorders (v5). With 16 training recorders the penalty on an unseen recorder mostly
   disappeared, as long as recorders from a similar site were among them. A site unlike every
   training site still broke the trained models; the floor share (learned or untrained) was the
   safe choice there.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here. Nothing in this folder
uses Zindi's data or is a contest submission.
