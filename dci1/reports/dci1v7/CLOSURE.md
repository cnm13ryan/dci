# DCI-1 v7: closed 2026-08-28, no replication reached the freeze

`closure.json` beside this file is the study-level closing record, written by
`tools/v7_closure.py` from the four signed terminal reports; zero survivors of
four. `replication_summary.json`, written by `tools/v7_replication_summary.py`
from the signed stage records, carries every number quoted here.
`execution_logs/` holds the driver logs and the CLI output of every stage
invocation. Nothing here is an estimate: v7 generated no confirmatory row and
opened no masked quantity.

| replication | last stage | terminal status | Δ_R | what the records say |
|---|---|---|---|---|
| `gemma-3n-e2b-it` | `GATE_4_COMPOSED_CONTRAST` (m\* = 10, n\* = 8; arms base + class, 8 cells) | `PREFREEZE_AUDIT_FAILURE` on `support_satisfied` alone (26 checks, 1 failed, 0 unresolved) | **not identified** (`REFERENCE_SUPPORT_NOT_IDENTIFIED` at Gate 3C) | §13.15's counts met — 3 core references over 3 feature groups (2 Tier-1), 12 qualified families, 2 frozen backups — but §12.6's C4 is lost on the calibration basis: 2 straddling groups against a floor of 6. Probe: D(B←A) −0.02 / +0.24, D(A←B) +0.29 / +0.26, Λ −0.31 / −0.02 (outcome-first / outcome-second), no boundary status. Gate 4 recorded 768 rows, no contrast status |
| `gemma-3n-e4b-it` | `GATE_4_COMPOSED_CONTRAST` (m\* = 9, n\* = 6; base + class, 8 cells) | `PREFREEZE_AUDIT_FAILURE` on `support_satisfied` alone | **not identified** | 3 Tier-1 core references, 11 qualified families, 2 backups; C4 lost on the calibration basis: 4 straddling groups. Probe: D(B←A) +0.02 / +0.40, D(A←B) +0.21 / +0.16, Λ −0.19 / +0.24. Gate 4: 768 rows, no contrast status |
| `qwen3-4b` | `GATE_4_COMPOSED_CONTRAST` (m\* = 12, n\* = 2; base only, 5 cells) | `PREFREEZE_AUDIT_FAILURE` on `support_satisfied` alone | **not identified** | 3 Tier-1 core references, 11 qualified families, 2 backups; C4 lost: 5 straddling groups. Probe at the point v6 terminated on: B under A 0.88 / 0.78 against solo 0.77, A under B 0.38 / 0.36 against solo 0.69 — D(B←A) −0.12 / −0.02, D(A←B) +0.31 / +0.33, Λ −0.42 / −0.34; **no arm at a boundary, nothing compressed, recorded, not terminal**. Gate 4: 480 rows, `COMPOSED_CONTRAST_RANGE_COMPRESSED` on the 24-topic projection |
| `qwen3-4b-instruct-2507` | `GATE_4_COMPOSED_CONTRAST` (m\* = 11, n\* = 5; base only, 5 cells) | `PREFREEZE_AUDIT_FAILURE` on `support_satisfied` alone | **not identified** | 3 Tier-1 core references, 11 qualified families, 2 backups; C4 lost: 4 straddling groups. Probe: B under A 0.92 / 0.60 against solo 0.78, A under B 0.62 / 0.89 against solo 0.57 — D(B←A) −0.14 (excess direction **compressed**: B under A above 0.90) / −0.12, D(A←B) −0.05 / −0.04, Λ −0.09 / −0.08. Gate 4: 480 rows, `COMPOSED_CONTRAST_RANGE_COMPRESSED` |

