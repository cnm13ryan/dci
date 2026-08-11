# Does preventing semicolon splicing remove the interference?

**`ANTI_SPLICE_MANIPULATION_FAILED`. The experiment is unidentified: no causal
conclusion about splicing is licensed.**

`EXPLORATORY_NO_EVIDENCE`. Run directory
`runs/semicolon_splice_intervention_20260811T233021Z/` (gitignored; this is the
tracked report). **160 generations** — the manipulation preflight only. The 640
planned main generations were not run.

---

## Question

The previous round showed that a semicolon interferes with sentence-defined
instructions and a matched degree symbol does not, and that the semicolon is
produced standing where a sentence boundary could stand. That manipulated **which
mark was required**. This experiment was to manipulate **how the semicolon is
used**: hold the semicolon requirement fixed and forbid its clause-joining use.

The causal chain under test:

```
semicolon required → used as a clause-like splice → sentence structure compressed
→ greater target failure under the focal instruction
```

The intervention closes the middle step. The estimand is
Ω_b = τ(anti-splice, b) − τ(off-route, b), with Ω < 0 meaning closing the route
reduced interference.

---

## Prior evidence

Δ_boundary = τ(semicolon) − τ(degree) = **+0.512 [+0.375, +0.662]** at b = 4096,
with the repository's `splice_count` proxy positive in **0.887–0.939** of
compliant semicolon answers and **0.000** of compliant degree answers. Boundary
capability predicted the interference; boundary *use* had never been intervened
on.

---

## Manipulation validation — this comes first, and it is where the experiment ends

160 generations on 20 calibration tasks (CAL33–CAL52, a block no earlier round
used), QACD, **reference arm only** so that no focal-versus-reference contrast is
computable from the design, `X_SEMICOLON_FREE` in every cell, route ∈
{`X_NO_EXCLAM`, `X_NO_SEMI_SPLICE`}, b ∈ {0, 4096}, 2 replicates. The two route
prompts were asserted to differ in exactly one line — the final D line — in all
40 matched groups before generation.

| measurement | b = 0 off-route | b = 0 anti-splice | b = 4096 off-route | b = 4096 anti-splice |
|---|---|---|---|---|
| semicolon compliance | 0.575 | 0.550 | 0.950 | **0.925** |
| P(splice > 0), unconditional | 0.650 | 0.575 | 0.925 | 0.950 |
| P(splice > 0 \| semicolon compliant) | 1.000 | **1.000** | 0.974 | **0.946** |
| D-instruction compliance | 1.000 | **0.425** | 1.000 | **0.050** |
| sentences | 4.00 | 4.00 | 3.93 | 3.95 |
| malformed / truncated / leaked | 0.000 | 0.000 | 0.000 | 0.000 |

**Gate results.**

| # | requirement | result |
|---|---|---|
| 1 | the instruction does not simply remove the semicolon | **PASS** — compliance 0.925 vs 0.950 |
| 2 | splicing materially reduced (≤ 0.25, or ≥ 0.50 absolute reduction) | **FAIL** — 0.946, reduction **0.028** |
| 3 | reduction visible at both reasoning states | **FAIL** — reduction is **0.000** at b = 0 |
| 4 | no new parsing or truncation problem | **PASS** — malformed 0.000 in both |

**The instrument is not invalid in the way §14 anticipates.** The semicolon
survives: 92.5% of anti-splice answers still contain exactly one. What fails is
the restriction on its *use*. `X_NO_SEMI_SPLICE` is obeyed in **5%** of answers at
high reasoning, against **100%** for the matched off-route instruction carried at
identical load — so this is not an instruction-load effect, and the model is not
ignoring the fourth slot in general.

The clean statement of the finding: **this model follows a COUNT constraint on
the semicolon (0.925) and essentially does not follow a USAGE constraint on the
same mark in the same prompt (0.050).**

This reproduces, in the light exact-one-semicolon setting, the failure the same
instruction showed in the earlier heavy per-sentence setting. The lighter
requirement did not make it satisfiable.

---

## Main result

**None.** The main experiment was not run. τ_off-route, τ_anti-splice and Ω are
undefined at both reasoning states, and no outcome contrast was generated, so
none could be inspected and narrated after the fact. `main/NOT_RUN.md` records
this.

---

## Structural response

There is none to report, because the assigned intervention produced no change in
the behaviour it targets. Splices per answer: 1.000 → 1.000 at b = 0 and 0.974 →
0.946 at b = 4096, among semicolon-compliant answers. Sentence count 4.00 → 4.00
and 3.93 → 3.95. Period count 4.00 → 4.00 and 3.93 → 4.00. Answer length 47.9 →
50.8 and 47.6 → 46.6 words.

