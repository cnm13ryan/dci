# Round 5 — is the collapse mechanism robust, causally specific, and general?

**EXPLORATORY_NO_EVIDENCE.** Nothing here authorises a freeze. Every interval is a
paired cluster bootstrap percentile over 20 task clusters, with no multiplicity
control and no inferential guarantee. Production code under `src/dci` is
unchanged; the constraints authored for these experiments live in
`exploratory/dci_exploratory/extensions.py`, carry an `X_` prefix and origin
`"exploratory"`, and the harvested registry's provenance hash is byte-identical
before and after they are registered (asserted in
`tests/test_round5_machinery.py`).

**Scale.** 21 new runs, 11,400 new generations (27 runs and 13,624 generations
including Rounds 1–4), **0 technical failures**, **0 truncations** in any
contrast row. Two models, 2× Radeon RX 7900 XTX, ROCm 7.2. Raw generations,
designs, configs and environment records are preserved per run under
`exploratory/runs/` (git-ignored by a Round 1 decision; they are on disk in this
worktree).

---

## The one-paragraph answer

The phenomenon is real, reproducible and much narrower than it looked. It is not
a fact about the registered (A, B) pair, and it is not about "per-sentence
constraints" or "boundary-capable punctuation". **Qwen3-4B-Instruct-2507 realises
a demand for several semicolons as a single clause-chained sentence**, and any
target that counts sentences then fails by undershoot. That disposition exists
before any target does — the semicolon instruction *alone*, with nothing to
interfere with, produces 1.1 sentences — and it survives fresh topics, a fresh
wording, target counts from 2 to 6, and the removal of the entire background. It
does **not** transfer to a paragraph-count target, does **not** occur for colons
or dashes demanded per sentence, does **not** occur for commas at any dose, and
does **not** produce interference in `gemma-2-9b-it`, which has the same
disposition but resolves the conflict the other way. Meanwhile the focal
instruction the study was built around, **B, turns out not to interfere at all
unless the shared background happens to supply a colon.**

---

## 1. Where the mechanism generalizes

| dimension | tested by | result |
|---|---|---|
| **fresh instances** | E2a, 20 unseen `burned` topics | reproduces: excess 0.375/0.375, identical signature |
| **fresh wording** | E2b, wording 2 | reproduces: 0.600/0.550, collapse 0.525/0.550 |
| **wording of the arm itself** | E4, `X_SEMICOLON_EACH` vs registry `S_SEMICOLON` | indistinguishable: 0.750/0.675 vs 0.725/0.750 |
| **target count N** | E3, N ∈ {2,3,4,5,6} | 0.375–0.925 at every N, no trend, **largest at N = 2** |
| **compositional load** | Stage A2 at k=2, no background at all | still +0.250/+0.125 |
| **background set** | 18 run-cells, 7 different background sets | positive in **every one**, +0.125 to +1.000 |
| **scope of the demand** | E4b, whole-answer floor vs per-sentence | both, whole-answer **harder** (0.975 vs 0.70) |
| **dose** | E4b, ≥2 / ≥4 / ≥6 semicolons | 0.20 → 0.975 → 0.99, threshold at the target count |
| **the disposition, across model families** | E6, gemma-2-9b-it in isolation | reproduces: 1.075–1.150 sentences |

The chain the replication criterion demands — **trigger → the same interpretable
failure strategy → target failure** — reproduces intact wherever the interference
reproduces. Across Stage B, E2a and E2b the collapsed responses carry 1.09–1.24
boundary-capable marks per lost boundary, 0.21–0.44 commas per lost boundary,
40–50 words, exactly one full stop, and in **100%** of cases satisfy the
semicolon instruction they were given.

---

## 2. Where it fails

| dimension | tested by | result |
|---|---|---|
| **other marks, per sentence** | E4 | colon **0.000**, dash **0.000**, comma 0.025–0.050 |
| **another structural unit** | E5a, exactly-4-paragraphs | **no transfer**: paragraph count 4.000 while the same responses' sentence count falls from 11.9 to 4.7 |
| **another constraint family** | E5b, four distinct integers | inconclusive — the target fails 0.725 unaided |
| **another model family** | E6, gemma-2-9b-it | **no interference**: excess 0.000–0.125, sentence count 3.93–4.00 |
| **B, the registered focal** | E4c and 18 run-cells | B interferes only when the background supplies a colon |
| **blocking the strategy** | E1 (scaffold + sham), E7 + E7c (prohibitions, 2 backgrounds) | **no instrument succeeded** |

### The two most informative failures

