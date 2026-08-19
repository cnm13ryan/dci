# Implement DCI-1 v4 as a Fresh, Fully Isolated Study

## Objective

Implement DCI-1 v4 faithfully from `DCI1_preregistration_v4r2.md` as a new,
self-contained implementation.

Start from a fresh understanding of the study. Do not update, patch,
extend, subclass, or retrofit the v3 implementation, and do not build on
the B+R pilot tool. V4 must be scientifically and operationally isolated
from both.

The completed implementation must encode the full v4 protocol, pass the
required validation and integrity tests, execute every pre-confirmatory
stage the environment legitimately supports, and produce the empirical
evidence the researcher needs to close the registered open decisions.

**Do not freeze the protocol. Do not perform confirmatory generation.**
v4 revision 2 is a prospective document with nine registered open
decisions and twenty-one pre-freeze checks, seventeen of which block the
freeze and four of which are report-only. Your task ends when those checks
have been executed or reported as blocked.

---

## 1. Source authority

Read these completely before making substantive changes. If a filename
below does not resolve, locate the document by content rather than by
name, and record the resolved path.

| # | Document | Authority |
|---|---|---|
| 1 | `user-notes/DCI1_preregistration_v4r2.md` | **The sole authoritative scientific specification.** |
| 2 | `user-notes/DCI1_v4r2_unresolved_decisions.md` | Binding. Lists what you must not decide. |
| 3 | `user-notes/DCI1_v4r2_prefreeze_checks.md` | Binding. Your work programme for checks C1 to C20 and C7b. |
| 4 | `user-notes/DCI1_v4r2_scientific_change_summary.md` | Audit aid. One row per change, with the evidence that forced it. |
| 5 | `user-notes/DCI1_v4r2_changelog.md` | Audit aid. The disposition of every historical DCI quantity. |
| 6 | `user-notes/dci-construct-pass2.md` | The construct decision memo. The design authority behind v4r2 §2, §11 and §16. Read §A, §C, §F, §G and §H in full. |
| 7 | `user-notes/prompt-to-red-team.md` | The integrity invariants of §X, the design dependency order of §N, and the operating-regime and reference requirements of §O and §P. Binding as engineering constraints. |
| 8 | `user-notes/DCI1_preregistration_v4.md` and its two companions (revision 1) | **Superseded in full. Historical design record only.** Never a source of requirements. |
| 9 | `user-notes/DCI-1_preregistration_v3.md`, `DECISIONS_V3.md`, `RESULTS_V3.md` | Historical. Read for the carry-over rule, the amendment machinery worth reproducing, and the defects v4 corrects. Never a source of v4 requirements. |
| 10 | `reports/br_pilot_v4/protocol.json`, `result.json`, `tools/br_pilot_v4.py`, `tests_v3/test_br_pilot_characterization.py` | **Non-confirmatory design evidence.** Read to understand what was measured and how. Its rows may never enter a v4 analysis. |

Apply them with this precedence: v4r2 first; this prompt only where v4r2
leaves ordinary software-engineering detail unspecified; everything else
as history.

If v3, revision 1, the pilot, existing code, or historical artifacts
disagree with v4r2, implement v4r2.

If a genuine scientific ambiguity survives a full reading of v4r2, record
it explicitly and fail closed. Do not resolve it by inferring intent from
v3, from revision 1, or from the pilot.

Create one canonical traceability document:

```text
docs/v4_traceability.md
```

For every substantive v4r2 requirement record:

```text
v4r2 section / requirement
resolved implementation
implementation location
test ID
status
```

Any unresolved scientific requirement blocks freeze. So does any
incomplete pre-freeze check.

---

## 2. Hard isolation from v3, from v2, and from the pilot

Treat the complete v3 implementation, the v3 evidence tree, the v2
material, and the B+R pilot cache as read-only historical material.

V4 gets its own implementation root. Follow the repository's existing
versioned-study convention. On present evidence that is:

```text
dci1/src/dci1v4/          package namespace dci1v4
dci1/evidence/dci1-v4/    registered evidence
dci1/durable_root/dci1-v4/  durable mirror
tests_v4/                 canonical test suite
```

Confirm the actual convention by inspecting the repository before
creating anything.

The v4 scientific implementation must have zero runtime dependency on
`dci1v3`, on any v2 package, or on `tools/br_pilot_v4.py`.

Specifically, do not:

- import `dci1v3` or any earlier DCI scientific module;
- call v3 prompt constructors, verifiers, calibration code, estimators,
  gate logic, masking code, analysis code, or reporting code;
- inherit from v3 study classes;
- read v3 or pilot configuration or registries at runtime;
- use v3 defaults as fallbacks;
- symlink v4 scientific files to v3 files;
- write v4 outputs into `evidence/dci1-v3/`, `durable_root/dci1-v3/`,
  `evidence/br-pilot-v4/` or `reports/br_pilot_v4/`;
- modify any v3, v2 or pilot artifact;
- migrate v3 or pilot state into v4 automatically;
- add compatibility layers whose purpose is to keep the v3 pipeline
  functioning as part of v4;
- execute a v3 stage to obtain a v4 scientific definition.

Repository infrastructure may be reused only when genuinely
study-independent: GPU locking, atomic filesystem operations, a generic
content-hash helper, a generic vLLM execution primitive. Wrap any reuse in
a v4-owned adapter. If a shared component embeds v3 scientific
assumptions, reimplement it inside v4.

Prefer duplicating a small neutral utility over introducing a scientific
dependency on v3.

Add an automated isolation test that fails if the v4 package imports from,
or opens a runtime path belonging to, v2, v3, or the pilot.

### 2.1 The one narrow carry-over, and how to do it without importing

v4r2 §10.2 permits the exact-count instrument to supply carried evidence
only when the construct string, the word-segmentation function source, the
counting function source, and the forty boundary case texts with their
expectations are byte-identical to the v3 artifacts.

Implement this as a **data-level** check, never an import:

1. read the v3 source files as bytes (`dci1v3/verifiers/words.py`,
   `dci1v3/verifiers/target.py`) and the frozen boundary-case fixture;
2. extract the two function sources by the same textual rule v3 used;
3. hash them and compare against the v4 copies you have written into
   `dci1v4/verifiers/`;
4. write a content-addressed v4 carry-over record naming the source, both
   hashes, and the provenance;
5. refuse on any mismatch, and require new v4 measurement evidence.

The v4 copy is the operative implementation. The v3 file is read as data
exactly once, at carry-over verification, and never at runtime.

The boundary suite for the exact-count instrument is **carried plus
extended**, per v4r2 §10.2: the v3 forty case texts and their expectations
are carried byte-identically, and the additional cases the §24 enumeration
requires and the v3 forty do not cover are authored and frozen for v4. The
carried subset must stay byte-identical. The word-length suite and every
family suite are authored for v4 in full.

**No other carry-over exists.** In particular, the pilot's reuse of
`gate2a solo:B:7` rows and confirmatory `AB added_pass` rows must not
appear anywhere in v4. Every v4 quantity is computed from v4 rows on v4
blocks.

---

## 3. What is in the repository, and what each thing is for

Inspect and confirm before relying on any of it. The list below is what
the design materials disclose; the repository is authoritative on what
actually exists.

### 3.1 v3 implementation, read for reference only

```text
dci1/src/dci1v3/protocol/constants.py      every registered v3 value
dci1/src/dci1v3/protocol/wordings.py       wording templates, length caliper
dci1/src/dci1v3/protocol/hashing.py        sha_text, sha_obj
dci1/src/dci1v3/verifiers/words.py         alpha_runs, words_lower
dci1/src/dci1v3/verifiers/target.py        s0..s3, graded, passes
dci1/src/dci1v3/verifiers/families.py      added_verifier(family, q)
dci1/src/dci1v3/verifiers/witnesses.py     verify_composition
dci1/src/dci1v3/generation/{cache,plans,prompts,backend}.py
dci1/src/dci1v3/engine/{fs,dispatch,signing,transitions,context}.py
dci1/src/dci1v3/stages/{gate1,gate2a,gate2b,inference,sensitivity}.py
dci1/src/dci1v3/analysis/{claims,estimators,bootstrap,run}.py
dci1/src/dci1v3/models/registry.py         model specs and revisions
dci1/src/dci1v3/topics/split.py            seeded stratified split
dci1/src/dci1v3/annotation/                blinded annotator GUI, rubric
dci1/src/dci1v3/protocol/data/autorater.json  frozen judge configuration
```

Read these to learn the shape of a working solution and the exact
invariants worth reproducing. Copy no code by import.

