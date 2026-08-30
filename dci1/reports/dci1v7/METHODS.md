# DCI-1 v7 Methods reconstruction — the directional matched-reference design

Reconstructed from the v7 implementation, the preregistration chain and the
signed records at repository HEAD `87a6c18`, for writing a paper's Methods
section. Nothing here is taken from an earlier prose summary: every fact cites
the file and line, document and section, or signed record field it was read
from. Where the executed code and the preregistered text disagree, both are
reported and the disagreement is flagged rather than resolved.

Each claim is labelled:

| Label | Meaning |
|---|---|
| **[P]** preregistered | Fixed in the registered documents and bound by the signed manifest before any outcome was seen |
| **[D]** development-time | A code default, an operational setting, or a number realised only in the non-confirmatory rehearsal lanes |
| **[H]** post-hoc | Computed after outcomes; licenses no claim |
| **[!]** discrepancy | Code and preregistration disagree, or a registered rule was not executed as written |

## Status of the evidence base — state this in the paper

The **registered** v7 study produced **no confirmatory data**. All four
replications stopped at `PREFREEZE_AUDIT_FAILURE` on 2026-08-28; no model has a
freeze, confirmatory-generation, masked-analysis or final-report record, and
zero confirmatory rows exist (`evidence/dci1v7/<model>/terminal_report.json`;
`reports/dci1v7/CLOSURE.md`). Every complete estimate of Δ_R in this repository
comes from six **development rehearsal** lanes in a structurally separate
namespace (`dci1v7-development`), which the protocol's own guards refuse to
admit as study evidence (`engine/guards.py:56-59`). The methodology below is
fully specified and has been executed end to end; the confirmatory experiment it
specifies has not been run.

Provenance of this reconstruction:

| Item | Value |
|---|---|
| Repository HEAD | `87a6c185a9bd7e0496548e5c3e0c44c63752bca3` |
| Registered manifest hash | `969a5b9f1947faddc42809a62377c6a725382e93b8f098f7d6ae98b5eb91ca14` |
| Registration commit | `ed0446ff58d0efc70b7703c162997863a9530768` |
| Protocol version | 7.0, adopted 2026-08-28 |
| Confirmatory data, registered study | none — 0 rows |
| Complete end-to-end lanes | 6, development namespace |

---

## 1. Scientific question and hypothesis discrimination

### 1.1 The question the design identifies

**[P]** The registered question has four parts (v5 §2.2 L137–153). The
matched-reference design answers the third, quoted verbatim:

> "Is the reduction of B specific to the companion A, or is it what a companion
> of A's difficulty and A's form would produce whatever its identity?"

The other three parts are: whether composing each constraint with the other
reduces its delivery relative to alone (L1); whether that reduction is
asymmetric between the two directions (L2); and whether any of it depends on
which constraint is stated first (L4b).

### 1.2 Competing explanations the (B+A) vs (B+R) contrast separates

**[P]** Nine named hypotheses (v5 §3.1 L247–269):

| Hypothesis | Claim | How the design treats it |
|---|---|---|
| `H_pair` | A damages B specifically, beyond every registered control | The hypothesis Δ_R > 0 supports; requires all controls to fail to explain it |
| `H_difficulty` | A behaves as any companion of its difficulty would | Directly contrasted: R_j matched on difficulty. Δ_R ≈ 0 is consistent with it |
| `H_A-general` | A is disruptive, but equally to every outcome | Ξ subtracts A's effect on the references themselves |
| `H_form` | Interference depends on predicate form, not identity | Δ_near against Tier-2 near-form controls — **never available in any lane** |
| `H_class` | Any second constraint of that class does it | Δ_broad *bounds* it with one Tier-3 companion; never estimates it |
| `H_family` | A property of the marker family | Three distinct feature groups required in the core set |
| `H_length` | Mediated by response length | Registered as a mediator, never conditioned on, **not identified** (v5 §22 L3125–3168, §29) |
| `H_order` | An artefact of presentation order | Both orders generated in every block; F11 order contrasts |
| `H_model` | A property of one checkpoint | Handled by construction: models are never pooled |

### 1.3 Held fixed, varied

**[P]** Across the matched cells the following are byte-identical: the base
question, the answer-length sentence, both wording indices, the prompt order,
m\*, n\*, the completion cap, decoding settings, model revision, and M
(v5 §8.4–8.5 L1003–1055). Exactly one thing varies: the identity of the
companion instruction. Two composed prompts sharing a constituent are asserted
to differ only in the other constituent's line
(`design/prompts.py:64-79`).

### 1.4 Why B versus B+A cannot identify companion-specific interference

D(B←A) is a solo-to-composed difference. It confounds the identity of A with
the generic cost of carrying a second instruction of that difficulty, and it
inherits the solo cell's ceiling and sampling noise. The matched contrast
differences two *composed* cells at equal load, and the solo baseline cancels
exactly (v5 §11.3 L1460–1462; `analysis/estimators.py:138-152`).

The magnitude of the confound is visible in the rehearsal data: for
`gemma-3n-e2b-it` with B stated second, D(B←A) = +0.211 while Δ_R = −0.085 —
the raw loss is large and the companion-specific component is small and of the
opposite sign, because the matched companions cost B more than A does.

### 1.5 Scope of identification

**[P]** The registered text is explicit that a Tier-1 control "differs from A
only in which marker word is counted and in the count, so Δ_R asks whether
*however* is special among discourse markers at matched difficulty. **It does
not ask whether A is special among companions in general**" (v5 §5 L348–393,
§7.5 L666–674). Every L3 statement carries the status
`REFERENCE_POOL_SAME_FORM` and a fixed qualifying sentence, appended
unconditionally (`constants.py:474-478`). Broadening beyond the same-form
family requires the near-form arm, which no lane had.

### 1.6 Causal language licensed

**[P]** Level L5 — "semantic identity-specificity, universal pair property,
arbitration, mechanism, class attribution, or generalisation" — is *"never
licensed by this design … permanently withheld"* (v5 §3.2 L289); there is no
emitter for it in the code (`analysis/claims.py:1200-1205`). Licensed
statements are within-model, within-configuration, cell-named contrasts only.
Mediation claims, length adjustment, pooled cross-model scalars, and any
statement about *why* an order effect occurs are forbidden (v5 §11.7
L1560–1565). And: *"failure to exclude zero is never reported as absence"*
(v5 §3.2 L322–325).

---

## 2. Notation and estimands

### 2.1 Scale, sign and unit — one convention throughout

**[P]** The primary scale is **compliance**, not failure
(`analysis/estimators.py:51`). No estimand in v7 operates on a failure rate.

- Compliance X_c ∈ {0,1} is the verifier's binary verdict on one generation.
- A *cell mean* is the mean of the M = 8 binary verdicts in one block
  (`analysis/observations.py:148-149`).
- Every estimator returns one value per block; the point estimate is the mean
  over the 384 blocks (`analysis/bootstrap.py:116-117`).

All contrasts are therefore **differences of proportions in [−1, 1]**. The
registered thresholds 0.10 and 0.25 are on that scale — if the paper reports
percentage points, multiply by 100 and say so.

```
P(c)  = compliance probability of instruction c, estimated by a block-mean
        of binary verdicts

D(c ← g) = P(c | c alone) − P(c | c with g, in the named configuration)

  positive  =>  composition REDUCED delivery of c
  negative  =>  delivery improved under composition
```

### 2.2 The definition to use — and one to correct

**[!]** The paper must **not** write `D(B←A) = (1/K) Σ_j D(B←R_j)`. That
equation asserts the treated loss equals the mean matched loss, which is the
null being tested, not a definition. The registered object is their
*difference*:

```
definitional (uncancelled) form            — estimators.py:155-162
  Δ_R = D(B ← A) − (1/K) Σ_j D(B ← R_j),        K = 3

expanding both terms:
      = [P(B|solo) − P(B|B+A)] − (1/K) Σ_j [P(B|solo) − P(B|B+R_j)]
      = −P(B|B+A) + (1/K) Σ_j P(B|B+R_j)     <- P(B|solo) cancels exactly

cancelled form, the one actually computed   — estimators.py:138-152
  Δ_R = (1/K) Σ_j P(B | B+R_j) − P(B | B+A)
```

Both forms are computed and asserted equal to a tolerance of 1e-9 on every run
(`estimators.py:165-192`; `constants.py:451`); the signed records show a worst
discrepancy of 1.1 × 10⁻¹⁶. The identity was re-derived independently from the
recorded cell levels in all six lanes and holds to rounding.

**Interpretation.** Δ_R > 0 means A costs B more than the matched companions
do; Δ_R = 0 means A is interchangeable with them for B's delivery; Δ_R < 0
means A is *gentler* on B than they are. The cancellation is a design property
worth stating in the paper: the solo cell is not on the critical path, so a
solo ceiling cannot inflate or deflate the estimate.

### 2.3 Full estimand catalogue

All on compliance; all in compliance-rate difference units.