**E5a is the boundary, shown positively.** Under a paragraph-count target the
semicolon instruction does everything it always does — 13.3 semicolons, sentence
count cut from the control's 11.9 to 4.7 — and the paragraph count sits at exactly
4.000 (excess −0.050 / +0.025). The behaviour is unchanged; the failure vanishes,
because the target counts a unit the semicolon cannot stand in for. (The
paragraph-side substitute, `X_LINEBREAK_EACH`, was **ignored by the model**, arm
compliance 0.000–0.025, so that route is untested rather than absent.)

**E6 dissociates disposition from arbitration.** Gemma has the habit more strongly
than Qwen — a bare semicolon demand alone gives it 1.075–1.150 sentences, and it
extends the habit to commas (1.425), which Qwen does not. But when an explicit
sentence count competes, gemma **drops the semicolons and keeps the count**: 2.0–2.6
semicolons where four are demanded, arm compliance 0.000–0.050, four sentences.
Qwen does the reverse. The interference needs a model that arbitrates in favour of
the added instruction.

---

## 3. What was withdrawn or corrected in this round

1. **D2's anti-collapse intervention is withdrawn as mechanistic evidence.** E1's
   sham — `Write each sentence in a plain style.`, matched to the real scaffold on
   form and length — reproduced most of its effect. Measured against the sham
   rather than against no scaffold, boundary content contributes 0.000 to −0.075
   in `o_A` (intervals spanning zero) and −0.15 to −0.20 in `o_Q`.
2. **No system-message scaffold will be used as an instrument again.** The sham
   was not inert: it cut B's commas from 9.19 to 7.42 and raised `S_SEMICOLON`'s
   sentence count from 2.34 to 2.90. No clause about *how to write sentences* can
   be inert with respect to *how many sentences get written*.
