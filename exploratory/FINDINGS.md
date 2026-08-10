# Findings — cheapest informative DCI probe

Run `runs/stageB_20260810T183206Z` · `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f` ·
2× RX 7900 XTX / ROCm 7.2 · 960 generations, 16.4 min, 0 technical failures.

**EXPLORATORY_NO_EVIDENCE.** Nothing here authorises a freeze, and every interval
is a descriptive bootstrap percentile with no multiplicity control.

---

## The one-paragraph answer

Under compositional load, adding B ("each sentence strictly longer than the last")
*does* impair compliance with A ("write exactly 4 sentences") more than three of
its four matched references do — but **only when B is stated before A**
(τ ≈ +0.27 to +0.30, bootstrap CIs excluding 0), and **not when A is stated first**
(τ ≈ +0.02 to +0.05, CIs spanning 0). The fourth reference, `S_SEMICOLON`, impairs
A about twice as strongly as B does in both orders, so on v19's own conservative
`min_j τ_j` headline B fails to beat every reference and the estimate is negative.
All of this is accounted for by a single failure mode that is not specific to B:
the answer collapsing into one clause-chained sentence.

> **Round 2 correction.** The r = 0.998 figure originally quoted here is
> **withdrawn** — collapse is a strict subset of A-failure, so that correlation
> was partly definitional. See Round 2 §0. The conclusion survives on stronger
> evidence (a mode decomposition plus a causal intervention), not on that number.

**So: directional interference of this kind is real and measurable, but this run
gives no support for it being specific to the registered (A, B) pair.**

---

## 1. Observations — what the stored data directly show

### Primitive competence (isolated, one instruction)

| Constraint | n | failure rate | mean tokens | truncated |
|---|---|---|---|---|
| **A** (exactly 4 sentences) | 60 | **0.000** | 74 | 0 |
| B (increasing lengths) | 60 (50 scorable) | 0.320 | 407 | 25 |
| C_L3 (initial letter S) | 60 | 0.283 | 84 | 0 |
| C_O2 (alphabetical starts) | 60 | 0.650 | 72 | 0 |
| C_W3 (≥8 words/sentence) | 60 | 0.000 | 157 | 0 |
| S_SEMICOLON (semicolon each) | 60 | 0.000 | 178 | 0 |

A is at **0/60** in isolation. The model is fully competent at the target, so any
A-failure under load is caused by the load, not by inability.

### A-failure under load k=5, by arm and order (n = 60 each)

| arm | `o_A` (A first) | `o_Q` (added first) | order Δ |
|---|---|---|---|
| **B** (focal) | 0.067 | **0.317** | **+0.250** |
| C_L3 | 0.017 | 0.017 | 0.000 |
| C_O2 | 0.050 | 0.050 | 0.000 |
| C_W3 | 0.033 | 0.017 | −0.016 |
| S_SEMICOLON | 0.633 | 0.567 | −0.066 |

**Order moves only the focal arm.** Every reference is flat to within ±0.07.

### Paired contrasts τ_j (positive = B costs more A-compliance)

| reference | `o_A` τ [95% CI] | `o_Q` τ [95% CI] | pooled τ [95% CI] |
|---|---|---|---|
| C_L3 | +0.050 [0.000, 0.100] | **+0.300 [0.166, 0.450]** | +0.175 [0.092, 0.258] |
| C_O2 | +0.017 [−0.033, 0.067] | **+0.267 [0.117, 0.417]** | +0.142 [0.067, 0.225] |
| C_W3 | +0.033 [−0.033, 0.100] | **+0.300 [0.166, 0.450]** | +0.167 [0.083, 0.250] |
| S_SEMICOLON | **−0.567 [−0.767, −0.367]** | **−0.250 [−0.483, 0.000]** | −0.408 [−0.592, −0.225] |

Aggregates (uniform weights, descriptive only):

| order | focal | weighted reference | τ_weighted [95% CI] | **τ_min over references** |
|---|---|---|---|---|
| `o_A` | 0.067 | 0.183 | −0.117 [−0.188, −0.042] | −0.567 (S_SEMICOLON) |
| `o_Q` | 0.317 | 0.163 | +0.154 [+0.004, +0.321] | −0.250 (S_SEMICOLON) |
| pooled | 0.192 | 0.173 | +0.019 [−0.073, +0.115] | −0.408 (S_SEMICOLON) |

### Diagnostics

- **Technical failures: 0 / 960.** No OOM, no backend error, no empty generation.
- **Truncation: 0 / 600 contrast rows.** Every one ended with EOS. Truncation
  cannot explain anything in Stage B. (It explained a great deal in Stage A —
  see §3.)
- **Unscorable: 10 / 960**, all `primitive/B`. Carried as null, never as failure.
- **Length**: B's answers are the longest (173 / 220 tokens vs 53–103 for
  references) — but `S_SEMICOLON`, with the *highest* failure rate, writes *short*
  answers (79 / 82). Length does not order the failure rates.

### The failure-mode decomposition