| Symbol | Formula (per block, then averaged) | Positive means | Role | Family | Source |
|---|---|---|---|---|---|
| `D(B<-A)` | P(B\|solo) − P(B\|composed with A) | A reduces B's delivery | Primary | F1 | `estimators.py:76-83` |
| `D(A<-B)` | P(A\|solo) − P(A\|composed with B) | B reduces A's delivery | Primary | F1 | `estimators.py:76-83` |
| `D(B<-R_j)` | P(B\|solo) − P(B\|composed with R_j) | R_j reduces B's delivery | Secondary | F2 | `estimators.py:76-83` |
| `D̄(B<-R)` | (1/3) Σ_j D(B←R_j), elementwise over blocks | matched companions reduce B | Component | F2 | `estimators.py:86-92` |
| **`Δ_R`** | (1/3) Σ_j P(B\|B+R_j) − P(B\|B+A) | **A costs B more than matched companions** | **Primary** | F1 | `estimators.py:138-162` |
| `Δ_j` | D(B←A) − D(B←R_j), one per reference | A costs B more than that one reference | Diagnostic (heterogeneity) | F2 | `estimators.py:195-201` |
| `Λ` | D(B←A) − D(A←B) | B loses more under A than A under B | Primary | F1 | `estimators.py:95-100` |
| `Ξ` | Δ_R − [D(R̄←A) − D(R̄←R̄′)] | the excess is specific to outcome B | Primary, direction-only gate | F1 | `estimators.py:238-244` |
| `Δ^A` | D(A←B) − (1/3) Σ_j D(A←R_j) | B costs A more than matched companions | Demoted diagnostic | F3 | `estimators.py:204-211` |
| `D(R̄<-g)` | (1/3) Σ_j D(R_j←g), g outside the set | g reduces the references' delivery | Secondary | F4 | `estimators.py:214-223` |
| `D(R̄<-R̄′)` | mean over the 6 ordered pairs (j≠k) of D(R_j←R_k) | references cost each other | Secondary | F4 | `estimators.py:226-235` |
| `Δ_near` | (1/3) Σ_k P(B\|B+N_k) − P(B\|B+A) | A costs B more than near-form controls | Secondary — **never available** | F9 | `estimators.py:247-268` |
| `Δ_broad` | P(B\|B+CL) − P(B\|B+A) | A costs B more than the class control | Secondary, bounding only | F10 | `estimators.py:271-287` |
| `Ord_A`, `Ord_B` | composed(outcome second) − composed(outcome first) | the loss is larger with the outcome stated first | Primary tier | F11 | `estimators.py:330-364` |
| `Ord_Λ`, `Ord_R̄`, `Ord_CL` | Ord_B − Ord_A; mean over references; class control | as above | Primary tier (Ord_Λ linearly dependent, registered anyway) | F11 | `estimators.py:367-402` |
| `δ_difficulty` | D(B←A) − [ᾱ + β·ι_A], OLS with family intercepts on 9 non-A points | A's loss exceeds the difficulty relation's prediction | Primary — **never identified** | F1 | `analysis/spectrum.py:168-181, 343-354` |
| `α_k`, `β`, `γ_tier` | secondary fit Y = α_f + β·d + γ·1[Tier 2] on 12 points | tier offset in the difficulty relation | Secondary — **never identified** | F8 | `spectrum.py:374-390, 596-611` |
| `vac(·)` | vacuity difference, composed − solo | composition increased vacuous passes | Gate for §17.4 | F6 | `estimators.py:460-467` |

F5 duplicates the F1 estimators on two alternative scales
(`non_vacuous_compliance`, `graded_threshold` at 0.99) as robustness variants
(`run/analysis_run.py:201-228`). There are eleven declared multiplicity
families, F1–F11 (v5 §15 L2545–2557).

---

## 3. The instructions A, B and R_j

### 3.1 A — the companion under test

**[P]** A is an exact marker count on the word *however*, severity n ∈ {1,…,8}
(`verifiers/constraints.py:79-80`). Its structural record: operator `==`,
statistic `marker_occurrence`, count, no denominator, lexical, no length
dependence, production class, feature group `marker_however`, discourse role
`contrastive` (`protocol/taxonomy.py:99-106`). Four registered wordings,
carried byte-identically from v4r2 (`protocol/wordings.py:57-59`). At n = 6:

```
1. Use the word however exactly 6 times.
2. Your answer must contain however exactly 6 times.
3. Include however exactly 6 times in your answer.
4. The word however must appear exactly 6 times.
```

### 3.2 B — the focal instruction whose delivery is measured

**[P]** B is a maximum word-length budget, severity m ∈ {7,…,14} with a
conditional extension to {15, 16} (`constraints.py:85-97`). Templates are
re-derived from two v4 renderings and refused if they differ by more than the
numeral (`wordings.py:62-83`). At m = 10:

```
1. Every word in the answer must have at most 10 letters.
2. Use only words of 10 letters or fewer.
3. Do not use any word longer than 10 letters.
4. No word in your answer may exceed 10 letters.
```

**Joint satisfiability is built into the grid.** The floor m ≥ 7 exists because
*however* has seven letters: below it, A and B are jointly unsatisfiable
(`constraints.py:82-84`). Satisfiability is not assumed — it is verified twice
for every admitted pair: a formal joint witness plus a non-entailment witness
(`verifiers/witnesses.py:278-333, 407-431`), and a *realistic* witness that must
also fit the 60–120-word answer band (`verifiers/realistic_witness.py:8-15,
45-49`). This is validity component V_sat; a family failing it is never admitted
(`stages/validity.py:185-210`).

### 3.3 Parameters

| Symbol | Meaning |
|---|---|
| `n` | A's severity — the required number of occurrences of *however*. Grid 1–8. Chosen per model at Gate 2 as n\*. |
| `m` | B's severity — the maximum letters per word. Grid 7–14 (+15, 16 by escalation). Chosen per model at Gate 2 as m\*, and frozen there. |
| `q` | A reference family's severity, on that family's own declared ladder (round 0) and frozen reserve. E.g. MK1 ladder 1–8, reserve 1–12 (`constraints.py:840-865`). |

### 3.4 The reference library and its taxonomy

**[P]** 40 families, 37 selectable (PS1–PS3 are probe-only stand-ins).

- **Tier 1** — the eight marker families MK1–MK8 (thus, hence, though, whereas,
  indeed, namely, instead, overall), which must match A on operator, statistic
  type, count-or-rate, denominator, lexical/structural, length dependence and
  length direction (`taxonomy.py:107-113`). They carry *A's own four templates
  with the marker word substituted*, generated at import rather than retyped
  (`wordings.py:227-253`) — so at q = 3, MK1 reads "Use the word thus exactly 3
  times."
- **Tier 2** (near-form) — XC1 semicolon, XC2 comma, XC3 sentence: same
  operator, different statistic.
- **Tier 3** (broad class) — 26 families including RF12 "Your answer may use at
  most q sentences."

Marker eligibility rules: *however* excluded, at most 7 letters, natural
occurrence probability ≤ 0.15 (v5 §7.6 L676–738).

---

## 4. Matched-reference construction

This is the methodological core. Everything here is **[P]** unless marked
otherwise.

### 4.1 Candidate pool

The §12.7 calibration population: *all* Tier-1 and Tier-2 rungs
unconditionally, plus at most 24 Tier-3 rungs ordered by ascending pre-screen
|ι − ι_A| (`constants.py:188-193`; `stages/regime.py:151-182`). No candidate is
discarded on a pre-screen point estimate. Each candidate is a (family,
severity) rung; the population is 674 instruments over 40 families.

### 4.2 "Same form", operationally

Not a judgement — a seven-field identity test against A's structural record
(Tier 1), enforced by `V_struct` against a slot-admissibility table: core
admits Tier 1 or 2, near-form admits Tier 2 only, broad class admits Tier 3
only, spectrum inherits its core family's tier (`taxonomy.py:126-130, 216-249`;
`validity.py:282-304`). The admitted core set must additionally contain at least
two Tier-1 members and span three distinct feature groups and at least two
discourse roles.

### 4.3 The difficulty metric

```
κ_c = chance compliance: P(c passes | unconstrained cell, same topics, same M)

ι_c = (P_solo(c) − κ_c) / (1 − κ_c)     instructed compliance
                                        — calibration_table.py:77-99

undefined and refused when κ_c ≥ 0.99 (CHANCE_DEGENERACY_MAX)
```

ι — chance-corrected, *not* raw solo compliance — is the registered matching
coordinate; raw solo compliance is the registered *secondary* coordinate under
§34 D14, reported for agreement only and never used to select (v5 §13.2 L2016).

#### [!] Discrepancy — must be disclosed in the Methods section

On the executed code the calibration table's chance column is **0.0 for every
candidate**, so each candidate's ι collapses to its raw solo compliance. The
code says so in terms: the column reproduces "the measured chance over every
grid row where the candidate is absent *when some grid row states it*, and 0.0
otherwise", which for a non-outcome candidate is always the second branch — "a
defect against §13.2 … deliberately NOT corrected here"
(`run/gates_run.py:673-691`).

Verified directly against the signed Gate-3B records: for `gemma-3n-e2b-it`,
MK2:1 has solo = 0.5911 and recorded ι = 0.5911; MK1:4 has solo = 0.5924 and
ι = 0.5924 — equal to all recorded digits.

**ι_A, however, is genuinely chance-corrected**, taking its κ from a different
code path (`gates_run.py:546-548`): ι_A = 0.5891 against solo = 0.5938
(κ_A = 0.011). So the caliper compares a chance-corrected target against
uncorrected candidates. Measured size of the induced target shift, by model:

| Model | solo(A) | ι_A | shift |
|---|---:|---:|---:|
| `qwen3-4b` | 0.6875 | 0.6855 | 0.002 |
| `gemma-3n-e2b-it` | 0.5938 | 0.5891 | 0.005 |
| `gemma-3n-e4b-it` | 0.7318 | 0.7252 | 0.007 |
| `qwen3-4b-instruct-2507` | 0.5664 | 0.5397 | 0.027 |

All are well inside the 0.10 caliper, but the paper should say the matching was
executed *on raw solo compliance for candidates*, not claim chance-corrected
matching on both sides.

### 4.4 The eight validity components

V(R) = V_spec ∧ V_sat ∧ V_head ∧ V_chance ∧ V_struct ∧ V_inter ∧ V_stab ∧
V_diff, evaluated in that lexicographic order; the order fixes only which
failure is *recorded*, and an unevaluated component is never a pass
(`validity.py:11-19, 116-143`). No composite score exists.

| Component | Rule | Thresholds | Source |
|---|---|---|---|
| `V_spec` | Complete structural record; wording length within tolerance of A's; parse independence | ±20% word count | `validity.py:167-183` |
| `V_sat` | Formal joint-satisfiability and non-entailment witnesses, plus a realistic witness against B at m\* inside the stem band | — | `validity.py:185-210` |
| `V_head` | 95% Wilson interval for raw solo compliance wholly inside the headroom band; instruction lift; solo vacuity ceiling | (0.10, 0.90); lift ≥ 0.20; vacuity ≤ 0.10 | `validity.py:213-251` |
| `V_chance` | Chance rate and its Wilson upper bound below ceilings | κ ≤ 0.75; upper ≤ 0.85 | `validity.py:254-279` |
| `V_struct` | The family's declared tier admits the slot | core {1,2}, near-form {2}, class {3} | `validity.py:282-304` |
| `V_inter` | Projected composed compliance p̂ = κ(R\|B) + ι(1−κ(R\|B)) inside a band; displacement bounded. A missing κ(R\|B) is a failure, never "unevaluated" | p̂ ∈ (0.10, 0.90); \|Σ\| ≤ 0.25 | `validity.py:307-329` |
| `V_stab` | Independently admissible on Calibration-A *and* Calibration-B; 95% percentile-bootstrap interval for the split difference of ι and of raw solo compliance wholly inside a bound; 10,000 resamples over **topics** | ±0.20 | `validity.py:332-345`; `stability.py:173-201` |
| **`V_diff`** | **The caliper.** (1) \|ι_R − ι_A\| within caliper; (2) 95% Newcombe interval for the paired solo-rate difference intersects a region; (3) raw-coordinate secondary check | (1) ≤ 0.10 on ι; (2) ±0.05; (3) ≤ 0.15 | `validity.py:348-390` |

