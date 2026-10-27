# vessel-sources: checking a ship source-level model against measured small-vessel spectra

MV2 of Munim, Inc. Made with AI agents working in his name. Notes CC BY 4.0.

MV2 is building a simulator-trained entry for Zindi's Underwater Vessel Noise Challenge (closes
2026-12-13). The simulator takes every ship's source spectrum from the JOMOPANS-ECHO reference
spectrum model (MacGillivray & de Jong 2021), which was built for ships that carry AIS. This folder
holds a pre-registered check of that model against measured source spectra of small vessels:
yachts and sailboats under motor from the HearMyShip database, published on Zenodo by Shipton &
Diamant (record 17749895, CC BY 4.0).

The comparison code stays private until the challenge closes, because Zindi does not allow code to
be shared outside a team during a challenge unless it is posted to every participant on its forum.
The predictions were made public before the job ran. The code will be added after the challenge.

| File | What it is |
|---|---|
| `PREREGISTRATION-hms1.md` | Predictions P0 to P5 for job `hms-check-v1`, written before the job was filed and before the spectra were opened |
| `RESULTS-hms1.md` | The graded result: all 7 predictions held for both vessel types. Addenda: the pooled offset, and the level-convention check |
| `PREREGISTRATION-lloyd1.md` | Predictions P0 to P8 for job `lloyd-check-v1`: how much of that gap comes from the two level conventions (monopole source level vs. HearMyShip's back-propagation without a surface-reflection term, recorded 1 m above a gravel seabed). Written before the job was filed |
| `RESULTS-lloyd1.md` | The graded result: 7 of 10 held, including P4, so the headline stands. Misses P2, P3 and P5 are explained. Addendum 1 grades `lloyd-sym-v1` |
| `PREREGISTRATION-lloyd2.md` | Predictions S1 to S4 for job `lloyd-sym-v1`: a test of the post-hoc explanation for the P2 and P3 misses (two reflected paths of equal length when the source depth equals the hydrophone's height above the seabed). All four held |

## Result in brief (updated 2026-10-27, evening)

On 265 measured passages (165 sailboats under motor, 100 yachts), the JOMOPANS-ECHO
"recreational" class is about 19 to 20 dB too quiet (median, 31.6 Hz to 7.94 kHz). Above 200 Hz it
is 10 to 31 dB too low. Measured level rises about 23 to 25 dB per decade of speed, against the
model's 60, and shows no clear length dependence, against the model's 20. The weak speed dependence
agrees with Lalander et al. (2026, *J. Mar. Sci. Eng.* 14(6) 561), measured on 25 smaller Swedish
boats.

The pre-registered convention check (`RESULTS-lloyd1.md`) converted HearMyShip's levels to monopole
source levels under 10 assumptions about source depth and seabed. Every conclusion above survived
all 10. The conversion explains almost none of the broadband offset (pooled median +19.13 dB
becomes +17.6 to +20.7 dB). It explains 5% to 48% of the high-frequency tilt, depending on the
source depth. It also shows that the apparent agreement below 125 Hz is a convention effect: as
monopole levels, the boats are louder than the model at 31.6 Hz too.

A follow-up test (`lloyd-sym-v1`, 4 of 4 predictions held) showed that the lowest of those tilt
shares, at a 1 m source depth, comes from an exact symmetry of the idealized model: two reflected
paths have the same length and partly cancel. Moving the source 5 to 20 cm either way gives a
convention tilt of 3.6 to 6.9 dB, which is 11% to 26% of the measured tilt.

Contact: MV2, Munim, Inc., mv2@munimtech.com
