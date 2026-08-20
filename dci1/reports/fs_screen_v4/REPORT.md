# FORM × STEM screen — report

**Classification: NON-CONFIRMATORY DESIGN SCREEN.** Not a registered v4 stage,
no Gate 1 dependency, same standing as the B+R pilot. Nothing here may enter a
v4 estimator. Gate 1 is not approved, the protocol is not frozen, no
confirmatory data were generated, V1–V9 remain open, and no candidate family
has been adopted.

| | |
|---|---|
| Screen protocol hash | `98f8ee0da826b5023e24c32f8b33d9fce1f645372742d6a0c2edec4f086755e5` |
| Producing commit | `8541f9fa5fd97d12c46e767e20b47e613983a17c` |
| Frozen | before the first generation, at `reports/fs_screen_v4/screen_protocol.json` |
| Canonical verifier hash | `f5d4f7e7…7580ee4` — **identical to the signed registration manifest** |
| Evidence root | `evidence/fs-screen-v4/` (outside the v4 namespace) |
| Generated | 13,392 rows across four models |

---

## 1. Two operational fixes

### 1.1 Orphaned backends — fixed and verified

All three (PIDs 1011292, 1012613, 1022671) were confirmed genuine orphans
before being killed: reparented to `systemd --user`, output files complete and
closed 11 h earlier (1200/1200/2544 lines), and 7–11 s of CPU consumed across
12 h — blocked, not working. Killed; no `vllm` process and no KFD registration
survived.

**Root cause.** `run_backend` used `subprocess.run`, which kills only the direct
child on timeout and nothing at all when the driver dies.

**Fix.** The backend now starts in its own process group (`start_new_session`)
with `PR_SET_PDEATHSIG`, and the group is torn down on return, on exception, on
timeout and on SIGTERM/SIGINT/SIGHUP. PDEATHSIG covers the one case no handler
can — `kill -9` of the driver — and that was verified empirically before being
trusted. Three regression tests in `tests_v4/test_backend_teardown.py`.

**Verified in production:** after all eight screen runs completed,
`pgrep vllm` returned nothing. The previous four-model run left three orphans.

### 1.2 Evidence durability — a real defect, found and fixed

The mirror was **not** complete: 152 of 158 files. The six missing were **all
four `regime_screen.json` records** plus the registration manifest and signing
key; four transition logs and three backend logs were also stale.

**Root cause.** Stage bodies called `store.replicate` and then returned; the
dispatcher wrote and signed the stage record *afterwards*. **The signed record
and its transition-log entry — the artifacts that *are* the evidence — were the
two files systematically excluded from every mirror.**

**Fix.** Replication moved to the stage exit in `engine/dispatch.run_stage`, on
both the success and terminal paths, and verified with
`store.assert_replicated` rather than assumed. `stages/registration.register`
mirrors the manifest likewise. Mirror repaired: **157 files, verified**.

**Loss detection.** `tools/evidence_manifest_v4.py` writes
`docs/evidence_manifest_v4.json` — every registered path with its SHA-256, 17
of them flagged critical — and `--verify` reports missing, changed and extra
files against it. It cannot restore anything.

**Stated plainly, as asked: there is no second physical copy.** `evidence/` and
`durable_root/` are verified on the same device (64512,
`/dev/mapper/ubuntu--vg-ubuntu--lv`, the single root volume). The mirror
protects against a bad write or a partial run, not against losing the disk.
A remote exists (`github.com/cnm13ryan/dci.git`) but this branch is unpushed,
so today even the manifest is single-copy.

---

## 2. The screen as run

Frozen before generation; the frozen record carries the candidate definitions,
ladders, wordings, witness certification, seeds, success criteria, the
twenty-response fixture verdict table, and the registered values it does not
touch.

**Isolation.** Own study id (`fs-screen-v4`), own root seed 202608200 under
domain `fsscreen:gen:v1` — distinct from every v3 root (202608170–175) and v4
root (202608190–195) — own evidence root and report directory. Thirteen tests
in `tests_v4/test_fs_screen_isolation.py` pin it, including that the v4
positive-admission guard refuses the screen tree and that the canonical
verifier hash still equals the manifest's.

