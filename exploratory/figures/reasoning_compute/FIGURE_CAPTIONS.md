# Figure captions

Every figure in this directory is rebuilt from preserved generations by
`../../make_figures.py`. No value is typed in by hand; the script ends with a QA
pass that re-derives each published headline number and fails if it disagrees.

## Execution condition (all reasoning figures)

| | |
|---|---|
| checkpoint | `Qwen/Qwen3-4B` @ `1cfa9a7208912126459214e8b04321603b3df60c` (a reasoning model) |
| reasoning protocol | two-phase. Phase 1 thinks under the assigned budget `b`, stopping at `</think>`; phase 2 answers under a budget **identical in every treatment** (512 tokens). The reasoning channel is never scored and never reaches a verifier. |
| `b = 0` | the model's **native non-thinking mode** (`enable_thinking=False`) — not a trace truncated to zero |
| backend | vLLM 0.15.1+rocm720, tensor-parallel 2 with `disable_custom_all_reduce=True` and `NCCL_P2P_DISABLE=1` |
| hardware | 2 × Radeon RX 7900 XTX (gfx1100), ROCm 7.2 |
| numerics / decoding | bf16, T = 0.7, top-p 0.9, seeded |
| task | Pair 3. **A** (target) = write exactly 4 sentences. **B** (focal) = make each sentence strictly longer than the last. **C_L3** = the matched reference occupying B's slot. |
| amplifier `C` | `X_SEMICOLON_FREE` — "Use exactly 1 semicolon in the whole answer, and place it wherever you judge best." |
| control `C` | `X_PAREN_FREE` — identical wording, "1 pair of round brackets". Matched in clause count and length. |
| design | π = QAC, k = 3, 20 pilot tasks × 2 replicates × 2 arms × 2 backgrounds × 5 budgets = **800 generations** |
| uncertainty | percentile bootstrap over the **20 task clusters**, 4000 draws, 2.5/97.5 percentiles, seeded per estimand so an interval does not depend on figure order. **Exploratory; uncorrected for multiplicity.** |

Amplifier figures (11–14) use `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f` on the
unchanged Transformers path, one GPU, so they remain comparable with Rounds 1–8.

τ(B→A) is the within-task paired difference in A-failure between the focal and
reference arms. Δ is τ(amplifier) − τ(control), paired task by task.

---

## `main_compute_figure`

**Panels.** A: compliance versus budget, focal arm. B: the two failure rates τ is
built from. C: τ(B→A) for both backgrounds. D: Δ amplification. E: arbitration
under the control background. F: realised reasoning and cap-hit rate.
**x-axis** assigned budget b (linear, literal). **y** as labelled.
**Observation.** τ under the control falls from +0.400 to exactly 0.000 by
b = 512 and stays there; under the amplifier it ends at +0.500. Δ grows from
+0.200 [−0.150, +0.550] to +0.500 [+0.300, +0.700].
**Permitted interpretation.** In this experiment, additional test-time reasoning
largely resolves ordinary directional interference and does not resolve amplified
interference — *amplified interference is more compute-resistant*.
**Caveat.** Panels C and D are two views of one dataset, not independent
evidence. The b = 256 dip is real and unexplained (see below).

## `fig01_assigned_vs_realised` (+ `_symlog` supplementary)

**Left** b → E[M | b] with the interquartile band, against the M = b diagonal.
**Right** cap-hit and natural-closure rates. **x** assigned budget, linear
(primary); the `_symlog` file is the same figure on a symlog axis (linthresh 256)
for low-budget readability and is **supplementary only**.
**Observation.** Realised reasoning rises 0 → 255 → 447 → 637 → 769 while
cap-hit falls 0.950 → 0.556 → 0.225 → 0.025. b = 4096 is effectively
non-binding.
**Caveat.** M is bounded above by b by construction, so the curve must bend; what
is informative is *where* it leaves the diagonal.

## `fig02_compliance_vs_budget`

**Panels** A / focal-Q / C / joint compliance × focal arm (top) and reference arm
(bottom). Backgrounds are never pooled. **Dotted ring** = budget exhausted on
≥ 90% of rows.
**Observation.** Target compliance in the focal arm reaches **1.000** at b ≥ 512
under the control and stays at 0.375–0.450 under the amplifier. Focal-B
compliance never exceeds 0.20 in any cell, and joint compliance never exceeds
0.10. Background compliance stays 0.80–1.000 throughout.
**Permitted interpretation.** Reasoning does not lift all constraints together —
it redistributes compliance toward the target.
**Caveat.** B is very hard for this model at every budget; its flat curve is a
floor effect, not evidence that reasoning cannot help B.

## `fig03_dci_components`

**Panels** control (left), amplifier (right). Solid = P(F_A | B, b), dashed =
P(F_A | R, b); the shaded gap is τ.
**Observation.** Under the control the gap closes because **focal** failure falls
to 0.000, not because reference failure rises. Under the amplifier focal failure
stays at 0.55–0.62 while reference failure falls from 0.25 to 0.05.
**Permitted interpretation.** The τ movement is a change in the focal arm, which
is what a directional-interference claim requires.
**Caveat.** Shown because a difference score alone cannot distinguish these cases.

## `fig04_tau_vs_budget`

**x** assigned budget. **y** τ(B→A). Zero line drawn. Points joined as a visual
guide only.
**Observation.** Control: +0.400 → +0.150 → 0.000 → 0.000 → 0.000. Amplifier:
+0.600 → +0.075 → +0.375 → +0.450 → +0.500.
**Permitted interpretation.** Ordinary B→A interference becomes negligible at
higher reasoning budgets **in this Qwen3-4B experiment**; interference under the
amplifying background remains substantial.
**Do not claim** a scaling law, a plateau beyond 4096, or generalisation to
reasoning models as a population. Five budgets on one checkpoint.

