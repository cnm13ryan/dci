# DCI-1 v8 — LOCAL confirmatory precision for Δ_R(f)

Produced by `tools/v8_local_precision.py`. **Projection only**, labelled `PROJECTION_NOT_REGISTERED_FOR_INFERENCE`: §17.3 evaluates the precision precondition on the realised confirmatory interval and `INSUFFICIENT_PRECISION` is its registered, non-terminal consequence. Nothing here gates anything and no composed cell was generated or read.

## The allocation, read from the design

* `C.N_BLOCKS` = 384 registered confirmatory blocks, one topic each, wording assigned by frame (§8.4), over `rules.CONFIRMATORY_FRAME_PASSES` = 3 passes at offsets [0, 1, 2] — so **288 blocks per frame** (`rules.CONFIRMATORY_BLOCKS_PER_FRAME`), 1152 blocks in all, the same share Gate 3's coverage projection uses. The offsets are distinct modulo 4, so a frame's blocks are 288 *distinct* topics and no topic recurs inside a frame; 4 passes is the ceiling.
* `C.M_DRAWS` = 8 draws per cell.
* Δ_R(f) reads 4 composed cells per configuration — `pair:B+A` and `pair:B+R_j` for three references — so **2304 generations per cell per frame** and **9216 entering the contrast** per configuration.
* The **independent unit is the block**, not the generation: §17.1's bootstrap resamples blocks with replacement and carries every cell mean of a drawn block, and cells are never resampled. Eight draws inside a cell shrink the draw component and leave the topic component untouched, so the effective n for Δ_R(f) is **288**.

## The estimator

§16.1 verbatim, imported from `dci1v4.analysis.variance.variances` — the registered paired/clustered form, not an independent-proportions formula:

```
Var(Delta_R) = ( 2 (1 - rho) sigma2_topic
                 + sigma2_draw (1/M + 1/(3M)) ) / blocks
```

`rho` is the within-block correlation between two cells of the same block; the draw term's `1/M + 1/(3M)` is the 4/3 that averaging three references against one A leaves behind. The simultaneous half-width is at the F1 (6-member) Šidák constant 2.6310 — the constant §16.2's table is quoted at, and an upper bound on the bootstrap's studentised maximum-modulus value, so it is the conservative end. Δ_R's registered precision precondition (§16.2) is **0.05**, and `claims.Interval.meets_precondition` evaluates it on the **simultaneous** half-width.

## A. Per LOCAL-supported (model, frame)

| model | frame | confirmatory allocation | expected SE | 95 % half-width (simultaneous) | ~80 % MDE |
|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | f1 | 288 blocks × 8 draws × 4 cells = 9216 generations | 0.0061 – 0.0271 | 0.0161 – 0.0713 | 0.021 – 0.094 |
| `gemma-3n-e2b-it` | f3 | 288 blocks × 8 draws × 4 cells = 9216 generations | 0.0061 – 0.0271 | 0.0161 – 0.0713 | 0.021 – 0.094 |
| `qwen3-4b` | f0 | 288 blocks × 8 draws × 4 cells = 9216 generations | 0.0061 – 0.0271 | 0.0161 – 0.0713 | 0.021 – 0.094 |
| `qwen3-4b` | f3 | 288 blocks × 8 draws × 4 cells = 9216 generations | 0.0061 – 0.0271 | 0.0161 – 0.0713 | 0.021 – 0.094 |
| `qwen3-4b-instruct-2507` | f1 | 288 blocks × 8 draws × 4 cells = 9216 generations | 0.0061 – 0.0271 | 0.0161 – 0.0713 | 0.021 – 0.094 |

The interval is the span across every scenario in section B, worst case included. The frames differ only through the `CALIBRATION_ANCHORED` row — every other scenario is a property of the allocation, which is the same for all of them.

## B. Scenarios

The variance depends on composed-cell compliance, which does not exist before a freeze. Every row says where its numbers came from.

