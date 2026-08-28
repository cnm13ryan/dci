# DCI-1 v6: closed 2026-08-27, no replication reached confirmatory generation

`closure.json` beside this file is the study-level closing record, written by
`tools/v6_closure.py` from the four signed terminal reports. Zero survivors of
four. This note is the plain-language reading of it; the numbers are in the
signed records and the readings are v6's, under v6's registered rule.

| replication | last stage | terminal status | what the record says |
|---|---|---|---|
| `qwen3-4b` | `GATE_2_75_COMPOSED_PROBE` (m\* = 12) | `COMPOSED_HEADROOM_UNREACHABLE` | `pair:B+A`, B-slot compliance 0.891 on 192 topics, projected Gate-4 interval 0.779–1.002 against [0.05, 0.95]. B solo was 0.747: B's compliance **rose** under A. A's own compliance under B fell to 0.36 / 0.32 from a solo 0.706 |
| `qwen3-4b-instruct-2507` | `GATE_2_75_COMPOSED_PROBE` (m\* = 11) | `COMPOSED_HEADROOM_UNREACHABLE` | `pair:A+B` B 0.875 → 0.994 and `pair:B+A` B 0.924 → 1.024. B solo 0.779. Two stand-in-dependent entries at 0.957 and 0.951, recorded and gating nothing (A13) |
| `gemma-3n-e4b-it` | `GATE_4_COMPOSED_HEADROOM` (m\* = 9, base + class arms) | `COMPOSED_HEADROOM_FAILURE` | `solo:CL` = 0.958 on the 24 composed topics against a calibrated solo of 0.686. Gate 3C had already recorded `REFERENCE_SUPPORT_NOT_IDENTIFIED` |
| `gemma-3n-e2b-it` | `PREFREEZE_AUDIT` (m\* = 10, base + class arms) | `PREFREEZE_AUDIT_FAILURE` | Gate 4 passed (8 cell types, all inside the band). The audit refused on `protocol_hashes_agree` — the preregistration had been amended (A16, A17) after registration and the lifecycle had no way to bind that — and on `support_satisfied`, the same Gate-3C non-identification. Incident: `incidents/2026-08-27_prefreeze_protocol_hash.md` |

**What v6 established.** All four replications registered, qualified, and
passed Gate 0, the regime screen (with A16), Gate 1, Gate 2 and Gate 2.5.
§12.6's coverage criterion was met at the pre-screen on every replication and
**lost on the calibration basis on both Gemmas** (V6-E04's paired re-read),
which is the finding that decided their arm set. No replication reached Gate 3
with a Qwen, because both Qwens stopped two stages earlier on the composed
probe. No `Delta_R`, `Delta_j` or `Xi` estimate exists. 12,096 probe rows per
replication and 768 Gate-4 rows per Gemma exist and are pre-confirmatory
evidence only.

**What v6's terminations are, and are not.** Each is a correct outcome under
the rule v6 registered. The two Qwen terminations are also the observation
that the criterion behind them inspected a marginal arm rate where the
estimand is a paired contrast — B being delivered *better* under A ended the
study of whether A harms B — and that observation is why there is a v7
(`user-notes/DCI1_preregistration_v7.md`, `CHANGES_SCIENTIFIC.md`
2026-08-27). Under §32.1 and §32.3 that cannot be a v6 amendment, and it is
not one: nothing here is re-verdicted, and no v6 record was edited.

**Retained, not reusable.** Every v6 row and record stays under
`dci1/evidence/dci1v6/` and its durable mirror; `dci1v7` names `dci1v6` a
foreign study and reads it only through `protocol/reuse_ledger.py` as
`HISTORICAL_OUTCOME` and `DEVELOPMENT_EVIDENCE`.
