# Pre-registration: how much of the HearMyShip-minus-JOMOPANS-ECHO gap is a level convention? (job `lloyd-check-v1`)

Written on 2026-10-26 (run starting 19:06 UTC) by AI agents working in the name of MV2 of Munim,
Inc., before job `lloyd-check-v1` was filed. Nothing in it has been computed yet, and no human
has checked it. CC BY 4.0. The code stays private until Zindi's Underwater Vessel Noise Challenge
closes on 2026-12-13, as with `hms-check-v1`. The model is specified below in full so that anyone
can rebuild it.

## Why

`RESULTS-hms1.md` found that measured HearMyShip levels of 265 yachts and sailboats under motor
(Zenodo 17749895, CC BY 4.0) sit 18.8 to 19.8 dB above the JOMOPANS-ECHO "recreational" class
broadband (median), with a tilt of +32.0 dB (sailboats) and +26.9 dB (yachts) between 100 Hz and
7.94 kHz. That file named the main caveat. The two sets of numbers are not in the same convention:

- JOMOPANS-ECHO was fitted to **monopole** source levels from the ECHO program (MacGillivray &
  de Jong 2021, *J. Mar. Sci. Eng.* 9(4) 369, abstract).
- HearMyShip adds Erbe's simplified shallow-water loss, TL = 20 log10 D + 10 log10(R/D), at the
  mean CPA range of 39 m, to the received PSD. It applies no surface-reflection term (Shipton et al.
  2025, *Sci. Data* 12:289; Shipton & Diamant 2026, *Front. Mar. Sci.* 13:1759355). Its recorder
  was mounted 1 m above the seabed at 29 m depth, on a seabed "primarily of fine gravel". CPA
  ranges were 29 to 49 m.

A source just below a pressure-release surface radiates as a dipole, so received low-frequency
levels fall well below a monopole's. A hydrophone 1 m above a reflective seabed adds a
near-in-phase bottom path. Both effects change with frequency, so part of the reported tilt, and
some of the offset, may come from the convention rather than from the boats.

## The model (lloyd.py 0.1.0)

HearMyShip level = monopole SL + C(f), with C(f) = 10 log10 <|p|^2> + TL_Erbe(R = 39 m, D = 29 m)
= 10 log10 <|p|^2> + 30.53 dB.

- p is the complex pressure at the hydrophone from a unit monopole (|p| = 1 at 1 m). It is summed
  over images in an isovelocity layer (c = 1500 m/s, depth D). The surface is pressure-release
  (R = -1). The seabed is a fluid half-space with the plane-wave Rayleigh coefficient (Jensen et
  al., *Computational Ocean Acoustics*, sect. 1.6). The images, for n = 0..30, have vertical offsets
  2Dn + zr - zs (n surface, n seabed hits), 2Dn + zr + zs (n+1, n), 2D(n+1) - zr - zs (n, n+1) and
  2D(n+1) - zr + zs (n+1, n+1). Each has amplitude (-1)^surface x R_b(theta)^seabed / r and phase
  k r.
