# Competing hypotheses

Written **before** any new generation, against run `stageB_20260810T183206Z`
(960 generations) and the Stage A runs. Confidence values are subjective and are
revised in place as evidence arrives; each revision is dated.

## Facts every hypothesis must explain

| Fact | Value |
|---|---|
| Primitive A (isolated) | 0/60 failures |
| B focal A-failure | 0.067 (`o_A`) → **0.317** (`o_Q`) |
| Ordinary references `C_L3`/`C_O2`/`C_W3` | 0.017–0.050, **flat across order** |
| `S_SEMICOLON` reference | 0.633 (`o_A`), 0.567 (`o_Q`) — *higher than the focal in both* |
| Truncation / technical failures | 0 / 0 |
| Dominant failure appearance | one long clause-chained sentence |
| Construction-time coupling of `S_SEMICOLON` with A | 0.00 |

---

## H1 — Pair-specific interference
*B impairs A beyond what a generic added instruction does, because of something
specific to the (B → A) direction.*

- **For.** In `o_Q`, τ vs the three ordinary references is +0.27 to +0.30 with
  bootstrap CIs excluding 0, at matched instruction count and identical
  background. The order asymmetry (+0.250) appears on the focal arm **and on no
  reference**, which is itself a pair-specific signature.
- **Against.** `S_SEMICOLON` — admitted blind as a *reference* — impairs A more
  than B does in both orders, so B is not the strongest interferer of the set.
  In `o_A` the advantage over ordinary references is ≈0.02–0.05 with CIs
  spanning zero.
- **Distinctive prediction.** After an intervention that suppresses the shared
  collapse strategy, B retains substantial excess A-failure over an ordinary
  reference; and B's failure is not fully predicted by whatever structural mode
  it induces.
- **Cheapest falsifying test.** The anti-collapse intervention (§6 of the plan):
  if B's excess over the ordinary reference goes to ≈0 when collapse is blocked,
  H1 as an *independent* mechanism is falsified.
- **Confidence (2026-08-10, pre-intervention): 0.25**
- **REVISED after D2 (anti-collapse intervention): 0.05.** Falsified by its own
  pre-registered criterion. With the scaffold, B's paired excess over `C_L3` is
  **0.000** in `o_Q` (CI [−0.075, +0.075], down from +0.275) and −0.025 in `o_A`.
  Every bit of B's advantage over an ordinary reference ran through the collapse
  route. Nothing pair-specific survives its removal.

## H2 — Structural failure-mode mechanism
*B and certain other instructions trigger a shared response strategy — merging
intended sentences into one clause chain — and that strategy is what breaks A.*

- **For.** 88/106 A-failures are ≤2 segments. Manual reading shows fluent,
  EOS-terminated, untruncated clause chains. `S_SEMICOLON` produces the same mode
  far more often. Semicolon counts move with it (B `o_Q` 0.58 vs B `o_A` 0.13;
  `S_SEMICOLON` ≈2.9).
- **Against.** **The supporting statistic is partly definitional** — see H5 and
  §2 of the plan. "Collapse" (≤2 segments) is a strict subset of A-failure
  (≠4 segments), so a high correlation is guaranteed to some degree and cannot on
  its own establish a mechanism. Nothing yet shows the strategy is *causally*
  upstream rather than a redescription of the failure.
- **Distinctive prediction.** Blocking the strategy reduces A-failure sharply for
  **both** B and `S_SEMICOLON`, and by more than it reduces failure for an
  ordinary low-interference reference (which has little collapse to remove).
- **Cheapest falsifying test.** The anti-collapse intervention. If A-failure
  stays high while the collapse mode disappears (failures migrate to 3 or 5
  segments), the collapse strategy was a symptom, not the mechanism.
- **Confidence (2026-08-10, pre-intervention): 0.45**
- **REVISED after D2: 0.85.** The intervention moved exactly what H2 predicted
  and nothing it did not. Blocking the strategy cut B's `o_Q` failure 0.275 →
  0.050 (Δ −0.225, CI [−0.375, −0.100]) and `S_SEMICOLON` 0.675 → 0.325 and
  0.575 → 0.325, while the control `C_L3` did **not** improve (0.025 → 0.050,
  0.000 → 0.050). So the scaffold is not a general A-helper that lifts every arm;
  it removes one specific route, and the arms that used that route are the ones
  that recover. Collapse is causally upstream, not a redescription.
