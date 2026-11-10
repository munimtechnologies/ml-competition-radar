# Vessel-recording sources for the Underwater Vessel Noise Challenge: access and licence, checked 2026-11-09

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0.

## Update, 2026-11-10: VTUAD clip lengths (a census of the rebuild's metadata)

A sealed job (`vtuad_meta.py` 0.1.0, stdlib only, 6 offline tests passed; 2026-11-10 05:52-05:55
UTC) downloaded only the metadata of the VTUAD rebuild v1.3.3
([Zenodo 23773305](https://doi.org/10.5281/zenodo.23773305)): `metadata.csv` (166,858 bytes,
SHA-256 7fcc57dd...), `clip_acoustic_stats.csv` (151,117 bytes, 06393af9...) and
`dataset_card.md`. No audio was downloaded. Counts only:

| label | clips | clip length, median (max) | AIS interval, median (max) | clips with >= 15 min | hours | distinct MMSI |
|---|---|---|---|---|---|---|
| tug | 188 | 5.0 min (23 min) | 4 min (23 min) | 6 | 18.8 | 56 |
| cargo | 97 | 5.0 (12) | 3 (12) | 0 | 8.5 | 45 |
| passenger ship | 71 | 3.0 (9) | 2 (8) | 0 | 5.5 | 10 |
| other | 40 | 4.0 (13) | 3 (13) | 0 | 3.5 | 8 |
| fishing | 34 | 6.0 (18) | 4 (18) | 1 | 3.5 | 21 |
| pleasure craft | 32 | 5.0 (13) | 3 (13) | 0 | 2.8 | 18 |
| dredger | 8 | 7.0 (8) | 2 (3) | 0 | 0.7 | 1 |
| sailing | 6 | 5.5 (8) | 4 (6) | 0 | 0.6 | 5 |
| tanker | 5 | 7.0 (8) | 2 (4) | 0 | 0.6 | 4 |
| rescue | 4 | 5.5 (14) | 5.5 (14) | 0 | 0.5 | 3 |
| pilot vessel | 2 | 4.5 (7) | 2 (2) | 0 | 0.2 | 1 |
| **all vessel clips** | **487** | **5.0 (23)** | **3 (23)** | **7** | **45.2** | **172** |
| background | 38 | 8.0 (37) | 5 (37) | 16 | 10.8 | 7 |

What this means for an entrant:

- **Most VTUAD passages are much shorter than the contest's 15-minute window.** Only 7 of 487
  vessel clips cover a full window. A VTUAD passage mixed into a 15-minute background occupies a
  few minutes, so its energy is concentrated in time. SanctSound passages in the vesselmix studies
  fill the whole window. If the contest's vessels are also brief passes, short clips are realistic.
  Either way, a model trained on one kind and tested on the other faces a second shift besides the
  vessel source.
- **Clip length is not the vessel's time in range.** For 161 vessel clips the clip runs exactly
  300 s past the AIS interval, which matches the record's own warning about container excess (it
  recommends its strict-interval WAVs). 311 match the interval exactly, and 15 differ by other
  amounts.
- **Few distinct hulls behind the small classes:** dredger 1 MMSI, pilot vessel 1, tanker 4. A
  cross-source study should hold out whole hulls (the record also ships
  `vtuad_v2_hulldisjoint.json`).
- **Counts differ from the record's summary.** `metadata.csv` labels 38 clips "background" and 487
  as vessels (525 total). The record's description says 509 single-vessel scenarios and 16
  backgrounds. We report what the file holds and have not resolved the difference.
- `clip_acoustic_stats.csv` adds per-clip levels in dBFS (uncalibrated), spectral centroid, three
  broad band levels, frame-level percentiles, spectral flux and AIS speed over ground. These are
  broad-band figures, not the contest's 25 third-octave bands. A cross-source study would still
  need to convert the WAVs.

Machine output: `CENSUS-vtuad-auto.md` and `census.json` from the job (not republished here). The
data are the record's (CC BY 4.0, attribution to Ocean Networks Canada and the rebuild's authors).

