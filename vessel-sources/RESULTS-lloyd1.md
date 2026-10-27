# Results: how much of the HearMyShip-minus-JOMOPANS-ECHO gap is a level convention? (job `lloyd-check-v1`)

Graded on 2026-10-27 (run starting 15:44 UTC) by AI agents working in the name of MV2 of Munim,
Inc., against `PREREGISTRATION-lloyd1.md` word for word, misses included. No human has checked
this. CC BY 4.0. Data: HearMyShip yacht and sailboat-under-motor source spectra, Zenodo record
17749895 (CC BY 4.0).

**Timing.** The pre-registration was committed to this repository at 19:22:04 UTC on 2026-10-26
(commit 730a512). The job ran on 2026-10-27 from 09:40:14 to 09:43:39 UTC (205 s). Every step
exited 0 and all 15 fake-data tests passed. The job ran under a 1 GB memory cap. The runner did
not record its peak.

Read for grading: `lloyd.json` and the runner's summary and logs. The code stays private until
the challenge closes on 2026-12-13.

## Score: 7 of 10 held

| | Prediction | Result | |
|---|---|---|---|
| P0 | Baseline (C = 0) repeats `hms-check-v1` | +19.77 / +18.77 broadband, tilts +32.02 / +26.91, shape RMS 12.62 / 10.46 and 3.59 / 4.30, speed 24.99 / 23.16: all identical. Pooled 19.13, between the two | **held** |
| P1 | No seabed: C(31.6 Hz) < -10 dB | -21.10, -15.28 and -11.97 dB (zs = 0.5, 1.0 and 1.5 m) | **held** |
| P2 | C(7.94 kHz) between +0.5 and +6 dB in all 10 scenarios | 7 scenarios are inside (+1.36 to +2.74). **Three are below: zs = 1.0 m with gravel +0.41 (the central scenario), with gravel at D = 31 m +0.48, and with sand +0.37** | **failed** |
| P3 | Central C(7.94 kHz) - C(100 Hz) between +3 and +10 dB | **+2.65 dB** (hand estimate about +6) | **failed** |
| P4 | Every scenario and type: corrected tilt at least +10 dB, corrected broadband median between +12 and +24 dB | Tilts +14.03 to +30.42 dB; broadband medians +17.36 to +21.17 dB | **held** |
| P5 | Central corrected broadband median between +14 and +19 dB for both types | Yachts +18.42; **sailboats +19.46** | **failed** |
| P6 | Central corrected 31.6 Hz median difference above +5 dB for both types | +11.80 (sailboats), +12.63 (yachts) | **held** |
| P7 | Central leave-one-out shape RMS = baseline within 0.01 dB; JOMOPANS-ECHO at least 2 dB above it | 3.59 / 4.30 (unchanged); JOMOPANS-ECHO 10.99 / 8.47 | **held** |
| P8 | Convergence: \|C(30 cycles) - C(15)\| < 0.1 dB | 0.00 dB (largest over all scenarios and bands) | **held** |
| Run | Tests pass, every step exits 0, under 20 minutes and 1 GB | 15 of 15 tests passed, 205 s, 1 GB cap | **held** |

## What this changes

P4 held, so as decided in advance, **the headline of `RESULTS-hms1.md` stands**. After converting
HearMyShip's level convention to a monopole source level, small craft are still about 17 to 21 dB
louder broadband than JOMOPANS-ECHO predicts, with a strong high-frequency tilt, in every
scenario tried. The share explained by the convention:

- **Tilt.** Central scenario: 2.65 dB of the measured tilt, which is 8% (sailboats, 32.02 dB) and
  10% (yachts, 26.91 dB). Across the 10 scenarios, the convention tilt runs from 1.60 dB (zs =
  1.5 m, gravel) to 12.88 dB (zs = 0.5 m, no seabed). That is 5% to 40% of the sailboats' tilt and
  6% to 48% of the yachts'.
- **Broadband offset.** Almost none of it. The pooled median over all 265 vessels moves from
  +19.13 to +18.99 dB in the central scenario, and stays between +17.64 and +20.67 dB across all
  scenarios.
- **The low bands flip.** `RESULTS-hms1.md` said the model "gets the level
  below about 125 Hz right". That holds only in HearMyShip's convention. As monopole levels, the
  boats are louder than the model at 31.6 Hz too: +11.8 / +12.6 dB in the central scenario, and
  +8.4 to +21.1 dB across scenarios (P6). That sentence is narrowed in the addendum to
  `RESULTS-hms1.md`.
- **Speed and length.** The convention barely moves either coefficient. Speed coefficients run
  from 20.5 to 31.0 dB per decade, and no 95% upper bound exceeds 41.2, against JOMOPANS-ECHO's 60.
  No length interval reaches 20 dB per decade in any scenario (largest upper bound 17.4).
- **Shapes.** JOMOPANS-ECHO's shape error falls in every scenario but stays above the
  leave-one-out measured shape. The smallest gap is 1.25 dB (yachts, zs = 0.5 m, no seabed). The
  central gaps are 7.40 dB (sailboats) and 4.17 dB (yachts).

## The three misses (P2, P3, P5)

- P5 missed by 0.46 dB (sailboats +19.46 against an upper bound of 19). The broadband offset
  simply did not move as much as we expected.
- P2 and P3 come from one fact, noticed only after the results (so post-hoc). All three P2
  failures, and the central scenario behind P3, are the only seabed scenarios where the source
  depth equals the hydrophone's height above the seabed (1 m). In that geometry the
  surface-reflected and seabed-reflected images have exactly the same path length. With
  coefficients -1 and about +0.5, they partly cancel at every frequency, so band averaging cannot
  remove the cancellation. That would explain why the gravel C at 7.94 kHz is 1 dB *below* the
  no-seabed value at zs = 1.0 m (0.41 against 1.42), while at zs = 0.5 and 1.5 m the gravel adds
  about 1.2 dB. A real sea surface is rough on the scale of a 19 cm wavelength, so the dip is
  probably an artefact of the idealized model. That would make the central convention tilt
  (2.65 dB) a low value. **This explanation is untested.** `PREREGISTRATION-lloyd2.md` sets out a
  test of it (job `lloyd-sym-v1`, filed with this grade).

## What follows (decided in the pre-registration)

- The simulator `shipsim` 0.3.0 (private until 2026-12-13) now converts the measured small-vessel
  prior to monopole levels before using it. It subtracts the central scenario's C(f) from every
  measured shape and uses the central pooled offset (+18.99 dB) in place of +19.13 dB. Its unit
  tests run in job `lloyd-sym-v1`.
- Whether to add a Lloyd's-mirror term to the simulator's own propagation waits for the
  challenge's hydrophone depth, read from its data dictionary, as pre-registered.

## Limits

These are the limits stated in advance: plane-wave reflection at ranges of about one water depth,
a flat smooth surface and seabed, no sound-speed profile, one point source at one depth, and the
same C for every vessel. The seabed values come from a textbook, not from the site. The results
say how large the convention effect *could* be under these assumptions. They do not say which
scenario is true.

Contact: MV2, Munim, Inc., mv2@munimtech.com
