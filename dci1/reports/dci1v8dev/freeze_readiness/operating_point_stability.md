# Operating-point stability (signed MEMBERSHIP records)

Root `evidence/dci1v8-confirm-r2`; §12.3 re-run on 2000 topic-level resamples per supported frame; a coordinate is OPERATING_POINT_UNSTABLE when the frozen value is re-selected on fewer than 0.667 of them. The frozen n*(f), m*(f) are never replaced; Δ_R(f) is conditional on them; an unstable coordinate on a LOCAL frame adds the runner-up sensitivity arm (A2 / B2).

| model | f | arm | n* | P(n* rep.) | runner-up (P) | m* | P(m* rep.) | runner-up (P) | status | runner-up slots |
|---|---|---|---:|---:|---|---:|---:|---|---|---|
| `gemma-3n-e2b-it` | 0 | LOCAL+SPECTRUM | 1 | 0.499 | 8 (0.28) | 8 | 0.460 | 9 (0.32) | OPERATING_POINT_UNSTABLE | A2, B2 |
| `gemma-3n-e2b-it` | 1 | LOCAL+SPECTRUM | 3 | 0.911 | 7 (0.04) | 10 | 0.791 | 11 (0.21) | OPERATING_POINT_STABLE | — |
| `gemma-3n-e2b-it` | 2 | none | 2 | 0.947 | 8 (0.00) | 10 | 0.911 | 9 (0.09) | OPERATING_POINT_STABLE | — |
| `gemma-3n-e2b-it` | 3 | LOCAL+SPECTRUM | 7 | 0.510 | 8 (0.22) | 11 | 0.894 | 10 (0.11) | OPERATING_POINT_UNSTABLE | A2 |
| `gemma-3n-e4b-it` | 0 | LOCAL+SPECTRUM | 6 | 0.434 | 4 (0.39) | 9 | 0.584 | 10 (0.31) | OPERATING_POINT_UNSTABLE | A2, B2 |
| `gemma-3n-e4b-it` | 1 | LOCAL+SPECTRUM | 6 | 0.415 | 7 (0.34) | 9 | 0.922 | 10 (0.08) | OPERATING_POINT_UNSTABLE | A2 |
| `gemma-3n-e4b-it` | 2 | SPECTRUM | 7 | 0.861 | 6 (0.13) | 9 | 0.745 | 8 (0.25) | OPERATING_POINT_STABLE | — |
| `gemma-3n-e4b-it` | 3 | LOCAL+SPECTRUM | 8 | 0.785 | 7 (0.21) | 10 | 0.908 | 11 (0.09) | OPERATING_POINT_STABLE | — |
| `qwen3-4b` | 0 | LOCAL+SPECTRUM | 6 | 0.534 | 3 (0.26) | 12 | 0.957 | 13 (0.04) | OPERATING_POINT_UNSTABLE | A2 |
| `qwen3-4b` | 1 | SPECTRUM | 7 | 0.585 | 3 (0.25) | 12 | 1.000 | — | OPERATING_POINT_UNSTABLE | — |
| `qwen3-4b` | 2 | SPECTRUM | 3 | 0.573 | 4 (0.43) | 12 | 0.828 | 11 (0.17) | OPERATING_POINT_UNSTABLE | — |
| `qwen3-4b` | 3 | LOCAL+SPECTRUM | 5 | 0.398 | 4 (0.43) | 13 | 0.885 | 12 (0.11) | OPERATING_POINT_UNSTABLE | A2 |
| `qwen3-4b-instruct-2507` | 0 | — | — | — | — | — | — | — | unsupported | — |
| `qwen3-4b-instruct-2507` | 1 | SPECTRUM | 6 | 0.636 | 5 (0.36) | 10 | 0.998 | 9 (0.00) | OPERATING_POINT_UNSTABLE | — |
| `qwen3-4b-instruct-2507` | 2 | — | — | — | — | — | — | — | unsupported | — |
| `qwen3-4b-instruct-2507` | 3 | SPECTRUM | 6 | 0.942 | 8 (0.06) | 12 | 1.000 | — | OPERATING_POINT_STABLE | — |

Distributions (share of resamples selecting each severity):

- `gemma-3n-e2b-it` f0: n* {"1": 0.4995, "2": 0.073, "3": 0.1155, "6": 0.0005, "7": 0.028, "8": 0.2835}; m* {"10": 0.0005, "7": 0.2185, "8": 0.46, "9": 0.321}
- `gemma-3n-e2b-it` f1: n* {"2": 0.0035, "3": 0.911, "7": 0.0445, "8": 0.041}; m* {"10": 0.7915, "11": 0.2085}
- `gemma-3n-e2b-it` f2: n* {"2": 0.9465, "3": 0.0005, "8": 0.0005, "None": 0.0525}; m* {"10": 0.911, "11": 0.001, "9": 0.088}
- `gemma-3n-e2b-it` f3: n* {"1": 0.02, "2": 0.006, "3": 0.15, "5": 0.0005, "6": 0.0945, "7": 0.51, "8": 0.219}; m* {"10": 0.106, "11": 0.894}
- `gemma-3n-e4b-it` f0: n* {"4": 0.392, "5": 0.0015, "6": 0.4345, "7": 0.172}; m* {"10": 0.307, "11": 0.074, "8": 0.0355, "9": 0.5835}
- `gemma-3n-e4b-it` f1: n* {"4": 0.0945, "5": 0.1485, "6": 0.415, "7": 0.342}; m* {"10": 0.0765, "11": 0.0005, "8": 0.0005, "9": 0.9225}
- `gemma-3n-e4b-it` f2: n* {"6": 0.133, "7": 0.8605, "8": 0.0065}; m* {"10": 0.0005, "8": 0.2545, "9": 0.745}
- `gemma-3n-e4b-it` f3: n* {"6": 0.0075, "7": 0.207, "8": 0.7855}; m* {"10": 0.908, "11": 0.092}
- `qwen3-4b` f0: n* {"3": 0.259, "4": 0.0295, "5": 0.1765, "6": 0.5345, "7": 0.0005}; m* {"12": 0.9565, "13": 0.0435}
- `qwen3-4b` f1: n* {"1": 0.0715, "3": 0.247, "4": 0.0965, "7": 0.585}; m* {"12": 1.0}
- `qwen3-4b` f2: n* {"3": 0.573, "4": 0.427}; m* {"11": 0.172, "12": 0.828}
- `qwen3-4b` f3: n* {"4": 0.435, "5": 0.3975, "6": 0.167, "7": 0.0005}; m* {"12": 0.1145, "13": 0.8855}
- `qwen3-4b-instruct-2507` f1: n* {"5": 0.364, "6": 0.636}; m* {"10": 0.9975, "11": 0.001, "9": 0.0015}
- `qwen3-4b-instruct-2507` f3: n* {"6": 0.942, "8": 0.058}; m* {"12": 1.0}