| order | arm | A-failure | collapse rate (≤2 segments) | residual | mean `;` |
|---|---|---|---|---|---|
| o_A | B | 0.067 | 0.033 | 0.033 | 0.13 |
| o_A | C_L3 | 0.017 | 0.000 | 0.017 | 0.00 |
| o_A | C_O2 | 0.050 | 0.000 | 0.050 | 0.00 |
| o_A | C_W3 | 0.033 | 0.017 | 0.017 | 0.15 |
| o_A | S_SEMICOLON | 0.633 | 0.600 | 0.033 | 2.95 |
| o_Q | B | 0.317 | 0.300 | 0.017 | 0.58 |
| o_Q | C_L3 | 0.017 | 0.000 | 0.017 | 0.00 |
| o_Q | C_O2 | 0.050 | 0.000 | 0.050 | 0.00 |
| o_Q | C_W3 | 0.017 | 0.000 | 0.017 | 0.00 |
| o_Q | S_SEMICOLON | 0.567 | 0.517 | 0.050 | 2.92 |

88 of 106 A-failures (83%) are collapses. Residuals are 0.017–0.050 everywhere,
and **B's residual is not larger than the references'** — C_O2's is the largest
at 0.050.

> **Round 2 correction.** A correlation coefficient between these two columns was
> originally quoted here and is **withdrawn as partly definitional** (collapse ⊂
> A-failure). The informative content is the residual column: non-collapse
> failure is flat at 0.017–0.050 across every cell while total failure spans
> 0.617, so the between-arm signal lives in the collapse mode. See Round 2 §0.

---

## 2. Interpretation — what those observations plausibly mean

There is one dominant causal path, and it is **not** pair-specific:

```
instruction that rewards long, clause-chained prose
      → model emits ≤2 sentences instead of 4
            → "exactly 4 sentences" fails
```

B enters this path only when it is read first. The reading that fits the data:
stating "write exactly 4 sentences" first anchors a structural plan, and B then
modulates the lengths of four already-committed sentences; stating B first starts
an escalating-length plan that the later count instruction does not restructure.
That is a **primacy effect on plan formation**, and it is genuinely
pair-asymmetric — order moves the focal arm and no reference.

`S_SEMICOLON` walks the same path by construction: "a semicolon in every
sentence" is most cheaply satisfied by chaining clauses, and clause-chains are
one sentence. It was selected, blind to outcomes, as a *reference* representing
generic added load. It is nothing of the sort.

---

## 3. Alternative explanations, and what this run says about each

| Explanation | How it could produce the result | Evidence here | Verdict |
|---|---|---|---|
| **Output truncation** | B implies a geometrically growing answer; censoring drops final sentences and breaks the count | **Was the dominant artefact in Stage A**: B's isolated rows averaged exactly 180.0 tokens, 8/8 at the cap, and focal A-failure read 0.69. Raising the cap to 512 dropped it to 0.125. In Stage B, 0/600 contrast rows truncated; all ended with EOS. | **Confirmed real at 180; fully eliminated at 512.** Not an explanation for Stage B. |
| **One anomalous reference drives the comparison** | A reference that is itself a strong interferer masks or reverses the aggregate | `S_SEMICOLON` fails at 0.60 pooled vs 0.017–0.050 for the other three. It alone turns τ_weighted from ≈ +0.17 into ≈ +0.02 and makes τ_min negative. | **Confirmed and decisive.** The single most important finding about the *method*. |
| **Generic compositional load** | Any added instruction costs A-compliance | Three references cost essentially nothing (0.017–0.050) at the same instruction count. So load per se is not sufficient. | **Weakened.** Load alone does not do it. |
| **Mechanism-class, not pair-specific** | Any clause-chaining-inducing instruction impairs a sentence-count target | Mode decomposition (non-collapse failure flat at 0.017–0.050 across cells); B and S_SEMICOLON fail by collapsing while ordinary references fail by overshooting. **Round 2 confirmed this causally**: blocking collapse takes B's excess to 0.000. | **Confirmed in Round 2.** |
| **Prompt-order / salience** | Position of B relative to A drives the effect | +0.250 on the focal arm; ±0.00–0.07 on every reference | **Confirmed as a large moderator**, and itself pair-asymmetric |
| **Response-length pressure** | Longer answers drift off the count | B is longest and fails moderately; S_SEMICOLON is short and fails most; C_W3 is mid-length and fails least | **Weakened.** Length does not order the outcomes. |
| **Unmatched reference difficulty** | B is simply harder than the references | Isolated difficulty is nearly orthogonal to interference: C_O2 is hardest alone (0.65) but interferes least (0.05); S_SEMICOLON is trivial alone (0.00) but interferes most (0.60) | **Weakened for B**, but it exposes that construction-time matching does not match on what matters |
| **Verifier error** | The segmenter mis-splits | 0/600 re-derivation mismatches; human reading agrees on every inspected case; 4 sentences each containing a semicolon score `full` | **Not supported.** |
| **Verifier coupling missed at construction** | A reference whose verifier entangles with A's | `S.COUPLING` scored `S_SEMICOLON` at **0.00** coupling with A on the model-free response bank, yet it is the strongest interferer | **Confirmed gap in the construction procedure** — the authored bank contains no clause-chained answers, so the audit could not see this |
| **Accidental incompatibility** | A and B cannot both hold | All 36 pairs pass `pair_verdict`; 41/60 `o_Q` focal rows do produce exactly 4 sentences | **Not supported.** |
| **Implementation bug** | Mis-pairing, mismatched counts, wrong scored constraint | 13 independent structural checks pass; τ recomputed from raw JSONL by a script importing nothing from the analysis module matches to 1e-9 | **Not supported.** |

