# DCI-1 v4r4 → v5: every substantive change, why it changed, and the v4r4 evidence that motivated it

Companion to [`DCI1_preregistration_v5.md`](DCI1_preregistration_v5.md). v5 is a
**standalone** preregistration and incorporates nothing by reference; this
document exists so that a reader who knows v4r4 can find what moved without
diffing two long documents, and so that every change carries the evidence that
caused it.

**Standing.** v4r4 **completed**. Its records, estimates and two terminations
are historical evidence, are unmodified, and are never reinterpreted here. v5
supersedes it prospectively. Under v4r3 §31, carried as v5 §32, a change after
study-wide freeze creates a new protocol version, so this is v5 and not v4r5.

**The overfitting declaration governs this whole document.** Every change below
was chosen after observing the completed v4r4 study. Retrospective performance
on v4r4 is **not** validation. See v5 §30 and
[`../dci1/reports/dci1v5/reference_design_development.md`](../dci1/reports/dci1v5/reference_design_development.md) §9.

---

## 0. The change map

| id | v5 section | Change | Motivating v4r4 finding |
|---|---|---|---|
| **C1** | §7.4, §7.5, §7.10 | The core reference pool becomes **production class and same-form with $A$**: exact counts of a short marker word. v4r4's budget pool moves to the spectrum and broad-class arms | Every v5 validity gate is free on the production pool and removes 3 of 4 models' entire budget pool |
| **C2** | §7.3, §7.4 | A **structural taxonomy** with twelve metadata fields and three tiers replaces the single `constraint_class` label | Two companions in one declared class gave $\Delta_{\text{class}}$ of $+0.011$ and $-0.511$ |
| **C3** | §13.1, §13.3 | $V(R)$ becomes a **lexicographic conjunction of eight components**; $\iota$ is demoted from the admission coordinate to the difficulty coordinate and is evaluated **last** | A rung at solo 0.9740 / chance 0.9323 was admitted because its $\iota$ was closest, and terminated a replication on its own solo cell |
| **C4** | §13.4 | New **raw-headroom** gate on the Wilson interval, a **lift floor**, and a **chance ceiling of 0.75** against v4r4's 0.99 | Six rungs sat inside the caliper with raw solo compliance above 0.90; $\iota$'s split-half instability rises 4.5× from chance-free to $\kappa \ge 0.75$ |
| **C5** | §13.6 | New **interaction gate**: $\kappa^{B}$, the displacement $\Sigma$, and the projected composed compliance $\hat p$ | `RF11` went 0.635 solo → 0.969 composed with $B$ and ended the only full-design replication |
| **C6** | §6.2, §13.7 | **Two independent calibration splits** (96 + 96) and an equivalence-style **stability** rule; the calibration sample doubles | 50–100% of straddling families were lost between pre-screen and calibration on every replication |
| **C7** | §12.2 | The regime screen becomes **high-recall**; the pre-screen distance caliper is **removed** | 35.7% of candidates move further between the two stages than the whole width of the caliper |
| **C8** | §12.6, §13.15 | **Support oversupply**: C4 requires six straddling groups against four, five families must qualify, three are used and **two are frozen as backups** | Three of four replications finished below three core references; the fourth had no spare |
| **C9** | §7.1, §12.3 | The focal grid extends to $\{7\dots14\}$ with an extension to $\{15,16\}$, and a **bracketing rule** requires both neighbours of $m^*$ to be measured | $m^*$ was the last measured rung on **all four** replications |
| **C10** | §11.7, §15, §3.2 | **Direct order contrasts** $\text{Ord}_A$, $\text{Ord}_B$, $\text{Ord}_\Lambda$, $\text{Ord}_{\bar R}$, $\text{Ord}_{CL}$ in a new primary-tier family F11, licensing **L4b** | $\Lambda$ reversed sign across configurations with both intervals excluding zero, and no registered contrast existed to test it |
| **C11** | §17.7, §19 | **L4 is fixed**: `emit_l4a` compares the classification of each *named member* and three regression tests are registered | v4r4's `emit_l4` compared level *sets* and asserted replication for the replication that least replicates |
| **C12** | §8.1, §13.9, §17.6 | New **near-form arm**: three Tier-2 controls and $\Delta_{\text{near}}$, with a registered disagreement table against $\Delta_R$ | $\Delta_R$ against a same-form pool answers a narrower question; the tier contrast is what recovers the broader one |
| **C13** | §13.10 | The class arm **inverts**: the broad-class control is budget class where the references are production | v4r4's arrangement put the class mismatch on the quantities that carry the primary claim |
| **C14** | §8.1 | The design is an **admitted set of arms** with a derived cell count, replacing named variants | v4r4's reduced design could not freeze until `VARIANT_EXEMPTIONS` was patched in |
| **C15** | §18 | Eighteen lifecycle stages: `PROTOCOL_REGISTERED`, Gate 2.5, Gate 3A/3B/3C, `PREFREEZE_AUDIT` and `FINAL_REPORT` become **stages** | A check that runs beside the lifecycle can be skipped; a stage cannot |
| **C16** | §7.7, §10.7 | The joint-satisfiability witness must additionally be **realistic**: inside the §8.5 stem band | `CL7`'s reserve runs to 140, and *at least 130 words must contain letter a* cannot be met by any answer of at most 120 words |
| **C17** | §9.1, §19 | §9.1's presence rule becomes mandatory **at every generative stage** | v4r4's calibration scored load-one rows on the present instance only, so $\kappa^{B}$ did not exist in its records |
| **C18** | §28.2 | New statuses: `REFERENCE_SUPPORT_NOT_IDENTIFIED`, `REFERENCE_POOL_SAME_FORM`, `LOCAL_TIER_DISAGREE`, `NEAR_FORM_ARM_NOT_AVAILABLE`, `OPERATING_POINT_AT_GRID_BOUNDARY`; `COMPANION_CLASS_NOT_MATCHED` narrows to the broad-class arm | Each names a failure v4r4 could produce and could not report |
| **C19** | §22, §23 | **Lexical register** is registered as a second mediator with per-cell diagnostics | At matched length the first-stated constraint appeared to determine vocabulary; length did not explain the ordering effect |
| **C20** | §26 | A **primary methodological success criterion**, judged before any composed outcome | v4r4 had no way to say "the counterfactual was identified" separately from "the effect was estimated" |
| **C21** | §33 | A **pre-freeze red-team checklist** of fifteen items, executed as a stage | — |
| **C22** | §30 | An explicit **overfitting declaration** and a five-class v4r4 → v5 reuse ledger | v5's rule is fitted to v4r4 and no artifact may call that validation |
| **C23** | §7.6, §7.10, §13.8 | The Tier-1 **marker vocabulary is measured, not asserted**: a natural-occurrence ceiling of 0.15 benchmarked against $A$'s own 0.104, a 7-letter structural rule, and a declared **discourse role** with a two-role requirement on the core set | `however` itself occurs in 1.3–10.4% of unconstrained responses, so "near zero" would reject $A$'s own marker; and four markers an earlier draft rejected on assumed frequency measure *below* $A$ |

