# Results: vesselmix-v5 (graded by hand, 2026-11-11)

MV2 of Munim, Inc. (made with AI agents working in his name). Text CC BY 4.0; code Apache-2.0.
Pre-registration: [PREREGISTRATION-vesselmix5.md](PREREGISTRATION-vesselmix5.md). Code:
`vessel_mix5.py` 0.5.0 on `vessel_mix.py` 0.1.0, `vessel_mix2.py` 0.2.0 and `vessel_mix3.py` 0.3.0,
downloaded from commit 2c4e55b (`fetch_base5.py`; all three matched the SHA-256 recorded by the v4
run, see `base_files5.json`). Machine output: [RESULTS-vesselmix5-auto.md](RESULTS-vesselmix5-auto.md)
and [results5.json](results5.json). Run: 2026-11-10 21:04-22:07 UTC in a sealed container (peak
memory 0.78 GB). All 12 offline tests passed. The pre-registration was public on GitHub before the
analysis started, and the public copy matched the local one byte for byte (`prereg_public5.json`,
seen 21:07:24Z).

**Headline: 6 of 7 predictions held. The unseen-recorder collapse in v3 and v4 came mostly from
training on too few recorders.** With backgrounds from 16 other recorders, the blend B scored RMSE
0.237 on a recorder it had never heard, 20.0% below a constant (0.296) and 17.1% below the untrained
floor share (0.286). Having also heard the test recorder added little (0.230). But the gain needs a
*similar site* among the training recorders: trained only on the other two sites, every multi-input
learner was again worse than the constant (B 0.307), and at Gray's Reef, whose backgrounds are about
10 dB louder than Stellwagen's, it lost badly (0.367 vs 0.293). The one-input learned floor share
G1F was the only trained model that beat the untrained floor in every pooled condition with 4 or
more recorders and at all three sites under SALL.

## Gates

| gate | rule | result |
|---|---|---|
| base files | v1-v3 code from commit 2c4e55b matches the v4 run's SHA-256 | **pass** (all three) |
| GA | >= 15 usable recorders, >= 4 per site | **pass** (21: GR01 7, SB01 7, SB03 7; each 288 training and 192 test windows) |
| GB | both vessel folds have >= 6 passages in each pool | **pass** (SB01 26/26, SB03 33/32) |
| GC | every condition exists for every usable recorder | **pass** (all 10 conditions x 21 recorders) |

Median training level per recorder: GR01 125.9-131.4 dB, SB01 113.9-124.9 dB, SB03 109.0-120.2 dB.

## Pooled RMSE (4,200 test mixtures: 21 held-out recorders x 2 vessel folds x 100)

Dn = n other recorders from any site (nested); S1/S4/SALL = recorders from the other two sites
only; SAME = the other 6 deployments of the test recorder's site only; IN16 = the test recorder's
own training days plus 15 others.

| condition | C0 | F1 | G1F | G1L | G1T | B |
|---|---|---|---|---|---|---|
| D1 | 0.2963 | 0.2859 | 0.2921 | 0.3620 | 0.3692 | 0.3211 |
| D2 | 0.2964 | 0.2859 | 0.2792 | 0.3331 | 0.3628 | 0.3002 |
| D4 | 0.2964 | 0.2859 | 0.2770 | 0.2949 | 0.2719 | 0.2514 |
| D8 | 0.2963 | 0.2859 | 0.2733 | 0.2532 | 0.2571 | 0.2382 |
| **D16** | 0.2964 | 0.2859 | 0.2709 | 0.2461 | 0.2621 | **0.2371** |
| S1 | 0.2964 | 0.2859 | 0.3099 | 0.4199 | 0.4418 | 0.3781 |
| S4 | 0.2964 | 0.2859 | 0.2805 | 0.3637 | 0.3466 | 0.3431 |
| SALL | 0.2963 | 0.2859 | 0.2761 | 0.3076 | 0.3316 | 0.3071 |
| SAME | 0.2964 | 0.2859 | 0.2680 | 0.2600 | 0.2417 | 0.2328 |
| IN16 | 0.2965 | 0.2859 | 0.2694 | 0.2435 | 0.2489 | 0.2303 |

C0 = training mean share; F1 = untrained floor share (no training, so identical in every row);
G1F = learned floor share; G1L = level + floor share; G1T = 132 features, randomised vessel spectra;
B = (G1L + G1T) / 2.

By target bin (D16 vs SALL, B): windows with nothing added RMSE 0.229 (bias +0.186) vs 0.391
(+0.338); vessel-dominated windows (share 0.5-0.9) 0.313 vs 0.297. F1: 0.301 (+0.245) and 0.373.
So the extra recorders mainly stop the learners from reading an unfamiliar background as a vessel.

### By site of the held-out recorder (RMSE)

| condition | model | GR01 | SB01 | SB03 |
|---|---|---|---|---|
| any | F1 | 0.2520 | 0.3082 | 0.2944 |
| D1 | B | 0.3748 | 0.3122 | 0.2673 |
| D16 | G1L | 0.2047 | 0.2582 | 0.2703 |
| D16 | B | **0.1686** | **0.2659** | **0.2636** |
| SALL | G1L | 0.3701 | 0.2633 | 0.2786 |
| SALL | B | 0.3668 | 0.2703 | 0.2746 |
| SALL | G1F | **0.2462** | 0.2967 | 0.2829 |
| SAME | B | 0.1259 | 0.2852 | 0.2558 |
| IN16 | B | 0.1595 | 0.2570 | 0.2600 |

