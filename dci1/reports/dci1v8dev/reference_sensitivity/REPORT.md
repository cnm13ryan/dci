# Reference-triple sensitivity (finding 5)

How tied was §13.8's choice of the three core references on each pilot frame? Produced by `tools/v8_reference_sensitivity.py` from the signed `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` records and the frames' own per-topic vectors. Every signature is verified on read (`confirm.pilot_import.open_pilot`).

**Nothing here changes a selection.** R1/R2/R3 stay the frozen primary triple and R4/R5 stay the frozen backups. The confirmatory analysis already re-forms Δ_R(f) over **every admissible triple of the five frozen families** from the same generated cells — the `F_REFSENS` member family in `src/dci1v8dev/confirm/analysis.py`, planned on the `MEMBERSHIP` record's `reference_sensitivity` block (`confirm/membership.py`). What this report adds is how much of the ranking that produced R1..R3 was signal.

**Convention.** MATERIAL when some admissible alternative triple's total distance is within 1 bootstrap SE of the primary triple's, or the registered ranking re-selects the frozen triple on fewer than 0.6667 of 2000 topic resamples. Neither number is a registered threshold; both are stated in advance and every count they read is printed beside them.

**What the bootstrap holds fixed.** Family admission — the full V(R), whose own components resample — is not re-evaluated. A resample re-forms ι_R and ι_A on resampled topics (paired: one topic index for A and every rung) at the measured κ, then re-runs the within-family rung choice and §13.8's ranking, group distinctness, Tier-1 look-ahead and role substitution over the families the pilot found LOCAL-valid. P(primary re-selected) is therefore a **lower bound** on the frozen triple's total variability.

## 1. Per model × frame

