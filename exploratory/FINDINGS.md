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
the answer collapsing into one clause-chained sentence. Across all ten arm×order
cells, A-failure tracks the collapse rate at r = 0.998, and B sits *on* that curve
rather than above it.

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

r(A-failure, collapse) = **0.998** across the ten cells. 88 of 106 A-failures
(83%) are collapses. Residuals are 0.017–0.050 everywhere, and **B's residual is
not larger than the references'** — C_O2's is the largest at 0.050.

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
| **Mechanism-class, not pair-specific** | Any clause-chaining-inducing instruction impairs a sentence-count target | r = 0.998 between collapse and A-failure; B on the curve, not above it; S_SEMICOLON further along the same curve | **Strongly supported.** The leading explanation. |
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
   between-arm variation (r = 0.998), and B has no excess residual over it.
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
  numbers, because the r = 0.998 relation is already the whole story.
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