---

## 4. Currently supported conclusions

1. The model is fully competent at A in isolation (0/60), so load causes the failures.
2. Under `o_Q`, B impairs A substantially more than `C_L3`, `C_O2` and `C_W3` do
   (+0.27 to +0.30, CIs excluding 0) at matched instruction count.
3. Under `o_A` that advantage is small and CI-consistent with zero.
4. On v19's conservative `min_j τ_j` headline, **B does not beat every reference
   in either order**, because `S_SEMICOLON` beats B.
5. A single failure mode — sentence collapse — accounts for essentially all
   between-arm variation, and B has no excess residual over it. *(The r = 0.998
   figure originally cited here is **WITHDRAWN as partly definitional**; the
   claim now rests on the mode decomposition and Round 2's intervention.)*
6. The reference-construction procedure as run admitted a reference that is a
   stronger directional interferer than the focal, and its construction-time
   coupling audit scored that reference 0.00.
7. The 180-token protocol cap materially distorts this pair.

## 5. Unsupported conclusions

- **That directional interference is specific to the (A, B) pair.** The data
  point the other way.
- **That τ > 0 generalises.** It is order-conditional and reference-conditional.
- Any claim about other pairs, other models, other loads, other wordings, or
  other decoding settings — none were varied.
- Any inferential claim. n = 20 task clusters, percentile bootstrap, no
  multiplicity control, exploratory throughout.
- That `S_SEMICOLON` is a "bad" reference in the protocol's formal sense. It
  passed every criterion the repository defines. That is the point.

---

## 6. Stage C decision — **not run**

Stage C would add ~30 more task clusters of the identical design. Declined:

- The `o_Q` contrasts against three references already have bootstrap CIs
  excluding zero, and the `S_SEMICOLON` reversal (−0.41 pooled) is far too large
  to be a sampling accident. Sign and rough magnitude are established.
- The remaining uncertainty is **mechanistic, not statistical**: is B special, or
  is it one member of a class of collapse-inducing instructions? Sampling the
  same five arms more finely cannot separate those — both predict the same
  numbers. *(This sentence originally justified the point by the r = 0.998
  relation; that statistic is **WITHDRAWN**. The point stands on the mode
  decomposition instead.)*
- The experiment in §7 addresses that question directly for roughly a third of
  Stage C's compute.

## 7. The single cheapest next experiment

**Put B on a graded collapse curve and test whether it sits above it.**

- **Competing hypotheses.**
  *H1 (pair-specific).* B impairs A through something specific to the B→A
  direction, over and above the collapse it induces.
  *H2 (mechanism-class).* A-failure is a function of induced sentence-collapse
  alone; B is an unremarkable point on that function.
- **The one factor changed:** the identity of the added instruction, swept across
  ~7 constraints already in the registry that span the collapse range — e.g.
  `S_SEMICOLON`, `S_TWOCOMMA`, `S_COMMA12`, `S_MINWORDS15`, `S_MINWORDS30`,
  `C_W3`, plus **B** itself.
- **Fixed:** A, the background set S, load k=5, order `o_Q` only (the sensitive
  one), the same 20 pilot tasks, the same model/revision/decoding, the same
  verifier, the same 512-token cap.
- **Primary measurement:** A-failure rate. **Mediator:** collapse rate (≤2
  segments). Fit A-failure on collapse across the non-B arms; B's signed residual
  from that fit is the estimate.
- **Expected outcomes.** Under H2, B's residual is within the scatter of the
  other arms (this run: 0.017–0.050) and the curve is a straight line through the
  origin. Under H1, B sits clearly above the line fitted to everything else.
- **Cost:** 7 arms × 20 tasks × 3 replicates × 1 order = **420 generations,
  ≈ 8 minutes** on one 7900 XTX — cheaper than Stage B.
- **Why it dominates.** More samples (Stage C) cannot separate H1 from H2. More
  models or more pairs multiply cost by the number of models or pairs while
  leaving the same confound in place, and would inherit a reference set now known
  to contain a stronger interferer than the focal. This experiment reuses the
  existing runner unchanged — only the arm list moves — and it is the question on
  which everything downstream depends: if H2 holds, the DCI estimand as currently
  operationalised is measuring a segmentation-collapse mechanism shared across a
  constraint class, and the reference-admission procedure needs a collapse-aware
  screen before any confirmatory run is worth its compute.

---

## Artifacts

| | |
|---|---|
| raw generations | `runs/stageB_20260810T183206Z/generations.jsonl` (960 rows, 2.7 MB) |
| tables | `analysis/table_{conditions,primitives,contrasts,aggregate,mechanism}.csv` |
| figures | `analysis/fig1_failure_rate_by_arm.png` · `fig2_paired_contrasts.png` · `fig3_per_task_paired.png` · `fig4_length_diagnostic.png` · `fig5_collapse_mechanism.png` |
| headline | `analysis/headline.json` |
| audit | `audit/audit_cases.md` (43 cases) · `audit/human_verdicts.md` · `audit/audit_sample.json` |
| independent check | `python verify_independently.py runs/stageB_20260810T183206Z` |
| selection trail | `selection_audit.json` |

---
---

# Round 2 — deep dive: what phenomenon is this actually?

Three runs: `stageB` (960, round 1), `stageD2_anticollapse` (480),
`stageD3_semicolon` (400). 1,840 generations total, **0 technical failures**.
Still `EXPLORATORY_NO_EVIDENCE`.

## 0. A correction to Round 1

Round 1 reported **r = 0.998** between A-failure and "sentence collapse" and read
it as mechanistic. **That statistic is withdrawn.** A-failure is
`observed ≠ 4` and collapse is `observed ≤ 2`, so collapse is a *strict subset*
of failure — verified directly, 0 collapse-but-passing rows in 600. A high
cell-level correlation was partly guaranteed by the nesting and could not, on its
own, establish a mechanism.

What replaces it is stronger, because it is a decomposition rather than a
correlation, and because it was then tested by intervention.

## 1. What behavioural phenomenon did we actually discover?

**A specific, blockable output strategy: the model answers with one
clause-chained sentence instead of the four it was asked for.** Instructions
differ in how often they push it into that strategy, and A-failure follows.

Three non-definitional facts establish this:

**(a) Arms differ in *which* failure mode they take, not just how much they fail.**
Ordinary references fail by *overshooting* — 8 of their 11 failures are 5
sentences, 2 are 6. B and `S_SEMICOLON` fail by *collapsing* to one. Direction is
not something nesting can manufacture.

**(b) Failure that is not collapse is flat.** Across all ten arm×order cells,
`P(failure ∧ ¬collapse)` sits in 0.017–0.050 — a range of **0.033** — while total
failure ranges over **0.617**. Essentially all between-arm signal is in the one
mode.

**(c) Blocking the strategy removes the failure.** One clause added to the system
message (`Write each sentence on its own line.`), identical across arms, with the
numbered constraint list byte-identical and load unchanged at k=5:

| | baseline | + scaffold | Δ [95% CI] |
|---|---|---|---|
| B `o_Q` | 0.275 | **0.050** | −0.225 [−0.375, −0.100] |
| `S_SEMICOLON` `o_A` | 0.675 | 0.325 | −0.350 [−0.500, −0.200] |
| `S_SEMICOLON` `o_Q` | 0.575 | 0.325 | −0.250 [−0.400, −0.100] |
| `C_L3` (control) `o_A` | 0.025 | 0.050 | +0.025 |
| `C_L3` (control) `o_Q` | 0.000 | 0.050 | +0.050 |

The control did **not** improve, so this is not a scaffold that makes A easy for
everyone — it removes one route, and only the arms using that route recover.

## 2. Which explanation best accounts for it?

**H2, the shared structural failure-mode mechanism.** For B it is sufficient:
its entire excess over an ordinary reference is mediated by collapse.

Paired excess over `C_L3` (figure: `fig_intervention_excess.png`):

| arm / order | baseline | + scaffold |
|---|---|---|
| **B `o_Q`** | **+0.275** [0.150, 0.425] | **0.000** [−0.075, +0.075] |
| B `o_A` | 0.000 | −0.025 |
| `S_SEMICOLON` `o_A` | +0.650 | +0.275 [0.150, 0.425] |
| `S_SEMICOLON` `o_Q` | +0.575 | +0.275 [0.100, 0.475] |

And the order effect is mediated too: B's `o_Q` − `o_A` gap falls from **+0.250
to +0.025** under the scaffold.

## 3. Which alternatives are weakened or ruled out?

| Hypothesis | Status | Decisive evidence |
|---|---|---|
| **H1 pair-specific interference** | **Falsified by its pre-registered criterion** | B's excess over `C_L3` → 0.000 once collapse is blocked. Nothing B-specific survives. |
| **H3 order as an independent mechanism** | **Ruled out**; survives only as a trigger | *Recency ruled out by sign*: under `o_Q`, A is the **more recent** instruction and fails **more**. It is primacy — whichever instruction is read first sets the structural plan. And the gap vanishes under the scaffold. |
| **H4 task susceptibility** | **Weakened** | B and `S_SEMICOLON` failure sets overlap **less** than independence predicts (Jaccard 0.131 vs 0.170 expected; P(`S_SEMICOLON` fails ǀ B fails) = 0.478 against a 0.600 base rate). Within-task replicates are 40% mixed for B `o_Q` — a stochastic strategy choice, not a task property. |
| **H5 definitional artefact** | **Confirmed for the statistic, resolved for the claim** | r = 0.998 withdrawn; replaced by the mode decomposition and the intervention. |
| Truncation | **Ruled out** | 0/600 truncated in Stage B; all EOS. (It *was* real at the protocol's 180-token cap — see Round 1.) |
| Response length | **Ruled out as the driver** | B's `o_Q` failures are **shorter** (180 tokens) than its successes (238). `S_SEMICOLON` has the shortest answers and the highest failure. |
| Verifier error | **Ruled out** | 0/600 re-derivation mismatches; human reading agrees; 4 sentences each containing a semicolon score `full`. |

## 4. What is descriptive, correlational, and causal?

- **Descriptive:** failure rates, mode taxonomy, sentence-count distributions,
  punctuation profiles, overlap and concentration statistics.
- **Correlational:** the association between collapse and A-failure (and it is
  partly definitional — §0); the association between semicolon use and collapse.
- **Causal, within this model/task/decoding setting:** the **scaffold**
  manipulation (D2) and the **order** manipulation, because both are randomised-
  by-design interventions on matched units with everything else held fixed. D3's
  variant comparison is causal for the *instruction* contrast but the variants
  are not otherwise matched on difficulty, so it identifies *which property
  matters*, not an effect size.

## 5. Does the pair-specific DCI hypothesis survive?

**No, not for this pair in this setting.** B does impair A more than ordinary
references — but only under `o_Q`, and that entire advantage is mediated by a
strategy B does not own and does not induce most strongly. Once the strategy is
blocked, B is indistinguishable from an ordinary added instruction (excess
0.000). Under v19's conservative `min_j τ_j` headline B never beat its own
reference panel in either order.

The honest restatement: **what looks like pair-specific directional interference
is, here, a shared output-strategy mechanism that several instructions can
trigger and that instruction *position* modulates.**

## 6. What does the `S_SEMICOLON` result imply?

Two things, one scientific and one methodological.

**Scientific (D3, pre-registered, explanation 2 selected):** the damage requires
a *per-sentence* requirement for a mark that can *stand where a sentence boundary
would*. Neither component alone suffices.

| arm | mark | scope | excess `o_A` | excess `o_Q` | collapse | mean periods |
|---|---|---|---|---|---|---|
| `S_SEMICOLON` | `;` | per-sentence | **+0.650** | **+0.525** | 0.65 / 0.55 | **2.10 / 2.45** |
| `U_FMT_SEMI2` | `;` | whole-text | +0.125 | +0.025 | **0.000** | 3.95 / 4.10 |
| `S_TWOCOMMA` | `,` | per-sentence | +0.025 | 0.000 | **0.000** | 4.15 / 4.28 |

`U_FMT_SEMI2` answers really do contain semicolons (93.8% carry ≥1) and keep 4.03
periods. `S_TWOCOMMA` demands two commas in *every* sentence and never collapses.
The mechanism is **substitution, not accumulation**: `S_SEMICOLON`'s *passes*
carry **more** semicolons (3.45) than its *failures* (2.63), differing in periods
(4.18 vs 1.42).

**Methodological:** a constraint admitted blind as a *reference for generic load*
was the strongest directional interferer in the panel, and it partially resists
even an explicit anti-collapse instruction (+0.275 residual). Reference panels
that are matched on construction can contain a stronger interferer than the
focal, which inverts the conservative headline.

## 7. Why did the construction-time coupling screen miss it?

**Because the failure mode does not exist in the support the screen is computed
over.** `S.COUPLING` is measured on an authored, model-free response bank.

| response structure | in coupling bank (64) | in probe corpus (264) | in model generations (960) |
|---|---|---|---|
| four normal sentences | 58 | 13 | 497 |
| n sentences containing semicolons | 6 | 37 | 64 |
| **one-sentence semicolon chain** | **0** | **0** | **120** |
| one-sentence run-on | 0 | 0 | 15 |
| over target (5–6) | 0 | 87 | 255 |
| 2–3 sentences | 0 | 125 | 8 |

The bank contains semicolons (6 texts) — but only *inside* well-formed
four-sentence answers, never replacing a boundary. 187 of the 264 probe-corpus
texts contain a semicolon and **none** is a chain. The screen was not wrong
arithmetically; its support omitted the one structure that couples the two
verifiers. Construction-time coupling also fails to rank the observed effects at
all: `S_SEMICOLON` scored **0.00** and interferes most; `C_O2` scored **0.40** and
interferes least.

*Exploratory methodological finding. The confirmatory procedure is not modified
from this worktree.*

## 8. The single most important unresolved question

**Is "collapse" one mechanism or a family?** The scaffold removes ~100% of B's
excess but only ~50% of `S_SEMICOLON`'s. Either the scaffold is a partial
manipulation that `S_SEMICOLON` resists more (it *was* less obeyed — mean
newlines 1.78 vs `C_L3`'s 3.00), or `S_SEMICOLON` has a second route to A-failure
that the scaffold does not touch. The current design cannot separate a
weak-manipulation explanation from a second-mechanism explanation.

## 9. Highest-information next experiment

**Strengthen the manipulation and see whether `S_SEMICOLON`'s residual survives.**
Same three arms, same tasks, one factor changed: scaffold *strength*, at three
levels — none / current soft clause / a hard structural scaffold (numbered
output lines, which the segmenter treats as separate segments and which cannot be
satisfied by a clause chain). Primary measurement: paired excess over `C_L3`;
mediator: collapse rate; manipulation check: mean newlines per arm.

- If `S_SEMICOLON`'s residual → 0 as compliance rises, collapse is **one**
  mechanism and D2 was simply under-powered as a manipulation.
- If the residual persists at full compliance, `S_SEMICOLON` has a **second**
  route, and the reference-admission procedure needs a screen for it specifically.

3 arms × 3 levels × 2 orders × 20 tasks × 2 reps = **720 generations, ≈13 min**.
This dominates a broader 5–7 arm sweep, which would characterise more instructions
against a mechanism we do not yet know is singular.

## Artifacts (round 2)

| | |
|---|---|
| forensics | `runs/stageB_.../forensics/` — `circularity_audit.json`, `failure_taxonomy.csv`, `failure_set_overlap.csv`, `order_transitions.csv`, `task_susceptibility.csv`, `replicate_repeatability.csv`, `concentration.json`, `coupling_bank_coverage.csv` |
| forensic packet | `runs/stageB_.../forensics/packet.md` (40 cases, 8 strata, within-stratum random) |
| intervention D2 | `runs/stageD2_anticollapse_.../analysis/` — `intervention_{cells,excess,modes,scaffold_effect}.csv`, `fig_intervention_excess.png` |
| intervention D3 | `runs/stageD3_semicolon_.../analysis/intervention_*.csv` |
| living record | `HYPOTHESES.md`, `DECISIONS.md` |

---
---

# Round 3 — verification, and a real verifier defect

No new generation. Three checks on the existing 1,840 generations: an
independent reanalysis, a blinded three-way sentence-count audit, and a
hand-labelled verifier stress corpus.

## R3.1 — Every headline reproduces (Step 1)

`reanalysis_standalone.py` imports nothing from `dci` or `dci_exploratory` and
re-implements segmentation from scratch. **70/70 checks pass**: primitive rates,
all arm×order failure rates, every τ_j and its bootstrap CI, sentence-count
distributions, the collapse taxonomy, order effects, D2 scaffold effects, D3
variant excesses, plus hand-checked arithmetic (Stage B / B / `o_Q` = 19/60;
D2 / B / `o_Q` / scaffold = 2/40).

Byte-level counterfactual checks also pass: focal and reference prompts differ on
exactly one line; `o_A` and `o_Q` differ only by swapping the first two
instructions, with preamble and background byte-identical; D2's user prompts are
**byte-identical** across scaffold conditions, with only the system message
differing and instruction count fixed at k=5.

*(One check initially failed — on my own arithmetic, not the data. The numbered
list is renumbered when instructions swap, so the swapped lines are never
byte-equal; the check now compares content with the positional numbering
stripped.)*

## R3.2 — The failures are genuine, but the verifier has a real defect (Steps 2–3)

**Blinded audit.** 175 cases exported with arm, condition, order and all verdicts
withheld; 43 counted against the blinded text before the key was opened.

| comparison | agreement |
|---|---|
| production verifier vs independent counter, **all 1,480 contrast rows** | **1,480 / 1,480 (100%)** |
| blinded manual count vs production | 34/43 (0.791) |
| blinded manual count vs independent | 34/43 (0.791) |

**All 9 disagreements have one cause**: both segmenters treat the full stop in
`a.m.`/`p.m.` as a sentence end, so *"Sales spike at 6 a.m. when others sleep."*
is counted as two sentences. The "independent" counter shares the bug because its
abbreviation list omitted `m` — **so on this specific point it was not
independent, and the 100% agreement above must be read with that caveat.**

**Stress corpus.** 31 hand-labelled items covering four-sentence outputs,
semicolon chains, comma chains, run-ons, merges, splits, newline/bulleted/
numbered layouts, abbreviations, quotations, decimals, initials and unusual
punctuation. All four (Y_A, Y_R) ground-truth combinations are covered.

| quantity | value |
|---|---|
| **E_A** target-verifier error rate | **0.207** (6 / 29 scorable) |
| **E_R** semicolon-verifier error rate | **0.000** (0 / 29) |
| **U_A** unscorable share | 0.065 |
| **U_R** unscorable share | 0.065 |
| **κ(A, R)** on this support | **−0.132** |
| **U_κ** 95% bootstrap | **[−0.375, +0.121]** |

All six A-errors are **over-splitting**: `a.m.` / `p.m.`, `Dr.` / `Mrs.`,
`approx.` / `e.g.`, initials `J. R.`, ellipses. The verifier is **correct on
every collapse-relevant structure** — all three semicolon chains, both comma
chains, the run-on, the merge, newline/bulleted/numbered layouts, and the crucial
*"four sentences each containing a semicolon"* case.

### Does the defect change anything? No — and it moves slightly the other way.

Recounting all 1,480 contrast rows with abbreviations protected changes 2.8–3.5%
of counts. The transitions are dominated by 5→4 and 6→4, i.e. the bug was
inventing **overshoot** failures, never collapses.

| quantity | as measured | abbreviation-corrected |
|---|---|---|
| τ(B − C_L3) pooled | +0.175 | **+0.183** |
| τ(B − C_O2) pooled | +0.142 | **+0.183** |
| τ(B − C_W3) pooled | +0.167 | +0.167 |
| τ(B − S_SEMICOLON) pooled | −0.408 | −0.392 |
| B order gap (`o_Q` − `o_A`) | +0.250 | **+0.267** |
| D2 B `o_Q` excess, baseline | +0.275 | +0.250 |
| D2 B `o_Q` excess, **scaffolded** | 0.000 | **+0.025** |
| D2 `S_SEMICOLON` excess, scaffolded | +0.275 | +0.325 |

**Every conclusion survives.** One refinement: the ~0.03 "non-collapse failure
baseline" reported in Round 2 is **largely the abbreviation artefact**, not model
behaviour — corrected, the ordinary references fail at ≈0.000.

## R3.3 — Correction to Round 2's coupling claim

Round 2 said the construction-time screen missed `S_SEMICOLON` **because its
support omitted the one-sentence chain**. Measured on a support that *does*
contain that mode, κ(A, R) = **−0.132 [−0.375, +0.121]** — still ≈ 0.

So the screen was not blind. It measures **verifier-error coupling**, which is a
different quantity from **behavioural interference** and could never rank it.
`S_SEMICOLON` does not make the two verifiers agree; it makes the *model* produce
a structure that fails A. The correct methodological finding is therefore
sharper than Round 2's: **the reference-admission procedure has no screen for
behavioural interference at all** — coupling is not a proxy for it, on any
support.

## R3.4 — Answers so far

1. **Which results reproduced?** All of them — 70/70 independent checks.
2. **Genuine behavioural failures?** **Yes.** Blinded manual counts agree with the
   verifier on every collapse case; the stress corpus shows E_A = 0 on all
   collapse-relevant structures. The verifier's only errors are over-splits that
   create false *overshoot*.
3. **Is the coupling audit valid on the relevant support?** It is *arithmetically*
   valid (κ ≈ 0 there too) but **not fit for the purpose it was being read for**.
   Verifier-error coupling ≠ behavioural interference.
4. **Verifier defect to record:** `E_A = 0.207` on structurally diverse text,
   entirely from abbreviation/initial/ellipsis over-splitting. Exploratory
   finding; the confirmatory implementation is untouched.

## R3.5 — Stopped here, per the stop conditions

The plan says to stop and report if human counts materially disagree with the
verifier. They **disagreed (9/43) but not materially** — every headline is
unchanged or slightly strengthened, as tabulated above. Because the disagreement
is nonetheless a real defect in a verifier the confirmatory pipeline also uses,
Steps 4–8 (sham control, scaffold ladder, instruction screen, N sweep,
cross-model) are **not started**: they would spend GPU time on a measurement
whose known defect the operator should decide about first.

Recommended handling before resuming: run the remaining steps with abbreviation
protection applied as a **reported sensitivity analysis** alongside the frozen
verifier, never as a silent substitution.

## Artifacts (round 3)

| | |
|---|---|
| independent reanalysis | `reanalysis_standalone.py` (70 checks) |
| blinded audit | `verifier_audit/blinded_cases.{jsonl,md}`, `KEY_DO_NOT_OPEN_FIRST.jsonl`, `human_counts.csv`, `three_way_counts.json` |
| stress corpus | `stress_corpus.py`, `verifier_audit/stress_corpus_results.json` |
| defect impact | `abbrev_impact.py` |

---
---

# Round 4 — measurement defect closed

No new generation. The Pair 3 sentence verifier was repaired in production,
certified, and every stored generation rescored.

## R4.1 — Defects found and closed

| # | Minimal reproducer | Root cause | Scientific consequence |
|---|---|---|---|
| 1 | `"Sales spike at 6 a.m. when others sleep."` → 2 | `SENTENCE_BOUNDARY` treats every `.` before whitespace as a sentence end | **F_A wrong.** Manufactured overshoot; compliant four-sentence answers recorded as violations |
| 2 | `"... or soufflés. 20 to 30 strokes ..."` → 3 not 4 | the *repair's own* ASCII-only trailing-token class fell back to the bare `s` and read it as an initial | would have suppressed real boundaries after any accented word |
| 3 | `"**Rain falls.** Water runs."` → 1 | boundary pattern allowed exactly **one** closer from `["”’]` | latent: 0 of 1,840 generations affected |

Defect 2 was found by the independent scanner, not by any test I wrote — the
instrument built to distrust the repair caught the repair.

Recorded but **not** changed: segments are kept only if they contain an ASCII
alphanumeric, so wholly non-Latin text is `unscorable`. Pre-existing, shared with
`word_tokens`, fails closed, out of scope.

## R4.2 — Repair and governance

`src/dci/verifiers/rules.py`: two closed abbreviation tables (titles never end a
sentence; medial abbreviations end one only before a capital), Unicode-aware
token matching, capital-only initials, ellipsis handling, widened closer class.
`docs/migration_ledger_patches.csv` gains `P13-sentence-abbreviations` recording
the scientific impact.

**Freeze state: pre-freeze, legitimately repairable.** No scientific freeze
exists — the only committed `freeze.json` is a `cpu_or_dry_run` dev_fast test
fixture. v19 is at Stage 1 with Stage 2 verifier certification pending, which is
exactly where this belongs. `verifier_source_sha256` and `plan_sha256` change;
`plan_sha256` is already in the regression comparator's allowlist.

## R4.3 — Measurement validation

| check | result |
|---|---|
| adversarial boundary fixtures | **63** cases, all pass |
| property + mutation tests | **43** cases (7 invariants, 15 mutations, 300 randomised) |
| gold corpus, production correct | **38/38** items (was 31/37 before repair) |
| independent scanner vs production, all generations | **1,840 / 1,840 (100%)** |
| **blinded human vs OLD verifier** | **12/22 (0.545)** |
| **blinded human vs CORRECTED verifier** | **22/22 (1.000)** |
| residual disagreements | **none** |

The blinded set was enriched for old-vs-corrected disagreements (33 of the 45),
so 22/22 is a hard test, not an easy one.

## R4.4 — Reliability and coupling, correctly named

| quantity | before repair | after repair |
|---|---|---|
| **E_A** | 0.207 (6/29) | **0.0000** (0/36) |
| **E_R** | 0.000 | **0.0000** (0/36) |
| **U_A / U_R** | 0.065 | 0.053 / 0.053 |

The E_A denominator is 36 of 38, not 38: `empty` and `punctuation_only` have true
count 0, are returned `unscorable`, and carry no verdict to be wrong about.

**κ, as the preregistration defines it** — the mean fraction of coupling *edits*
that flip **both** verdicts — is **0.400**, U_κ **[0.400, 0.400]** over 8
informative responses. It is a rate in [0,1] and cannot be negative.

> **Correction.** Round 3 reported "κ = −0.132 [−0.375, +0.121]". That was
> **Cohen's kappa on ground-truth agreement — a different statistic under the
> right name — and it is withdrawn.** The signed agreement coefficient is now
> reported separately as `agreement_phi` = +0.035.

U_κ is **degenerate**: every informative response flips on exactly 2 of 5 edits,
so the bootstrap has zero spread. That is a property of the *edit set*, not of
behaviour, and it is precisely what `dci.analysis.coupling_audit.kappa_is_degenerate`
exists to detect. It reinforces R3.3: **coupling is not a proxy for behavioural
interference on any support.**

## R4.5 — Rescore: old vs corrected

Counts changed on 45 of 1,480 contrast rows (3.0%); F_A flipped on 33.
Historical scores are preserved; `generations_rescored.jsonl` carries both.

| quantity | old | corrected |
|---|---|---|
| τ(B − C_L3) pooled | +0.175 | **+0.183** CI [+0.100, +0.275] |
| τ(B − C_O2) pooled | +0.142 | **+0.183** CI [+0.100, +0.275] |
| τ(B − C_W3) pooled | +0.167 | +0.167 CI [+0.092, +0.250] |
| τ(B − S_SEMICOLON) pooled | −0.408 | −0.392 CI [−0.583, −0.192] |
| B `o_A` / `o_Q` | 0.067 / 0.317 | **0.050 / 0.317** (gap +0.250 → **+0.267**) |
| D2 B `o_Q` excess, baseline | +0.275 | **+0.250** CI [+0.125, +0.400] |
| D2 B `o_Q` excess, scaffolded | 0.000 | **+0.025** CI [0.000, +0.075] |
| D2 `S_SEMICOLON` excess, scaffolded | +0.275 | **+0.325** CI [+0.150, +0.500] |

## R4.6 — Claim survival

| claim | verdict |
|---|---|
| **A** — B and `S_SEMICOLON` disproportionately collapse | **unchanged.** collapse: B 0.167, `S_SEMICOLON` 0.567, `C_L3` 0.000, `C_O2` 0.000, `C_W3` 0.008 |
| **B** — ordinary references fail by a *different mode* | **CHANGED, and the finding strengthens.** Under corrected scoring `C_L3` and `C_O2` have **zero** failures and `C_W3` has two. The "overshoot" failure mode reported in Round 2 was **the verifier defect**. Ordinary references do not fail by another mode; they essentially do not fail |
| **C** — scaffold removes B's excess | **unchanged.** +0.250 → +0.025, CI [0.000, +0.075] |
| **D** — order asymmetry | **unchanged, slightly larger.** +0.250 → +0.267 |
| **E** — verifier correct on collapse structures | **confirmed.** 0 count errors on 38 gold items |

Of B's 22 corrected failures, **20 are collapse and 0 are overshoot**; of
`S_SEMICOLON`'s 69, **68 are collapse**.

**Verdict: the clause-chain/collapse result survives the repair intact, and the
contrast against ordinary references is cleaner than before.**
