# Experiment decisions

One entry per new experiment: why it was chosen, which hypotheses it separates,
what each outcome would mean. Written **before** the run.

---

## D1 — Existing-data forensics (no generation)

**Why.** Four of the five hypotheses could be moved without spending a token.
Running compute before exhausting the 960 generations already on disk would have
been waste.

**Distinguishes.** H5 (definitional artefact) decisively; H4 (task
susceptibility) decisively; informs H2/H3.

**Outcomes and readings.** Recorded in `FINDINGS.md`. In brief: H5 was **partly
confirmed** — collapse is a strict subset of A-failure, so the r = 0.998
statistic reported in the first round was inflated by nesting and has been
withdrawn. H4 was **weakened** — B's and `S_SEMICOLON`'s failure sets overlap
*less* than independence predicts.

---

## D2 — Anti-collapse intervention

**Why.** After D1, H1 and H2 both survive and make the same predictions about
every quantity measurable on the existing data. Only an intervention that
removes the suspected mediator can separate them, and it is cheap.

**The one factor changed.** The **system message** gains one clause:
`Write each sentence on its own line.`

The scaffold lives in the system message rather than in the numbered constraint
list on purpose: it keeps the instruction count at k=5 in both conditions, keeps
the numbered list byte-identical, and applies to every arm identically. Adding it
as a sixth numbered constraint would have changed the load and confounded the
comparison it exists to make.

**Fixed.** A, the background set, load k=5, both orders, the same 20 pilot tasks,
same model/revision/decoding/cap/verifier. Arms cut to three.

**Arms.** `B` (focal), `S_SEMICOLON` (the anomalous reference), `C_L3` (the
lowest-interference ordinary reference, 0.017 pooled). 3 arms × 2 scaffold
conditions × 2 orders × 20 tasks × 2 replicates = **480 generations, ≈9 min**.
The baseline condition is re-run rather than taken from Stage B so that both
conditions come from one run under one system message contrast.

**Competing hypotheses.** H1 (pair-specific) vs H2 (shared structural mode), with
a side-reading on H3.

**Outcomes and how each updates the interpretation.**

| Outcome | Reading |
|---|---|
| A-failure falls sharply for **both** B and `S_SEMICOLON`, and by much more than for `C_L3` (which has little collapse to remove) | **H2 supported.** The collapse strategy is causally upstream, not a redescription. |
| A-failure stays high while the mode migrates (failures reappear as 3 or 5 segments) | **H2 falsified as a mechanism.** Collapse was a symptom; something else drives A-failure. |
| `S_SEMICOLON` recovers but **B retains substantial excess** over `C_L3` | **H1 supported** as an additional, pair-specific mechanism beyond the shared one. |
| B's `o_Q` − `o_A` gap survives the scaffold | **H3 strengthened** as an independent position effect, not merely a collapse trigger. |
| B's gap disappears with the scaffold | Order acts *through* collapse; H3 is a trigger for H2 rather than a separate mechanism. |

**Pre-registered caveat.** The scaffold may reduce A-failure everywhere by making
segmentation easier. That is expected and is not the readout. The readout is
whether the *excess* of B and `S_SEMICOLON` over `C_L3` shrinks.

---

## D3 — `S_SEMICOLON` minimal-variant diagnostic

**Why.** `S_SEMICOLON` was admitted blind as a reference for generic load and
turned out to be the strongest interferer in the set. Understanding why is worth
more than measuring it again, and it bears directly on whether the
reference-admission procedure is sound.

**Three explanations to separate.**
1. **Requiring semicolons at all** — the mark itself invites clause chaining.
2. **Per-sentence scope inviting boundary substitution** — "one in every
   sentence" is cheapest to satisfy by using `;` *instead of* `.`, which directly
   destroys the sentence count.
3. **Generic per-sentence formatting burden** — any punctuation requirement
   applied per sentence costs A-compliance.

**Variants — all four already authored in the registry, none written for this
test.** Wording is not tuned post hoc; that would be fitting the explanation to
the effect.

| Arm | Rule | Mark | Scope | Isolates |
|---|---|---|---|---|
| `S_SEMICOLON` | ≥1 semicolon in every sentence | `;` | per-sentence | baseline (known: 0.60) |
| `U_FMT_SEMI2` | exactly 2 semicolons in the whole answer | `;` | **whole-text** | holds the mark fixed, changes scope |
| `S_TWOCOMMA` | exactly 2 commas per sentence | **`,`** | per-sentence | holds scope fixed, changes the mark |
| `C_L3` | every sentence begins with S | none | per-sentence | non-punctuation per-sentence control |

`,` cannot terminate a sentence, so it cannot substitute for a boundary; `;` can
sit where a `.` would go. That asymmetry is what makes the pair informative.

**Cost.** 4 arms × 2 orders × 20 tasks × 2 replicates = **320 generations, ≈6 min**.

**Outcomes and how each updates the interpretation.**