### 3.2 Machinery worth reproducing in v4's own namespace

These exist in v3 and v4r2 requires equivalents. Reimplement, do not
import.

- **Guarded claim emitter.** v3 `analysis/claims.py::licensed_equivalence`
  raises rather than emitting an unlicensed absence statement. v4 needs
  one guarded emitter per claim level (v4r2 §17.5).
- **Fail-closed stage dispatch.** v3 `engine/dispatch.py` plus
  `engine/transitions.py` verify the predecessor PASS record's hash and
  signature before any mutation.
- **Append-only artifact ledger.** v3 `artifacts.py` enforces the one-shot
  calibration rule *before* any mutation, so a deleted record file cannot
  re-open it. v4 needs the same property for its one-shot stages.
- **Write-once evidence and durable mirroring.** v3 `engine/fs.py`
  `write_json_once`, incremental byte-identical replication.
- **Partial-identification both-bounds rule.** v3 decision V12: a claim is
  licensed only when both recalculations license the same claim. v4r2
  §17.4 requires the same conservative reading for vacuity.
- **Masked-view field exclusion list.** v3 decision V11 enumerates the
  fields that would identify the true arm. v4 needs the analogous list for
  the companion dimension.
- **Autorater workflow invariants.** v3 amendments A2, A2.1, A2.2, A3,
  A3.1 and A3.2 encode: a class-stratified disjoint development and
  calibration split; a judge registry disjoint from the study models; a
  hashed configuration that fails closed on drift; realised
  evidence-boundary binding re-verified at calibrate and approval;
  one-shot calibration enforced by the ledger; a machine
  `measurement_basis` marker distinct from a bare PASS state; and audited
  supersession that parks rather than deletes. v4r2 §10.4 registers all of
  it prospectively. Reproduce it.
- **Access-controlled sequestered material.** v3 `tools/build_topics_v3.py`
  produced sequestered identities and hashes without materialising text,
  with an executable no-materialisation check on every load.

### 3.3 Design evidence, never analysis input

```text
user-notes/dci-construct-pass2.md               the construct decision
reports/br_pilot_v4/protocol.json               frozen pilot protocol
reports/br_pilot_v4/result.json                 pilot results
reports/br_pilot_v4/prompt_plan_*.json          pilot cell manifests
evidence/br-pilot-v4/<model>/                   pilot raw cache
tools/br_pilot_v4.py                            pilot tool
tests_v3/test_br_pilot_characterization.py      pins the reused v3 baselines
evidence/dci1-v3/<model>/                       v3 signed evidence
reports/nearmiss_sensitivity_v3.json            v3 unregistered sensitivity
autorater_forensics/experiments/human_review/   author-performed labels
reports/gate1_dev_review*.md                    judge failure-mode listings
```

You will read some of these to execute pre-freeze checks C6, C12, C13,
C14 and C18. Reading them for that purpose is required. Feeding any of
them into a v4 estimator is prohibited, and §14.2 of v4r2 requires an
executable guard that refuses exactly that.

---

## 4. Traps in the existing codebase

These are the places where a competent engineer following v3's shape will
implement the wrong thing for v4. Handle each explicitly and test it.

**T-1. The verdict model is target-and-added, not a vector.** v3's `Cell`
carries `arm`, `target_wording`, `added_wording`, `n`, `constraint_id`,
`severity`. Its rows carry `verdicts.s0` for the target and
`verdicts.added_pass` for the companion. v4's primitive is a **compliance
vector over every constraint present**, so the cell model is a *pair of
constraints with positions* and the row carries one verdict, one graded
score and one degeneracy flag per constituent. A composed generation
yields two `(outcome, companion)` observations, not one outcome and one
manipulation check.

**T-2. `added_verifier` returns a boolean and nothing else.** v4r2 §7.4
requires a graded score per constraint form and §9.3 requires a
non-vacuity predicate per constraint form. Neither exists. Implement both
in `dci1v4`, pin them with unit tests against hand-derived expectations at
every registered severity, and include both in the canonical verifier
hash. This is pre-freeze check C2.

**T-3. Non-violation constraints pass on empty output.** Every reference
family is "at most q …" and B is "every word at most m letters". An empty
or three-word answer satisfies them mechanically. In v3 that was a
footnote because these verifiers scored a secondary check. In v4 they are
primary outcomes. Implement the predicate, count vacuous passes per cell,
and route them through partial identification (v4r2 §9.3, §17.4). **Do not
filter them out of the primary estimand.**

**T-4. v3 computed failure; v4 computes compliance.** `gate2a.py::_rates`
derives failure as `verdicts["s0"] != row["n"]` for target cells and
`not verdicts["added_pass"]` for constraint cells. v4's delivery loss is
on the compliance scale and needs both constituents scored on every
composed row. Do not port the failure-rate helper.

**T-5. The order convention differs and the names collide.** v3 used
`target_first` and `added_first` as **block-level** strata, with
`added_first` meaning the added constraint is stated first. v4 makes order
a **cell-level** factor: every block runs both order variants of every
pair, and every configuration is estimated on all 384 blocks. Do not reuse
the v3 order names, do not assign order by block parity, and do not
stratify the bootstrap by order.

**T-6. Wording allocation must not be tied to the block index in a way
that collides with order.** v3's confirmatory rule was
`target_wording = i mod 4`, `added_wording = floor(i/4) mod 4`, with order
also `i mod 2`. Under a cell-level order that collision is gone, but the
offset formula is still required so the two wording indices decorrelate:
`w(c1) = i mod 4`, `w(c2) = (i + floor(i/4)) mod 4`, applied identically
to both order variants of a cell. The coverage assertion must refuse a
plan containing a structural zero.

**T-7. The completion cap must be selected against every registered
load.** v3's no-constraint arm truncated in 322 of 384 and 333 of 384
responses at the selected cap, so its accidental-compliance base rate was
measured on mostly truncated text. The v3 preregistration does not state
the load composition of its 96-prompt cap-selection set, so treat this as
a requirement rather than as a diagnosis: v4r2 §12.1 requires the
cap-selection set to contain zero-, one- and two-constraint prompts,
requires the zero-constraint truncation rate to be recorded separately,
and requires any quantity from a cell whose truncation rate exceeds 0.10
to be reported as a bound.

**T-8. The reference matching target inverted.** v3 matched R to **B** on
solo failure rate. v4 matches R to **A** on solo compliance. The v3
admission code, its caliper and its tie-breakers are the wrong rule.
Realised v3 references sit about 0.20 **above** A in solo compliance, so
v4 needs *harder* severities than v3 ever selected.

**T-9. Composed uptake must never rank or admit a reference.** In v4
composed compliance is the outcome. Any selection on it is circular.
Delete the v3 composed-eligibility ranking idea from your mental model:
v4's Gate 4 evaluates each cell type independently against a band and
computes no contrast between cells.

**T-10. There is no primary-draw selection rule in v4.** v3's
`H("primary-root", model_id, prompt_hash) mod 16` selected one draw of
sixteen. v4 averages all `M` draws into a cell mean and has no selector.
If you find yourself writing a selector, you have ported the wrong design.
The pilot's `P(B|A)` is already a draw-average over all 16 v3 draws, which
is why it differs from v3's `per_arm.AB.uptake`; both figures are correct
and they answer different questions.

**T-11. Reference-pool failure is not terminal in v4.** v3 returned
`REFERENCE_POOL_MISMATCH` and stopped the replication. v4 sets
`EXCESS_NOT_IDENTIFIED`, routes the model to the reduced design of §8.6,
and continues. Two of four v3 replications produced no evidence at all
because of the v3 rule; reproducing it would repeat that loss.

**T-12. The verifier-hash binding defect.** v3's binding was enforced at
the dispatcher only after a specific commit. v4r2 §10.6 names nine entry
points and pre-freeze check C5 adds the ladder screen and solo
calibration; implement the union of the eleven: ladder screen, solo
calibration, reference admission, composed-headroom validation, freeze,
confirmatory generation, scoring, resume and restart paths, analysis,
unmasking and report generation. Implement the five regression tests of
check C5.

**T-13. Deprecated and foreign sources.** The construct memo §B.0 records
a committed analysis table built entirely from files the project itself
marks DEPRECATED and FOREIGN, with about 98% byte-identical replicate
pairs and roughly half the nominal effective sample size. v4r2 §14.2 and
§26 require an executable guard that refuses any analysis input that is
not a registered v4 artifact. Test it against a legacy artifact, a v3
artifact and a pilot artifact.

