# v4r3: change map, seams, and blast radius

Written before the behavioural implementation and updated as it landed. It
records what the current system does, where the new design enters, what each
change reaches, and which paths were deliberately left alone.

**Status (2026-08-21):** the v4r3 preregistration is **adopted and registered**
(`dci1/DECISIONS_V4R3.md` A0) and **not frozen**. Nothing in
`dci1/src/dci1v4/`, `dci1/evidence/dci1-v*`, `dci1/evidence/*-screen-v4` or
`dci1/docs/` was changed on account of it. The one edit outside the new package
and its evidence tree is a `testpaths` line in `dci1/pyproject.toml`.

**Amended after execution.** Three changes below were forced by evidence
produced *after* the first draft of this map, and each is recorded where it
belongs rather than folded into the original text: the allocation correction
(§16.2 / D1), the feature groups (§7.0 / C23), and the lexical-composition
correction (§7.0 / C24). A fourth entry records an event: the §10.6 verifier
binding fired during development and refused to place 4,920 rows.

---

## 1. Reconstructed starting state

| | State on 2026-08-21 |
|---|---|
| Registered protocol | v4 revision 2, drafted, **never registered, never frozen** |
| Confirmatory data | **none**, on any model, under any version |
| Furthest stage reached | `REGIME_SCREEN`, on all four models. No `gate1_measurement.json` exists anywhere, so `dispatch.frozen_verifier_hash` returns `None` for every replication and the §10.6 binding has never actually compared |
| Design evidence | four non-confirmatory screens — FORM × STEM, B-grid, Gate-2 calibration, pairwise matrix — plus two read-only re-analyses of closed evidence |
| Test baseline | `dci1` suite **705 pass, 76 s** before this work |
| Uncommitted | the segmentation-defect fix and the shortlist invariant in `dci1v4`, from the preceding session; unrelated to v4r3 |

The four screens are what make a prospective redesign possible at all: each was
run deliberately **outside** the registered lifecycle so that what they found
could change the design without any change being adopted *because a gate
failed*, which §31 prohibits. Gate 2 has never been run, and that is the option
this redesign spends.

## 2. Version boundary

