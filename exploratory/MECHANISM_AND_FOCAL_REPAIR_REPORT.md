# The clause-boundary mechanism, and a focal repair that failed informatively

`EXPLORATORY_NO_EVIDENCE`. Run directory
`runs/mechanism_and_focal_repair_20260811T204943Z/` (gitignored; this is the
tracked report). **1,648 generations**, all on `Qwen/Qwen3-4B` @ `1cfa9a72` under
the Round 11 execution condition, read from its manifest and unchanged.

| stage | generations | outcome |
|---|---|---|
| boundary-control preflight | 288 | `X_DEGREE_FREE` selected, asterisk rejected |
| boundary main experiment | 640 | **Δ_boundary = +0.512 [+0.375, +0.662]** at b = 4096 |
| focal-ladder calibration | 720 | **`NONDEGENERATE_FOCAL_NOT_IDENTIFIED`** |
| priority bridge / main / extension | 0 | not run — stop condition met |

---

## 1. Starting problem

Rounds 7–11 removed every proposed explanation of the semicolon background's
unusually persistent interference: free-versus-fixed placement, single-character
atomicity, the mark merely appearing in the output, wording length, and simple
response chaining. One account survived — **the semicolon can stand where a
sentence boundary could stand, and both constraints it interferes with are
defined over sentences** — and had never been tested positively.

Separately, Round 11's focal instruction was satisfied in 0.000–0.138 of rows and
"focal only" occurred in 7 of 640, so its four-state decomposition was really
*neither → target only*. No priority intervention can be tested in that regime,
because the model is never observed preserving the focal instruction at all.

---

## 2. Boundary-control construction

Candidates were fixed in advance at `°` and `*`. The preflight ran on **12
`calibration` tasks** — a split no previous run had used, zero topic overlap with
the 20 evaluation tasks — and **contained no focal-arm row**, so the control could
not be chosen on the quantity the main experiment measures.

| mark | combined compliance | markup collision | count > 1 | words | sentences |
|---|---|---|---|---|---|
| semicolon (reference) | 0.896 | 0.000 | 0.000 | 48.3 | 3.98 |
| **degree `°` — selected** | **0.729** | 0.000 | 0.062 | 47.8 | 3.88 |
| asterisk `*` — rejected | 0.208 | 0.188 | **0.792** | 43.4 | 4.00 |

The asterisk fails on a hazard pinned by tests written before any generation:
`LIST_MARKER` strips a leading `* ` for segmentation while `v_exact_char_total`
still counts it, and `**emphasis**` counts four. 79.2% of its combined answers
carry more than one asterisk.

**A correction to my own gate is recorded rather than hidden.** The first version
of the preflight scored criterion 2 as "the answer contains markdown anywhere"
and disqualified **both** candidates. That was wrong: it flagged degree answers
whose prose contained `**temperature sensor**`, which cannot change a
degree-symbol count. Markup built *from the counted character* is 0.000 for `°`.
The corrected criterion is the one the pre-generation tests already pinned. The
original output is kept at `boundary_control_preflight/report_gate_v1.txt`.

Full detail: `BOUNDARY_MECHANISM_REPORT.md`.

---

## 3. Boundary experiment

640 generations. QAC, arms {B, `C_L3`}, backgrounds {semicolon, degree},
b ∈ {0, 4096}, the 20 evaluation tasks, 4 scientific seeds. The two background
prompts were asserted to differ only in the mark name in all 160 matched groups
before generation.

### Raw arm failure rates

| background | b | P(A fails \| B) | P(A fails \| R) | background compliance (focal arm) |
|---|---|---|---|---|
| degree | 0 | 0.113 | 0.013 | 0.500 |
| degree | 4096 | 0.062 | 0.100 | 0.675 |
| semicolon | 0 | **0.725** | 0.037 | 0.938 |
| semicolon | 4096 | **0.512** | 0.037 | 0.825 |

### τ, Δ_boundary and uncertainty

| estimand | b = 0 | b = 4096 |
|---|---|---|
| τ, degree (non-boundary) | +0.100 [+0.025, +0.188] | **−0.037** [−0.150, +0.062] |
| τ, semicolon (boundary-capable) | +0.688 [+0.537, +0.825] | +0.475 [+0.375, +0.575] |
| **Δ_boundary** | **+0.588** [+0.438, +0.738] | **+0.512** [+0.375, +0.662] |
| Γ (4096 − 0) | — | −0.075 [−0.212, +0.075] |

10,000-draw cluster bootstrap over the 20 tasks, carrying all replicates and both
arms of a task together.

### Task heterogeneity

17/20 tasks positive at b = 0 and 19/20 at b = 4096, with **zero negative tasks**
at either budget; top-3 share of the total 0.26 and 0.32. Per-replicate Δ is
positive in all eight cells (+0.30 to +0.70).

