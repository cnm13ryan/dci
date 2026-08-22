# DCI-1 v5 — document reconciliation

Every discrepancy found while implementing v5 in `dci1/src/dci1v5/`, classified
as the implementation prompt requires: **stale documentation**, **unresolved
scientific choice**, **implementation defect**, or **true protocol
contradiction**. Stale documentation and implementation defects were fixed;
the other two are escalated here and nothing was silently edited to make
documents agree.

**No threshold, band, count or rule moved.** Every fix below is a name, a
cross-reference or a stale value that contradicted its own neighbour.

---

## 1. Stale documentation — fixed

| # | Where | What it said | What it says now | Why the change is safe |
|---|---|---|---|---|
| S1 | `DCI1_v4r4_to_v5_changelog.md` §14 | "v5 §34 carries **fourteen** registered open decisions" | nineteen, D0 to D18 | §34's own table lists D0–D18 and says "all nineteen"; the changelog was written against an earlier draft |
| S2 | same, D4 bullet | the eight markers were "chosen on three prospective rules, **none of them measured on any model**" | two of the three rules **are** measured on the predecessor study's unconstrained responses; what is not measured is any marker's behaviour *as a constraint* | §7.6 rule 3 and §7.10's table quote measured occurrence rates per marker; the unmeasured thing is the difficulty coordinate, which §6.2 states separately |
| S3 | `reference_design_spec.json` `what_this_spec_does_not_decide[0]` | "section 33 leaves as a researcher decision" | section 34, decision D1 | §33 is the red-team checklist; §34 is the open decisions |
| S4 | same, `support_requirements` | key named `terminal_status_when_unmet` | `status_when_unmet`, plus `status_when_unmet_is_terminal: false` and a note naming D6 and R16 | §13.15 says in terms that `REFERENCE_SUPPORT_NOT_IDENTIFIED` is "an identification status, **not** a stage-terminal one"; the key name contradicted the value's own meaning. §13.1: the preregistration governs and the file is repaired |
| S5 | same, `structural_taxonomy.tiers` | Tier 1's `eligible_slots` included `class_same_form` | `core_reference`, `spectrum` | no slot of that name exists anywhere; §7.4's slot table registers four |
| S6 | same, Tier 3 | `eligible_slots: [spectrum, broad_class_control]` | `broad_class_control`, with a note | see the escalation P1 below: no rule can put a Tier-3 family in a spectrum slot |
| S7 | same, `tier2_near_form_families` | statistic `comma_character` | `comma` | the registered statistic identifier is `comma`; §7.6 names it |
| S8 | `DCI1_preregistration_v5.md` §7.6 | the registered marker statistics were listed as `marker_thus, marker_hence, marker_indeed, marker_namely, **marker_notably**, marker_overall, marker_instead, **marker_finally**` | `marker_thus, marker_hence, marker_though, marker_whereas, marker_indeed, marker_namely, marker_instead, marker_overall` | §7.6's own rule 3 **rejects** `finally` at 0.185, and §7.10's registered table carries `though` and `whereas` with `notably` as a *reserve* marker. The list contradicted the two paragraphs beside it |

---

## 2. Under-specification — one reading implemented, recorded here

None of these is a contradiction; each is a rule the preregistration states
without saying how to compute one of its terms. In every case exactly one
reading is executable, the implementation takes it, and the code says so where
it is taken.

### U1. §13.8's discourse-role spread, and what a Tier-2 member contributes

§13.8 requires the three core references to "span at least two declared
discourse roles" and describes a substitution when "the three otherwise-chosen
references share one role". §7.6 assigns a discourse role to **marker**
families and to no others, so a Tier-2 member has none — and §13.8 does not
say what it contributes to the count.

**Implemented:** `none` is not a role. `protocol/taxonomy.declared_roles`
counts only members that declare one. §13.15 guarantees at least two Tier-1
members, so at least two members always declare a role and the requirement is
always well defined under this reading.

**The alternative** — counting `none` — would let a set of two same-role
markers and one Tier-2 control satisfy a rule written to make the pool span
discourse function. `assert_core_set_structure` records both the counted set
and the set as declared, so a reader can see which reading produced the
verdict.

### U2. §11.8's tier-indicator secondary fit is not identified as written

§11.8 registers `Y = alpha_f + beta*d + gamma*1[Tier 2]` over twelve points
and does not say what `alpha_f` is for the three near-form controls. Giving
each of them its own family intercept makes `gamma` **exactly collinear** with
the sum of those three dummies: the design matrix is singular and `gamma`
identifies nothing.

