# Prospective Stage 2 specification amendments

Four questions the v19 preregistration leaves open, or answers inconsistently, are
settled here **prospectively** — before any confirmatory generation, any calibration,
and any reference selection. Each amendment states the governing text, why the text
cannot be applied as written, the decision, and its consequences.

## How an amendment becomes binding

Three states are kept apart, and the difference matters more than any single
amendment:

| state | what it means | where it lives |
|---|---|---|
| **implemented candidate** | the code computes it, and it is tested | `dci.v19.*` |
| **accepted** | the investigator accepted it, on stated evidence | a record in `src/dci/v19/stage2_frozen.json` |
| **frozen** | the registry carries the value | `Slot.resolution is FROZEN`, applied by `frozen.apply` |

The registry slots below are declared `PENDING_DECISION`, **not** `FIXED`. `FIXED`
means the preregistration fixes a value directly; these are decisions it does not
make. Acceptance is a signed record naming who accepted it, when, and on what
evidence — never the presence of a candidate in the source, which would let the
implementation treat a scientific decision as made before the investigator made it.

Every amendment is machine-readable. Values are validated against typed domains in
`dci.v19.schemas` on the way into the registry, so an amendment cannot be widened by
editing a private helper, and a recorded value the code can no longer reproduce fails
at import rather than at whatever later stage reads it.

---

## A1 — the canonical Pair 1 list grammar

**Governing text.** §4.1 fixes the two statements; §4.2 names the shared-parser
coupling; §10.9 and §14.2 require the support to be built. Nothing fixes a parsing
rule.

**Why an amendment is needed.** Ten grammar decisions change verdicts and none has an
answer in the protocol: which characters open an item, whether enumerated lists are
bullet-list items, nesting, continuation lines, empty items, how an item is matched to
a declared entity, and whether an undeclared item is permitted. Six of seven
single-field variants change an observed item count on an adversarial corpus.

**Decision.** `dci.v19.parsing.CANONICAL_LIST_POLICY`. Every field's answer and reason
is in `RESOLVED_BY_AMENDMENT`, which `assert_policy_fields_are_accounted_for` keeps
exhaustive. Two answers carry the most weight:

- **`label_match = "token_membership"`** — an item is identified with a declared
  entity when that entity is one of the item's word tokens. Substring containment,
  the earlier reading, found `item1` inside `item10` and found the label `alfa` inside
  a mandatory word `alfaX`.
- **`extra_items_permitted = False`** — an item matching no declared entity is a
  structural failure. Permitting it would leave the focal rule silent about part of
  the list the target counts, and §4.2's coupling analysis presumes both rules read
  the same list.

One field departs from the inherited regex: `numbered_max_digits` rises from 2 to 3,
so a calibrated `n_items` between 100 and 999 cannot silently exceed the parser. The
inherited cap was an artefact of `\d{1,2}`, not a decision.

**Slot.** `verifiers.p1.list_policy`, domain `list_policy`, accepted 2026-08-11.

---

## A2 — the Pair 2 and Pair 3 verifiers are corrected, not reused unchanged

**Governing text.** §14.2 permits reuse "only after hash/semantic audit". §10.6: "A
demonstrated semantic or verifier defect requires repair and re-audit before freeze;
collecting more confirmatory data is not a remedy for invalid measurement."

**Why an amendment is needed.** The audit demonstrated three defects, so reuse
unchanged was not available. §4.3 and §4.4 defer to "the frozen normalisation and
tokenisation-for-verification rule" and "the frozen sentence segmentation" without
saying which rule is frozen, so naming one is an amendment rather than an
implementation choice.

**Decision.** All six verifiers read `dci.v19.text.CANONICAL_TEXT_POLICY`. Five
corrections, each recorded in `INTENTIONAL_CORRECTIONS` with the defect it repairs:
NFKC normalisation; removal of format and control characters; a Unicode-aware word
pattern; one case rule (`casefold`) replacing the mixture of `casefold` and
`str.lower`; and a segmentation that survives on any word token rather than only an
ASCII one. The inherited module is untouched — the v15.1 pipeline depends on it — and
the differential audit enumerates every disagreement.

**Explicitly not attempted.** Confusable detection. A Cyrillic look-alike is a
different string and NFKC does not merge it, so `"аpple apple"` is two distinct words.
§10.6 assigns homoglyphs to human audit material, not to an automated rule.