### Background compliance, and the confound it creates

The degree symbol is complied with less (0.500/0.675 against 0.938/0.825 in the
focal arm), and lower compliance would attenuate its interference. Two things
bear on it, neither conclusive on its own:

* the descriptive compliant-only split — **post-treatment, reported as such,
  never substituted for the estimate** — gives Δ = +0.530 and **+0.566**, slightly
  *larger* than the assigned-condition value;
* a 0.15 compliance gap at b = 4096 producing a 0.51 difference in τ would need
  an implausibly steep dependence of interference on compliance.

### Did the boundary hypothesis survive?

**Yes.** And the mechanism variable separates completely. `splice_count` — the
repository's own audited proxy for "this mark is standing where a sentence
boundary could stand" — is > 0 in **0.887–0.939** of complied semicolon answers
and in **0.000** of complied degree answers, in every cell. The semicolon
condition writes 2.29 sentences at b = 0 where the degree condition writes 3.68;
the target is "exactly 4".

---

## 4. Focal calibration

720 generations on **CAL13–CAL32**, disjoint from the evaluation tasks and from
the preflight block. QAC, `X_PAREN_FREE` primary, b ∈ {0, 4096}, 3 replicates, no
priority cue anywhere. Gates applied in the fixed order B → B2 → B1.

| rung | focal | target | both | target only | focal only | neither | verdict |
|---|---|---|---|---|---|---|---|
| B3 = `B` | 0.033 | 0.758 | 0.033 | 0.725 | **0.000** | 0.242 | fail |
| B2 = `X_B_INC2` | 0.258 | 0.808 | 0.258 | 0.550 | **0.000** | 0.192 | fail |
| B1 = `X_B_INC1` | 0.467 | **0.958** | 0.458 | 0.500 | **0.008** | 0.033 | fail |

`NONDEGENERATE_FOCAL_NOT_IDENTIFIED`. `X_B_INC2` clears every gate but one.

**Half the repair worked and the other half revealed why it could not.** Focal
compliance rose fourteenfold, 0.033 → 0.258 → 0.467, so the ladder does lift the
focal off its floor. But `P(focal only)` never reached 0.05: as the focal gets
easier the probability moves into **both**, never into *focal only*. Under the
parenthetical background, **A and B do not compete** — whenever this model can
satisfy the length ordering it can also write four sentences.

Details, exact wordings, verifier definitions and the decision timestamp:
`NONDEGENERATE_FOCAL_CALIBRATION.md`.

---

## 5. Non-degenerate priority experiment

**Not run.** §19 gates it on a valid focal, and §32's stop condition is explicit.
With no regime in which the model preserves the focal at the target's expense, a
priority cue has nothing to act on and a null would mean only that the design
could not express the effect. `priority_bridge/`, `priority_main/` and
`priority_semicolon_followup/` each carry a `NOT_RUN.md` recording this.

No further rung was constructed. §15 permits one only if all three are unusable,
and the observed direction makes it futile: each easier rung moves probability
into *both* and pushes the target toward its ceiling — B1 is already at 0.958,
outside its own gate — which is the opposite of what the failing gate needs.

---

## 6. Semicolon priority extension

Not run; conditional on §5.

---

## 7. Sanity checks

**Seeds.** In all three datasets: exactly one answer seed per (task, replicate),
as many distinct seeds per task as replicates, and **0** rows reusing the thinking
seed for the answer. The 160 semicolon design cells shared with Round 11
Experiment 1 have **0 prompt mismatches and 0 seed mismatches**.

**Cross-run reproduction — with a correction.** I expected identical prompt +
identical seed to reproduce the answer exactly at b = 0. It does **not**: 125/160
= 0.781 byte-identical, and 65/160 at b = 4096. vLLM's continuous batching makes
the forward pass depend on batch composition, and the two runs had different
batch shapes. This does not license "bitwise deterministic", but it does show the
seed is in force — nothing like the ~0% of independent sampling, nor the ~100%
the old shared-seed defect produced. τ(semicolon, QAC, b = 0) reproduced at
**+0.688 in both runs to three decimals** despite 22% of the underlying answers
differing.

**Verifier audit.** 23 quantities recomputed from the raw JSONL by a script that
imports no estimand, grouping helper or bootstrap from the analysis module: no
disagreements. `A_pass`, `Q_pass` and `background_pass` re-derived from the answer
text: **0 mismatches** in 640 rows.

**Manual inspection.** 54 outputs read. The registry segmenter and an independent
character-scanning segmenter agreed on 52 of 54.

**Both disagreements were one artefact, then measured across all 640 rows.** All
**12** disagreements are degree rows and **100%** contain a `°` unit ending a
sentence — `…drop below 20°C. This practice…` — which the production segmenter
does not split. Among the 23 degree rows with that pattern `A_pass` is 0.478
against 0.963 elsewhere. The semicolon condition has **0** disagreements. The
artefact depresses A_pass in the degree condition only, inflating τ_degree and
therefore **deflating** Δ_boundary: **+0.512 is a lower bound with respect to it.**