v4r2 §31: *"Before study-wide freeze, any change is a revision of this
document."* v4r2 is unfrozen with no confirmatory data, so the change is a
revision — **v4r3**, not v5. The v4r1 → v4r2 transition is the exact precedent,
for the same reason and with the same disposition ("superseded in full and
retained as a design record").

## 3. Change points and seams

The established seam in this repository is a **sibling package**: `fs_screen_v4`,
`bgrid_screen_v4`, `cal_screen_v4` and `matrix_screen_v4` all import `dci1v4`'s
protocol-neutral machinery, define their own protocol, and write to their own
evidence tree. `dci1v4r3` follows it.

| Concern | Decision | Why |
|---|---|---|
| Package | new sibling `src/dci1v4r3/` | v4r2's cell-count constants are literals, its `full_slots` accepts only two exact tuples, and seven code sites assume exactly three references. Generalising them in place would change what v4r2's signed regime-screen records mean |
| Study identity | `STUDY_ID = "dci1v4r3"`, **no hyphen** | `dci1v4/engine/guards.assert_admissible_manifest` tests `startswith("dci1-v4")`. `"dci1-v4r3"` would pass it and a v4r3 artifact could reach a v4r2 estimator |
| Carried instrument sources | hashed **by path**, not re-exported | a local wrapper would hash its own bytes and let `dci1v4/words.py` drift underneath it |
| Cell count | derived from the arms; the literal 47 appears once, in an assertion | v4r2's `N_CELLS_FULL = 25` is the definition, so a design change there is a silent redefinition |
| Configuration | `outcome_first` / `outcome_second`, in the protocol text | v4r2's implementation already used this reading and its prose did not; §11.4's own argument requires it |

**Not done, deliberately:** no generalisation of `dci1v4`'s cell plan, no
version-aware branching inside `dci1v4`, no refactor of its estimators. Every
one of those would put v4r3's design pressure on code that v4r2's records were
produced by.

## 4. Blast radius, by path

### Upstream

| Path | Disposition |
|---|---|
| preregistration | **new document**: `user-notes/DCI1_preregistration_v4r3.md`, complete and self-contained, 2,523 lines |
| constants | **duplicated** into `dci1v4r3/protocol/constants.py`; v4r2's untouched |
| model registry, topic bank, seeds, hashing, prompt rendering primitives | **unchanged, imported** — protocol-neutral |
| topic split | **changed**: 34 confirmatory per area, 6 sequestered. Derived in v4r3's constants; v4r2's split is recorded in its own regime-screen records and is not edited |
| constraint families and ladders | **extended**: 8 count + 3 rate references, 2 lower-bound class-control families, 13 in all, 134 severities |
| severity grids | focal grid unchanged with a **conditional** extension; target grid unchanged |
| wordings | **unchanged in form**; the new families need their own four, authored against the same §7.5 caliper |
| Gate-1 instrument enumeration | **grows** to the whole registered pool, and is decoupled from Gate 3 |

### Core

| Path | Disposition |
|---|---|
| reference selection | **new**: `stages/selection.py`, on instructed compliance, with a closed input schema that has no field a composed outcome could occupy |
| spectrum selection | **new**: strict straddling, registered offset ±0.20 |
| class admission | **new**: production-class families, class arm only, refused in every reference and spectrum slot |
| regime selection | **new**: `stages/regime.py`, shortlist built around three targets, ranking on spanning feasibility first |
| cell planning | **new**: `design/cells.py`, four arms, 47 cells, allocation assertions carried forward |
| order allocation | **unchanged in rule**, extended to the new slots |
| seed derivation, generation, caching | **unchanged, importable** |
| scoring | **new**: `verifiers/compliance.py` with three predicate forms and a `present` flag that separates treated from chance verdicts |

### Downstream

| Path | Disposition |
|---|---|
| estimators | `Delta_R`, `Lambda`, `Delta_j`, `Xi`, the `Rbar` rules — **unchanged in definition**; v4r3 adds `delta_difficulty` and `Delta_class` |
| the difficulty fit | **new**: `analysis/spectrum.py`, family-aware OLS, A excluded, weights recorded |
| bootstrap | **new refit loop**; the block-resampling and studentised max-modulus construction are unchanged |
| multiplicity families | **F1 grows to six**; F4 loses `Xi` to F1; **F8** and **F9** are new |
| claim logic | **new**: L3d, L3e, §17.6's joint reading, three new identification statuses |
| report generation, plotting | not yet written for v4r3 |
| freeze verification | **new field list**: v4r2's 32 fields plus 21 |
| provenance hashes | v4r3 has its own canonical verifier hash; v4r2's is unmoved and asserted so |

### Legacy

| Path | Disposition |
|---|---|
| v2, v3 readers | **unchanged**; no v4r3 module imports them |
| v4r2 readers and estimators | **unchanged**; the study-identity choice keeps v4r3 artifacts out of them |
| screen packages | **unchanged**; v4r3 imports none of them |
| tests assuming five roles / 25 cells / three references | **unchanged and still passing**: they test `dci1v4`, which v4r3 does not modify |

## 5. Characterization performed before modification

- Full `dci1` suite run and recorded as a baseline: **705 pass, 76 s**.
- The registered v4 lifecycle was read end to end and its behaviour recorded:
  write-once stage records, terminal states disabling every later command, the
  §10.6 binding's eleven entry points and the one (`resume_restart`) no stage
  maps to, `admit_family`'s six conditions and their tie-breaks, `gate2_payload`
  and the §12.4 float it compares, the freeze completeness rule, the mask
  key's single open.
- The screens' estimators were read for their *defects* rather than their
  numbers, and each defect became a registered rule in v4r3 rather than being
  inherited: a fit through the point it predicts, an extrapolated residual
  reported as a measurement, a fitted nuisance object with no interval, a
  spanning arm whose rungs both landed on one side of A, a witness constructor
  used outside its envelope, a shortlist that cannot reach the rungs a spectrum
  needs.

**Defects characterized separately from their replacements**, as the method
requires: each is described in the v4r2 → v4r3 changelog with what it was, what
it produced, and what replaced it, so that "the old behaviour" and "the new
requirement" stay separately legible.

## 6. New tests, and what they would catch

`dci1/tests_v4r3/` — **126 tests**, all passing. Mapped to the failure modes a
difficulty-spectrum design makes possible:

| # | Failure | Pinned by |
|---:|---|---|
| 1, 2 | selection reads a composed outcome | `CalibrationRow` has no such field; `load_calibration_table` refuses a table carrying one, by schema, before a value is read |
| 3 | A included in the fit that predicts A | `fit_difficulty_relation` raises; a companion test demonstrates the bias direction |
| 4 | a residual reported outside support | `support_verdict` + `delta_difficulty_reading` withhold L3d/L3e and say "not a null" |
| 5 | the bootstrap does not refit | a different resample must produce a different slope **and** a different `iota_A` |
| 6 | rungs of one family treated as independent | the fit is family-aware and differs from a pooled-intercept fit |
| 7 | spectrum order variants missing | `assert_allocation` refuses |
| 8 | draws discarded or selected | every cell carries exactly `M` |
| 9 | chance compliance substituted for solo | `instructed_compliance` is explicit and an anti-productive rung is ineligible |
| 10 | a new family bypasses Gate 1 | the pool lives inside the hashed module |
| 11 | reserved topics used in development | development and reserved sets are disjoint and exhaustive |
| 12, 19 | selection or functional form changes after the fact | both are freeze fields, with the calibration-table hash |
| 13 | a new field omitted from the freeze | parametrized over all 21 new fields |
| 14 | v4r3 results enter v4r2 estimators | the prefix test, run against the real guard |
| 15 | v4r2 evidence mutated | write-target scan over every v4r3 module |
| 16 | old readers break | the v4/v3/v2 suites still pass |
| 17 | `Delta_R` / `Xi` change unintentionally | v4r3 does not modify them; F1 membership and the Šidák value are asserted |
| 18 | `delta_difficulty` reuses `Delta_R`'s thresholds | asserted absent, and a 0.40 estimate still licenses only L3d |
| 20 | prose and code disagree | registered numbers read out of the preregistration and compared |

## 7. What the allocation costs, and why

| | v4r2 | v4r3 |
|---|---:|---:|
| cells/block | 25 | 47 |
| blocks | 384 | 408 |
| generations/model | 38,400 | 76,704 |
| four models | 153,600 | **306,816** |

408 is the smallest whole-strata block count meeting every precision
precondition under both fitted variance settings once the primary family
carries six members. The binding member is `D` at φ = 0.37, which projects
0.0515 at 384 blocks and fails its 0.05 precondition. `tools/allocation_v4r3.py`
reproduces v4r2's published §16.2 row exactly under an executable assertion, so
the only thing that changed in the new row is the estimand set.

## 8. Researcher decisions this work does not take

D0 (adopt v4r3 at all), D1 (budget and whether to enlarge the topic bank rather
than shrink the sequestered set), D3 (confirm §12.4's share reading), D5
(whether `delta_difficulty` gets a magnitude threshold of its own), D6 (whether
instructed compliance or raw solo compliance is primary). §33 of the
preregistration states each with its default.


---

## 8. What execution changed, and what it cost

Four things landed after the first draft of this map. Each came from running
something rather than from reading something, and each is a change to what a
number means.

### 8.1 The allocation was not executable

`tools/allocation_v4r3.py` said 408 blocks at M = 4. `dci1v4.topics.bank` says
the released bank holds **528** questions and `dci1v4.topics.sequestered` holds
the other 96 as content hashes. 408 blocks needs 34 confirmatory topics per
area and the bank can release 32. The allocation table had been arithmetically
correct and materially impossible since it was written, and reading the topic
module rather than the table is what found it.

The repair keeps v4r2's split byte for byte and raises M to 8: 384 blocks,
144,384 generations per model, 577,536 across four. The sequestered set returns
to 96.

### 8.2 The witness suite found an unsatisfiable obligation

§7.5's non-entailment check, run over every pair of distinct families at every
declared severity, failed **1,748 times** — and not because the constructor was
weak. A count budget at *q* = 0 entails the rate budget of the same numerator,
and RF6 at *q* = 0 entails every CR6 severity. No response can satisfy the
first and fail the second.

§7.0 now groups the nine numerators into **eight feature groups**, §13.4 admits
three core references from three different *groups*, and the witness module
**refuses** to construct a witness for a same-group pair. The rules are checked
against each other rather than assumed compatible. 25,337 realisable pairs,
all discharged.

The scientific content is larger than the bookkeeping: three references from
three families could have been three families over two measurements, and
§11.7's fit would have carried three intercepts over two properties of an
answer.

### 8.3 The independent reimplementation found a segmentation defect

Written from the registered prose by a process that read no primary source, it
disagreed with the primary on `one_letter`. The cause is a composition order:
v4r2 lower-cases the response then segments; the prose segments then lower-cases
each word for the tests. Exactly one Unicode character behaves differently —
`İ` (U+0130) — and it appears **zero** times in the 285,936 rows this programme
has generated.

§10.2 adjudicates against the prose, so v4r3 composes in the registered order.
A's carry-over survives because §9.2 registers S0 as fold-then-segment in its
own words. This is what §10.2's independent implementation is *for*, and it
earned its cost on its first run.

### 8.4 The §10.6 binding fired, and was right to

A hashed module was edited while the ladder screen was generating. The stage
refused to place 4,920 rows rather than score them under a hash that had moved.

No row was mixed and nothing was lost: the raw generations were reused on a
re-run only after an identity check on row id, prompt hash and scientific seed,
and the reuse is recorded on every row as `resumed: true`. The lesson is
operational and worth stating — **the verifier layer must be settled before a
stage starts**, and the binding is what turns that from advice into a refusal.

### 8.5 What the regime screen cost

| | per model |
|---|---:|
| §12.1 completion cap | 288 generations (96 prompts × 3 caps) |
| §12.2 dense ladder, round 0 | 4,920 |
| §12.6 expansion, up to 2 rounds | ≤ 3,840 |
| **stage 3 total** | **≤ 9,048** |

Against a confirmatory 144,384. The point of §12.6 is that a design whose pool
cannot support the difficulty relation finds out here.