| model | frame | scenario | φ | ρ | p(1−p) | SE | simultaneous half-width | ~80 % MDE | ≤ 0.05? |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `gemma-3n-e2b-it` | f1 | CALIBRATION_ANCHORED | 0.133 | 0.062 | 0.1523 | 0.0144 | 0.0380 | 0.050 | yes |
| `gemma-3n-e2b-it` | f1 | CALIBRATION_ANCHORED_REGISTERED_RHO | 0.133 | 0.500 | 0.1523 | 0.0121 | 0.0319 | 0.042 | yes |
| `gemma-3n-e2b-it` | f1 | REGISTERED_ALTERNATE | 0.370 | 0.500 | 0.2150 | 0.0188 | 0.0495 | 0.065 | yes |
| `gemma-3n-e2b-it` | f1 | REGISTERED_PLANNING | 0.270 | 0.500 | 0.2150 | 0.0171 | 0.0450 | 0.059 | yes |
| `gemma-3n-e2b-it` | f1 | REHEARSAL_ANCHORED | — | 0.600 | — | 0.0110 | 0.0288 | 0.038 | yes |
| `gemma-3n-e2b-it` | f1 | REHEARSAL_ANCHORED_OPTIMISTIC | — | 0.740 | — | 0.0061 | 0.0161 | 0.021 | yes |
| `gemma-3n-e2b-it` | f1 | REHEARSAL_ANCHORED_PESSIMISTIC | — | 0.450 | — | 0.0158 | 0.0416 | 0.055 | yes |
| `gemma-3n-e2b-it` | f1 | WORST_CASE | 0.370 | 0.000 | 0.2500 | 0.0271 | 0.0713 | 0.094 | **NO** |
| `gemma-3n-e2b-it` | f3 | CALIBRATION_ANCHORED | 0.189 | 0.246 | 0.1457 | 0.0146 | 0.0384 | 0.051 | yes |
| `gemma-3n-e2b-it` | f3 | CALIBRATION_ANCHORED_REGISTERED_RHO | 0.189 | 0.500 | 0.1457 | 0.0128 | 0.0337 | 0.044 | yes |
| `gemma-3n-e2b-it` | f3 | REGISTERED_ALTERNATE | 0.370 | 0.500 | 0.2150 | 0.0188 | 0.0495 | 0.065 | yes |
| `gemma-3n-e2b-it` | f3 | REGISTERED_PLANNING | 0.270 | 0.500 | 0.2150 | 0.0171 | 0.0450 | 0.059 | yes |
| `gemma-3n-e2b-it` | f3 | REHEARSAL_ANCHORED | — | 0.600 | — | 0.0110 | 0.0288 | 0.038 | yes |
| `gemma-3n-e2b-it` | f3 | REHEARSAL_ANCHORED_OPTIMISTIC | — | 0.740 | — | 0.0061 | 0.0161 | 0.021 | yes |
| `gemma-3n-e2b-it` | f3 | REHEARSAL_ANCHORED_PESSIMISTIC | — | 0.450 | — | 0.0158 | 0.0416 | 0.055 | yes |
| `gemma-3n-e2b-it` | f3 | WORST_CASE | 0.370 | 0.000 | 0.2500 | 0.0271 | 0.0713 | 0.094 | **NO** |
| `qwen3-4b` | f0 | CALIBRATION_ANCHORED | 0.461 | 0.016 | 0.1888 | 0.0256 | 0.0673 | 0.089 | **NO** |
| `qwen3-4b` | f0 | CALIBRATION_ANCHORED_REGISTERED_RHO | 0.461 | 0.500 | 0.1888 | 0.0190 | 0.0500 | 0.066 | yes |
| `qwen3-4b` | f0 | REGISTERED_ALTERNATE | 0.370 | 0.500 | 0.2150 | 0.0188 | 0.0495 | 0.065 | yes |
| `qwen3-4b` | f0 | REGISTERED_PLANNING | 0.270 | 0.500 | 0.2150 | 0.0171 | 0.0450 | 0.059 | yes |
| `qwen3-4b` | f0 | REHEARSAL_ANCHORED | — | 0.600 | — | 0.0110 | 0.0288 | 0.038 | yes |
| `qwen3-4b` | f0 | REHEARSAL_ANCHORED_OPTIMISTIC | — | 0.740 | — | 0.0061 | 0.0161 | 0.021 | yes |
| `qwen3-4b` | f0 | REHEARSAL_ANCHORED_PESSIMISTIC | — | 0.450 | — | 0.0158 | 0.0416 | 0.055 | yes |
| `qwen3-4b` | f0 | WORST_CASE | 0.370 | 0.000 | 0.2500 | 0.0271 | 0.0713 | 0.094 | **NO** |
| `qwen3-4b` | f3 | CALIBRATION_ANCHORED | 0.419 | 0.056 | 0.1044 | 0.0179 | 0.0472 | 0.062 | yes |
| `qwen3-4b` | f3 | CALIBRATION_ANCHORED_REGISTERED_RHO | 0.419 | 0.500 | 0.1044 | 0.0137 | 0.0360 | 0.047 | yes |
| `qwen3-4b` | f3 | REGISTERED_ALTERNATE | 0.370 | 0.500 | 0.2150 | 0.0188 | 0.0495 | 0.065 | yes |
| `qwen3-4b` | f3 | REGISTERED_PLANNING | 0.270 | 0.500 | 0.2150 | 0.0171 | 0.0450 | 0.059 | yes |
| `qwen3-4b` | f3 | REHEARSAL_ANCHORED | — | 0.600 | — | 0.0110 | 0.0288 | 0.038 | yes |
| `qwen3-4b` | f3 | REHEARSAL_ANCHORED_OPTIMISTIC | — | 0.740 | — | 0.0061 | 0.0161 | 0.021 | yes |
| `qwen3-4b` | f3 | REHEARSAL_ANCHORED_PESSIMISTIC | — | 0.450 | — | 0.0158 | 0.0416 | 0.055 | yes |
| `qwen3-4b` | f3 | WORST_CASE | 0.370 | 0.000 | 0.2500 | 0.0271 | 0.0713 | 0.094 | **NO** |
| `qwen3-4b-instruct-2507` | f1 | CALIBRATION_ANCHORED | 0.334 | 0.008 | 0.1406 | 0.0194 | 0.0511 | 0.067 | **NO** |
| `qwen3-4b-instruct-2507` | f1 | CALIBRATION_ANCHORED_REGISTERED_RHO | 0.334 | 0.500 | 0.1406 | 0.0147 | 0.0388 | 0.051 | yes |
| `qwen3-4b-instruct-2507` | f1 | REGISTERED_ALTERNATE | 0.370 | 0.500 | 0.2150 | 0.0188 | 0.0495 | 0.065 | yes |
| `qwen3-4b-instruct-2507` | f1 | REGISTERED_PLANNING | 0.270 | 0.500 | 0.2150 | 0.0171 | 0.0450 | 0.059 | yes |
| `qwen3-4b-instruct-2507` | f1 | REHEARSAL_ANCHORED | — | 0.600 | — | 0.0110 | 0.0288 | 0.038 | yes |
| `qwen3-4b-instruct-2507` | f1 | REHEARSAL_ANCHORED_OPTIMISTIC | — | 0.740 | — | 0.0061 | 0.0161 | 0.021 | yes |
| `qwen3-4b-instruct-2507` | f1 | REHEARSAL_ANCHORED_PESSIMISTIC | — | 0.450 | — | 0.0158 | 0.0416 | 0.055 | yes |
| `qwen3-4b-instruct-2507` | f1 | WORST_CASE | 0.370 | 0.000 | 0.2500 | 0.0271 | 0.0713 | 0.094 | **NO** |

