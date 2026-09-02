# DCI-1 v8 pre-freeze audit — verification ledger (2026-09-02)

Every suspected finding was verified against the repository at commit
`11697e9` (the state that froze the superseded root) before any change was
made. Paths are relative to the repository root unless they begin with
`dci1v7/` or `dci1v8dev/`, which abbreviate `dci1/src/…`. Line numbers are
those of `11697e9`. Protected confirmatory outputs were never opened; the
protected-outcome check is §14 below.

| # | finding | verdict |
|---|---|---|
| 1 | v8 is a redesign, not a bug-fixed v7 | **CONFIRMED** (docs: PARTIALLY — no single statement said so) |
| 2 | v7 recorded κ_R = 0; v8 corrects it | **CONFIRMED**, with a correction: two causes, not one |
| 3 | v7 applied LOCAL matching to the spectrum; v8 splits the rules | **PARTIALLY CONFIRMED** for v7 (formally exempt, leaked in effect); **CONFIRMED** for v8 |
| 4 | n*(f) unstable to calibration noise | **CONFIRMED** |
| 5 | many effectively tied reference triples | **CONFIRMED** (numbers: `reports/dci1v8dev/reference_sensitivity/REPORT.md`) |
| 6 | frame-blind pre-screen | **PARTIALLY CONFIRMED** (mechanism real; screen coordinate too noisy to have steered around it; counts small) |
| 7 | model × frame eligibility rule as described | **CONFIRMED** |
| 8 | unequal calibration budgets | **CONFIRMED** (facts); the exposed model is `gemma-3n-e4b-it`, not `gemma-3n-e2b-it` |
| 9 | 288 vs 384 in active sources | **CONFIRMED** |
| 10 | v8 analysis narrower than v7's registered pipeline | **CONFIRMED** |
| 11 | adaptive design history | **CONFIRMED** (no composed outcome involved) |
| 12.1 | `hash()` in the stability bootstrap | **CONFIRMED** |
| 12.2 | no clean-worktree gate | **CONFIRMED** |
| 12.3 | fixed-seed generation not bit-for-bit deterministic | **CANNOT ESTABLISH from the record; measured** — see `backend_determinism.md` |

## 1. v8 is a redesign — CONFIRMED

- v7 pooled the four frames: `dci1v7/stages/calibration_table.py:104-144`
  (`CalibrationRow` has no frame field); one scalar n*/m* per model
  (`dci1v7/run/gates_run.py:369`, `run/freeze_run.py:165,446`);
  `dci1v7/analysis/estimators.py:138 delta_r()` takes no frame; the v5
  protocol text calls wordings a block-level factor
  (`user-notes/DCI1_preregistration_v5.md:1014-1020`).
- v8 conditions on the frame: `dci1/docs/V8_FRAME_CONDITIONING.md:53-73`;
  `dci1v8dev/run/calibration.py:1,26-29` (n*(f), m*(f), ι_A(f));
  `run/references.py:1-33` (Gate 3 per frame); `rules.py`
  `LOCAL_ELIGIBILITY_MIN_FRAMES`.
- v7 composed prompts mixed frames: `dci1v7/design/cells.py:271-287`
  (`wording_indices`: first = i mod 4, second = (i + i//4) mod 4 — equal
  only when ⌊i/4⌋ ≡ 0 mod 4, so three blocks in four rendered the two lines
  under different frames; `assert_allocation` :349-405 enforced that
  balance). v8: `dci1v8dev/confirm/design.py` renders every slot under the
  block's frame and refuses otherwise; test
  `tests_v8dev/test_confirm_design.py::test_every_slot_of_a_block_is_under_the_blocks_frame`.
- Templates changed: frames 1 and 2 of the exact-count template gained
  "the word" (`wording_v8.py:68-73`; guard :132-136); grammatical number
  repaired at q = 1 in every non-Tier-1 template (`wordings.py:86-96`); B
  unchanged (`wordings.py:133-136`).
- Docs: `RESEARCH_STATE.md:114-118` says "redesign"; but
  `CHANGES_SCIENTIFIC.md:745,794` headings say "(no registered rule
  changes)" and "replication" at `RESEARCH_STATE.md:300` means one model's
  run. **Resolved:** `docs/DCI1_preregistration_v8.md` §1 and §20 state the
  redesign in one place; `CHANGES_SCIENTIFIC.md` (2026-09-02, audit entry)
  and `RESEARCH_STATE.md` say v8 is not a replication of v7.

## 2. Chance basis — CONFIRMED (two causes)

