# 02 — Introduction outline

Step 2 of the process. Follows `guidelines-introduction.md`: the introduction is
an extended abstract. Source shorthand is defined in `01_narrative.md`.

Claim order below is the order the body will present evidence in, and the order
the contributions list ends on: **C2 leads** because the body's evidence runs
that way — the gates first, then what survived them — and C1 supplies what
survived. **This ordering is not a claim about which contribution is larger or
newer**; that is unresolved pending CITE-02 and CITE-03 (`GAPS.md`). Provenance
and the commitment device are reported in §2.7 and §6.1 and are **not** claimed.

---

## ¶1 — Context

- **Opener (draft).** "Deployed prompts routinely carry more than one verifiable
  instruction, and models satisfy some and abandon others."
- The practitioner question: when two instructions are composed, is each still
  delivered, and does the answer depend on which instructions they are?
- The scientific question underneath it: *directional constraint interference* —
  does instruction *B* damage compliance with instruction *A* beyond what any
  companion of the same difficulty would? `TODO(CITE)` for the field-level
  framing and for prior instruction-following benchmarks.
- Name the identification problem in one sentence, because it is the paper's
  subject: adding *B* changes both the identity of the instruction set and its
  size, so a degradation observed on addition confounds *B* with the generic
  cost of a second instruction. The fix is replacement, not addition — compare
  *A+B* against *A+R* for a reference *R* matched on difficulty.
- **Closer (draft).** "This paper reports what happens when that replacement
  design is preregistered, gated, and run: the replacement contrast was not
  identified on any of four model checkpoints, and the gate records say why."

## ¶2 — Technical background

- Define the two constraints without jargon: *A* is an exact-count production
  constraint, *B* is a word-length budget constraint. Both are scored by
  deterministic verifiers.
- Define the primitive: the compliance vector of a prompt — for every
  instruction present, whether its verifier passes.
- Define the estimand: `D(c←g)` = solo compliance of *c* minus composed
  compliance of *c* when *g* is present. It is directional, solo-anchored, and
  it contains the generic cost of a second instruction. State this explicitly
  here, because it is what separates `D` from `Delta_R`.
- Define the companion contrast the design exists to form: `Delta_R` =
  `D(B←A)` − mean over admitted references of `D(B←R_j)`. Instruction count is
  held fixed. **Companion identity and structural class move together**, because
  §13.7 admits only budget-class families to the core pool while *A* is
  production-class; `Delta_R` is the excess of *A* over budget-class companions
  matched on ι, and `COMPANION_CLASS_NOT_MATCHED` is permanent. Do not write
  "only the companion's identity moves".
- Define the difficulty coordinate ι (instructed compliance, chance-corrected)
  and the caliper on it, so the reader can follow C2. Registered caliper 0.10 on
  the calibration sample, 0.15 on the disjoint pre-screen
  [`dci1/src/dci1v4r4/protocol/constants.py:233,235`; `ADM` → `thresholds`].
- The gap: a replacement design needs a reference pool that *exists*. Whether it
  exists is an empirical question about the constraint library. **Whether prior
  work assumes it rather than checking it is a hypothesis pending CITE-02 and is
  written as a question, not an assertion.**

## ¶3 — Key claim (C2, the headline)

- State C2 in full, at existence-proof strength. The account is what this
  procedure encountered on this library, not a systematic mechanism.
- Define the terms the claim needs: eligible rung, straddling family, core
  reference, composed-headroom validation.
- Name the organising object as a **three-way split**: the **registered gate
  outcomes** that defeated identification (signed); the **two post-hoc attrition
  diagnostics** — ladder skew and equivalence precision — which describe why the
  pool was small and are **not shown to be binding causes**; and the
  **structural-class scope restriction**, which was never a cause.
- **Closer (draft).** "The design that could have measured directional
  interference did not carry a companion contrast through to confirmatory
  estimation, and the gate outcomes that stopped it are on signed records."

## ¶3.5 — Key evidence for C2

- Four checkpoint runs entered; all four passed Gates 1–3; one obtained the
  47-cell full design; Gate 4 ended that one and one other [`G3:<model>`,
  `TERM:<model>`].
- §13.7 refuses every production-class family from the core pool before
  measurement, so the pool is budget-class while *A* is production [`ADM`].
