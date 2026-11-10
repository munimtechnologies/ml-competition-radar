# vessel_mix2 0.2.0: automatic results

Gates: GA=True, GB=True, GC=True (G1 reproduces v1: {"G1_rmse": 0.2694491587478854, "v1_G1_rmse": 0.2694491587478854, "abs_diff": 0.0}). Vessel folds: sb01, sb03.

| estimator | pooled RMSE | bias | RMSE share>0.5 | bias share>0.5 | RMSE share=0 | fold sb01 | fold sb03 |
|---|---|---|---|---|---|---|---|
| C0 | 0.2943 | +0.0036 | 0.3653 | -0.3461 | 0.3557 | 0.2934 | 0.2952 |
| F1 | 0.2722 | -0.0715 | 0.3707 | -0.3427 | 0.2665 | 0.2807 | 0.2634 |
| G1 | 0.2694 | -0.1146 | 0.4035 | -0.3592 | 0.1732 | 0.2631 | 0.2757 |
| G1S | 0.3190 | -0.1625 | 0.4890 | -0.4575 | 0.1763 | 0.3128 | 0.3252 |
| G1L | 0.2342 | +0.0071 | 0.2500 | -0.1871 | 0.2851 | 0.2411 | 0.2271 |
| G1T | 0.2463 | -0.0857 | 0.3502 | -0.2981 | 0.1934 | 0.2375 | 0.2548 |
| G1TS | 0.3060 | -0.1378 | 0.4616 | -0.4268 | 0.1979 | 0.3018 | 0.3102 |
| G0 | 0.1928 | -0.0460 | 0.2650 | -0.2095 | 0.1715 | 0.2102 | 0.1736 |

| id | prediction | held | value |
|---|---|---|---|
| Q1 | pooled RMSE(G1T) < RMSE(G1) | True | `{"G1T": 0.24633835050771377, "G1": 0.2694491587478854}` |
| Q2 | pooled RMSE(G1S) < RMSE(G1) | False | `{"G1S": 0.3190419792192318, "G1": 0.2694491587478854}` |
| Q3 | the best of G1T, G1S, G1TS closes >= 25% of the pooled RMSE gap from G1 down to G0 | True | `{"best": "G1T", "best_rmse": 0.24633835050771377, "fraction_closed": 0.3014348644374189}` |
| Q4 | pooled RMSE(G0) < RMSE of every G1 variant (G1T, G1S, G1TS, G1L) | True | `{"G0": 0.19277983158394127, "G1T": 0.24633835050771377, "G1S": 0.3190419792192318, "G1TS": 0.3060297159555051, "G1L": 0.23420903245117503}` |
| Q5 | pooled RMSE(G1L) < RMSE(C0) | True | `{"G1L": 0.23420903245117503, "C0": 0.29430116814239327}` |
| Q6 | pooled RMSE(G1L) < RMSE(G1) | True | `{"G1L": 0.23420903245117503, "G1": 0.2694491587478854}` |
| Q7 | the best variant's mean bias on windows with share > 0.5 is below -0.20 | True | `{"best": "G1T", "bin": {"n": 1019, "rmse": 0.350165020671176, "bias": -0.2981066631892356}}` |