---

## 1. C1 — the core reference pool inverts class

**v4r4.** §7.3: sixteen budget-class families are the reference pool, and §7.3
excludes every production family from it: *"a count lower bound imposes a
length floor, pushing response length up while $B$ pushes it down, which
replaces one length confound with its mirror image."* Production families are
admissible to the class arm alone.

**v5.** §7.4: Tier 1 (exact count of a marker word) and Tier 2 (exact count,
other statistic) are the core pool. The twenty-six budget and lower-bound
families move to the spectrum and to the broad-class slot.

**Why.** v4r3 §13.1 says the reference occupies $A$'s slot and must resemble
$A$. §7.3 then required it to differ from $A$ in class. The two rules
contradict each other, and the exclusion argument is correct only for count
*lower bounds*: an exact count of a four-letter word three times imposes no
length floor.

**The v4r4 evidence.**
[`reference_design_development.md`](../dci1/reports/dci1v5/reference_design_development.md)
§5.2 applies v5's full validity stack to v4r4's own library and measurements:

| pool | e2b | e4b | qwen3-4b | qwen-instruct |
|---|---:|---:|---:|---:|
| budget (v4r4's references), v4r4 rule | 6 | 3 | 3 | 1 |
| budget, full v5 stack | **3** | **0** | **0** | **0** |
| production (v4r4's class pool), v4r4 rule | 4 | 4 | 2 | 3 |
| production, full v5 stack | **4** | **4** | **2** | **3** |

Not one production family is lost at any stage of the stack on any model. And
the one marker family v4r4 carried, `CX1` over *thus*, has $\kappa = 0.0000$
and $\kappa^{B} = 0.0000$ on all four models, the smallest split-half
$\lvert\Delta\iota\rvert$ of any predicate form (median 0.0381 against 0.0764
for count budgets), and an $\iota$ ladder straddling $\iota_A$ on every model.

**What it costs, stated.** `COMPANION_CLASS_NOT_MATCHED` is removed from every
L3 statement and `REFERENCE_POOL_SAME_FORM` replaces it: v5's excess is
relative to companions *very* like $A$, where v4r4's was relative to companions
of a different class. The limitation moves; it does not vanish. §12 below is
the arm that recovers the broader question.

---

## 2. C3, C4 — $\iota$ is demoted and raw compliance rules are added

**v4r4.** §13.4's six conditions are: an $\iota$ caliper of 0.10 with a
Newcombe condition; a pre-screen $\iota$ caliper of 0.15; the wording caliper;
parse independence; witnesses; a vacuity ceiling; and budget class. `κ` is
bounded only by `CHANCE_DEGENERACY_MAX = 0.99`. **No rule reads raw solo
compliance.**

**v5.** §13.1's eight components, evaluated lexicographically with $V_{\text{diff}}$
**last**; §13.4 adds the Wilson interval for $p_{\text{solo}}$ inside
$[0.10, 0.90]$, an instruction-lift floor of 0.20, and a chance ceiling of 0.75
on the point with 0.85 on the Wilson upper bound.

**The v4r4 evidence.** `qwen3-4b-instruct-2507` terminated at Gate 4 on a
**solo** cell: `CL8:3`, *at least 3 words must end with y*, at calibration solo
0.9740 and chance 0.9323, admitted because $\lvert\iota - \iota_A\rvert =
0.0191$ was the smallest of any eligible production rung, and observed at
0.9896 against a 0.95 ceiling. §13.7 admitted on $\iota$; §13.10 checked the
raw rate; nothing between them checked the raw rate. Five further rungs across
the four models sat inside the caliper with raw solo compliance above 0.90,
including `RF2:6` on `qwen3-4b` at distance 0.0060 and chance 0.8203.

**Where the values come from.** $[0.10, 0.90]$ is Gate 4's $(0.05, 0.95)$
contracted by 0.05 a side, on the interval and not the point. The lift floor of
0.20 is two SESOI, because $D(R \leftarrow B) \le H_R$ and a reference with
$H_R < 0.20$ has its reciprocal loss bounded by the design. The chance ceiling
of 0.75 is where measured split-half $\lvert\Delta\iota\rvert$ reaches roughly
three times the chance-free value (0.195 against 0.044) while the
$1/(1-\kappa)$ amplification is still single digit.

---

## 3. C5 — the interaction gate

**v4r4.** Nothing. §13.10's composed-headroom check is the first and only place
composition is inspected, and it is a terminal gate rather than a filter.

**v5.** §13.6. Under §9.1's presence rule every candidate's verifier is already
run on responses written under $B$ **alone**, giving

$$\kappa^{B}_R = P(X_R = 1 \mid B \text{ alone at } m^*,\ R \text{ absent}),$$

at **zero extra generations**. The gate is

$$0.10 \;\le\; \hat p_R = \kappa^{B}_R + \iota_R(1 - \kappa^{B}_R) \;\le\; 0.90,
\qquad \lvert \kappa^{B}_R - \kappa_R \rvert \le 0.25 .$$

**The v4r4 evidence.** All five of `gemma-3n-e2b-it`'s Gate-4 failures involve
`RF11` composed with $B$: $B$ shortens answers, `RF11`'s vowel-initial count
falls from ≈24 to ≈17, and a budget of 26 becomes trivial. Recomputed with the
registered verifiers on the stored $B$-solo calibration responses,
$\kappa^{B}$(`RF11:26`) $= 0.833$ against $\kappa = 0.148$, and
$\kappa^{B}$(`RF11:32`) $= 0.964$ against $0.445$. Against `gemma-3n-e2b-it`'s
20 observed Gate-4 rate checks the projection had a median absolute error of
0.067 and, at a ceiling of 0.90, caught 4 of 4 failures with 0 false alarms.

**Not outcome-based selection.** $\Delta_R$ reads $X_B$ in the $B{+}R_j$ cells;
$\kappa^{B}_R$ reads $X_R$ in the $B$-solo cell and observes $B$'s compliance
nowhere. The residual-bias direction is conservative: a reference $B$ makes
trivial would show a small $D(B \leftarrow R_j)$ and therefore a **large**
$\Delta_R$, so excluding it works against $H_{\text{pair}}$.

**Not a family-specific exception.** The rule names a property of the pair
(statistic, focal constraint) and measures it. It is not *"exclude `RF11`"*.

**Twenty rate checks on one model is design fitting**, the ceiling is derived
from the band and a 0.05 error allowance rather than from the observed gap, and
§34 D7 records it as a decision.

---

## 4. C6, C7 — two calibration splits, and a high-recall screen

**v4r4.** One calibration set of 96 topics; a pre-screen of 24 topics at one
draw used as a hard selector, with a 0.15 pre-screen $\iota$ caliper as its
winner's-curse protection.

**v5.** Calibration-A and Calibration-B, 96 topics each, disjoint; the
pre-screen caliper **removed**; §12.2's retention rule keeps every Tier-1 and
Tier-2 rung regardless of pre-screen estimate and keeps a Tier-3 rung whose
pre-screen Wilson interval intersects $[0.05, 0.95]$; §13.7 requires
independent admissibility on both splits plus 95% bootstrap intervals for the
split differences of $\iota$ and $p_{\text{solo}}$ inside $\pm 0.20$.

**The v4r4 evidence.** Pre-screen → calibration $\lvert\Delta\iota\rvert$ has
median 0.0709 and 35.7% of candidates move further than the whole 0.10 caliper;
$\iota_A$ itself moves by up to 0.048. Straddling-family support fell 7→3, 5→0,
4→2 and 4→0. A clean split-half at fixed $n$ gives SE($\iota$) = 0.0477 at 96
topics, so **v4r4's caliper is 2.10 SE wide**; at 192 topics it is 2.96 SE.

**The caliper does not move, deliberately.** Tightening it would select harder
on a coordinate whose error is the size of the window. What changes is the
sample.

**Why an equivalence rule for stability.** A threshold on the point difference
rewards an imprecisely measured candidate; requiring the interval to lie inside
a bound penalises imprecision, which is the right direction for a gate asking
*can this candidate's coordinate be shown stable?* $\pm 0.20$ is twice the
matching caliper.

---

## 5. C8 — support oversupply

| Requirement | v4r4 | v5 |
|---|---:|---:|
| straddling feature groups at coverage (C4) | 4 | **6** |
| eligible rungs within 0.15 of $\iota_A$ (C3) | 6 from 3 groups | **8 from 4 groups** |
| eligible rungs in total (C5) | 12 | **16** |
| eligible families at coverage (C6) | 6 from 4 groups | **8 Tier-1/2 from 6 groups** |
| families passing the full admission rule | 3 | **5** |
| core references used | 3 | 3 |
| frozen unused backups | **0** | **2** |

**The v4r4 evidence.** v4r4 registered "three groups plus one spare" and
measured 50–100% attrition between the two stages on all four replications.
`gemma-3n-e2b-it` reached three core references with `RF6` admitted but unable
to straddle — no spare at all.

**The backups are not a substitution mechanism.** §13.14 forbids substituting
one into a design after Gate 4, and §19's test 4 requires that the substitution
path **not exist**. They exist so the support requirement is a real requirement
and so a future version has a documented pre-committed pool.

---

## 6. C9 — the focal grid and the bracketing rule

| | v4r4 | v5 |
|---|---|---|
| focal grid | $\{7,8,9,10\}$ | $\{7,\dots,14\}$ |
| extension | $\{11,12\}$ | $\{15,16\}$ |
| bracketing | none | both neighbours of $m^*$ measured at calibration |
| boundary status | none | `OPERATING_POINT_AT_GRID_BOUNDARY` |

**The v4r4 evidence.** $m^*$ was the last measured rung on **all four**
replications, not only the one that needed the extension. `qwen3-4b`'s B curve
over $m = 7\dots12$ is $0.031, 0.107, 0.245, 0.411, 0.659, 0.742$ against a
band of $(0.60, 0.95)$: only the two extension rungs were in band and 12 was
the top of the extension.

**$n^*$ keeps its grid.** $n = 0$ is a well-formed exact count whose chance
compliance is near one, so it is chance-degenerate and is not admitted. Where
$n^* = 1$ the record carries `OPERATING_POINT_AT_GRID_BOUNDARY` with that
reason rather than a manufactured terminal status.

---

## 7. C10 — direct order estimands

**v4r4.** §11.1 indexes every estimand by configuration and §28.1 pairs
*Replication* with *Configuration dependence*. **No cross-configuration
contrast is registered**, `FAMILY_MEMBERS` contains no order member, and the
records store no bootstrap replicates — so the question could not be answered
during the study and cannot be answered from its artifacts afterwards.

**v5.** §11.7 registers five contrasts in family **F11**, declared across
configurations, licensing claim level **L4b**:

$$\text{Ord}_A,\quad \text{Ord}_B,\quad \text{Ord}_\Lambda = \text{Ord}_B - \text{Ord}_A,\quad \text{Ord}_{\bar R},\quad \text{Ord}_{CL}.$$

Each is a paired within-block difference of two composed cells; the solo
baseline cancels and they are position-clean. F1's membership is unchanged, so
no primary interval widens. $\text{Ord}_\Lambda$'s linear dependence on the
other two is declared rather than hidden.

**The v4r4 evidence.** On `gemma-3n-e4b-it`, $\Lambda = -0.1097$
$[-0.155, -0.065]$ in `outcome_first` and $+0.3154$ $[+0.259, +0.371]$ in
`outcome_second` — both simultaneous intervals excluding zero, a difference of
0.425, and no registered way to say whether the *difference* is supported.

**What it licenses and what it does not.** An interval excluding zero licenses
*the quantity depends on the position of the outcome constraint*. It licenses
no statement about why. An interval containing zero is not order-invariance
unless §17.3's equivalence rule and its precision precondition are met, and the
emitter refuses the word.

---

## 8. C11 — the L4 fix

**The v4r4 defect.** `analysis.claims.emit_l4` received
`per_configuration: Mapping[configuration, Sequence[level]]` and compared the
**sets** of levels reached. `run/analysis_run.py` built that input as
`[s["claim_level"] for s in statements if emitted]`, discarding member identity
before the emitter could see it. For `gemma-3n-e4b-it`, $D(A\leftarrow B)$
reached L1 in `outcome_first` only and $D(B\leftarrow A)$ in `outcome_second`
only, so both configurations' sets were `{L1}`, they matched, and the emitted
L4 asserted replication. §3.2 licenses L1 on *"the named $D(c \leftarrow g)$"*
and §28.1's two rows are both about **a named quantity**: the gate is per
member.

**Scope.** Exactly one emitted statement in v4r4 is invalidated —
`gemma-3n-e4b-it`'s `claims.L4`. `qwen3-4b`'s L4 is valid under both readings,
and all 44 ladder rows stand: `emit_l4` reads already-emitted statements and
enters no estimate, interval, bootstrap draw, precision check or licensing
decision.

**Why v4r4 could not repair it.** `run_unmasked_analysis` refuses an unmasked
analysis under an `analysis_code_hash` differing from the masked seal, and §20
forbids re-masking after unmasking. The commitment device worked and bound the
author of the defect.

**The v5 fix.** §17.7 registers

```
emit_l4a(*, per_member: Mapping[str, Mapping[str, str | None]], ...)
```

licensed iff every registered configuration appears for every member, at least
one member reached a classification, and **for every member the classification
is identical across every configuration**. §19 registers three tests that must
exist and pass before qualification: v4r4's `gemma-3n-e4b-it` pattern must not
emit; v4r4's `qwen3-4b` pattern must emit; and the emitter must be uncallable
with a bare sequence of levels.

**v4r4's field is not recomputed.** The fix is prospective and repairs nothing
retrospectively.

---

## 9. C12, C13 — the near-form arm, and the class arm inverts

**v4r4.** One production-class class-control companion beside $B$, admitted on
$\iota$ alone, giving $\Delta_{\text{class}}$.

**v5.** Three Tier-2 near-form controls beside $B$, giving
$\Delta_{\text{near}}$ (§13.9), **and** one Tier-3 budget-class control beside
$B$, giving $\Delta_{\text{broad}}$ (§13.10). §17.6 registers a second
disagreement table for $(\Delta_R, \Delta_{\text{near}})$ with
`LOCAL_TIER_DISAGREE` on the two rows where they classify differently.

**The v4r4 evidence.** `Δ_class` was $+0.0114$ / $+0.0384$ on `qwen3-4b`, whose
class companion `CX1:4` is $A$'s own form with one word changed, and $-0.3102$
/ $-0.5114$ on `gemma-3n-e4b-it`, whose `CL7:80` forces a long letter-a-rich
answer. Both are "one production companion matched on $\iota$". $\iota$ is
blind to form and $\Delta_{\text{class}}$ was not one quantity measured twice.

**Why the inversion.** v4r4 put the class mismatch on the *references* — the
quantities carrying the primary claim — and matched the class control to $A$'s
class. v5 does the reverse: the references match $A$'s class and form, and the
one companion of a different class is a secondary bound.

---

## 10. C14 — arms, not variants

**v4r4.** Three named variants — `full` (47), `no_spectrum` (29, unreachable in
code) and `reduced` (8) — with `VARIANT_EXEMPTIONS` mapping each to the freeze
fields it may leave empty.

**v5.** §8.1's five arms are admitted independently and the cell count is
derived: 56 with all of them, down to 5 with the base alone. §18.1 refuses an
empty freeze field that no identification status explains.

**The v4r4 evidence.** The reduced design could not freeze at all until
`VARIANT_EXEMPTIONS` was added, because three fields it legitimately leaves
empty were read as missing. A named variant is a fourth thing to keep in sync
with the cell plan, the freeze schema and the analysis.

---

## 10b. C23 — the marker vocabulary is measured

**v4r4.** One marker family, `CX1` over *thus*, chosen because it is $A$'s rule
with one word changed.

**v5.** Eight, chosen by three rules of which two are measured on the
predecessor study's unconstrained development responses
(`d6_marker_frequency.json`): at most seven letters, so the family is jointly
satisfiable with $B$ at every admissible $m$; and
$P(\ge 1 \text{ occurrence} \mid \text{unconstrained}) \le 0.15$ on every
registered model.

**The benchmark is $A$, not zero.** `however` appears in **1.3% to 10.4%** of
unconstrained responses, so a rule demanding "near zero" would reject $A$'s own
marker. 0.15 is about 1.5 times $A$'s measured maximum.

| registered | thus 0.057 · hence 0.000 · though 0.013 · whereas 0.013 · indeed 0.000 · namely 0.000 · instead 0.021 · overall 0.112 |
|---|---|
| reserve | notably 0.000 · albeit 0.013 · besides 0.000 |
| rejected on frequency | **finally 0.185** · **also 0.419** |
| rejected on length | moreover, likewise (8) · therefore, meanwhile, otherwise (9) · conversely (10) · nonetheless (11) |

**Two corrections the measurement forced on an earlier draft of this design.**
It rejected `also`, `then`, `next`, `yet` and `still` on an assertion of high
natural frequency; the measurement supports that for **`also` alone** — `then`
0.039, `next` 0.021, `yet` 0.005 and `still` 0.018 are all *below* $A$'s own
rate, and they are excluded on a stated different ground. And it registered
`finally`, which the measurement rejects at 0.185.

**Discourse role.** $A$ is a **contrastive** connective. Every marker declares
a role; §13.8 requires the three core references to span at least two roles and
records `REFERENCE_ROLE_NOT_MATCHED` when none is contrastive. Two of the eight
registered markers are contrastive (`though`, `whereas`), so the matched case
is reachable. §29 records that role is a declared label and that nothing in
this design measures whether a model treats *though* and *however* as the same
kind of connective.

---

## 11. C15, C16, C17 — lifecycle, witnesses, presence

**Lifecycle.** v4r4's twelve stages become eighteen. `PROTOCOL_REGISTERED`
makes §34's open decisions a gate rather than a promise; Gate 2.5 gives the
pre-composition validity components a stage of their own; Gate 3A/3B/3C
separate calibration, selection and identification so that each writes its own
signed record; `PREFREEZE_AUDIT` and `FINAL_REPORT` become stages, because in
v4r4 both were tools and a tool can be skipped.

**Realistic witnesses.** v4r4's §7.5 obligation is formal: a machine-verified
response satisfying both constraints. `CL7:80` has one at every admissible $m$
and is unreachable for a model writing 60–120 words under a maximum-word-length
budget. v5 §7.7 requires the witness to lie inside the stem band.

**The presence rule.** v4r3 §9.1 requires every generation to be scored on
every registered instance. v4r4's Gate-2 calibration scored load-one rows on
the present instance only, so $\kappa^{B}$ did not exist in its records and had
to be recomputed from raw responses for the development analysis. v5 makes the
rule mandatory at every generative stage and asserts it at qualification and in
the pilot — which is what makes §13.6 free.

---

## 12. What v5 keeps unchanged

Carried in substance and restated in full, because v5 is standalone:

1. The core scientific question and `dci-construct-pass2.md` §G row 1's two
   $\Delta_R$ thresholds, 0.10 and 0.25, verbatim.
2. $A$ as an exact-count marker constraint and $B$ as a maximum-word-length
   constraint.
3. The directional delivery-loss definitions, $\Lambda$, $\Delta_j$,
   $\Delta_R$, $\delta_{\text{diff}}$ and $\Xi$ as concepts and as formulas.
4. The reciprocal and reference-on-reference effects, and the five-constraint
   core matrix that identifies $\Xi$.
5. The deterministic verifier architecture and §10.1's six invariants.
6. Gate 1 in full: the specification audit, A′'s prose-to-predicate invariant
   and its direction lexicon, deterministic implementation validation, the
   independent prose-only reimplementation, mutation testing over the six
   defect classes, witnesses, wording hashes and provenance hashes.
7. `measurement_basis = deterministic_measurement_validated` and §10.5's scope
   sentence, attached permanently at every rung.
8. Topic-set separation, the development/reserved split, and the audit over
   generated rows rather than source.
9. Masking, the stratified draw, and irreversible unmasking.
10. Multiplicity-aware simultaneous intervals by studentised maximum modulus,
    the 10,000-resample block bootstrap, and the refit loop.
11. Stage-record signing, durable copies, evidence manifests and the closed
    artifact-type vocabulary.
12. No post-gate criterion weakening; a gate failure is a result.
13. Explicit terminal and identification statuses, and the sentence *a terminal
    pre-confirmatory status carries no evidence about the effect*.
14. "Not significant" is never "no effect": §17.3's guarded equivalence
    function is the only route to an absence statement.
15. 384 blocks, $M = 8$, and §16's absolute precision preconditions with no
    effect estimate entering the calculation.
16. The four registered model checkpoints.
17. The §12.4 regime-adequacy conditions and the share reading of its graded
    clause.
18. The §9.3 non-vacuity predicates, the 20-word threshold and the
    vacuity-forced partial-identification recomputation.
19. §22's prohibition on conditioning on post-treatment quantities.

**The verifier-validation architecture is not reopened**, and §33 item 13
requires the pre-freeze audit to diff v5 §10.7 against v4r4's and enumerate
every difference.

---

## 13. Dispositions of v4r4 quantities

| Quantity | Disposition | Reason |
|---|---|---|
| Budget-class families as the reference pool | **Moved** to the spectrum and broad-class arms | Every v5 validity gate removes them on three of four models |
| Exact-count marker families as class-arm-only | **Promoted** to the core reference pool | Chance-free, interaction-free, same-form with $A$, tunable in difficulty |
| `CX1`, `CX2` | **Relabelled** `MK1`, `XC1`; instruments carried byte-identically | They are Tier 1 and Tier 2 under v5's taxonomy |
| `FORM_RATE_LOWER_BOUND` | **Retained in the grammar, instantiated by no family** | v4r4 removed `CP4`/`CP7` on a §10.7 A′ wording finding and v5 does not restore them |
| $\iota$ as the admission coordinate | **Demoted** to the difficulty coordinate, evaluated last | A ratio with a denominator near zero is not a certificate of comparability |
| Raw solo compliance | **Promoted** from a reported secondary to a registered admission gate and a secondary matching check | It is what Gate 4 checks and nothing before Gate 4 checked it |
| `CHANCE_DEGENERACY_MAX = 0.99` | **Retained** as the degeneracy guard; **superseded** as a ceiling by §13.4's 0.75 | 0.99 is where $\iota$ is undefined, not where it is usable |
| The pre-screen distance caliper (v4r4 §13.4 condition 2) | **Removed** | It selected on a coordinate whose error exceeds the caliper; §13.7's two-split rule replaces it at a sample size that can support it |
| `REFERENCE_CALIPER = 0.10`, `REFERENCE_NEWCOMBE_REGION = 0.05` | **Retained unchanged** | Tightening would select harder on noise; the sample doubles instead |
| `REFERENCE_VACUITY_MAX = 0.10` | **Retained unchanged** | It rejected two rungs in v4r4 and mis-rejected none |
| Named design variants | **Superseded** by an admitted arm set with a derived cell count | |
| $\Delta_{\text{class}}$ | **Split** into $\Delta_{\text{near}}$ (Tier 2) and $\Delta_{\text{broad}}$ (Tier 3 budget) | One quantity was measuring two different things on two models |
| `COMPANION_CLASS_NOT_MATCHED` on every L3 statement | **Narrowed** to statements about $\Delta_{\text{broad}}$; **replaced** on L3 by `REFERENCE_POOL_SAME_FORM` | The class mismatch moved off the primary quantities and onto the secondary one |
| `emit_l4` | **Superseded** by `emit_l4a` (per named member) and `emit_l4b` (order) | v4r4's compared level sets |
| $H_{\text{order}}$ handled "by construction" | **Superseded** by registered contrasts in F11 | Reporting configurations separately is not a test |
| v4r4's confirmatory estimates | **Historical outcome.** Never a v5 observation, never re-analysed, never used to size v5 | §30's ledger |
| v4r4's Gate-2 tables and `gemma-3n-e2b-it`'s Gate-4 table | **Development evidence** for v5's design | §30's ledger; and the Gate-4 table remains viability material on a terminated replication |
| v4r4's two terminations | **Preserved unmodified.** The replications are re-entered under v5 because v5's rule rejects the responsible companions before Gate 4 | Re-entry under a new protocol is not a repair of a v4r4 outcome |

---

## 14. What was decided, and what remains a limitation

v5 §34 carried **nineteen** registered open decisions, D0 to D18, every one of
which had to be closed in the signed registration manifest before stage 1 could
pass. D15 to D18 came from the pre-freeze red-team and D6 was reopened by it.
**All nineteen are now taken**, U2 is resolved at A2 and P1 is confirmed.

### Four were taken first (2026-08-22)

Recorded with their evidence in
`dci1/reports/dci1v5/researcher_decisions.json`, which `protocol/decisions.py`
reads at import and the registration manifest binds by hash. **Two went against
this document's standing proposal**, and those two change what v5 is:

- **D18 — the near-form arm is a precondition of the *strong* L3c.** L3c now
  carries a registered scope. `strong` — *no pair-specific excess*, the source
  memo's refutation verdict — requires the near-form arm to have run;
  `same_form_only` is what a same-form Tier-1 pool alone licenses, and it is
  what a replication without the arm emits. The strong conclusion is
  **unreachable** without the arm, which is the gate R1 asked for in place of a
  qualifying sentence. **This is why the 47-cell compute option is no longer a
  cheaper version of the same study.**
- **D16 — Calibration-B measures the complete carried population**, not
  Calibration-A's survivors. §13.7 becomes a test of the candidate landscape's
  stability rather than a re-confirmation of an already-selected set, which is
  what R11 says "independent" otherwise overstates. About 35,000 further
  generations per replication, accepted. What is *not* accepted is accidental
  repetition: a row whose complete scientific identity already exists is
  reused, and the **split is part of that identity**, so no Calibration-A row
  can ever satisfy a Calibration-B one.
- **D6 — `REFERENCE_SUPPORT_NOT_IDENTIFIED` stays an identification status,
  and the non-identification is irreversible.** A replication that cannot build
  its reference set continues and keeps every estimand that does not need one;
  the reference-dependent set is derived by one rule, frozen, and four
  rehabilitation paths are refused by name — including an observed composed
  outcome being read as evidence the pool was adequate after all, which is the
  observe-then-choose loop §30 forbids.
- **D3 — the 96 Calibration-B questions are authored.** They exist, at
  `dci1/src/dci1v5/topics/data/calibration_b_v5.json`, authored before any v5
  measurement or selection outcome existed, disjoint from all five other sets
  in id and in text, hashed into the manifest.

### The remaining fifteen, U2 and P1 (2026-08-23)

`dci1/reports/dci1v5/v5_adoption_checklist.md` is the one-page record. Four had
evidence-backed recommendations and all four were approved as recommended:

- **D1, the compute budget — `four_models_56_cells`.** All five arms, four
  models, 56 cells, 384 blocks, $M = 8$: **1,144,896** generations, derived by
  `dci1v5.design.budget` from the code's own constants and bound into the
  manifest, so the figure the signature carries is one the code reproduces.
  The near-form arm is *registered* rather than merely permitted, which is what
  makes R1's mitigation part of the design.
- **D4, the Tier-1 marker vocabulary — `approve_eight`.** All eight stand.
  `though`, `namely` and `overall` each carried a judgement the rules do not
  settle, and all three were kept as **accepted limitations**: they are
  registered by name, bound into the manifest, and reported alongside
  `REFERENCE_POOL_SAME_FORM` on every L3 statement, so "approved" cannot be
  read as "no concern was found". A population hash over the eight makes a
  substitution detectable rather than merely forbidden.
- **D17, a construct floor for B — $\kappa^{B}(m^{*}) \le 0.50$**, on the
  **point** estimate, with the Wilson bound reported beside it and
  `CONSTRUCT_FLOOR_MARGINAL` when the interval straddles it. A selected $m^*$
  that satisfies §12.3's compliance band and fails the floor ends the
  replication at `FOCAL_RANGE_EXHAUSTED` before anything confirmatory is
  generated. The threshold is a field of the closure record, not a constant in
  the source. **Closing it exposed an estimator defect**: Gate 2's registered
  chance rate averages every row where the severity was absent — including the
  $B$-solo cells at other severities — while the threshold was derived on
  load-zero answers. Both are now computed and recorded; the floor reads the
  load-zero one and every other chance quantity is untouched.
- **U2, §11.8's singular secondary fit — A2.** $\alpha_f$ over the three
  **core** families; a Tier-2 point at the unweighted mean core intercept plus
  $\gamma$. §11.8's sentence is amended to say so. A4 stays constructed and
  non-adopted, because the evidence for preferring A2 is computed from it on
  every test run.

The other eleven — D0, D2, D5, D7–D15 — closed at this document's own standing
proposal. **Two carry a recorded objection the closure does not answer**: R13
against D7's 0.90 interaction ceiling, and R2 against D15's transfer of the
memo's 0.10 and 0.25 to a same-form $\Delta_R$. Both objections are bound into
the manifest beside the value. **P1** is confirmed: Tier 3 takes the
broad-class role only and was *not* made spectrum-eligible.

### What no decision closed

**R5.** $\kappa^{B}$ is measured under $B$, so the reference set is a function
of how each model writes under its own $B$ at its own $m^*$: the set is not
exchangeable across models and neither is $\Delta_R$'s meaning. §13.8's
`INTERACTION_ESTIMATE_DRIFTED` closes the second half of the finding; no rule
closes the first. It is an **accepted permanent limitation**, reported
separately from the blocking findings in every audit, and it is why no
cross-model scalar carries a claim.

**R22 and R23 are registered rather than resolved**, and they are what comes
next: the full design has never been executed on any revision — §19's
procedural pilot at stage 3 is the mitigation, and it is the first stage that
generates a model response — and the Tier-1 pool has never been measured, which
Gate 1 at stage 5 does, over the regime screen's own generated text. Stage 1
has run, because it is the stage that signs the registration manifest; nothing
after it has.