## `fig05_amplification_gap`

**y** Δ = τ(amplifier) − τ(control), paired by task.
**Observation.** +0.200 [−0.150, +0.550] at b = 0, −0.075 [−0.376, +0.250] at
b = 256, then +0.375, +0.450, **+0.500 [+0.300, +0.700]**.
**Permitted interpretation.** The contextual gap widens with reasoning.
**Critical caveat.** **A growing gap does not mean the amplified condition
becomes more harmful.** Here it widens mainly because the control's interference
is *removed* — the amplifier's own τ ends below its b = 0 value (+0.500 against
+0.600). Read Δ against fig03 before interpreting it.

## `fig06_arbitration`

**Panels** control and amplifier, focal arm. Four states; direct-labelled where
separated, legend always present.
**Observation.** Control: "neither" 0.400 → **0.000**, "target only" 0.600 →
**0.900**, "both" only 0.100. Amplifier: "neither" stays at 0.500–0.600.
**Permitted interpretation.** Under the ordinary background the improvement is
**target-priority arbitration**, not joint satisfaction — reasoning decides which
constraint to keep, it does not reconcile them.
**Caveat.** With B compliance near its floor, "both" has little room; the
neither → target-only movement is the interpretable signal.

## `fig07_performance_vs_residual_gap`

Aligned panels on one shared budget axis, no dual y-axis. **Upper** P(A
compliant), focal arm, control background. **Lower** Δ amplification.
**Observation.** The upper curve saturates at 1.000; the lower one grows.
**Permitted interpretation.** A conventional accuracy curve can hide residual
context dependence — the same budgets that look "solved" above show a widening
gap below.
**Caveat.** The two panels are different conditions by construction (the upper is
the control only); that is the point, not a confound.

## `fig08_descriptive_realised_reasoning`

**x** mean **realised** reasoning tokens M, labelled by assigned budget.
**DESCRIPTIVE ONLY.** M is chosen partly by the model and is post-treatment.
**Do not** read these as dose-response curves and do not regress on M.

## `fig09_time_axis`

**x** mean seconds per response: 0.094, 0.312, 0.484, 0.669, 1.039 s for
b = 0…4096. **This is throughput, not latency** — vLLM generated all 160 rows of
a budget as one continuously-batched job and the figure divides that batch wall
clock by 160. It covers **both** phases (reasoning and the fixed answer budget).
**Purpose.** A resource axis independent of tokenizer units.
**Caveat.** Batch composition, hardware and backend all enter this number; it is
not portable to other setups.

## Cost figure — deliberately absent

No cost figure is produced. These runs are on local hardware with no billing
meter, and the only defensible input would be an energy estimate from board power
under partial utilisation, which would be a guess dressed as a measurement.
Tokens (fig08) and time (fig09) are the resource axes, as instructed.

## `fig11_amplifier_variants`

**Left** τ by background variant at π = QAC, k = 3, point + bootstrap interval,
coloured by declared structural class. **Right** the variant's own compliance,
with the 0.50 usability gate.
**Observation.** Every unattached-mark variant that was actually followed
amplifies (+0.400 to +0.975); every enclosing-pair variant does not (0.000 to
+0.075) at compliance 0.988–1.000. All ten positional wordings fall **below**
0.35 compliance.
**Permitted interpretation.** The unattached/enclosing distinction tracks
amplification; single-character-ness does not (the 3-character ellipsis
amplifies).
**Critical caveat.** Grey rows failed their manipulation check. **Their τ values
are not evidence about placement.** Free placement is therefore **untested**, not
established — the fixed-placement interventions could not be executed by the
model.

## `fig12_order_dependence`

Same instruction set at π = QAC and π = ACQ, k = 3, with compliance printed in
each bar.
**Observation.** Semicolon τ = +0.950 at QAC and +0.100 [−0.100, +0.300] at ACQ;
Δ against the enclosing control moves from +0.875 to **−0.125**.
**Permitted interpretation.** The same three constraints move from strongly
amplifying to null-or-reversed when their order changes.
**Do not claim** "the amplifier must come after the target". The design varies
the whole permutation at once and does not identify a rule that simple.

## `fig13_load_transport`

k = 3 versus k = 5 at π = QAC. k = 5 is raised with `--fixed-tail`, and the rows
carry load 5 (QA-checked); an earlier run mislabelled by a CLI flag is excluded.
**Observation.** Semicolon Δ +0.875 → +0.650; ellipsis Δ +0.325 → +0.125
[−0.075, +0.325], while the control's own τ rises to +0.225 under load.
**Permitted interpretation.** Membership of the same apparent amplifier class at
low load does not guarantee the same robustness under compositional load.

## `fig14_strategy_dissociation`

**x** `chain_share` (left) and mean sentence count (right) in the focal arm;
**y** τ. One point per variant from a declared preferred run; replications appear
in fig11 and in `data/amplifier_conditions.csv`.
**Observation.** The semicolon amplifies at chain_share ≈ 0.43 with 1.3
sentences; the **ellipsis amplifies at chain_share ≈ 0.03 with 3.3 sentences**.
**Permitted interpretation.** Similar DCI effects arise through different
downstream response strategies, so `chain_share` is **not a sufficient mediator**
of amplification.
**Caveat.** These are condition-level associations, not mediation estimates.
`chain_share` remains descriptive throughout this study.
