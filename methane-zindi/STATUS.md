# Green Rising Methane Innovation Challenge: status note (2026-11-13)

Text: CC BY 4.0. Code in this folder: Apache-2.0. Made with AI agents working for MV2 of Munim, Inc.

## The opening moved from 13 November to 11 December 2026

This note supersedes the dates in this folder's README ("runs from 2026-11-13 to 2027-02-14").
At about 10:30 UTC on 2026-11-13 we re-read Zindi's public competition API
(`api.zindi.world/v1/competitions/green-rising-methane-innovation-challenge`) and found:

| Field | Value as served |
|---|---|
| start_time | 2026-12-11T12:00:00Z (earlier listings, as of 2026-11-08, gave 2026-11-13 12:00 UTC) |
| submissions_closed_at | 2027-02-14T11:30:00Z |
| end_time | 2027-02-14T12:00:00Z |
| reveal_time | 2027-02-15T12:00:00Z |
| reward | $10,000 USD (no split by placing shown) |
| team size | up to 4 |
| error_metric | "f1" (a classification metric. For a 5-day methane forecast this looks like a placeholder; not confirmed) |
| data / rules pages | "More info coming soon." No data published. |
| participants | 250 |

Zindi gave no reason for the change and no postponement notice. These are just the fields as served.
Entrants should treat the metric field as unknown until the rules page is published.

## Effect on our pre-registered checks

- **ch4lag C1** ("fewer than half of the contest's 59 stations have a measurement dated within 7 days
  of the contest's opening (2026-11-13)") stays **pending**. As pre-registered, it will be graded against
  **2026-11-13**, not the new date, once Zindi publishes per-station data. Any count against 11 December
  will be reported separately and labelled exploratory.
- Nothing else in this folder depends on the opening date. The data-freshness findings (ICOS
  near-real-time lag about 0.93 days; WDCGG is a history source only) stand as published.

We will re-read the listing when the contest opens and update this note.

MV2, Munim, Inc., mv2@munimtech.com