**T-14. Seeding must derive from experimental identity.** The construct
memo §B.1 records that most legacy datasets seeded all requests in a batch
identically, giving about 98% byte-identical replicate pairs, and that
only one legacy programme seeded from experimental identity. v4's seed derives from the root seed, the v4 stage label, the
model identity, the prompt hash and the draw index. Register fresh v4 root
seeds and fresh domain-separation strings; do not reuse any `dci1v3:`
domain. Measure the realised duplicate rate (check C14); §14.2 fails
qualification above 0.05.

**T-15. Autorater determinism requires serialised serving.** The forensics
recorded unacceptable repeated-run label instability under concurrent
serving and exact repeatability at concurrency one. Any autorater
execution path must run serialised, or on an equivalently demonstrated
fixed-composition offline path, and must record which.

**T-16. Author-performed labels are not independent validation.** The 120
v3 blinded labels and the 56-item calibration set were produced by the
study author. They are diagnostic evidence. Never relabel them, never
carry them as v4 independent human validation, and never fabricate labels.

**T-17. The sealed reserved set.** A 40-item sealed set exists with a
recorded hash. Do not open it, do not inspect its composition, and do not
use it for tuning. v4's instrument population differs from v3's, so check
C4 must decide whether a **new** sealed set is required rather than
reusing that one.

**T-18. The v3 failure taxonomy is exact-count specific.** Its nine
categories describe how an exact-count constraint failed. In v4 it applies
to the exact-count outcome only, split by whether the realised margin is
exactly one, and it does not generalise to the word-length or budget
outcomes.

---

## 5. Registered models and inference

Four separate replications, in this execution order:

```text
1. google/gemma-3n-E2B-it
2. google/gemma-3n-E4B-it
3. Qwen/Qwen3-4B                    (hybrid, thinking disabled)
4. Qwen/Qwen3-4B-Instruct-2507
```

The Gemma models run first because their operating points are known from
v3 and the pilot. The Qwen models are the ones this architecture newly
unblocks and they carry the most information about whether the phenomenon
is a capability threshold.

**No replication is blocked by the outcome of another.** The v3 early-stop
rule is withdrawn. Do not implement it.

Re-pin every model revision in the v4 signed manifest before
qualification. Do not inherit a revision from the v3 manifest. A missing
or unavailable registered repository blocks v4 rather than triggering
substitution.

```text
backend: vLLM
dtype: bfloat16
temperature: 0.7
top_p: 0.9
top_k: 50
maximum_new_tokens: selected from {512, 768, 1024}
ladder_screen_draws_per_cell: 1
calibration_draws_per_cell: 4
confirmatory_cached_draws_per_cell: 4
observations_per_cell: 1 cell mean over all M draws
```

Zero-shot, single turn, no examples, tools, retrieval, self-consistency,
best-of-N, revision passes or extra turns. Disable thinking for
`Qwen/Qwen3-4B` through its actual supported mechanism, and record for the
others that thinking is unavailable or inactive.

Record and assert exact revision, tokenizer and chat-template identity,
GPU class and architecture, vLLM configuration, and the execution command.

Every study-wide rule is fixed in the signed registration manifest before
the first qualification (v4r2 §6.1, cross-replication firewall). Only
these adapt mechanically by model, and only through the registered gates:

```text
n*
m*
completion-token cap
one selected severity per admitted reference family
the identities of the three admitted reference families
whether the full or the reduced design runs
```

Do not pool across models and do not create a cross-model estimand or
multiplicity family.

---

## 6. Constraints, graded scores, predicates, witnesses

Implement:

```text
A: Use the word "however" exactly n times.        n in {1..8}
B: Every word in the answer must have at most m letters.   m in {7,8,9,10}
```

`m >= 7` is structural: `however` has seven letters. Under v4 that floor
is benign, because B is an outcome whose solo compliance should be high
with room to fall.

The registered lexical convention, v4r2 §7.2, applies to every verifier: a
word is a maximal run of alphabetic characters; suffix and letter tests use
the lower-cased word; comma and upper-case counts read raw characters.

The exact-count rule `S0`, v4r2 §9.2: take the whole response, lower-case
it, find every maximal alphabetic run, count the runs equal to `however`,
pass when the count equals `n`. Every state other than pass is a failure,
including empty responses, refusals, truncations and verifier-processing
failures.

Three alternatives are registered for the robustness family and never
redefine the outcome:

```text
S1  the same procedure without the lower-casing step
S2  non-overlapping substring occurrences in the lower-cased text
S3  S0 after deleting a leading colon-terminated line and any line
    repeating an active constraint wording
```

`S1` to `S3` apply to the exact-count outcome only. The **independent
reimplementation required by check C1 must be written from the registered
prose of v4r2 §7 and §9 and from nothing else**: §7.1 for the two outcome
constraints, §7.2 for the family templates and the lexical convention,
§7.4 for the graded scores, §9.2 for the scoring rules and §9.3 for the
non-vacuity predicates. It must not read the v4 primary source and must
not read v3.

Implement all eight reference families with the **complete integer
ladder**, 94 severities in total:

```text
RF1 at most q words begin with b            q in 0..8
RF2 at most q words end with "ing"          q in 0..8
RF3 at most q words have one letter         q in 0..8
RF4 at most q words contain a doubled letter q in 0..6
RF5 at most q comma characters              q in 0..12
RF6 at most q upper-case English letters    q in 0..12
RF7 at most q words contain the letter a    q in 0..24
RF8 at most q words end with y              q in 0..8
```

The family maxima are the v3 grid maxima. v4 fills the interiors. At most
one severity per family enters the final set, and the three admitted
references come from three distinct families.

### 6.1 Graded scores

```text
A:   max(0, 1 - abs(s0 - n) / n)
B:   1 - (words longer than m) / (total words); 0 for an empty answer
RFx: min(1, q / max(q, realised count)) for q > 0
     indicator(count == 0)               for q = 0
```

Deterministic, recorded on every row, never a primary outcome, members of
the robustness family.

### 6.2 Non-vacuity predicates

```text
A:   non-empty and not truncated
B:   non-empty, not truncated, at least 20 words
RFx: non-empty, not truncated, at least 20 words
```

A pass on a non-violation constraint by a response failing its predicate
is a **vacuous pass**. Count it as a pass in the primary estimand. Report
the vacuity rate **per cell and per constraint**, gate on family F6, and
recompute every primary estimand with vacuous passes forced to failures as
partial-identification bounds. A pass produced by a degenerate response is
never described as engagement without the predicate (v4r2 §10.1).

### 6.3 Executable pre-generation tests

- parse independence for every registered verifier;
- **joint satisfiability for all ten unordered pairs** at every candidate
  severity, with a machine-verified witness. v3 certified only `A+B` and
  `A+R`; v4 additionally needs `B+R` and `R+R'`. This is check C9;
- bidirectional non-entailment for all ten pairs;
- four frozen wordings per constraint, checked for identical verifier
  behaviour on a twenty-response fixture suite at every severity;
- the wording-length caliper measured against **A**, not against B.
  Severity parameters render as numerals and contribute no words, so the
  caliper is severity-invariant; assert that property rather than assuming
  it.

---

## 7. Topics, prompts, blocks, and cells

Author **624 new topics**, 52 per subject area across the twelve declared
strata, each verified individually against the four authoring rules of
v4r2 §6.2. No v3 topic and no B+R pilot topic may enter any v4 set. Do not
inspect v3 sequestered text.

Seeded split per stratum:

```text
2  pre-screen
8  solo calibration
2  composed validation
32 confirmatory
8  sequestered
```

Totals: 24 / 96 / 24 / **384** / 96. All five disjoint. v4 sequestered
text stays inaccessible throughout.

Every prompt is: topic question, numbered active-constraint list,
`Answer:`.

### 7.1 The confirmatory cell set

Five registered constraints per replication: `A`, `B`, `R1`, `R2`, `R3`.
Every block runs:

```text
5  solo cells                    one per constraint
20 composed cells                each of the 10 unordered pairs
                                 in each of the 2 instruction orders
-----------------------------------------------------------------
25 cells per block
```

Every composed generation is scored on **both** of its constraints, so a
block yields 5 solo observations and 40 composed `(outcome, companion)`
observations per draw.

Per model:

```text
384 blocks
25  cells per block
4   cached draws per cell
38,400 cached confirmatory generations
```

Four models: 153,600.

Reduced design when fewer than three references are admitted:

```text
4 cells per block   A solo, B solo, A+B order 1, A+B order 2
6,144 generations per model
```

Greedy sensitivity: the 20 composed cells on the first 96 confirmatory
blocks at temperature 0, one draw per cell, 1,920 generations.

