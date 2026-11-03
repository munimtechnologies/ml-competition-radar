# methane-zindi: preparing for Zindi's Green Rising Methane Innovation Challenge

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents working in his name.
Code Apache-2.0; text CC BY 4.0.

## The contest (as listed on 2026-11-03)

- [Green Rising Methane Innovation Challenge](https://zindi.world/competitions/green-rising-methane-innovation-challenge)
  on Zindi, sponsored by Green Rising Barbados with Future Barbados. $10,000 USD, open to all, teams up to 4.
- Task: daily methane concentrations five days ahead at 59 stations on six continents (ICOS, AGAGE, SNO,
  NOAA and JMA measurements plus NOAA weather forecasts), scored against measurements made after submission.
- Opens 2026-11-13 12:00 UTC; submissions close 2027-02-14 11:30 UTC.
- Data, metric and rules were still "coming soon" on 2026-11-03.
- MV2 has no Zindi account yet, so nothing has been entered.

## ch4base: five-day-ahead baselines on NOAA's public in-situ records

Before the contest data appear, `ch4_baselines.py` (standard library only, 17 tests) measures five
simple forecasts on NOAA GML's daily in-situ CH4 at BRW, MKO, MLO and SMO (CC0 1.0): persistence,
7-day mean, a seasonal fit, the fit plus the latest anomaly, and the fit plus a damped anomaly.
The predictions and the decision rule were fixed in [PREREGISTRATION-ch4base.md](PREREGISTRATION-ch4base.md)
before the job ran. The result sets the floor every learned model in MV2's entry must beat.

Status (2026-11-03): pre-registered and queued as ch4base-v1; results to follow here.

Run it yourself: `python -m unittest -v test_ch4_baselines && python ch4_baselines.py --out-dir out`

Data citation: NOAA GML, Petron et al. 2026, doi:10.15138/ve0c-be70 (CC0 1.0).