Spectrum rungs run every component *except* V_diff — by design, since their
purpose is to sit ±0.20 away from ι_A (`selection.py:62-63`;
`validity.py:410-415`).

### 4.5 Selection algorithm

```
# stages/selection.py:121-593.  K = N_CORE_REFERENCES = 3.

pool = pooled 192-topic calibration rows     # Calibration-A (96) + B (96), M_CAL = 4

for each Tier-1/Tier-2 family f:
    for each measured rung of f: evaluate all 8 components of V(R), slot = core
    if no rung passes: f not admitted            # every rung's failure reason retained
    else: best_rung(f) = argmin ( round(|ι_R − ι_A|, 12), restrictiveness_key )

ranked = sort admitted families by
         ( |ι − ι_A|,  structural_tier,  registered feature-group order,
           restrictiveness_key,  family_id )     # fully deterministic tie-breaking

chosen = [];  groups = {}
while ranked and len(chosen) < 3:
    v = pop(ranked)
    if v.feature_group in groups:                     continue   # group exclusivity
    if v.tier != 1 and lookahead cannot still reach 2 Tier-1:  continue
    triple = select_spectrum_triple(v)          # needs rungs strictly below AND above ι_A
    if triple is None:                                continue
    chosen += v;  groups += v.feature_group

if distinct discourse roles in chosen < 2:
    replace the LOWEST-ranked member with the highest-ranked qualifying family
    of a different role (new group, triple exists, Tier-1 count preserved)

identified = (len(chosen) == 3) and assert_core_set_structure(chosen)
if not identified:
    re-run with require_spectrum = False
    if that identifies: core stands, spectrum arm dropped,
                        status += DIFFICULTY_SUPPORT_NOT_IDENTIFIED
    else:               status += EXCESS_NOT_IDENTIFIED    # irreversible; core arm lost
status += REFERENCE_POOL_SAME_FORM                         # always, unconditionally

# the other arms
spectrum:   per core family, targets ι_A ± 0.20, same family, severity != core,
            strictly one below and one above, nearest each target
near-form:  Tier-2 families EXCLUDING the core families, 3 distinct groups, full V(R)
            fewer than 3  ->  NEAR_FORM_ARM_NOT_AVAILABLE
class:      Tier-3 AND constraint_class == budget, min |ι − ι_A|, ties by family id
            none -> CLASS_ARM_NOT_AVAILABLE;  distance > 0.15 -> CLASS_ARM_NOT_MATCHED
            always records COMPANION_CLASS_NOT_MATCHED
backups:    the first 2 spare qualified families, in registered order — NEVER substituted
```

### 4.6 Properties of the procedure

| Property | Value |
|---|---|
| K | Exactly 3 core references, plus 2 frozen backups (`constants.py:333`; `support.py:79-89`). Δ_R raises if the count is not 3 (`estimators.py:143-147`) |
| Model-specific | **Yes.** Every calibration row carries `model_key` and the loader refuses a foreign one; κ(R\|B) refuses cross-model transfer by name (`calibration_table.py:264-267`; `interaction.py:114-119`) |
| Position-specific | **No.** One slot map serves both configurations; the same three references are used for `outcome_first` and `outcome_second` (`design/cells.py:172-184`) |
| Selection before outcomes | **Yes** — the §6 firewall. Gate 3B precedes Gate 4 and confirmatory generation; selection functions take a closed schema with no composed field; the calibration-table schema refuses composed columns before any value is read (`calibration_table.py:56-68, 103-148`). The manifest walker refuses model-adaptive values (`n_star`, `m_star`, `admitted_references`, …) anywhere in the registration payload (`manifest.py:86-94, 940-960`) |
| Backups | **Never substitute.** `BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4 = False`, and the guarantee is that no substitution *function* exists (`constants.py:338-341`; `selection.py:596-622`; `gates_run.py:2376-2398`) |
| Insufficient references | Fewer than 3 core references, or fewer than 5 families passing full V(R), yields `REFERENCE_SUPPORT_NOT_IDENTIFIED` / `EXCESS_NOT_IDENTIFIED`: the core and spectrum arms are dropped, L3a–L3e withheld, irreversibly, and the replication continues on its surviving estimands (v5 §13.15 L2458–2478; `identification.py:1-11`) |

### 4.7 Why this makes R_j a fair comparison — and what it does not control

The matching equalises, between A and each R_j: predicate form (seven identity
fields), stand-alone difficulty (caliper on ι, plus a Newcombe interval on the
paired rate difference and a raw-coordinate check), instruction load (both cells
carry exactly two instructions), headroom (both inside the Wilson band with a
minimum instruction lift), chance behaviour (κ ceilings), stability across two
independent topic splits, and the projected composed operating point (V_inter,
so a reference is not admitted if it would be pinned at a boundary when
composed). Wording length is matched to within 20% of A's, and the marker
families literally reuse A's four sentence templates, so surface phrasing is not
a confound.

**Residual confounds the design does not control**, which the paper must name:

- **Form itself.** All three references are exact marker counts. Whether the
  null result is a property of *however* or of the exact-count form is exactly
  what the near-form arm tests, and it was unavailable in every lane.
- **Lexical properties of the marker** — frequency, register, discourse
  function. Tier 1 deliberately does *not* require identity on
  `production_burden` or `natural_frequency_band` (`taxonomy.py:107-113`), so a
  reference may be a rarer or commoner word at the same measured difficulty.
- **Response length**, registered as a mediator, never conditioned on, and not
  identified (v5 §22, §29).
- **Difficulty measured on the outcome-free cell.** Matching is on solo
  behaviour; two companions equally difficult alone may interact differently
  with B. V_inter bounds this by projection but does not eliminate it.
- **The chance-basis asymmetry** documented in §4.3.
- **Position of the companion** is balanced, not matched — order is a factor,
  so companion-specific and position-specific effects are estimated separately
  rather than adjusted for one another.

---

## 5. Experimental conditions and prompt construction

### 5.1 Notation warning for the paper

**"B+A" is an ordered presentation, not an unordered pair.** In the code,
`pair:B+A` and `pair:A+B` are distinct cells, both generated in every block, and
`CellType.slots` is documented as "(first, second) in PROMPT order"
(`design/cells.py:157, 166, 213-215`).

Separately, a *configuration* is the position of the **outcome** constraint, not
the slot order (`constants.py:140-145`) — so one generation serves two
configurations at once, one per constituent.

### 5.2 Prompt template

**[P]** Four parts, no system message, single user turn, zero-shot
(`constants.py:158-162`; `design/prompts.py:28-38`):

```
{question}
(blank line)
Answer in 60 to 120 words.        <- byte-identical in every cell, asserted once
(blank line)
1. {constraint stated first}
2. {constraint stated second}
(blank line)
Answer:
```

Load 0 omits the numbered list; load 1 has one line; load > 2 is refused
(`prompts.py:37-38`). Nothing in the prompt marks which instruction is "the
outcome" — that is an analysis-side label.

Rendered examples, topic `art-and-design-05`, block 5, A at n = 6, B at m = 10,
R1 = MK1 at q = 3:

```
--- solo:B ---
How does a designer work with a client who cannot describe what they want?

Answer in 60 to 120 words.

1. Use only words of 10 letters or fewer.

Answer:

--- pair:B+A   (B is the outcome, stated first -> configuration = outcome_first) ---
How does a designer work with a client who cannot describe what they want?

Answer in 60 to 120 words.

1. Do not use any word longer than 10 letters.
2. Your answer must contain however exactly 6 times.

Answer:

--- pair:R1+B  (B is the outcome, stated second -> configuration = outcome_second) ---
How does a designer work with a client who cannot describe what they want?

Answer in 60 to 120 words.

1. Include thus exactly 3 times in your answer.
2. Use only words of 10 letters or fewer.

Answer:
```

### 5.3 Conditions required for the primary matched-reference analysis

The full five-arm design is 56 cells per block; the rehearsal lanes admitted 26
(base+core) or 29 (base+core+class).

| Cell | Prompt | Measured on | Serves | Required for |
|---|---|---|---|---|
| `unconstrained` | Load 0 — question + stem only | every instruction, absent | both | chance κ (§25); κ(c\|B) source |
| `solo:B` | B alone | B | both | D(B←·); ι_B; not on Δ_R's critical path |
| `solo:A` | A alone | A | both | D(A←·); ι_A, the matching target |
| `pair:B+A` | B first, A second | B *and* A | B: first · A: second | **Δ_R** (B first); D(A←B) (A second) |
| `pair:A+B` | A first, B second | A *and* B | A: first · B: second | **Δ_R** (B second); D(A←B) (A first) |
| `pair:B+R_j` | B first, R_j second | B and R_j | B: first | **Δ_R** reference term, j = 1,2,3 |
| `pair:R_j+B` | R_j first, B second | R_j and B | B: second | **Δ_R** reference term, j = 1,2,3 |
| `solo:R_j` | R_j alone | R_j | both | D(R_j←·) for Ξ; ι validation |
| `pair:A+R_j` / `R_j+A` | both orders | A and R_j | both | D(R̄←A) for Ξ; Δ^A |
| `pair:R_j+R_k` | all 6 ordered pairs | both constituents | both | D(R̄←R̄′) for Ξ |
| `pair:B+CL` / `CL+B` | both orders | B and CL | both | Δ_broad (class arm only) |
| `pair:B+N_k` / `N_k+B` | both orders | B and N_k | both | Δ_near (near-form arm — never ran) |

