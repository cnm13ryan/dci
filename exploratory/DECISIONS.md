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

---

# Round 5 — is the mechanism robust, causally specific, and general?

Rounds 1–4 produced one candidate mechanism on one pair, one model and one
target count, and a repaired verifier. Round 5 asks whether that mechanism
survives a sham control, a fresh sample, other marks, other target counts, other
structural units, another constraint family, and another model family.

**The replication criterion is not positive DCI.** A run counts as a replication
only if the whole chain reproduces:

    trigger  ->  the same interpretable failure strategy  ->  target failure

and, where an intervention is available, the mechanism-specific intervention
selectively reduces *both* the strategy and the failure while leaving a matched
control alone. An arm that fails the target by some other route is a different
phenomenon wearing the same summary statistic.

## Standing hypotheses

| | claim | what it predicts that the others do not |
|---|---|---|
| **M1** delimiter substitution | a per-sentence demand for a mark that can grammatically stand where a sentence boundary would stand is satisfiable by *replacing* boundaries with the mark | collapse tracks the mark's **boundary capability**, not its frequency, not per-sentence scoping alone, not generic burden |
| **M2** per-sentence scoping | any per-sentence requirement makes many sentences costly, so fewer are written | a per-sentence **comma** rule collapses too; a whole-answer semicolon rule does not |
| **M3** mark quantity | demanding many marks of any kind pushes toward clause-chaining | **the same number** of semicolons demanded without per-sentence scoping collapses just as much |
| **M4** generic instruction burden | behaviour moves whenever the system message gains any clause | a **sham** clause reduces failure as much as a real boundary reminder |
| **M5** B is a separate route | B loses count while planning a strictly growing structure, not by substituting a delimiter | B's failures carry no substitution signature and respond differently to the ladder |

D3 already weighed against M2 and M3 with registry wordings. E3 re-tests both
under wordings matched across marks, which D3 could not do.

**Verifier policy for every Round 5 run.** The corrected segmenter is primary;
the pre-repair segmenter is carried as a sensitivity column and never as the
headline. Every run preserves raw generations, the design, the config, the
environment record and the model fingerprint, and no run directory is reused.

---

## E1 — sham-controlled scaffold-strength ladder

**Why.** D2 showed that adding `Write each sentence on its own line.` to the
system message removed B's excess failure and halved `S_SEMICOLON`'s. It had no
sham. Nothing in D2 excludes M4: a system message that gains *any* extra clause
may simply raise compliance attention.

**The ladder.** One factor, four levels, applied to the system message only, so
the numbered constraint list stays byte-identical and the load stays k=5.

| level | clause | chars |
|---|---|---|
| none | *(the protocol's message, unchanged)* | 0 |
| weak | ` Remember that each sentence ends with a full stop.` | 50 |
| strong | ` Write each sentence on its own line.` | 36 |
| **sham** | ` Write each sentence in a plain style.` | 37 |

The sham shares the strong clause's opening three words, its imperative form and
its length to within one character, and says nothing about boundaries. The
ordering none < weak < strong is an *assumption about instruction strength*, not
a measurement; a result that violates it is a violation, not a nuisance.

**Fixed.** A; the background set; load k=5; both orders; wording 0; 20 pilot
tasks (the same 20 as Stage B and D2, so the no-scaffold cells are a direct
replication); 2 replicates; the same decoding and the same model revision.

**Arms.** B (focal), `S_SEMICOLON` (the strongest interferer), `C_L3` (the
low-interference control). 1600 generations.

**Primary readout.** Paired excess of each arm's A-failure over `C_L3` within
each (scaffold, order) cell, and the change in that excess across scaffold
levels. Intervals are cluster bootstraps over the 20 tasks.

**Also measured, per row.** Exact sentence count; severe collapse (one sentence);
non-collapse failure; the arm's own compliance (does the model *keep* the added
instruction while dropping A?); periods; semicolons; newlines; and literal
scaffold compliance where it is mechanically checkable.

**Outcomes and readings, written before the run.**

| observation | reading |
|---|---|
| strong ≪ none **and** sham ≈ none | the scaffold's *content* is what acts — **M4 rejected**, D2 survives |
| sham ≈ strong | **M4 supported**: D2's recovery is a demand characteristic of a longer system message, and the intervention evidence for the mechanism is withdrawn |
| weak strictly between none and strong | graded boundary salience; substitution is a *difficulty*, not a default |
| weak ≈ strong | a bare reminder suffices; substitution is a **default choice**, not an inability |
| `C_L3` moves under any scaffold | the scaffold is a general A-helper; only the excess over `C_L3` may be read |
| an arm's own compliance falls with its A-failure | it is not trading A away; the substitution account weakens for that arm |

**Stop condition.** If the sham matches the strong scaffold, stop the causal
line, record M4 as supported, and do not present any scaffold result as
mechanistic evidence.

---

## E2 — replication on fresh instances and on a fresh wording

**Why.** Every number in Rounds 1–4 comes from the same 20 pilot topics under
wording 0. Two ordinary explanations survive that: the effect is a property of
those 20 topics, or of that one phrasing of each instruction.

**Two runs, one change each.** Changing both at once would leave a failed
replication uninterpretable.

| run | tasks | wording | what it tests |
|---|---|---|---|
| **E2a** | 20 `burned`-split topics, never used in this study | 0 (as before) | instance generality |
| **E2b** | the same 20 pilot topics as Stage B | 2 | phrasing generality |

The `burned` split holds topics already spent by the protocol's own development
and therefore unusable by the confirmatory study, which is exactly what makes
them free to spend here. Wording 2 is in the escalation pool; wordings 6 and 7
are permanently held out for Gate 3b and are not touched.

**Arms.** B (focal), `S_SEMICOLON`, `C_L3`, `C_O2`. Two controls rather than one,
so "the control moved" and "everything moved" are distinguishable. Both orders,
2 replicates, no scaffold, load k=5. 520 generations each.

**Outcomes and readings.**

| observation | reading |
|---|---|
| both runs reproduce B's `o_Q` excess and `S_SEMICOLON`'s excess in both orders | the effect is not the topics and not the phrasing |
| E2a reproduces, E2b does not | the effect is **phrasing-specific**; it is a fact about wording 0, and every claim must be restated at that scope |
| E2b reproduces, E2a does not | the effect is **instance-specific**; the pilot topics are doing the work |
| neither reproduces | the Round 1–4 result does not survive replication. Stop. |
| the collapse route reproduces but the A-failure does not, or vice versa | the chain is broken; report the strategy and the outcome separately and do not call it the same phenomenon |

---

## E3 — target-count generalization, N ∈ {2, 3, 4, 5, 6}

**Why.** Every result so far is at N = 4. Two accounts fit that equally well and
differ everywhere else:

* **substitution as a strategy** — the model resolves the per-sentence mark
  demand by writing one clause-chained sentence. What it does is then largely
  *independent of N*, because it is not trying to hit N at all.
* **substitution as a difficulty response** — the model collapses because
  producing four sentences each carrying a semicolon is hard. Then the collapse
  should ease as N falls and worsen as N rises.

**The sweep.** Five runs, identical but for the target's `n`. The targets at
n = 2, 3, 5, 6 are `X_A2`, `X_A3`, `X_A5`, `X_A6`; they use the registry's own
`exact_sentence_count` family and its certified templates, so only the number in
the sentence changes. N = 4 is the registry's `A` and doubles as an internal
replication of Stage B on this apparatus.

**Arms.** B, `S_SEMICOLON`, `C_L3`. Both orders, the same 20 pilot tasks, 2
replicates, wording 0, load k=5, no scaffold. ~2000 generations in total.

N = 2 is the sharpest cell: it is the *easiest* target for a per-sentence
semicolon rule — two sentences, two semicolons, no strain — and collapse to one
sentence still fails it.

**Outcomes and readings.**

