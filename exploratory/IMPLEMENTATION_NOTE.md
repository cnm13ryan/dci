# Implementation note — cheapest informative DCI probe on local ROCm

Written before the substantive edits, per the task's "short implementation note"
requirement. It records what is reused, what is new, what is deliberately left
out, and what the omissions cost.

## What this experiment is

One matched causal comparison, on one model, one pair, one load, one decoding
configuration:

    S ∪ {A, B}     versus     S ∪ {A, C_j}    for four matched references C_j

with compliance measured on **A only**, by a deterministic verifier. Positive
`τ_j = mean_i [ Y_{i,A+B} − Y_{i,A+C_j} ]` (Y = A-failure) means B costs more
A-compliance than that reference does. The unmatched "with B vs without B"
contrast is *not* computed: it reintroduces the generic-load confound the
reference construction exists to remove.

## Components reused, not reimplemented

Everything scientific is imported from the v15/v19 implementation on this
branch. `dci_exploratory/harvest.py` imports stages `c112 … c212` under a
dry-run `dev_fast` profile and reads their shared state:

| Reused | Source | Why not rewritten |
|---|---|---|
| Constraint identities and parameters | `S.CONSTRAINTS` (stage c142) | 45 authored, audited specs incl. declared incompatibilities |
| Canonical instruction wordings | `S.INSTRUCTIONS` (stage c172) | 8 certified paraphrases per rule; re-typing one would change the treatment |
| System message | `S.SYSTEM_MESSAGE` (c172) | part of the frozen prompt format |
| Prompt assembly | `compose_prompt` (c182) | the exact numbered-list format the protocol uses |
| Deterministic verifiers | `dci.verifiers.rules`, dispatched by `S.verify` (c152) | already unit-tested (`tests/unit/test_verifier_rules.py`) |
| Task/topic bank and splits | `S.TASKS` (c142) | disjoint splits; the pilot split exists precisely so exploratory looks cannot burn study topics |
| Joint-satisfiability check | `dci.constraints.satisfiability.pair_verdict` | an unsatisfiable pair measures impossibility, not interference |
| Reference eligibility | `S.hard_eligible_universe` (c212) | the repo's own criteria, which never mention resemblance to B |
| Verifier coupling with A | `S.COUPLING` (c162), from the model-free `S.RESPONSE_BANK` | construction evidence available at zero GPU cost |
| Pair identity (A, B) | `dci.v19.pairs.PAIR_3` | the v19-registered pair; its two verifiers are the implemented ones |
| GPU backend shape | patterned on `dci.inference.hf_transformers` | same left-padding, EOS accounting, termination records |

## What is genuinely new

- `harvest.py` — a read-only adapter that runs the stage prelude once and hands
  back the definitions above. No scientific content.
- `design.py` — the exploratory slice: reference selection under a pre-stated
  deterministic rule, background-set selection, and matched design construction.
- `runner.py` — batched ROCm generation + scoring + JSONL artifacts.
- `analysis.py`, `audit.py` — exploratory tables, figures, and the human audit
  export.
- `rocm_doctor.py` — local environment record and GPU correctness smoke test.

## The pair, and why

v19 registers three pairs. Pair 1's two verifiers are **not implemented**
(`dci.v19.pairs.unimplemented_verifiers()`), so it cannot be measured at all.
That leaves p2 and p3. **p3 is selected**:

- A = `v19:p3.target.exact_sentence_count` — "Write exactly 4 sentences."
  Verifier `v_exact_sentence_count`: count segments, compare to 4. Deterministic
  and trivially checkable by eye, which the mandatory manual audit needs.
- B = `v19:p3.focal.increasing_lengths` — strictly increasing sentence word
  counts. Verifier `v_increasing_lengths`.
- p3 carries the most existing construction evidence: it is v15's own A/B pair
  (`v15_lineage = "A / S2"` and `"B / O1"`), so its whole candidate-reference
  pool, coupling table and response bank already exist.
