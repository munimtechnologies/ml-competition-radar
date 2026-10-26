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
| `RESULTS-hms1.md` | The graded result: all 7 predictions held for both vessel types |

## Result in brief (2026-10-26)

On 265 measured passages (165 sailboats under motor, 100 yachts), the JOMOPANS-ECHO
"recreational" class matches the measured median below about 125 Hz. Above 200 Hz it is 10 to
31 dB too low, and across the challenge's 31.6 Hz to 7.94 kHz bands it is about 19 to 20 dB too
low (median). Measured level rises about 23 to 25 dB per decade of speed, against the model's 60.
It shows no clear length dependence, against the model's 20. The weak speed dependence agrees with
Lalander et al. (2026, *J. Mar. Sci. Eng.* 14(6) 561), measured on 25 smaller Swedish boats. The
HearMyShip levels carry no surface-reflection correction, so part of the high-frequency tilt may
come from that convention. See `RESULTS-hms1.md` for every number and its limits.

Contact: MV2, Munim, Inc., mv2@munimtech.com