| observation | reading |
|---|---|
| `S_SEMICOLON` collapse rate roughly flat in N, including at N = 2 | substitution is a **strategy**, not a difficulty response; the mechanism is N-general |
| collapse rises monotonically with N | it is a **difficulty response**; restate the claim as compositional strain, not delimiter substitution |
| collapse near zero at N = 2 and high at N = 6 | as above, and the N = 4 result is one point on a difficulty curve |
| B's excess rises with N | B's route is capacity-limited and is not the mark route (**M5**) |
| `C_L3` failure rises steeply with N | the target itself is getting harder; excesses may be compared only within an N, never across |

**Sanity condition.** `C_L3`'s own failure rate measures the difficulty of the
target at each N with no interfering arm. If it is already near 1 at N = 6 there
is no headroom and that cell is uninformative — a measurement limit to report,
not a finding.

---

## E4 — the mark factorial: what exactly triggers collapse?

**Why.** D3 compared `S_SEMICOLON`, `U_FMT_SEMI2` and `S_TWOCOMMA` and concluded
substitution. Those three carry three different registry wordings, three
different quantities ("a semicolon", "exactly two semicolons", "exactly two
commas") and two different scopes. Any of those could be the operative
difference. E3 fixes all of it.

**The design.** One authored wording family, `Use at least one {mark} in every
sentence.`, instantiated at four marks. The mark is then the ONLY thing that
varies across four of the arms.

| arm | mark | scope | boundary-capable | M1 | M2 | M3 |
|---|---|---|---|---|---|---|
| `X_SEMICOLON_EACH` | `;` | per sentence | yes | collapse | collapse | collapse |
| `X_COLON_EACH` | `:` | per sentence | yes | collapse | collapse | collapse |
| `X_DASH_EACH` | `— – --` | per sentence | yes | collapse | collapse | collapse |
| `X_COMMA_EACH` | `,` | per sentence | **no** | **no collapse** | **collapse** | collapse |
| `X_SEMI_TOTAL4` | `;` | whole answer, ≥4 | yes | **no collapse** | no collapse | **collapse** |
| `S_SEMICOLON` | `;` | per sentence | yes | collapse | collapse | collapse |
| `B` | — | cross-sentence | n/a | separate route (M5) | | |
| `C_W3` | words | per sentence | no | no collapse | **collapse** | no collapse |
| `C_L3` | letter | per sentence | no | no collapse | **collapse** | no collapse |

The three hypotheses are separated by three cells, each of which one theory
requires and another forbids:

* `X_COMMA_EACH` — a per-sentence demand that cannot be met by replacing a
  boundary. **M2 needs it to collapse; M1 needs it not to.**
* `X_SEMI_TOTAL4` — the same mark and the same *quantity* the per-sentence rule
  implies at N = 4, with the per-sentence scoping removed. **M3 needs it to
  collapse; M1 and M2 need it not to.**
* `X_SEMICOLON_EACH` vs `S_SEMICOLON` — the same rule under two wordings. If
  these differ, the effect is partly phrasing and the whole factorial is weakened.

**Background change, and why.** The standard background contains `U_FMT_COLON1`
("exactly one colon in the answer"), which is flatly unsatisfiable alongside a
colon in each of four sentences. The registry's own satisfiability screen
returns **`ok`** for that pair — it hard-codes the semicolon and comma cases and
generalises to nothing else (verified 2026-08-11; a general screen has been
added in `extensions.punctuation_conflicts` and is now enforced for every
hypothesis-driven design). `U_FMT_COLON1` is therefore replaced by
`U_FMT_PAREN1`, the one format-family member that counts a mark no arm demands.
`S_SEMICOLON` is kept in the factorial precisely so the background swap is
checkable against Stage B.

**Fixed.** A (N = 4), load k=5, both orders, wording 0, the same 20 pilot tasks,
2 replicates, no scaffold. 1120 generations.

**Outcomes and readings.**

| observation | reading |
|---|---|
| collapse in {`;`, `:`, `—`} and not in `,` | **M1 supported**, M2 rejected |
| collapse in all four per-sentence marks | **M2 supported**, M1 rejected |
| `X_SEMI_TOTAL4` collapses like `X_SEMICOLON_EACH` | **M3 supported**, M1 and M2 rejected |
| collapse graded `; > — > :` | consistent with M1 and with grammatical substitutability specifically, since a colon's listing use competes with its clause-joining use |
| `X_SEMICOLON_EACH` ≠ `S_SEMICOLON` | phrasing matters; report the factorial at wording scope only |
| an arm collapses while failing its **own** rule | not substitution — it is not even satisfying the instruction it was given |

---

# Round 5 outcomes

### E1 — sham-controlled scaffold ladder · `runs/stageE1_ladder_20260810T231640Z`

1600 generations, 38.1 min, 0 technical failures, 0 truncations. The
no-scaffold cells replicate Stage B and D2 closely (`S_SEMICOLON` excess 0.625
`o_A` / 0.500 `o_Q` against D2's 0.650 / 0.575; B 0.300 `o_Q` against 0.275).

**Paired excess over `C_L3`, the pre-registered readout:**

| arm / order | none | weak | strong | **sham** |
|---|---|---|---|---|
| `S_SEMICOLON` `o_A` | 0.625 | 0.350 | 0.275 | **0.350** |
| `S_SEMICOLON` `o_Q` | 0.500 | 0.200 | 0.250 | **0.400** |
| B `o_Q` | 0.300 | 0.075 | 0.100 | **0.150** |
| B `o_A` | 0.025 | 0.050 | 0.000 | **0.000** |
| `C_L3` (the control itself) | — | 0.000 | 0.000 | **0.000** |

**The contrast that decides M4** — each boundary scaffold against the SHAM, not
against no scaffold, so the number is boundary *content* with message length and
imperative form already subtracted:

| arm / order | strong − sham | weak − sham |
|---|---|---|
| `S_SEMICOLON` `o_A` | −0.075 [−0.275, +0.150] | 0.000 [−0.225, +0.225] |
| `S_SEMICOLON` `o_Q` | −0.150 [−0.300, 0.000] | −0.200 [−0.400, −0.025] |
| B `o_Q` | −0.050 [−0.150, +0.050] | −0.075 [−0.150, 0.000] |
| B `o_A` | 0.000 | +0.050 |

**Row 2 of the pre-registered table fired: M4 is largely supported.** A clause
that says nothing whatever about sentence boundaries — `Write each sentence in a
plain style.` — reproduces most of D2's recovery. In `o_A` no boundary-specific
effect is detectable at all; in `o_Q` a residual of −0.15 to −0.20 survives, and
only one of those two intervals excludes zero.

**Consequence, applied rather than noted: the D2 intervention is withdrawn as
mechanistic evidence.** D2 had no sham, so it could not distinguish "the boundary
reminder blocks the substitution route" from "an extra system-message clause
raises compliance attention". E1 shows the second explains most of it. Every
claim that rested on D2's causal leg is downgraded to correlational.

**The ladder ordering assumption failed.** `weak` and `strong` are
indistinguishable, and in `o_Q` the weak reminder is *better*. Whatever the
scaffolds do, it is not graded by how forcefully they specify the format.

**The sham is not inert, and that is the deeper problem.** It changed the text
in exactly the direction the boundary scaffolds do:

| arm | metric | none | sham | strong |
|---|---|---|---|---|
| B | commas | 9.19 | **7.42** | 8.38 |
| B | words | 171.6 | **160.0** | 167.0 |
| `S_SEMICOLON` | sentences | 2.34 | **2.90** | 3.22 |
| `S_SEMICOLON` | newlines | 0.75 | **1.16** | 2.01 |

`Write each sentence in a plain style.` evidently pushes toward shorter, simpler,
less chained sentences. So it is a **style** manipulation, not a pure length
control, and it plausibly acts on the very behaviour under study. The design
conclusion: for this outcome a system-message clause **cannot** be made inert,
because almost any instruction about how to write sentences touches sentence
structure. A system-message scaffold is therefore the wrong instrument for the
causal leg, and no further version of it will be run.

**What survives.** The correlational chain is untouched and was replicated in the
same run: the trigger produces the strategy (23/23 and 20/20 collapsed
`S_SEMICOLON` rows satisfy the semicolon rule while carrying ≈1.2 boundary-capable
marks per lost boundary) and the strategy accompanies the failure. The scaffolds
are not general A-helpers — `C_L3` is at exactly 0.000 failure under all four
conditions — so whatever they do is specific to the arms using a chaining route.

**Replacement plan for the causal leg.** The instrument must prohibit the
*substitution* without mentioning sentences, against a sham that prohibits an
equally arbitrary punctuation usage off the route. Pre-registered below as E6b,
after the factorial identifies which mark is decisive.

### E2 — replication on fresh instances and on a fresh wording

`runs/stageE2a_freshtasks_20260810T232938Z` (20 `burned` topics, wording 0) and
`runs/stageE2b_freshwording_20260810T234101Z` (the Stage B topics, wording 2).
520 generations each, 0 technical failures, 0 truncations.

**Paired excess over `C_L3`:**

| arm / order | Stage B (pilot, w0) | **E2a** (fresh topics, w0) | **E2b** (pilot, w2) |
|---|---|---|---|
| `S_SEMICOLON` `o_A` | 0.617 | 0.375 | 0.600 |
| `S_SEMICOLON` `o_Q` | 0.550 | 0.375 | 0.550 |
| B `o_A` | 0.050 | 0.025 | **0.525** |
| B `o_Q` | 0.300 | 0.550 | **0.750** |
| `C_O2` (second control) | ~0 | 0.000 / 0.025 | 0.000 / 0.000 |

Both controls sit at exactly 0.000 corrected failure in the fresh-wording run
and within 0.025 of it in the fresh-topic run. The target is not getting harder;
the arms are doing the damage.

**`S_SEMICOLON` replicates completely — outcome AND strategy.**

| | Stage B | E2a (fresh topics) | E2b (fresh wording) |
|---|---|---|---|
| collapse to exactly 1 sentence | 0.517–0.600 | 0.250–0.300 | 0.525–0.550 |
| boundary marks per lost boundary | 1.16–1.24 | 1.19–1.20 | 1.09–1.19 |
| commas per lost boundary | 0.21–0.29 | 0.33–0.42 | 0.37–0.44 |
| **its own semicolon rule satisfied while collapsed** | (not recorded) | **100%** | **100%** |
| words | 48–50 | 45–47 | 40–41 |

The chain **trigger → strategy → target failure** reproduces on unseen topics and
on a different phrasing, with the same numerical signature. This is the strongest
evidence in the study.

**B does NOT replicate as the same phenomenon.** Its *outcome* replicates and
grows — the excess is larger under both changes — but its *strategy* is
phrasing-dependent:

| | wording 0 | wording 2 |
|---|---|---|
| wording of B | "Make each sentence strictly longer than the preceding sentence when measured by word count." | "Every sentence after the first must contain more words than the sentence before it." |
| collapse to 1 sentence | 0.300 (`o_Q`) | **0.050** |
| sentence count distribution | 1 or 4 | **2 or 3** |
| B's own rule satisfied | 0.05–0.21 | **0.60** |
| words | 148–192 | 108 |

Under wording 0, B writes one enormous comma-chained run-on and fails its own
growth rule. Under wording 2 it writes two or three sentences that *do* grow, and
undershoots the count. Same direction, same target failure, **different route.**

**Reading, against the pre-registered replication criterion.** The criterion is
trigger → *the same interpretable failure strategy* → target failure.
`S_SEMICOLON` meets it. **B meets only the outcome half**, so the two arms must
not be reported as one phenomenon. B is an instruction that makes the target
harder by several routes; `S_SEMICOLON` is a specific, reproducible strategy.

**Instance and phrasing generality: both established for the mark route.** The
E2a/E2b split was designed so that a failure would be attributable; neither
failed.

---

## E7 — the replacement causal test: a double dissociation, no sham required

**Why.** E1 killed the system-message scaffold as an instrument. The problem was
not that the sham was badly chosen but that no clause about *how to write
sentences* can be inert with respect to *how many sentences get written*. An
instrument is needed whose control is not a supposedly-inert clause but **another
active treatment aimed at a different route.** Then neither condition has to be
inert; each is the other's control, and the prediction is a pattern rather than a
single reduction.

**The three prohibitions.** All added as a sixth numbered instruction, so the
load is k=6 in *every* cell and nothing is compared across loads. All three have
the same grammatical form and comparable length, and none mentions sentence
counts, line breaks or the word "paragraph".

| condition | instruction | route it closes |
|---|---|---|
| `X_NO_EXCLAM` | `Do not use any exclamation marks.` | **neither** — the off-route control |
| `X_NO_SEMI_SPLICE` | `Do not use a semicolon to join two complete sentences.` | the `S_SEMICOLON` substitution route |
| `X_NO_COMMA_SPLICE` | `Do not use a comma to join two complete sentences.` | B's comma-chained run-on route (E2a) |

**Arms.** `S_SEMICOLON`, B, `C_L3`. Both orders, wording 0, the 20 pilot tasks,
2 replicates. 3 prohibitions × 3 arms × 2 orders × 20 × 2 = 720 contrast rows.

**The predicted pattern — a double dissociation.**

| | `S_SEMICOLON` collapse | B collapse | `C_L3` |
|---|---|---|---|
| `X_NO_SEMI_SPLICE` − `X_NO_EXCLAM` | **↓ large** | ≈ 0 | ≈ 0 |
| `X_NO_COMMA_SPLICE` − `X_NO_EXCLAM` | ≈ 0 | **↓ large** | ≈ 0 |

| observation | reading |
|---|---|
| the double dissociation appears | **M1 and M5 both causally supported**, and M4 is excluded by construction: a generic-clause account cannot produce a crossed pattern |
| both prohibitions reduce both arms equally | **M4**: it is the extra clause, not its content. The mechanism claim has no causal leg and must be reported as correlational only |
| the semicolon prohibition reduces `S_SEMICOLON` and the comma one does nothing to B | M1 supported; B's route is not comma splicing and remains unexplained |
| neither prohibition changes anything | the prohibitions were not obeyed — check the splice proxy before drawing any conclusion |

**Compliance is measured, not assumed.** `extensions.splice_count` counts marks
immediately followed by a clause-initial pronoun or connective. It is a **proxy**
and is labelled one wherever it appears: determiners were removed from its word
list because `The parts are a lever; a spring; a base.` is a list rather than a
clause join, so the proxy can only **under**-count. Exact counts of semicolons,
commas, periods and sentences are reported alongside it.

**Stop condition.** If the splice proxy shows the prohibitions were not obeyed,
report that and do not interpret the outcome at all.

---

## E5 — where does it stop? Another structural unit, then another family

**Why.** Every positive result so far is about one target: a count of *sentences*,
whose delimiter is a full stop, interfered with by a mark that can stand where a
full stop stands. The claim is only worth stating at the width the evidence
supports, so the next two runs are chosen to find the edge rather than to add
another confirmation.

### E5a — the structural twin: paragraphs

Same shape, different unit. The target counts **paragraphs**, whose delimiter is
a blank line; the substitutable delimiter is a **single newline**, which can
stand where a blank line would without being one.

| arm | rule | on the paragraph route? | prediction |
|---|---|---|---|
| `X_LINEBREAK_EACH` | a line break inside every paragraph | **yes** | large excess |
| `X_SEMICOLON_EACH` | a semicolon in every sentence | no — it substitutes for a *sentence* boundary | **≈ 0** |
| `B` | each sentence longer than the last | no | ≈ 0 |
| `C_L3` | every sentence begins with S | no (control) | 0 |

`X_SEMICOLON_EACH` is the specificity test: the same instruction that destroys the
sentence count should leave the paragraph count alone, because a semicolon cannot
stand where a blank line stands.

**Stop condition, stated first.** In every run so far the model produced exactly
**1.000** blank-line-separated block on average — it does not write paragraphs
unprompted. If `X_PARA4` in isolation already fails often, there is no headroom
and the cell measures the target's difficulty rather than any interference. The
isolated primitive rows decide that, and the answer is reported either way.

### E5b — a different constraint family: counting integers

Target `U_NUM_FOURDISTINCT` ("four distinct integers"), a **numerical**
whole-answer count with no delimiter at all. Arms `X_SEMICOLON_EACH` (focal),
`B`, `C_L3`. Background named explicitly as `U_LEX_FORBID3, U_FMT_COLON1,
U_LEX_NOLY` because the standard background's `U_NUM_MAXINT` ("at most two
integers") is flatly incompatible with a four-integer target.

| observation | reading |
|---|---|
| no arm impairs the integer count | the mechanism is **specific to delimited-unit targets**; this is the boundary of the claim |
| `X_SEMICOLON_EACH` impairs it too | the mechanism is broader than delimiter substitution — most likely via answer length, since collapsed answers are shorter — and the account must be rewritten |
| `B` impairs it | consistent with B being a general difficulty manipulation rather than a route (E2) |

520 generations each, both orders, wording 0, 20 pilot tasks, 2 replicates.

### E4 — the mark factorial · `runs/stageE4_marks_20260811T000148Z`

1120 generations, 18.4 min, 0 technical failures, 0 truncations.

**Paired excess over `C_L3` (A-failure), both orders:**

| arm | mark | scope | `o_A` | `o_Q` | collapse `o_A`/`o_Q` |
|---|---|---|---|---|---|
| `X_SEMICOLON_TOTAL4` (as `X_SEMI_TOTAL4`) | `;` | **whole answer, ≥4** | **1.000** [1.000, 1.000] | **1.000** [1.000, 1.000] | 1.000 / 0.975 |
| `X_SEMICOLON_EACH` | `;` | per sentence | 0.750 [0.625, 0.875] | 0.675 [0.475, 0.850] | 0.725 / 0.600 |
| `S_SEMICOLON` | `;` | per sentence (registry wording) | 0.725 [0.550, 0.875] | 0.750 [0.625, 0.875] | 0.725 / 0.625 |
| `X_COMMA_EACH` | `,` | per sentence | 0.050 | 0.025 | **0.000** |
| **`X_COLON_EACH`** | `:` | per sentence | **0.000** | **0.000** | **0.000** |
| **`X_DASH_EACH`** | `—` | per sentence | **0.000** | **0.000** | **0.000** |
| `C_W3` | words | per sentence | 0.000 | 0.000 | 0.000 |
| **`B`** | — | cross-sentence | **0.000** | **0.000** | **0.000** |

**Two of my three pre-registered predictions were wrong, and the third was right
for the wrong reason.**

1. **The effect is specific to the semicolon, not to boundary-capable marks.**
   I predicted collapse for `;`, `:` and `—` alike. Colon and dash produce
   **zero** failures. The model writes four clean sentences carrying 3.65 colons
   or 7.58 dashes — it uses them *inside* sentences:

   > `Swimmers exhale underwater to reduce their lung pressure – allowing the body to move more efficiently through water.`
   > `This helps maintain a neutral buoyancy – which is essential for smooth and steady swimming strokes.` …

   `MARK_IS_BOUNDARY_CAPABLE` was a judgement about English. The operative
   property is narrower and empirical: **which mark this model actually deploys
   as a full-stop replacement.** For Qwen3-4B that is the semicolon and nothing
   else tested.

2. **Per-sentence scoping is not required, and is not even the strongest form.**
   I predicted `X_SEMI_TOTAL4` — a whole-answer floor of four semicolons — would
   *not* collapse, as the scoping control. It collapses **100%**, harder than
   either per-sentence semicolon rule. **M2 is dead** (five per-sentence rules
   in this run and only the semicolon ones collapse) and **M3 is the surviving
   account**: what matters is how many semicolons are demanded.

   > `A doorbell circuit completes a sound when the button is pressed; this closes the circuit and allows current to flow; the current activates an electromagnet; which causes a clapper to strike a bell; (this creates the audible ring).`

   Four semicolons, one sentence, one full stop, and its own rule satisfied.

   The isolated primitive settles it: `X_SEMI_TOTAL4` **alone**, with no target
   and no load, produces **1.075 sentences**. Against `X_COLON_EACH` 8.175,
   `X_DASH_EACH` 8.075, `C_L3` 6.300, `S_SEMICOLON` 4.025.

3. **`X_SEMICOLON_EACH` ≈ `S_SEMICOLON`** (0.750/0.675 against 0.725/0.750). The
   effect is wording-invariant, so the factorial's comparisons are clean.

**An unplanned finding: B's interference vanished.** B's excess is 0.000 in both
orders here, against 0.300–0.400 in Stage B, E1 and E3-N4 on the *same* 20 tasks,
the *same* wording, the same load and the same orders. The single difference is
one background member: `U_FMT_COLON1` ("exactly one colon in the answer") was
replaced by `U_FMT_PAREN1` to make the colon arm satisfiable. B's colons fall
from 0.28–0.30 to 0.000 and its failures with them. A dedicated matched pair
(`E4c`) is running to confirm that one substitution is responsible.

**Revised mechanism, stated at the width the evidence supports.**

> When Qwen3-4B is asked for several semicolons in a short answer, it spends them
> as clause joins inside a single sentence rather than distributing them across
> sentences. Any target that counts sentences then fails by undershoot. The
> trigger is the **semicolon in quantity**; per-sentence phrasing is one way to
> demand quantity, not the mechanism.

**Next, pre-registered before running:** `E4b` crosses quantity with mark at one
scope and one wording — semicolons at ≥2, ≥4, ≥6, against colons, dashes and
commas at ≥4. If the account is right, only the semicolon arms collapse and they
do so monotonically in the count. If instead every mark at ≥4 collapses, the
mechanism is about demanded punctuation volume and the semicolon is incidental.

### E4b — quantity crossed with mark, at one scope and one wording

`runs/stageE4b_totals_20260811T002409Z`. 880 generations, 5.5 min, 0 technical
failures. All six arms use the identical template `Use at least {n} {marks} in
the whole answer.`, so nothing varies but the number and the mark.

**Paired excess over `C_L3` (A-failure):**

| arm | demanded | `o_A` | `o_Q` | severe collapse `o_A`/`o_Q` | marks produced |
|---|---|---|---|---|---|
| `X_SEMICOLON_TOTAL2` | 2 `;` | 0.200 [0.075, 0.325] | 0.275 [0.150, 0.400] | 0.025 / 0.000 | 2.05 / 1.93 |
| `X_SEMICOLON_TOTAL4` | 4 `;` | **0.975** [0.925, 1.000] | **0.975** [0.925, 1.000] | 1.000 / 0.900 | 3.75 / 3.23 |
| `X_SEMICOLON_TOTAL6` | 6 `;` | **0.975** [0.925, 1.000] | **1.000** [1.000, 1.000] | 1.000 / 0.875 | 6.20 / 4.88 |
| `X_COLON_TOTAL4` | 4 `:` | **0.850** [0.725, 0.950] | 0.175 [0.075, 0.275] | 0.550 / 0.100 | 4.00 / 1.60 |
| `X_DASH_TOTAL4` | 4 `—` | 0.275 [0.150, 0.400] | 0.475 [0.300, 0.675] | **0.000 / 0.000** | 4.88 / 4.28 |
| `X_COMMA_TOTAL4` | 4 `,` | **−0.025** | 0.050 | 0.000 / 0.000 | 4.25 / 3.28 |

**A dose–response in semicolons, with a threshold at the target count.** Two
semicolons cost 0.20–0.28; four cost 0.975. The step sits between 2 and 4 —
i.e. at about the number of sentences the target asks for. Six adds nothing,
because one sentence already absorbs any number.

**The comma is inert at the same dose** (−0.025 / 0.050, four commas produced,
four sentences kept). It is the negative control the design needed and it holds.

**The isolated primitives are the cleanest statement in the study.** The arm
alone — no target, no background, nothing to interfere with:

| instruction alone | sentences produced |
|---|---|
| `Use at least 2 semicolons in the whole answer.` | **1.225** |
| `Use at least 4 semicolons in the whole answer.` | **1.125** |
| `Use at least 6 semicolons in the whole answer.` | **1.075** |
| `Use at least 4 colons in the whole answer.` | 4.500 |
| `Use at least 4 dashes in the whole answer.` | 4.575 |
| `Use at least 4 commas in the whole answer.` | 3.875 |
| `Write exactly 4 sentences.` | 4.000 |
| (`C_L3`, every sentence begins with S) | 6.575 |

Asking this model for **two semicolons and nothing else** makes it write one
sentence. That is a disposition of the model, present before any target exists,
and the interference is what happens when a sentence-count target has to fight it.

**Per-sentence scoping turns out to be PROTECTIVE, which reverses the naive
reading of D3.** The colon shows it directly, at the same dose:

| colon rule | colons produced | sentences | excess |
|---|---|---|---|
| `at least one colon in every sentence` (E4) | 3.65 | **4.000** | **0.000** |
| `at least 4 colons in the whole answer` (E4b, `o_A`) | 4.00 | **1.775** | **0.850** |

Four colons either way. The per-sentence rule *requires them to be spread out*
and the sentence count survives; the whole-answer floor permits concentration and
the model concentrates. D3 read the scope difference as "per-sentence scoping
causes substitution". It is the opposite: per-sentence scoping **forces
distribution**, and the semicolon is simply the one mark whose chaining pull is
strong enough to defeat that protection.

**The colon's order asymmetry is a compliance difference, not a mechanism
difference.** In `o_A` the model obeys (4.00 colons, arm compliance 0.575) and
places them by writing ` : ` where a full stop would go:

> `Bakeries open early … by 8:00 a.m. : This timing ensures … : Many families rely on the bakery …`

In `o_Q` it largely ignores the rule (1.60 colons, arm compliance 0.050) and keeps
four sentences. Where the colon is actually produced in quantity, it collapses.

**The dash concentrates weakly and differently.** It costs 0.275–0.475 with
**zero** severe collapse — the answers land at 3.5–3.7 sentences, an undershoot
by one rather than a collapse to one. A different failure shape, and one that
would have been invisible without the mode decomposition.

**Unified account, which fits every cell in the study including D3's.**

> The damage comes from **concentrating** demanded punctuation into few
> sentences. A whole-answer floor permits concentration; a per-sentence rule
> requires distribution and therefore partly protects. Marks differ in how
> readily this model concentrates them into boundary positions:
> semicolon ≫ colon > dash ≫ comma. `U_FMT_SEMI2` (exactly two semicolons) did
> not collapse in D3 because two is below the threshold — exactly what
> `X_SEMICOLON_TOTAL2` shows here at 0.20–0.28.

---

## E6 — cross-model replication: `google/gemma-2-9b-it`

**Why.** Everything so far is a fact about `Qwen3-4B-Instruct-2507`. The
disposition E4b isolated — realising "use semicolons" as a single clause-chained
sentence — is a stylistic habit, and stylistic habits are exactly the kind of
thing that differs between training pipelines.

**Model.** `google/gemma-2-9b-it` @ `11c9b309abf73637e4b6f9a3fa1e92e615547819`,
already resident, a different developer, a different tokenizer and a different
size class. Its chat template **rejects the `system` role**, so the system
message is merged into the first user turn, as its own model card prescribes;
the run summary records `prompt_convention` so the two models' prompts are never
silently assumed identical. Batch 8 rather than 16 for the 9B weights.

**The smallest decisive battery.** Four arms, chosen because each one now has a
sharp prediction rather than because it is available:

| arm | Qwen3-4B result | what gemma tests |
|---|---|---|
| `X_SEMICOLON_TOTAL4` | excess 0.975 / 0.975 | is the disposition model-general? |
| `X_SEMICOLON_EACH` | 0.750 / 0.675 | does per-sentence protection behave the same way? |
| `X_COMMA_TOTAL4` | **−0.025 / 0.050** | is the negative control still negative? |
| `C_L3` | 0 by definition | the paired control |

Target A, background `U_LEX_FORBID3, U_NUM_MAXINT, U_FMT_PAREN1` — the same as
E4b, so the comparison across models holds everything else fixed. Both orders,
20 pilot tasks, 2 replicates, wording 0. 520 generations.

**Outcomes and readings.**

| observation | reading |
|---|---|
| semicolon floor collapses gemma too, comma floor does not | the disposition is **not Qwen-specific**; the claim can be stated about instruction-tuned models generally, pending a third family |
| neither arm moves gemma | the whole effect is a fact about **one model**, and every earlier claim must be restated at that scope |
| both semicolon and comma floors move gemma | gemma has a general punctuation-volume sensitivity that Qwen lacks; the marks are not doing the same work in the two models |
| gemma's isolated primitive for the semicolon floor stays near 4 sentences | the disposition is absent even though interference may appear; report them separately |

**A third family is contingent, not planned.** It is worth the download only if
gemma reproduces — one replication and one failure would say the effect is
model-specific without needing a third data point, whereas two replications make
a third worth having.

**Two checks on E4b that were not pre-registered but had to be made.**

*Is the collapse just a hard instruction?* No — arm difficulty is uncorrelated
with interference, and the sign is wrong:

| arm | own-rule failure **in isolation** | A-failure under load | collapse |
|---|---|---|---|
| `X_SEMICOLON_TOTAL4` | **0.050** (easiest but one) | **0.988** | 0.950 |
| `X_SEMICOLON_TOTAL6` | 0.075 | 1.000 | 0.938 |
| `X_DASH_TOTAL4` | **0.000** (easiest) | 0.388 | 0.000 |
| `X_COLON_TOTAL4` | **0.500** (hardest) | 0.525 | 0.325 |
| `C_L3` | 0.225 | **0.013** | 0.000 |
| `X_COMMA_TOTAL4` | 0.050 | 0.025 | 0.000 |

The most damaging arm is among the easiest to satisfy on its own, and the hardest
arm in the set is less damaging than it. Compositional difficulty is excluded.

*Is it a clean trade — target given up to satisfy the arm?* Only partly, and the
answer is order-dependent. Among collapsed `X_SEMICOLON_TOTAL4` rows, the arm's
own rule is met in **55%** under `o_A` but **5.6%** under `o_Q`. The model moves
toward the demand (3.1–3.8 semicolons against 0.000 for every control arm) and
collapses on the way, but frequently stops short of the number asked for. The
accurate phrasing is "collapses while **pursuing** the semicolon demand", not
"collapses **in order to satisfy** it". The per-sentence semicolon rules are the
clean-trade cases: there the arm is satisfied in 100% of collapsed rows.

### E3 — target-count generalization, N ∈ {2, 3, 4, 5, 6}

Five runs, 2000 generations, 0 technical failures. Only the target's `n` differs;
the wordings are the registry's own `exact_sentence_count` templates.

**Paired excess over `C_L3` (A-failure):**

| N | `S_SEMICOLON` `o_A` | `S_SEMICOLON` `o_Q` | B `o_A` | B `o_Q` | `C_L3` own failure |
|---|---|---|---|---|---|
| 2 | 0.475 | **0.750** | **0.475** | **0.575** | 0.30 / 0.20 |
| 3 | 0.600 | **0.925** | 0.050 | 0.475 | 0.000 |
| 4 | **0.675** | 0.575 | 0.000 | 0.400 | 0.000 |
| 5 | 0.475 | 0.500 | 0.075 | 0.225 | 0.025 / 0.000 |
| 6 | 0.475 | 0.375 | 0.025 | 0.175 | 0.000 |

**The pre-registered row for a *strategy* fired.** `S_SEMICOLON`'s excess is
between 0.375 and 0.925 at every N and shows no monotone trend. It is **largest
at N = 2**, where the instruction is easiest to satisfy alongside the target —
two sentences, two semicolons, no strain at all. A difficulty response cannot
produce that.

**The distribution is binary, and the mean was hiding it.** At N = 6, mean
sentence count under `S_SEMICOLON` is 3.6, which reads like a partial undershoot.
It is not:

| N = 6, `S_SEMICOLON` | 1 sentence | 5 | 6 (fully compliant) |
|---|---|---|---|
| `o_A` | **0.47** | 0.00 | **0.53** |
| `o_Q` | **0.35** | 0.03 | **0.62** |

Nothing between one and six. The model either writes one clause-chained sentence
or complies exactly. That is a strategy being selected, not an ability degrading.
`C_L3` is at 6.00 sentences in 100% of rows in the same cell.

**B's excess falls monotonically with N** — 0.575, 0.475, 0.400, 0.225, 0.175 in
`o_Q` — the opposite of the pre-registered capacity prediction. B pushes toward
long sentences and few of them (its words rise 88 → 249 across the sweep), so a
larger target gives it room and the interference dissipates. Another respect in
which B is not the same phenomenon as the mark route.

**Headroom, as pre-registered.** N = 2 is the only cell where the control itself
fails (0.20–0.30); writing exactly two sentences under load is genuinely hard.
Every excess at N = 2 is still measured against that control, but the cell is the
weakest in the sweep and is reported as such. N = 3 to 6 all have a clean floor
(`C_L3` at 0.000–0.025).

### E4c — B's interference is an interaction with the background

Two runs, 400 generations each, identical in every respect — same 20 pilot tasks,
wording 0, load k=5, both orders, 2 replicates, same model and decoding —
**except one member of the shared background set.**

| arm / order | background = `U_FMT_COLON1` ("exactly one colon") | background = `U_FMT_PAREN1` ("exactly one parenthetical") |
|---|---|---|
| **B `o_Q`** | **0.325** [+0.17, +0.47] | **0.075** [0.00, +0.15] |
| B `o_A` | 0.050 [0.00, +0.12] | 0.000 [0.00, 0.00] |
| `S_SEMICOLON` `o_A` | 0.575 [+0.40, +0.75] | **0.725** [+0.60, +0.85] |
| `S_SEMICOLON` `o_Q` | 0.475 [+0.33, +0.62] | **0.725** [+0.55, +0.88] |
| `C_L3` (the control) | 0.000 | 0.000 |

B's colon count falls from 0.325 to 0.025 and its interference falls with it, to
an excess whose interval includes zero. `S_SEMICOLON` moves the *other* way and
stays large under both. The control does not move at all, so this is not the run
being easier.

**Reading.** The colon-requiring background instruction was supplying B with a
boundary-capable mark. B on its own does not reliably produce one; B alongside
"use exactly one colon" does, and the sentence count suffers. Most of what was
measured as **B's** directional interference in Stage B, E1 and E3-N4 is an
interaction between B and a background member — not a property of B.

**A methodological consequence for DCI generally, not just for this pair.** The
background set is identical in the focal and every reference arm, and the study
has been relying on that to argue it "cannot bias τ". That argument is correct
and insufficient. A shared background cannot *bias* τ, but it can determine
**whether τ exists at all**: here it moves B's estimate by a factor of four while
leaving the matched control untouched. τ is therefore **conditional on the
background**, and a τ reported without naming its background set is
underspecified. This is a property of the estimand, not a defect in this
implementation, and it was found only because the colon arm forced a background
substitution for an unrelated reason.

**E7 amendment, written after the first condition ran and before the rest.** The
design assumed B would supply the second limb of the dissociation. It cannot: in
the `X_NO_EXCLAM` baseline B's excess is **0.000** in both orders, because that
background has no colon in it and E4c has since shown B's interference requires
one. A prohibition cannot selectively rescue an arm that is not failing.

Two consequences, both applied rather than noted:

1. The dissociation across **prohibitions** still works and is what the first
   block tests: the same arm under an off-route prohibition, an on-route one, and
   an on-route-for-a-different-mark one. Each manipulation's own effect on its own
   mark is measured, so "it did nothing" and "it was not obeyed" stay separable.
2. A second block, `E7c`, restores the arm limb by keeping `U_FMT_COLON1` in the
   background and spending the *other* slot on the prohibition. B interferes
   there, so the comma-splice prohibition has something to act on. Load stays
   k=5 and the three conditions differ in exactly one instruction, as before.

### E5a — the structural twin: paragraphs · `runs/stageE5a_paragraphs_20260811T004553Z`

520 generations, 13.5 min, 0 technical failures. Target `X_PARA4`, "exactly 4
paragraphs, separated by a blank line". The pre-registered headroom worry did not
materialise: the target **alone** is satisfied in 40/40 rows at exactly 4.000
paragraphs.

| arm | excess `o_A` | excess `o_Q` | paragraphs | **sentences** | semicolons |
|---|---|---|---|---|---|
| `X_SEMICOLON_EACH` | **−0.050** | **+0.025** | **4.000 / 3.975** | 4.7 / 7.5 | 13.3 / 10.0 |
| `X_LINEBREAK_EACH` | 0.000 | 0.000 | 4.050 / 4.000 | 15.1 / 13.8 | 0.0 |
| `B` | **+0.300** [+0.13, +0.48] | **+0.175** [+0.05, +0.33] | 4.35 / 4.18 | 5.1 / 4.4 | 0.5 / 0.2 |
| `C_L3` (control) | — | — | 3.900 / 4.000 | 11.9 / 12.5 | 0.0 |

**The mechanism does not transfer, and the demonstration is unusually direct.**
In these very same responses the semicolon instruction is doing exactly what it
does everywhere else — it cuts the sentence count from the control's 11.9 to 4.7
while producing 13.3 semicolons. The **paragraph** count sits at 4.000. The
behaviour is identical; the failure does not occur, because the target counts a
unit the semicolon cannot stand in for.

That is the boundary of the claim, established positively rather than by absence
of evidence.

**The paragraph-side substitution route was NOT tested, and that must be said
plainly.** `X_LINEBREAK_EACH` was designed to be the blank line's substitutable
delimiter, but the model **ignored it**: arm compliance 0.000 (`o_A`) and 0.025
(`o_Q`). An instruction that is not followed cannot interfere, so this cell shows
only that the instruction was unpersuasive, not that the route is absent. The
isolated primitive shows the instruction does change behaviour when nothing
competes (2.300 paragraphs against the target's 4.000), so a better-worded
version might well test it. Left open.

**B interferes on paragraphs, in the opposite direction.** Its excess is
+0.300/+0.175, and it is entirely **overshoot** (0.350/0.175 over, 0.000 under) —
B writes 303–339 words and spills into a fifth paragraph. B damages counts in
whichever direction its length pressure happens to push, which is a further
reason not to treat it as one mechanism.

### E5b — a different constraint family: counting integers · `runs/stageE5b_integers_20260811T005938Z`

520 generations, 0 technical failures. Target `U_NUM_FOURDISTINCT`, "four
distinct integers".

**The target was a poor choice and the cell is underpowered. That is the first
thing to report, not a footnote.** `U_NUM_FOURDISTINCT` **alone**, with no
interference at all, fails **0.725** of the time. Under load the matched control
`C_L3` fails 0.525 (`o_A`) / 0.325 (`o_Q`). With the floor that high and that
noisy, only a very large effect could be detected.

| arm | excess `o_A` | excess `o_Q` | sentences | semicolons |
|---|---|---|---|---|
| `X_SEMICOLON_EACH` | +0.150 [−0.08, +0.38] | +0.075 [−0.18, +0.33] | **1.03 / 1.00** | 3.75 / 3.58 |
| `X_SEMICOLON_TOTAL4` | −0.150 [−0.40, +0.13] | +0.225 [−0.03, +0.45] | **1.25 / 1.03** | 4.73 / 5.83 |
| `B` | +0.075 [−0.13, +0.28] | +0.325 [+0.13, +0.53] | 1.40 / 1.05 | 0.35 / 0.05 |
| `C_L3` (control, own failure) | 0.525 | 0.325 | 3.68 / 3.00 | 0.18 / 0.23 |

**No semicolon interval excludes zero.** The behaviour is unmistakably present —
both semicolon arms collapse to ~1.0 sentences against the control's 3.0–3.7 —
and the integer count does not follow. That is the same specificity as E5a, but
here it is *consistent with* no transfer rather than *evidence of* it, because
the design could not have detected a moderate effect.

**Conclusion for this cell: inconclusive, and the reason is a design error I
made.** A target that fails 72.5% of the time unaided is not a usable outcome. A
proper numerical-family test needs a target the model can actually hit — "at
least two integers" rather than "four distinct integers". Not run; recorded as
the open item it is.

B's `o_Q` excess of +0.325 is the one interval excluding zero here, and this run
carries `U_FMT_COLON1` in its background, which E4c identified as the condition
B needs. Consistent, not independent.

### E7 (first block) — the prohibitions were not obeyed as written

Three runs, 1200 generations, 0 technical failures, differing in exactly one
background instruction.

**Manipulation checks first, as pre-registered — and both fail.**

| | semicolons produced | semicolon splices | commas produced | comma splices |
|---|---|---|---|---|
| `X_NO_EXCLAM` (off-route) | 4.400 | 2.375 | 6.58 (B) / 1.13 (`C_L3`) | 0.400 / 0.100 |
| `X_NO_SEMI_SPLICE` | **4.175** | **2.150** | 6.63 / 1.25 | 0.350 / 0.125 |
| `X_NO_COMMA_SPLICE` | 3.850 | 2.325 | **0.000 / 0.000** | **0.000 / 0.000** |

* **The semicolon prohibition was ignored.** `Do not use a semicolon to join two
  complete sentences.` left semicolon splices at 2.15 against the control's 2.38.
  The model went on doing precisely the thing it had been told not to do, while
  obeying the semicolon *requirement* in the same prompt.
* **The comma prohibition was over-applied.** `Do not use a comma to join two
  complete sentences.` was read as "use no commas", taking B's comma count from
  6.58 to **exactly 0.000** in 80/80 rows. That is not the manipulation the design
  specified; it is a different and much heavier constraint.

**The pre-registered stop condition therefore applies: the outcomes are not
interpreted as an intervention.** For the record they were `S_SEMICOLON` excess
0.325/0.375 (off-route), 0.500/0.350 (semicolon prohibition), 0.275/0.200 (comma
prohibition) — but with one instrument ignored and the other transformed into a
comma ban, no causal reading is available from them.

**One observation worth carrying forward anyway**, because it is a manipulation
that demonstrably *did* something: banning commas outright pushed **B** from
0.000 to **0.250** excess in `o_Q` and cut its sentence count to 3.30. B builds
its long sentences with commas, and removing them made its target compliance
worse rather than better.

**Status of the causal leg after two failed instruments.** The system-message
scaffold failed because no such clause can be made inert (E1). The numbered
prohibition failed because the model does not follow this class of negative
instruction as written. No mediator-blocking intervention has succeeded, and none
is claimed. What the study has instead is two *manipulations of the trigger* with
matched controls:

* **dose–response** (E4b): demanded semicolons 2 → 4 → 6 moves collapse
  0.01 → 0.95 → 0.94, while four commas at the same dose leave it at 0.000;
* **target substitution** (E5a): the identical instruction, producing the
  identical behaviour, causes no failure when the target counts paragraphs.

Those are experimental, not correlational, and together they support the causal
claim about the trigger. They do not establish that blocking the strategy would
prevent the failure, and that is not asserted.

### E6 — cross-model: `google/gemma-2-9b-it` · 520 generations, 7.9 min, 0 technical failures

Verified to be the intended model: `Gemma2ForCausalLM`, 9,241,705,984 parameters,
bfloat16, 18.1 GB peak, revision `11c9b309abf7`, and
`prompt_convention = "system merged into first user turn"` because gemma's chat
template rejects the `system` role.

**Under load — the interference does not replicate.**

| arm | Qwen3-4B excess | **gemma excess** | gemma sentences | semicolons produced |
|---|---|---|---|---|
| `X_SEMICOLON_TOTAL4` | 0.975 / 0.975 | **0.000 / 0.075** | 4.00 / 3.93 | 2.03 / 2.28 |
| `X_SEMICOLON_EACH` | 0.750 / 0.675 | **0.125** [0.03, 0.25] / 0.075 | 3.83 / 3.93 | 2.65 / 2.55 |
| `X_COMMA_TOTAL4` | −0.025 / 0.050 | 0.000 / 0.000 | 4.00 / 4.00 | — |

Severe collapse maxes out at **0.025** across the whole run.

**In isolation — the disposition replicates exactly.**

| instruction alone | Qwen3-4B sentences | **gemma sentences** |
|---|---|---|
| `Use at least 4 semicolons in the whole answer.` | 1.125 | **1.150** |
| `Use at least one semicolon in every sentence.` | 3.075 | **1.075** |
| `Use at least 4 commas in the whole answer.` | 3.875 | **1.425** |
| `Write exactly 4 sentences.` | 4.000 | 4.000 |

**The finding is a dissociation between disposition and arbitration.** Both models
realise a bare semicolon demand as a single clause-chained sentence — gemma if
anything more strongly, and it extends the habit to commas, which Qwen does not.
What differs is what happens when an explicit sentence count competes with that
habit. Qwen keeps the semicolons and loses the count (3.2–3.8 semicolons, 1.0
sentences). **Gemma keeps the count and drops the semicolons** — it produces 2.0–2.6
where four are demanded, with arm compliance 0.000–0.050, and holds 4 sentences.

So the *behavioural regularity* is not Qwen-specific, but the *interference* is:
it requires a model that resolves the conflict in favour of the added instruction.

**No third model family will be run.** The pre-registered rule was that a third
family is worth the download only if gemma reproduces the effect. It did not, and
one reproduction plus one failure already establishes that the interference is
model-dependent; a third data point would refine the frequency of a property, not
the existence of the dependency. The disposition's generality (2 of 2) is worth a
follow-up, but that is a different question from the one this study asked.

### E7c (second block, colon background) — same compliance failures, one real result

Three more runs, 1200 generations, 0 technical failures. Background
`U_LEX_FORBID3 + U_FMT_COLON1 + <prohibition>`, so B interferes and the arm limb
of the dissociation is available.

**The semicolon prohibition is confirmed ineffective in a second background.**
Semicolon splices 1.350 → **1.450** (`o_A`) and 1.875 → **1.725** (`o_Q`) against
the off-route control; `S_SEMICOLON`'s excess 0.850 → 0.900 and 0.450 → 0.550. It
does not reduce the behaviour and it does not reduce the failure. Two backgrounds,
same answer.

**The comma prohibition is confirmed to be a comma ban.** B's commas 6.550 →
**0.050**; `C_L3`'s 1.350 → 0.300.

**But the comma ban is itself a real manipulation, and it replicates a selective
effect across both blocks:**

| | B `o_Q` excess | `S_SEMICOLON` `o_A` / `o_Q` excess |
|---|---|---|
| **block 1**, off-route control | 0.000 | 0.325 / 0.375 |
| **block 1**, comma ban | **+0.250** | 0.275 / 0.200 |
| **block 2**, off-route control | 0.125 | 0.850 / 0.450 |
| **block 2**, comma ban | **+0.300** | 0.875 / 0.475 |

Removing commas makes **B** worse in both blocks and leaves `S_SEMICOLON`
essentially untouched in both. It is a dissociation, though not the one that was
pre-registered and in the opposite direction from a rescue: B builds its long
sentences out of comma-joined clauses, so a comma ban damages its ability to reach
the target count, while the semicolon route does not use commas and is indifferent.

That is the closest thing to route-specific causal evidence this round produced,
and it should be read for what it is — a post-hoc reading of a manipulation that
was not the one specified, replicated across two independent backgrounds.

---

# Round 6 — consolidation, then the three experiments the matrices justify

`CLAIM_EVIDENCE_MATRIX.md` and `EXPERIMENT_COVERAGE_MATRIX.md` were built first,
the second of them programmatically from the run configs. Building them changed
the plan in three ways before any new generation:

1. **W7 — the q ≈ N threshold claim is withdrawn as unidentified.** The coverage
   matrix shows free q was varied **only at N = 4**; every other N sits on the
   diagonal q = N because per-sentence rules pin q to N. At N = 4, "q ≥ 4",
   "q ≥ N" and "q/N ≥ 1" are the same hypothesis.
2. **W9 — `severe_collapse` is retired as the mediator variable.** It counts
   sentences, so it is a subset of the sentence-count outcome. Replaced by
   `splice_share` and `chain_share`, computed from punctuation counts alone.
3. **A measurement defect was found and fixed.** `splice_count` matched only
   `[;,]`, so colon and dash splices silently returned 0 for every input.

The replacement mediator was validated on **existing** data before any new run,
by the only test that matters for non-circularity — that the measure and the
outcome can come apart:

| cell | chain/splice share | target failure |
|---|---|---|
| E5a `X_SEMICOLON_EACH`, paragraph target | **0.456** | **0.013** |
| E4b `X_COLON_TOTAL4` `o_A` | 0.394 | 0.875 |
| E4b `X_COLON_TOTAL4` `o_Q` | 0.134 | 0.175 |
| E4b `X_DASH_TOTAL4` | 0.11–0.16 | 0.30–0.48 |
| E4b `X_COMMA_TOTAL4`, `C_L3` | 0.000 | 0.000–0.025 |
| E2b `B` | 0.087 | 0.637 |

Both off-diagonal quadrants are populated: high share with no failure (E5a), and
high failure with zero share (B, `C_O2`, `C_W3`). Pearson across 106 contrast
cells is +0.794 — informative rather than arithmetic. `chain_share` additionally
absorbs the colon's order asymmetry, which the sentence-count measures could not.

---

## R6-A — the q × N phase diagram

**Hypothesis space.** Four accounts predict different surfaces over (q, N):

| | account | prediction |
|---|---|---|
| **A1** | absolute dose | failure depends on **q** alone; the surface is flat in N |
| **A2** | ratio | failure depends on **q/N**; iso-failure contours are rays from the origin |
| **A3** | boundary at q = N | failure jumps where **q ≥ N**; contours follow the diagonal |
| **A4** | difference | failure depends on **q − N** |

At N = 4 all four coincide, which is why the existing data cannot separate them.

**Design.** Targets `X_A2, X_A3, A, X_A5, X_A6` × arms `X_SEMICOLON_TOTAL{1..6}`,
plus two q = 0 controls: `X_COMMA_TOTAL4` (wording- and dose-matched, no
semicolons) and `C_L3` (the registry control used throughout). Background
`U_LEX_FORBID3 + U_NUM_MAXINT + U_FMT_PAREN1`, chosen because it is E4b's, so the
N = 4 column is a direct replication rather than a new measurement. Both orders,
20 pilot tasks, 2 replicates, wording 0. 3,560 generations.

**Primary readout.** Paired excess over `C_L3` at each (q, N), and `chain_share`
at each (q, N) as the strategy surface. Fitting is descriptive: compare the
deviance of failure ~ f(q), ~ f(q/N), ~ f(q−N) and ~ f(q, N).

**Discriminating predictions.**

| observation | reading |
|---|---|
| the q at which failure jumps is the **same for every N** | **A1** — absolute dose; the mechanism has nothing to do with the target |
| the jump tracks **q/N ≈ 1** | **A2** — ratio |
| the jump tracks **q = N** exactly, e.g. q=2 collapses at N=2 but not at N=6 | **A3** — the boundary account, and the withdrawn claim is restored |
| `X_COMMA_TOTAL4` moves anywhere | the dose control is not inert and the whole dose reading is confounded |
| `C_L3` failure rises with N | the target's own difficulty is moving and excesses must be read within N only |

**Stop condition.** If `C_L3` fails above ~0.3 at any N, that column has no
headroom and is reported as uninformative rather than interpreted (this happened
at N = 2 in E3).

---

## R6-B — the B × colon 2×2 factorial

**Why.** I7 rests entirely on across-run comparisons at fixed load. The clean
2×2 has never been run.

**Design.** Two runs, differing only in load, so that adding B moves k by exactly
one in both differences:

| run | load | target | arms | gives |
|---|---|---|---|---|
| `R6B_load2` | 2 | A | `B`, `U_FMT_COLON1`, `C_L3`, `S_SEMICOLON` | F(A+B), F(A+C), F(A+ctrl), F(A+semi); primitives give F(A) |
| `R6B_load3` | 3 | A | `B`, `C_L3`, `S_SEMICOLON`, background `[U_FMT_COLON1]` | F(A+C+B), F(A+C+ctrl), F(A+C+semi) |

**Two interaction estimates, both reported.**

* **raw**, as specified: `[F(A+C+B) − F(A+C)] − [F(A+B) − F(A)]`
* **count-matched**, using `C_L3` as an inert filler so instruction count is
  constant within each difference:
  `[F(A+C+B) − F(A+C+ctrl)] − [F(A+B) − F(A+ctrl)]`

The count-matched form is the DCI-correct one; the raw form is reported because
it is what was asked for and because a large gap between them would itself be
informative about `C_L3`'s inertness.

**Discriminating predictions.**

| observation | reading |
|---|---|
| interaction ≫ 0, and F(A+B) ≈ F(A) | **B alone does nothing; B × colon is the whole effect.** I7 confirmed, and the v19 pair-3 headline is a higher-order interaction |
| interaction ≈ 0, both differences > 0 | B is an ordinary main effect and the background-swap result was something else |
| interaction ≈ 0, both differences ≈ 0 | B does not interfere at load 2–3 at all; the earlier effects need a full background |
| `S_SEMICOLON` positive in both loads | the positive control holds and the run is interpretable |

**Manipulation check.** Colon counts must actually rise when `U_FMT_COLON1` is
present. If they do not, the factor was not delivered.

---

## R6-C — cross-model conflict arbitration

**Why.** I10 rests on one gemma run at one cell. And "Qwen vs Gemma" confounds
developer, size, generation and training recipe.

**Models.** Verified against the Hub on 2026-08-11; exact ids and blockers in
`EXPERIMENT_COVERAGE_MATRIX.md` §11.

| model | id | params | status |
|---|---|---|---|
| Qwen3-4B-Instruct | `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f` | 4.02 B | ✔ rerun under the identical battery |
| Gemma-2-9B-it | `google/gemma-2-9b-it` @ `11c9b309` | 9.24 B | ✔ already run (E6) |
| **Qwen3.5-4B** | `Qwen/Qwen3.5-4B` | 4.66 B | ✔ new — size-matched to Q4, one generation later |
| **Qwen3.5-9B** | `Qwen/Qwen3.5-9B` | 9.65 B | ✔ new — size-matched to G9 |
| **Qwen3.6-27B** | `Qwen/Qwen3.6-27B` | 27.78 B | ✘ **BLOCKED**: ≈55.6 GB bf16 against 48 GB total VRAM |
| **Qwen3.6-35B-A3B** | `Qwen/Qwen3.6-35B-A3B` | 35.95 B | ✘ **BLOCKED**: ≈71.9 GB bf16 |

The 3.6 line ships FP8 and GPTQ-Int4 variants that would fit. Neither is used:
gfx1100 has no FP8 tensor support in this ROCm build, and an Int4 stand-in would
change the numeric condition and answer a different question. **No substitution
is made silently; Qwen 3.6 is recorded as untestable on this hardware.**

The 3.5 line drops the `-Instruct` suffix — the plain id *is* the instruct model.
`Qwen/Qwen3.5-4B-Instruct` returns HTTP 401 and does not exist.

**Design.** Identical to E6 for every model: target A, focal
`X_SEMICOLON_TOTAL4`, arms `X_SEMICOLON_EACH`, `X_COMMA_TOTAL4`, `C_L3`,
background `U_LEX_FORBID3 + U_NUM_MAXINT + U_FMT_PAREN1`, both orders, 20 pilot
tasks, 2 replicates, wording 0, bf16, T = 0.7, top_p = 0.9, 512 new tokens.

**The comparison is NOT "does the effect replicate".** Five quantities per model,
reported separately:

| quantity | measured by |
|---|---|
| **D_m** isolated semicolon disposition | sentences and `chain_share` in the arm-alone primitive rows |
| **target competence** | failure rate of the A-alone primitive rows |
| **joint target compliance** | `a_failure` in the contrast rows |
| **joint semicolon compliance** | `arm_binary_pass` in the contrast rows |
| **which instruction is sacrificed** | the 2×2 cross-tabulation of the two above |
| **resulting structure** | sentences, semicolons, `chain_share`, words |

A model can have high D_m and no interference (gemma), high D_m and interference
(Qwen3-4B), or low D_m — and the cross-tabulation says *which* instruction gave
way, which a single excess figure cannot.