- B is substantively different from A: A is a global count, B is a cross-sentence
  ordering relation. They are not nested, and neither entails the other.

p2 (mandatory words → all-words-unique) was rejected: its own registered
`measurement_risk` is that the composition can be *logically impossible*, which
is outside the estimand and is the wrong thing to spend a first look on.

## Reference selection rule (stated before looking at any outcome)

From `S.CANDIDATE_IDS` (17 sentence-scoped candidates, all hard-eligible):

1. keep only candidates that are hard-eligible under `S.hard_eligible_universe`;
2. keep only candidates jointly satisfiable with A, with B, with the background
   set and with each other, under `pair_verdict`;
3. take the whole **non-shadow** pool (`origin == "cse_pool"`): `C_L3`, `C_W3`,
   `C_O2` — these are the repo's primary authored reference candidates;
4. add shadow candidates to reach v19's fixed `N_REFERENCES == 4`, choosing the
   one that adds the missing *constraint family*, breaking ties by lowest
   verifier coupling with A, then by constraint id.

This yields R1..R4 = `C_L3`, `C_O2`, `C_W3`, `S_SEMICOLON` and covers all three
mechanisms the registry distinguishes — crucially including `C_O2`
(cross-sentence comparison), which shares B's *mechanism* while differing in its
*content*. That is the strictest available control for "adding any comparison-type
instruction is what costs A", as opposed to something specific to B.

Selection never consults an outcome, so it cannot be tuned toward an effect.

## Weights

v19 is explicit that primitive effects stay reference-specific with "no primary
averaging or weighting", and v15's stochastic weights are a Stage-3 output of a
calibration run that has not happened. So **no fitted weights exist to reuse**.
Reported instead:

- per-reference `τ_j` — the primary quantity;
- a **uniform** `w_j = 1/4` aggregate, labelled as an exploratory descriptive
  average and nothing more;
- `min_j τ_j`, which is the shape v19's headline actually takes (`L_s = min_j L_r`)
  and is the conservative reading: B must beat *every* reference.

## Deliberately omitted from the v19/v15 pipeline, and why it is safe here

| Omitted | Why safe for an exploratory look |
|---|---|
| Gates 0/M/1/2/3/3b/4, freeze, export | They gate *confirmatory evidence*. Nothing here is evidence; artifacts are stamped `EXPLORATORY_NO_EVIDENCE`. |
| Reference admission via calipers, joint reference-error certificate, validation split | Requires a calibration generation run. Cost is that references are matched on *construction*, not on measured difficulty — recorded as the leading alternative explanation and partly probed by measuring each reference's isolated difficulty in the same run. |
| Stochastic reference weights | No calibration signature exists; uniform weights are used and labelled. |
| Paraphrase escalation (P = 4, 6) | One canonical wording (`paraphrase_id = 0`) is held fixed across focal and reference, so wording cannot differ *between* arms. Cost: a wording-specific effect is not separable — recorded as an alternative explanation. |
| Multiple budgets, both loads as primary, all three pairs, multi-model | Explicit scope exclusions in the task. |
| WSR/MP-EB inference, multiplicity control, power analysis | Exploratory: paired bootstrap only, labelled descriptive. |
| Task-cluster bootstrap over the confirmatory split | The pilot split is used instead, so no confirmatory topic is burned. |

## Assumptions

1. Importing stages `c112 … c212` under `dry_run_mode = True` is side-effect-free
   with respect to the scientific definitions — it loads no weights and writes
   only into a scratch data root. (Verified: `ALL STAGES OK`, no GPU touched.)
2. The v15 verifiers are correct as written; this study audits their *verdicts*
   by hand but does not re-derive their logic.
3. `S.COUPLING` and `hard_eligible_universe` are meaningful at construction time
   because both are computed from the authored, model-free response bank.
4. ROCm's `torch.cuda` is a HIP alias, so `cuda:0` is GPU 0 of the two 7900 XTXs.