- **Caveat.** `S_SEMICOLON` keeps a **+0.275** excess under the scaffold and its
  collapse rate only halves (0.60 → 0.30), so the shared mechanism is not the
  whole of *its* effect. H2 is sufficient for B; it is only partial for
  `S_SEMICOLON`.

## H3 — Order / salience mechanism
*The large `o_Q` effect is substantially caused by instruction position — recency,
primacy, or implied priority — rather than by the content relation between A and B.*

- **For.** The order swap moves the focal arm by +0.250 while moving every
  reference by ≤0.07. Under `o_Q` the model reads "each sentence strictly longer
  than the last" before it reads "exactly 4 sentences".
- **Against.** If position alone mattered, references should also shift when they
  move into slot 1; they do not. So position interacts with *which* instruction
  occupies it — i.e. order is a moderator, not the whole cause.
- **Distinctive prediction.** The order effect survives the anti-collapse
  intervention; and the set of tasks that flip from pass to fail under the swap
  is not explained by task identity alone.
- **Cheapest falsifying test.** Task-level transition analysis on existing data
  (§5) plus the order arm of the intervention. If flips are concentrated in a few
  tasks that also fail everywhere else, H4 is doing the work instead.
- **Confidence (2026-08-10): 0.55 as a moderator; 0.10 as the primary cause**
- **REVISED after D1 and D2: 0.90 as a moderator acting THROUGH collapse; <0.05
  as an independent mechanism.**
  - *Recency is ruled out by sign.* Under `o_Q`, A is the **more recent** of the
    two swapped instructions and yet fails more. Recency predicts the opposite
    sign; primacy predicts the observed one. Whichever instruction is read first
    sets the structural plan.
  - *The effect is mediated.* Under the scaffold, B's order gap falls from
    +0.250 to **+0.025**. Order does not survive the removal of collapse, so it
    is a trigger for the shared mechanism rather than a mechanism of its own.
  - Within the 16 units that flip pass→fail on the order swap alone (same task,
    same replicate), structure goes from 4.00 periods / 0.00 semicolons under
    `o_A` to 1.19 / 1.94 under `o_Q`.

## H4 — Task susceptibility
*Some underlying tasks are intrinsically prone to collapse, and instructions
differ mainly in how strongly they trigger that latent vulnerability.*

- **For.** Not yet assessed. Topics differ in how naturally they invite a single
  explanatory sentence.
- **Against.** Not yet assessed.
- **Distinctive prediction.** Failure sets across arms overlap far more than
  chance (high Jaccard); a small set of tasks accounts for a disproportionate
  share of failures in *every* arm; replicate-to-replicate repeatability within
  task is high.
- **Cheapest falsifying test.** Existing-data forensics (§3) — no new generation
  needed. If failures are spread near-uniformly across tasks and Jaccard overlap
  between B and `S_SEMICOLON` is near chance, H4 is weak.
- **Confidence (2026-08-10): 0.35** → **REVISED after D1: 0.15 as a driver.**
  B's and `S_SEMICOLON`'s failure sets overlap **less** than independence
  predicts (Jaccard 0.131 against 0.170 expected; P(`S_SEMICOLON` fails | B
  fails) = 0.478 against its 0.600 base rate). They are not two triggers of one
  vulnerable-task set. Failures are only mildly concentrated (B: 11/20 tasks
  affected, top quarter carries 0.65 of failures against 0.25 uniform;
  `S_SEMICOLON`: 18/20 tasks, 0.42). Within-task replicates are frequently
  **mixed** (B `o_Q`: 40% of task cells split), so the outcome is a stochastic
  strategy choice the instruction biases, not a fixed task property.

## H5 — Measurement / definition artefact
*The near-perfect collapse↔failure association is substantially definitional, and
the "mechanism" claim is weaker than it looked.*

- **For.** A = "exactly 4 sentences"; collapse = "≤2 sentences". Collapse ⊆
  A-failure by construction, so `residual = A_failure − collapse ≥ 0` always and
  r is inflated by the nesting. The r = 0.998 reported earlier therefore
  **cannot** be cited as mechanistic evidence without decomposition.
- **Against.** The *non*-definitional content survives: the residual
  (non-collapse failure) is roughly constant at 0.017–0.050 across all ten cells,
  so between-arm variation lives in the collapse mode specifically rather than in
  miscounts generally. That is a real decomposition even if the raw correlation
  is not.
- **Distinctive prediction.** Once failures are partitioned by exact observed
  sentence count, arms differ in *which* failure mode they take, not merely in
  total failure — and `P(F_A=1, ¬collapse)` is small and arm-independent.