**What v7 established.** All four replications registered under one manifest
(`969a5b9f…`, commit `ed0446f`, zero rows), qualified with a clean tree, and
passed Gate 0, the regime screen, Gate 1, Gate 2, Gate 2.5, the composed
probe, Gates 3A–3C and Gate 4. **The criterion v7 withdrew did not end
anything**: both Qwens passed the composed probe that terminated them in v6 —
B's delivery rose under A on both, and the rule recorded it (on the 2507
checkpoint as a compressed excess direction) — and both Gemmas passed Gate 4,
where v6 ended `gemma-3n-e4b-it` on a companion's own solo cell. What ended
every replication is the same single condition, upstream of anything v7
changed: §12.6's decisive coverage condition C4 (≥ 6 feature groups
straddling ι_A) was certified on the 24-topic pre-screen and lost on the
192-topic calibration basis (v6 A3's paired re-read) on all four —
`conditions_moved_by_the_basis` names C4 on every record — so Gate 3C
recorded `REFERENCE_SUPPORT_NOT_IDENTIFIED` under §34 D6 while §13.15's own
counts (≥ 5 families, ≥ 3 core, ≥ 2 Tier-1, 3 groups, 2 backups) were met on
all four. No `Delta_R`, `Delta_j` or `Xi` is identified on any replication.
118,176–142,320 pre-confirmatory rows per replication exist and are
pre-confirmatory evidence only.

**How each replication ended, precisely.** §34 D6 is closed at
`identification_status`: Gate 3C is not terminal, it drops the core and
spectrum arms, and the replication proceeds. Each did — through Gate 4 — and
was then refused by the pre-freeze audit's mandatory `support_satisfied`
artifact check, which requires §13.15's support to be *met*
(`prefreeze_run.py`, `bool(support_met)`). This is the behaviour v5's closure
recorded as correctly computed when two of its replications ended on it, the
check v6's READINESS lists as non-waivable, and the outcome v7's own
preregistration (§5: "both v6 Gemmas ended here in substance") and READINESS
(§4.3: "the Gemmas are not rescued by anything here") anticipated. It was
therefore left as the operative rule; amending it after four terminations
would be the §32.1 case the registration forbids. **It is nevertheless a
standing tension the researcher should decide before any v8**: §13.15's
registered prose says a non-identified replication continues to the freeze
("the freeze carries it") with its base-arm estimands — D(B←A), D(A←B), Λ,
the order contrasts — identified and estimated as usual, and D6's closure
says the same, while the pre-freeze check makes D6 = `identification_status`
terminal one stage later, so those estimands were never generated on any
replication of v5, v6 or v7. The execution-path audit's
`reference_support_not_identified` scenario stops at Gate 3C and never
walked the audit, which is why the contradiction is only visible on a real
tree.

**What v7's terminations are, and are not.** Each is a correct outcome under
the rule v7 registered and ran. None is evidence about the effect: every
terminal status is a statement about the apparatus reaching identification.
The probe and Gate-4 quantities in the table are projections the records
label as deciding nothing and are not confirmatory results. The one
measurement that recurs across every v6 and v7 replication — composing B
with A raises or barely moves B's delivery while A's own delivery falls on
three of four models — is a development-evidence observation about the
treated arm on calibration topics, not a registered claim.

**Apparatus, for the record.** Two replications shared each RX 7900 XTX as
independent TP=1 lanes; the driver (`tools/run_v7_replication.sh`) was
revised twice during the run for scheduling only — a per-card lock so that a
multi-call stage is not interleaved with another replication's calls, and a
fix to that lock's argument handling — and `qwen3-4b-instruct-2507` was moved
to card 0 once card 0 fell idle. No stage was re-run after producing a record;
the one stage attempt that failed and was repeated (`gemma-3n-e2b-it`'s
regime screen, on the backend's per-device lock) reused its finished calls
by generation identity and regenerated nothing. Stage records carry the
commits `ed0446f` (registration), `a4d35f6`, `a894e20`, `0f56bce` and
`7fda7d9`; the differences between them are documentation, the driver, the
regenerated execution-path audit and the closure tool's label. No verifier,
wording, estimator, threshold or constant moved.

**Retained, not reusable.** Every v7 row and record stays under
`dci1/evidence/dci1v7/` and its durable mirror `dci1/durable_root/dci1v7/`
(12 signed records per replication, all mirrored; 17 GB each root).