**Truncation, leakage, failures.** Boundary: truncation 0.0016, leakage 0.0016, 0
technical failures. Calibration: 0, 0, 0. Preflight: 0, 0, 0.

**Concentration.** No task and no replicate drives the boundary result; see §3.

**Execution condition.** Model, revision, temperature, top-p, answer budget and
master seed are identical across all three datasets and to Round 11.

---

## 8. Observations

Only directly measured facts.

1. τ under a freely placed degree symbol is +0.100 at b = 0 and −0.037 at
   b = 4096; under a freely placed semicolon, +0.688 and +0.475.
2. Δ_boundary is +0.588 and +0.512, both intervals excluding zero.
3. Γ = −0.075, interval containing zero.
4. `splice_count > 0` in 0.887–0.939 of complied semicolon answers and 0.000 of
   complied degree answers.
5. The semicolon focal arm writes 2.29 sentences at b = 0; the degree focal arm
   writes 3.68.
6. Degree background compliance is 0.500–0.912; semicolon 0.775–1.000.
7. All 12 segmenter disagreements are degree rows containing a `°` unit at a
   sentence end.
8. Focal compliance across the ladder: 0.033, 0.258, 0.467.
9. P(both) across the ladder: 0.033, 0.258, 0.458.
10. P(focal only) across the ladder: 0.000, 0.000, 0.008.
11. Target compliance across the ladder: 0.758, 0.808, 0.958.
12. Under the semicolon background, B1 shows P(focal only) = 0.133 at b = 0 and
    0.183 at b = 4096.
13. 79.2% of asterisk-condition answers contain more than one asterisk.

---

## 9. Supported interpretations

* **Within these conditions, boundary capability is what makes the mark
  interfere.** A mark that can occupy a sentence boundary damages
  sentence-defined constraints; an otherwise identically specified mark that
  cannot, does not. This is the first positive intervention on the mechanism
  rather than another elimination.
* **Reasoning does not erode it.** Γ's interval contains zero: the gap is as wide
  without reasoning as with it.
* **The interference is not about "a mark to place".** The degree symbol is one
  mark, exactly one, freely placed, in the identical sentence, and τ under it is
  −0.037 at b = 4096.
* **The target and this focal instruction do not compete.** Making the focal
  easier moves probability into *both*, not into *focal only*, at every rung.
  Combined with observation 12, the state an arbitration account needs appears
  only once a boundary-capable mark is present to damage the target.

---

## 10. Falsified or weakened hypotheses

* **"Any single, freely placed, unattached mark produces this interference."**
  **Falsified.** τ(degree) = −0.037 at b = 4096.
* **"Reasoning erodes the semicolon's effect."** **Not supported.** Γ = −0.075
  [−0.212, +0.075].
* **"The Round 11 priority null was caused by the focal instruction's floor."**
  **Weakened.** The floor is real and was repaired — focal compliance rose
  fourteenfold — and the *focal only* state still did not appear. The obstacle
  was not the focal being too hard.
* **"The asterisk is a usable non-boundary control."** **Falsified** on a
  pre-registered hazard.

---

## 11. Remaining hypotheses

Kept narrow.

* **The mark's boundary *use*, not its boundary *capability*, is what matters.**
  The intervention assigns the instruction; the boundary behaviour follows.
  `X_NO_SEMI_SPLICE` — a prohibition on the semicolon standing where a sentence
  could end — exists in the registry and was never crossed with this design.
* **`°` may differ in a second way.** It is matched on count, scope, placement
  freedom, wording and response length, but it is not punctuation at all.
* **Whether any of this transports.** One model, one order, one load, one task
  set. Round 11 already found the semicolon amplification itself does not
  transport to SmolLM3-3B.

---

## 12. Highest-value next experiment

**Cross `X_SEMICOLON_FREE` with `X_NO_SEMI_SPLICE`.**

Keep the semicolon instruction exactly as it is and add the registry's existing
prohibition on a semicolon standing where a sentence could end. If interference
survives, boundary *capability* is doing the work and the mark's actual use is
incidental. If it collapses toward the degree symbol's τ, the mechanism is the
*use*, and the account becomes a causal claim about what the mark does in the
text rather than about what it could do.

Why this one: it is the only remaining step that converts the surviving account
from "capability predicts interference" into an intervention on the behaviour
itself, it needs no new model or engine, and both constraints already exist and
are audited. ~640 generations, the same design as Experiment 1 with the
prohibition as a third background arm.

It also has a clean failure mode worth having: if the prohibition proves
uncompliable — as every fixed-placement wording did in Round 9 — that is
measurable in a preflight before any τ is read, on the same calibration split
used here.