Mapping directions to cells (`observations.py:47-48, 132-142`): D(B←A) in
`outcome_first` reads `pair:B+A`; in `outcome_second` it reads `pair:A+B`.
D(A←B) in `outcome_first` reads `pair:A+B`. So within one configuration, the two
directions are read from *different prompts* — worth stating explicitly in the
paper.

### 5.4 Order and wording: balanced by construction, not randomised

**[P]** Order is a cell-level factor: both variants of every pair appear in
every block. Wording is a block-level factor assigned deterministically
(`design/cells.py:271-287`):

```
first  = block_index mod 4
second = (block_index + floor(block_index / 4)) mod 4

solo cells use `first`; composed cells give `first` to the constituent earlier
in the registered slot order, applied identically to BOTH order variants.
```

Because the order variant does not depend on the block index, **wording and
order are orthogonal by construction**, each (cell, slot, wording) combination
occurs 96 times, and structural zeros or skews are refused
(`cells.py:278-279, 361-389`).

---

## 6. Base tasks, blocking and sampling

### 6.1 Topic bank and splits

**[P]** 720 questions: 12 subject areas × 60 (`constants.py:38-79`). Authored
in-repo under rules forbidding reuse of public dataset or examination text
(`constants.py:81-86`); 624 carried from v4's released split, 96 newly authored
for Calibration-B on 2026-08-22, before any v5 measurement
(`topics/calibration_b.py:41-74`). Splits are a seeded per-area shuffle-and-cut
with a deliberately reused seed (202608192) (`src/dci1v4/topics/split.py:58-74`;
`seeds.py:45-48`). Disjointness is checked over both ids and normalised question
text (`topics/bank.py:171-230`).

| Split | Per area | Total | Used for |
|---|---:|---:|---|
| Pre-screen | 2 | 24 | Cap selection, ladder screen (1 draw), §12.6 certificate |
| Calibration-A | 8 | 96 | Difficulty table, split-A admissibility |
| Calibration-B | 8 | 96 | Split-B admissibility, V_stab equivalence |
| Composed validation | 2 | 24 | Gate 4 composed contrast |
| **Confirmatory** | 32 | **384** | **The 384 blocks of the primary analysis** |
| Sequestered | 8 | 96 | Never used |

### 6.2 Blocking, draws, and the two units

**[P]** **A block is one confirmatory topic**, so there are 384 blocks
(`run/confirmatory_run.py:69-77`; `constants.py:147`). Every cell of the design
is generated at that topic, in both orders, at **M = 8** draws
(`constants.py:148`). All M draws enter the cell mean; none is selected or
discarded (`confirmatory_run.py:186-189, 247-249`). Calibration stages use
M_CAL = 4.

- **Experimental unit** — the **cell mean over the M draws of one block**.
  `build_observations` requires exactly the M registered draw indices, refuses a
  partial cell and imputes nothing; no draw-level index is reachable from the
  observation table (`observations.py:82-108, 173-178`).
- **Resampling unit** — the **block**: "the assignment, pairing, clustering and
  generalisation unit … the only index" (`observations.py:3-7`). Every
  registered contrast is formed *inside* one block, and `assert_within_block`
  checks each block carries exactly the cells the admitted arms require
  (`observations.py:297-337`).

Design totals: 4 models × 384 blocks × 8 draws × 56 cells = 688,128 generations
for the full five-arm design; the realised rehearsal budgets were
26 cells × 384 × 8 = **79,872** rows (base+core) and 29 × 384 × 8 = **89,088**
rows (base+core+class) (`prefreeze_run.py:497-500`).

### 6.3 Dependence structure

All 56 cells of a block share one question, in both configurations, at all 8
draws. Blocks congruent mod 4 share the solo wording index. **Draws are not
paired across cells**: the per-request seed is a function of the prompt hash,
which differs between cells, so draw *k* of `solo:B` and draw *k* of `pair:B+A`
share no random state (`seeds.py:58-65`). Pairing is at the block level only —
which is exactly the level the bootstrap resamples.

### 6.4 Exclusion and retry rules

**[P]** **There are none.** No generation is discarded for what it says, no
draw is selected, and there is no retry path. Truncated and empty responses are
scored, not dropped (§8). Completeness is verified over the union of batches:
every (block, cell, draw) identity exactly once, with missing, duplicate and
unexpected rows all refusals (`confirmatory_run.py:166-190`).

---

## 7. Models and generation procedure

### 7.1 The four registered models

All defined once, in `src/dci1v4/models/registry.py`.

| Key | Hugging Face id | Pinned revision | Thinking mode | Model-specific |
|---|---|---|---|---|
| `gemma-3n-e2b-it` | `google/gemma-3n-E2B-it` | `5e092ebca197cdcd8d8b195040accf22693501bc` | unavailable | — |
| `gemma-3n-e4b-it` | `google/gemma-3n-E4B-it` | `c1221e9c62e34a43ab7ffacd1be0ea71f126ef10` | unavailable | `gpu_mem_util 0.95` |
| `qwen3-4b` | `Qwen/Qwen3-4B` | `1cfa9a7208912126459214e8b04321603b3df60c` | disabled — `enable_thinking=False` | switch verified live |
| `qwen3-4b-instruct-2507` | `Qwen/Qwen3-4B-Instruct-2507` | `cdbee75f17c01a7cc42f958dc650907174af0554` | unavailable | — |

Defaults shared by all four (`registry.py:41-44`): dtype `bfloat16`,
`tensor_parallel_size = 1`, `max_model_len = 4096`,
`gpu_memory_utilization = 0.85`. The chat template is the one in the pinned
snapshot, applied by the engine's own tokenizer with `add_generation_prompt=True`
(`vllm_backend/engine.py:222-227`). For Qwen3-4B the hybrid template switch is
disabled through its own kwarg and *verified* — the backend renders
declared-versus-negated and refuses to run if the kwarg is inert
(`engine.py:230-280`).

### 7.2 Operating points selected per model

**[D]** Read from the signed records. The registered study and the development
rehearsals selected **identical** operating points for every model — a
reproducibility fact worth reporting:

| Model | completion cap | m\* | n\* | arms admitted (rehearsal) |
|---|---:|---:|---:|---|
| `gemma-3n-e2b-it` | 512 | 10 | 8 | base + core + class |
| `gemma-3n-e4b-it` | 512 | 9 | 6 | base + core + class |
| `qwen3-4b` | 512 | 12 | 2 | base + core |
| `qwen3-4b-instruct-2507` | 512 | 11 | 5 | base + core |

### 7.3 Message structure and decoding

**[P]** **No system prompt is ever sent.** A system turn is appended only if
`system_message` is non-empty; it defaults to `""` and no v7 module sets it
(`engine.py:222-225`; `contract.py:66`). Every request is a single user turn.

| Parameter | Value | Source |
|---|---|---|
| temperature | 0.7 | `backend.py:170-171` |
| top_p | 0.9 | `backend.py:170-171` |
| top_k | 50 | `backend.py:170-171` |
| max_new_tokens | the selected cap ∈ {512, 768, 1024} — 512 for all four models | `constants.py:165`; `regime_run.py:140-150` |
| penalties (presence/frequency/repetition) | none passed | `engine.py:65-81` |
| stop sequences | none | `plan.py:117`; `engine.py:9-12` |
| generations per prompt | M separate requests, not n>1 sampling | `execute.py:216-241`; `engine.py:289-296` |
| per-request seed | `domain_int("dci1v7:gen:v1", 202608240, stage, model_id, prompt_hash, draw_index)` | `seeds.py:58-65` |
| batching | 64 requests per generate call | `execute.py:463` |
| engine | `enforce_eager`, quantization none, `trust_remote_code=False` | `backend.py:188-197` |

**Fixed across models:** temperature, top-p, top-k, M, prompt template, seed
scheme, dtype, TP=1, no system prompt, no stop strings, completion cap (512 was
selected independently for each). **Differing:** n\*, m\*, the admitted
references and arms, and gemma-3n-e4b-it's memory utilisation.

**Reproducibility caveat.** No docstring in the repository claims bitwise
reproducibility of generation. What is guaranteed is that the per-request seed
is a pure function of scientific identity and never of batch position, "so a
seed derived from position would make results depend on scheduler order"
(`contract.py:58-62`). The engine-level seed is a separate constant (20260819)
fixing engine state only (`backend.py:162-166`). State this honestly rather than
claiming determinism.

---

## 8. Compliance measurement and the verifier

### 8.1 Word segmentation — the primitive everything rests on

**[P]** No regular expression. A word is a **maximal run of Unicode-alphabetic
characters**, accumulated by a loop over `str.isalpha()`; every non-alphabetic
character is a boundary (`src/dci1v4/verifiers/words.py:3-27`). The prose
specification states the class as Unicode general category L, and Gate 1 proves
`str.isalpha()` ≡ category-L over all 1,114,112 codepoints
(`stages/gate1.py:145-163`).

Consequences, all verified by probe and all needing a sentence in the paper:

- Digits, underscores and symbols split: `abc123def` → two words; `**bold**` →
  one.
- **Hyphenated forms split**: `state-of-the-art` → four words. **Apostrophes
  split**: `don't` → `don`, `t`.
- URLs split into alphabetic pieces: `https://example.com/thus` → four words —
  and that includes a countable `thus`.
- Soft hyphen, zero-width space and non-breaking space are boundaries.
- Precomposed `café` is one 4-letter word; **NFD-decomposed `naïve` splits**
  because the combining mark is not alphabetic.
- CJK and fullwidth text count as alphabetic runs.

### 8.2 The three predicate forms in use

```
B (focal, budget)      statistic = max(len(run) for run in alpha_runs(text)), 0 if none
                       pass <=> statistic <= m       # casing irrelevant; no tolerance
                       graded = 1 − (#words longer than m)/(#words), 0.0 if no words

A (exact count)        statistic = count of alpha_runs(text.lower()) == "however"
                       pass <=> statistic == n       # fold-then-segment (S0)

MK1–MK8 (exact count)  statistic = count of w in [run.lower() for run in alpha_runs(text)]
                       equal to the marker
                       pass <=> statistic == q       # segment-then-fold
```

**Whole-word equality after folding**, so substrings never count (`thusly` → 0),
case is irrelevant, and adjacent punctuation is irrelevant
(`hence hence, hence; hence.` → 4). But hyphens and zero-width characters
*create* occurrences: `though-provoking though` → 2
(`verifiers/boundary_v5.py`).