(SALL, GR01: C0 0.2932, G1L bias +0.249.) Descriptive trend: G1L's RMSE is lower at D16 than at
D1 on 17 of the 21 held-out recorders.

## Predictions, graded by hand (the code's `grade5()` agrees on all seven)

| id | prediction | confidence | value | held |
|---|---|---|---|---|
| T1 | G1L: RMSE(D16) < RMSE(D1) | 80% | 0.2461 < 0.3620 | yes |
| T2 | D16: RMSE(G1L) < RMSE(C0) | 50% | 0.2461 < 0.2964 | yes |
| T3 | D16: RMSE(B) < RMSE(F1) | 40% | 0.2371 < 0.2859 | yes |
| T4 | RMSE(D1)/RMSE(D16) larger for G1T than for G1L | 55% | G1T 0.3692/0.2621 = 1.409; G1L 0.3620/0.2461 = 1.471 | **no** |
| T5 | G1L: RMSE(SAME) < RMSE(SALL) | 70% | 0.2600 < 0.3076 | yes |
| T6 | G1L: RMSE(IN16) < RMSE(D16) | 70% | 0.2435 < 0.2461 | yes, by 0.0026 (a tie) |
| T7 | D16: RMSE(G1F) < RMSE(F1) | 50% | 0.2709 < 0.2859 | yes |

## What it means

1. **More recorders fix most of the unseen-recorder penalty (T1-T3).** v3/v4 trained on two
   recorders and every trained model lost to the constant. Here the same learners lose at D1 and D2,
   break even around D4, and from D8 on beat both the constant and the untrained floor. My
   pre-registered confidence in T3 was 40%; it held clearly.
2. **But the recorders must include the test recorder's kind of site (T5).** SAME (six other
   deployments of the same site) beat SALL (fourteen recorders from the other two sites) for every
   multi-input learner. Under SALL the Stellwagen recorders were fine (each had the other Stellwagen
   site in training), and Gray's Reef failed: its backgrounds are about 10 dB louder, outside
   anything the learners had seen. D16's random draw almost always included some GR01 deployments,
   which is why GR01 was the best site under D16 (B 0.169).
3. **Hearing the exact recorder adds little once you have heard its site (T6 a tie).** IN16 vs D16:
   0.230 vs 0.237 for B, 0.2435 vs 0.2461 for G1L. Deployments of one site differ in season and
   instrument; pooling them was enough here.
4. **The 132-feature learner did not gain more from diversity (T4 failed).** G1T improved fastest
   from D2 to D4 but then stalled (D8 0.257, D16 0.262); G1L kept improving. Read as: one seed,
   no tuning; not a mechanism.
5. **The learned floor share is the safest trained model (T7).** G1F beat F1 at D2 and above and
   under SALL at all three sites (GR01 0.246 vs 0.252, SB01 0.297 vs 0.308, SB03 0.283 vs 0.294), unlike v4 where it lost on one Stellwagen recorder
   after training on two.

**For an entrant.** Zindi's unlabelled training release covers ten South African sites; the page
does not say whether test backgrounds come from those sites. If they do, this proxy says: pool all
ten sites and use the blend (here 20% below a constant on an unseen deployment). If test sites may
be new, the risk is a site whose level and texture lie outside the training sites' range; there a
trained multi-input model can still lose to a constant, and the learned or untrained floor share is
the safe choice. Ten sites span far more variety than the two used here, so that risk is likely
smaller in the contest, but this proxy cannot measure it.

## Closest prior work found

Spadon, Renaud and Aravindan ([arXiv 2609.26125](https://arxiv.org/abs/2609.26125)) show that
deployments of the same station can differ and recommend validating by station for unseen-station
claims, for vessel-*presence* detection. ONCship ([arXiv 2610.19722](https://arxiv.org/abs/2610.19722))
compares adding recordings from the same vs different hydrophone stations for vessel-*type*
recognition. A search on 2026-11-11 found no open measurement of how the unseen-recorder penalty
of vessel *energy-share* regression shrinks with the number of training recorders, or of the
site-vs-deployment split shown here.

## Caveats

- Three U.S. Atlantic sites, two on the same bank; deployments differ in season and instrument and
  the two cannot be separated. Calibrated levels; the contest's are not verified.
- 3 training and 2 test days per recorder; one random recorder order per held-out recorder; two
  vessel folds from deployment 01 only; one learner and seed; v2's untuned augmentation. T6 held
  by 0.0026, inside what a different seed could move.
- In deployment 01, test backgrounds and test vessel passages can come from the same days of the
  same recorder, as in v1.
- No Zindi data were used, and nothing here is a contest submission.

## Next

The proxy studies stop here unless the contest says whether its test backgrounds come from its
training sites. The write-up (section 6) now carries the decision rule above.

Data credit: NOAA Office of National Marine Sanctuaries and U.S. Navy, SanctSound, NCEI (HMD
product doi:10.25921/ymf8-5k59). Used as published, not redistributed here.
