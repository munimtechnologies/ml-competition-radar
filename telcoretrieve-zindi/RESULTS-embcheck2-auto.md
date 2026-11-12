# embcheck-2 automatic summary (grade by hand before trusting)

Script 0.2.0; dataset revision `2ec07608ee2a77a59a3f5995ca3c10e9cba4c976`; questions 191; finished 2026-11-12T14:16:16Z.
Gates: {"GA": true, "GQ": false}

## otel (otel-0.6b)

- resolved 10000 of 10000; dtype torch.bfloat16; encode 504 s
- base rates {"L254": 0.0829, "SHORT": 0.296, "LONG": 0.3681}
- instruction affinity (median cosine) {"L254": 0.46156823785583634, "SHORT": 0.1969597896523681, "LONG": 0.0891885258856501, "all": 0.12159101014440565}

| query mode | group | base rate | top-10 share | ratio | any in top-10 | top-1 share | N10 skew | N10 max |
|---|---|---|---|---|---|---|---|---|
| Q | L254 | 0.0829 | 0.0010 | 0.01 | 0.010 | 0.005 | 4.45 | 9 |
| Q | SHORT | 0.2960 | 0.2052 | 0.69 | 0.843 | 0.230 | 4.45 | 9 |
| D | L254 | 0.0829 | 0.0021 | 0.03 | 0.021 | 0.005 | 3.71 | 6 |
| D | SHORT | 0.2960 | 0.1906 | 0.64 | 0.843 | 0.194 | 3.71 | 6 |

## control (qwen3-embedding-0.6b)

- resolved 10000 of 10000; dtype torch.bfloat16; encode 503 s
- base rates {"L254": 0.0915, "SHORT": 0.2979, "LONG": 0.3722}
- instruction affinity (median cosine) {"L254": 0.29068377806637136, "SHORT": 0.24569670508070074, "LONG": 0.17497928383668204, "all": 0.20069232864438472}

| query mode | group | base rate | top-10 share | ratio | any in top-10 | top-1 share | N10 skew | N10 max |
|---|---|---|---|---|---|---|---|---|
| Q | L254 | 0.0915 | 0.0005 | 0.01 | 0.005 | 0.000 | 5.35 | 13 |
| Q | SHORT | 0.2979 | 0.1874 | 0.63 | 0.838 | 0.194 | 5.35 | 13 |
| D | L254 | 0.0915 | 0.0000 | 0.00 | 0.000 | 0.000 | 16.27 | 42 |
| D | SHORT | 0.2979 | 0.2482 | 0.83 | 0.880 | 0.204 | 16.27 | 42 |

## Predictions (automatic)

- P1: not graded
- P2: not graded
- P3: not graded
- P4: not graded
- P5: not graded
- P6: not graded
