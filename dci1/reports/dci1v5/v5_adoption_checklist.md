# The v5 adoption checklist

Nineteen §34 decisions, three specification questions, one confirmation. This
page is the whole of what stands between the repository and a signed
registration manifest. **Nothing on it is unfinished analysis or unwritten
code.** Every item is a judgement, and every judgement is stated as one
question in ordinary language.

Executable state: `protocol/decisions.py` (the nineteen),
`protocol/open_items.py` (U1–U3, P1), and the committed closures in
`researcher_decisions.json`. `run/cli.py plan` prints the live version of the
first table.

---

## A. Taken (4)

Recorded in `researcher_decisions.json` with evidence, in force at import, and
bound into the registration manifest by hash.

| | Question | Taken |
|---|---|---|
| **D3** | Are the 96 Calibration-B questions authored before adoption? | **Yes.** Bank authored, audited, hashed, committed |
| **D6** | Does an unbuildable reference set stop the replication? | **No.** It continues; the reference-dependent estimands become `NOT_IDENTIFIED`, irreversibly |
| **D16** | Does Calibration-B measure the whole candidate set or only Calibration-A's survivors? | **The whole set** |
| **D18** | Does the strong L3c conclusion require the near-form arm? | **Yes** |

## B. Ready for approval — a recommendation exists, on evidence (4)

Each has a decision packet in this directory. The analysis is done; the value
is the researcher's.

| | Plain question | Recommendation | Packet |
|---|---|---|---|
| **D1** | Which arms, and how many models, does the study run? | all five arms, four models, 56 cells — 1,135,104 generations | `d1_arm_compute_decision.md` |
| **D4** | Are these eight marker words the right eight? | seven approved; `though`, `namely` and `overall` each carry one open judgement | `d4_marker_audit.md` |
| **D17** | How weak may B be at the severity the study selects? | $\kappa^{B}(m^{*}) \le 0.50$ — at most half of unconstrained answers may already satisfy B | `d17_b_strength_decision.md` |
| **U2** | §11.8's secondary fit is singular as written; which repair? | A2 — family intercepts over the three **core** families | `u2_tier_model_decision.md` |

## C. Follows from something already decided (2)

Mechanical, but still a closure somebody signs.

| | Plain question | Follows from |
|---|---|---|
| **D0** | Adopt v5 at all, knowing its matching rule was fitted to v4r4? | Not mechanical, but it is the *same* judgement the researcher already made by directing this work. §30's declaration is attached permanently either way |
| **D2** | Add a load-three arm so the memo's $\Gamma$ becomes estimable? | D1. Adding it changes the cell set, so it cannot be decided after the budget |

## D. Standing proposal, no contest recorded (8)

Each has a proposal in §34, no red-team finding against it, and nothing in the
implementation or the evidence that argues with it. Closing them is an
afternoon's reading, not an investigation.

| | Plain question | Standing proposal |
|---|---|---|
| **D5** | Lexicographic validity, or a weighted composite score? | lexicographic — the development data cannot fix weights that generalise |
| **D8** | Is 0.75 the right chance ceiling? | 0.75 on the point, 0.85 on the Wilson upper bound |
| **D9** | Will an independent annotator be available? | no; the measurement basis stays `deterministic_measurement_validated` with its scope sentence |
| **D10** | One broad-class companion, or several? | one; no class claim is made |
| **D11** | Carry v4's confirmatory topics, or re-author them? | carry, with §6.2's statement of the residual |
| **D12** | Does $\delta_{\text{difficulty}}$ get a magnitude threshold of its own? | no; direction and the SESOI only |
| **D13** | Is F11 primary-tier? | yes, licensing L4b |
| **D14** | Is instructed compliance still the difficulty coordinate? | yes; raw solo secondary, `DIFFICULTY_COORDINATE_DEPENDENT` on disagreement |

## E. Contested, and the contest is recorded (2)

| | Plain question | Standing proposal | Who disagrees |
|---|---|---|---|
| **D7** | Is 0.90 the right interaction-gate ceiling? | 0.90 | **R13** — it sits inside a gap observed on twenty points, which is a coincidence and not a derivation. Recorded and not used as evidence |
| **D15** | Do the memo's 0.10 and 0.25 transfer to a *same-form* $\Delta_R$? | both transfer | **R2** — the memo defined them for a different companion pool. Registered as contestable |

## F. Not a decision — one confirmation (1)

| | What happened | What is asked |
|---|---|---|
| **P1** | §7.10 admitted Tier 3 "to the spectrum"; §7.4, §11.8 and §13.12 make that unreachable. The **sentence** was corrected to match the three sections, and the sentence is now in the preregistration | Confirm the corrected wording. **Nothing executable changed** — under either reading the code admitted no Tier-3 spectrum rung — and making Tier 3 reachable instead would be a §32 amendment to the candidate population, the §11.8 fit structure and the derived cell set. It was not made |

`U1` and `U3` are `SINGLE_ADMISSIBLE_READING`: the preregistration leaves a term
undefined, exactly one reading is executable, the implementation takes it and
records where. Neither blocks adoption and neither needs a decision.

## G. Not decisions, and not closeable by one

| | What it is | Status |
|---|---|---|
| **R5** | $\kappa^{B}$ is measured under B, so it is not pre-treatment for the pair | **accepted permanent limitation.** No §34 decision carries it, §13.8 closes only its second half, and no rule can close the first. It is reported as a limitation and it does not block the freeze |
| **R22** | the full design has never been executed on any revision | registered; §19's pilot is the mitigation and it runs before qualification |
| **R23** | the Tier-1 pool has never been measured | registered; Gate 1 over the 650-instrument population is the measurement, and it is the largest remaining compute prerequisite that needs no model |

---

## What adoption needs, in order

1. Close **D4** and **D17** — they gate the regime screen and Gate 2, and the
   packets are written.
2. Resolve **U2** — it blocks the manifest outright.
3. Close **D1** — and **D2** with it, since a load-three arm changes the cell
   set.
4. Close the remaining eleven (D0, D5, D7–D15) — eight are uncontested and two
   have their contest on the record.
5. Confirm **P1**.
6. Sign the registration manifest. `manifest.signing_blockers()` returns empty
   only when every one of the above is done.
7. Run **Gate 1** over the 650-instrument population, and §19's pilot with the
   claim-ladder tests passing, before qualification.