**Discipline, proved not claimed.** 960 fixture verdicts (48 severities × 20
responses), 576 certified joint witnesses against A and B, severity-invariant
wording word counts, all 48 candidate severities inside the 20 % caliper
against A at every *n*, vocabulary checked against each family's own rule
statement, parse independence asserted on the callable signatures.

**RF2 excluded, with the reason measured** rather than asserted: a lower-bound
RF2 needs words ending in *ing*; B at *m* = 7 forbids words over seven letters;
the intersection is a ~13-word closed vocabulary while the *ing*-final words
the models actually produce all exceed seven letters.

### Cells generated

| model | screen rows | reused registered rows | total analysed | truncation | stem obeyed (floored) |
|---|---:|---:|---:|---:|---:|
| E2B | 3,312 | 2,544 | 5,856 | 267 | 0.891 |
| E4B | 3,168 | 2,544 | 5,712 | 157 | 0.879 |
| Qwen3-4B | 3,528 | 2,544 | 6,072 | 56 | 0.709 |
| Qwen3-4B-Inst | 3,384 | 2,544 | 5,928 | 174 | 0.858 |

`count × current` was **not regenerated**: it is the registered §12.2 ladder
screen, read only. The §12.1 cap set supplies the `current`-stem B-solo and
A+B fixture baseline, likewise read only. Seeds: `fsscreen:gen:v1`, root
202608200, derived from stage, model id, prompt hash and draw index; one draw
per cell; each model's own selected cap (512 for all four).

**The stem is obeyed** — 71–89 % of floored answers land in the 60–120 band. It
is not an instruction the models ignore.

---

## 3. The §2.4 reference criterion

Families carrying a rung inside the 0.10 caliper of A **and** at solo vacuity
≤ 0.10, **at the same severity**. Three required, on all four models.

| model | count × current | count × floored | candidate × current | candidate × floored |
|---|---|---|---|---|
| E2B | 0 | 2 (RF1,RF3) | **3** (CL7,CR6,CR7) | 2 (CR6,CR7) |
| E4B | 0 | 2 (RF1,RF6) | **4** (CL7,CR4,CR6,CR7) | **4** (CL7,CL8,CR4,CR7) |
| Qwen3-4B | 0 | 2 (RF6,RF7) | **5** (CL1,CL7,CR4,CR6,CR7) | 2 (CR4,CR6) |
| Qwen3-4B-Inst | 0 | 2 (RF2,RF8) | 2 (CL1,CR6) | **5** (CL7,CL8,CR4,CR6,CR7) |

**On the point estimates, no single cell meets the criterion on all four
models.** `candidate × current` meets it on three of four; `candidate ×
floored` on two of four. Every model has *some* candidate configuration that
meets it; no one configuration serves every model.

### The point estimates must not be read at one-family resolution

24 topics, one draw. Topic-clustered bootstrap, 1,000 resamples:

| model | cell | point | 90 % interval | P(≥3 families) |
|---|---|---:|---|---:|
| E2B | count × current | 0 | [0, 1] | **0.001** |
| E4B | count × current | 0 | [0, 0] | **0.000** |
| Qwen3-4B | count × current | 0 | [0, 1] | **0.000** |
| Qwen3-4B-Inst | count × current | 0 | [0, 1] | **0.000** |
| E2B | count × floored | 2 | [0, 3] | 0.054 |
| E4B | count × floored | 2 | [0, 3] | 0.221 |
| Qwen3-4B | count × floored | 2 | [0, 4] | 0.461 |
| Qwen3-4B-Inst | count × floored | 2 | [0, 3] | 0.250 |
| E2B | candidate × current | 3 | [1, 3] | 0.410 |
| E4B | candidate × current | 4 | [2, 4] | 0.774 |
| Qwen3-4B | candidate × current | 5 | [2, 6] | 0.884 |
| Qwen3-4B-Inst | candidate × current | 2 | [1, 4] | 0.517 |
| E2B | candidate × floored | 2 | [2, 5] | 0.827 |
| E4B | candidate × floored | 4 | [2, 5] | 0.879 |
| Qwen3-4B | candidate × floored | 2 | [2, 5] | 0.813 |
| Qwen3-4B-Inst | candidate × floored | 5 | [2, 5] | 0.893 |