- **Cheapest falsifying test.** §2 audit on existing data. If arms differ mainly
  in non-collapse failures too, the collapse framing adds nothing.
- **CONFIRMED. The r = 0.998 statistic is withdrawn.** Collapse is a strict
  subset of A-failure (0 collapse-but-passing rows in 600), so the correlation
  was partly guaranteed by nesting and was over-claimed in the first report.
- **The decomposition survives and is stronger than the correlation was.**
  Failure that is *not* collapse sits at 0.017–0.050 across all ten cells — a
  range of 0.033 — while total failure ranges over 0.617. And the arms differ in
  **which mode** they take: ordinary references fail by *overshooting* to 5–6
  sentences (8 of 11 failures), B and `S_SEMICOLON` by collapsing to one. A
  qualitative difference in direction cannot be manufactured by nesting.
- **Confidence the framing is now sound: 0.90**
- **REVISED after Round 3 (blinded audit + stress corpus): H5 is PARTLY TRUE, and
  in a direction that does not help the rival hypotheses.**
  - A real verifier defect exists: `E_A = 0.207` on a 31-item hand-labelled
    stress corpus. **All six errors are over-splitting** — `a.m.`/`p.m.`, titles
    (`Dr.`), `approx.`/`e.g.`, initials (`J. R.`) and ellipses.
  - The verifier is **correct on every collapse-relevant structure**: semicolon
    chains, comma chains, run-ons, merges, newline/bulleted/numbered layouts, and
    the crucial "four sentences each containing a semicolon" case (`E_R = 0.000`).
  - The defect therefore manufactures **false overshoot**, never false collapse.
    Correcting it across all 1,480 contrast rows changes 2.8–3.5% of counts and
    moves every headline slightly **in favour** of the main finding: τ(B−C_L3)
    0.175 → 0.183, τ(B−C_O2) 0.142 → 0.183, the order gap 0.250 → 0.267, and the
    scaffolded B excess stays ≈0 (0.000 → +0.025).
  - **Correction to Round 2's §7 claim.** I said the coupling screen missed
    `S_SEMICOLON` because its support omitted the mode. Measured on a support
    that *does* contain the mode, κ(A,R) = **−0.13** [−0.37, +0.12] — still ≈0.
    The screen was not blind; it measures **verifier-error coupling**, which is a
    different quantity from behavioural interference and was never going to rank
    it. That is the more precise and more damning finding about the method.
  * **Round 4 addendum.** Recomputed with the statistic the preregistration
    actually defines — the mean fraction of coupling *edits* flipping BOTH
    verdicts — κ = **0.400**, U_κ **[0.400, 0.400]** over 8 informative
    responses, i.e. degenerate. Round 3's "κ = −0.132" was Cohen's kappa under
    the wrong name and is **withdrawn**; the signed coefficient is now reported
    separately as `agreement_phi` = +0.035. The conclusion is unchanged and
    better supported: coupling does not track behavioural interference.

---

## Relationship between hypotheses

These are not mutually exclusive. The most likely world is a **conjunction**:
a shared structural strategy (H2) whose triggering probability depends on both
instruction identity and its position (H3) and on the task (H4), with H1
surviving only if B shows excess failure once the strategy is blocked. H5 is a
constraint on how the evidence may be *described*, not a rival mechanism.

## Test order (cheapest and most decisive first)

1. §2 collapse circularity audit — existing data, no compute. Resolves H5.
2. §3 matched forensics — existing data, no compute. Resolves H4, informs H2/H3.
3. §5 order transitions — existing data, no compute. Informs H3.
4. §4 raw-output audit — existing data, human reading. Informs H2.
5. §6 anti-collapse intervention — small new run. **Discriminates H1 vs H2.**
6. §7 semicolon variants — small new run. Explains the `S_SEMICOLON` anomaly.
7. §8 coupling-bank coverage — existing data. Methodological.

---

# Round 5 hypotheses — what the mechanism actually is, and how far it reaches

H1–H5 asked *whether* B's interference was pair-specific. That question is
settled: it is not (H1 falsified by its own criterion at D2). M1–M5 ask what the
shared mechanism **is** and where it stops. Confidence is subjective and revised
in place, dated.

## Facts every Round 5 hypothesis must explain

