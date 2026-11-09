# Vessel-recording sources for the Underwater Vessel Noise Challenge: access and licence, checked 2026-11-09

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0.

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
| **Ocean Networks Canada (ONC)**, Oceans 3.0 | cabled hydrophones off British Columbia (e.g. Strait of Georgia); WAV/FLAC audio and a 1/3-octave spectral product (`dataProductCode=HSD`, `extension=oct`) | **API needs a free account token**: `https://data.oceannetworks.ca/api/locations?locationCode=SCVIP` without a token returned HTTP 401 | CC BY 4.0 for data solely owned by ONC; partner-owned data may be more restrictive ([data policy](https://www.oceannetworks.ca/data/data-policy/)) | no (account) |
| **HearMyShip** | over 1,500 small-vessel passages by its authors' count (yachts, motorboats, sailboats) in Croatia's Krka estuary, with video and 1/3-octave levels ([site](https://hearmyship.fer.hr/); raw data [doi:10.57760/sciencedb.13099](https://doi.org/10.57760/sciencedb.13099); code doi:10.57760/sciencedb.13532) | the web catalogue loads without a login; the ScienceDB landing page is rendered by script and showed no file list or licence to a plain fetch | **not confirmed**. The site footer says "All rights reserved"; the paper (Scientific Data, 2025) is CC BY-NC-ND 4.0, which covers the article, not necessarily the data | not yet (licence unconfirmed; small boats only) |
| **NOAA / U.S. Navy SanctSound** | U.S. sanctuary hydrophones; 1-minute hybrid millidecade spectra (HMD) plus labelled ship-passage detections | public Google Cloud bucket `noaa-passive-bioacoustic`, no account (used by [vesselmix-v1](PREREGISTRATION-vesselmix.md)) | no explicit licence; NCEI asks for the citation "NOAA Office of National Marine Sanctuaries and U.S Navy. 2023", doi:10.25921/ymf8-5k59, and disclaims warranty ([metadata](https://doi.org/10.25921/ymf8-5k59)) | **yes**. It is not named in the contest rules, so an entrant should declare it and confirm with the organisers before training on it |
| DeepShip | 47 h of ship audio from 265 ships in four classes, recorded at ONC's Strait of Georgia node, 2016-2018 ([GitHub](https://github.com/irfankamboh/DeepShip)) | part of the audio is in the GitHub repo; the rest is on request from the author by email | no licence file in the repo | no (no licence; partial) |
| ShipsEar | Spanish coastal vessel recordings (Applied Acoustics, 2016) | the Zenodo record (14570052) holds only the article PDF; the audio is distributed by the authors' university site | not checked for the audio | not checked |

## What this means for an entry

- The two sources the rules name are the hard ones: ONC needs an account, and HearMyShip's data
  licence could not be confirmed by a plain fetch. A browser visit to the ScienceDB page, or a
  question to the authors, would settle the second.
- SanctSound is the only one of the five that is fully open with no account. It also comes with
  ship-passage labels, which neither the contest nor the other sources supply in this form. The
  rules say "including", which reads as a non-exhaustive list, but that is our reading. Declare it
  and ask on the challenge's discussion board before using it.
- Vessel mismatch is the open question: South African test vessels come from an unknown source.
  vesselmix-v1 measures what a site mismatch costs on SanctSound (pre-registered, queued).

Nothing here uses Zindi's data or is a contest submission. MV2 does not yet have a Zindi account.