**What each scenario is.**

* `REGISTERED_PLANNING` — φ 0.27, p(1−p) 0.215, ρ 0.5: the constants §16.2's table is quoted at and the 384-block allocation was itself chosen at. This is the design's own row.
* `REGISTERED_ALTERNATE` — φ 0.37, the sensitivity value §16.3 carries.
* `WORST_CASE` — p(1−p) = 0.25 (a composed cell at 0.5, the variance maximum) with ρ = 0. Var falls as ρ rises, so ρ = 0 is the conservative end; nothing the design can produce exceeds this row.
* `CALIBRATION_ANCHORED` — φ and ρ estimated from **this frame's own solo cells** (A at n\*(f) and the three core references at their selected severities) by the production `realised_decomposition` and `realised_correlation` (§23 / check C12), with p(1−p) at B's solo compliance at m\*(f). Its ρ is the correlation between two *different constraints'* solo cells; the ρ that governs Δ_R is between composed cells that all measure **B** under different companions, which shares far more. This row therefore understates ρ and its SE is conservative for that reason as well.
* `REHEARSAL_ANCHORED*` — the block-bootstrap SE of one companion's `D` and the between-companion per-block correlation measured on the **completed v7 development rehearsal** at 384 blocks × 8 draws (`dci1v8dev.spectrum.precision.MEASURED`, already the constant Gate 3's coverage projection runs on), rescaled to the frame's blocks. This is the only row measured on composed cells that actually measure B under a companion, so it is the most apt — and it is v7 evidence, a design constant, not a v8 outcome. The pessimistic and optimistic rows are the ends of `MEASURED`'s own recorded range (SE [0.009, 0.016], ρ [0.45, 0.74]).