**Two counting conventions — registered, and quantified.** A folds first then
segments; the marker families segment first then fold
(`statistics.py:13-19`; `words.py:14-32`). The code enumerates the whole Unicode
range to prove the two conventions differ on **U+0130 (İ) alone**, "which occurs
zero times in the 285,936 rows this programme has generated"
(`words.py:31-32, 51-75`). Report it as a stated design fact, not a bug.

Other families in the library use `count_budget` (S ≤ q), `rate_budget`
(100·S/W ≤ q, denominator always *words*), `count_lower_bound` (S ≥ q) and
`exact_count` over semicolons, commas or sentences. Sentence segmentation counts
maximal runs of `.` `!` `?`, adding one if non-whitespace follows the last run;
the docstring registers the consequence verbatim: *"a decimal point and an
abbreviation's full stop both terminate a sentence under this rule: a registered
over-count, stated rather than discovered"* (`words.py:78-105`).

### 8.3 Scoring pipeline and invalid outputs

**[P]** Evaluation is **binary**; a graded score in [0,1] is recorded alongside
but is never the primary outcome. **Every registered instance is scored on every
row**, not only the stated ones — a verdict on an unstated constraint is a
chance observation with `present=False`, and a guard refuses chance observations
inside any treated estimand (`execute.py:536-540`; `compliance.py:260-271`).
That is where κ(R|B) comes from at zero extra generation cost.

| Case | Treatment | Source |
|---|---|---|
| Empty answer | Scored normally. B and budgets **pass vacuously** (max word length 0 ≤ m); exact counts and rate forms fail. `empty` recorded, never a filter | `compliance.py:129-135, 244` |
| Truncated at the cap | Scored normally; forces `non_vacuous=False`. Truncation share feeds cap selection only | `compliance.py:184-186` |
| `finish_reason` | Recorded on the row; **no predicate reads it** | `execute.py:539, 555` |
| Refusals | No detector and no special scoring; scored as any other text | `constants.py:830-832` |
| Verifier exception | Fails closed: `passed=False, graded=0.0, processing_failure=True` | `compliance.py:198-203` |
| Vacuous pass | Stays a pass; §9.3 floor marks a budget pass under 20 words vacuous, and §17.4 recomputes claims under a forced non-vacuous scale | `compliance.py:32, 57, 193` |

### 8.4 Verifier validation — Gate 1's ten conditions

**[P]** All-or-terminal (`gate1.py:376-518`): determinism across three OS
processes must be exactly 1.000; an **independent reimplementation written from
prose alone** (stdlib only, a deliberately different route —
`unicodedata.category`, `groupby`, `re.split`) must agree on all 22 statistics
for every response and on pass/graded/vacuity for a declared sample of 1,200
(`verifiers/independent.py`); a frozen boundary suite of 177 cases over 674
instruments must agree exactly and cover 34 required phenomena; an adversarial
corpus must cover 18 named phenomena (zero-width, soft hyphen, combining marks,
İ case-folding, fullwidth, markdown …) with realised frequencies reported beside
them; mutation validation must detect six seeded defect kinds including a
segmentation-order drift; joint-satisfiability witnesses must pass; and verdicts
must be invariant across all four wordings of each instrument (20 responses × 674
instruments × 4 wordings).

### 8.5 [!] No human evaluation exists — and this bounds the paper's central term

There is no human labelling anywhere in v7. The measurement basis
`human_validated` is explicitly *refused* (`constants.py:461-463`;
`gate1.py:385-394`); the strongest basis Gate 1 can record is
`deterministic_measurement_validated`. A verifier-audit module exists for
building operationalisation cards, but it carries its own standing note: *"it
shows the verdict, so it measures nothing about human-verifier agreement and its
output must never be reported as an agreement rate"*
(`stages/verifier_audit.py:38-41`).

Accordingly, a registered scope sentence attaches permanently to every analysis
record, every claim at every rung, and the final report:

> "the outcomes are verifier-defined and support no claim about compliance as an
> independent human would judge it" (`constants.py:464-465`)

The paper should carry that sentence, or its equivalent, in the Methods and
again beside the results.

---

## 9. Calibration and parameter selection

### 9.1 Choosing m\* and n\*

**[P]** Both severities are chosen per model from measured solo-compliance
curves, **on raw solo compliance, not on ι** — the code says so in terms
(`stages/regime.py:192-194`):

```
eligible(q)  <=>  measured solo compliance at q lies inside the band
selected     =   argmin over eligible q of ( |curve[q] − aim|,  q )   # ties to SMALLER q

A:  band (0.50, 0.85)   aim 0.70   grid 1–8
B:  band (0.60, 0.95)   aim 0.80   grid 7–14 (+15,16 by escalation)
```

The selection must be *bracketed*: both grid neighbours measured at calibration
precision, else the status `OPERATING_POINT_AT_GRID_BOUNDARY` is recorded
(`regime.py:206-219`). Exhaustion yields the terminal statuses
`TARGET_RANGE_EXHAUSTED` / `FOCAL_RANGE_EXHAUSTED`. **m\* is frozen at Gate 2**
and no later stage may move it — the composed probe may stop a replication but
never steer it (`composed_probe.py:802-882`).

Three further preconditions at (n\*, m\*), else `REGIME_NOT_FOUND`
(`regime.py:246-307`): both solo rates inside their bands; B's solo vacuity ≤
0.10; and the graded shares above 0.99 and below 0.01 each ≤ 0.99 — read as a
share, not a mean. Plus §34 D17's construct floor: chance compliance for B at
m\* on the load-zero cells ≤ 0.50, as a point estimate with the Wilson interval
reported beside it.

### 9.2 Selection quantities versus description quantities

The distinction the paper must preserve:

| Quantity | Selects | Describes only | Note |
|---|---|---|---|
| Raw solo compliance | m\*, n\*; the §12.6 eligibility rule (U4 at E2); the V_head Wilson band | the D14 secondary difficulty coordinate | Selection coordinate for the operating point |
| ι (instructed compliance) | the V_diff caliper; reference ranking; spectrum targets; class-control matching | reported for every candidate | Primary difficulty coordinate |
| κ (chance) | V_chance ceilings; the D17 floor; ι itself | — | See the §4.3 chance-column discrepancy |
| κ(c\|B), Σ, p̂ | V_inter admissibility | the projection audit, post-unmasking | Obtained free from absent-instance verdicts |
| Truncation share | the completion cap | reported per cell | ≤ 0.10 rule |
| Vacuity | V_head ≤ 0.10; §12.4 adequacy | the §17.4 forced recomputation | — |
| Composed proximity band (0.05, 0.95) | **nothing in v7** | descriptive only | **[!]** v5/v6 registered it as a terminating criterion; v7 A1 withdrew that (`constants.py:347-353`) |
| Graded scores | §12.4 adequacy shares | F5 robustness scale | Never primary |

### 9.3 Coverage conditions C1–C8

**[P]** Evaluated on eligible rungs only; a rung with no ι (κ ≥ 0.99) is dropped
and recorded (`regime.py:545-714`).

| Cond. | Rule | Gates |
|---|---|---|
| C1 | ≥1 eligible rung strictly below and one strictly above ι_A | core arm |
| C2 | ≥3 Tier-1/2 feature groups below and ≥3 above | spectrum arm |
| C3 | ≥8 rungs within 0.15 of ι_A, from ≥4 groups | core arm |
| **C4** | ≥6 feature groups whose family straddles ι_A with ≥3 rungs spanning ≥0.40 in ι | spectrum arm |
| C5 | ≥16 eligible rungs | core arm |
| C6 | ≥8 Tier-1/2 families from ≥6 groups | core arm |
| C7 | ≥1 Tier-3 budget rung within 0.15 of ι_A | class arm |
| C8 | ≥3 Tier-2 rungs from three groups | near-form arm |

Two bases exist: a **certificate** on the 24-topic pre-screen at 1 draw, and the
**gating re-read** on the 192-topic calibration table at Gate 2's measured ι_A
(`stages/feasibility.py:466-569`). The code records that all four registered
replications passed C4 at the screen and lost it on the calibration basis
(`feasibility.py:496-500`); the same happened in every rehearsal lane. A bounded
expansion loop (≤2 rounds, ≤4 reserve rungs per family per round, picks only
from the frozen reserve) may repair a failure before it is final.

---

## 10. Baselines and controls

| Comparator | Purpose | Rules out | Cannot rule out | Status in v7 |
|---|---|---|---|---|
| solo vs pair — `D(B<-A)`, `D(A<-B)` | Establish that composition costs delivery at all | "nothing happens when instructions are combined" | anything about companion identity — confounded with load | **Ran.** L1 emitted in most lanes |
| same-form matched references — `Δ_R` (K=3, Tier 1) | **The primary contrast.** Companion identity at matched form and difficulty | `H_difficulty` as an explanation of an *excess*; solo-ceiling artefacts (baseline cancels) | whether the null is a property of the exact-count *form* rather than of *however* | **Ran.** Identified in every lane |
| outcome-specificity — `Ξ` | Is the excess specific to B, or is A generally disruptive? | `H_A-general`, when its lower bound exceeds 0 | direction-only: an unresolved direction yields `A_GENERAL_NOT_EXCLUDED`, not absence | **Ran.** Gate only, no threshold |
| broad-class control — `Δ_broad` (Tier 3, budget) | *Bound* the class explanation with one matched-difficulty companion of a different class | nothing on its own — it is one companion | class attribution; it carries `COMPANION_CLASS_NOT_MATCHED` permanently | **Ran, Gemmas only.** Absent for both Qwens (`CLASS_ARM_NOT_AVAILABLE`) |
| near-form control — `Δ_near` (Tier 2, K=3) | Separate "property of A" from "property of the exact-count form". **Precondition of the strong L3c** under D18 | `H_form` — would have | — | **[!] Never available.** `NEAR_FORM_ARM_NOT_AVAILABLE` in every lane; cells never generated |
| difficulty spectrum — `δ_difficulty`, ±0.20 rungs | Fit loss against difficulty on non-A companions and test A's residual | `H_difficulty` parametrically rather than by matching | — | **[!] Never identified.** C4 lost on the calibration basis in every lane; 20 members withheld |
| order reversal — F11 `Ord_·` | Position of the outcome constraint as an explicit factor | `H_order` as an artefact — both orders always generated | the mechanism of any order effect (§29: not identified) | **Ran.** L4b emitted in three models |
| wording variants (4 per instrument) | Prevent one phrasing from carrying the result | phrasing-specific verifier behaviour (wording suite proves verdict invariance) | phrasing-specific *model* behaviour — wording is balanced, not analysed as a factor | **Ran** as design balance |

