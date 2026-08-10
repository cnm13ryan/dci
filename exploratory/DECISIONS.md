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