| model | f | LOCAL-valid families | frozen | triples (all valid / frozen) | primary triple | distances \|ι_R−ι_A\| | SE(d) | closest alternative | Δsum (SE) | P(primary) | flag |
|---|---:|---:|---:|---:|---|---|---|---|---|---:|---|
| `qwen3-4b` | 0 | 5 | 5 | 9 / 9 | MK1+XC3+MK8 | MK1:4 0.0091 / XC3:10 0.0273 / MK8:2 0.0322 | 0.0327 / 0.0363 / 0.0367 | MK1+MK2+MK8 | +0.0039 (0.0329) | 0.226 | **MATERIAL** |
| `qwen3-4b` | 1 | 4 | 4 | 4 / 4 | XC3+MK7+MK1 | XC3:9 0.0039 / MK7:2 0.0169 / MK1:8 0.0404 | 0.0356 / 0.0340 / 0.0320 | MK7+MK8+XC3 | +0.0217 (0.0327) | 0.636 | **MATERIAL** |
| `qwen3-4b` | 2 | 4 | 4 | 4 / 4 | MK1+MK2+MK7 | MK1:6 0.0065 / MK2:3 0.0247 / MK7:2 0.0286 | 0.0337 / 0.0308 / 0.0295 | MK1+MK2+MK6 | +0.0065 (0.0265) | 0.225 | **MATERIAL** |
| `qwen3-4b` | 3 | 7 | 5 | 34 / 9 | MK2+XC3+MK7 | MK2:6 0.0091 / XC3:8 0.0109 / MK7:2 0.0221 | 0.0292 / 0.0328 / 0.0304 | MK2+MK6+XC3 | +0.0052 (0.0253) | 0.091 | **MATERIAL** |
| `gemma-3n-e2b-it` | 0 | 4 | 4 | 4 / 4 | XC3+MK4+MK2 | XC3:8 0.0057 / MK4:1 0.0387 / MK2:3 0.0521 | 0.0415 / 0.0364 / 0.0377 | MK4+MK5+XC3 | +0.0156 (0.0409) | 0.266 | **MATERIAL** |
| `gemma-3n-e2b-it` | 1 | 6 | 5 | 19 / 9 | XC3+MK1+MK4 | XC3:9 0.0207 / MK1:4 0.0286 / MK4:6 0.0312 | 0.0369 / 0.0417 / 0.0361 | MK1+MK5+XC3 | +0.0052 (0.0224) | 0.133 | **MATERIAL** |
| `gemma-3n-e2b-it` | 2 | 1 | 1 | 0 / 0 | *none* | — | — | — | — | — | **NO_CORE** |
| `gemma-3n-e2b-it` | 3 | 6 | 5 | 19 / 10 | MK2+MK4+MK5 | MK2:1 0.0026 / MK4:5 0.0026 / MK5:5 0.0104 | 0.0423 / 0.0384 / 0.0412 | MK2+MK4+MK8 | +0.0000 (0.0235) | 0.247 | **MATERIAL** |
| `qwen3-4b-instruct-2507` | 0 | — | — | — | *unsupported at Gate 2* | — | — | — | — | — | — |
| `qwen3-4b-instruct-2507` | 1 | 7 | 5 | 35 / 10 | MK5+MK2+MK8 | MK5:10 0.0026 / MK2:8 0.0065 / MK8:8 0.0260 | 0.0344 / 0.0354 / 0.0303 | MK2+MK3+MK5 | +0.0052 (0.0407) | 0.240 | **MATERIAL** |
| `qwen3-4b-instruct-2507` | 2 | — | — | — | *unsupported at Gate 2* | — | — | — | — | — | — |
| `qwen3-4b-instruct-2507` | 3 | 3 | 3 | 1 / 1 | MK6+MK2+XC1 | MK6:10 0.0026 / MK2:7 0.0703 / XC1:2 0.0729 | 0.0324 / 0.0298 / 0.0287 | — | — | 1.000 | **FORCED** |
| `gemma-3n-e4b-it` | 0 | 3 | 3 | 1 / 1 | MK1+MK4+MK2 | MK1:5 0.0000 / MK4:8 0.0026 / MK2:6 0.0208 | 0.0329 / 0.0334 / 0.0345 | — | — | 1.000 | **FORCED** |
| `gemma-3n-e4b-it` | 1 | 4 | 4 | 4 / 4 | MK4+MK1+MK5 | MK4:6 0.0234 / MK1:5 0.0521 / MK5:6 0.0547 | 0.0345 / 0.0339 / 0.0403 | MK1+MK4+XC3 | +0.0073 (0.0632) | 0.387 | **MATERIAL** |
| `gemma-3n-e4b-it` | 2 | 3 | 3 | 1 / 1 | MK4+MK2+MK5 | MK4:8 0.0078 / MK2:6 0.0156 / MK5:7 0.0156 | 0.0403 / 0.0400 / 0.0423 | — | — | 1.000 | **FORCED** |
| `gemma-3n-e4b-it` | 3 | 6 | 5 | 18 / 9 | MK2+MK4+MK5 | MK2:8 0.0078 / MK4:8 0.0078 / MK5:7 0.0234 | 0.0350 / 0.0358 / 0.0331 | MK2+MK4+XC3 | +0.0045 (0.0309) | 0.119 | **MATERIAL** |

## 2. Every admissible triple

### `qwen3-4b` (dci1v8-pilot-r9)