3. **"Per-sentence scoping causes substitution" (D3's reading) is inverted.**
   Per-sentence scoping is **protective**. The same four colons collapse the
   answer when demanded of the whole answer (excess 0.850, 1.775 sentences) and do
   not when demanded per sentence (0.000, 4.000 sentences), because the
   per-sentence rule forces them apart. The semicolon is simply the one mark whose
   pull defeats that protection.
4. **"Boundary-capable mark" was the wrong predictor.** It was a judgement about
   English grammar. Colons and dashes are boundary-capable and produce zero
   excess per sentence, because this model uses them *inside* sentences.
5. **B is largely not a directional interferer.** See §4.

---

## 4. The finding that bears on DCI itself

**τ is conditional on the background set, and reporting it without naming that
set underspecifies it.**

The study has been relying on the argument that a background identical in the
focal and every reference arm cannot bias τ. That argument is correct and
insufficient. A shared background cannot *bias* τ, but it can decide **whether τ
exists**:

| background | B `o_A` | B `o_Q` | `C_L3` control |
|---|---|---|---|
| none at all (load k=2) | +0.000 | **+0.000** | 0.000 |
| `U_LEX_FORBID3 + U_NUM_MAXINT + U_FMT_COLON1` (8 runs) | 0.000–0.125 | **+0.125 … +0.400** | 0.000 |
| `U_LEX_FORBID3 + U_NUM_MAXINT + U_FMT_PAREN1` (2 runs) | 0.000 | **+0.000, +0.075** | 0.000 |
| `U_LEX_FORBID3 + U_NUM_MAXINT + X_NO_EXCLAM` | 0.000 | **+0.000** | 0.000 |

`U_FMT_COLON1` is "use exactly one colon in the answer". It supplies B with a
boundary-capable mark that B does not reliably produce on its own; B's colon count
falls from 0.325 to 0.025 when it is swapped out, and its interference falls with
it. The matched control never moves, so this is not the run being easier.

Most of what Rounds 1–4 measured as **B's** directional interference is an
interaction between B and a background member. `S_SEMICOLON`'s is not: it is
positive in all 18 run-cells and does not need a colon.

**A second methodological finding.** The registry's satisfiability screen is
written pair by pair and generalises to nothing. It returns `ok` for
`U_FMT_COLON1` × "a colon in every sentence" — impossible above one sentence — and
for `U_FMT_NOCOMMA` × "a comma in every sentence". It even returns `ok` for the
very relation it was written to catch (`U_FMT_SEMI2` × a per-sentence semicolon
rule) when that rule carries an unrecognised family name. A general form is
implemented in `extensions.punctuation_conflicts` and enforced for every
hypothesis-driven design here; a test asserts the registry screen still misses
the colon case, so that if it is ever generalised the redundancy is noticed
rather than left as dead code.

---

## 5. The causal status of the claim

Two instruments were tried for a mediator-blocking intervention and **both
failed**, for different and separately diagnosable reasons:

* the **system-message scaffold** failed because its sham could not be made inert
  (E1);
* the **numbered prohibitions** failed on compliance, in two independent
  backgrounds. `Do not use a semicolon to join two complete sentences.` left
  semicolon splices at 2.15 against a control's 2.38 in one background and 1.45
  against 1.35 in the other — the model simply went on doing it, while obeying the
  semicolon *requirement* in the same prompt. `Do not use a comma to join two
  complete sentences.` was over-applied into a total comma ban (6.58 → **0.000**
  and 6.55 → **0.050**). The pre-registered stop condition applied and those
  outcomes are not interpreted as the intervention they were meant to be.

The comma ban was nevertheless a real manipulation, and it produced the round's
only **route-selective** result, replicated across both backgrounds: it made **B**
worse (o_Q excess 0.000 → 0.250 and 0.125 → 0.300) and left `S_SEMICOLON`
untouched (0.325/0.375 → 0.275/0.200 and 0.850/0.450 → 0.875/0.475). B builds its
long sentences out of comma-joined clauses and a comma ban damages its ability to
reach the count; the semicolon route does not use commas and is indifferent. This
is a post-hoc reading of a manipulation that was not the one specified, and is
reported at that strength.

**No mediator-blocking evidence is claimed.** What the study has instead is two
*experimental manipulations of the trigger*, each with a matched control:

* **dose–response** (E4b): demanded semicolons 2 → 4 → 6 moves collapse
  0.013 → 0.950 → 0.938, while four **commas** at the same dose leave it at 0.000;
* **target substitution** (E5a): the identical instruction, producing the
  identical behaviour, causes no failure when the target counts paragraphs.

Both are interventions on the cause, not observations of a correlation. Neither
shows that blocking the strategy would prevent the failure, and that is not
asserted.

Two further controls exclude the obvious alternatives:

* **it is not compositional difficulty.** The most damaging arm is among the
  easiest to satisfy alone (`X_SEMICOLON_TOTAL4`: own-rule failure 0.050 in
  isolation → A-failure 0.988), while the hardest arm in the set does less damage
  (`X_COLON_TOTAL4`: 0.500 → 0.525) and `C_L3` (0.225) does none.
* **it is not ability.** At N = 6 the sentence count is bimodal — 1 or exactly 6,
  nothing between (0.47 / 0.53 in `o_A`). A strategy is being selected, not an
  ability degrading.

---

## 6. The narrowest claim the evidence supports

> For `Qwen/Qwen3-4B-Instruct-2507` at bf16, temperature 0.7, on short expository
> prompts: an instruction that requires **semicolons in a quantity at or above the
> target sentence count** is realised as a single clause-chained sentence in a
> large fraction of generations, and an exact-sentence-count target then fails by
> undershoot. The effect is 0.375–1.000 in paired excess over a matched control,
> reproduces across topics, wordings, target counts 2–6, background sets and
> compositional loads, and is carried by a visible and countable strategy: one
> full stop, ~1.2 boundary-capable marks per lost sentence boundary, and the
> semicolon instruction itself satisfied.

Everything outside that sentence is either unsupported or refuted:

* not other marks — colons and dashes per sentence give exactly 0.000;
* not per-sentence scoping — that is protective;
* not other structural units — paragraph counts are untouched;
* not other model families — gemma has the disposition and no interference;
* not the registered (A, B) pair — B needs a colon in the background;
* not "punctuation volume" — four commas cost −0.025.

---

## 7. Open items, stated as such

1. **The paragraph-side substitution route is untested.** `X_LINEBREAK_EACH` was
   not obeyed. A differently worded instruction might test it.
2. **The numerical-family test needs a usable target.** "Four distinct integers"
   fails 0.725 unaided; "at least two integers" would be a proper test.
3. **No mediator-blocking intervention exists.** A third instrument would have to
   avoid both failure modes — not a system-message clause, and not a negative
   instruction this model ignores.
4. **The disposition's generality is 2 of 2 models and worth its own study.** That
   is a different question from the interference one, and no third family was run
   because the pre-registered rule made a third family contingent on the
   interference reproducing, which it did not.
5. **Order effects were measured throughout but are not explained.** `S_SEMICOLON`
   is order-insensitive; `X_COLON_TOTAL4` swings 0.850 → 0.175 purely through
   compliance; B is `o_Q`-dominant. No account is offered.