### 7.2 Order and wording

Order is a **cell-level** factor. Both order variants of every pair are
present in every block, so order is balanced by construction and each
configuration is estimated on all 384 blocks.

Wording is a **block-level** factor:

```text
w(c1) = i mod 4
w(c2) = (i + floor(i / 4)) mod 4
solo cells use i mod 4
```

applied identically to both order variants of a cell. Each of the four
wordings must appear in 96 of the 384 blocks in each order of each cell
type. Assert that count explicitly at every generative stage, refuse a plan
containing a structural zero, and fail qualification where a formula and an
assertion disagree.

---

## 8. The primitive observation and the row schema

Every generation records, for **every constraint present in that prompt**:

```text
constraint identity, severity, position, wording index
compliance verdict
graded score
non-vacuity flag
verifier source hash
```

including, in **every** cell, the verifier verdict of every registered
constraint that is **absent** from that prompt. That is how accidental
compliance is measured, v4r2 §25: the base rate at which an unconstrained
or differently-constrained answer satisfies a constraint by chance. Mark
those verdicts as accidental-compliance diagnostics, never as outcomes.

and per row:

```text
stage, artifact state, model replication, block, cell type
constituent pair and order, draw index
prompt hash, model revision, backend version, interpreter identity
dependency digest, hardware class, seed
raw response, response content hash
token counts, finish reason, truncation
emptiness, word count
verifier-processing failure flag
accidental-occurrence count of the exact-count target word in every cell
  where A is absent
```

Nothing is marginalised at record time. The exact-count verdict has no
privileged status.

### 8.1 The procedural pilot, Gate 0

Twelve fixed pre-screen topics, all 25 cells, both orders, the registered
wording allocation, `M = 4`: **1,200 cached draws**. Fixture values for
`n`, `m` and the reference severities that exercise the structure and
cannot become calibration evidence.

The pilot is technical only. Do not compute or expose any compliance rate,
delivery loss, companion swap or contrast. Persist its structurally
complete analysis fully redacted, with every numeric value replaced.

All eight acceptance conditions of v4r2 §19 must hold:

1. every logical cell and draw committed exactly once;
2. every cell yielding one cell mean over exactly `M` accepted draws;
3. zero technical generation failures after retries;
4. every codebook field present and in domain;
5. the full pipeline running to a structurally complete redacted result;
6. mutating one stored byte changing its content hash and causing the
   analysis to refuse the row;
7. cache deletion and durable restore reproducing every row with matching
   hashes;
8. the separate pilot mask cycle completing without touching the
   confirmatory mask namespace.

Failure returns `APPARATUS_FAILURE`. A repair creates a new producing
commit and requires qualification and the pilot to run again.

---

## 9. Measurement

### 9.1 Five primary instruments, not one

Under v4 the exact-count rule, the word-length rule, and each admitted
family verifier are all primary instruments. v3 required the forty-case
boundary suite and three-process determinism of every verifier, so those
two lines already extend beyond the exact-count rule; everything else was
exact-count only. For **every** registered outcome verifier, v4 requires:

- three-process determinism, exactly `1.000`;
- a frozen boundary suite of at least forty cases covering the §24
  enumeration. The exact-count suite is the v3 forty cases carried
  byte-identically **plus** the additions §24 requires; the word-length
  suite and every family suite are authored for v4 in full;
- an independent reimplementation written from the registered prose by a
  process that does not read the primary source, agreement exactly
  `1.000`;
- a targeted adversarial corpus, with the realised frequency of each
  boundary case reported per cell type;
- human agreement under the tool-assisted protocol, or the autorater
  pathway with `HUMAN_VALIDATION_UNAVAILABLE`.

This is pre-freeze check C1 and it is the single largest new
implementation burden.

### 9.2 Human agreement

At least one annotator independent of the design and analysis team. The
interface has the annotator mark each qualifying feature and tallies the
annotator's own marks. It performs no automatic detection, highlighting,
counting or normalisation, and shows no cell label, model, companion,
verdict, item identity or other annotator's work.

Criterion: one-sided 95% Wilson upper bound on human-to-verifier
disagreement at most `0.10` in each verifier class, on a seeded sample of
`min(150, N_c)` natural responses per class, with the fail class
additionally split by whether the realised margin is exactly one.

Statuses: `MEASUREMENT_NOT_ESTABLISHED`,
`MEASUREMENT_EVIDENCE_INSUFFICIENT`, and the identification status
`HUMAN_VALIDATION_UNAVAILABLE`.

Keep the identification status distinct from the machine measurement-basis
field, which takes exactly one of:

```text
human_validated
autorater_calibration_approved
human_validation_unavailable
```

Every analysis record carries the basis, and while it is not
`human_validated` every record carries the registered scope sentence of
v4r2 §10.5 verbatim: *the outcomes are verifier-defined and support no
claim about compliance as an independent human would judge it.*

Reimplement the annotation interface inside v4's namespace, preserving the
blinding and finalisation properties v3's GUI established: per-annotator
seeded display order so a class-ordered packet cannot leak; structural
absence of item identities, verdicts and other annotators' work;
finalisation requiring a label on every item, immutable thereafter; and
session files recorded outside the evidence tree until submitted through
the registered pathway. Extend it to five instruments. Read the v3
interface for its properties; import nothing from it.

### 9.3 Autorater pathway

Implement v4r2 §10.4 in full: deterministic class-stratified disjoint
split; one judge from a registry disjoint from the study models at a
pinned revision with a hashed configuration that fails closed on drift;
**serialised deterministic execution at concurrency one**; a
development-phase repeatability check; a single-shot signed freeze binding
verifier hashes, the regression-test file and its passing run, the split
derivation, the realised evidence boundary and the judge configuration;
one-shot calibration on the untouched half enforced by an append-only
ledger written before any mutation; explicit researcher approval writing
`measurement_basis = autorater_calibration_approved`.

Selection hierarchy for the judging condition: valid deterministic
execution, then adequate cap and absence of problematic truncation, then
valid parsing and coverage, then agreement with human labels, then the
cheaper setting when performance is practically indistinguishable.
Compare candidate configurations **paired** on the same items.

Autorater judgments never become behavioural scores, never overwrite a
deterministic verdict, and live in separate artifacts.

**A v4 reserved final-check set** is sealed at Gate 1 with its hash
recorded, and opened at most once after every autorater choice is frozen.
It is never used for tuning and is never rerun to obtain a better result.
Check C4 decides whether the v3 sealed set may serve or whether v4's wider
instrument population requires a new one; the v3 set stays sealed either
way.

### 9.4 Verifier freeze and downstream binding

One canonical verifier hash covering every source and configuration
component that can change semantics for any registered instrument,
including the graded-score functions and the non-vacuity predicates.
Frozen in the Gate 1 record. Re-verified at every entry point listed in
T-12. Never silently updated. Historical rows stay auditable under their
own recorded hash and are never treated as newly valid.

---

## 10. Stage machine, gates, and identification statuses

The only valid sequence:

```text
QUALIFIED
→ GATE_0_APPARATUS
→ REGIME_SCREEN
→ GATE_1_MEASUREMENT
→ GATE_2_REGIME
→ GATE_3_REFERENCES
→ GATE_4_COMPOSED_HEADROOM
→ GATE_5_FREEZE
→ confirmatory generation
→ masked analysis
→ unmasking and unmasked analysis
```

Every command verifies the predecessor PASS record's content hash and
signature **and** re-verifies the frozen verifier hash before any
mutation. A terminal state mechanically disables every later generation
command.

**Gate 3 is not terminal.** Fewer than three admitted families sets
`EXCESS_NOT_IDENTIFIED`, selects the reduced design, and proceeds. Encode
this as an identification status on the record, not as a stop.

### 10.1 Regime pre-screen

Cap selection on a fixed subject-balanced 96-prompt set containing
zero-, one- and two-constraint prompts, at each of `{512, 768, 1024}`.
Smallest cap with truncation at most `0.10` over the constrained prompts.
None qualifying returns `RESPONSE_LENGTH_INCOMPATIBLE`. Record the
zero-constraint truncation rate separately.

**The truncation-bound rule is operative everywhere, not only here.** Any
quantity derived from a cell whose realised truncation rate exceeds `0.10`
is emitted as a bound and labelled as one, at every stage, including every
accidental-compliance figure (v4r2 §12.1, §25). Implement it as a property
of the emitter, not as a note in a report.