**Slot.** `verifiers.inherited_reuse_decision`, domain `reuse_disposition`, accepted 2026-08-11.

---

## A3 — the exact Clopper–Pearson interval, a strict fixed design, and register row D45

**Governing text.** §10.4: "The 5% Tier-1 ceiling … and inherited 73-per-truth-class
Tier-1 planning count are preserved. The exact two-sided binomial interval
implementation used by the inherited gate must be recovered … and frozen at Stage 2;
if it is not uniquely recoverable, its choice is a \PFD within register item D9."

**Why an amendment is needed.** Recovery succeeded and contradicts the sentence. The
inherited gate inverts `wilson_interval` — a normal-approximation interval, not an
exact one — and both counts §10.4 preserves are Wilson's:

| | Wilson | Clopper–Pearson | §10.4 states |
|---|---|---|---|
| n per truth class at 5% / 95% | 73 | **72** | 73 |
| Tier-1 labels (6 units × 2 classes) | 876 | **864** | 876 |

The interval is uniquely recoverable *and* is not exact, so "exact two-sided binomial"
and "73 preserved" cannot both hold.

**Decision.** Keep the adjective, drop the preserved count. §6.2 already requires the
exact two-sided 95% Clopper–Pearson interval for boundary parameter calibration and
cites Brown, Cai and DasGupta on normal approximations near boundaries; using a looser
interval for the *primary outcome's own verifier* than for parameter calibration is
the harder position to defend.

**Consequences, stated rather than hidden.** The Tier-1 planning count becomes **72
per truth class and 864 adjudicated labels**. `INHERITED_TIER1_PER_TRUTH_CLASS = 73`
is retained as a record of what the inherited gate implied. On identical adjudicated
evidence — 0 errors in 72 per class — Wilson fails and Clopper–Pearson passes, so this
choice changes real Tier-1 verdicts.

### The strict fixed design

An interval does not determine a decision rule, so A3 also fixes the design:

> `n = 72` per truth class; **zero** observed errors required to pass; any observed
> error fails the audit; after failure the verifier is repaired and re-audited under a
> **fresh prospectively specified audit**. The original sample is **not** extended.

The exact bound at one observed error:

| n | exact upper bound at 1 error | verdict on the 5% ceiling |
|---|---|---|
| 72 | 0.0750 | fails |
| 109 | 0.0501 | fails |
| **110** | **0.0496** | **passes** |
| 200 | 0.0275 | passes |

**110 is the smallest sample at which a single observed error still clears the
ceiling.** "Extend to 110" is therefore not an arbitrary enlargement; it is the
precise size that converts an audit failure into an audit pass, which is why it is the
extension named and forbidden. Without a prospectively fixed `n`, the verdict would
depend on a sample size chosen after the errors were seen, and the nominal 95%
coverage would not describe the procedure that was run.

`tier1_certificate_under` refuses a realised audit the design does not admit *before*
the bound is allowed to speak, and reports which rule was broken: extension, a short
class, or an error over budget. A clean but extended sample is refused too — the
design fixed the size.

§10.6 supplies the remedy: "collecting more confirmatory data is not a remedy for
invalid measurement."

**Register row.** §10.4 cites D9, which is the construction bootstrap. **D45** is
added: *Two-sided binomial interval for the Tier-1/Tier-2 reliability gates, and the
fixed audit design built on it — accepted by Stage 2 amendment A3 — freeze blocker:
yes — exact two-sided Clopper–Pearson; 72 adjudicated labels per truth class; zero
observed errors required; no conditional sample extension.*

**Slots.** `verifiers.binomial_interval_implementation` (domain `binomial_interval`)
and `verifiers.tier1_audit_design` (domain `tier1_audit_design`), both accepted
2026-08-11.

---

## A4 — `ordering_depth` is longest-chain cardinality, under a frozen generator

**Governing text.** §6.1 lists ordering depth among the family-specific parameter
quantities. `pairs.PAIR_1` declares it as the focal parameter. Nothing defines it, so
Stage 5 had no construct to calibrate.

**Why an amendment is needed.** A focal parameter with no definition cannot have an
admissible set, and §6.2's boundary calibration selects from an ordered grid of
settings of *something*.

