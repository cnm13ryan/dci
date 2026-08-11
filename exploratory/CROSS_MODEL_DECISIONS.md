# Cross-model transport study — decisions

Prospective record. Every entry below was written when the decision was taken,
before the cross-model DCI estimates existed. Entries D1–D12 predate the first
scientific generation; anything added after a result is known says so explicitly
and gives the date.

Branch `exp/cross-model-transport`, worktree `/home/cnm13ryan/git/dci-cross-model`,
branched from `cfb84be` (the tip of `exp/natural-reasoning-headline`, clean).

---

## D1 — A dedicated worktree, based on the natural-reasoning branch

**Decision.** Work in a new worktree on a new branch cut from
`exp/natural-reasoning-headline`, not in either existing exploratory worktree.

**Why.** The task names `CANONICAL_RUN_MANIFEST.json`,
`NATURAL_REASONING_RESULTS.md` and `REASONING_DATA_PROVENANCE.md` as reference
artefacts, and those exist only on that branch. The other exploratory worktree
(`dci-cheapest-rocm-study`) has uncommitted work in progress — a modified
`arb_verify.py`, `arbprogram.py`, `extensions.py` and five new `mfr_*` scripts —
and running a five-model study on top of someone else's dirty tree would put
unrelated work at risk. `main` holds only the confirmatory core libraries and is
not where exploratory work belongs.

**Consequence.** The canonical run directory is read from the neighbouring
worktree by path; `exploratory/runs/` is gitignored and was not copied.

---

## D2 — Transformers, not vLLM, for every checkpoint

**Decision.** Execute all five checkpoints through Transformers 5.15.0.

**Why.** The canonical Qwen3-4B result was produced by vLLM 0.15.1+rocm720.
vLLM is **not installed anywhere on this machine** — no package in any
environment on the host, and no ROCm build present. Transformers is the one
backend that loads these architectures on gfx1100 today. Running some
checkpoints on one backend and some on another would make the five-way
comparison a backend comparison.

**Consequence, stated rather than glossed.** The cross-model comparison is
internally consistent (all five on one backend) but is **backend-confounded
against the historical vLLM result**. No number from this study may be placed
beside the canonical +0.400 as though the two were the same execution condition.

---

## D3 — The contract is copied from the canonical run's own config

**Decision.** `crossmodel/contract.py` fixes target `A`, focal `B`, matched
reference `C_L3`, backgrounds `X_SEMICOLON_FREE` and `X_PAREN_FREE`, order
`QAC`, load 3, the first 20 `pilot` tasks, 2 replicates, 512 answer tokens,
T = 0.7, top-p 0.9.

**Why.** These are not transcribed from prose. They are the flags in
`runs/stageS18_reasoning_design_20260811T144250Z/config.json`:
`--target A --focal B --arms C_L3 --background X_SEMICOLON_FREE,X_PAREN_FREE
--load 3 --permute QAC --tasks 20 --replicates 2`. The wordings, prompt assembly
and verifiers come from the v15/v19 registry through `dci_exploratory.harvest`,
so no instruction is re-typed. `assert_matches_canonical_run` re-reads that
config and fails if the two ever disagree.

**Confirmed count.** 2 arms x 2 backgrounds x 20 tasks x 2 replicates = **160**
rows per checkpoint per reasoning mode — the repository's own value, not the 320
that 4 replicates would give.

---

## D4 — Seeds derive from scientific identity, not row position

**Decision.** `seed = f(MASTER_SEED, task_id, replicate, arm, background,
order, paraphrase, phase)`, via SHA-256.

**Why.** The historical defect was one shared seed for all 160 requests, making
390/400 nominal replicate pairs byte-identical. The fix at the time was
`20260810 + offset + 7919 * i`, where `i` is the row's **index in the design
file** — which removes the duplication but re-couples the sample to position, so
re-ordering, sharding across two cards, or re-batching changes which sample a
scientific cell draws.

**Consequence.** Batch composition is fixed by sorting on `row_id` before any
device is chosen, and sharding partitions whole batches, so a row lands in the
same batch at the same offset on one card or two. Independence of replicates is
then verified on the output — `replicate_duplication` counts identical pairs
against the repository's existing 25% alarm — rather than assumed.

**Honest limit.** Transformers seeds one RNG per `generate()` call, not one per
sequence, so under batching a row's realised sample is determined by its batch's
seed and its offset within a deterministic batch. That is still a function of
scientific identity alone. `--batch-size 1` gives exact per-row seeding.

---

## D5 — Provenance travels in the row

**Decision.** Every stored row carries `model_id`, `model_revision` (a resolved
40-character sha), backend, backend version, dtype, quantization, device layout,
chat-template hash, reasoning mode, reasoning control and decoding.