Dense ladder screen at the selected cap on the 24 pre-screen topics, one
draw per cell: the full `n` grid, the full `m` grid, and all 94 ladder
severities. `(8 + 4 + 94) * 24 = 2,544` generations. Produces the
shortlist of at most three severities per family nearest A's pre-screen
solo compliance. The shortlist is written before Gate 2 generates
anything.

### 10.2 Gate 2, operating regime

On the 96 solo-calibration topics at `M_cal = 4`:
`(8 + 4 + 24) * 96 * 4 = 13,824` generations at most.

```text
n*: eligible solo compliance of A in [0.50, 0.85], minimise |p - 0.70|,
    smaller n breaks an exact tie
m*: eligible solo compliance of B in [0.60, 0.95], minimise |p - 0.80|,
    smaller m (more restrictive) breaks an exact tie
```

Regime adequacy additionally requires the solo vacuity rate for B at most
`0.10` and a non-degenerate graded distribution for each outcome
constraint, meaning not concentrated above `0.99` or below `0.01`. Failure
returns `REGIME_NOT_FOUND`, which is a statement about the registered grid
and never about the model or the hypothesis.

`GRID_RESOLUTION_INSUFFICIENT` applies when two adjacent registered
severities lie on opposite sides of a whole admission band;
`TARGET_RANGE_EXHAUSTED` and `FOCAL_RANGE_EXHAUSTED` apply when the curve
reaches a grid boundary while staying on one side of the band. Every
diagnosis records the complete curve and makes a claim only about the
registered grid.

### 10.3 Gate 3, references

Within family `f`, choose the severity minimising the absolute difference
between its solo compliance and A's solo compliance at `n*`, subject to:

```text
absolute difference <= 0.10 on the 96 solo-calibration topics
95% Newcombe interval for the paired difference intersects +/- 0.05
absolute difference <= 0.15 on the disjoint 24 pre-screen topics
every wording within 20% of the corresponding A wording length
whole-answer scope and parse independence for every registered verifier
joint satisfiability and non-entailment against A, against B, and
  against every other admitted reference
family solo vacuity rate at that severity <= 0.10
```

The less restrictive severity breaks an exact within-family tie. At most
one severity per family. The final three are the admitted families with
the smallest solo distance from A, family identifier breaking an exact
tie.

Fewer than three: `EXCESS_NOT_IDENTIFIED` and the reduced design.

### 10.4 Gate 4, composed headroom

Every registered cell type on the 24 composed-validation topics at
`M_cal = 4`, at most `20 * 24 * 4 = 1,920` generations. Each cell's
compliance rate is evaluated independently against `[0.05, 0.95]` for each
of its two constraints. **The gate ranks nothing, selects nothing, and
computes no contrast between cells.** Any cell type outside the band
returns `COMPOSED_HEADROOM_FAILURE`.

### 10.5 Gate 5, freeze

Do not execute this gate in this task. Implement it, and implement the
completeness check that refuses to freeze while any required field, any
open decision, or any blocking pre-freeze check is unresolved.

The freeze record carries, per v4r2 §18.1: model revision; completion cap;
`n*`; `m*`; the admitted reference families and severities or the
`EXCESS_NOT_IDENTIFIED` marker; every wording; topic splits; prompt
template; chat-template hash; every verifier source and the canonical
verifier hash; the graded-score definitions; the non-vacuity predicates;
decoding settings; `M` and the block count with the §16.1 re-estimate that
justified them; seed rules; the 25-cell plan; family declarations;
thresholds and regions; precision preconditions; the claim ladder; the
codebook; producing commit; clean-tree assertion; dependency and
environment digests; hardware record; gate-record hashes; the Gate 1
measurement basis; and the complete analysis plan. An unknown or
unresolved required field fails the freeze.

---

## 11. Cached generation

`M = 4` draws per cell. **All `M` enter the cell mean. There is no
selector.** Each draw's identity derives from at least:

```text
model_id, model_revision, prompt_hash, draw_index, v4 root seed, v4 stage label
```

Require exactly `M` committed accepted draws per cell before any cell mean
is formed. A missing draw is an integrity failure: repair only the
predetermined missing draw identity with its predetermined seed. Never
shrink a cell, average around a gap, impute, substitute, or encode a gap
as model behaviour.

Keep separate random-number systems for model generation and for the
statistical bootstrap.

**There is no pseudo-run machinery in v4.** v3's 1,000 pseudo-runs each
selected one of sixteen cached draws per cell; v4 has no selector, so the
construct has no referent. What replaces it is the registered secondary of
v4r2 §23: the **realised variance decomposition**, meaning
$\sigma^2_{\text{topic}}$, $\sigma^2_{\text{draw}}$ and the within-block
correlations of §16.1 estimated from the confirmatory cell means, reported
beside every primary estimate together with the realised simultaneous
half-width and the achieved detectable effect it implies.

---

## 12. Estimation and analysis

The **block** is the assignment, pairing, clustering and generalisation
unit. Cached draws are never independent observations. Cells are never
resampled.

Per configuration, meaning per (model, instruction order), estimated on
all 384 blocks:

```text
D(c <- g) = E[ mean_M X_c | c alone ] - E[ mean_M X_c | c with g ]

Primary family F1:
  D(B <- A)
  D(A <- B)
  Lambda  = D(B <- A) - D(A <- B)
  Delta_R = D(B <- A) - mean_j D(B <- R_j)
```

Note the algebra: the solo baseline cancels from `Delta_R`, so implement
it as `mean_j E[X_B | B+R_j] - E[X_B | A+B]` and assert the two forms
agree.

Families, each with its own simultaneous 95% interval by the studentised
maximum-deviation bootstrap over blocks, 10,000 resamples:

```text
F1 Primary                     4 members
F2 Companion heterogeneity     6   D(B<-R_j), Delta_j
F3 Outcome-side control        4   D(A<-R_j), Delta^A
F4 Matrix completion           4   D(Rbar<-A), D(Rbar<-B), D(Rbar<-Rbar'), Xi
F5 Robustness                  6   F1 under vacuity-forcing; D(B<-A) and
                                   Delta_R under a graded threshold at 0.99
F6 Degeneracy symmetry         4   vacuity-rate differences, B cells vs B solo
F7 Reciprocal detail           6   D(R_j<-B), D(R_j<-A)
```

Writing `D(Rbar <- g) = mean_j D(R_j <- g)` for a companion `g` outside
the reference set, and `D(Rbar <- Rbar')` for the mean of
`D(R_j <- R_k)` over the six ordered pairs of distinct admitted
references, the secondary members are:

```text
Delta_j  = D(B <- A) - D(B <- R_j)
Delta^A  = D(A <- B) - mean_j D(A <- R_j)
Xi       = Delta_R - [ D(Rbar <- A) - D(Rbar <- Rbar') ]
```

These two aggregation rules are registered in v4r2 §11.5. Assert them in
code rather than inferring them at the call site.

Šidák critical values for reference: 2.4909 at k = 4, 2.6310 at k = 6.
The bootstrap supplies the exact value.

Thresholds: `Delta_R` against `0.10` and `0.25`; smallest effect of
interest `0.10` for `D` and `Lambda`; precision preconditions
`0.05` for `D` and `Delta_R`, `0.08` for `Lambda`, `0.06` for `Delta_j`.

`Delta^A` is v3's registered pooled swap effect re-expressed on the
compliance scale. Implement it as a **demoted diagnostic** with its three
gates: outcome headroom, a companion matched on measured solo compliance,
and the configuration quoted with the number. Add a test asserting the
algebraic identity, writing `C` for a compliance rate and `F = 1 - C` for
the corresponding failure rate:

```text
Delta^A = mean_j C(A | A+R_j) - C(A | A+B)
        = F(A | A+B) - mean_j F(A | A+R_j)
```

the second form being exactly v3's `secondary.pooled_swap_effect`.

### 12.1 The variance model and the allocation menu

Implement v4r2 §16.1 and §16.3 so that check C12 can re-run the menu rule
mechanically.

```text
p(1-p) = 0.215
phi    = 0.27 under an among-reference correlation of 1
         0.37 under an among-reference correlation of 0.5
rho    = 0.5   between a cell containing A and a cell containing a
               reference with the same outcome constraint
sigma2_topic = phi * p(1-p)          0.0581 at phi = 0.27
sigma2_draw  = (1 - phi) * p(1-p)    0.1570 at phi = 0.27

Var[Delta_R] = ( 2(1-rho) s2_topic + s2_draw (1/M + 1/(3M)) ) / T
Var[D]       = ( 2(1-rho) s2_topic + 2 s2_draw / M ) / T
Var[Lambda]  = ( 4(1-rho) s2_topic + 4 s2_draw / M ) / T
```