- κ_R = 0 was a producer bug: `except ProtocolError → chance =
  {"compliance": 0.0}` at `7f89dae^:dci1v7/run/gates_run.py:686-691`; no
  grid row states a non-outcome candidate, so the fallback fired for every
  candidate of every v5/v6/v7 replication. κ_A was never 0: it came from a
  broader all-A-absent denominator (`gates_run.py:308,546-550`). Fixed by
  `7f89dae` (2026-08-29); current refusal path `gates_run.py:709-723`.
- Stored evidence: no v7 evidence root is on this machine;
  `reports/dci1v7/chance_basis_impact/REPORT.md:5` states the recorded
  column is 0.0 on every replication (gemma-3n-e2b-it: κ_A = 0.0117 against
  κ_R = 0.0000); `reports/dci1v8dev/chance_basis/v7__qwen3-4b.json`: 49/128
  labels have non-zero corrected κ.
- v8: one unconstrained cell per (topic, frame) for A and every candidate
  (`run/calibration.py:292-296, 449-495, 496-518`); r9 qwen3-4b frame 0:
  19 of 63 rows have κ > 0 (max 0.704), `chance_basis.cell =
  "unconstrained"`, `kappa_a = 0.0` is a measured zero (ι_A 0.6706 vs
  0.6528 on v7's basis, recorded beside it).
- No silent zero: `execute.py:660-663`, `gates_run.py:709`,
  `regime.py:131-135`, `chance_basis.py:110/203/262`.
- **Resolved:** `tests_v8dev/test_chance_basis_guard.py` (refusal on a
  missing unconstrained cell; equal basis for A and references; AST guard
  against an except-handler assigning a literal zero to a chance name);
  definition in the preregistration §11.3.

## 3. LOCAL/SPECTRUM validity — PARTIALLY CONFIRMED (v7), CONFIRMED (v8)

- v7 formally exempted the spectrum from V_diff
  (`dci1v7/stages/selection.py:62-63`) but V_diff re-entered through
  V_stab's split admissibility (`stages/stability.py:66-69`, one verdict
  computed in the core slot and shared) and spectrum rungs were drawn only
  from V_diff-passing core families (`selection.py:15-18`); the spectrum
  pool spanned 0.07–0.16 in ι against ± 0.20 targets
  (`CHANGES_SCIENTIFIC.md:800-806`).
- v8: `dci1v8dev/spectrum/validity.py:71-83` — LOCAL = v7's full V(R);
  SPECTRUM = V_spec, V_sat, V_coord, V_chance, V_struct, V_inter_s, V_stab
  (unfolded), V_pos; coverage gate `spectrum/coverage.py:45-79`; backups
  `spectrum/backups.py:32-81`. Tests: `tests_v8dev/test_spectrum.py:46,62,
  74,102,154`, `test_simulation_and_evidence.py:62`,
  `test_eligibility_boundary.py`, `test_backups.py`,
  `test_frame_conditioning.py:308,348`.
- Gap: no test guarded the pool-composition half (spectrum candidates not
  restricted to V_diff-passing families). **Resolved:**
  `tests_v8dev/test_spectrum_pool_independence.py`.
- Rationale documented: `spectrum/validity.py:1-39,86-120`,
  `docs/V8_CANDIDATE.md:62-124`; both rules restated in the preregistration
  §12–§13.

## 4. Operating-point instability — CONFIRMED

The superseded root's `MEMBERSHIP` records (10:43–11:10Z, seeded with the
process-salted `hash()`) recorded, for the frozen n*(f), the share of 2000
topic resamples on which §12.3 re-selected it:

| model | frame | LOCAL | n* | P(n* reproduced) | m* | P(m* reproduced) |
|---|---|---|---|---|---|---|
| qwen3-4b | 0 | yes | 6 | 0.56 | 12 | 0.95 |
| qwen3-4b | 3 | yes | 5 | 0.40 | 13 | 0.89 |
| gemma-3n-e2b-it | 1 | yes | 3 | 0.88 | 10 | 0.76 |
| gemma-3n-e2b-it | 3 | yes | 7 | 0.47 | 11 | 0.91 |
| gemma-3n-e2b-it | 0 | no | 8 | 0.85 | 8 | 0.46 |
| gemma-3n-e4b-it | 1 | no | 5 | 0.39 | 9 | 0.55 |

Three of the four LOCAL frames fall below 2/3 on n*. **Resolved:**
`confirm/stability.py` records status `OPERATING_POINT_UNSTABLE` below
`OPERATING_POINT_MIN_RECOVERY` = 2/3, the runner-up and its share, and the
membership seeds it deterministically; the frozen point stays authoritative;
the runner-up sensitivity arm (`design.ARM_RUNNER_UP`) is added to an
unstable LOCAL frame's design and analysed as F_RUNNER_UP. The
deterministic recomputation on the final pilot roots is in
`operating_point_stability.md` beside this file.

