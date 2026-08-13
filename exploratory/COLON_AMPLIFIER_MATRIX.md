# Colon-amplifier property isolation matrix

Which property of a background instruction makes it amplify B → A?

All rows: Pair 3, target `A` (exactly 4 sentences), focal `B` vs reference
`C_L3`, `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f`, bf16, T=0.7, wording 0, 20
pilot tasks. τ is the paired focal−reference difference in A-failure; Δ is τ
minus τ under `U_FMT_PAREN1` in the same design.

---

## The direct factorial (S14, π = QAC, k = 3, 320 generations)

| variant | wording | exact count | global scope | punctuation | **object** | free placement | own compliance | **τ(B→A)** | **Δ vs paren** |
|---|---|---|---|---|---|---|---|---|---|
| `X_SEMI_EXACT1` | `Use exactly 1 semicolon in the whole answer.` | ✔ | ✔ | ✔ | **single char** | ✔ | 0.975 | **+0.950** | **+0.950** [+0.875, +1.000] |
| `U_FMT_COLON1` | `Use exactly 1 colon in the whole answer.` | ✔ | ✔ | ✔ | **single char** | ✔ | 0.950 | **+0.450** | **+0.450** [+0.275, +0.625] |
| `U_FMT_QUOTE1` | `Use exactly 1 pair of double quotation marks in the whole answer.` | ✔ | ✔ | ✔ | **paired construct** | ✘ (must wrap content) | 1.000 | +0.050 | +0.050 [0.000, +0.125] |
| `U_FMT_PAREN1` | `Use exactly 1 pair of round brackets in the whole answer.` | ✔ | ✔ | ✔ | **paired construct** | ✘ | 1.000 | 0.000 | — (baseline) |

**Manipulation check passes for all four** (compliance 0.950–1.000), so "did not
amplify" is separable from "was not followed".

## What this eliminates

| candidate | verdict | why |
|---|---|---|
| **exact-count bookkeeping** | **insufficient** | all four are "exactly 1"; two amplify, two do not |
| **global scope** | **insufficient** | all four are whole-answer |
| **punctuation / formatting identity (as a class)** | **insufficient** | all four are formatting constraints |
| **wording length / complexity** | **insufficient** | the two amplifiers have the *shorter* wordings, but so does neither control uniformly; the semicolon and colon wordings are byte-matched but for the mark name and differ by 0.500 in τ |
| **colon-specific identity** | **REFUTED** | the semicolon amplifies **more than twice as strongly** as the colon |
| **the mark appearing in the output** | **REFUTED** (Round 7 Stage 2) | colon production ranges 0.150–0.950 across orderings without tracking Δ; within-condition, rows containing a colon fail −0.049 [−0.134, +0.033] |
| **single free-floating mark / free placement** | **SUPPORTED** | the only property that separates the two amplifiers from the two controls |

## The surviving account

> A background instruction amplifies B → A when it demands **a single
> free-floating character placed anywhere in the answer**, and does not when it
> demands a **paired construct that must wrap content**. The mark's identity
> modulates the size (semicolon ≫ colon) but is not what makes it an amplifier,
> and the mark need not actually be produced.

> **Superseded by Round 9.** Single-character atomicity is now REFUTED: a
> three-character unpaired mark (`X_ELLIPSIS_FREE`) amplifies at 1.000
> compliance. Ten positional wordings all failed their manipulation check, so
> free placement remains untested rather than supported. See
> `AMPLIFIER_MECHANISM_MATRIX.md`, which is now the current record.

**Free placement and single-character-ness are not yet separated from each
other.** Both amplifiers are single characters *and* freely placeable; both
controls are paired *and* placement-constrained. A fixed-placement single-mark
condition (Round 8 Stage 18) is the cheapest test that would separate them, and
it has not been run.

## A caveat on the strategy measure

`chain_share` does **not** order these variants: the semicolon variant has the
*lower* share (0.345) and the *higher* failure (0.950) against the colon's 0.414
and 0.450. Sentence counts do order them (1.95 vs 2.90). This is a limit of
`chain_share` as a single summary and is one more reason it is carried as
suggestive rather than as an identified mediator.

## Conditions inherited from earlier rounds

| condition | round | scope | τ or Δ | note |
|---|---|---|---|---|
| `U_FMT_COLON1`, π = QAC, k = 3 | R7 S2 | global, exactly 1 | Δ = +0.400 | replicated here at +0.450 |
| `U_FMT_COLON1`, π = ACQ, k = 3 | R7 S2 | " | Δ = **−0.125** | ordering reverses it |
| `U_FMT_COLON1`, π = QAC, k = 5 | R7 S3 | " | Δ = +0.250 | attenuates under load |
| `U_FMT_COLON1`, no permutation, k = 5 | R6 E4c | " | Δ = +0.312 | the original 2×2 |
| `U_FMT_SEMI2` (exactly **2** semicolons) | R2 D3 | global | no collapse | below the q ≈ 3 threshold |
| `X_SEMICOLON_TOTAL{3..6}` (**at least** q) | R6 A | global | failure 0.89–1.00 | a *floor*, not an exact count |