**frame 0** — n\*=6, m\*=12, ι_A=0.6706 (SE 0.0258, 192 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK1, R2=XC3, R3=MK8, R4=MK2, R5=MK6

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK2+MK6 | yes | 0.0820 | +0.0134 | 0.0547 | ✓ | 0.155 |
| MK1+MK2+MK8 | yes | 0.0726 | +0.0039 | 0.0329 | ✓ | 0.227 |
| MK1+MK6+MK8 | yes | 0.0830 | +0.0143 | 0.0444 | ✓ | 0.098 |
| MK1+MK6+XC3 | yes | 0.0781 | +0.0095 | 0.0465 | ✓ | 0.218 |
| MK1+MK8+XC3 **(primary)** | yes | 0.0687 | +0.0000 | 0.0000 |  | 0.226 |
| MK2+MK6+MK8 | yes | 0.1051 | +0.0365 | 0.0436 | ✓ | 0.004 |
| MK2+MK6+XC3 | yes | 0.1003 | +0.0316 | 0.0423 | ✓ | 0.007 |
| MK2+MK8+XC3 | yes | 0.0908 | +0.0221 | 0.0286 | ✓ | 0.061 |
| MK6+MK8+XC3 | yes | 0.1012 | +0.0326 | 0.0297 |  | 0.003 |

**frame 1** — n\*=7, m\*=12, ι_A=0.6081 (SE 0.0247, 192 topics), state LOCAL_AND_SPECTRUM, frozen: R1=XC3, R2=MK7, R3=MK1, R4=MK8

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK7+MK8 | yes | 0.1194 | +0.0582 | 0.0353 |  | 0.034 |
| MK1+MK7+XC3 **(primary)** | yes | 0.0612 | +0.0000 | 0.0000 |  | 0.636 |
| MK1+MK8+XC3 | yes | 0.1064 | +0.0452 | 0.0457 | ✓ | 0.191 |
| MK7+MK8+XC3 | yes | 0.0829 | +0.0217 | 0.0327 | ✓ | 0.139 |

**frame 2** — n\*=3, m\*=12, ι_A=0.6719 (SE 0.0250, 192 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK1, R2=MK2, R3=MK7, R4=MK6

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK2+MK6 | yes | 0.0664 | +0.0065 | 0.0265 | ✓ | 0.381 |
| MK1+MK2+MK7 **(primary)** | yes | 0.0599 | +0.0000 | 0.0000 |  | 0.225 |
| MK1+MK6+MK7 | yes | 0.0703 | +0.0104 | 0.0297 | ✓ | 0.364 |
| MK2+MK6+MK7 | yes | 0.0885 | +0.0286 | 0.0187 |  | 0.030 |

**frame 3** — n\*=5, m\*=13, ι_A=0.6966 (SE 0.0236, 192 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK2, R2=XC3, R3=MK7, R4=MK1, R5=MK6

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK2+MK5 | no | 0.0755 | +0.0333 | 0.0394 | ✓ | 0.035 |
| MK1+MK2+MK6 | yes | 0.0625 | +0.0203 | 0.0407 | ✓ | 0.105 |
| MK1+MK2+MK7 | yes | 0.0573 | +0.0151 | 0.0316 | ✓ | 0.107 |
| MK1+MK2+MK8 | no | 0.1164 | +0.0742 | 0.0532 |  | 0.013 |
| MK1+MK5+MK6 | no | 0.0938 | +0.0516 | 0.0430 |  | 0.006 |
| MK1+MK5+MK7 | no | 0.0885 | +0.0464 | 0.0376 |  | 0.012 |
| MK1+MK5+MK8 | no | 0.1476 | +0.1055 | 0.0483 |  | 0.000 |
| MK1+MK5+XC3 | no | 0.0773 | +0.0352 | 0.0404 | ✓ | 0.027 |
| MK1+MK6+MK7 | yes | 0.0755 | +0.0333 | 0.0441 | ✓ | 0.037 |
| MK1+MK6+MK8 | no | 0.1346 | +0.0924 | 0.0636 |  | 0.003 |
| MK1+MK6+XC3 | yes | 0.0643 | +0.0221 | 0.0337 | ✓ | 0.030 |
| MK1+MK7+MK8 | no | 0.1294 | +0.0872 | 0.0563 |  | 0.006 |
| MK1+MK7+XC3 | yes | 0.0591 | +0.0169 | 0.0234 | ✓ | 0.043 |
| MK1+MK8+XC3 | no | 0.1182 | +0.0760 | 0.0452 |  | 0.001 |
| MK2+MK5+MK6 | no | 0.0768 | +0.0346 | 0.0398 | ✓ | 0.024 |
| MK2+MK5+MK7 | no | 0.0716 | +0.0294 | 0.0330 | ✓ | 0.035 |
| MK2+MK5+MK8 | no | 0.1307 | +0.0885 | 0.0442 |  | 0.000 |
| MK2+MK5+XC3 | no | 0.0604 | +0.0182 | 0.0416 | ✓ | 0.164 |
| MK2+MK6+MK7 | yes | 0.0586 | +0.0164 | 0.0320 | ✓ | 0.071 |
| MK2+MK6+MK8 | no | 0.1177 | +0.0755 | 0.0553 |  | 0.009 |
| MK2+MK6+XC3 | yes | 0.0474 | +0.0052 | 0.0253 | ✓ | 0.084 |
| MK2+MK7+MK8 | no | 0.1125 | +0.0703 | 0.0463 |  | 0.009 |
| MK2+MK7+XC3 **(primary)** | yes | 0.0422 | +0.0000 | 0.0000 |  | 0.091 |
| MK2+MK8+XC3 | no | 0.1013 | +0.0591 | 0.0379 |  | 0.005 |
| MK5+MK6+MK7 | no | 0.0898 | +0.0477 | 0.0375 |  | 0.011 |
| MK5+MK6+MK8 | no | 0.1489 | +0.1068 | 0.0504 |  | 0.000 |
| MK5+MK6+XC3 | no | 0.0786 | +0.0365 | 0.0411 | ✓ | 0.017 |
| MK5+MK7+MK8 | no | 0.1437 | +0.1016 | 0.0428 |  | 0.000 |
| MK5+MK7+XC3 | no | 0.0734 | +0.0312 | 0.0355 | ✓ | 0.032 |
| MK5+MK8+XC3 | no | 0.1325 | +0.0903 | 0.0424 |  | 0.000 |
| MK6+MK7+MK8 | no | 0.1307 | +0.0885 | 0.0581 |  | 0.004 |
| MK6+MK7+XC3 | yes | 0.0604 | +0.0182 | 0.0244 | ✓ | 0.016 |
| MK6+MK8+XC3 | no | 0.1195 | +0.0773 | 0.0480 |  | 0.002 |
| MK7+MK8+XC3 | no | 0.1143 | +0.0721 | 0.0381 |  | 0.001 |

### `gemma-3n-e2b-it` (dci1v8-pilot-r8)

**frame 0** — n\*=8, m\*=8, ι_A=0.6797 (SE 0.0253, 96 topics), state LOCAL_AND_SPECTRUM, frozen: R1=XC3, R2=MK4, R3=MK2, R4=MK5

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK2+MK4+MK5 | yes | 0.1585 | +0.0620 | 0.0296 |  | 0.026 |
| MK2+MK4+XC3 **(primary)** | yes | 0.0964 | +0.0000 | 0.0000 |  | 0.266 |
| MK2+MK5+XC3 | yes | 0.1255 | +0.0290 | 0.0373 | ✓ | 0.277 |
| MK4+MK5+XC3 | yes | 0.1121 | +0.0156 | 0.0409 | ✓ | 0.430 |

**frame 1** — n\*=3, m\*=10, ι_A=0.6276 (SE 0.0289, 96 topics), state LOCAL_AND_SPECTRUM, frozen: R1=XC3, R2=MK1, R3=MK4, R4=MK5, R5=MK2

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK2+MK4 | yes | 0.1198 | +0.0392 | 0.0482 | ✓ | 0.031 |
| MK1+MK2+MK5 | yes | 0.1250 | +0.0444 | 0.0518 | ✓ | 0.040 |
| MK1+MK2+MK8 | no | 0.1771 | +0.0965 | 0.0823 |  | 0.008 |
| MK1+MK4+MK5 | yes | 0.0964 | +0.0157 | 0.0264 | ✓ | 0.155 |
| MK1+MK4+MK8 | no | 0.1484 | +0.0678 | 0.0546 |  | 0.005 |
| MK1+MK4+XC3 **(primary)** | yes | 0.0806 | +0.0000 | 0.0000 |  | 0.133 |
| MK1+MK5+MK8 | no | 0.1536 | +0.0730 | 0.0574 |  | 0.004 |
| MK1+MK5+XC3 | yes | 0.0858 | +0.0052 | 0.0224 | ✓ | 0.145 |
| MK1+MK8+XC3 | no | 0.1379 | +0.0573 | 0.0466 |  | 0.004 |
| MK2+MK4+MK5 | yes | 0.1276 | +0.0470 | 0.0546 | ✓ | 0.082 |
| MK2+MK4+MK8 | no | 0.1797 | +0.0991 | 0.0856 |  | 0.015 |
| MK2+MK4+XC3 | yes | 0.1119 | +0.0312 | 0.0428 | ✓ | 0.036 |
| MK2+MK5+MK8 | no | 0.1849 | +0.1043 | 0.0868 |  | 0.012 |
| MK2+MK5+XC3 | yes | 0.1171 | +0.0365 | 0.0473 | ✓ | 0.046 |
| MK2+MK8+XC3 | no | 0.1692 | +0.0885 | 0.0772 |  | 0.005 |
| MK4+MK5+MK8 | no | 0.1562 | +0.0756 | 0.0609 |  | 0.014 |
| MK4+MK5+XC3 | yes | 0.0884 | +0.0078 | 0.0256 | ✓ | 0.246 |
| MK4+MK8+XC3 | no | 0.1405 | +0.0599 | 0.0509 |  | 0.010 |
| MK5+MK8+XC3 | no | 0.1457 | +0.0651 | 0.0542 |  | 0.008 |

**frame 2** — n\*=2, m\*=10, ι_A=0.7937 (SE 0.0268, 96 topics), state SPECTRUM_ONLY, frozen: R1=MK2

*No admissible triple: the frame holds 1 LOCAL-valid family/families and §13.8 needs three feature groups.*

**frame 3** — n\*=7, m\*=11, ι_A=0.6797 (SE 0.0279, 96 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK2, R2=MK4, R3=MK5, R4=MK8, R5=XC3

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK2+MK4 | no | 0.0677 | +0.0521 | 0.0399 |  | 0.018 |
| MK1+MK2+MK5 | no | 0.0755 | +0.0599 | 0.0391 |  | 0.006 |
| MK1+MK2+MK8 | no | 0.0755 | +0.0599 | 0.0411 |  | 0.003 |
| MK1+MK4+MK5 | no | 0.0755 | +0.0599 | 0.0467 |  | 0.058 |
| MK1+MK4+MK8 | no | 0.0755 | +0.0599 | 0.0471 |  | 0.007 |
| MK1+MK4+XC3 | no | 0.0792 | +0.0635 | 0.0570 |  | 0.029 |
| MK1+MK5+MK8 | no | 0.0833 | +0.0677 | 0.0462 |  | 0.006 |
| MK1+MK5+XC3 | no | 0.0870 | +0.0714 | 0.0563 |  | 0.011 |
| MK1+MK8+XC3 | no | 0.0870 | +0.0714 | 0.0560 |  | 0.003 |
| MK2+MK4+MK5 **(primary)** | yes | 0.0156 | +0.0000 | 0.0000 |  | 0.247 |
| MK2+MK4+MK8 | yes | 0.0156 | +0.0000 | 0.0235 | ✓ | 0.102 |
| MK2+MK4+XC3 | yes | 0.0193 | +0.0036 | 0.0258 | ✓ | 0.054 |
| MK2+MK5+MK8 | yes | 0.0234 | +0.0078 | 0.0220 | ✓ | 0.059 |
| MK2+MK5+XC3 | yes | 0.0271 | +0.0115 | 0.0244 | ✓ | 0.038 |
| MK2+MK8+XC3 | yes | 0.0271 | +0.0115 | 0.0327 | ✓ | 0.017 |
| MK4+MK5+MK8 | yes | 0.0234 | +0.0078 | 0.0244 | ✓ | 0.149 |
| MK4+MK5+XC3 | yes | 0.0271 | +0.0115 | 0.0302 | ✓ | 0.139 |
| MK4+MK8+XC3 | yes | 0.0271 | +0.0115 | 0.0355 | ✓ | 0.043 |
| MK5+MK8+XC3 | yes | 0.0349 | +0.0193 | 0.0343 | ✓ | 0.012 |

### `qwen3-4b-instruct-2507` (dci1v8-pilot-r10)

**frame 1** — n\*=6, m\*=10, ι_A=0.6419 (SE 0.0238, 192 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK5, R2=MK2, R3=MK8, R4=MK3, R5=MK6

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK2+MK3 | no | 0.0938 | +0.0586 | 0.0353 |  | 0.000 |
| MK1+MK2+MK5 | no | 0.0651 | +0.0299 | 0.0288 |  | 0.050 |
| MK1+MK2+MK6 | no | 0.1029 | +0.0677 | 0.0470 |  | 0.014 |
| MK1+MK2+MK7 | no | 0.1484 | +0.1133 | 0.0530 |  | 0.001 |
| MK1+MK2+MK8 | no | 0.0885 | +0.0534 | 0.0327 |  | 0.009 |
| MK1+MK3+MK5 | no | 0.0898 | +0.0547 | 0.0376 |  | 0.003 |
| MK1+MK3+MK6 | no | 0.1276 | +0.0924 | 0.0418 |  | 0.000 |
| MK1+MK3+MK7 | no | 0.1732 | +0.1380 | 0.0427 |  | 0.000 |
| MK1+MK3+MK8 | no | 0.1133 | +0.0781 | 0.0312 |  | 0.001 |
| MK1+MK5+MK6 | no | 0.0990 | +0.0638 | 0.0409 |  | 0.012 |
| MK1+MK5+MK7 | no | 0.1445 | +0.1094 | 0.0461 |  | 0.002 |
| MK1+MK5+MK8 | no | 0.0846 | +0.0495 | 0.0265 |  | 0.016 |
| MK1+MK6+MK7 | no | 0.1823 | +0.1471 | 0.0645 |  | 0.002 |
| MK1+MK6+MK8 | no | 0.1224 | +0.0872 | 0.0468 |  | 0.013 |
| MK1+MK7+MK8 | no | 0.1680 | +0.1328 | 0.0531 |  | 0.003 |
| MK2+MK3+MK5 | yes | 0.0404 | +0.0052 | 0.0407 | ✓ | 0.246 |
| MK2+MK3+MK6 | yes | 0.0781 | +0.0430 | 0.0370 |  | 0.005 |
| MK2+MK3+MK7 | no | 0.1237 | +0.0885 | 0.0368 |  | 0.000 |
| MK2+MK3+MK8 | yes | 0.0638 | +0.0286 | 0.0282 |  | 0.008 |
| MK2+MK5+MK6 | yes | 0.0495 | +0.0143 | 0.0278 | ✓ | 0.145 |
| MK2+MK5+MK7 | no | 0.0951 | +0.0599 | 0.0337 |  | 0.006 |
| MK2+MK5+MK8 **(primary)** | yes | 0.0352 | +0.0000 | 0.0000 |  | 0.240 |
| MK2+MK6+MK7 | no | 0.1328 | +0.0977 | 0.0505 |  | 0.003 |
| MK2+MK6+MK8 | yes | 0.0729 | +0.0378 | 0.0295 |  | 0.028 |
| MK2+MK7+MK8 | no | 0.1185 | +0.0833 | 0.0375 |  | 0.002 |
| MK3+MK5+MK6 | yes | 0.0742 | +0.0391 | 0.0418 | ✓ | 0.038 |
| MK3+MK5+MK7 | no | 0.1198 | +0.0846 | 0.0399 |  | 0.000 |
| MK3+MK5+MK8 | yes | 0.0599 | +0.0247 | 0.0366 | ✓ | 0.105 |
| MK3+MK6+MK7 | no | 0.1576 | +0.1224 | 0.0443 |  | 0.000 |
| MK3+MK6+MK8 | yes | 0.0977 | +0.0625 | 0.0342 |  | 0.000 |
| MK3+MK7+MK8 | no | 0.1432 | +0.1081 | 0.0344 |  | 0.000 |
| MK5+MK6+MK7 | no | 0.1289 | +0.0937 | 0.0456 |  | 0.002 |
| MK5+MK6+MK8 | yes | 0.0690 | +0.0339 | 0.0267 |  | 0.042 |
| MK5+MK7+MK8 | no | 0.1146 | +0.0794 | 0.0333 |  | 0.004 |
| MK6+MK7+MK8 | no | 0.1523 | +0.1172 | 0.0513 |  | 0.003 |

**frame 3** — n\*=6, m\*=12, ι_A=0.6810 (SE 0.0229, 192 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK6, R2=MK2, R3=XC1

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK2+MK6+XC1 **(primary)** | yes | 0.1458 | +0.0000 | 0.0000 |  | 1.000 |

### `gemma-3n-e4b-it` (dci1v8-pilot-r11)

**frame 0** — n\*=4, m\*=9, ι_A=0.7240 (SE 0.0268, 96 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK1, R2=MK4, R3=MK2

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK2+MK4 **(primary)** | yes | 0.0234 | +0.0000 | 0.0000 |  | 1.000 |

**frame 1** — n\*=5, m\*=9, ι_A=0.7031 (SE 0.0268, 96 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK4, R2=MK1, R3=MK5, R4=XC3

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK4+MK5 **(primary)** | yes | 0.1302 | +0.0000 | 0.0000 |  | 0.387 |
| MK1+MK4+XC3 | yes | 0.1375 | +0.0073 | 0.0632 | ✓ | 0.387 |
| MK1+MK5+XC3 | yes | 0.1687 | +0.0385 | 0.0381 |  | 0.044 |
| MK4+MK5+XC3 | yes | 0.1401 | +0.0099 | 0.0361 | ✓ | 0.182 |

**frame 2** — n\*=7, m\*=9, ι_A=0.6589 (SE 0.0294, 96 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK4, R2=MK2, R3=MK5

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK2+MK4+MK5 **(primary)** | yes | 0.0391 | +0.0000 | 0.0000 |  | 1.000 |

**frame 3** — n\*=8, m\*=10, ι_A=0.6823 (SE 0.0283, 96 topics), state LOCAL_AND_SPECTRUM, frozen: R1=MK2, R2=MK4, R3=MK5, R4=XC3, R5=MK1

| triple | frozen five? | Σd | Δsum vs primary | SE(Δsum) | within 1 SE | P(selected) |
|---|---|---:|---:|---:|:-:|---:|
| MK1+MK2+MK3 | no | 0.0833 | +0.0443 | 0.0436 |  | 0.026 |
| MK1+MK2+MK4 | yes | 0.0443 | +0.0052 | 0.0343 | ✓ | 0.242 |
| MK1+MK2+MK5 | yes | 0.0599 | +0.0208 | 0.0268 | ✓ | 0.080 |
| MK1+MK3+MK4 | no | 0.0833 | +0.0443 | 0.0410 |  | 0.008 |
| MK1+MK3+MK5 | no | 0.0990 | +0.0599 | 0.0450 |  | 0.010 |
| MK1+MK3+XC3 | no | 0.1035 | +0.0644 | 0.0540 |  | 0.007 |
| MK1+MK4+MK5 | yes | 0.0599 | +0.0208 | 0.0237 | ✓ | 0.018 |
| MK1+MK4+XC3 | yes | 0.0644 | +0.0253 | 0.0389 | ✓ | 0.024 |
| MK1+MK5+XC3 | yes | 0.0800 | +0.0410 | 0.0399 |  | 0.019 |
| MK2+MK3+MK4 | no | 0.0625 | +0.0234 | 0.0344 | ✓ | 0.051 |
| MK2+MK3+MK5 | no | 0.0781 | +0.0391 | 0.0428 | ✓ | 0.072 |
| MK2+MK3+XC3 | no | 0.0826 | +0.0436 | 0.0522 | ✓ | 0.046 |
| MK2+MK4+MK5 **(primary)** | yes | 0.0391 | +0.0000 | 0.0000 |  | 0.119 |
| MK2+MK4+XC3 | yes | 0.0436 | +0.0045 | 0.0309 | ✓ | 0.110 |
| MK2+MK5+XC3 | yes | 0.0592 | +0.0201 | 0.0365 | ✓ | 0.101 |
| MK3+MK4+MK5 | no | 0.0781 | +0.0391 | 0.0364 |  | 0.018 |
| MK3+MK5+XC3 | no | 0.0983 | +0.0592 | 0.0583 |  | 0.029 |
| MK4+MK5+XC3 | yes | 0.0592 | +0.0201 | 0.0299 | ✓ | 0.018 |

## 3. Verdict

**Finding 5 CONFIRMED.** Of 13 model × frame cells with an identified core triple, 10 are MATERIAL: 10 carry an admissible alternative triple whose total distance is within 1 bootstrap SE of the frozen triple's, and 10 re-select the frozen triple on fewer than 0.667 of 2000 topic resamples. Of the 3 that are not, 3 are `FORCED` — the frame's LOCAL-valid pool admits exactly one triple, so nothing was chosen and P(primary) = 1 says only that there was no alternative. That leaves 0 cell(s) on which the registered ranking was genuinely well separated.

On 7 of the 10 cells where the rule had more than one admissible triple to choose from, the bootstrap selects some alternative **more often than the frozen one**: the ranking did not merely fail to separate the candidates, it put a family first that a resample of the same topics would usually not have put first.

P(primary re-selected) ranges from 0.091 (`qwen3-4b` frame 3) to 1.000 (`qwen3-4b-instruct-2507` frame 3).

The consequence is a reading instruction, not an amendment: on a MATERIAL frame the frozen triple is one of several the registered rule could equally have produced, so `F_REFSENS`'s spread over the admissible triples of the five frozen families is the estimate's sensitivity to a selection the data did not determine, and a Δ_R(f) that moves across those triples should be read as such. On a `FORCED` frame there was no choice to make and the pool is the binding constraint (§13.15's five families, not the ranking); on a `STABLE` frame the spread is a robustness check that the ranking was well separated.

Every count above is recomputed by `python3 tools/v8_reference_sensitivity.py --all`; the machine-readable form is `reference_sensitivity.<root>.<model>.json` beside this file.