**[!] Do not present unavailable arms as tested.** Two of the design's four
discriminating controls — the near-form arm and the difficulty spectrum — **were
never identified in any lane**. Their estimands are recorded as `NOT_IDENTIFIED`
with the status that explains them, never as zero, never as an omission
(`run/analysis_run.py:26-30`). Every L3c statement in the data therefore carries
scope `same_form_only` and the registered sentence: *"no excess relative to
same-form exact-count companions; this is not the refutation verdict, which
requires the near-form arm (§34 D18)"* (`constants.py:494-496`). The strong
refutation verdict was not reached, and the paper must not imply otherwise.

---

## 11. Statistical inference and uncertainty

### 11.1 Point estimates and the bootstrap

**[P]**

| Element | Specification |
|---|---|
| Point estimate | Mean over the 384 blocks of the estimator's per-block value (`bootstrap.py:116-117`) |
| Method | Nonparametric **block bootstrap**: blocks drawn with replacement, carrying *every* cell mean of each drawn block. Cells are never resampled (`bootstrap.py:1-8, 120-131`) |
| Resampling unit | The block (= one confirmatory topic). Both configurations of a block travel together |
| Replicates | **10,000** (`constants.py:448`) |
| Shared draw | **One index draw per replicate**, applied to every member of a family, so the joint variation of Δ_R and δ_difficulty is the real one (`bootstrap.py:123-131`) |
| Refit inside replicates | **Yes, for the difficulty members.** Every replicate recomputes κ, the difficulty coordinates, the losses, *refits* the non-A relation, predicts at that replicate's ι_A and recomputes the residual; fitting once and bootstrapping the residual would treat the coefficients as constants and understate the interval (`bootstrap.py:15-29`; v5 §17.2). Δ_R itself is a per-block vector and needs no refit |
| Studentisation | Each member standardised by its bootstrap standard error (sample SD, n−1) (`bootstrap.py:133-141`) |
| Simultaneous interval | **Studentised maximum-modulus.** Per replicate take max over members of \|rep − est\|/se; the critical value is the 95th percentile of that maximum; bounds are est ∓ critical·se (`bootstrap.py:143-172`). **Decisions read the simultaneous interval** |
| Marginal interval | 2.5th/97.5th percentiles of the member's own replicates, reported alongside, not used for decisions (`bootstrap.py:159-169`) |
| Multiplicity family | Eleven declared families F1–F11, per configuration, except F11 which is declared across configurations. **No cross-model family and no cross-model pooling.** A Šidák value is reported beside but never used |
| Confidence level | 95% |
| Seeds | `bootstrap_seed(phase, model_key)` from root 202608241 under domain `dci1v7:boot:v1` — a different root and domain from generation, so a resample can never consume a generation seed (`seeds.py:26-39, 68-71`) |
| Significance tests | **None.** No p-value is computed anywhere. Inference is interval-versus-threshold throughout |

### 11.2 Boundary cells and degenerate intervals

**[P]**, revised pre-adoption. §13.14, as revised by the boundary audit of
2026-08-28 *before* v7 was adopted and with zero v7 rows in existence, defines
three readings (`analysis/boundary.py:256-370`):

1. **Structural zero** — every differenced cell sits at the same exact boundary
   in every block. The standard error is 0 and the simultaneous interval
   degenerates to [0,0], so the decision interval becomes the Wilson allowance
   about zero, ±h_n, where h_384 = 0.0099 and h_24 = 0.138. No directional level
   is reachable by construction; the equivalence reading proceeds on that
   interval, so it is available at 384 blocks and not at 24.
2. **Arm at a boundary** — the simultaneous interval is widened *in the open
   direction only*, by each boundary constituent's absolute weight × 0.0099 (a
   third of it per reference in Δ_R's mean). Conservative by construction.
3. **Compressed direction** — when an arm sits above 0.90 or below 0.10 the
   attainable range is recorded and a status attached; **no verdict changes**
   (`boundary.py:41-45`).

The revision's own justification is worth quoting in a limitations paragraph:
the earlier blanket veto "made 3072/3072 perfect draws weaker evidence than
3071/3072" (`boundary.py:19-25`).

### 11.3 Thresholds and what each licenses

All on the compliance-difference scale.

| Threshold | Value | Applies to | Decision rule | Licenses exactly |
|---|---:|---|---|---|
| SESOI | 0.10 | all contrasts | — | the smallest difference the study treats as meaningful |
| Δ_R generic-load | 0.10 | Δ_R only | lower > 0.10 → **L3a** | "A costs B at least the generic-load threshold more than matched same-form companions" |
| Δ_R pair-specific | 0.25 | Δ_R only | lower > 0.25 → **L3b** | the source memo's pair-specific excess |
| Δ_R upper bound | 0.10 | Δ_R only | **upper < 0.10 → L3c** | "the local excess is bounded below the generic-load threshold" — *one-sided* |
| Equivalence region | ±0.10 | δ_difficulty (L3e) | interval wholly inside ±0.10 *and* precision met | "any change is smaller than the smallest effect of interest, at adequate precision" |
| Precision precondition | 0.05 / 0.06 / 0.08 | D, Δ_R, Δ_near, δ_diff, Ord_A/B = 0.05; Δ_j = 0.06; Λ, Ord_Λ = 0.08 | half-width above it → `INSUFFICIENT_PRECISION` | direction may still be reported; threshold and equivalence statements are withheld |
| L1 solo headroom floor | 0.05 | D(·←·) | solo compliance ≤ 0.05 → L1 not emitted | — |

### 11.4 [!] "Equivalent to zero" is not what L3c says

These are two different statements and the paper must not merge them.

**L3c is a one-sided upper bound: `upper < 0.10`** (`claims.py:313-314`). It
says the excess is bounded below the generic-load threshold. It does *not* say
Δ_R is near zero — an interval lying wholly *below* zero also satisfies it, and
in the rehearsal data several do: gemma-e2b with B second gives Δ_R = −0.085,
interval [−0.119, −0.051], which is L3c with the direction recorded separately
as `A_COMPARATIVELY_BETTER` (the matched companions cost B *more* than A does)
(`claims.py:258-280`).

**Two-sided equivalence** is a different predicate — `wholly_inside(±0.10)` —
and in v7 it is applied only to δ_difficulty at L3e
(`claims.py:182-183, 390-391`), an estimand that was never identified. So **no
equivalence claim about Δ_R was licensed in any lane**. The defensible sentence
is "the companion-specific excess is bounded above by 0.10 with 95% simultaneous
confidence", plus the direction where it is resolved.

### 11.5 The claim ladder as coded