| Fact | Value | Source |
|---|---|---|
| `S_SEMICOLON` failure at k=5 | 0.633 (`o_A`) / 0.567 (`o_Q`) | Stage B |
| Its failures are one clause-chained sentence | 88/106 A-failures are collapses | Stage B forensics |
| Its **passing** answers carry MORE semicolons than its failing ones | 3.45 vs 2.63 | Stage B |
| but far more periods | 4.18 vs 1.42 | Stage B |
| Whole-answer semicolon rule never collapses | `U_FMT_SEMI2` collapse 0.000, 93.8% carry ≥1 | D3 |
| Per-sentence **comma** rule never collapses | `S_TWOCOMMA` collapse 0.000 | D3 |
| A boundary scaffold removes B's excess and halves `S_SEMICOLON`'s | −0.225 / −0.350 | D2 |
| Ordinary references barely fail at all under the corrected verifier | `C_L3`, `C_O2`: **zero** corrected failures | Round 4 rescore |

---

## M1 — Delimiter substitution
*A per-sentence demand for a mark that can grammatically stand where a sentence
boundary would stand is satisfiable by putting the mark **instead of** the
boundary. The sentence count then collapses as a side effect of complying.*

- **For.** Every D3 result: the mark matters (`,` does not collapse, `;` does),
  the scope matters (whole-answer `;` does not collapse), and the quantity does
  not (passes carry more semicolons than failures). Raw outputs read exactly like
  this — one sentence, one full stop, several semicolons.
- **Against.** Nothing yet, but D3's three arms differ in wording as well as in
  mark and scope, so the comparison is not clean. E4 fixes that.
- **Confidence 2026-08-11: 0.6.**
- **Would be falsified by.** `X_COMMA_EACH` collapsing; or `X_SEMI_TOTAL4`
  collapsing; or the effect vanishing when the wording is held fixed across marks.

## M2 — Per-sentence scoping burden
*Any per-sentence requirement makes many sentences expensive, so the model writes
fewer. The mark is incidental.*

- **For.** It is the simplest account of why scope mattered in D3.
- **Against.** `S_TWOCOMMA` is a per-sentence requirement and collapses **never**;
  so are `C_L3` and `C_W3`, and neither interferes.
- **Confidence 2026-08-11: 0.1.**
- **Decisive cell.** `X_COMMA_EACH` under a wording identical to the semicolon
  arm's. M2 requires it to collapse; M1 requires it not to.

## M3 — Mark quantity
*Demanding many marks of any kind pushes the text toward clause chaining.*

- **For.** Collapsed answers do contain several semicolons.
- **Against.** `S_SEMICOLON`'s passes carry *more* semicolons than its failures.
- **Confidence 2026-08-11: 0.05.**
- **Decisive cell.** `X_SEMI_TOTAL4` — the same mark, the same quantity implied at
  N = 4, no per-sentence scoping. M3 requires it to collapse.

## M4 — Generic instruction burden / demand characteristic
*Behaviour moves whenever the system message gains any clause; D2's recovery is
about message length, not about boundaries.*

- **For.** Nothing yet; it is unexcluded rather than supported. D2 had no sham.
- **Against.** Nothing yet.
- **Confidence 2026-08-11: 0.25 — the largest unaddressed threat to the causal
  claim.**
- **Decisive cell.** E1's `sham_plain_style`.

## M5 — B is a separate route
*B ("each sentence strictly longer than the last") loses the count while planning
a growing structure, not by substituting a delimiter.*

- **For.** B writes by far the longest answers (173–220 tokens vs 53–103); its
  collapse is order-dependent (0.033 `o_A` → 0.300 `o_Q`) while
  `S_SEMICOLON`'s is not; the two arms' failure sets overlap *less* than
  independence predicts (D1).
- **Against.** Both respond to the same boundary scaffold, which is what a single
  shared mediator predicts.
- **Confidence 2026-08-11: 0.5.**
- **Decisive evidence.** Whether B's failures carry the substitution signature
  (few periods, many boundary-capable marks) or a different one, and whether
  B's excess scales with N while the mark arms' does not.

---

## Round 5 test order

1. **E1** sham ladder — retires **M4**, the largest threat to the causal claim.
2. **E2** fresh instances and fresh wording — retires "it is these 20 topics" and
   "it is this phrasing".
3. **E3** N ∈ {2,3,4,5,6} — separates *strategy* from *difficulty response*.
4. **E4** mark factorial — separates **M1 / M2 / M3** under one matched wording.
5. **E5** other structural unit, other constraint family — finds the boundary of
   the claim. Conditional on the mechanism still being coherent.
6. **E6** cross-model — tests whether any of it is a fact about Qwen3-4B.
