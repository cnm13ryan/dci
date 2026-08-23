# The v5 adoption checklist — closed

Nineteen §34 decisions, three specification questions, one confirmation. This
page was the whole of what stood between the repository and a signed
registration manifest. **Every item on it is now taken.**

Executable state: `protocol/decisions.py` (the nineteen),
`protocol/open_items.py` (U1–U3, P1), and the committed record in
`researcher_decisions.json`, which both modules read at import and the
registration manifest binds by hash. `run/cli.py plan` prints the live version
of the first table; it reports `can_register: true`.

---

## The nineteen, and what each one took

Recorded in `researcher_decisions.json` with its evidence, who took it and
when. Three went **against** the standing proposal, which is the column that
matters: a checklist on which every proposal survives is a checklist nobody
read.

| | Question | Taken | Against? |
|---|---|---|---|
| **D0** | Adopt v5 at all, knowing its matching rule was fitted to v4r4? | **adopt** — §30's declaration attached permanently | no |
| **D1** | Which arms, and how many models? | **`four_models_56_cells`** — all five arms, 4 models, 384 blocks, $M = 8$, **1,172,544** generations | no |
| **D2** | Add a load-three arm so the memo's $\Gamma$ becomes estimable? | **no load-three arm**; §5's exclusion stands | no |
| **D3** | Are the 96 Calibration-B questions authored before adoption? | **yes** — authored, audited, hashed, committed | no |
| **D4** | Are these eight marker words the right eight? | **`approve_eight`** — all eight, with four accepted limitations recorded | no |
| **D5** | Lexicographic validity, or a weighted composite? | **lexicographic** | no |
| **D6** | Does an unbuildable reference set stop the replication? | **no** — it continues; the reference-dependent estimands become `NOT_IDENTIFIED`, irreversibly | no |
| **D7** | Is 0.90 the right interaction-gate ceiling? | **0.90**, with R13's objection recorded and not answered by evidence | no |
| **D8** | Is 0.75 the right chance ceiling? | **0.75** on the point, 0.85 on the Wilson upper bound | no |
| **D9** | Will an independent annotator be available? | **no**; the basis stays `deterministic_measurement_validated` | no |
| **D10** | One broad-class companion, or several? | **one**; no class claim | no |
| **D11** | Carry v4's confirmatory topics, or re-author? | **carry**, with §6.2's residual declared | no |
| **D12** | Does $\delta_{\text{difficulty}}$ get its own magnitude threshold? | **no**; direction and the SESOI only | no |
| **D13** | Is F11 primary-tier? | **yes**, licensing L4b | no |
| **D14** | Is instructed compliance still the difficulty coordinate? | **yes**; raw solo secondary | no |
| **D15** | Do the memo's 0.10 and 0.25 transfer to a same-form $\Delta_R$? | **both transfer**, with R2's objection on the record | no |
| **D16** | Does Calibration-B measure the whole candidate set or only A's survivors? | **the whole set** | **yes** |
| **D17** | How weak may B be at the severity the study selects? | **$\kappa^{B}(m^{*}) \le 0.50$** on the point estimate | **yes** |
| **D18** | Does the strong L3c conclusion require the near-form arm? | **yes** | **yes** |

## The specification questions

| | Question | Status |
|---|---|---|
| **U1** | What a Tier-2 core reference contributes to §13.8's role spread | `SINGLE_ADMISSIBLE_READING`. `none` is not a role; §13.15 guarantees two Tier-1 members, so the count is always well defined |
| **U2** | §11.8's secondary fit is singular as written; which repair? | **RESOLVED at A2** — $\alpha_f$ over the three **core** families, a Tier-2 point at the unweighted mean core intercept plus $\gamma$. A1 never constructed, A3 never constructed, A4 constructed and non-adopted |
| **U3** | Which direction "the less restrictive severity" runs | `SINGLE_ADMISSIBLE_READING`, derived from the family's predicate form |
| **P1** | §7.10 admitted Tier 3 "to the spectrum"; three sections make that unreachable | **CONFIRMED.** Tier 1 and Tier 2 take the core, near-form and spectrum roles; Tier 3 takes the broad-class role only. Nothing executable changed — under either reading the code admitted no Tier-3 spectrum rung — and making Tier 3 reachable would be a §32 amendment to the candidate population, the §11.8 fit structure and the derived cell set. It was not made |

## What the decisions did to the red team

