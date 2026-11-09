# Vessel-recording sources for the Underwater Vessel Noise Challenge: access and licence, checked 2026-11-09

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0.

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
