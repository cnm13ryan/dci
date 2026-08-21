# DCI-1 v4 revision 3 — adoption and pre-freeze decisions register

Every entry is a dated, explicit pre-freeze decision. Each resolves a value the
preregistration (`user-notes/DCI1_preregistration_v4r3.md`) leaves open, or
records a protocol-level interpretation. Nothing here may change after the
study-wide freeze; the freeze record carries these values and any post-freeze
mismatch fails closed.

## A0 — researcher adoption of DCI-1 v4r3 (2026-08-21)

The researcher authorised, in the session brief of 2026-08-21 and before any
v4r3 generation, that the study proceed as **DCI-1 v4 revision 3**: adopting the
difficulty-spectrum design, expanding the reference-candidate library
prospectively, amending the v4r3 preregistration to specify that expansion,
implementing the infrastructure, executing permitted development and calibration
work, running the registered gates, freezing the study if all preconditions
pass, and running confirmatory generation after a valid freeze.

The same authorisation **explicitly withholds** four things, and none of them is
taken here:

1. any retrospective change to v4r2 or to earlier evidence;
2. any weakening of a gate after observing a failure;
3. any selection of a control from a composed outcome;
4. **any separate researcher approval that the protocol reserves** — in
   particular §10.4's `measurement_basis = autorater_calibration_approved`,
   which Gate 1 cannot pass without and which no agent may write on the
   researcher's behalf.

**Why v4r3 and not v5.** v4r2 §31: *"Before study-wide freeze, any change is a
revision of this document."* v4r2 was never frozen and produced no confirmatory
data — all four replications stand at `REGIME_SCREEN`, and no
`gate1_measurement.json` exists anywhere in the tree, so the §10.6 binding has
never compared. A pre-freeze change is therefore a revision. The v4r1 → v4r2
transition is the precedent, for the same reason. This closes **D0**.

## D — the registered open decisions and their standing

| # | Decision | Standing as of 2026-08-21 |
|---|---|---|
| D0 | Adopt v4r3 | **CLOSED** by A0 |
| D1 | Confirmatory compute budget and allocation | **CLOSED** by A1 below: 384 blocks at M = 8 |
| D2 | Models carried to confirmation | open; four registered, per-model outcomes independent |
| D3 | §12.4's graded clause read as a share | open; the share reading is registered and its coherence argument is in §12.4 |
| D4 | Whether the focal extension is a study-wide escalation | **CLOSED**: registered as an escalation in §7.2 |
| D5 | Whether `delta_difficulty` gets a magnitude threshold of its own | open; direction and the registered SESOI only |
| D6 | Instructed compliance as the primary difficulty coordinate | **CLOSED**: registered in §13.3, raw solo retained as secondary |
| D7 | The class arm's scope | **CLOSED** in part by A2 below |
| D8–D11 | as registered in §33 | open |

## A1 — the allocation is 384 blocks at M = 8, not 408 at M = 4 (2026-08-21)

An earlier v4r3 draft registered 34 confirmatory and 6 sequestered topics per
area so that 408 blocks would meet every §16.2 precision precondition at M = 4.

**That allocation is not executable.** `dci1v4.topics.bank` releases the 528
non-sequestered questions; the other 96 exist to this repository only as
identities and content hashes in `dci1v4.topics.sequestered`, and
`assert_no_materialisation` refuses a released topic that reproduces one. The
two extra confirmatory topics per area could only be drawn from text no v4-era
process can read. The finding came from reading the topic module rather than
the table, and the table had been wrong since it was written.

With the block count fixed at 384, M is the only remaining lever, and under
§16.1's variance model it is the effective one: at φ = 0.37 and ρ = 0.5 the
draw term is 0.0000704 against a topic term of 0.0000415 at M = 4, so the part
M reduces is the larger part. **384 blocks at M = 8** meets every precondition
under both φ settings, restores v4r2's 96-topic sequestered set, and leaves the
topic split byte-identical to v4r2's.

Cost: 144,384 generations per model, 577,536 across four — against the 306,816
the unexecutable row promised. The alternative, authoring at least 24 further
topics under §6.2's four rules and re-cutting the split, is recorded as D1's
open half.

## A2 — the class pool gains two rate lower bounds (2026-08-21)

The pairwise-matrix screen measured one production-class companion and found it
cost B **+0.601** and **+0.632** where A cost +0.086 and +0.228. A
Δ_class computed between companions that far apart in difficulty bounds a class
effect only in the weakest sense.

A count lower bound is hard to make gentle: it demands an absolute number of
qualifying words and so scales with response length. A **rate** lower bound
(`100·S/W ≥ q`) is scale-free and can be tuned to any difficulty, so §13.7 has a
real chance of admitting a class companion matched to A on ι. CP4 and CP7 are
registered for that purpose, and §13.7 now distinguishes an *admitted* class
companion from a *matched* one: `CLASS_ARM_NOT_MATCHED` fires when
|ι_CL − ι_A| > 0.15 and every class statement carries it.

A rate lower bound is classed `production` because its registered satisfaction
route is to produce more of the counted feature. It also admits a budget-like
route — deleting non-conforming words raises the rate — and §7.4 records that
rather than hiding it.

## A3 — the lexical rule's composition order is corrected (2026-08-21)

§10.2's independent reimplementation, written from the registered prose by a
process that read no primary source, disagreed with the primary on the
`one_letter` statistic. v4r2's helper lower-cases the whole response and then
segments; §7.3's prose segments the answer and lower-cases each word for the
suffix and letter tests. §10.2 adjudicates against the prose, so v4r3 composes
in the registered order.

Scope, enumerated executably over the whole Unicode range: **exactly one
character** behaves differently. `İ` (U+0130) lower-cases to `i` followed by
U+0307 COMBINING DOT ABOVE, which is not alphabetic, so folding first splits the
word — `İstanbul` becomes two words of one and seven letters, and B at m = 7
would pass an answer containing an eight-letter word.

Realised frequency of U+0130 in the 285,936 rows every v4-era process has
generated: **zero**. No measured quantity moves and no historical comparison is
broken. The correction is prospective; the boundary suites carry a frozen case
for it; §24 reports its realised frequency so a future firing is visible.

**A is deliberately untouched.** §9.2 registers S0 in its own words as
lower-case-then-segment, and A's carried counting function implements exactly
that, so A's construct string, segmentation function and counting function stay
byte-identical to the closed v3 instrument and its §10.2 carry-over survives.
The two rules differ because the two constructs differ: A counts occurrences of
a string; B and the families make claims about words as objects, whose identity
must not depend on case.

## A4 — the candidate library is a grammar with a frozen reserve (2026-08-21)

The expansion the researcher authorised is registered as a *restriction of a
frozen enumeration*, never as authoring after data has been seen. §7.0 declares
nine counted statistics and four predicate forms; every family is a pair of
those; every family carries a round-0 ladder and a frozen reserve that is a
superset of it; §12.6's expansion may admit reserve rungs and nothing else, at
most four per family per round and at most two rounds, by a deterministic rule
that reads ι and severity only.

Because wordings are severity-invariant and §10.2 freezes boundary cases over
the whole declared range before qualification, a reserve rung inherits its
family's wordings and its evidence exactly, so an expansion never admits an
instrument that carries no evidence.

The stopping rule is the §12.6 identification-coverage criterion, whose seven
conditions and their values are registered before any measurement. Failure is
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED` at design time, which is a registered
outcome and not a fallback to be avoided.