## Update, 2026-11-09 about 19:50 UTC: an open, account-free ONC vessel set exists (VTUAD rebuild on Zenodo)

The table below said ONC needs an account. That is true of ONC's own API, but an open
**rebuild of VTUAD** (Vessel-Type Underwater Acoustic Data) made from ONC's archive is on Zenodo
with no account:

- **Record:** "VTUAD: An AIS-Auto-Labeled Vessel-Type Underwater Acoustic Dataset Reconstructed
  from Ocean Networks Canada Archives", by Hao Yuan and Wenbo Wang (Wuhan University of Science
  and Technology). Concept DOI [10.5281/zenodo.22274549](https://doi.org/10.5281/zenodo.22274549);
  latest version v1.3.3, [10.5281/zenodo.23773305](https://doi.org/10.5281/zenodo.23773305),
  published 2026-10-30. This is a third-party reconstruction, not the original 2022 VTUAD of
  Domingos, Skelton and Santos (IEEE DataPort, doi:10.21227/msg0-ag12, whose licence we did not check).
- **Licence:** Zenodo lists `cc-by-4.0`, access open. The record's `license_evidence_v131.md`
  (compiled 2026-09-29) says the hydrophone audio is ONC-operated and released under CC BY 4.0
  with ONC attribution; raw AIS messages are **not** redistributed (only derived intervals and
  MMSI/UTC metadata), and a partner notice added later on an ONC dataset page would take precedence.
- **What it holds:** 525 clips (509 single-vessel scenarios in 11 AIS-derived vessel types + 16
  background recordings), about 56 h of 32 kHz mono WAV, from **one** ONC icListen hydrophone
  (ICLISTENAF2523, Strait of Georgia, British Columbia), May 2016 to May 2017; per-clip UTC
  interval, MMSI, vessel dimensions and CTD covariates; no range-to-vessel labels.
- **Sizes:** per-class WAV zips from 69 MB (pilot vessel) and 253 MB (tanker) up to 8.7 GB (tug);
  the "strict-interval" WAVs (all 525 clips re-cut to the exact AIS interval, added in v1.3.0) are
  3 x 1.24 GB for vessels plus 0.93 GB for background.
- **A caveat the record states itself:** in the original per-class containers, 184 clips run 300 s
  past the labelled AIS interval, and for 167 of them the tail re-reads audio from before
  `utc_begin`. The record recommends the strict-interval WAVs for label-strict work.
- **Use in the contest:** the rules name ONC among allowed declared public corpora. On 2026-11-09
  two participants posted external-data declarations on the challenge's discussion board citing
  VTUAD v1.3.2 (one also HearMyShip V1). Those are participant posts; no organiser had replied.

Why it matters: Zindi supplies no vessel clips, and [vesselmix-v1](RESULTS-vesselmix.md) found that
a learner trained on vessels from other SanctSound sites kept only a small edge over the constant
benchmark. VTUAD adds vessels from a different ocean, hydrophone model and operator, which makes a
true cross-**source** check possible (train on one source, test on the other). We have not
downloaded or used it yet; any such study will be pre-registered first, after vesselmix-v2 is graded.

## Original check (2026-11-09, about 02:30-03:30 UTC)

Zindi's [Underwater Vessel Noise Challenge](https://zindi.africa/competitions/french-embassy-underwater-vessel-noise-challenge)
ships unlabelled South African backgrounds and **no vessel recordings and no synthetic training
set**, so every entrant has to bring vessel passages from somewhere. Its rules (as embedded in
Zindi's public API, 2026-11-09) allow training on "released South African data and declared public
corpora, including ONC and HearMyShip", and ask entrants to disclose source URLs, versions,
preprocessing and access requirements. This page records what one real request to each candidate
source showed on 2026-11-09 (about 02:30-03:30 UTC). It is a dated check, not legal advice. Each
source's own terms win.

| source | what it is | access found | licence found | usable for an account-free proxy? |
|---|---|---|---|---|
| **Ocean Networks Canada (ONC)**, Oceans 3.0 | cabled hydrophones off British Columbia (e.g. Strait of Georgia); WAV/FLAC audio and a 1/3-octave spectral product (`dataProductCode=HSD`, `extension=oct`) | **API needs a free account token**: `https://data.oceannetworks.ca/api/locations?locationCode=SCVIP` without a token returned HTTP 401 | CC BY 4.0 for data solely owned by ONC; partner-owned data may be more restrictive ([data policy](https://www.oceannetworks.ca/data/data-policy/)) | no (account), **but see the VTUAD update above** |
| **HearMyShip** | over 1,500 small-vessel passages by its authors' count (yachts, motorboats, sailboats) in Croatia's Krka estuary, with video and 1/3-octave levels ([site](https://hearmyship.fer.hr/); raw data [doi:10.57760/sciencedb.13099](https://doi.org/10.57760/sciencedb.13099); code doi:10.57760/sciencedb.13532) | the web catalogue loads without a login; the ScienceDB landing page is rendered by script and showed no file list or licence to a plain fetch | **not confirmed**. The site footer says "All rights reserved"; the paper (Scientific Data, 2025) is CC BY-NC-ND 4.0, which covers the article, not necessarily the data | not yet (licence unconfirmed; small boats only) |
| **NOAA / U.S. Navy SanctSound** | U.S. sanctuary hydrophones; 1-minute hybrid millidecade spectra (HMD) plus labelled ship-passage detections | public Google Cloud bucket `noaa-passive-bioacoustic`, no account (used by [vesselmix-v1](PREREGISTRATION-vesselmix.md)) | no explicit licence; NCEI asks for the citation "NOAA Office of National Marine Sanctuaries and U.S Navy. 2023", doi:10.25921/ymf8-5k59, and disclaims warranty ([metadata](https://doi.org/10.25921/ymf8-5k59)) | **yes**. It is not named in the contest rules, so an entrant should declare it and confirm with the organisers before training on it |
| **VTUAD rebuild (ONC-derived)** (added 19:50 UTC) | 525 AIS-labelled clips from one ONC hydrophone, Strait of Georgia, 2016-2017 ([Zenodo](https://doi.org/10.5281/zenodo.22274549)) | Zenodo, no account | CC BY 4.0 (Zenodo record; ONC attribution) | **yes** (see update above) |
| DeepShip | 47 h of ship audio from 265 ships in four classes, recorded at ONC's Strait of Georgia node, 2016-2018 ([GitHub](https://github.com/irfankamboh/DeepShip)) | part of the audio is in the GitHub repo; the rest is on request from the author by email | no licence file in the repo | no (no licence; partial) |
| ShipsEar | Spanish coastal vessel recordings (Applied Acoustics, 2016) | the Zenodo record (14570052) holds only the article PDF; the audio is distributed by the authors' university site | not checked for the audio | not checked |

## What this means for an entry

- The two sources the rules name were the hard ones at 03:30 UTC: ONC's API needs an account, and
  HearMyShip's data licence could not be confirmed by a plain fetch. The VTUAD rebuild (update
  above) is an open route to ONC audio. A browser visit to the ScienceDB page, or a question to the
  authors, would settle HearMyShip.
- SanctSound and the VTUAD rebuild are both open with no account. SanctSound comes with
  ship-passage labels on 1-minute spectra; VTUAD comes with AIS-labelled raw audio. SanctSound is
  not named in the rules ("including" reads as a non-exhaustive list, but that is our reading), so
  declare it and ask on the challenge's discussion board before using it.
- Vessel mismatch is the open question: South African test vessels come from an unknown source.
  vesselmix-v1 measured what a site mismatch costs on SanctSound ([results](RESULTS-vesselmix.md)).

Nothing here uses Zindi's data or is a contest submission. MV2 does not yet have a Zindi account.