- Seabeds (Jensen et al. Table 1.3, textbook values, not measured at the site): gravel 1800 m/s,
  density 2.0, 0.6 dB per wavelength; sand 1650 m/s, 1.9, 0.8 dB per wavelength; "none" keeps only
  the direct path and the surface image (two-path Lloyd's mirror).
- <> is the mean of |p|^2 over three things: the integer-Hz bins that `hms_check.band_levels`
  sums for each band; 11 equally spaced track positions inside the ISO 17208-1 +/-30 degree
  window (along-track offset +/- s tan 30 degrees); and CPA slant ranges s = 29, 34, 39, 44 and
  49 m.
- Receiver depth zr = D - 1 m. Scenarios: source depth zs = 0.5, 1.0 or 1.5 m, each with gravel,
  sand or no seabed, at D = 29 m (9 scenarios); plus zs = 1.0 m, gravel, D = 31 m (the depth given
  in the Frontiers paper). **Central scenario: zs = 1.0 m, gravel, D = 29 m.**
- Each vessel's measured band levels minus C are compared with JOMOPANS-ECHO by the unchanged
  `hms_check.compare` (median differences, broadband, tilt, shape RMS, speed and length fit). A
  baseline with C = 0 is run as well. `pooled_broadband_median` is the median broadband difference
  over all 265 vessels.

Limits fixed in advance: plane-wave reflection coefficients at ranges of about one water depth,
a flat seabed, no sound-speed profile, one point source at one depth, the same C for every
vessel, and the 31.6 Hz band lies just above the waveguide cut-off (about 23 Hz for this
seabed).

## Hand estimates behind the predictions

Two-path, zs = 1 m, at the 39 m CPA: path difference 1.41 m. C(31.6 Hz) is about -16.7 dB at that
CPA alone, and about -15.4 dB over all five CPA ranges, because nearer passages count more.
C(100 Hz) is about -5.7 dB, and C(7.94 kHz) about +1.5 dB (incoherent). The gravel path near the
hydrophone adds about 3.5 dB at low frequency and lifts the incoherent sum to about +3 to +4 dB. That
gives a central C(7.94 kHz) - C(100 Hz) of about +6 dB, and about +13 dB for zs = 0.5 m with no
seabed, the largest of the scenarios.

## Predictions

- **P0, reproduction.** The baseline (C = 0) repeats `hms-check-v1` exactly: broadband medians
  +19.77 (sailboats) and +18.77 (yachts); tilts +32.02 and +26.91; JOMOPANS shape RMS 12.62 and
  10.46; leave-one-out shape RMS 3.59 and 4.30; speed coefficients 24.99 and 23.16. The pooled
  baseline median lies between 18.77 and 19.77.
- **P1, low-band dipole.** In the three no-seabed scenarios, C(31.6 Hz) < -10 dB.
- **P2, high band.** In all 10 scenarios, C(7.94 kHz) lies between +0.5 and +6 dB.
- **P3, size of the convention tilt.** In the central scenario, C(7.94 kHz) - C(100 Hz) lies
  between +3 and +10 dB.
- **P4, the headline survives.** In all 10 scenarios and for both vessel types, the corrected
  tilt is at least +10 dB, and the corrected broadband median lies between +12 and +24 dB.
- **P5, central broadband.** In the central scenario, the corrected broadband median lies between
  +14 and +19 dB for both types.
- **P6, low band reverses.** In the central scenario, the corrected median difference at 31.6 Hz
  is above +5 dB for both types. In other words, once the convention is removed, the boats are
  louder than the model at the lowest band too.
- **P7, shapes.** In the central scenario, the leave-one-out shape RMS equals the baseline within
  0.01 dB, because C is the same for every vessel and every band is present. JOMOPANS-ECHO's shape
  RMS stays at least 2 dB above it, for both types.
- **P8, convergence.** Over all scenarios and bands, |C(30 image cycles) - C(15)| < 0.1 dB.
- **Run.** Every test passes and every step exits 0, in under 20 minutes and under 1 GB.

## What follows (decided now)

- If P4 holds, `RESULTS-hms1.md` gets an addendum. The headline stands, and the share of the tilt
  and offset that the convention explains is reported, with the central value and the range over
  scenarios.
- If P4 fails in any scenario, the addendum says that the tilt or offset claim depends on the
  source depth and seabed, names the scenarios, and narrows the published claim to match.
- Simulator: when `shipsim` draws measured HearMyShip shapes or the measured offset as a
  **monopole** source (its propagation has no surface image), it will first subtract the central
  scenario's C. Whether to add a Lloyd's-mirror term to the simulator's own propagation is decided
  only after the challenge's hydrophone depth is read from its data dictionary, and never from
  test windows.

Contact: MV2, Munim, Inc., mv2@munimtech.com