**Decision.**

> `ordering_depth(R)` is the **longest-chain cardinality** of the required precedence
> relation `R`: the number of items in the longest chain of `R`.

Counted in items, not edges. `OrderingRelation.chain_depth` predates this and counts
edges; the two differ by one, and a test asserts that rather than leaving it implied.

**Why the generator is frozen with the statistic.** A statistic on a relation does not
fix what the parameter manipulates. At depth 2 over six items:

| relation | depth | edges | unconstrained items |
|---|---|---|---|
| one precedence | 2 | 1 | 4 |
| a five-edge star | 2 | 5 | 0 |
| three disjoint pairs | 2 | 3 | 0 |

If the protocol could generate any of these, "ordering depth" would be confounded
with total constrainedness, and a dose–response over depth would not be a
dose–response over anything nameable. So A4 also freezes the generator:

> for `N` items at depth `d`, expose exactly **one chain** containing `d` items, and
> leave the remaining `N − d` items **explicitly unconstrained**.

Under that form the edge count (`d − 1`), the constrained-item count (`d`) and the
free-item count (`N − d`) are all functions of `d` alone.

**Cover relations, not the closure.** The chain is exposed as its `d − 1` cover edges.
The closure of a `d`-chain states `d(d−1)/2` precedences for the same partial order,
so presenting it would grow the number of stated requirements quadratically in `d`
while the order itself did not — confounding depth with prompt length. The verifier
still evaluates the closure internally.

**Randomisation.** Chain membership, chain order and presentation order are each drawn
from a separate domain-separated stream of the recorded seed, hash-derived rather than
from `random.Random` so a realisation is reproducible from the seed alone. Without the
presentation-order stream, an answer could satisfy the relation by copying the
prompt's order without representing the order at all.

**Range.** `2 ≤ d ≤ N`. Depth 1 is the empty relation: no arrangement could be wrong,
so the focal constraint would be vacuous.

**Direction.** Larger `d` is the **nominal** harder direction — it states more required
precedences over more items. Nominal because whether it is empirically harder is what
Stage 5 measures.

**What A4 does not decide.** The retained depths. §6.2's ordered grid of at most five
admissible settings is the Stage 5 boundary-calibration output
`parameters.p1.admissible_set` (register item **D6**). `DECISION["grid"]` is `null`
with `grid_rule` saying why, and the typed domain **refuses** a Stage 2 value that
carries a grid — anticipating it would pre-empt the procedure that selects it.

**Alternatives considered and rejected**, recorded in
`dci.v19.ordering.DECISION["rejected_alternatives"]`:

- **item count** — not a property of the ordering relation at all. It would make the
  focal parameter a second copy of the target's `n_items` and confound the two
  constraints the pair exists to separate.
- **edge count** — counts stated requirements rather than the depth of the order.
  Under the canonical generator it is `d − 1` and carries the same information; off
  it, a wide shallow relation and a deep narrow one can share an edge count.
- **linear-extension count** — measures constrainedness, a defensible but different
  construct. It is not a depth, is #P-hard in general, and is not monotone in any
  quantity the prompt states.

**Registry.** `verifiers.p1.ordering_depth`, domain `ordering_depth`, accepted
2026-08-11.

---

## Superseded — "not amended: `ordering_depth`"

An earlier draft of this document left `ordering_depth` open, on the grounds that
nothing in the protocol's text or in the inherited code determines it. That remains
true; what changed is that the investigator supplied the construct rather than the
implementation guessing one. A4 above records it.

Two things from that draft were wrong and are corrected here:

1. The typed domain then required a §6.2-shaped **grid** of at most five ordered
   settings. That would have forced Stage 2 to pre-empt the Stage 5 calibration (D6)
   that selects the grid. The domain now refuses a grid.
2. The draft decision memo noted that item count "needs no code change" and that
   longest-chain depth would need `n_items` declared separately. The second claim was
   false — `PAIR_1.target.parameters` already declares `n_items`, so neither
   longest-chain depth nor edge count requires touching a fixed declaration — and the
   first had no place in a scientific decision memo at all.

`OrderingRelation.chain_depth` is a diagnostic counted in **edges** and must not stand
in for the parameter, which is counted in items.
