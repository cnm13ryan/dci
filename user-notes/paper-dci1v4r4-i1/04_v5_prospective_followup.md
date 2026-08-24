# 04 · The v5 prospective follow-up — what it contributes beyond v4r4

**Status.** v5 was executed and closed on 2026-08-24. This document records
what that execution contributes to the paper. It is written to be read without
repository context.

**One-sentence contribution.** v4r4 showed retrospectively that
composition-related delivery loss is measurable while companion-specific
attribution is not identified; v5 was a prospectively registered design built
to repair that identification failure, and it **still did not carry a valid
matched-companion comparison into confirmatory analysis** — failing at two
distinct, sequential bottlenecks.

Sources, all signed or committed: `dci1/reports/dci1v5/CLOSURE.md`,
`closure.json`, `survival_diagnosis.md`, `survival_diagnosis.json`,
`amendment_register.md` (A5–A8). Where those disagree with any summary,
including this one, they govern.

---

## 1 · Why v5 was run

v4r4 left one question open, and it is the question the paper's centre (§4) is
built around.

v4r4 obtained two clean position-matched directional composition-loss estimates
and two further position-confounded losses. It did **not** obtain a valid
matched-companion estimate — no `Delta_R`, `Delta_j`, `Xi` or
`delta_difficulty`. The reason was an identification failure, not a null: the
reference pool that would have supplied the matched counterfactual did not
survive its own admission criteria.

v4r4's account of *why* was retrospective. Two diagnostics — a headroom breach
and a ladder skew in the candidate pool — were computed after the outcomes they
explain. `GAPS.md` G17 states the resulting limitation exactly: **no ablation
showed that relaxing either diagnostic would have made `Delta_R` identifiable**,
and nothing showed the excluded families would have supplied acceptable
references. The diagnostics motivate; they do not demonstrate.

v5 exists to convert that retrospective account into a prospective test.

**An important caveat that does not go away.** v5's *design* was fitted to
v4r4. Its reference-matching rule, its extended focal grid and its
construct-floor threshold were all chosen after observing all of v4r4, and the
v5 preregistration says so in its own §30. That makes the **design**
development evidence. What is prospective is the **execution**: the design was
registered, frozen and signed before v5 generated a single row, and it was then
run without amendment to its scientific rules. So v5 tests whether a design
fitted to v4r4's diagnosis actually works — which is precisely the test G17
says is missing.

---

## 2 · What v5 prospectively tested

Three things, all registered before data:

**Strengthened reference construction and identification.** The core reference
pool was inverted to production class and same-form with the anchor; the
difficulty coordinate was demoted from admission to difficulty; a
pre-composition interaction gate and two calibration splits were added. The
matched-companion estimands were retained unchanged as the target.

**A prospective support requirement.** §12.6 registered an
identification-coverage criterion, C1–C8, evaluated on the pre-screen. Its
decisive conditions are C1–C6. C4 is the one that matters below: it requires
**at least six feature groups** each containing a family that straddles the
anchor difficulty with at least three eligible rungs spanning at least 0.40 in
the difficulty coordinate. Failing the decisive set drops the core and spectrum
arms and records an **irreversible** non-identification (decision D6).

C4's margin was itself set from v4r4 experience: v4r4 registered four
straddling families against a requirement of three — one spare — and lost 50%
to 100% of them between pre-screen and calibration. C4 asks for six, i.e. three
spare. This is the repair being tested.

**Composed-headroom validation before confirmatory inference.** §13.14 requires
every registered cell type to sit inside [0.05, 0.95] compliance, checked at a
dedicated gate *before* the freeze, so that a design with no measurable room
cannot proceed to confirmatory generation.

Four replications were registered: `gemma-3n-e2b-it`, `gemma-3n-e4b-it`,
`qwen3-4b`, `qwen3-4b-instruct-2507`.

---

## 3 · What happened

**459,312 real generated rows. Zero replications reached confirmatory
generation.** Masking never opened; no unmasking occurred; no confirmatory
estimate of any kind exists.

### 3.1 · Three replications lost reference identification (D6)

C4 requires six qualifying straddling feature groups. Realised:

| replication | qualifying groups | required | C4 |
|---|---|---|---|
| `gemma-3n-e2b-it` | **4** | 6 | fail |
| `gemma-3n-e4b-it` | **5** | 6 | fail |
| `qwen3-4b` | **5** | 6 | fail |
| `qwen3-4b-instruct-2507` | 8 | 6 | pass |

Each failure dropped the core and spectrum arms and recorded D6
`REFERENCE_SUPPORT_NOT_IDENTIFIED`, marked irreversible, with 48 estimand
members unidentified on each — including every primary contrast. The three then
failed the mandatory `support_satisfied` pre-freeze check and could not freeze.
Because a stage record is write-once, that outcome is not re-runnable: those
replications are terminal in substance.

### 3.2 · The one identified replication then failed composed headroom

`qwen3-4b-instruct-2507` cleared C1–C8, retained the core arm and carried 26
derived cells — the only replication with companion identification intact. It
terminated at the composed-headroom gate with `COMPOSED_HEADROOM_FAILURE`, its
observed cells sitting at 0.9896 and 0.9583 against a 0.95 ceiling.
`gemma-3n-e4b-it` terminated at the same gate (0.9792, 0.9583), having already
lost identification.

The registered terminal sentence on both records reads: *a terminal
pre-confirmatory status carries no evidence about the effect.*

### 3.3 · The two bottlenecks are independent