The registered menu, all at 25 cells, with half-widths at phi = 0.27:

```text
blocks  M   generations/model   hw D    hw Delta_R  hw Lambda  hw Delta_j
   288  4              28,800   0.0542      0.0488     0.0767      0.0573
   384  4              38,400   0.0470      0.0422     0.0664      0.0496
   480  4              48,000   0.0420      0.0378     0.0594      0.0444
   384  8              76,800   0.0396      0.0369     0.0561      0.0419
   480  8              96,000   0.0355      0.0330     0.0502      0.0375
```

The rule: take the smallest entry meeting every precision precondition
under the pre-freeze variance re-estimate, and record the choice in the
freeze. Under the registered constants that entry is 384 blocks at
`M = 4`. **Implement the rule and report what it selects. Do not choose
the allocation; that is V1.**

### 12.2 The claim ladder

Five levels with one guarded emitter each (v4r2 §3, §17.5), each with its
licensing rule and identification gate, all read within one configuration:

```text
L1   delivery loss exists
     F1 simultaneous interval for the named D(c <- g) has lower bound > 0
     gate: c has solo headroom; the position caveat is stated

L2   directional asymmetry
     F1 simultaneous interval for Lambda excludes 0
     gate: L1 conditions for both D(B <- A) and D(A <- B)

L3a  excess above the generic-load threshold
     F1 simultaneous interval for Delta_R has lower bound > 0.10
     gate: three references admitted, else EXCESS_NOT_IDENTIFIED

L3b  pair-specific threshold reached
     the same interval has lower bound > 0.25

L3c  generic compositional load
     the same interval has upper bound < 0.10

L4   replication
     the same L1/L2/L3 classification in every registered configuration
     gate: every configuration reached the corresponding level

L5   semantic identity-specificity, universal pair property, arbitration,
     mechanism, generalisation
     never licensed; no code path emits it
```

An interval spanning 0.10 or 0.25 records `INDETERMINATE` at that
threshold **with both bounds**. A member whose realised simultaneous
half-width exceeds its precondition records `INSUFFICIENT_PRECISION`,
withholds every equivalence and threshold statement, and still reports a
resolved direction if one exists. Failure to exclude zero is never
reported as absence.

Reproduce the fifteen-row outcome vocabulary of v4r2 §28.1 as the fixed
mapping from interval geometry to licensed statement, including the
reference-heterogeneity and companion-difficulty qualifiers of §13.4 and
§13.2: when the three `Delta_j` intervals do not agree on one side of the
threshold used, the L3 statement names the disagreeing reference and its
value; when a realised confirmatory-measured companion-difficulty gap
exceeds 0.15, the L3 statement names the reference and its gap and the
§23 sensitivity is reported beside it.

Every emitted statement carries:

```text
claim_level, configuration, family, interval_type,
identification_status, measurement_basis,
position of the outcome constraint
```

Executable rules: each emitter refuses a member name not registered to it,
so a secondary quantity cannot appear inside an L1, L2 or L3 statement; a
check refuses a statement missing a field; a second check refuses a
statement quoting a scalar without its configuration; the equivalence
emitter's precondition is the interval region **and** the half-width
precondition, and the analysis aborts if it is reached with the
precondition false.

L5, covering semantic identity-specificity, universal pair properties,
arbitration, mechanism and generalisation, is permanently withheld. There
is no code path that emits it.

### 12.3 Prohibited and mediating quantities

Response length, token count, truncation, finish reason, graded score,
vacuity flag, accidental occurrence count, joint state and every other
post-generation quantity are recorded and never enter a primary estimand
as covariate, filter, stratifier or weight. Assert this from the codebook
causal-role field.

Every L1 statement names the position of its outcome constraint. In the
configuration where that constraint is stated second the statement carries
`POSITION_CONFOUNDED` and the registered wording that composition and
position change together, because the solo baseline places its single
constraint in position one (v4r2 §11.4).

**Response length is registered as a mediator**, reported and never
conditioned on. Implement the descriptive within-strata decomposition and
emit no mediation effect.

Fail closed on missing cells, incomplete draw sets, duplicate accepted
rows, non-finite standard errors and non-finite bounds. Retain degenerate
all-identical contrasts and report them.

**Missingness and duplicates.** Retry an invalid generation under the
registered seed derivation. A cell still short of `M` committed draws
fails the run closed for that cell; never impute, substitute or average
around a gap. Report missingness per cell type and per configuration
together with the arm-differential rate, and report any cell type above
`0.01` beside every primary estimand. Count byte-identical replicate pairs
within cells; a duplicate rate above `0.05` in any cell fails
qualification.

**Fixed size.** No interim analysis, no optional stopping, no adaptive
sample size. The analysis runs once, in the fixed order of v4r2 §21.

---

## 13. Masking

Permute the **companion label** within each `(outcome constraint, order,
block)` group of composed observations, from the system random source.
Solo cells carry no companion and are not permuted.

Declared limitation, which must appear in the analysis records: a composed
generation contributes two observations whose companion labels are
permuted independently, so joint-state and joint-success quantities cannot
be computed in the masked phase. Compute them after unmasking under the
registered plan and label them as computed post-unmasking. They support no
L1, L2 or L3 claim.

Maintain separate `pilot_mask` and `confirmatory_mask` namespaces. One
named unmasking function, invoked once, recording timestamp, mask-key hash
and analysis-code hash. Executable checks: permuted labels differ from
true labels in at least half the blocks in every group; the mask-key file
is opened exactly once in a full run; the recorded analysis-code hash
reproduces every masked-phase output byte for byte.

Masked-phase changes to an estimand, family, threshold, region,
precondition, reference set, verifier, scoring rule, claim rule, claim
level, non-vacuity predicate or topic split are forbidden.

---

## 14. Artifacts, provenance, codebook

Monotonic artifact states `generated`, `committed`, `accepted`,
`superseded`, with the closed artifact-type vocabulary of v4r2 §26. A
committed artifact becomes accepted only after durable write, content-hash
verification, stage authorisation, predecessor-gate verification, schema
validation and frozen-plan membership. A superseded artifact never returns
to accepted. Append-only transition log for every attempted transition,
with `generated`, `committed` and `accepted` counts reported separately.

Per-model records:

```text
qualification.json      gate0_apparatus.json    regime_screen.json
gate1_measurement.json  gate2_regime.json       gate3_references.json
gate4_composed.json     gate5_freeze.json
transition_log.jsonl    terminal_report.json
```

and when confirmation exists, `confirmatory_manifest.json`,
`masked_result.json`, `unmasked_result.json`. One frozen path function.
Unexpected, stale or missing paths fail evidence verification.

Clean worktree required, `writer_dirty = false` for registered artifacts,
the complete v4 implementation tracked before the first v4 artifact,
`uv.lock` plus a deterministic frozen export as the canonical dependency
representation, and every environment field of v4r2 §27. Record a
container digest only when the producing process actually runs in that
container. Implement restoration from durable storage without regenerating
committed model output.

**The machine-readable result table** carries, per v4r2 §30, each estimate
with its configuration, claim level, family, identification status,
measurement basis, standard error, marginal and simultaneous bounds,
realised half-width, realised variance decomposition, achieved detectable
effect and cell counts. Every reported figure must be reproducible from
that table without regenerating a response, and every number in it from
accepted raw responses in the recorded environment. No number is
transcribed by hand.

**Contamination controls.** Embed a canary string in the released dataset
file. At release, query the exact text of each confirmatory topic against
a public web search index and report the number of exact-phrase matches.
Release the 528 non-sequestered v4 topics with a manifest recording that
96 of the 624 are withheld. The 96 v4 sequestered topics and the 96 v3
sequestered topics stay withheld.

**Amendment register.** One append-only register carrying each amendment's
text, its timing relative to every affected artifact, what it supersedes
and what it leaves untouched. Before the study-wide freeze a change is a
revision of the preregistration and is prospective by definition. After
it, only operational settings that cannot change a scientific quantity may
move, with a recorded environment note; every other change creates v5. An
amendment is never used to weaken a criterion so a gate passes.

Codebook with `name, type, permitted values, units, causal role,
definition` and causal role in `identity, treatment, design, outcome,
post-treatment, provenance`. Implement the four executable codebook
checks.

---

## 15. Terminal statuses and identification statuses

Terminal, stopping the replication:

```text
QUALIFICATION_FAILURE
APPARATUS_FAILURE
RESPONSE_LENGTH_INCOMPATIBLE
TARGET_RANGE_EXHAUSTED
FOCAL_RANGE_EXHAUSTED
GRID_RESOLUTION_INSUFFICIENT
REGIME_NOT_FOUND
COMPOSED_HEADROOM_FAILURE
MEASUREMENT_NOT_ESTABLISHED
MEASUREMENT_EVIDENCE_INSUFFICIENT
```

Identification, **not** stopping the replication:

```text
EXCESS_NOT_IDENTIFIED       fewer than three admitted references
POSITION_CONFOUNDED         attached to L1 where the outcome is stated second
HUMAN_VALIDATION_UNAVAILABLE
```

Per-quantity result markers, recorded on the estimate rather than on the
replication:

```text
INSUFFICIENT_PRECISION      realised half-width above its precondition
INDETERMINATE               the Delta_R interval spans a threshold
```

Every terminal record carries the model and revision, gate, criterion,
threshold, observed value, complete curves, admission table, composed
table, degeneracy and truncation summary, verifier status and measurement
basis, artifact hashes, producing commit, environment digest, the
strongest permissible statement, the estimands left unanswerable, and
verbatim: **a terminal pre-confirmatory status carries no evidence about
the effect.**

Neither `REFERENCE_POOL_MISMATCH` nor `COMPOSED_UPTAKE_MISMATCH` is a v4
status; do not emit either. Both remain the correct **historical** labels
when v4 documents cite the two v3 Qwen terminations or the withdrawn
revision 1 gate, so the ban is on emission, not on the string.

---

## 16. Anti-regression checks

Add tests or static assertions preventing reintroduction of superseded
assumptions.

### Against v3

- target failure `F_A` as the sole or primary outcome;
- `tau` as a primary estimand;
- the primary-draw hash selector and `M = 16`;
- one draw of sixteen entering the estimator;
- order as a block-level stratum, and `target_first` / `added_first`
  naming;
- pooling only within an order stratum of 192 blocks;
- reference matching to B on solo failure rate;
- the four-point severity grid;
- `REFERENCE_POOL_MISMATCH` as a terminal status;
- composed-target-failure ranking of references;
- calibration that generates `A+B` with its outcome verdicts computed and
  exposed to a selection rule;
- uptake treated as a manipulation check only, rather than as an outcome;
- the six-arm confirmatory design and six-arm masking;
- exchangeability as the gate on an identity-specific claim;
- the early-stop rule blocking later replications;
- reading live scientific state from `dci1v3`.

### Against v4 revision 1, which is superseded

Assert only what the corpus attests about revision 1, namely the items
listed in `DCI1_v4r2_changelog.md` and the revision 1 to revision 2 change
table. Do not invent a revision 1 parameter in order to ban it.

- any surrogate outcome constraint, in particular one on the word *hence*;
- the estimand `iota` and any outcome-crossing difference in differences;
- the eleven-arm design with an S-side;
- composed uptake as an admission predicate, and the `0.15` uptake
  caliper;
- `COMPOSED_UPTAKE_MISMATCH` as a status;
- revision 1's **justification** for its allocation, namely sizing against
  an expected or projected effect for the withdrawn estimand rather than
  against the absolute precision preconditions. Ban the reasoning, not the
  numbers: every row of the §16.3 menu, including 384 blocks at `M = 8`
  and 480 blocks at either `M`, is a live entry the menu rule may select;
- pooling the order estimands with an interaction gate, and any
  order-conditional estimand estimated on fewer than all 384 blocks;
- the twelve-item `U1` to `U12` open-decision register, superseded by
  `V1` to `V9`.

No allocation may be banned by a static assertion, because every menu row
is selectable by the registered rule. Assert instead that the selected
allocation carries the menu-rule evidence that chose it. Nothing in the
corpus records revision 1's topic-bank size, its precision preconditions,
or a point-difference reference caliper, so assert nothing about them.

### Against the legacy corpus

- ingesting any artifact classified DEPRECATED or FOREIGN;
- counting byte-identical replicate pairs as independent replicates;
- quoting a scalar without its configuration;
- describing author-performed labels as independent validation;
- carrying any threshold, region, precondition or caliper without its
  registered provenance recorded in the manifest. The four provenances are
  distinct: the `Delta_R` thresholds 0.10 and 0.25 come from
  `dci-construct-pass2.md` §G row 1; the smallest effect of interest 0.10
  and the equivalence region are carried from v3 §11; the precision
  preconditions come from v4r2 §16.2; the calipers come from §13.2.

Use `DCI1_v4r2_changelog.md` and `DCI1_v4r2_scientific_change_summary.md`
as the final audit checklists and demonstrate that every listed change is
represented in code or tests.

---

## 17. Canonical test groups

### T1. Authority and isolation
Source precedence; zero v2, v3 or pilot scientific imports; separate
artifact roots; immutable historical evidence; the carry-over performed as
a data-level byte comparison rather than an import; the
deprecated-and-foreign input guard; and the §6.1 cross-replication
firewall, asserted statically: no study-wide value is reachable from a
per-model record, and no per-model outcome can write a study-wide rule.

### T2. Model execution
Exact repository and revision, vLLM configuration, chat template, thinking
policy, hardware recording, decoding settings, answer extraction, seed
uniqueness and the duplicate-replicate rate.

### T3. Constraints, graded scores, predicates, witnesses
Every ladder value; the graded-score functions at every severity; the
non-vacuity predicates including the empty and short-answer cases; `S1`,
`S2` and `S3` against hand-derived expectations; witnesses and
bidirectional non-entailment for all ten unordered pairs; four wordings
each; the wording-length caliper measured against A and its
severity-invariance.

### T4. Topics, prompts, cells, allocation, row schema
624 topics, the five-way split, disjointness, no v3 or pilot topic
present, sequestered inaccessibility; the 25-cell enumeration; both order
variants present in every block; the explicit 96-of-384 wording count per
order per cell type, refusal of a structural zero, and qualification
failure where a formula and an assertion disagree; byte-level prompt
equality between two composed cells differing in one constituent; the row
schema carrying a verdict, graded score and non-vacuity flag per present
constraint, the verifier-processing-failure flag, the accidental-occurrence
count, and the absent-constraint verdicts marked as accidental-compliance
diagnostics.

### T5. Verifiers and measurement
Determinism at 1.000 for every instrument; the split boundary suites, with
the carried A-side subset asserted byte-identical and the authored
additions present; the independent reimplementations and an assertion that
their source material is the registered prose only; parse independence;
Wilson and Newcombe calculations including the fail-class margin split; the
carry-over hash conditions; autorater parser, prompt, config-drift refusal,
serialised execution, one-shot ledger; the v4 reserved final-check set
sealed at Gate 1 with its hash recorded, refusing to open before every
autorater choice is frozen, refusing a second open, and refusing any use
for tuning; the three-value `measurement_basis` domain; the §10.5 scope sentence attached to every analysis record while
the basis is not `human_validated`; and the annotation interface's blinding
and finalisation properties.

### T6. Stage machine and gates
Every legal and illegal transition; cap selection including
zero-constraint prompts and the truncation-bound rule firing on a cell
above `0.10`; the ladder screen and the shortlist written
before Gate 2; `n*` and `m*` selection with tie-breakers; reference
admission including the Newcombe condition and the disjoint pre-screen
confirmation; the composed-headroom predicate computing no contrast;
`EXCESS_NOT_IDENTIFIED` selecting the reduced design and **not** stopping;
every terminal payload.

### T7. Cached evidence integrity
Exact cardinality `384 x cells x M`; the greedy sensitivity run at exactly
`20 x 96 x 1 = 1,920` generations at temperature 0, kept in its own
namespace and reported as a different generation population; deterministic
unique seeds; immutable raw writes; content hashes; exact-identity repair;
duplicate rejection; restoration from durable storage; refusal to form a
cell mean from a partial cell.

### T8. Verifier-hash binding
The five regression cases: unchanged verifier succeeds downstream; a
committed semantic change fails every protected stage closed; reverting
succeeds again; an irrelevant source change produces no false mismatch;
stored verdict provenance stays traceable to the verifier that produced
it.

### T9. Statistics
Block-level estimators; both algebraic forms of `Delta_R` agreeing; the
two `Rbar` aggregation rules; the bootstrap resampling 384 blocks and
carrying every cell mean; F1 to F7 simultaneous intervals; the precision
preconditions; the vacuity-forced partial identification and the
both-bounds rule; the prohibition on post-treatment variables; the
`Delta^A` identity with v3's pooled swap effect; the variance model and
the §16.3 menu rule returning the registered selection under the
registered constants; the realised variance decomposition.