## C. What allocation would meet the registered precondition

A block-bootstrap SE falls as 1/√blocks, so the blocks needed scale as (realised ÷ target)². Both targets are registered: §16.2's precondition 0.05, and an 80 %-power MDE at §11.9's smallest effect of interest 0.1. No threshold is invented here.

Each row is the **worst LOCAL-supported frame** for that scenario, so the allocation it names covers every frame.

| scenario | blocks/frame for the 0.05 precondition | passes | blocks/frame for an MDE of 0.10 | passes | binding frame |
|---|---:|---:|---:|---:|---|
| CALIBRATION_ANCHORED | 522 | 6 | 227 | 3 | `qwen3-4b` f0 |
| CALIBRATION_ANCHORED_REGISTERED_RHO | 288 | 3 | 126 | 2 | `qwen3-4b` f0 |
| REGISTERED_ALTERNATE | 283 | 3 | 124 | 2 | `gemma-3n-e2b-it` f1 |
| REGISTERED_PLANNING | 234 | 3 | 102 | 2 | `gemma-3n-e2b-it` f1 |
| REHEARSAL_ANCHORED | 96 | 1 | 42 | 1 | `gemma-3n-e2b-it` f1 |
| REHEARSAL_ANCHORED_OPTIMISTIC | 30 | 1 | 14 | 1 | `gemma-3n-e2b-it` f1 |
| REHEARSAL_ANCHORED_PESSIMISTIC | 200 | 3 | 87 | 1 | `gemma-3n-e2b-it` f1 |
| WORST_CASE | 585 | 7 | 255 | 3 | `gemma-3n-e2b-it` f1 |


**Feasibility.** §6.2 holds `N_CONFIRMATORY` = 384 confirmatory topics and the sequestered set is reserved, so one pass gives 96 blocks per frame and more blocks per frame means **passes** — rendering the confirmatory topics again under a different frame offset, exactly as `rules.CALIBRATION_FRAME_OFFSETS` does at Gate 2. 4 passes is the ceiling: every frame then holds every confirmatory topic once, and a further pass would repeat a topic inside a frame and count one measurement as two.

Across every LOCAL-supported frame, **3 passes** (288 blocks per frame) covers every scenario that is an estimate rather than a bound, and is inside the 4-pass ceiling. The allocation in force is **3 passes**, 288 blocks per frame, so this is what the design already runs. The two bounds need more — `WORST_CASE` up to 7 passes — but `WORST_CASE` fixes p(1−p) at its maximum 0.25 while every supported frame's own B-solo compliance at m\*(f) is 0.75–0.88, i.e. p(1−p) of 0.10–0.19, and `CALIBRATION_ANCHORED`'s ρ is a cross-constraint floor. Neither is a scenario the pre-freeze evidence supports; both are stated so the range is not quietly truncated.