| | Finding | Status now |
|---|---|---|
| **R1** | a same-form pool may make L3c near-automatic | **resolved** by D18, and D1 registers the near-form arm rather than merely permitting it |
| **R2** | the memo's 0.25 on a redefined $\Delta_R$ | **adopted over the objection** (D15); the disagreement stays on the record |
| **R11** | Calibration-A screens and Calibration-B confirms | **resolved** by D16 |
| **R13** | the 0.90 ceiling sits in an observed gap | **adopted with the coincidence recorded** (D7), and not used as evidence |
| **R14** | the focal extension trades construct strength for band membership | **resolved** by D17 |
| **R16** | `REFERENCE_SUPPORT_NOT_IDENTIFIED` is not terminal | **resolved** by D6 |
| **R5** | $\kappa^{B}$ is measured under $B$, so it is not pre-treatment for the pair | **ACCEPTED PERMANENT LIMITATION.** No §34 decision carries it, §13.8 closes only its second half, and no rule can close the first. It is reported as a limitation, it does not block the freeze, and it is **not** resolved |
| **R22** | the full design has never been executed | registered; §19's procedural pilot at stage 3 is the mitigation and it precedes every scientific stage |
| **R23** | the Tier-1 pool has never been measured | registered; Gate 1 (stage 5) over the 650-instrument population is the measurement, and it reads the regime screen's own generated text — so it is not reachable before a model runs |

## What adoption bound

Everything below is in the signed manifest, and a change to any of it is a §32
amendment rather than an edit.

- the **protocol document** and the **reference design spec**, by content hash;
- the **researcher-decision record**, by hash — the nineteen closures with
  their evidence, D17's floor spec, and U2's and P1's resolutions;
- the **four model replications** with their exact 40-character revisions,
  their thinking policies and their chat-template arguments (§6.1);
- the **five arms**, 56 cells per block, 384 blocks, $M = 8$, and the
  **1,172,544**-generation budget, recomputed from constants by
  `dci1v5.design.budget` rather than quoted;
- the **eight Tier-1 markers** with their ids, words, discourse roles, verifier
  statistic ids, ladders, reserves, a **population hash**, and the four
  accepted limitations;
- both **calibration topic banks** by hash, with Calibration-B's authoring
  provenance;
- the **candidate library**: 37 families, 326 round-0 severities, 632 declared,
  650 instruments, 39 verifiers;
- every registered **threshold**, **estimand**, **multiplicity family**, claim
  level, identification status and terminal status;
- §11.8's secondary as **A2**, with A1, A3 and A4 named as non-adopted;
- §30's **reuse ledger** and the DEVELOPMENT_EVIDENCE declaration.

## What adoption did NOT do

**No v5 observation exists.** No model has been loaded, no prompt has been
generated, no calibration measurement has been taken, and no gate has been run
on model output. Adoption fixes the rules; it does not start the study.

---

## What comes next, in order

Stage 1, `PROTOCOL_REGISTERED`, **has run**: it is the stage that signs the
manifest, and signing it outside the stage machine would have produced a
registration with no stage record and no transition-log entry.

**It has run twice.** The first registration —
`2960a1fc44f036abd4729f7628095475018672adfac609bb2244a8763ba00ded`, producing
commit `f895646` — was superseded on 2026-08-23 by the pre-data engineering
amendment, before Stage 2 and with no observation under it. Three defects made
the registered lifecycle unexecutable as committed: three of the four models
could never obtain a stage-1 record, the pinned backend was unreachable from
four of the five generating stages, and a row's `synthetic` flag recorded how
the runner was called rather than what wrote the text. The superseded
registration is retained under `registration/superseded/2960a1fc…/`; the
replacement is `70608e5d…`
at commit `5e35ca6`, it names what it supersedes, and no registered scientific
value differs between them. **All four replications now carry a stage-1
record.** See
[`CHANGES_SCIENTIFIC.md`](../../../CHANGES_SCIENTIFIC.md).

The rest of §18 is untouched, one model at a time in §6.1's registered
execution order:

1. **Stage 2, `QUALIFIED`** — the next action. Non-scientific: it reads no
   behavioural rate. It checks the clean worktree, the resolved model
   revisions, the dependency manifest, the prompt-plan schema and the topic
   split identity. **Nothing after stage 2 has been run, and stage 2 has not
   been run.**
2. **Stage 3, `GATE_0_APPARATUS`** — §19's procedural pilot: the full 56-cell
   plan at $M = 4$ on twelve pre-screen topics, at fixture values that cannot
   become calibration evidence. R22's mitigation, and **the first stage that
   generates model responses** — which, before the amendment, it could not
   have done: it substituted a deterministic stand-in with no way to reach the
   pinned backend.
3. **Stage 4, `REGIME_SCREEN`**, then **stage 5, Gate 1** over the
   650-instrument population — R23's mitigation. Gate 1 reads the regime
   screen's own responses, so it is not reachable before a model runs.
4. Stages 6–18 in order.
