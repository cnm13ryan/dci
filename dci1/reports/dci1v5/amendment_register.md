# DCI-1 v5 — the §32 amendment register

Append-only. One entry per amendment, carrying the amendment text, its timing
relative to every affected artifact, what it supersedes, and what it leaves
untouched. §32 requires exactly those four things and this file is the single
register it names.

An entry is never edited after the artifact it affects exists. A correction to
an entry is a new entry.

---

## A1 — pre-data engineering amendment (2026-08-23)

**Author.** Researcher, on the Phase-0 pre-execution report of 2026-08-23.

**Timing, relative to every affected artifact.**

| Artifact | State when the amendment was adopted |
|---|---|
| §34 decisions D0–D18 | all closed, none reopened |
| U2, P1 | resolved (A2 / confirmed), neither reopened |
| Registration manifest `2960a1fc…` | signed, verified, **superseded by this amendment** |
| Stage 1 `PROTOCOL_REGISTERED` | run for `gemma-3n-e2b-it` only; record retained, superseded |
| Stages 2–18, all models | **never run** |
| v5 model responses | **none exist**, on any model, at any stage |
| v5 calibration measurements | **none exist** |
| Gate 2.5 / §13 components | never begun, so §32's clause 3 is not engaged |
| v4r4 evidence | untouched, and untouched by this amendment |

It is therefore a **pre-data** amendment under §32's first paragraph:
prospective by definition, because no confirmatory data exist under this
version and none exist under the superseded registration either.

**Amendment text.** Three defects were found in the pre-execution sweep. None
is a scientific quantity; each made the registered lifecycle unexecutable or
its provenance untrue.

1. **V5-E1 — registration is study-level, its record is per model.**
   `run/registration_run.registration_payload` called
   `manifest.sign_registration` on every invocation, which writes the
   study-level manifest under write-once semantics, while
   `engine/transitions.assert_predecessor_passed` requires the replication's
   own stage-1 record. The second replication therefore raised
   `IntegrityError` and three of the four registered models had no legal path
   into `QUALIFIED`. **Amended:** `manifest.ensure_registration` signs on the
   first call and thereafter verifies the signature, rebuilds the manifest
   from the running code, compares by hash, and requires the same producing
   commit. A replication registering at another commit, or against a manifest
   its own code no longer reproduces, is refused.

2. **V5-E2 — the generative seam was not reachable and not guarded.**
   `GATE_0_APPARATUS`, `REGIME_SCREEN`, `GATE_2_FOCAL_CALIBRATION` and
   `GATE_4_COMPOSED_HEADROOM` each read `generate = generate or
   fake_backend(...)`. That substitutes unconditionally and admits no
   override, so `run/execute.run_backend` — the pinned backend — was reachable
   only from `CONFIRMATORY_GENERATION`, and `run/cli.py`, the only production
   entry point, passes no generator. The documented way to run Gate 0 would
   have signed fabricated text into the registered evidence tree, and no
   downstream rule refuses a synthetic row in the registered namespace.
   **Amended:** `execute.resolve_generate` decides. In the registered
   namespace `generate` must be absent and resolves to the pinned backend, and
   an injected callable is refused; the deterministic stand-in is constructed
   only in the synthetic namespace. This is the guard `assert_synthetic_only`
   already applied to `topic_limit` and `block_limit`, extended to the larger
   substitution it had been left off.

3. **V5-E3 — a row's provenance recorded the call shape.**
   `run/execute.py` stamped `"synthetic": generate is not None`, so every row
   of the four runners above was synthetic by definition and a real backend
   injected into one of them would still have been stamped synthetic.
   **Amended:** the flag is taken from the generator's own provenance, and
   `fake_backend` stamps each raw row so the flag survives a resumed run.
   Separately, `CLASSIFICATION` had not moved at adoption and still read
   `DCI-1 PROTOCOL v5 (DRAFTED, NOT ADOPTED, NOT FROZEN)`; it is now
   `DCI-1 PROTOCOL v5 (ADOPTED AND REGISTERED, NOT FROZEN)`, with the old
   string retained in `SUPERSEDED_CLASSIFICATIONS` because records under the
   superseded registration carry it.

**What it supersedes.** Registration manifest
`2960a1fc44f036abd4729f7628095475018672adfac609bb2244a8763ba00ded`, producing
commit `f8956465fb1525c738ba7f79b49698141b3c1f82`, and the `gemma-3n-e2b-it`
stage-1 record signed under it. Both are **retained, not deleted**:
`dci1/evidence/dci1v5/registration/superseded/2960a1fc…/` holds the manifest
and a supersession record, and the stage record is retained under the model's
own `superseded/2960a1fc…/`. `engine/paths.is_superseded` excludes retained
files from every current pool while the durability audit still counts them.
The replacement manifest names the superseded one in its `supersedes` field.

**The replacement.** Manifest
`70608e5d5880c6ed2b8bbea1379b47061f60ea3f0705c374d0df581bc39bda2c`, producing
commit `5e35ca687c52af86640f167fe145c20d52af36a9`, signed 2026-08-23 with a
stage-1 record for **all four** registered replications — which is the first
time that has been possible.

**What it leaves untouched.** Everything the study measures or decides:

- every §34 closure and its evidence, D17's floor spec included;
- U2 = A2 and P1 = confirmed;
- the five arms, 56 cells, 384 blocks, $M = 8$, four models and the
  1,135,104-generation budget;
- the eight Tier-1 markers, their population hash and their four accepted
  limitations;
- both calibration topic banks and the split identity;
- the candidate library, every severity ladder and every reserve;
- every threshold, estimand, multiplicity family, claim level, identification
  status and terminal status;
- every prompt, wording, verifier, seed, cap and decoding policy;
- §13's reference-selection rules in full;
- v4r4's evidence.

Verified rather than asserted: the replacement manifest was diffed against the
superseded one, leaf by leaf. **Seven fields differ and every other binding is
byte-identical.**

| Field | Why it moved |
|---|---|
| `classification` | V5-E3 — the label that had not moved at adoption |
| `revision_changes.classification` | the same string, echoed by `revision_record()` |
| `producing_commit` | `f895646` → `5e35ca6`, the amendment commit |
| `protocol_hash` | §32 of the preregistration now names this register; a documentation edit, no scientific text changed |
| `supersedes` | new; names `2960a1fc…` |
| `adoption` | records the amendment's provenance beside the original approval |
| `manifest_hash` | consequent on the six above |

Byte-identical across the amendment: the models and their revisions, the design
and budget, every threshold including D17's floor block, the decision record
and its hash, the open-item resolutions, the marker population and its hash,
both topic-bank hashes and the split identity, the candidate library, the
estimands, the multiplicity families, the claim ladder, the masking
specification, the seeds, the selection rules, the measurement basis, the reuse
ledger and the red-team block.

**This amendment does not weaken a criterion to make a gate pass.** No gate had
run. It adds refusals — three of them — and removes none.
