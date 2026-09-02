# DCI-1 v8 — recorded SPECTRUM coverage restated at 288 blocks per frame

Produced by `tools/v8_coverage_at_allocation.py`. **Projection only**, labelled `PROJECTION_NOT_REGISTERED_FOR_INFERENCE`. r8 and r9 were run and signed at 96 blocks per frame (one confirmatory pass); their records are read, never rewritten. This file exists so that §4e's allocation amendment does not silently change what an existing SPECTRUM verdict would have been.

Only **condition 4** of `spectrum.coverage` moves with the block count: `SPECTRUM_MAX_SE_BETA` = 0.05 is unchanged, the within-family leverage of a selected design is unchanged, and the projected SE falls as 1/√blocks. Every other refusal — points, families, offsets, span, coordinate SE — is a statement about the selected points and is reproduced verbatim.

The **LOCAL** arm reads no block count (`local_validity`, §13.8's core kernel, §13.15's family count, `admissible_backups`), so no LOCAL support verdict in this table moves. It is shown for contrast.

| root | model | frame | recorded status | SE(β) recorded | SE(β) at 288 | condition 4 at 288 | other refusals | verdict changes? | LOCAL |
|---|---|---|---|---:|---:|---|---|---|---|
| `dci1v8-pilot-r10` | `qwen3-4b-instruct-2507` | f0 | no operating point | — | — | — | — | no | — |
| `dci1v8-pilot-r10` | `qwen3-4b-instruct-2507` | f1 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0176 | 0.0176 | meets | 0 | no | supported |
| `dci1v8-pilot-r10` | `qwen3-4b-instruct-2507` | f2 | no operating point | — | — | — | — | no | — |
| `dci1v8-pilot-r10` | `qwen3-4b-instruct-2507` | f3 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0166 | 0.0166 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r11` | `gemma-3n-e4b-it` | f0 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0143 | 0.0143 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r11` | `gemma-3n-e4b-it` | f1 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0140 | 0.0140 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r11` | `gemma-3n-e4b-it` | f2 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0200 | 0.0200 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r11` | `gemma-3n-e4b-it` | f3 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0172 | 0.0172 | meets | 0 | no | supported |
| `dci1v8-pilot-r8` | `gemma-3n-e2b-it` | f0 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0327 | 0.0189 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r8` | `gemma-3n-e2b-it` | f1 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0308 | 0.0178 | meets | 0 | no | supported |
| `dci1v8-pilot-r8` | `gemma-3n-e2b-it` | f2 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0397 | 0.0229 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r8` | `gemma-3n-e2b-it` | f3 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0287 | 0.0165 | meets | 0 | no | supported |
| `dci1v8-pilot-r8` | `qwen3-4b` | f0 | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` | 0.0744 | 0.0430 | meets | 4 (1 points below A; 1 points above A) | no | unsupported |
| `dci1v8-pilot-r8` | `qwen3-4b` | f1 | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` | 0.0516 | 0.0298 | meets | 2 (1 points below A; 1 families below A) | no | unsupported |
| `dci1v8-pilot-r8` | `qwen3-4b` | f2 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0315 | 0.0182 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r8` | `qwen3-4b` | f3 | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` | 0.0639 | 0.0369 | meets | 0 | **YES** | unsupported |
| `dci1v8-pilot-r8` | `qwen3-4b-instruct-2507` | f0 | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` | 0.0522 | 0.0301 | meets | 4 (0 points above A; 0 families above A) | no | unsupported |
| `dci1v8-pilot-r8` | `qwen3-4b-instruct-2507` | f1 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0360 | 0.0208 | meets | 0 | no | supported |
| `dci1v8-pilot-r8` | `qwen3-4b-instruct-2507` | f2 | no operating point | — | — | — | — | no | — |
| `dci1v8-pilot-r8` | `qwen3-4b-instruct-2507` | f3 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0248 | 0.0143 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r9` | `qwen3-4b` | f0 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0254 | 0.0147 | meets | 0 | no | supported |
| `dci1v8-pilot-r9` | `qwen3-4b` | f1 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0245 | 0.0141 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r9` | `qwen3-4b` | f2 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0264 | 0.0152 | meets | 0 | no | unsupported |
| `dci1v8-pilot-r9` | `qwen3-4b` | f3 | `DIFFICULTY_SUPPORT_IDENTIFIED` | 0.0273 | 0.0158 | meets | 0 | no | supported |

**1 of the recorded frame verdicts would differ** at the amended allocation. A frame whose verdict changes was refused for the projected slope precision alone; a frame that stays refused was refused for something the allocation cannot buy.

These frames are **not** re-verdicted. r8 and r9 stand as run: their SPECTRUM verdicts are conservative with respect to the amended design, and the next replication measured under it will say what it says on its own record.