- The candidate ladder is skewed harder than *A*: of the 84 shortlisted rungs
  Gate 2 calibrated across the four checkpoint runs — 21, 20, 23 and 20 — 65 lie
  below ι_A, and eligible rungs strictly above ι_A number 2, 1, 1 and 0. **Two
  qualifiers travel with that count and are stated in the same breath:** the 84
  are the shortlisted rungs, not the 254 eligible rungs the pre-screen measured
  per run; and the shortlist was chosen on pre-screen ι and re-measured at
  calibration ι, where the split was 54/30 before and 65/19 after — 14 rungs
  moved above→below, 3 below→above, 17 changing side [`ADM`; `COV`; derivation in
  `EVIDENCE_MAP.md` Table 3 rows 2d–2g]. On the two checkpoints that admitted a
  single family, the admitted rung was the **top of its family's measured
  ladder**, so no spectrum rung existed above it.
- Of the 18 rungs inside the caliper, 9 are refused — 8 by the Newcombe
  equivalence region and one on the pre-screen caliper alone. The Newcombe
  refusals are a calibration-sample property, not a library property [`ADM`].
- `RF11:26` measured 0.6875 solo and 0.9688 composed with *B*, exceeding the
  registered [0.05, 0.95] headroom ceiling [`G2:gemma-3n-e2b-it`,
  `TERM:gemma-3n-e2b-it`].
- Six named estimands have no interval anywhere in the study [`FR`].
- Point at **Figure 1**.

## ¶4 — Secondary claim (C1) and its evidence

- State C1 at narrow strength, **as four separately licensed statements rather
  than one four-cell conjunction**: the registered simultaneous intervals control
  error within a family in one configuration of one checkpoint run, and no
  procedure controls error across the conjunction.
- **Split by position.** Two cells are position-matched and isolate composition;
  two are position-shifted and confound composition with position, carrying
  `POSITION_CONFOUNDED` and the fixed phrase *composition and position change
  together*.
- Evidence in one breath: 49,152 confirmatory rows; twenty interval-bearing
  estimates, of which **twelve are delivery-loss quantities** `D(·←·)` and
  **eight are derived contrasts** (`Lambda`, `Delta_class`); L1 emitted somewhere
  in every configuration of both survivors, and never for the same member across
  `gemma-3n-e4b-it`'s two configurations.
- Give the two **position-matched** numbers, which are the clean ones:
  `D(A←B)` = +0.3919 [+0.3503, +0.4335] on `qwen3-4b` and +0.1159
  [+0.0771, +0.1546] on `gemma-3n-e4b-it`, both with the outcome constraint
  stated first.
- State immediately that L2 is withheld everywhere and that the
  cross-configuration comparison is described rather than tested. Point at
  Table 1.

## ¶5 — Impact

- For benchmark builders: matching controls on marginal difficulty did not
  suffice here, and both attrition diagnostics read solo cells only, so they can
  be computed against a candidate library before any composed cell is generated.
  Neither is shown to be a binding cause here, and whether another benchmark
  meets either is not established by this study.
- For anyone reporting composition effects: report the direction and the
  anchor, because `D(A←B)` and `D(B←A)` are different quantities and on
  `qwen3-4b` they have opposite signs.
- For preregistration practice: §6.1 reports one episode in which the device
  prevented a repair its own author wanted. Reported, not claimed.
- Calibration word for the paper as a whole: **narrow**, not compelling, and
  never definitive. What kind of contribution it is — whether it corrects
  anything the field currently assumes — is unresolved pending CITE-02 and
  CITE-03 and is not asserted here.

## ¶6 — Contributions list

Pairs each claim with its strongest single piece of evidence, in body order.

1. **A measured account of a preregistered difficulty-matched companion control
   that did not reach confirmatory estimation on any of four checkpoint runs** —
   the registered gate outcomes that defeated identification, on signed records,
   with two post-hoc attrition diagnostics computed by the registered selection
   functions on the signed Gate-2 tables and labelled as post-hoc; six registered
   estimands left `NOT_IDENTIFIED` study-wide and reported by name.
   *(C2; §4, Figure 1.)*
2. **Twenty preregistered interval-bearing estimates** — twelve delivery-loss
   quantities and eight derived contrasts — from 49,152 confirmatory generations
   on two checkpoint runs. In the two position-matched cells a composed
   constraint loses delivery relative to itself alone; the two position-shifted
   cells confound composition with position and are reported as such.
   *(C1; §5, Table 1.)*
*(Two contributions. The evidence bundle and the provenance record are an
**artifact and reproducibility statement**, not a third contribution: the bundle
reports six missing items and one claim-supporting diagnostic sits outside it, so
"full" would be wrong, and calling auditability a contribution recreates what
demoting C3 was meant to remove. They live in Appendix G.)*

---

## Foreshadowing check

The introduction promises: the gate outcomes, two attrition diagnostics and one
scope restriction (§4), twenty estimates split 12/8 (§5), the bundle and
provenance (Appendix G). Nothing else. `03_paper_outline.md` delivers exactly
these and adds no claim the introduction has not named.