The one clearly assigned-condition difference is in the reasoning channel:
realised reasoning is **978.7** tokens under anti-splice against **470.0** under
the off-route control at b = 4096. The model spends about twice as long thinking
when told not to splice, and then splices anyway.

---

## Task and replicate robustness

Not applicable — there is no scientific contrast to check for breadth. The
manipulation failure itself is uniform: at b = 0 the conditional splice rate is
1.000 in **every** cell of both conditions, and at b = 4096 it is 0.946 and 0.974.

---

## Manual verification

The null rests entirely on `splice_count`, so the proxy was audited before the
result was accepted.

* **12 anti-splice rows flagged as splices, read by hand: 11 of 12 are
  unambiguous clause joins** — `…through continuous operation; this ensures
  consistent output…`, `…where it faces harsh conditions; sacrificial zinc coating
  ensures…`, `…a series of arches; these arches channel water…`. One
  (`537d8ae6bd87`, `Speed ratios; systems synchronize engine output…`) joins a
  fragment to a clause and is a plausible **false positive**.
* **Both anti-splice rows with a semicolon that the proxy called clean, read by
  hand.** One is genuinely clean — `Safeguarding sharpness; sustaining scientific
  clarity.`, two participial phrases, not two sentences. One
  (`…use water from high tides; systematically, the stored water is released…`)
  looks like a missed join: a plausible **false negative**.
* **No differential measurement bias.** `splice_count` has two rules — a
  high-precision closed-list rule and a recall-oriented length rule. The
  high-precision rule accounts for **0.610** of anti-splice flags and **0.486** of
  off-route flags at b = 4096, so if anything the anti-splice flags are the more
  certain ones. Nothing here could manufacture the null.
* Most common word following a flagged semicolon: `this` (48), `the` (18),
  `however` (14), `it` (11).

Full audit: `independent_checks/proxy_audit.txt`.

---

## Independent recomputation

Not applicable to a headline contrast, because there is none. The manipulation
figures are recomputed from the scored rows by the figure script, which shares no
aggregation code with the gate script, and the two agree.

---

## Interpretation

**Experiment unidentified because the manipulation failed.**

Per §14, no causal story about splicing may be told from outcome data, and none
was generated to tell one from. What *is* established, within these conditions:

* **`X_NO_SEMI_SPLICE` does not close the route it names.** 5% compliance at high
  reasoning, 0.028 absolute reduction in splicing.
* **The failure is specific to the usage constraint, not to load or to the fourth
  slot.** The matched off-route instruction at identical load is obeyed 100% of
  the time.
* **The semicolon requirement itself is unaffected**, so this is not the
  "compliance collapses" failure mode of §14 — the instrument did not prevent the
  mark, it failed to constrain how the mark was used.

The clause-boundary account from the previous round is therefore **neither
supported nor weakened** by this experiment. It stands exactly where it did:
boundary capability predicts the interference, and boundary use has still never
been intervened on successfully.

---

## Limitations

* **`splice_count` is a proxy.** It tests only the *following* side of the mark;
  "two complete sentences" strictly also requires the preceding side to be a
  complete clause, which it cannot check. A stricter proxy would flag fewer rows
  in both conditions and could not create a reduction that is absent at 0.028.
* **The anti-splice instruction is itself another instruction**, which is why the
  off-route control exists; the comparison never contrasts three instructions
  with four.
* **One model, one instruction pair, one order, one background, one task set.**
  The preflight also used calibration rather than evaluation tasks by design.
* **One wording of the prohibition was tested** — the registry's paraphrase 0.
  The registry holds five more, and none was tried, because trying wordings until
  one works after seeing the outcome is what §10 forbids. A prospective wording
  screen is a legitimate separate experiment; substituting a stronger wording
  into *this* one is not.
* Everything here is exploratory and uncorrected.

---

## Next experiment

**One: a prospective wording screen for the anti-splice constraint, scored only
on the manipulation.**

Run all six registry paraphrases of `X_NO_SEMI_SPLICE`, plus the same instruction
carrying a worked example — the device that rescued the anchored-placement
manipulation in Round 10, where every counting wording had failed at 0.000–0.338
compliance and a lexical anchor with an example reached 0.700–0.875. Score
**only** semicolon compliance and `P(splice > 0 | compliant)`, on calibration
tasks, in the reference arm alone, with no focal contrast computable. Freeze the
first wording that clears the same gate this round failed; if none does, the
splice route is not closable by instruction in this model and the mechanism must
be attacked another way — by constraining the answer's structure rather than the
mark's use.

This is the right next step precisely because the current experiment is
unidentified: the causal question is still open and unanswered, and the only
thing standing between it and an answer is an instrument that works.