| Level | Member | Gate and rule | Source |
|---|---|---|---|
| L1 | D(B←A), D(A←B) | solo headroom, not a structural zero, vacuity-forced recomputation agrees, decision lower > 0 | `claims.py:804-847` |
| L2 | Λ | both L1s licensed; interval excludes 0 | `claims.py:856-897` |
| L3a/b/c | Δ_R | precision precondition, then the three threshold comparisons above | `claims.py:283-320` |
| L3d/e | δ_difficulty | support must hold first, else `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and L3a–c only | `claims.py:355-392` |
| L4a | the six named F1 members | identical classification for the named member in *both* configurations of one model | `claims.py:1040-1131` |
| L4b | F11 order contrasts | both configurations analysed, not a structural zero, precision met, interval excludes 0. **An interval containing zero is not order-invariance** | `claims.py:1134-1197` |
| L5 | — | **No emitter exists.** Permanently withheld | `claims.py:1200-1205` |

Two joint-reading rules suppress a level rather than resolve a conflict:
`LOCAL_TIER_DISAGREE` (Δ_R and Δ_near on opposite sides of 0.10) and
`LOCAL_AND_SPECTRUM_DISAGREE` (L3a with L3e, or L3c with L3d)
(`claims.py:409-451, 616-635`).

---

## 12. Preregistration and analysis status

### 12.1 What a registration binds, and how

**[P]** Two documents are hashed by content — the preregistration and a
machine-readable reference design spec — and both must declare themselves
adopted; silence reads as draft (`manifest.py:116-136, 162-219`). The manifest
binds 43 required keys, closes all 26 §34 decisions, and is signed
**HMAC-SHA256 over the SHA-256 content hash** with a write-once 0600 key
(`src/dci1v4/engine/signing.py:22-65`). One registration commit binds a whole
study: a second commit is refused as needing formal supersession
(`manifest.py:1117-1175`). Records are write-once (`O_CREAT|O_EXCL` + fsync),
mirrored to a durable root and byte-verified, and every read verifies hash *and*
signature (`fs.py:43-56`; `transitions.py:140-155`).

### 12.2 Masking

**[P]** After confirmatory generation and before any analysis, the **companion
label** of every composed observation is permuted within (outcome,
configuration, block); solo and unconstrained cells pass through, and companion
*difficulties* are not permuted since they were fixed at Gate 3
(`masking.py:1-27, 278-310`). Six members are forbidden in the masked phase —
δ_difficulty, **Δ_R**, β, α_1..3, γ_tier (`masking.py:104-107`). The **analysis
code hash** over eight modules is sealed into the masked record and re-verified
at unmasking; a mismatch raises "the analysis code moved between the seal and
the unmask" (`analysis_run.py:67-75, 998, 1062-1068`). The mask key opens
exactly once and there is deliberately no re-unmasking path.

### 12.3 Amendments

| ID | Change | Timing | Direction |
|---|---|---|---|
| A1 | Withdraws the absolute composed-headroom criterion as terminal; no composed rate terminates a replication | pre-outcome | loosening |
| A2 | New §13.14 boundary readings (structural zero, arm-at-boundary, compression) | pre-outcome | neutral |
| A3 | §26 restated on the estimand | pre-outcome | neutral |
| A4 | Signed append-only post-registration amendment chain | pre-outcome | neutral |
| A5 | Withdraws D23, D26; adds D27 | pre-outcome | neutral |
| **A6** | Pre-freeze audit *records* §13.15 rather than requiring success; the unregistered `support_satisfied` check is withdrawn by name | **post-outcome** | loosening |
| **A7** | C1/C3/C5/C6 gate the core arm; C2/C4 gate the spectrum arm only. "No number moves" | **post-outcome** | loosening |
| **A8** | D6 means irreversible-and-continue everywhere | **post-outcome** | neutral |

The chain record for A6–A8 is signed and self-disclosing: it names the sections
(§12.6, §18, §19, §28.2, §33, §34 — *no* §13), records that all four
replications stood at `PREFREEZE_AUDIT_FAILURE` with 118,176–142,320 pre-freeze
rows at adoption, states that under A6 each would have reached the freeze and
under A7 each would have retained the core arm and Δ_R, and concludes that "the
four v7 terminal reports stand under the rule they ran"
(`evidence/dci1v7/registration/amendments/001_A6_A7_A8.json`). §32.3 is
executable: an amendment naming any §13 section is refused once any replication
holds a Gate-2.5 record (`registration_run.py:413-419`).

### 12.4 [!] The honest paragraph about analysis status

The four registered replications terminated on a pre-freeze check,
`support_satisfied`, that **was never in the preregistration** and contradicted
§13.15, §28.2, §18, §26 and D6 (`prefreeze_run.py:28-44`). The same unregistered
check had ended two v5 and one v6 replication. A6 withdrew it after the fact, as
a declared loosening.

That sequence is fully documented in signed records, and it is why the
confirmatory experiment is unrun rather than run-and-null. The correct framing
for the paper: the protocol and its instrument are validated end to end; the
confirmatory study under the amended rules has not been executed, and the
amendment that would permit it was adopted with outcomes visible.

### 12.5 Namespaces

Three: `registered` (dci1v7), `synthetic` (stand-in generator and scale knobs
permitted), and `development` (dci1v7-development; real backend, real rules, no
knobs, added 2026-08-28) (`engine/context.py:49-57`). Roots may not overlap, and
four independent mechanisms keep development evidence out of the registered tree
— a foreign-manifest guard, a positive admission rule, a study-id check at read
time, and a different signing key per root (`guards.py:56-116`;
`transitions.py:118-137`).

---

## 13. Tests of the design's own components

| Component isolated | Mechanism | Status | What may be said |
|---|---|---|---|
| Matching on **difficulty** | Spectrum arm: two rungs per core family at ι_A ± 0.20, fitted relation, δ_difficulty as A's residual | **[!] Unidentified** in every lane — C4 lost on the calibration basis; 20 members withheld irreversibly under D6 | Nothing empirical. Report the design and the non-identification with its registered reason |
| Matching on **form** | Near-form arm: three Tier-2 controls, Δ_near, D18's precondition for the strong L3c | **[!] Unavailable** in every lane — fewer than three qualifying Tier-2 families; cells never generated | Nothing empirical. Every L3c is `same_form_only` |
| **Position / order** | Both orders in every block; five F11 order contrasts with simultaneous intervals across configurations; L4a checks classification stability per member | **Valid and ran** | "Ord_B depends on the position of the outcome constraint", and nothing about why (§29) |
| **Wording** | Four wordings per instrument, deterministically balanced and orthogonal to order; verifier invariance proved over 20 × 674 × 4 | **Design control**, not an analysis — wording is not a factor in any estimand | That phrasing is balanced and verifier-invariant; not that model behaviour is wording-invariant |
| **Choice of references** | Δ_j, the three per-reference contrasts, with a heterogeneity qualifier attached when their intervals fall on different sides of 0.10 | **Valid and ran**, as a qualifier on L3a/L3b only | Whether the three references agree; the rehearsal data show they often do not (e.g. gemma-e2b second position: Δ_1 = −0.102, Δ_2 = −0.117, Δ_3 = −0.036) |
| **Number of references (K)** | — | **[!] No ablation** — K = 3 is fixed and Δ_R raises if the count differs | Nothing. Do not describe K as tuned or explored |
| **Difficulty coordinate** | §17.6 secondary: the whole fit repeated on raw solo compliance, classifications compared, disagreement recorded as `DIFFICULTY_COORDINATE_DEPENDENT` | **[H] Post-hoc, registered as such** — marginal intervals only, explicitly `NOT_REGISTERED_FOR_INFERENCE` | An agreement status; never a level and never a magnitude |
| **Projection accuracy** | Projection audit: predicted composed compliance p̂ vs realised, mean absolute error against a 0.05 allowance | **[H] Post-hoc diagnostic**, licenses nothing | Descriptive support for V_inter's model; no claim |
| **Vacuity robustness** | §17.4: when the F6 vacuity gate binds, L1/L2/L3 are recomputed on a forced non-vacuous scale and must agree, else the claim is withheld | **Valid and ran** — it withheld an L2 in one lane | That the claim survives a vacuity-robust recomputation |

---

## 14. Reproducibility

### 14.1 Authoritative paths

| Artefact | Path |
|---|---|
| Preregistration (v7, incorporating v6 → v5) | `user-notes/DCI1_preregistration_v7.md` |
| Machine-readable design spec | `dci1/reports/dci1v7/reference_design_spec.json` |
| Constants, thresholds, families | `dci1/src/dci1v7/protocol/constants.py` |
| Estimators | `dci1/src/dci1v7/analysis/estimators.py` |
| Bootstrap and intervals | `dci1/src/dci1v7/analysis/{bootstrap,intervals,boundary}.py` |
| Claim ladder | `dci1/src/dci1v7/analysis/claims.py` |
| Masking | `dci1/src/dci1v7/analysis/masking.py` |
| Verifier | `dci1/src/dci1v7/verifiers/{words,statistics,constraints,compliance}.py` |
| Prompt templates and cells | `dci1/src/dci1v7/design/{prompts,cells}.py` |
| Wordings | `dci1/src/dci1v7/protocol/wordings.py` |
| Reference selection | `dci1/src/dci1v7/stages/{selection,validity,calibration_table,stability}.py` |
| Seeds | `dci1/src/dci1v7/protocol/seeds.py` |
| Model registry | `dci1/src/dci1v4/models/registry.py` |
| Serving backend | `exploratory/vllm_backend/` · `dci1/environments/backend/` |

### 14.2 Identifiers for the analysed version

| Item | Value |
|---|---|
| Repository HEAD at reconstruction | `87a6c185a9bd7e0496548e5c3e0c44c63752bca3` |
| Registered manifest hash | `969a5b9f1947faddc42809a62377c6a725382e93b8f098f7d6ae98b5eb91ca14` |
| Registered protocol hash → after A6–A8 | `15fa1786…82dc` → `2e91a1c0aa83a11573678df22c37ec3ef316c6606af2fa885ba10028ba9b5d2d` |
| Registration commit (registered study) | `ed0446ff58d0efc70b7703c162997863a9530768` |
| Lane producing commit (r5, all stages from Gate 2.5) | `43bb22a533b0d57c2ff7486d5ea0af858ef972a0` |
| Freeze hash (r5, gemma-3n-e2b-it) | `4fd019c72f00628eac95c55f0cb8d94a85e838701229a408ad5661a8ea3b7d0b` |
| Canonical verifier hash (r5) | `1ffd4044063506b379c97f4f0ef42c7532c843a6847f52ea1344d82b15830fb3` |
| Analysis code hash (r5, sealed at masking) | `5ca907f6342c94b2b77a6c45e70a45fd3a6664a2d4d8d8c0738c06cac71c4feb` |
| Wording hash (r5) | `476dbaa7e516ad6c4f8db866a9694a627eb0184784c7033c13e655f1a74800f0` |
| Calibration table hashes (A / B) | `57850f1c…a59e` / `bc7a7350…2c73` |
| Evidence roots (gitignored, not in a clone) | `dci1/evidence/dci1v7` · `dci1v7-development{,-r2..-r5}` |

### 14.3 Environment

**[D]** Two interpreters by design.

- **Backend** — Python 3.12, vLLM 0.15.1+rocm720 (vendored wheel, hashes in
  `vendor/MANIFEST.sha256`), torch 2.9.1+rocm7.2.0, torchvision
  0.24.0+rocm7.2.0, triton 3.5.1+rocm7.2.0, transformers 4.57.6, numpy 2.1.3,
  huggingface-hub 0.36.2, `HF_HUB_OFFLINE=1`.
- **Scientific** — Python ≥ 3.13, numpy 2.5.2 only, no GPU stack.
- **Hardware** — 2 × AMD Radeon RX 7900 XTX (gfx1100, 24 GB), run as two
  independent TP=1 lanes pinned by `HIP_VISIBLE_DEVICES` with a per-card lock.
- **Runtime** (rehearsal measurement) — 4 h 08 m to 14 h per model end to end;
  `gemma-3n-e4b-it` is the slowest at ~5 h 48 m for 89,088 confirmatory rows.

---

## 15. Paper-ready summary

### 15.1 Plain-language description (218 words)

> We measure whether one instruction interferes with another *specifically*,
> rather than merely adding load. A focal instruction B ("every word must have
> at most m letters") is held fixed, and we compare how well the model delivers
> B when it is accompanied by the instruction under test, A ("use the word
> *however* exactly n times"), against how well it delivers B when accompanied
> by one of three reference instructions R_j. Each R_j is chosen, before any
> paired outcome is observed, to share A's predicate form on seven structural
> fields and to match A's stand-alone difficulty within a pre-set caliper, after
> correcting for the rate at which the instruction is satisfied by chance. The
> companion-specific contrast Δ_R differences two composed conditions of equal
> instruction load, so the solo baseline cancels algebraically and no solo
> ceiling can distort it. Because interference may depend on presentation order,
> every pair is generated in both orders in every block, and the focal
> instruction's position is carried as an explicit factor rather than averaged
> away. Severities are calibrated per model to place both instructions in a
> registered compliance band. Compliance is decided by a deterministic verifier
> validated against an independent reimplementation, a frozen boundary suite and
> an adversarial corpus. Uncertainty is a block bootstrap with simultaneous
> intervals over declared families of estimands.

### 15.2 Formal specification

```
Design.   models M = {4 checkpoints};  blocks b = 1..384 (one topic each);  draws k = 1..8
          configurations γ ∈ {outcome_first, outcome_second}
                            = position of the OUTCOME instruction
          every instruction pair generated in BOTH prompt orders in every block

