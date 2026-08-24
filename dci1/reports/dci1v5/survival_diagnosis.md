# Why zero v5 replications survived to confirmatory generation

**Classification: DEVELOPMENT_EVIDENCE.** Current v5 is read here only for
survival and identification. No effect quantity is estimated, compared or
interpreted, and nothing below is evidence about `Delta_j`, `Delta_R` or `Xi`.
Numbers: [`survival_diagnosis.json`](survival_diagnosis.json). Where a
reconstruction and a signed record disagree, the signed record governs; the
family-level reconstruction is marked *approx* because it re-derives
eligibility rather than replaying the run's expansion rounds.

There are **two independent bottlenecks**. Neither is a threshold being too
strict; both are the candidate library and the operating point being unable to
supply what the registered criteria ask for.

## Bottleneck 1 — §12.6 C4: too few straddling feature groups

C4 requires **≥6 feature groups** each containing a family that straddles
$\iota_A$ with **≥3 eligible rungs** spanning **≥0.40** in $\iota$.

| model | $\iota_A$ | straddling groups | eligible rungs | above $\iota_A$ | below | C4 |
|---|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | 0.667 | **4** | 174 | 19 | 155 | ✗ |
| `gemma-3n-e4b-it` | 0.708 | **5** | 179 | 14 | 163 | ✗ |
| `qwen3-4b` | 0.667 | **5** | 174 | 20 | 154 | ✗ |
| `qwen3-4b-instruct-2507` | 0.624 | 8 | 164 | 21 | 143 | ✓ |

Two facts locate the cause precisely.

**The eligible pool is lopsided.** Only 14–21 rungs sit above $\iota_A$ against
143–163 below. A family can straddle only if it has an eligible rung on each
side, so with so few rungs above, most families cannot straddle at all —
roughly 23–27 of ~35 families are one-sided on every model. The lower a model's
$\iota_A$, the more straddling groups it has: `qwen3-4b-instruct-2507` has the
lowest $\iota_A$ (0.624) and the most groups (8); `gemma-3n-e4b-it` has the
highest (0.708) and the fewest rungs above (14). **The library does not reach
far enough above $\iota_A$ while staying inside the $p_{solo} \in [0.10,0.90]$
eligibility band.**

**The 0.40 within-family span is the second binding condition.** On every
model, 3–4 families *do* straddle with ≥3 rungs and are rejected only on span,
and they miss narrowly:

- `gemma-3n-e2b-it`: `marker_thus` 0.38, `letter_a` 0.36, `marker_hence` 0.33, `marker_indeed` 0.29
- `gemma-3n-e4b-it`: `marker_hence` 0.33, `marker_namely` 0.29, `marker_thus` 0.21
- `qwen3-4b`: `sentence` 0.37, `marker_thus` 0.33, `marker_namely` 0.33

The recurring names are the marker families, whose ladders (1…8 occurrences)
compress into a narrow $\iota$ range. Had span alone been satisfied, each of
the three failing models would have cleared C4 with margin. **This is a
library-shape deficit, not a threshold problem:** the ladders are too short in
$\iota$, and too few of them extend above $\iota_A$.

Consequence: C4 false → `decisive_met` false → the core and spectrum arms are
dropped → D6 `REFERENCE_SUPPORT_NOT_IDENTIFIED`, irreversible, 48 estimand
members unidentified, and the mandatory `support_satisfied` prefreeze check
fails. Three replications died on this single condition.

## Bottleneck 2 — §13.14 composed headroom: the operating point ignores composition

§13.14 requires every registered cell type inside **[0.05, 0.95]**.

| model | worst cell | compliance | margin |
|---|---|---|---|
| `gemma-3n-e2b-it` | `pair:B+CL` (B) | 0.8958 | **+0.054** |
| `qwen3-4b` | `pair:A+B` (B) | 0.8958 | **+0.054** |
| `gemma-3n-e4b-it` | `pair:B+CL` (B) | **0.9792** | −0.029 → TERMINAL |
| `qwen3-4b-instruct-2507` | `pair:B+R1` (B) | **0.9896** | −0.040 → TERMINAL |

**Gate 4 was marginal on all four, not just the two that failed.** The
survivors cleared their worst cell by 0.054.

The mechanism is composition lifting the B slot above its solo value:

- `gemma-3n-e2b-it`: `solo:B` 0.7917 → `pair:B+CL` 0.8958 (**+0.104**)
- `qwen3-4b`: `solo:B` 0.8438 → `pair:A+B` 0.8958 (**+0.052**)

Order matters and the lift is not uniform — on e2b, `pair:A+B` *lowers* B to
0.625 while `pair:B+CL` raises it to 0.896.

$m^*$ is chosen at Gate 2 from **solo** curves. Composition is not measured
until Gate 4, after references are fixed. So a model whose solo B sits at
0.79–0.84 can be handed an $m^*$ that looks comfortable and then crosses 0.95
once composed. Models with higher baseline compliance cross first — which is
exactly which two died.

## Which of the four candidate causes applies

| candidate cause | verdict |
|---|---|
| **candidate-library coverage** | **Primary.** Drives bottleneck 1 entirely: too few rungs above $\iota_A$, ladders too compressed in $\iota$. |
| **operating-point choice** | **Primary.** Drives bottleneck 2: $m^*$ selected on solo behaviour with no composed-headroom margin. |
| model-specific behaviour | **Modulating, not causal.** It sets *which* models cross first (higher $\iota_A$ → fewer straddling groups; higher baseline compliance → composed ceiling), but all four were marginal on both criteria. |
| another registered design bottleneck | **Not found.** C1, C2, C3, C5, C6 passed everywhere; C7/C8 are non-decisive by construction. Gate 0, the regime screen, Gates 1, 2, 2.5, 3A, 3B and 3C all passed on all four. |

The two bottlenecks are independent: fixing the library would not have saved
`qwen3-4b-instruct-2507`, which cleared C4 and died at Gate 4; fixing the
operating point would not have saved the three that died at C4.
