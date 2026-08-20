# Amendment B (draft) — candidate reference families of non-budget form

**Status: DRAFT, CONDITIONAL, UNSIGNED. Not applied. Not adopted.**
This document is written so that it can be adopted whole if the FORM × STEM
screen meets its §2.4 reference criterion, and discarded whole if it does not.
Nothing in the registered pool has been changed. The candidate definitions
exist in `dci1/src/fs_screen_v4/`, outside the v4 namespace, where no v4
estimator can reach them.

**Amends:** §7.2 (the reference pool and its ladders), §7.3 (wordings and
witnesses), §13.2 (reference admission), with a mandatory consequence for
§10.2 and therefore for Gate 1.

> **The cost list in §5 was incomplete — see §5a, added 2026-08-20.** It omitted
> §7.3's witness obligation over the enlarged pool: 2,448 pairs with no
> constructive certificate under §6's recommended adoption set, against the 288
> the screen actually proved. Read §5a before reading §9's recommendation.

---

## 1. The problem this answers

From the read-only diagnostic of 2026-08-20, established structurally rather
than statistically:

Every reference statistic in `verifiers/statistics.py` is a count over words or
characters, and every pass predicate is `S ≤ q`. Every such statistic is
monotone non-decreasing under text extension, so **every reference family's
pass set is downward-closed under prefix**: shortening a response can never
turn a pass into a fail. B (`max word length ≤ m`) has the same property. A
(`S == n`, exact-count production) does not.

Evaluated through the canonical verifier:

| text | RF1–RF8 (94 severities) | B (4) | A (8) |
|---|---|---|---|
| `''` | **94/94 pass** | **4/4** | **0/8** |

The empty string is a perfect score on the entire reference pool and a zero on
A. The consequence, replicated on all four models: only 3–6 of 94 rungs meet
§13.2 condition 6 (solo vacuity ≤ 0.10), and **none of them fall inside the
0.10 caliper**. The low-vacuity rungs are bimodal — either far below A
(nothing passes) or far above (everything passes). The pool crosses A's
compliance level *only* through the vacuity channel. Check C10 records the
same thing from the other side: 0 of 64 matched rungs survive condition 6.

## 2. The candidate families

Six, in two forms. Naming keeps `RF*` reserved for the registered pool so no
artifact can be confused: `CR*` = rate form, `CL*` = lower-bound form.

| id | form | numerator | ladder | numerator source |
|---|---|---|---|---|
| CR7 | rate | words containing the letter *a* | 24,28,32,36,40,44,48,52 (%) | registered `RF7` |
| CR4 | rate | words containing two identical adjacent letters | 3,5,7,9,11,13,15,18 (%) | registered `RF4` |
| CR6 | rate | words containing an upper-case letter | 3,4,5,6,7,8,10,12 (%) | **new** |
| CL1 | lower bound | words beginning with *b* | 1,2,3,4,6,8,11,15 | registered `RF1` |
| CL7 | lower bound | words containing the letter *a* | 10,20,30,45,60,80,100,130 | registered `RF7` |
| CL8 | lower bound | words ending with *y* | 2,3,5,7,10,14,19,25 | registered `RF8` |

Predicates:

```
rate:        100 * S / words <= q     (a wordless answer has no rate: it fails)
lower_bound: S >= q
```

Both break prefix closure. The empty string passes **0 of 48** candidate
severities against 94 of 94 registered ones.

**CR6's numerator is genuinely new and is flagged as such.** Registered RF6
counts upper-case *characters*. A rate form is denominated in words, so a
character numerator over a word denominator is not a proportion of anything.
CR6 counts *words containing an upper-case letter*. It is the one candidate
numerator not byte-identical to a registered one, and §5 below is the reason
that matters more than it looks.

### Why these ladders

Rate ladders are one shared grid; lower-bound ladders are geometric. That is
forced by the data, not by taste. On A-solo text across all four models:

| quantity | E2B | E4B | Qwen3-4B | Qwen3-4B-Inst |
|---|---|---|---|---|
| RF7 **rate** median | 39.5 % | 38.8 % | 36.0 % | 37.0 % |
| RF7 **count** median | 93 | 94 | 34 | 43 |