**Why.** The canonical natural-reasoning file carries none of these. Its analysis
recovers the checkpoint by regex over a vLLM banner in a preserved log, and its
own comment calls this "a provenance gap in the runner". Resolution happens
before generation and refuses to fall back to a mutable alias.

---

## D6 — A practical context envelope, not the advertised maximum

**Decision.** All adapters derive the natural-reasoning engineering ceiling from
`CONTEXT_LIMIT = 40960`.

**Why.** The architectures advertise 262,144 (Qwen3.5, Gemma 4 12B), 131,072
(Gemma 4 E4B, Kimi-VL). A ceiling derived from those would be a quarter-million
token "limit" that two 24 GiB cards cannot serve and that no observed trace comes
near — a number shaped like a treatment and behaving like a fiction. 40,960 is
the envelope the canonical Qwen3-4B run used, is two orders of magnitude above
the observed natural traces, and fits the hardware. Holding it equal across
families also stops the ceiling being a cross-model confound.

**This is a safety bound, never a dose.** `assigned_reasoning_budget` is `None`
under NATURAL_REASONING by construction; the ceiling is recorded separately.

---

## D7 — The splice only where the template guarantees it

**Decision.** Qwen3.5 uses the canonical two-phase splice. Gemma 4 and Kimi-VL
use one unbroken generation, split afterwards by their own documented parsers.

**Why.** The splice — stop at the think-close marker, re-prompt past it — assumes
reasoning strictly precedes the answer. That holds for Qwen3.5 *structurally*:
its template ends the generation prompt with `<think>\n`, so the model begins
inside the trace and cannot emit answer text first. It does **not** hold for
Gemma 4. Observed directly: on trivial prompts Gemma answered and *then* opened
its `<|channel>thought` block; on the DCI prompts it opened the block first. A
splice would have stored that leading answer as reasoning and scored a second,
regenerated answer. Kimi's template likewise does not pre-open a block, and its
model card's reference parser reads one unbroken generation.

**Consequence.** Under the single-phase strategy the 512-token answer allowance
is not separately enforced; the budget is ceiling + 512 for the whole response
and truncation is measured. Recorded per row as an execution difference.

---

## D8 — Decode without skipping special tokens

**Decision.** Every family decodes with `skip_special_tokens=False` and then
strips its own control tokens, taken from the tokenizer rather than hand-listed.

**Why.** Qwen3.5 writes `<think>`/`</think>` as ordinary vocabulary that survives
`skip_special_tokens=True`. Gemma 4's `<|channel>` and `<channel|>` are **special
tokens** (ids 100 and 101) and are *erased* by it. Decoded the Qwen way, Gemma's
reasoning boundary vanishes and the scratchpad flows into the scored answer.
Taking the strip list from the tokenizer was forced by a second finding: the
first Qwen smoke run left `<|im_end|>` on the end of every answer, which would
have reached a sentence-count verifier as prose.

---

## D9 — Text-only loading is verified, not assumed

**Decision.** A text-only causal-LM class is preferred, but the missing-key
report is inspected and any missing parameter disqualifies it.

**Why.** `Gemma4ForCausalLM` against the E4B checkpoint **does not raise**. It
reports every parameter missing, initialises them at random, loads, generates,
and emits fluent multilingual noise. That noise fails "write exactly 4
sentences" exactly as a real answer would, so nothing downstream would have
noticed, and the result would have been reported as "Gemma shows no DCI".

**Consequence.** Gemma 4 stores `model.language_model.*` beside vision **and
audio** towers, so text-only loading is impossible for it and the full
conditional-generation class is used with those towers allocated. Qwen3.5 loads
text-only cleanly. A weight-integrity check (can the checkpoint name the capital
of Japan?) now gates every mode probe.

---

## D10 — Kimi-VL gets no fabricated non-thinking condition

**Decision.** `SUPPORTED_MODES` for Kimi-VL-A3B-Thinking-2506 is
`(NATURAL_REASONING,)`.

**Why.** Its chat template has no `enable_thinking` branch at all; the checkpoint
always thinks. The model card names a separate non-thinking checkpoint,
`Kimi-VL-A3B-Instruct`. That is a **different checkpoint** and therefore a
different execution condition, not a mode of this one. Emulating non-thinking by
truncating a trace would make the condition an artefact of this harness.

**Consequence.** The `NO_THINKING` cell is left missing for Kimi. No cross-model
"no-thinking versus natural" comparison includes it.

---

## D11 — The bootstrap stays at 4,000 draws

**Decision.** Reuse `dci_exploratory.plotstyle.summarise` — a paired
task-cluster bootstrap, task as the resampling cluster, 2.5/97.5 percentiles.

