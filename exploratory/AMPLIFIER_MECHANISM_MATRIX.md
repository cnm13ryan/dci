# Amplifier mechanism matrix

Every background variant tested for amplification of B → A, with the properties
that distinguish it and the manipulation check that says whether its own rule was
followed at all.

All rows: Pair 3, target `A` (exactly 4 sentences), focal `B` (strictly
increasing sentence lengths) against reference `C_L3`,
`Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f`, bf16, T = 0.7, wording 0, 20 pilot
tasks × 2 replicates, π = QAC, k = 3. τ is the paired focal−reference difference
in A-failure; intervals are cluster-bootstrapped over the 20 tasks.

**Compliance is not decoration.** A variant obeyed 0.10 of the time supports no
conclusion about the property it was built to vary.

---

## The variants

| variant | wording (clause after the base) | chars | paired? | placement | exact? | representation | own compliance | τ(B→A) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `X_SEMI_EXACT1` | — (bare, Round 8) | 1 | no | free | ✔ | named | 0.975 | **+0.950** [+0.875, +1.000] | amplifies |
| `X_SEMICOLON_FREE` | `place it wherever you judge best` | 1 | no | free | ✔ | named | **1.000** | **+0.950** [+0.875, +1.000] | amplifies |
| `U_FMT_COLON1` | — (bare, Round 8) | 1 | no | free | ✔ | named | 0.950 | **+0.450** [+0.275, +0.625] | amplifies |
| `X_COLON_FREE` | `place it wherever you judge best` | 1 | no | free | ✔ | named | 0.938 | **+0.700** [+0.550, +0.850] | amplifies |
| `X_ELLIPSIS_FREE` | `place it wherever you judge best` | **3** | no | free | ✔ | named | **1.000** | **+0.400** [+0.250, +0.550] | **amplifies** |
| `X_DASHDASH_FREE` | `place it wherever you judge best` | 2 | no | free | ✔ | named | **0.000** | (+0.275) | **manipulation failed** |
| `X_PAREN_FREE` | `place it wherever you judge best` | 2 | **yes** | must wrap | ✔ | named | 0.988 | **+0.075** [0.000, +0.150] | does not amplify |
| `U_FMT_PAREN1` | — (bare, Round 8) | 2 | **yes** | must wrap | ✔ | named | 1.000 | 0.000 | does not amplify |
| `U_FMT_QUOTE1` | — (bare, Round 8) | 2 | **yes** | must wrap | ✔ | named | 1.000 | +0.050 [0.000, +0.125] | does not amplify |

### Positional variants — all failed their manipulation check

| variant | clause | own compliance | τ | usable? |
|---|---|---|---|---|
| `X_SEMICOLON_AT_W1` | `immediately after the first word` | 0.087 | +0.875 | **no** |
| `X_SEMICOLON_AT_W2` | `immediately after the second word` | **0.000** | +0.700 | **no** |
| `X_SEMICOLON_AT_W5` | `immediately after the fifth word` | 0.100 | +0.775 | **no** |
| `X_SEMICOLON_AT_W10` | `immediately after the tenth word` | 0.050 | +0.825 | **no** |
| `X_SEMICOLON_FIRST5` | `within the first five words` | 0.138 | +0.800 | **no** |
| `X_SEMICOLON_FIRST12` | `within the first twelve words` | 0.325 | +0.450 | **no** |
| `X_SEMICOLON_FIRST25` | `within the first twenty-five words` | 0.338 | +0.250 | **no** |
| `X_COLON_AT_W5` | `immediately after the fifth word` | 0.025 | +0.850 | **no** |
| `X_COLON_AT_W10` | `immediately after the tenth word` | **0.000** | +0.825 | **no** |
| `X_COLON_FIRST12` | `within the first twelve words` | 0.087 | +0.600 | **no** |

Ten positional wordings, two marks, exact indices and windows alike: compliance
never exceeds 0.338, against 0.938–1.000 for the same instruction with placement
left free. **Fixing where the mark goes is not a manipulation this model can
execute at k = 3**, so Stage 10's intended contrast could not be run. Their τ
values are recorded for completeness and are **not** evidence about placement.

---

## What is now established

| candidate | verdict | evidence |
|---|---|---|
| exact-count bookkeeping | **insufficient** | all nine primary variants are "exactly 1"; some amplify, some do not |
| global scope | **insufficient** | all are whole-answer |
| punctuation / formatting identity as a class | **insufficient** | all are formatting constraints |
| colon-specific identity | **REFUTED** (R8) | the semicolon amplifies more than twice as strongly |
| the mark actually appearing in the output | **REFUTED** (R7 S2) | colon production varies 0.150–0.950 across orderings without tracking Δ |
| wording length / having a second clause | **REFUTED** | the length-matched free arm reproduces the bare wording exactly (`X_SEMICOLON_FREE` +0.950 = `X_SEMI_EXACT1` +0.950), and the *paired* control stays null under the identical clause (+0.075) |
| **single-character atomicity** | **REFUTED** | `X_ELLIPSIS_FREE` is **three characters** and amplifies (+0.400), against +0.075 for the wording-matched paired control — Δ = +0.325 [+0.175, +0.475], at 1.000 compliance |
| **paired construct that must wrap content** | **SUPPORTED as protective** | three paired variants, two wordings, compliance 0.988–1.000, τ ∈ [0.000, +0.075] |
| free placement | **untested** — not "unsupported" | every attempt to remove placement freedom destroyed compliance |

## The narrowest surviving account

> A background instruction amplifies B → A when it demands **one unattached mark
> that the model must find somewhere to put**, and does not when it demands a
> **paired construct that must wrap content**. The mark's identity and its
> character count modulate the magnitude — semicolon (+0.950) > colon (+0.700) >
> ellipsis (+0.400) — but neither is what makes an instruction an amplifier, the
> mark need not appear in the output, and single-character-ness is now refuted as
> necessary.

**What is still confounded.** "Unattached" and "freely placeable" remain a single
property, because no compliable way to fix placement was found. The paired
controls differ from the amplifiers in both respects at once.

## A dissociation the strategy measure does not capture

The ellipsis amplifies (+0.400) while producing `chain_share = 0.025` and 3.300
sentences; the semicolon amplifies (+0.950) with `chain_share = 0.432` and 1.325
sentences. **The same amplification direction is reached by two different
structural routes** — clause-chaining collapse for the semicolon, ordinary
undershoot for the ellipsis. This is a second reason `chain_share` is carried as
descriptive and not as an identified mediator, and a direct instance of the
warning against inferring one mechanism from a shared A-failure.

## Does more reasoning change the amplifier?

Measured directly (see `REASONING_COMPUTE_MATRIX.md`). Under a **non-amplifying**
background, additional reasoning drives τ to exactly 0.000 and holds it there.
Under the **amplifier** it does not: τ settles at +0.500 and Δ amplification
*grows* with budget, from +0.200 [−0.150, +0.550] at b = 0 to +0.500 [+0.300,
+0.700] at b = 4096. **Reasoning does not overcome the amplifier; it widens the
gap.**