**A caveat on the bootstrap that matters.** For three cells the bootstrap's
P(≥3) sits *above* the point estimate's own verdict (E2B and Qwen3-4B at
`candidate × floored`: point 2, P(≥3) ≈ 0.82). A count of families crossing a
threshold is not an unbiased statistic under resampling — duplicated topics make
cell rates more extreme and push marginal families across the caliper more often
than the data warrant. **P(≥3) should be read as an optimistic bound, not as a
probability.** The one thing it establishes cleanly is the contrast: 0.000–0.001
for `count × current` against 0.41–0.89 for every candidate cell. That gap is far
larger than the bias.

### Sensitivity map — a map only

Registered values are caliper 0.10 and threshold 20 words; **this screen changed
neither**, and no result below was used to select either.

`count × current` returns 0 in every cell of the grid except at T = 10, where
lowering the vacuity threshold rather than the caliper admits 3 (Qwen3-4B) and
1 (Qwen3-4B-Inst). `candidate × current` is **flat in T** — E2B returns 3 at
every threshold, E4B 3–4 — because the candidates produce few short answers, so
their vacuity barely moves with the threshold. That insensitivity is itself
evidence: the candidate result is not a threshold artifact. The candidate cells
are sensitive to the *caliper*, as any matching criterion must be.

---

## 4. The §2.4 B-side criterion

B-solo vacuous share of passes ≤ 0.10 under `floored`, on all four models.

| model | stem | B-solo compliance | vacuous share of B passes | B-solo med words | A+B med words | D(B←A) raw | D(B←A) ≥20 w only |
|---|---|---:|---:|---:|---:|---:|---:|
| E2B | current | 0.792 | 0.474 | 25 | 67 | +0.375 | +0.250 |
| E2B | **floored** | 0.458 | **0.000** | 86 | 94 | +0.208 | +0.208 |
| E4B | current | 0.750 | 0.389 | 31 | 92 | +0.333 | +0.230 |
| E4B | **floored** | 0.667 | **0.000** | 83 | 93 | +0.375 | +0.375 |
| Qwen3-4B | current | 0.333 | 1.000 | 8 | 20 | +0.125 | −0.071 |
| Qwen3-4B | **floored** | 0.167 | **0.000** | 57 | 46 | +0.000 | −0.007 |
| Qwen3-4B-Inst | current | 0.750 | 0.944 | 8 | 25 | +0.042 | −0.333 |
| Qwen3-4B-Inst | **floored** | 0.250 | **0.167** | 53 | 52 | −0.167 | −0.199 |

The `current` rows reproduce the 2026-08-20 diagnostic exactly, which
cross-checks the pipeline.

**Criterion met on three of four models.** Qwen3-4B-Instruct misses at 0.167.

**The stem does what it was proposed to do, and more.** B-solo vacuous share
falls from 0.39–1.00 to 0.00–0.17. Median B-solo answers go from 8 words to 53
on Qwen3-4B-Instruct and from 25 to 86 on E2B. And the length confound in the
primary estimand largely disappears: under `floored` the raw and ≥20-word
estimates of D(B←A) **converge** (+0.208/+0.208, +0.375/+0.375,
0.000/−0.007, −0.167/−0.199), where under `current` they differed by up to
0.375 and reversed sign on both Qwens. The collider caveat still attaches to the
restricted column, but under `floored` there is almost nothing left for it to
bite on.

---

## 5. Attribution — and the finding that decides it

### FORM alone is sufficient and safe