**Why.** The repository's `BOOTSTRAP_DRAWS` is **4000**, not the 10,000 the brief
supposed. Changing it without a documented reason would make the cross-model
intervals incomparable with every existing figure. The independent recomputation
states 4000 separately rather than importing it, so a change in one would be
caught by disagreement with the other.

---

## D12 — `A3B` and `E4B` are not memory plans

**Decision.** Memory is planned from measured bf16 weight size on the hub:
Qwen3.5-4B 8.7 GiB, Qwen3.5-9B 18.0 GiB, gemma-4-E4B-it **14.9 GiB**,
gemma-4-12B-it 22.3 GiB, Kimi-VL-A3B-Thinking-2506 **30.6 GiB**.

**Why.** `E4B` does not mean 4B stored parameters and `A3B` is an active
parameter count over a mixture of experts. Planning from the names would have
put a 30.6 GiB checkpoint on a 24 GiB card. Both checkpoints above 20 GiB are
expected to need dual-GPU capacity mode; which one is used is decided by
measurement and recorded per row.

**No numerical rescue.** If bf16 cannot run on the two cards the checkpoint is
recorded `BF16_EXECUTION_BLOCKED`. A quantized run would be a separately
labelled experiment, never a substitute in this table.

---

## D13 — What "reasoning did not close" means, and what it does not

**Decision.** `reasoning_emitted` and `natural_reasoning_closed` are separate
fields, and only a trace that was *opened and not closed* counts against the
reasoning gate.

**Why.** Gemma 4 declines to open a thought channel on easy prompts and opens one
on composed-constraint prompts. Treating "never opened" as a closure failure
would report a behavioural choice of the checkpoint as a broken adapter. It also
made the first smoke set useless for validating a reasoning interface, so the
smoke prompts now carry composed constraints while staying disjoint from the DCI
task bank.

---

## D14 — The forced-close artefact is repaired visibly

**Decision.** When the splice's answer phase contains a second think-close
marker, the answer is taken after the final one and the row is flagged
`forced_close_artefact`.

**Why.** Observed on Qwen3.5-4B when an artificially small smoke ceiling cut a
trace short: the model kept thinking into the answer phase, closed a second
time, and re-answered — putting `</think>` and a duplicated answer into the
scored channel. This is the "forced-close artefact" that makes a reasoning
condition invalid. It must never be read as a behavioural failure, so it is
counted rather than silently cleaned. It is expected to be absent under the real
engineering ceiling, where no trace is cut short.

---

## D15 — Chunk size is a scientific constraint under a 39,500-token ceiling

**Decision.** Generation chunks are small (4 in calibration, 8 in the main run)
and halve on OOM.

**Why.** A batched `generate()` runs until EVERY sequence in the batch has
finished or hit `max_new_tokens`. Under a ~39,500-token natural ceiling, one
non-closing trace therefore drags its whole chunk to the cap — not just itself.
Qwen3.5 reasons an order of magnitude longer than the checkpoint this study was
built on (median 5,848 tokens against 511 on comparable prompts), and a chunk of
ten stalled on the first attempt at its Stage D natural pass.

**Consequence, recorded because it touches the seed regime.** An OOM split
changes batch composition for the affected rows, and therefore their realised
sample. The split is printed when it happens rather than being silent, so a run
whose rows were re-batched can be identified.

---

## D16 — Stage E runs before Stage D where time is contended

**Decision.** For Qwen3.5, the natural-reasoning pilot (Stage E) was run before
the primitive gate (Stage D).

**Why.** Stage E is the admission-critical measurement: a checkpoint whose
natural reasoning cannot close reliably is not admitted at all, and there is no
point measuring its primitives. Stage D constrains *interpretation* of a result
that only exists if Stage E passes. Reordering two independent measurements
changes neither, and both are complete before the main factorial runs.

**Not a weakening.** Both stages are still required, and both are recorded in
the frozen matrix before the scientific run.

---

## D17 — Qwen3.5-4B is FOCAL_FLOOR_LIMITED under no-thinking

**Recorded 2026-08-11, from the Stage D gate, before the main slice was run or
analysed.**

Isolated compliance under `QWEN35_4B_NO_THINKING`: A = 1.00, **B = 0.12**,
C_L3 = 0.88, semicolon background = 1.00, bracket background = 0.62.

**Consequence for interpretation.** With the focal instruction at floor, the
four-state table under this condition mostly distinguishes *neither* from
*target only*, and does **not** identify arbitration between two live
constraints. Any positive τ under this condition is compatible with the model
simply failing B and the target degrading alongside it. This limit is stated now
so it cannot be fitted to whatever the estimate turns out to be.

The checkpoint is **not** excluded for it. Floor-limited constrains what may be
concluded; it does not make the row set invalid.