The rate is model-portable to within a few percentage points; the count varies
nearly threefold. A single registered rate ladder can serve all four
replications. A single count ladder cannot, which is a standing argument in
favour of the rate form over the lower-bound form independent of how the screen
comes out.

## 3. RF2 carries no candidate form, deliberately

A lower-bound RF2 requires *q* words ending in *ing*. B at *m* = 7 forbids any
word over seven letters. The pair is satisfiable in principle — *going, doing,
being, bring, thing, swing…* — but only from a closed vocabulary of roughly
thirteen words, most of them function words, while the *ing*-final words the
models actually produce (*planning, designing, considering, maintaining*) all
exceed seven letters. It is admissible in principle and unusable in practice.
`fs_screen_v4.witnesses.assert_rf2_conflict` records the measurement rather
than the assertion. **Do not add RF2 to the candidate set.**

## 4. Discipline: proved, not claimed

Each candidate is held to exactly the registered obligations of §7.3, and each
is executable:

| obligation | status |
|---|---|
| four wordings per constraint | ✓ |
| one verifier decides all four | ✓ 960 fixture verdicts, twenty-response suite |
| word counts severity-invariant | ✓ `assert_severity_invariance` |
| every wording within 20 % of the A wording of the same index, at every *n* | ✓ `assert_caliper_feasible` |
| whole-answer scope, single clause | ✓ by construction |
| parse independence (text, kind, severity only) | ✓ asserted on the signatures |
| vocabulary drawn from the family's own rule statement | ✓ `assert_rule_vocabulary` |
| joint witness and both non-entailment directions vs A and vs B at every severity | ✓ **576 compositions certified** |

The caliper is tight and it bound the authoring: A's wording word counts are
[6, 7, 7, 7], so index 0 must land in {5, 6, 7} and indices 1–3 in {6, 7, 8}.
That is why the phrasing is compact (*"At most 32% of words contain letter a."*)
rather than the fuller *"…may contain the letter a"* of the §7.2 table — the
same authoring constraint, and the same resolution, as the registered families
already required.

## 5. Adopting this re-opens §10.2, and therefore Gate 1

**This is the cost that must not be buried.**

§10.2 carries the verifier sources byte-identically from the closed v3
instrument, and `dci1v4.carryover` verifies that identity and refuses on drift.
Five of six candidates reuse a registered numerator unchanged, so their
*counting* inherits that carry-over. But:

1. **The predicates are new.** `S ≥ q` and `100·S/words ≤ q` have no v3
   ancestor. They are new verifier code on a mandatory scoring path.
2. **CR6's numerator is new outright.** It has no carry-over evidence at all.
3. Therefore **the canonical verifier hash changes**, and §10.6 binds that hash
   at eleven entry points.
4. Therefore **Gate 1's instrument set changes with it**. Gate 1 freezes the
   verifier hash; a pool amendment adopted after Gate 1 would invalidate it.
   The boundary suite (currently 40 carried cases + 8 added target cases + 45
   focal cases) must be extended with boundary cases for each new predicate —
   at minimum `S = q−1, q, q+1` for the lower-bound form and rates
   straddling each `q` for the rate form — and the determinism and audit checks
   re-run.

**Sequencing consequence:** Amendment B must be adopted **before** Gate 1, or
not in this study. There is no order in which it can be adopted afterwards
without discarding Gate 1's instrument freeze.

### 5a. The cost list above is incomplete — §7.3's witness obligation over the enlarged pool

> **Added 2026-08-20.** §5 names four costs: the new predicates, CR6's new
> numerator, the canonical verifier hash, and the Gate 1 instrument set with its
> boundary suite. It does not name the largest one. **Found by the sibling
> session `dci-79`** while building the matrix screen's witness check;
> independently reproduced and sized here.

§7.3 requires, for **every registered unordered pair of constraints at every
registered severity**, a machine-verified witness satisfying both, and one
witness in each direction of non-entailment. That obligation is discharged
pool-wide at qualification by `verifiers.witnesses.verify_all_witnesses`, which
iterates `all_pairs()` — every unordered pair of *distinct kinds* over
`registered_instances()`, reference × reference included. It is recorded and
signed on all four models at stage 1:

| model | pairs | kind-pair classes | verified |
|---|---|---|---|
| gemma-3n-e2b-it | 4,910 | 45 | true |
| gemma-3n-e4b-it | 4,910 | 45 | true |
| qwen3-4b | 4,910 | 45 | true |
| qwen3-4b-instruct-2507 | 4,910 | 45 | true |

Enlarging the pool enlarges that set, and the growth is quadratic in the pool,
not linear in the families added:

| adoption set | instances added | pool pairs | certified by this screen | **uncertified obligation** |
|---|---|---|---|---|
| rate families CR7, CR4, CR6 (§6's recommendation) | 24 | 4,910 → 7,646 | 288 (candidate × A/B) | **2,448** |
| lower-bound families CL1, CL7, CL8 | 24 | 4,910 → 7,646 | 288 | **2,448** |
| all six candidates | 48 | 4,910 → 10,958 | 576 | **5,472** |

The screen certified candidate × A and candidate × B — 576 compositions, all six
candidates against the full target and focal grids. Every other pair an enlarged
pool creates has **no constructive certificate**, in three classes:

1. **candidate × registered family** — 2,256 pairs under the recommended set,
   and exactly what an enlarged pool is *for*;
2. **candidate × candidate** — 192 pairs, unavoidable once more than one
   candidate is adopted;
3. **anything involving B at m = 11 or 12** — the registered `Constraint`
   constructor refuses those severities by design, so Amendments B and C
   interact here rather than composing independently.

**And the existing constructor cannot simply be pointed at them.** Used outside
its envelope, `fs_screen_v4.witnesses.verify_candidate_pair` *silently
misreported*: its "candidate satisfied, companion failed" branch fails the
companion by appending a long word, which moves B's statistic and no reference
family's, so against RF3 it raised `CR6@7 appears to entail RF3@4` — a
construction failure dressed as an entailment claim, in the one place a reader
would trust a machine verdict. Reproduced on this side for CR6, CR4 and CL1
against RF1, RF3 and RF6. The envelope is now **enforced rather than
documented**: `assert_in_envelope` refuses any companion outside `("A", "B")`
and names why, and two tests in `tests_v4/test_fs_screen_isolation.py` pin it.
No screen output changed — `verify_all` still certifies 576 compositions and the
frozen screen protocol payload is byte-identical apart from `producing_commit`.

**Consequence for this amendment.** Adopting it requires a witness constructor
that does not exist: one that builds joint and both-direction non-entailment
witnesses for candidate × reference and candidate × candidate at every severity
combination, for a form whose numerator is a *rate* rather than a count. That is
new code on a §7.3 mandatory pre-generation path, and it lands *before* Gate 1
by §5's sequencing argument, alongside the boundary suite and the re-run
determinism and audit checks. It should be costed with them, not discovered
after adoption.

**This cost disappears entirely if the registered pool clears three families
under Amendment A's stem** — the condition dci-79's pool arm is measuring. In
that case Amendment B is unnecessary and this obligation is never incurred.

---

## 6. Consequences for §13.2

The six admission conditions apply unchanged. Two behave differently:

- **Condition 1 (caliper on solo compliance)** — unchanged in form. The
  candidate compliance curve is measured on the 96 solo-calibration topics as
  now.
- **Condition 6 (solo vacuity ≤ 0.10)** — this is the condition the registered
  pool fails 0 of 64 times, and the one the candidates are designed to make
  attainable *inside* the caliper rather than only at the ends of the ladder.
  The screen's §2.4 reference criterion is exactly the conjunction of
  conditions 1 and 6 at the same severity.

The pool would become eight registered families **plus** the adopted
candidates, and §13.2 would select three from the enlarged pool by the existing
rule. Nothing in the selection logic changes. `REFERENCE_LADDERS`,
`FAMILY_STATISTICS`, `REFERENCE_CALIPER`, `REFERENCE_VACUITY_MAX` and every
registered wording remain exactly as they are; the amendment is additive.

**Recommended adoption set, if the screen succeeds:** the three rate families
(CR7, CR4, CR6), because a shared model-portable ladder is worth more than the
lower-bound families' cleaner boundary behaviour, and because a lower bound
imposes a length *floor* — pushing length up while B pushes it down, which
replaces one length confound with its mirror image. Adopt the lower-bound
families only if the rate families fail and the lower-bound families pass.

## 7. What Amendment B does not fix

A rate-form constraint is length-orthogonal in its **gradient** —
correlation with word count falls from +0.21…+0.99 for the count form to
mostly under 0.10 for the rate form — but it is **not** fixed at the boundary:
a one-word answer with a zero numerator still has rate 0 and still passes. Of
48 candidate severities, 16 pass a one-word answer, all of them rate-form
rungs. The rate form therefore still needs the §9.3 non-vacuity predicate, or
Amendment A's stem, or both. That is the reason the screen crosses the two
factors instead of testing either alone.

## 8. Discard condition

If the screen's reference criterion fails — fewer than three families reaching
the condition-1 ∧ condition-6 conjunction on all four models — **discard this
amendment**. Do not widen the caliper, lower the vacuity threshold, or extend a
ladder to make it pass; those are the moves the sensitivity map exists to
foreclose. A failure means the two remaining options are the ones set out in
the screen report: change the outcome constraint's structural class, or accept
the reduced design of §8.6 with L3 withheld **by design** and the reason
recorded, rather than as a fallback nobody chose.

---

## 9. Screen outcome — 2026-08-20. **Supported; proceed, with one condition.**

The FORM × STEM screen (`dci1/reports/fs_screen_v4/REPORT.md`, protocol hash
`98f8ee0d…`) tested the candidate families under both stems.

**Families meeting the §13.2 condition-1 ∧ condition-6 conjunction at the same
severity** (three required):

| model | registered pool (`count × current`) | candidates (`candidate × current`) |
|---|---:|---|
| E2B | 0 | **3** — CL7, CR6, CR7 |
| E4B | 0 | **4** — CL7, CR4, CR6, CR7 |
| Qwen3-4B | 0 | **5** — CL1, CL7, CR4, CR6, CR7 |
| Qwen3-4B-Inst | 0 | 2 — CL1, CR6 |

Topic-clustered bootstrap P(≥3 families): **0.000–0.001** for the registered
pool against **0.41–0.88** for the candidates. That contrast is the finding; the
individual counts are not stable at one-family resolution on 24 topics at one
draw, and the bootstrap of a threshold-crossing count is itself optimistic.

**The candidate result is insensitive to the non-vacuity threshold.** Across
T ∈ {10, 20, 30} the count is flat (E2B returns 3 at every T; E4B 3–4), because
candidates produce few short answers so their vacuity barely moves with the
threshold. The registered pool returns 0 across the whole grid except where
T = 10 loosens the vacuity condition itself. **The candidates did not clear the
criterion by threshold choice**, which is the objection this design most needed
to answer.

CR7 and CR6 appear in every non-empty qualifying set; CR4 in three. **The rate
families carry the result.** CL7 also qualifies on three models, but on ladders
that had to be geometric and model-agnostic because the counts vary threefold
across models while the rates do not.

### Recommendation

**Proceed with the three rate families — CR7, CR4, CR6.** This is the set §6
recommended in advance and the screen supports it: they carry the result, they
share one model-portable ladder, and they avoid the lower-bound families' length
*floor*, which would push length up while B pushes it down.

**One condition, not optional.** Everything above is 24 pre-screen topics at one
draw. §12.3 re-measures on the disjoint 96 solo-calibration topics at M = 4 and
§13.2 admits against *that*. This screen has never been shown to predict it, and
the instability of the counts argues it may not. **The candidate families must
clear the conjunction on the calibration set before they are adopted into the
registered pool.** Adoption still has to precede Gate 1 for the §10.2 reason in
§5, so the sequence is: calibration-set confirmation → adopt → **build the
missing candidate × reference and candidate × candidate witness constructor
(§5a)** → extend the boundary suite → Gate 1.

The screen did **not** reproduce the bimodality that made the registered pool
fail, so §8's discard condition is not triggered.