Measurement.  X_c(b,k,cell) ∈ {0,1} deterministic verifier verdict for instruction c
              P̂_c(b, cell) = (1/8) Σ_k X_c(b,k,cell)        # the experimental unit

Calibration (per model, before any composed outcome).
   κ_c   = P̂_c on the unconstrained cell                     # chance
   ι_c   = (P_solo(c) − κ_c) / (1 − κ_c)                      # difficulty coordinate
   n*    = argmin_{n : P_solo(A_n) ∈ (0.50,0.85)} |P_solo(A_n) − 0.70|
   m*    = argmin_{m : P_solo(B_m) ∈ (0.60,0.95)} |P_solo(B_m) − 0.80|

Reference admission.  R is admissible <=> V_spec ∧ V_sat ∧ V_head ∧ V_chance
                                        ∧ V_struct ∧ V_inter ∧ V_stab ∧ V_diff,
   with V_struct: R matches A on 7 structural fields (Tier 1)
        V_diff:   |ι_R − ι_A| ≤ 0.10
                  ∧ Newcombe_95(P_solo(R) − P_solo(A)) ∩ [−0.05, 0.05] ≠ ∅
                  ∧ |P_solo(R) − P_solo(A)| ≤ 0.15
   {R_1,R_2,R_3} = the 3 top-ranked admissible families, distinct feature groups,
                   ≥2 Tier 1, ≥2 discourse roles;  ranking by (|ι_R − ι_A|, tier, group, …)

Estimands, per model and per configuration γ, on the compliance scale.
   D_γ(c ← g)(b) = P̂_c(b, solo:c) − P̂_c(b, composed cell with g at position γ)
   Δ_R,γ(b)      = (1/3) Σ_j P̂_B(b, B+R_j @γ) − P̂_B(b, B+A @γ)
   Λ_γ           = D_γ(B←A) − D_γ(A←B)
   Ξ_γ           = Δ_R,γ − [ D_γ(R̄←A) − D_γ(R̄←R̄′) ]
   Ord_B         = D(B←A)|first − D(B←A)|second

Inference.  θ̂ = (1/384) Σ_b θ(b)
   B* = 10,000 block-bootstrap replicates, blocks drawn with replacement,
        one index draw per replicate shared by all members of a family
   se(θ) = sd(θ*);   q = 95th pct of max_{members} |θ* − θ̂| / se
   CI_sim(θ) = θ̂ ∓ q · se(θ)     # studentised maximum-modulus, family-simultaneous

Decision.  half-width ≤ 0.05 required for Δ_R (else INSUFFICIENT_PRECISION)
   L3a: CI_low > 0.10     L3b: CI_low > 0.25     L3c: CI_high < 0.10
   L5 (mechanism, generalisation): never emitted
```

### 15.3 Pseudocode for the matched-reference experiment

```
for model in {4 pinned checkpoints}:                # never pooled

  # ---- calibration, no composed outcome observed ----
  cap    = smallest cap in {512,768,1024} with truncation ≤ 0.10   # 24 pre-screen topics
  n*, m* = operating points on their registered bands   # 192 calibration topics, 4 draws
  assert regime_adequate(n*, m*) and chance(B, m*) ≤ 0.50
  ι_A    = (P_solo(A_n*) − κ_A) / (1 − κ_A)

  # ---- reference selection, still blind to composed outcomes ----
  table = calibration rows for all Tier-1/2 rungs + ≤24 Tier-3 rungs,
          on Calibration-A and Calibration-B separately and pooled
  R1,R2,R3 = select_core(table, ι_A)      # §4.5; distinct groups, ≥2 Tier 1
  if fewer than 3: record EXCESS_NOT_IDENTIFIED, withhold L3a–L3e, continue
  CL       = matched Tier-3 budget control or CLASS_ARM_NOT_AVAILABLE
  N1..N3   = Tier-2 near-form controls     or NEAR_FORM_ARM_NOT_AVAILABLE
  freeze(references, arms, cells, seeds, hashes, thresholds)      # clean worktree

  # ---- confirmatory generation ----
  for b in 384 confirmatory topics:
    for cell in admitted cells:               # includes BOTH orders of every pair
      for k in 1..8:
        seed   = H("dci1v7:gen:v1", root, stage, model_id, prompt_hash, k)
        answer = generate(prompt(b, cell), temp=0.7, top_p=0.9, top_k=50, cap, seed)
        score every registered instruction on the answer     # present and absent alike
  assert every (block, cell, draw) identity exactly once     # no retry, no exclusion

  # ---- analysis ----
  permute companion labels within (outcome, configuration, block); seal code hash
  compute the label-independent members;  unmask once;  compute Δ_R and the rest
  for γ in {outcome_first, outcome_second}:
      Δ_R,γ = mean_j P̂_B(B+R_j @γ) − P̂_B(B+A @γ)
      CI    = studentised-max-modulus bootstrap over 384 blocks, family F1
      emit L1/L2/L3 by the registered rules; attach REFERENCE_POOL_SAME_FORM
  emit L4a (classification stability) and L4b (order dependence)
```

### 15.4 Component table

| Component | Final v7 choice | Why | Source file/line |
|---|---|---|---|
| Primary estimand | Δ_R = mean_j P(B\|B+R_j) − P(B\|B+A) | Differences two equal-load composed cells so the solo baseline cancels exactly | `estimators.py:138-162` |
| Outcome scale | Compliance, binary, block-mean of 8 draws | Failure rates are never used; one convention avoids sign confusion | `estimators.py:51` |
| Number of references K | 3, plus 2 frozen backups that never substitute | Averaging over three controls damps single-reference idiosyncrasy; no substitution function exists, so post-hoc swapping is impossible | `constants.py:333, 338-341` |
| Form matching | Tier 1 = identity on 7 structural fields | Makes "same form" a computable test, not a judgement; excludes burden and frequency deliberately | `taxonomy.py:107-113` |
| Difficulty coordinate | ι = (solo − κ)/(1 − κ) | Two instructions with the same solo rate differ if one is often satisfied by accident | `calibration_table.py:77-99` |
| Caliper | \|ι_R − ι_A\| ≤ 0.10, plus a Newcombe interval and a raw-rate check | A point caliper alone would admit a reference whose match is an artefact of sampling | `validity.py:348-390` |
| Selection timing | Gate 3B, before any composed outcome | The §6 firewall; selection schemas refuse composed columns before a value is read | `calibration_table.py:56-68` |
| Order | Both prompt orders in every block; configuration = outcome position | Interference is directional; averaging over order would hide the largest effect in the data | `cells.py:213-215`; `constants.py:140-145` |
| Wording | 4 per instrument, deterministic block-indexed allocation | Balanced and orthogonal to order by construction rather than by randomisation | `cells.py:271-287` |
| Blocking | 384 topics; every cell at every topic | Every contrast is formed within a block, so topic difficulty cancels | `observations.py:297-337` |
| Draws | M = 8, all kept | No selection of draws means no hidden filtering | `confirmatory_run.py:247-249` |
| Uncertainty | Block bootstrap, 10,000 replicates, studentised max-modulus, 95% | The block is the clustering unit; simultaneous coverage over declared families | `bootstrap.py:120-172` |
| Multiplicity | 11 declared families, per configuration (F11 across) | Declared before outcomes; no cross-model family | v5 §15 L2545–2557 |
| Decision rule | Interval vs registered thresholds; no p-values | Thresholds carry provenance from a prior memo; L3c is an upper bound, not equivalence | `claims.py:283-320` |
| Boundary handling | Structural zero → ±Wilson allowance; boundary arm → one-sided widening; compression → status only | Perfect cells must not be treated as more uncertain than near-perfect ones | `boundary.py:256-370` |
| Masking | Companion label permuted within (outcome, configuration, block); Δ_R withheld; code hash sealed | Prevents analyst degrees of freedom between generation and estimation | `masking.py:104-107`; `analysis_run.py:998` |
| Verifier | Deterministic; validated against an independent reimplementation, 177 boundary cases, 18 adversarial phenomena, 6 mutation classes | Compliance is verifier-defined, so the instrument itself is the measurement claim | `gate1.py:376-518` |
| Non-identification | Recorded with a reason; never zero, never omitted | An unavailable arm must not read as a null result | `analysis_run.py:26-30` |

### 15.5 Information still missing for a reproducible Methods section

1. **A confirmatory run.** The registered study has no freeze and no
   confirmatory rows. Any Methods section describing results must either
   describe the development rehearsals as such, or wait for a registered run
   under the amended rules.
2. **The chance-column decision.** Candidate ι is raw solo compliance on the
   executed code while ι_A is chance-corrected (§4.3). Whether to correct it —
   and how, given that the fix touches modules pinned byte-for-byte by revision
   V9 — is an open researcher decision that must be settled before any
   confirmatory claim about difficulty matching.
3. **Host CPU, RAM, OS and kernel** are not recorded in any committed file; the
   richer environment record exists in code but v7 does not call it. Only the
   two GPUs are documented.
4. **Licences.** No LICENSE file exists at any depth; no licence identifier is
   stored for any model checkpoint; the topic bank carries authoring rules but
   no licence term. All three are needed for release.
5. **Two provenance defects to fix or disclose:** `dependency_digest` hashes the
   *path string* of the lock file rather than its contents, and
   `environment_digest` is free text supplied on the command line
   ("rocm7.2/vllm0.15.1/gpu1") rather than a computed digest.
6. **The backend lives outside the governed tree** (`exploratory/vllm_backend/`),
   so its behaviour is pinned by lock file and vendored wheel hashes rather than
   by the signed manifest. State the pinning mechanism explicitly.
7. **Nine documented preregistration inconsistencies** in the v7 → v6 → v5
   chain, including C4's core-versus-spectrum scope, the open-versus-closed
   composed band notation, and §26's "both splits" versus §13.15's "pooled and
   both splits". Decide which reading the paper reports for each.
8. **Reviewer-facing statement of the unregistered `support_satisfied` check**
   and of the post-outcome A6–A8 amendments — the signed chain already discloses
   these; the paper needs its own paragraph.

*Resolved while writing this document (2026-08-30): the per-model operating
points and completion caps, previously listed as missing, are recorded in the
signed records and are reproduced in §7.2. All four models selected cap 512, and
m\*/n\* are identical between the registered study and the development lanes.*
