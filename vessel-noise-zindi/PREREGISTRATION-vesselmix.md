# Pre-registration: vesselmix-v1

Can you tell how much of a 15-minute underwater sound window comes from an added vessel passage,
and how much does it cost when your training vessels come from a different place than the test
vessels? An account-free public proxy for Zindi's Underwater Vessel Noise Challenge.

MV2 of Munim, Inc. (made with AI agents working in his name). Written 2026-11-09 before the job
ran and before any SanctSound spectrum was opened. Code: `vessel_mix.py` 0.1.0 in this folder
(Apache-2.0). The job checks that this file is public on GitHub before it starts the analysis.

## Why

Zindi's [Underwater Vessel Noise Challenge](https://zindi.africa/competitions/french-embassy-underwater-vessel-noise-challenge)
($5,000; closes 2026-12-13; open to all) gives 15-minute windows of 25 third-octave levels
(31.6 Hz to 7.94 kHz, one value per minute) and asks for `share_added_vessel`: the fraction of the
window's total energy that comes from a recorded vessel passage that the organisers mixed into a
real South African background. The score is 1 - RMSE. Its training data are **unlabelled**, so an
entrant has to build labelled examples themselves: mix vessel passages from permitted public
corpora (the rules name Ocean Networks Canada and HearMyShip) into the unlabelled backgrounds and
train on that. The organisers' own vessel recordings are unknown. The contest's data need a Zindi
account, which MV2 does not yet have. So this study asks the same question on public data that
need no account.

## Data (public, no account)

NOAA Office of National Marine Sanctuaries and U.S. Navy **SanctSound**, public Google Cloud bucket
`noaa-passive-bioacoustic`:
- 1-minute hybrid millidecade spectra (HMD product, PSD in dB re 1 uPa^2/Hz, 1-Hz bins to 435 Hz,
  then millidecade bins to 24 kHz), `sound_level_metrics/<site>/sanctsound_<site>_01_hmd/data/*.nc`;
- SanctSound's ship-passage detections (`ISOStartTime,ISOEndTime,Labels`),
  `detections/<site>/sanctsound_<site>_01_ships/data/*.csv`.

Sites: **SB01 and SB03** (Stellwagen Bank, Massachusetts) and **GR01** (Gray's Reef, Georgia),
deployment 01 each. Of the 10 sites I checked (CI01, FK01, GR01, GR02, GR03, HI01, MB01, SB01,
SB02, SB03; SanctSound lists 31), these were the only three that publish 1-minute HMD files; the
others offer hourly levels only. The other 21 sites were not checked. Days: the 2nd to
the 13th daily HMD file in name order (12 days; the first is a partial deployment day).

## Method (fixed in code)

1. Each HMD minute is converted to the contest's 25 base-10 third-octave bands (centres 10^(n/10),
   n = 15..39; edges x10^(+-0.05)) by summing PSD x bin width over bins whose centre falls in the
   band. Minutes with a missing value in any used bin are dropped.
2. **Backgrounds**: every complete 15-minute window on a 15-minute grid. Days 1-8 give training
   backgrounds and days 9-12 test backgrounds, pooled over all three sites. Backgrounds are NOT
   filtered by ship labels, as in the contest, where a zero target "does not mean the original
   background is vessel-free".
3. **Vessel passages**: for each SanctSound ship detection, the 15-minute window centred on its
   midpoint, kept if complete and carrying at least 3 dB more energy than the site's median window.
   In time order, passages alternate train / test (even index train, odd index test).
4. **Mixtures**: background B plus vessel V scaled by g so that V carries exactly the target share
   s of the window's total linear energy (all bands, all minutes). s = 0 with probability 0.25,
   else uniform on [0.05, 0.90]. 1,500 test mixtures per fold (as in Test.csv), 6,000 training
   mixtures per learner per fold; fixed seeds.
5. **Folds**: one per *vessel site* with at least 6 passages in each pool. In fold k, test vessels
   are site k's test passages; test backgrounds are days 9-12 of all sites.