Repairing either would not have rescued the group that died of the other.
Fixing the reference library would not have saved
`qwen3-4b-instruct-2507`, which cleared C4 and died at headroom. Fixing the
operating point would not have saved the three that died at C4.

---

## 4 · What v5 adds scientifically beyond v4r4

**(a) It converts a retrospective concern into a prospective result.** v4r4's
reference-attrition and headroom problems were diagnostics computed after the
fact. v5 registered a design to fix them, froze it, ran it, and recorded the
outcome under gates that could not be renegotiated afterwards. This is the
direct, if negative, answer to `GAPS.md` G17: a design built on those
diagnostics was tried, and identification still did not survive.

**(b) It shows the strengthened procedure still failed to obtain the required
counterfactual.** Not "the effect was small" — the matched comparison was never
licensed. Three replications could not identify it; the fourth could, and then
had no measurable room in which to observe it.

**(c) It separates two bottlenecks that v4r4 could not distinguish.** In v4r4
the reference-pool problem and the headroom problem were entangled in a single
retrospective account. v5 separates them cleanly by *sequence*: support
coverage is decided at the pre-screen, headroom at a later independent gate,
and the four replications distribute across both failure modes. That
separation is new and is v5's most transferable finding.

**(d) It quantifies how far short the design fell, prospectively.** The support
failures were near-misses against a registered bar (4, 5 and 5 against 6), not
collapses — which is a far stronger motivation for a successor design than a
retrospective diagnostic can supply.

**(e) It strengthens the methodological case without any new effect claim.**
The paper gains a prospectively tested identification result. It gains no new
behavioural number.

---

## 5 · What v5 does **not** establish

Stated flatly, because each is a mistake the material invites:

- **No confirmatory estimate of `Delta_R`, `Delta_j`, `Xi` or
  `delta_difficulty`.** None was computed on any replication.
- **`NOT_IDENTIFIED` is not a null result.** Three replications did not fail to
  find a companion-specific effect; the design could not identify the estimands
  at all. Reporting D6 as "no effect" would be a category error.
- **No evidence for or against companion-specific effect magnitude**, in either
  direction, on any model.
- **No claim that matched-companion identification is impossible in general.**
  v5 tested one registered design, on four models, on one host. It shows this
  design did not deliver; it cannot show none could.
- **No justification for relaxing any threshold post hoc.** The support and
  headroom bars were registered before data and are not renegotiated because
  they were missed. Any successor changing a threshold needs a separate
  scientific argument and an explicit researcher decision.
- **No new confirmatory directional-loss result.** The directional composition
  losses in the paper remain v4r4's, on v4r4's evidence, unchanged.
- **v5's failure is not evidence that v4r4's behavioural result is correct.**
  The two speak to different questions; a failed identification design neither
  corroborates nor undermines a measured delivery loss.

---

## 6 · Implications for the paper

### 6.1 · Revised architecture

The paper can now be built on two studies with distinct and non-overlapping
roles:

| study | role | supplies |
|---|---|---|
| **v4r4** | behavioural / composition result | the directional composition-loss estimates, position-matched and position-confounded |
| **v5** | prospective identification follow-up | a registered, frozen, executed test of whether the identification failure could be repaired |

This moves the paper from

> *v4r4 result + retrospective failed-control diagnostics*

to

> *v4r4 behavioural result + prospectively tested identification failure.*

The second is materially stronger on the identification story: the same
limitation is now supported by a preregistered test rather than by post-hoc
inspection alone.

### 6.2 · Where it goes

Most naturally a dedicated subsection of §4 (the identification attempt, the
paper's centre) or of §6, presenting v5 as the prospective sequel to §4's
retrospective account. §4 is the better home if the paper's centre of gravity
stays on identification.

### 6.3 · What this changes about the existing v5 caveats

The bundle currently treats v5 material as design fitting throughout
(`GAPS.md` G10, red-team R10, outline §6.3). **That remains correct for the v5
*development report*** — its thresholds were fitted to v4r4, and no sentence
may call that validation. What is new is that the fitted design was then
*registered and executed*, so the run is prospective even though the design is
not. The distinction is narrow and must be stated explicitly wherever v5 is
cited, or the paper will overclaim.

### 6.4 · Novelty is not decided here

Whether a prospectively tested identification failure is a publishable
contribution in its own right, and how it is positioned, **depends on the
literature review, which is not complete** (`GAPS.md` G3, G4; CITE-02 remains
the single most important unverified citation). Nothing in this document
settles novelty, and `TITLES.md` is not revised on the strength of it.

---

## 7 · Implications for future work

A prospective successor must solve two problems, and they are independent:

1. **Overprovision difficulty and reference support.** The support criterion
   must be satisfiable with margin, not narrowly. v5's failures were
   near-misses against the registered bar, and the shortfall traces to a
   candidate library whose ladders are too compressed in the difficulty
   coordinate and too rarely extend above the anchor.

2. **Establish composed headroom before the final reference freeze.** v5
   selected its operating point from solo behaviour and only discovered the
   composed ceiling at a later gate, after references were fixed. Headroom must
   be demonstrated while the operating point can still move.

**A concrete proposal exists and is explicitly unadopted.**
`user-notes/DCI1_v6_proposal.md` sets out candidate remedies — extending the
candidate library, adding a composed-headroom probe before the operating point
is fixed, and requiring at least two surviving identified replications before
confirmatory generation is licensed. It relaxes no threshold. **It is a
proposal, not a registered protocol; its parameters are unadopted and await
researcher decision; and no data may be generated against it.** No number or
threshold from that proposal may enter the paper as a result.