### T10. Claim ladder
Vocabulary closure; one emitter per level; the L1 to L4 licensing rules and
their identification gates; the fifteen-row §28.1 outcome vocabulary;
`INDETERMINATE` emitted with both bounds when an interval spans a
threshold; `INSUFFICIENT_PRECISION` withholding equivalence and threshold
statements while still reporting a resolved direction; the
reference-heterogeneity and companion-difficulty emission blocks; refusal
of an unregistered member name; refusal of a statement missing a machine
field; refusal of a scalar quoted without its configuration; the
equivalence precondition abort; the absence of any L5 code path; the
`POSITION_CONFOUNDED` wording on every position-shifted L1.

### T11. Masking
Companion-label permutation within `(outcome, order, block)`; solo cells
unpermuted; separate pilot and confirmatory namespaces; single unmask;
mask-key access restriction; exact masked-phase rerun from the recorded
analysis-code hash; the declared inability to compute joint states while
masked.

### T12. Provenance and reporting
Clean-tree enforcement; producing-commit membership; non-empty dependency
manifests; environment digests; stage records; transition logs; content
hashes; durable restoration; the four codebook checks; the append-only
amendment register; the freeze-record completeness check refusing an
unresolved field; the result-table column set; programmatic result
generation with no manually transcribed number.

### T13. Pilot, missingness, contamination, provenance of thresholds
Gate 0's eight acceptance conditions including the redacted structural
result, the byte-mutation refusal and the durable restore; retry and
fail-closed behaviour on a short cell; the `0.01` missingness report and
the `0.05` duplicate qualification failure; the canary string and the
release manifest counts; an assertion that every registered threshold,
region, precondition and caliper carries its provenance field.

### T14. End-to-end readiness
CPU-only and synthetic first. Real-model stages only where the model and
infrastructure are available, and only in the registered order.

---

## 18. Pre-freeze empirical checks to execute

`DCI1_v4r2_prefreeze_checks.md` is your work programme. Execute each,
record the evidence, and report status. Groups A, B and C block the
freeze; Group D is recorded for the report and blocks nothing. You are not
freezing in this task in any case.

| Group | Checks | Note |
|---|---|---|
| Blocks Gate 1 | C1 boundary suites, adversarial corpora and independent reimplementations for all five instruments; C2 graded scores and non-vacuity predicates; C3 annotator availability and the paired medium-versus-high autorater comparison under serialised execution; C4 sealed-set status and whether a **new** sealed set is required; C5 verifier-hash binding at every entry point | C1 is the largest single burden |
| Blocks Gate 2 and 3 | C6 read the `solo:A:<n*>` cells from the v3 Gate 2A cache to anchor the reference caliper feasibility; C7 whether a reference severity matched to A exists in each family ladder; C7b the realised companion-difficulty gap is estimable from the v4 confirmatory solo cells; C8 the operating regime for both Qwen models; C9 witnesses for all ten pairs; C10 realised vacuity rates and the 20-word threshold; C11 accidental compliance and per-cell truncation | C6 reads v3 as data only |
| Blocks the freeze | C12 re-estimate the two correlations separately, the among-reference one from the pilot rows and the A-versus-reference one from the v3 confirmatory cache, then re-run the §16.3 allocation menu rule; C13 re-score the 576 pilot B+R rows per model under the current verifier; C14 duplicate-generation rate; C15 the deprecated-and-foreign guard; C16 an executable check that every registered contrast is formed within block; C17 topic authoring and the seeded split | C12 decides the final allocation |
| Report only | C18 confirm the `Delta^A` identity on the v3 rows; C19 record the memo hash, the quoted §G row 1 lines and both dates in the manifest; C20 restate the pilot's non-confirmatory status in every artifact citing it | |

---

## 19. Decisions you must not make

`DCI1_v4r2_unresolved_decisions.md` Part 2 lists nine open decisions. Your
job is to produce the evidence that lets the researcher close them, and to
implement the registered default so the system is runnable.

| # | Decision | Your role |
|---|---|---|
| V1 | Compute budget, allocation from the menu, number of models | Implement the menu and the selection rule; report cost and projected precision; **do not choose** |
| V2 | Whether a load-three arm is added | Not implemented; report the cost if asked |
| V3 | The reference caliper | Implement `0.10` with the Newcombe condition and the `0.15` realised-gap qualifier; report the realised admission table |
| V4 | The non-vacuity word threshold | Implement `20`; report the realised distribution; **never tune it to a rate** |
| V5 | Matched versus difficulty-spanning references | Implement matched only |
| V6 | Full or reduced design for the Qwen models | **Executed by the deterministic Gate 3 rule.** This one you do decide, mechanically |
| V7 | Author new topics or reuse a v3 set | Author 624 new topics; report the authoring record |
| V8 | Independent annotator availability | Report availability; if unavailable, complete the autorater pathway and set the basis correctly. **Never fabricate a label and never relabel author judgments as independent** |
| V9 | A second focal-like outcome constraint | Not implemented |

If executing a registered rule would require a judgement the rule does not
determine, stop and report rather than choosing.

---

## 20. Implementation sequence

1. inspect the repository, confirm the versioned-study convention, and
   identify the exact v3 and pilot boundary;
2. create the isolated v4 root and `docs/v4_traceability.md`;
3. encode the study-wide v4 manifest, fresh root seeds, fresh
   domain-separation strings, and the schemas;
4. implement constraints, verifiers, graded scores, non-vacuity
   predicates, wordings, and the witness and non-entailment suites for all
   ten pairs;
5. perform the carry-over verification as a data-level byte comparison and
   write the carry-over record;
6. author and verify the 624 topics and run the seeded split;
7. implement the cell model, prompt construction, order and wording
   allocation, and the coverage assertions;
8. implement the four model adapters and the vLLM execution layer;
9. implement provenance, artifact states, storage, transition logging,
   evidence verification, the deprecated-and-foreign guard, and the
   verifier-hash binding with its five regression tests;
10. implement qualification and the procedural pilot;
11. implement the regime pre-screen and the dense ladder screen;
12. implement Gate 1 for all five instruments, including the annotation
    interface and the autorater pathway;
13. implement Gate 2, Gate 3 with its identification status and reduced
    design, and Gate 4;
14. implement the freeze record and its completeness check, without
    executing it;
15. implement confirmatory cache generation without executing it;
16. implement cell means, the delivery-loss estimators, the seven
    families, the bootstrap, the variance model and the §16.3 menu rule,
    the precision preconditions and the partial-identification
    recomputation;
17. implement the claim ladder emitters and their executable guards;
18. implement companion-label masking and one-way unmasking;
19. implement the diagnostics: the realised variance decomposition, the
    failure taxonomy split by margin, the `S1` to `S3` recomputations, the
    graded manipulation check, the joint-state quantities computed after
    unmasking and labelled, the companion-difficulty sensitivity, and the
    mediator reporting;
20. implement terminal and identification reporting and the release
    artifacts;
21. implement the canonical tests;
22. run all CPU and synthetic tests;
23. execute the pre-freeze checks of §18 that the environment supports, in
    dependency order;
24. run only those real-model pre-confirmatory stages the environment
    legitimately supports, in the registered model order;
25. audit against every v4r2 section, every change-summary row and every
    changelog entry;
26. produce the final report;
27. **stop before the freeze and before confirmatory generation.**

---

## 21. Final report

Return one concise report containing:

- the new v4 root and the files added or changed;
- confirmation that no v2, v3 or pilot file or evidence tree was modified;
- proof that v4 has no scientific import or runtime dependency on v2, v3
  or the pilot, and the result of the isolation test;
- any generic infrastructure reused and why it is study-independent;
- the completed requirement-to-code-to-test mapping;
- the carry-over record and its hash validation, or the reason new
  measurement evidence is required;
- exact model and backend configuration per replication;
- status of every test group;
- status of every pre-freeze check C1 to C20 and C7b, with the evidence
  produced or the precise reason it is blocked;
- the realised allocation the §16.3 menu rule selects under the C12
  variance re-estimate, presented as a recommendation for V1 rather than a
  decision;
- status of every model replication reached, including any terminal or
  identification status and the full admission table;
- the Gate 1 measurement basis per model and the exact blocker if it is
  not established;
- the topic-authoring record and the split hash;
- every unresolved issue that blocks freeze, and for each: what is
  missing, why it cannot be produced autonomously, and the exact action
  that would resolve it.

Do not describe the implementation as ready while a required gate, a
provenance check, a real-model pre-confirmatory stage, a pre-freeze check,
or an unresolved scientific requirement remains incomplete.

Do not freeze the protocol. Do not perform confirmatory generation.