## 5. Reference-triple instability — CONFIRMED

The superseded membership records carried 9–10 admissible triples per LOCAL
frame over the five frozen families; the enumeration over all LOCAL-valid
families, the distances |ι_R − ι_A(f)| with their SEs, and the topic-bootstrap
probability that the primary triple is re-selected are in
`reports/dci1v8dev/reference_sensitivity/REPORT.md`
(`tools/v8_reference_sensitivity.py`). **Resolved:** R1/R2/R3 stay the frozen
primary; R4/R5 are frozen backups generated beside B; the analysis re-forms
Δ_R(f) over every admissible triple of the five (F_REFSENS) and reports
whether the reading changes; membership records carry the distances.

## 6. Frame-blind pre-screen — PARTIALLY CONFIRMED

`tools/v8_frame_screen_diagnostic.py` →
`reports/dci1v8dev/frame_screen_diagnostic/REPORT.md`. Ranking and retention
are pooled (the prescreen table has no frame column; one scalar
`iota_a_prescreen`). Cross-frame ι spread at calibration (median across
families): 0.209 / 0.260 / 0.194 / 0.266 for qwen3-4b / gemma-3n-e2b-it /
qwen3-4b-instruct-2507 / gemma-3n-e4b-it — 2.3× the caliper — but the screen
coordinate's own SE at six topics per frame is 0.17–0.21, so a frame-aware
screen could not have steered around it. Unforwarded Tier-1/2 rungs whose
frame-f screen ι lies inside the caliper: 0–5 per frame (3, 5, 1, 2 on the
four unsupported frames of gemma-3n-e4b-it and 2–3 on the others), of which
the top-up rule captures 0–3. **Resolved:** membership unchanged by the
diagnostic; the frame-aware top-up (§15.4) is the one prospective channel;
the scope restriction is stated (preregistration §16).

## 7. Eligibility rule — CONFIRMED

`dci1v8dev/run/eligibility.py::local_support` (core identified, ≥ 5
LOCAL-valid families, ≥ 2 backups on the frame's own table) and
`local_eligibility` (≥ `LOCAL_ELIGIBILITY_MIN_FRAMES` = 2 supported frames;
every supported frame of an eligible model enters); provenance: commit
`5e4791e` (2026-08-31 16:31) after pilots r8/r9. **Resolved:** the full rule
(frame support, model eligibility, which frames enter, unsupported frames,
SPECTRUM for a LOCAL-ineligible model, LOCAL_TOPUP trigger, candidates and
stopping) is fixed in the preregistration §15 and unchanged in code; no
model-specific exception exists.

## 8. Unequal calibration budgets — CONFIRMED

`rules.CALIBRATION_FRAME_OFFSETS_BY_MODEL` at `11697e9`: both Qwens (0,1,2,3)
= 4 passes / 192 topics per frame; both Gemmas at the default (0,2) = 2
passes / 96. Sequence: `c8b70d3` (08-30 17:01, two passes after r5/r6) →
`bf136bb` (08-31 07:40, qwen3-4b to four after r8; r8 gemma-3n-e2b-it's f0
sat on the same 4-families/1-backup margin and was not raised) → `5e4791e`
(08-31 16:31, qwen3-4b-instruct-2507 to four) → r11 gemma-3n-e4b-it run at
two passes on 08-31/09-01 with f1 on the same margin, locked
LOCAL-ineligible. The raise made qwen3-4b eligible (r8: 0 supported frames;
r9: 2) and shrank 2507's f3 (4/1 → 3/0). r9 was a fresh root (all nine
stages regenerated). **Resolved:** `CALIBRATION_FRAME_OFFSETS = (0, 1, 2, 3)`
universal, committed at `957e5d7` before any new calibration; the Gemma
models are re-measured on fresh roots (`dci1v8-pilot-r12`, `-r13`) from a
clean worktree at that commit; eligibility is recomputed for every model on
the same basis by the confirmatory layer; the readiness audit refuses a
model whose pilot Gate 2 was not at the universal allocation.

## 9. Allocation conflict — CONFIRMED

`rules.CONFIRMATORY_FRAME_OFFSETS = (0, 1, 2)` (288) was inside the signed
rule table of every confirmatory manifest while `confirm/precision.py`'s
menu rule chose 384 and every freeze bound 384; the pilot coverage gate
projected condition 4 at 288 (and r9 at 96); `docs/V8_CONFIRMATORY.md`
carried "k ≤ 8" against `MAX_SPECTRUM_POINTS = 12`. **Resolved:** one value,
`CONFIRMATORY_BLOCKS_PER_FRAME = 384`, in rules, precision (`ALLOCATION`,
no menu), coverage, manifest, lock, freeze, preregistration §17, and
`test_every_active_source_of_the_allocation_agrees`.

