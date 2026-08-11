# `verifiers.tier1_audit_protocol` — investigator decision memo

Stage 2's last open decision. Nothing here is adopted; the slot stays
`PENDING_DECISION` until you record one.

---

## 1. The decisions you must make

| # | Decision | Why it is yours |
|---|---|---|
| **D-1** | **Reviewers per case, and the adjudication rule.** | §10.4 says "human-adjudicated" and stops. §8.6's two-independent-plus-third-adjudicator rule is scoped to *semantic review of compositions* — clauses "whose intended semantics are not exhaustively covered by the frozen machine encoding and deterministic verifier". Adopting it for Tier-1 reliability is an **explicit extension**, not an inference. |
| **D-2** | **Whether the intended truth class is blinded.** | §10.6 blinds arm, automatic verdict and constraint role. It says nothing about the class the author intended. Blinding it is *stricter* than the protocol — a new commitment, not a reading of one. |
| **D-3** | **Whether a case adjudicated against its intended class is credited to the other class or discarded.** | Drives the content budget by ~20% (see §2). §11.1 and §11.2 count "examples with both true pass and true fail support" without saying which. |
| **D-4** | **The initial pool size per unit per class**, and therefore the authoring budget. | §11.2 requires the sufficiency counts to be established before expensive work; it fixes no number. |
| **D-5** | **The short-class rule**: what happens if a class ends below 72. | A3 permits only prospectively frozen behaviour here. |
| **D-6** | **The post-adjudication selection rule** picking exactly 72 per class. | Must be fixed now and independent of verifier output. |
| **D-7** | **Reviewer assignment across the six units.** | Unspecified anywhere. 864 cases is a lot for one panel; reuse risks correlated error, rotation risks heterogeneous standards. |

---

## 2. Pool-size calculations

Target 72 per class per unit; 12 strata (6 units × 2 classes) must **all** reach it.

Let *p* = probability an authored case is adjudicated into the class its author
intended. Two models, corresponding to **D-3**:

- **Model A — cross-credited.** A case authored "truly fails" but adjudicated
  "truly passes" counts toward *truly passes*. Adjudicated count per class is
  `Bin(N,p) + Bin(N,1−p)`, so **E[count] = N for every p** — misauthoring
  redistributes rather than destroys.
- **Model B — discarded.** A mis-adjudicated case is a defect and is dropped.
  Count is `Bin(N,p)`.

### P(a single stratum reaches 72)

| N/class | *p*=0.85 A | 0.85 B | 0.90 A | 0.90 B | 0.95 A | 0.95 B |
|---|---|---|---|---|---|---|
| **72** | 0.547 | 0.000 | 0.556 | 0.001 | 0.577 | 0.025 |
| **80** | 0.970 | 0.134 | 0.988 | 0.593 | 0.999 | 0.982 |
| **85** | 0.998 | 0.603 | 1.000 | 0.958 | 1.000 | 1.000 |
| **90** | 1.000 | 0.926 | 1.000 | 0.999 | 1.000 | 1.000 |
| **100** | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

**Authoring exactly 72 is a coin flip even under the generous model, and fails
almost surely under the strict one.** That single line is the reason this decision
cannot be skipped.

### P(all 12 strata reach 72) and the resulting budget

| Model | *p* | N/class | P(all 12) | Labels authored |
|---|---|---|---|---|
| A | 0.85 | 85 | 0.978 | 1,020 |
| A | 0.90 | 85 | 0.996 | 1,020 |
| A | 0.90 | 90 | 1.000 | 1,080 |
| B | 0.90 | 90 | 0.984 | 1,080 |
| B | 0.90 | 100 | 1.000 | 1,200 |
| B | 0.85 | 100 | 0.997 | 1,200 |

Smallest N per class for P ≥ 0.99 per stratum:

| *p* | 0.80 | 0.85 | 0.90 | 0.95 | 0.98 |
|---|---|---|---|---|---|
| Model A | 84 | 83 | 81 | 78 | 76 |
| Model B | 102 | 95 | 88 | 81 | 77 |

**Every number is adjudication volume, not just authoring** — all authored cases go
through the full reviewer process, so 1,080 authored means 1,080 × (reviewers per
case) judgements.

*p* is unknown. It is a property of your authoring procedure, and the honest way to
learn it is a small pilot on one unit before committing the full budget.

---

## 3. Short-class (tranche) rules

Model B, *p* = 0.90, per stratum:

| Rule | P(reach 72) | Expected labels/stratum |
|---|---|---|
| **R1** N=80, else fail closed → fresh audit | 0.593 | 80 |
| **R2** N=80 + one frozen top-up of 10 | 0.999 | 84.1 |
| **R2′** N=80 + one frozen top-up of 20 | 1.000 | 88.1 |
| **R3** N=100, single tranche | 1.000 | 100 |

**R2 dominates R3 on cost** (84 vs 100 expected labels for the same success) but
adds a data-dependent stopping rule. **R3 is the simplest to defend**: one tranche,
no stopping rule, nothing to argue about.

### The crux you must accept for R2

A3 forbids conditional extension. R2's top-up is triggered by **the number of cases
the blinded humans put in a class** — never by a verifier verdict, which reviewers
never see. The verifier's error on a case is therefore independent of whether that
case's stratum triggered a top-up, so the conditional error rate keeps its meaning.

Two caveats, stated so you can weigh them rather than discover them:

- the argument is *conditional independence given the case set*. If authoring
  quality correlates with verifier difficulty, a stratum needing a top-up could be
  systematically harder. R3 has no such exposure.
- the implemented gate already refuses any realised denominator ≠ 72
  (`design_violation`), so **whichever rule you pick, the denominator entering the
  interval is exactly 72**. The tranche question is about how the 72 are obtained,
  not about the sample the bound is computed on.

