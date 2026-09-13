# DCI-1 v8 — LOCAL frame eligibility

Produced by `tools/v8_local_eligibility.py` from the signed `GATE_3_REFERENCES` records. Pre-freeze only: no composed cell, no Δ_R(f), no pooled statistic enters this verdict.

**Rule.** a frame is LOCAL_SUPPORTED iff §13.8 identifies its three core references, §13.15 counts >= 5 LOCAL-valid families and >= 2 admissible backups on that frame's own table at its own iota_A(f); a model is LOCAL_ELIGIBLE iff >= 2 frames are independently LOCAL_SUPPORTED, and every supported frame of an eligible model enters (no best-two selection, no cross-frame pooling, no outcome read).

## The verdict, on the latest run of each model

| model | root | passes | supported frames | unsupported frames + reason | n | eligible? |
|---|---|---:|---|---|---:|---|
| `gemma-3n-e2b-it` | `dci1v8-pilot-r8` | 2 | f1 (state LOCAL_AND_SPECTRUM, 6 families, 2 backups); f3 (state LOCAL_AND_SPECTRUM, 6 families, 2 backups) | f0: LOCAL_FAMILIES_BELOW_MINIMUM, BACKUPS_BELOW_MINIMUM (4 families, 1 backups); f2: CORE_NOT_IDENTIFIED, LOCAL_FAMILIES_BELOW_MINIMUM, BACKUPS_BELOW_MINIMUM (1 families, 0 backups) | 2 | **YES** |
| `gemma-3n-e4b-it` | `dci1v8-pilot-r11` | 2 | f3 (state LOCAL_AND_SPECTRUM, 6 families, 2 backups) | f0: LOCAL_FAMILIES_BELOW_MINIMUM, BACKUPS_BELOW_MINIMUM (3 families, 0 backups); f1: LOCAL_FAMILIES_BELOW_MINIMUM, BACKUPS_BELOW_MINIMUM (4 families, 1 backups); f2: LOCAL_FAMILIES_BELOW_MINIMUM, BACKUPS_BELOW_MINIMUM (3 families, 0 backups) | 1 | **NO** |
| `qwen3-4b` | `dci1v8-pilot-r9` | 4 | f0 (state LOCAL_AND_SPECTRUM, 5 families, 2 backups); f3 (state LOCAL_AND_SPECTRUM, 7 families, 2 backups) | f1: LOCAL_FAMILIES_BELOW_MINIMUM, BACKUPS_BELOW_MINIMUM (4 families, 1 backups); f2: LOCAL_FAMILIES_BELOW_MINIMUM, BACKUPS_BELOW_MINIMUM (4 families, 1 backups) | 2 | **YES** |
| `qwen3-4b-instruct-2507` | `dci1v8-pilot-r10` | 4 | f1 (state LOCAL_AND_SPECTRUM, 7 families, 2 backups) | f0: NO_OPERATING_POINT (Gate 2: GRID_RESOLUTION_INSUFFICIENT); f2: NO_OPERATING_POINT (Gate 2: GRID_RESOLUTION_INSUFFICIENT); f3: LOCAL_FAMILIES_BELOW_MINIMUM, BACKUPS_BELOW_MINIMUM (3 families, 0 backups) | 1 | **NO** |

Minimum for eligibility: 2 frames. Every supported frame of an eligible model enters; the supported column is the set that would be generated, not a shortlist.

## Every root, for the record

| root | model | frame | state | families | backups | core | LOCAL |
|---|---|---|---|---:|---:|---|---|
| `dci1v8-pilot-r10` | `qwen3-4b-instruct-2507` | f0 | UNSUPPORTED | — | — | — | LOCAL_UNSUPPORTED (NO_OPERATING_POINT) |
| `dci1v8-pilot-r10` | `qwen3-4b-instruct-2507` | f1 | LOCAL_AND_SPECTRUM | 7 | 2 | yes | LOCAL_SUPPORTED |
| `dci1v8-pilot-r10` | `qwen3-4b-instruct-2507` | f2 | UNSUPPORTED | — | — | — | LOCAL_UNSUPPORTED (NO_OPERATING_POINT) |
| `dci1v8-pilot-r10` | `qwen3-4b-instruct-2507` | f3 | LOCAL_AND_SPECTRUM | 3 | 0 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r11` | `gemma-3n-e4b-it` | f0 | LOCAL_AND_SPECTRUM | 3 | 0 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r11` | `gemma-3n-e4b-it` | f1 | LOCAL_AND_SPECTRUM | 4 | 1 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r11` | `gemma-3n-e4b-it` | f2 | LOCAL_AND_SPECTRUM | 3 | 0 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r11` | `gemma-3n-e4b-it` | f3 | LOCAL_AND_SPECTRUM | 6 | 2 | yes | LOCAL_SUPPORTED |
| `dci1v8-pilot-r8` | `gemma-3n-e2b-it` | f0 | LOCAL_AND_SPECTRUM | 4 | 1 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r8` | `gemma-3n-e2b-it` | f1 | LOCAL_AND_SPECTRUM | 6 | 2 | yes | LOCAL_SUPPORTED |
| `dci1v8-pilot-r8` | `gemma-3n-e2b-it` | f2 | SPECTRUM_ONLY | 1 | 0 | no | LOCAL_UNSUPPORTED (CORE_NOT_IDENTIFIED) |
| `dci1v8-pilot-r8` | `gemma-3n-e2b-it` | f3 | LOCAL_AND_SPECTRUM | 6 | 2 | yes | LOCAL_SUPPORTED |
| `dci1v8-pilot-r8` | `qwen3-4b` | f0 | LOCAL_ONLY | 4 | 1 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r8` | `qwen3-4b` | f1 | NEITHER | 3 | 2 | no | LOCAL_UNSUPPORTED (CORE_NOT_IDENTIFIED) |
| `dci1v8-pilot-r8` | `qwen3-4b` | f2 | SPECTRUM_ONLY | 1 | 0 | no | LOCAL_UNSUPPORTED (CORE_NOT_IDENTIFIED) |
| `dci1v8-pilot-r8` | `qwen3-4b` | f3 | LOCAL_ONLY | 4 | 1 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r8` | `qwen3-4b-instruct-2507` | f0 | NEITHER | 0 | 0 | no | LOCAL_UNSUPPORTED (CORE_NOT_IDENTIFIED) |
| `dci1v8-pilot-r8` | `qwen3-4b-instruct-2507` | f1 | LOCAL_AND_SPECTRUM | 6 | 2 | yes | LOCAL_SUPPORTED |
| `dci1v8-pilot-r8` | `qwen3-4b-instruct-2507` | f2 | UNSUPPORTED | — | — | — | LOCAL_UNSUPPORTED (NO_OPERATING_POINT) |
| `dci1v8-pilot-r8` | `qwen3-4b-instruct-2507` | f3 | LOCAL_AND_SPECTRUM | 4 | 1 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r9` | `qwen3-4b` | f0 | LOCAL_AND_SPECTRUM | 5 | 2 | yes | LOCAL_SUPPORTED |
| `dci1v8-pilot-r9` | `qwen3-4b` | f1 | LOCAL_AND_SPECTRUM | 4 | 1 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r9` | `qwen3-4b` | f2 | LOCAL_AND_SPECTRUM | 4 | 1 | yes | LOCAL_UNSUPPORTED (LOCAL_FAMILIES_BELOW_MINIMUM) |
| `dci1v8-pilot-r9` | `qwen3-4b` | f3 | LOCAL_AND_SPECTRUM | 7 | 2 | yes | LOCAL_SUPPORTED |
