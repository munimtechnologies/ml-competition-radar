# vessel_mix 0.1.0: automatic results

Gates: GA=True, GB=True. Vessel folds: sb01, sb03.

| site | grid windows | bg train | bg test | bg with ship | passage windows | median SNR dB | passages train/test |
|---|---|---|---|---|---|---|---|
| gr01 | 1152 | 768 | 384 | 34 | 20 | 1.0 | 2/2 |
| sb01 | 1152 | 768 | 384 | 898 | 175 | 1.3 | 26/26 |
| sb03 | 1152 | 768 | 384 | 821 | 133 | 2.5 | 33/32 |

| estimator | pooled RMSE | bias | fold sb01 | fold sb03 |
|---|---|---|---|---|
| C0 | 0.2943 | +0.0036 | 0.2934 | 0.2952 |
| F1 | 0.2722 | -0.0715 | 0.2807 | 0.2634 |
| G0 | 0.1928 | -0.0460 | 0.2102 | 0.1736 |
| G1 | 0.2694 | -0.1146 | 0.2631 | 0.2757 |

| id | prediction | held | value |
|---|---|---|---|
| P1 | pooled RMSE(G1) <= 0.6 x RMSE(C0) | False | `{"G1": 0.2694491587478854, "C0": 0.29430116814239327, "ratio": 0.915555858811666}` |
| P2 | pooled RMSE(F1) < RMSE(C0) | True | `{"F1": 0.27221869673305704, "C0": 0.29430116814239327}` |
| P3 | pooled RMSE(G1) < RMSE(F1) | True | `{"G1": 0.2694491587478854, "F1": 0.27221869673305704}` |
| P4 | RMSE(G0) < RMSE(G1) in every fold and pooled RMSE(G1)/RMSE(G0) >= 1.10 | True | `{"every_fold": true, "pooled_ratio": 1.3977040883063554, "folds": {"sb01": [0.21019843635459565, 0.26307357651160457], "sb03": [0.17362241872854015, 0.2756773324763558]}}` |
| P5 | mean F1 on share-0 windows > 0.05 | True | `0.22413741127764925` |
| P6 | mean (F1 - share) on windows with share >= 0.5 is < 0 | True | `-0.34266455084917896` |
| P7 | share-0 windows: G1 mean higher with a labelled ship in the background (within site) | True | `{"eligible_sites": 2, "sites_higher": 2, "by_site": {"gr01": {"n_ship": 5, "n_noship": 239, "G1_mean_ship": 0.03600477319811199, "G1_mean_noship": 0.00440179399335832}, "sb01": {"n_ship": 193, "n_noship": 51, "G1_mean_ship": 0.17798880910552806, "G1_mean_noship": 0.15833329887013506}, "sb03": {"n_sh` |