| Outcome | Reading |
|---|---|
| Only `S_SEMICOLON` interferes; `U_FMT_SEMI2` and `S_TWOCOMMA` do not | **Explanation 2.** The damage is per-sentence scope applied to a mark that can replace a sentence boundary. |
| `U_FMT_SEMI2` also interferes strongly | **Explanation 1.** Requiring the mark at all is enough; scope is secondary. |
| `S_TWOCOMMA` also interferes strongly | **Explanation 3.** Generic per-sentence formatting burden; the semicolon is incidental. |
| Everything interferes about equally | The reference pool has a systematic problem with per-sentence constraints, not a semicolon problem. |

**Prior from existing data.** `S_SEMICOLON` *passes* carry **more** semicolons
(3.50) than its failures (2.63) while differing sharply in periods (4.18 vs
1.42). So the count of semicolons is not the driver; where they sit is. That
favours explanation 2 before the run — which is why the run is worth doing, to
avoid confirming a story from the data that suggested it.

---

## Outcomes

### D2 — anti-collapse intervention · `runs/stageD2_anticollapse_20260810T192423Z`
480 generations, 0 technical failures. Baseline arms replicate Stage B closely
(B `o_Q` 0.275 vs 0.317; `S_SEMICOLON` `o_A` 0.675 vs 0.633), which is itself a
successful independent replication on a fresh run.

| | without scaffold | with scaffold | Δ [95% CI] |
|---|---|---|---|
| B `o_Q` | 0.275 | 0.050 | **−0.225 [−0.375, −0.100]** |
| B `o_A` | 0.025 | 0.025 | 0.000 [−0.075, +0.075] |
| `S_SEMICOLON` `o_A` | 0.675 | 0.325 | −0.350 [−0.500, −0.200] |
| `S_SEMICOLON` `o_Q` | 0.575 | 0.325 | −0.250 [−0.400, −0.100] |
| `C_L3` (control) `o_A` | 0.025 | 0.050 | +0.025 |
| `C_L3` (control) `o_Q` | 0.000 | 0.050 | +0.050 |

Paired **excess over `C_L3`** — the pre-registered readout:

| arm / order | without | with |
|---|---|---|
| B `o_Q` | **+0.275** [0.150, 0.425] | **0.000** [−0.075, +0.075] |
| B `o_A` | 0.000 | −0.025 |
| `S_SEMICOLON` `o_A` | +0.650 | **+0.275** [0.150, 0.425] |
| `S_SEMICOLON` `o_Q` | +0.575 | **+0.275** [0.100, 0.475] |

**Row 1 of the pre-registered table fired:** failure fell sharply for both B and
`S_SEMICOLON` and did not fall for the control → **H2 supported**. Row 3 did not
fire: B retains **no** excess → **H1 falsified by its own criterion**. Row 5
fired: B's order gap fell from +0.250 to +0.025 → **order acts through collapse**.

The pre-registered caveat did **not** materialise — the scaffold is not a general
A-helper. `C_L3` got slightly *worse*, so the recovery is specific to the arms
that were using the collapse route.

Unanticipated: the scaffold was only partly obeyed by the very arms it targets
(mean newlines — `C_L3` 3.00, `S_SEMICOLON` 1.78, B 0.49), yet B recovered
anyway, producing 4.09 periods without line breaks. The scaffold works by
reasserting that discrete sentences are wanted, not purely as a formatting
change. And `S_SEMICOLON` keeps a substantial residual: half its collapse
survives an explicit instruction not to collapse.

### D3 — semicolon minimal variants · `runs/stageD3_semicolon_20260810T192430Z`
400 generations, 0 technical failures. B's order effect replicates again
(`o_A` 0.050 → `o_Q` 0.300).

| arm | mark | scope | excess `o_A` | excess `o_Q` | collapse rate | mean periods |
|---|---|---|---|---|---|---|
| `S_SEMICOLON` | `;` | per-sentence | **+0.650** | **+0.525** | 0.650 / 0.550 | **2.10 / 2.45** |
| `U_FMT_SEMI2` | `;` | whole-text | +0.125 | +0.025 | **0.000** | 3.95 / 4.10 |
| `S_TWOCOMMA` | `,` | per-sentence | +0.025 | 0.000 | **0.000** | 4.15 / 4.28 |

**Explanation 2 selected, as pre-registered.** Requiring semicolons is not
sufficient: `U_FMT_SEMI2` responses actually contain them (93.8% carry ≥1, mean
1.02) yet keep 4.03 periods and collapse **never**. Generic per-sentence
formatting burden is not sufficient either: `S_TWOCOMMA` demands two commas in
*every* sentence and collapses **never**. Only the conjunction — a per-sentence
requirement for a mark that can stand where a sentence boundary would — produces
the effect.

The mechanism is substitution, not accumulation. `S_SEMICOLON`'s *passes* carry
**more** semicolons (3.45) than its *failures* (2.63) while differing sharply in
periods (4.18 vs 1.42). It is not how many semicolons appear, it is whether they
replace the full stops.