## 10. Analysis narrowing — CONFIRMED

The component table is `analysis_components.md` beside this file. Omitted
without declaration at `11697e9`: L1 headroom gate, L1/L2 licensing, the Ξ
direction gate, F5/F6 and the §17.4 vacuity gate, F7, the projection
audit, the raw-coordinate secondary, the within-frame Δ_j heterogeneity
qualifier, the identification ledger, L4a, the L3c near-form guard, the
spectrum algebraic-form check and degenerate-replicate ceiling, the
prefreeze audit and final-report checks, §26. **Resolved:** implemented per
frame in `confirm/analysis.py` / `report.py` (preregistration §18.4–§18.6)
with synthetic tests; the remainder declared with reasons (§18.7, §20).

## 11. Adaptive history — CONFIRMED

Reconstructed from git, pilot records and confirm records; the dated table
is `adaptive_history.md` beside this file. Universal rule decisions:
Approach A (`ebf757d`, after r3), two passes (`c8b70d3`, after r5/r6), the
≥ 2-frame rule and 288 (`5e4791e`, after r8/r9), the confirmatory layer and
384 (`cd61e72`). Model-specific: the two Qwen raises and running e4b at
two. No composed outcome existed before the last design commit of that
design (first composed file 10:11:44Z, 2026-09-02; membership lock 16 s
earlier). Discrepancies found and corrected: six topped-up rungs, not seven
(records vs `CHANGES_SCIENTIFIC.md`); k ≤ 8 vs 12.

## 12. Reproducibility — CONFIRMED (12.1, 12.2); measured (12.3)

- 12.1 `confirm/membership.py:198` seeded the stability bootstrap with
  `hash(tree.model_key) & 0xFFFF` (process-salted). **Resolved:**
  `seeds.bootstrap_seed("operating_point_stability:frame<f>", model_key)`;
  `tests_v8dev/test_provenance_gate.py` proves byte-identical output across
  processes with different `PYTHONHASHSEED` and forbids a builtin `hash(`
  in the confirm package by AST.
- 12.2 neither `run/lifecycle.py::run_stage` nor
  `confirm/lifecycle.py::run_stage` called `gitinfo.assert_clean_worktree`;
  the CLI accepted an operator `--commit`. **Resolved:**
  `run/lifecycle.py::stage_provenance` on both mandatory paths (clean
  worktree, HEAD, operator commit must equal HEAD, fail closed, no bypass;
  synthetic namespaces record only); the environment record names the
  backend packages; the manifest binds the rule-table hash and the
  preregistration hash.
- 12.3 The stack (vLLM 0.15.1 ROCm, TP = 1, temperature 0.7) is not
  documented as bit-deterministic anywhere in the repository; the
  preregistration §8 promises reproducibility of the design and the
  analysis of stored rows, not of the sampled text. The measurement is
  `backend_determinism.md`.

## 13. Discrepancies between this prompt and the repository

- Finding 8 named `gemma-3n-e2b-it` as disadvantaged; it had two supported
  frames at two passes. The disadvantaged model was `gemma-3n-e4b-it`
  (one supported frame, f1 on the exact 4-families/1-backup margin the
  Qwen raise closed). Both are re-measured.
- Finding 2 described one cause; there were two (a zero fallback for
  references and a broader denominator for A).
- Finding 3: v7 formally exempted the spectrum from V_diff; the constraint
  entered indirectly.

## 14. Protected-outcome check (metadata only)

The only protected artifacts in the repository are the composed batches
under `dci1/evidence/dci1v8-confirm/evidence/dci1v8/{qwen3-4b,
gemma-3n-e2b-it}/CONFIRMATORY_GENERATION/backend_runs/` (13 and 12
`scored.jsonl` files, written 10:11–13:06Z on 2026-09-02, generation stopped
by the operator at 13:09Z; no `confirmatory_generation.json`,
`CONFIRMATORY_ANALYSIS` or `FINAL_REPORT` record exists). Every finding above
was verified from code, git history, pilot records (signed pre-freeze
stages), the superseded root's pre-freeze records, and development
reports; no file under a protected stage was opened during the audit
(the agents and tools that ran were instructed and checked not to), and the
successor root adopts no row from the superseded one. The decisions taken
(one allocation, universal calibration, stability status, runner-up arm,
provenance gate, analysis restoration) are each traceable to a code or
record fact listed above, none of which is an outcome.