6. **Estimators**:
   - **C0**: a constant, the mean share of G1's training mixtures.
   - **F1**: untrained floor. Per band, background = 15 x the lowest 3-minute running mean of
     linear power; share = 1 - sum(background) / sum(total), clipped to [0, 1]. (This is the
     low-percentile background idea used in vessel-noise work, e.g. the 5th-percentile background
     around closest approach, cut down to one 15-minute window.)
   - **G1**: scikit-learn HistGradientBoostingRegressor (300 iterations, learning rate 0.05,
     seed 0) on 132 features (per-band spectral shape, range, SD and excess over the floor;
     per-minute broadband profile, raw and sorted; absolute level; F1). Trained on mixtures whose
     vessels are the **training passages of the other sites** (the entrant's position).
   - **G0**: the same learner, trained on mixtures whose vessels are **site k's own training
     passages** (other passages from the same source as the test vessels).
   G0 and G1 are scored on the same test mixtures.

## Gates

- **GA**: all three sites give 12 days, each with at least 1,000 complete minutes.
- **GB**: at least two vessel sites (each with 6 or more passages in both pools).
If either gate fails, no prediction is graded; the counts are still published.

What I have seen beforehand: bucket listings (file names and sizes), the HMD metadata record for
SB01 deployment 01, and the first lines of the SB01 and GR01 ship-detection files. GR01 has only
94 detections in its whole first deployment, about 20 of them in the 12 chosen days, so GR01 may well
fail the 6+6 passage rule and serve only as a background site and as a source of G1 training
vessels. That would still pass GB with folds SB01 and SB03. Those two are both Stellwagen Bank
sites, so their vessel sources differ less than an entrant's would.

## Predictions (graded by `grade()` in the code, on the pooled test mixtures)

| id | prediction | my confidence |
|---|---|---|
| P1 | RMSE(G1) <= 0.6 x RMSE(C0) | 70% |
| P2 | RMSE(F1) < RMSE(C0) | 50% |
| P3 | RMSE(G1) < RMSE(F1) | 90% |
| P4 | RMSE(G0) < RMSE(G1) in every fold, and pooled RMSE(G1) / RMSE(G0) >= 1.10 | 55% |
| P5 | mean F1 on share-0 windows > 0.05 (the floor sits below the mean of a fluctuating background) | 85% |
| P6 | mean (F1 - share) on windows with share >= 0.5 is < 0 (a passage fills most of the window, so the floor holds vessel energy) | 75% |
| P7 | on share-0 test windows, within a site, G1's mean prediction is higher when the background window overlaps a labelled ship detection; holds if true at most sites with >= 20 windows in each group (ungraded if no site qualifies) | 70% |

For scale: with this share distribution a constant scores RMSE of about 0.30 (a score of 0.70);
the contest's public constant benchmark is 0.7539 (RMSE about 0.246), so its share distribution
differs from mine. The comparisons between estimators are the point, not the absolute RMSE.

## Limits, stated before the run

- SanctSound vessel windows are real recordings that include their own background, so "vessel
  energy" here is the whole passage window, which is probably also true of the organisers' clips.
  At 3 dB above the median window, up to half a passage window can be background.
- U.S. Atlantic sites, not South African ones; calibrated levels, while the contest's are
  uncalibrated; no missing cells in my windows, while Test.csv has blank cells.
- One learner, one seed, one share distribution. P4 measures site mismatch between two sites on the
  same bank, a weak version of an entrant's real mismatch.
- No data from the Zindi challenge are used or needed. Nothing here is a contest submission.

## Outputs

`results.json` (counts, per-fold and pooled RMSE and bias by share bin, gate details, grades),
`RESULTS-vesselmix-auto.md`, `prereg_public.json`. A hand-read RESULTS file follows the run.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI
(HMD product doi:10.25921/ymf8-5k59). Data are used as published and not redistributed here.
