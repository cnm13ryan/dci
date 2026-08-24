# DCI-1 v6 — proposal (NOT ADOPTED, NOT REGISTERED)

**Status: PROPOSAL AWAITING RESEARCHER DECISION.** Nothing here is registered,
no manifest exists, and no behavioural row may be generated against it. v6 is a
**new prospective version**, not a continuation of v5's confirmatory run: v5 is
closed, its four replications are scientifically terminal, and none of its rows
may enter v6 as confirmatory evidence.

Rationale and numbers: [`../dci1/reports/dci1v5/survival_diagnosis.md`].
v5 is used as **DEVELOPMENT_EVIDENCE** for survival and identification only.
Per §30's precedent this means v6 is the prospective test of anything fitted
here, and v6 may not claim that these choices generalise.

## What v6 keeps unchanged

The scientific question is unchanged, and so is everything that makes the
answer interpretable:

- the primary question, and `Delta_j`, `Delta_R`, `Xi` and the companion-specific
  identification goal;
- interaction-blind reference selection; no B+R composed outcome may enter
  reference selection (§13.11's schema refusal stands);
- D6-style **irreversible** non-identification;
- a prospective freeze before any confirmatory data, one-shot masking, and the
  §31 prohibition on post-outcome repair, reselection or re-expansion;
- the claim ladder, the multiplicity families F1–F11, the estimators, the
  block bootstrap and §17.2's refit-per-replicate;
- **every threshold**: §13.4's $[0.10,0.90]$ band, §13.8's calipers, §13.14's
  $[0.05,0.95]$ composed band, C4's ≥6 groups / ≥3 rungs / ≥0.40 span, D17's
  construct floor, D18's precondition;
- U4 = E2 (eligibility on $p_{solo}$), carried forward as resolved.

**No threshold is relaxed.** Every change below adds measurement or supply; it
does not lower a bar. This is deliberate: the diagnosis found no threshold that
was wrong, only a library and an operating point that could not meet them.

## Change 1 — prospectively extend the candidate reference library (addresses bottleneck 1)

**Follows from:** only 14–21 eligible rungs sit above $\iota_A$ against 143–163
below, so 23–27 of ~35 families are one-sided and cannot straddle; and 3–4
families per model straddle with ≥3 rungs but miss the 0.40 span, at 0.21–0.38.

**Modification.** Extend the registered ladders of existing families upward in
$\iota$, and add families whose ladders span wider, subject to:

- **L1.** Every family's registered ladder must be extended until either its
  measured $\iota$ span reaches ≥0.55 on the development models, or its next
  rung would fall outside $p_{solo} \in [0.10, 0.90]$. The 0.55 target is
  0.40 plus the largest observed pre-screen→calibration attrition, so a family
  that qualifies at the screen still qualifies after it.
- **L2.** The library must supply, per development model, at least **10**
  feature groups with a straddling family (C4 requires 6; this is four spare,
  the same spare-margin logic C4's own "three spare" used against v4r4's F5).
- **L3.** New families must be **structurally distinct** under §7.3 — a new
  `feature_group` and `discourse_role`, not another marker count — because the
  compressed-$\iota$ problem is characteristic of the marker families.
- **L4.** Library extension is fixed and hashed **before** v6 registration and
  may not be revised after Gate 0.

**What this does not do.** It does not change C4, does not change eligibility,
and does not select families by their effect. Families are admitted on
$\iota$-span and structural distinctness only, both interaction-blind.

## Change 2 — a composed-headroom probe before the operating point is fixed (addresses bottleneck 2)

**Follows from:** $m^*$ is chosen at Gate 2 from solo curves; composition lifts
the B slot by up to +0.104; Gate 4 measures this only after references are
fixed, and all four models were within 0.054 of the ceiling or over it.

**Modification.** Add **Gate 2.75 — Composed Headroom Probe**, between
`GATE_2_5_CANDIDATE_QUALIFICATION` and `GATE_3A`:

- **P1.** At the $m^*$ Gate 2 selected, measure the composed cells §13.14 will
  later audit, on the **calibration** topic split, using **structural
  stand-ins** for the companion slots — never a selected reference, and never
  a B+R composed outcome, so reference selection stays interaction-blind.
- **P2.** Record the realised composed lift per slot and order.
- **P3.** If any probed cell exceeds $0.95 - \delta$ or falls below
  $0.05 + \delta$ with $\delta = 0.05$ (a registered **margin**, not a
  relaxation of §13.14's band), re-select $m^*$ **once** by the registered
  focal rule restricted to severities whose probe stays inside the margin.
- **P4.** If no severity on the registered grid satisfies P3, the replication
  terminates `COMPOSED_HEADROOM_UNREACHABLE` — a new registered §28 status.
  This is a *terminal outcome*, not a repair loop: exactly one re-selection is
  permitted, it is driven by a rule fixed before data, and it uses no outcome
  quantity.

**Why this is not post-hoc adaptation.** The probe is prospective, registered,
and blind to the effect: it measures compliance headroom, which §13.14 already
governs, and it cannot see any reference or any composed *outcome*. It moves
the headroom check from after reference selection to before it.

## Change 3 — additional models, only if 1 and 2 are insufficient

**Not proposed now.** The preferred order is library, then operating point,
then models. Whether more models are needed is answerable from the Change-1/2
development measurements before v6 registration, and it is a researcher
decision (see open questions).

## New gates, statuses and selection rules

| item | kind | detail |
|---|---|---|
| `GATE_2_75_COMPOSED_PROBE` | new stage | between 2.5 and 3A; generates; probes composed headroom at $m^*$ |
| `COMPOSED_HEADROOM_UNREACHABLE` | new §28 terminal status | no grid severity satisfies the P3 margin |
| L1–L4 | library admission rules | fixed and hashed pre-registration |
| P3 margin $\delta = 0.05$ | new registered constant | a margin *inside* §13.14's band; the band is unchanged |

## Licensing confirmatory generation

**At least two replications must reach `GATE_5_FREEZE` with D6 identified**
before any confirmatory generation is licensed for the study. One is not
enough: v5 produced exactly one identified replication and it then died at
Gate 4, so a single survivor is a demonstrated single point of failure. A
replication that is identified but terminal at any gate does not count.

If fewer than two survive, v6 terminates as a study with the same standing as
v5: a recorded non-identification, carrying no evidence about the effect.

## Generation budget (estimate, to be recomputed by `tools/v5_compute_budget.py`)

Per replication, on v5's realised counts: Gate 0 2,688 · regime ~10,800 ·
Gate 2 ~100,600 · **Gate 2.75 ~6,000 (new)** · Gate 4 ~1,200 ·
confirmatory (unreached in v5) ~110,000. Library extension raises the regime
screen and Gate 2 candidate pools roughly in proportion to added rungs;
at L1/L2's targets expect **+25–40%** on those two stages.

Rough per-replication total to freeze: **~135,000** rows (v5 realised ~115,000).
Four replications to freeze: **~540,000**. Plus confirmatory only for
replications that survive.

## Failure and terminal rules

Unchanged from v5, plus `COMPOSED_HEADROOM_UNREACHABLE`. D6 stays irreversible.
A `PREFREEZE_AUDIT` failure is terminal and now *raises* (v5 A8 fix). No gate
failure may be repaired, and no replication may be re-run to obtain a different
verdict.