**Never permitted under any rule**: adding cases because the verifier erred. §10.6 —
*"collecting more confirmatory data is not a remedy for invalid measurement."*

---

## 4. Check against v19

### Explicitly required

**§10.4** — each target/focal verifier individually certified at a 5% conditional
error ceiling; 72 (A3-amended from 73) adjudicated true failures *and* 72 true
passes per unit; a false-pass bound needs examples that truly fail and a false-fail
bound needs examples that truly pass; a missing denominator is missing evidence, not
zero error; if either class is absent the bound is unavailable and the unit cannot
pass.

**§10.6** — adjudication blinded to arm, automatic verdict and constraint role
"where feasible"; audit material includes the 14 named categories; a signed audit
cannot be overwritten by a later run; a demonstrated defect requires repair and
re-audit, and more data is not a remedy.

**§11.1** — the audit pool is one of six disjoint scientific splits; it may not
contain the pair's target, focal, admitted references, semantic duplicates, known
incompatible rules, or content allocated to another split; material may be authored
before freeze under a versioned content procedure; **once a pool is signed and
hashed, moving items between pools is prohibited**.

**§11.2** — the sufficiency report counts "human-audit examples with both true pass
and true fail support" separately by pair and scope.

### Left unspecified

Reviewer count; adjudication mechanism; adjudicator independence; whether the
intended class is blinded; how exactly 72 is reached when the class is established
*by* adjudication; the fate of mis-adjudicated cases; any reserve/tranche policy for
the audit pool (§6.2's reserve rule covers target/focal *items*, not audit cases);
reviewer qualification, training and assignment across units.

### Genuinely new prospective decisions in the proposal

D-1 (extending §8.6's rule to Tier-1), D-2 (blinding the intended class — stricter
than §10.6), D-3, D-4, D-5, D-6, D-7. All seven are additions to the protocol, not
readings of it.

### Conflicts

**None found.** Three near-misses worth recording:

1. **Tranche top-up vs A3's no-extension.** Compatible: the denominator entering the
   interval is exactly 72 either way, and the trigger is human labels, not verifier
   output. Requires your explicit acceptance of the argument in §3.
2. **§11.1's no-movement-between-pools.** A top-up tranche must come from **reserve
   material inside the audit pool, frozen at the same time**, never reallocated from
   another split. This constrains D-5: reserve must be authored and hashed up front.
3. **§10.6's "signed audit cannot be overwritten".** A failed unit gets a *fresh
   prospectively specified* audit, not a re-run. `frozen.apply` already refuses to
   re-freeze a resolved slot.

---

## 5. Freeze records your decision would create

**One record now**, on `verifiers.tier1_audit_protocol`, validated by the
`tier1_audit_protocol` domain:

```json
{
  "slot": "verifiers.tier1_audit_protocol",
  "value": {
    "independent_reviewers": 2,
    "adjudicator_resolves_disagreement": true,
    "adjudicator_id": "<named adjudicator, distinct from the reviewers>",
    "unresolved_disagreement": "fails",
    "oversampling_rule": "prospective_oversample",
    "oversample_factor": "<e.g. 1.18 for 85 per class>",
    "selection_rule": "<see below>",
    "citation": "sections 10.4, 10.6, 11.1 + this memo, accepted <date>"
  },
  "frozen_by": "<you>",
  "recorded_at": "<ISO-8601>",
  "evidence": "<which options in D-1..D-7 were chosen, and why>"
}
```

The domain **refuses**: fewer than 2 independent reviewers; a missing adjudicator;
`unresolved_disagreement` other than `"fails"`; `prospective_oversample` with no
`oversample_factor > 1` or no `selection_rule`.

A `selection_rule` that satisfies D-6 and is already implementable: *"the first 72
cases in each adjudicated class, in `AuditManifest.ordered` order — (unit,
intended class, case hash, case id)."* That ordering is fixed by the manifest hash
before any judgement exists and is a function of case content only, so it cannot
respond to verifier output.

**Records later, in this order:**

1. `pool.p1.audit`, `pool.p2.audit`, `pool.p3.audit` — the authored cases *and*
   their reserve tranche, signed and hashed together (§11.1).
2. `sufficiency.{pair}.audit_true_pass_examples` / `…_true_fail_examples`.
3. `verifiers.tier1_reliability` — the `certify_all` output, which the
   `tier1_certificates` domain re-checks for a pass and no unavailable class.

Only then does `certify_stage2` have all 16 requirements met.

---

## 6. Remaining ambiguity before human authoring begins

1. **Reviewer assignment across units (D-7).** Nothing in v19 addresses it. One
   panel across all 864 cases risks correlated error and learning effects; rotation
   risks heterogeneous standards. Both are defensible; neither is preregistered.
2. ***p* is unknown.** Every budget line in §2 is conditional on it. A pilot on one
   unit would measure it, but a pilot is itself unpreregistered material and must be
   declared disjoint from the audit pool under §11.1.
3. **What "truly fails" means at a parameter boundary.** Pair 1's target at
   `n_items = 3` is unambiguous; Pair 3's focal ("strictly increasing sentence
   lengths") on a response whose segmentation is itself contested is exactly the
   §8.6 uncovered semantics. Reviewers will hit these. Whether they answer anyway or
   have an "unclear" escape is undecided — and an escape would change the
   denominator, so it interacts with D-3 and D-5.
4. **Whether one case may serve two units.** A response can violate the target and
   satisfy the focal of the same pair. Reusing it halves the authoring budget but
   correlates the two units' error estimates, which §10.4 treats as independent
   certifications.

Item 3 is the one I would resolve before authoring starts: it changes what authors
are asked to produce.