`candidate × current` clears three families on E2B, four on E4B, five on
Qwen3-4B, and two on Qwen3-4B-Instruct, with no change to any prompt and no
effect on any operating point. Every registered constant, band and grid keeps
its meaning.

### STEM alone is insufficient

`count × floored` returns exactly 2 families on all four models, with P(≥3)
between 0.05 and 0.46. It moves the registered pool substantially — from a
decisive 0 to a near-miss 2 — but does not reach three on any model.

### STEM is not merely insufficient; on the two Qwens it is fatal

This is the result that decides the attribution, and it was not visible in the
criterion table.

**A curve (n\*), band [0.50, 0.85]**

| model | stem | n=1…8 | eligible | n\* |
|---|---|---|---|---|
| E2B | current | .33 .38 .46 .67 .50 .42 .46 .42 | 2/8 | 4 |
| E2B | floored | .62 .67 .50 .38 .58 .62 .58 .38 | 6/8 | 2 |
| E4B | current | .67 .54 .67 .79 .62 .58 .42 .50 | 7/8 | 1 |
| E4B | floored | .79 .79 .79 .88 .92 .58 .58 .50 | 6/8 | 1 |
| Qwen3-4B | current | .71 .62 .46 .50 .42 .42 .25 .17 | 3/8 | 1 |
| Qwen3-4B | floored | .96 .54 .46 .71 .58 .58 .38 .25 | 4/8 | 4 |
| Qwen3-4B-Inst | current | .92 .92 .71 .62 .46 .29 .25 .12 | 2/8 | 3 |
| Qwen3-4B-Inst | floored | 1.00 1.00 .92 .88 .62 .38 .50 .33 | 2/8 | 5 |

**B curve (m\*), band [0.60, 0.95]**

| model | stem | m=7 | m=8 | m=9 | m=10 | eligible | m\* |
|---|---|---:|---:|---:|---:|---|---|
| E2B | current | .83 | .88 | .83 | .96 | 3/4 | 7 |
| E2B | floored | .50 | .46 | .62 | .75 | 2/4 | 10 |
| E4B | current | .67 | .83 | .83 | .92 | 4/4 | 8 |
| E4B | floored | .42 | .67 | .71 | .88 | 3/4 | 10 |
| Qwen3-4B | current | .25 | .58 | .54 | .75 | 1/4 | 10 |
| **Qwen3-4B** | **floored** | .04 | .17 | .21 | .33 | **0/4** | **`FOCAL_RANGE_EXHAUSTED`** |
| Qwen3-4B-Inst | current | .71 | .79 | .92 | .88 | 4/4 | 8 |
| **Qwen3-4B-Inst** | **floored** | .17 | .25 | .42 | .54 | **0/4** | **`FOCAL_RANGE_EXHAUSTED`** |

**Under the floored stem both Qwen replications terminate at Gate 2.** This is
the risk Amendment A §5.3 predicted, realised on exactly the two models where
the reference failure is decisive.

The mechanism is not subtle and follows from the diagnostic: B is
length-monotone, so forcing length makes it strictly harder. It is robust for
Qwen3-4B — best value 0.33 against a 0.60 floor, a gap of 6.5 topics of 24 — and
**marginal for Qwen3-4B-Instruct**, whose best value 0.54 is only 1.5 topics
below the floor and should not be treated as settled.

Note also that even where the stem does not exhaust the grid it pushes m\* to
**m = 10, the most permissive rung the grid contains**, on all three of E2B,
E4B and Qwen3-4B — leaving no headroom in the direction the stem pushes.

### Verdict on attribution

| | reference criterion | B-side criterion | operating point |
|---|---|---|---|
| FORM alone | 3 of 4 models | not addressed | **unharmed** |
| STEM alone | 0 of 4 models | 3 of 4 models | **breaks both Qwens** |
| FORM + STEM | 2 of 4 models | 3 of 4 models | **breaks both Qwens** |

**FORM is the factor to adopt. STEM as specified is not adoptable.**

---

## 6. What this changes, and what it does not

