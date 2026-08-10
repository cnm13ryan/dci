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
- **Confidence (2026-08-10): 0.35, and it is compatible with H2 rather than
  rival to it — task susceptibility would be the moderator of a shared mechanism**

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
- **Confidence that the r=0.998 statistic was over-claimed: 0.85**
- **Confidence that the underlying decomposition is still informative: 0.60**

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
