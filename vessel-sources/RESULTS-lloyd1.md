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
  6% to 48% of the yachts'. (See Addendum 1: the central 2.65 dB sits in a narrow dip.)
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
  (2.65 dB) a low value. This explanation was untested when this grade was written.
  `PREREGISTRATION-lloyd2.md` set out a test of it (job `lloyd-sym-v1`), and Addendum 1 grades
  that test: the explanation held.

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

## Addendum 1 (2026-10-27, run starting 21:33 UTC): the symmetry test, job `lloyd-sym-v1`

Graded against `PREREGISTRATION-lloyd2.md` word for word by AI agents working in MV2's name. No
human has checked it.

**Timing.** The pre-registration was committed at 16:01:57 UTC on 2026-10-27 (commit aedcc14),
before the job started at 16:50:57 UTC. The job finished at 16:53:44 UTC (167 s). Every step
exited 0. All 10 tests passed: 5 for `shipsim` 0.3.0 and 5 for `sym_check.py` 0.1.0. The job ran
under a 1 GB memory cap, and the runner did not record its peak.

Gravel seabed, D = 29 m, receiver 28 m deep, 30 image cycles. C is the convention correction in
dB. "Incoherent" means the same images with their powers summed.

| zs (m) | C(100 Hz) | C(7.94 kHz) | tilt | incoherent C | coherent - incoherent | equal-length pairs |
|---|---|---|---|---|---|---|
| 0.50 | -8.02 | 2.74 | 10.76 | 2.79 | -0.05 | 0 |
| 0.80 | -4.08 | 2.86 | 6.94 | 2.75 | +0.11 | 0 |
| 0.90 | -3.10 | 2.70 | 5.80 | 2.74 | -0.04 | 0 |
| 0.95 | -2.66 | 3.77 | 6.43 | 2.74 | +1.03 | 0 |
| **1.00** | **-2.24** | **0.41** | **2.65** | 2.73 | **-2.32** | **31** |
| 1.05 | -1.85 | 3.90 | 5.75 | 2.73 | +1.17 | 0 |
| 1.10 | -1.47 | 2.59 | 4.06 | 2.72 | -0.13 | 0 |
| 1.20 | -0.78 | 2.86 | 3.64 | 2.71 | +0.15 | 0 |
| 1.50 | +0.97 | 2.57 | 1.60 | 2.68 | -0.12 | 0 |

**Score: 4 of 4 predictions held, and the run condition held.**

| | Prediction | Result | |
|---|---|---|---|
| S1 | At zs = 1.00: C(7.94 kHz) = 0.41 and tilt = 2.65, both within 0.01 dB of `lloyd-check-v1`; 31 equal-length pairs at 1.00 and none elsewhere | 0.41 and 2.65; 31 pairs at 1.00, 0 at the other 8 depths | **held** |
| S2 | At zs = 1.00, coherent minus incoherent C(7.94 kHz) is -1.5 dB or lower | -2.32 dB (hand estimate about -2) | **held** |
| S3 | At zs = 0.5 and 1.5, \|coherent - incoherent\| is 0.5 dB or less | 0.05 and 0.12 dB | **held** |
| S4 | At zs = 0.9 and 1.1, C(7.94 kHz) is at least 0.5 dB above its zs = 1.00 value | +2.29 and +2.18 dB above | **held** |
| Run | Every test passes and every step exits 0, in under 10 minutes | 10 of 10 tests, 167 s | **held** |

**What follows (decided in the pre-registration).** S2, S3 and S4 held. So the low high-band C in
the central scenario, and with it the 2.65 dB central convention tilt, sits in a narrow dip caused
by the idealized model's exact symmetry. Only the zs = 1.00 m depth has equal-length image pairs,
and moving the source 5 cm either way removes the dip. A real rough sea surface would break that
symmetry at a 19 cm wavelength. The non-symmetric neighbouring depths are the better guide. From
zs = 0.8 to 1.2 m they give a convention tilt of 3.64 to 6.94 dB (4.06 and 5.80 dB at 1.1 and
0.9 m). That is 11% to 22% of the sailboats' measured tilt (32.02 dB) and 14% to 26% of the
yachts' (26.91 dB), instead of the central 8% and 10%. **The conclusion does not change:** most of
the measured high-frequency tilt is not a level-convention effect. The simulator's default
(`shipsim` 0.3.0, central scenario) stays as pre-registered. A different scenario will be chosen
only before any challenge score is seen, and the reason will be recorded.

**Not predicted (post-hoc, recorded only).** At zs = 0.95 and 1.05 m the coherent C(7.94 kHz) is
about 1 dB *above* the incoherent value (+1.03 and +1.17 dB). The paired paths differ there by
only about 0.07 m, so the pair is still partly coherent across the band, now with the opposite
sign. The dip at 1.00 m therefore sits between two small peaks, so the C at any single depth near
1 m is fragile. This is one more reason not to read too much into a single idealized depth.

Contact: MV2, Munim, Inc., mv2@munimtech.com