### Decisions the screen supports

1. **Amendment B (reference form) is supported and should proceed** — with the rate families CR7, CR4, CR6 as the recommended set. They meet the conjunction the registered pool fails 0-of-64, they are model-portable on one shared ladder, and they leave every operating point untouched. Adoption must happen **before Gate 1**, because new predicates and CR6's new numerator change the canonical verifier hash and re-open §10.2.
2. **Amendment A (prompt stem) should not be adopted as specified.** It achieves its stated purpose — B-side vacuity essentially eliminated, and the length confound in D(B←A) removed — at the cost of terminating both Qwen replications at Gate 2. That is not a trade worth taking to keep a diagnostic clean.
3. **If Amendment A is pursued, it needs an extended focal grid**, and that requires its own screen. Pooled max-word-length distributions under `floored` suggest the band could be restored around m = 10–12 for three models and m ≈ 11+ for Qwen3-4B, but that is an extrapolation from text generated under other severities and establishes nothing. It is a hypothesis for a screen, not a result.
4. **B's own length-monotonicity remains the deepest unfixed problem.** B is the primary outcome and it is a budget constraint; no reference redesign touches that. The screen shows the stem *can* neutralise it and shows what that costs.

### What the screen cannot decide

- **Whether the pre-screen predicts Gate 2 and Gate 3.** Everything here is 24 pre-screen topics at one draw. §12.3 re-measures on the disjoint 96 solo-calibration topics at M = 4, and §13.2 admits against *that*. This screen has never been shown to predict it, and its one-family-resolution instability argues it may not. **The candidate families must clear the conjunction on the calibration set before anything is adopted on their account.**
- **The A-versus-reference correlation ρ.** Still `BLOCKED`, exactly as check C12 records. It dominates the §16.3 allocation decision — at ρ = 0.75 every allocation passes even at φ = 0.65, at ρ = 0.3 nothing in the menu passes once φ ≥ 0.45 — and only a v4 stage carrying two composed cells with the same outcome constraint on the same blocks can supply it. This screen carries no composed reference cells and does not supply it.
- **Whether φ at M = 4 on v4 cells matches the pilot's M = 2 estimate** (0.556 and 0.441, both above the registered [0.27, 0.37]).
- **Anything at all about confirmatory behaviour.** No confirmatory data exist.

---

## 7. If the redesign fails on the calibration set

The screen did **not** fail on the same bimodality — that is the one clear
positive result, and the candidate cells break the pattern that made the
registered pool fail 0-of-64. But the calibration set is the test that counts,
and if the candidates fail there, the two remaining options are unchanged:

1. **Change the outcome constraint's structural class.** B is a length-monotone
   budget and it is the primary outcome. A reference pool matched to A while B
   remains budget-class leaves the primary estimand carrying a length channel
   that no reference fixes. Replacing or supplementing B with a production-class
   outcome addresses the problem at its source, and is the larger amendment.
2. **Accept the reduced design of §8.6 deliberately** — 2 solo and 2 composed
   cells, 4 per block — with L3 withheld **by design** and the reason recorded,
   rather than reached as a fallback nobody chose. §13.5 already makes Gate 3
   non-terminal precisely so this is a recorded decision and not a dead end.

---

## 8. Artifacts

| path | contents |
|---|---|
| `reports/fs_screen_v4/screen_protocol.json` | the frozen protocol, hash `98f8ee0d…` |
| `reports/fs_screen_v4/results.json` | machine-readable readouts, all cells |
| `reports/fs_screen_v4/REPORT.md` | this document |
| `evidence/fs-screen-v4/<model>/screen-cap512/` | 13,392 scored rows and per-model reports |
| `docs/evidence_manifest_v4.json` | content manifest of registered v4 evidence |
| `user-notes/DCI1_v4_amendment_A_prompt_stem.md` | Amendment A draft — **not adopted** |
| `user-notes/DCI1_v4_amendment_B_reference_pool.md` | Amendment B draft — **not adopted** |