**Implemented:** `alpha_f` ranges over the three **core** families, and a
Tier-2 point sits at the average core intercept plus `gamma`, so `gamma` is
the tier's offset from the difficulty line the core families define.
`analysis/spectrum.fit_with_tier_indicator` says this in its docstring and
refuses the singular alternative by name. `gamma` is an F8 secondary and
licenses no claim, so the reading changes no decision rule.

### U3. "The less restrictive severity breaks an exact within-family tie"

§13.8 states the tie-break and leaves the word to the form. For a budget
(`<=`) a larger q admits more answers; for a lower bound (`>=`) and for an
exact count (`==`) a smaller q does — and §7.10 states the exact-count
direction in its own words: *"Higher q is harder, so extending the reserve
extends the span downward in iota"*.

**Implemented:** `stages/selection.restrictiveness_key`, derived from the
family's form. The same function fixes §12.6's expansion direction, which a
severity-value reading would have sent the wrong way for a marker ladder —
into the *non*-deficient side §7.10 widened the reserve to reach.

---

## 3. True protocol tension — escalated, nothing edited in the preregistration

### P1. §7.10 admits Tier 3 "to the spectrum"; §7.4 and §13.12 make that unreachable

§7.10 says the twenty-six Tier-3 families are "admissible to the spectrum and
to the broad-class slot only". §7.4's slot table says a spectrum rung's
admissible tier is "the tier of its own core family, because §13.12 draws both
rungs from that same family", and §7.4 admits Tier 1 and Tier 2 to the core
slot alone.

Both cannot be exercised: a Tier-3 family can never supply a spectrum rung,
because a spectrum rung belongs to an admitted **core** reference's family and
no Tier-3 family can be one.

**Operationally the two agree** — under either reading no Tier-3 rung reaches
the spectrum — so this changes no verdict, and the implementation follows §7.4
and §13.12, which are the rules with an executable form
(`assert_tier_admits_slot` requires the core family's tier for that slot).
**It is escalated rather than fixed** because narrowing §7.10's sentence is a
scientific edit and the researcher should make it, and because the sentence is
the only place a reader would learn that a Tier-3 spectrum was ever
contemplated.

---

## 4. Findings the implementation produced, which are not discrepancies

### F1. §7.7's realistic-witness rule finds four unreachable rungs, not two

§7.7 names `CL7:130` and `CL7:140` as formally satisfiable and unreachable
inside the 60–120 word stem band. Computed over the whole declared range
against B at every admissible severity,
`verifiers/realistic_witness.run_realistic_suite` finds **`CL7:125`, `130`,
`135` and `140`** and nothing else in the library. The general statement — a
count lower bound over `letter_a` above about 120 has no witness inside the
band — is what the preregistration's two examples illustrate, and 125 and 135
are reserve rungs of the same family.

### F2. `assert_feature_words_are_specific` cannot hold unconditionally in v5

v4r4's witness constructor chose every feature word for orthogonality, so no
breaking word carried a second registered feature. v5's eight marker words are
**registered by §7.6** and their letters are what English makes them:
`whereas` contains an `a` and ends in `s`, `indeed` has a doubled letter and
is vowel-initial, `overall` has both, `though` is t-initial, `namely` contains
an `a` and ends in `y`.

None of that is a design defect and none can be designed away without changing
the marker vocabulary. What matters is whether a collision can occur **in a
cell**, and it cannot: every colliding numerator belongs to a Tier-3 family,
§7.4 admits Tier 3 to the broad-class slot alone, and §13.10 places a
broad-class companion beside B only. The check therefore asks
`assert_pair_realisable` rather than assuming, and records every tolerated
collateral feature with the reason it cannot bite.

### F3. `joint_witness` had to be generalised before v5's pool could pass

v4r4's constructor satisfied only the **first** exact-count constraint of a
pair and built an exact *sentence* count as loose terminators followed by
filler — which §9.2's rule counts as one sentence too many. Neither mattered
in v4r4, whose library held one exact-count reference family and no
sentence-exact family. In v5 both are ordinary: a realisable pair can carry
two exact counts (a marker family and a near-form family from different
feature groups), and `XC3` is an exact sentence count.

With both generalised the suite discharges **20,332 realisable pairs with zero
joint-satisfiability and zero non-entailment failures**. This is a latent
defect in carried code that v5's library exercises, found by running the
carried suite over the new population rather than by reading it — which is
what §29 of the implementation prompt asks characterization to do.

### F4. v4r4's `stages/library.py` is not carried

It is keyed on v4r4's `role` field (`reference` / `class_control`), which v5
replaces with the structural tier, and everything it did — §12.2's retention,
§12.6's coverage criterion and expansion, §12.7's budget — is in
`stages/regime.py` under v5's rules. Carrying a stale role-keyed module would
be exactly the unexecuted downstream path with a latent contract defect that
this repository has already been bitten by.
