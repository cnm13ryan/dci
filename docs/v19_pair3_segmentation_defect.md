# Pair 3 target verifier: abbreviations are not protected under the frozen v19 policy

**Status:** code repaired; **Stage 2 re-audit outstanding**. Still blocks the v19
Stage 2 freeze until the re-audit runs. See "Repair" at the end of this document —
the rest of the record describes the defect as it stood and is kept as written.

**Discovered:** 13 Aug 2026, by `tests/unit/test_v19_inherited_verifier_audit.py::`
`test_the_disagreement_set_is_exactly_the_enumerated_one`, which is the section 11.3
differential audit and is doing exactly what it was written to do.

## The defect

`v19:p3.target.exact_sentence_count` decides F_A, the primary outcome. Under the
frozen v19 text policy it splits a sentence at every `.`, including the full stops
inside abbreviations and initials:

| answer | inherited count | frozen v19 count |
|---|---|---|
| `A. B. C. D. E.` | 1 | 5 |
| `Mr. Smith went to Washington. He stayed.` | 2 | 3 |
| `e.g. this is one. And another.` | 2 | 3 |

The inherited verifier is the corrected one. `src/dci/verifiers/rules.py` states the
consequence directly: the unprotected form "manufactured sentence-count OVERSHOOT
and turned compliant answers into violations". Under an exact-count constraint the
error is two-sided — the answer fails at its true `n` and passes at the inflated one
— so it does not average out and it is not conservative.

## Why it is present

The two changes were developed on parallel branches and neither was red alone:

* `cd5d1ba` (10 Aug) `fix(v19): protect abbreviations in Pair 3 sentence segmentation`
  — added `TITLE_ABBREVIATIONS`, `MEDIAL_ABBREVIATIONS` and `_ends_sentence` to
  `src/dci/verifiers/rules.py`, the **inherited** verifier.
* `08db4c2` (11 Aug) `feat(v19): adopt the canonical Pair 1 grammar and correct Pair
  2/3 (A1, A2)` — wrote `dci.v19.text.split_sentences`, the **corrected** verifier,
  from the pre-repair semantics.

Neither is an ancestor of the other (`git merge-base --is-ancestor` fails both ways).
They first met at `8809282`, the 13 Aug merge that is `main`'s tip, and the audit
test has been red since. A clean textual merge — the two commits touch different
files — with a semantic conflict underneath.

## Why it was not fixed when this was written

The frozen Stage 2 declaration pins the verifier's `implementation_hash`. Changing
`dci.v19.text.split_sentences` was tried and the freeze mechanism refused to load:

```
ValueError: verifiers.specification_bundle: {...} is not admissible for domain
'specification_bundle' - the frozen specification bundle does not match the
implemented verifiers' declared and executed hashes
```

Nine test modules error at collection. That is the freeze working, not breaking.

Repair therefore requires, in order:

1. port abbreviation protection into `dci.v19.text.split_sentences`;
2. add the corresponding entry to `dci.v19.text.INTENTIONAL_CORRECTIONS`;
3. re-freeze `verifiers.specification_bundle` in `src/dci/v19/stage2_frozen.json`
   with the new `implementation_hash` for `v19:p3.target.exact_sentence_count`;
4. regenerate `docs/v19_stage2_semantic_review_packets.json`, which pins both
   policy hashes;
5. **re-run the Stage 2 semantic review.** Section 10.6: "A demonstrated semantic or
   verifier defect requires repair and re-audit before freeze."

Steps 3–5 invalidate reviewer packets that have already been issued. Performing 3
and 4 without 5 would produce a repository that presents as frozen and reviewed
while its packets no longer match what any reviewer saw. A red audit test is the
better state of the two, and it is the state section 10.6 prescribes.

## Scope of the consequences

* **No published number is affected.** The exploratory and v15 lines run through
  `dci.verifiers.rules`, which carries the repair. `dci.v19` has produced no
  confirmatory data — Stage 2 is unfrozen pending the Tier-1 audit, which has also
  not been performed (`docs/v19_tier1_audit_handoff.md`).
* **The unified vLLM backend is unaffected.** It does not import `dci.v19`.
* Until repaired, `tests/unit/test_v19_inherited_verifier_audit.py` fails with six
  unenumerated `p3.target` disagreements, all of the shape above. They must **not**
  be added to `EXPECTED_DISAGREEMENTS`: that table declares intentional corrections,
  and these are the defect, not a correction of it.

## How the failure is carried while it is open

`test_the_disagreement_set_is_exactly_the_enumerated_one` is marked
`xfail(strict=True)` naming this document, **not** skipped and **not** silenced.
The reasoning:

* the defect stays visible — the marker states it, this record states it, and the
  test still runs and still reports;
* the six disagreements are still kept out of `EXPECTED_DISAGREEMENTS`, so the
  distinction between a declared correction and a defect is untouched;
* CI became meaningful only once it was green for the right reasons. A suite that
  is permanently red teaches its readers to stop looking, which is how this defect
  survived from `8809282` in the first place;
* `strict=True` means the marker cannot outlive the defect: the moment the repair
  lands the test XPASSes, which pytest reports as a failure, forcing whoever fixes
  it to remove the marker in the same change.

That marker has now been **removed**: the repair below makes the test pass,
and `strict=True` meant it could not have been left behind.
---

## Repair

Steps 1-4 of the sequence above are done. **Step 5 is not**, and it is the step
that governs whether this freeze may be presented as reviewed.

| step | state |
|---|---|
| 1. port abbreviation protection into `dci.v19.text.split_sentences` | done |
| 2. declare the correction | done, as a hashed policy field rather than an `INTENTIONAL_CORRECTIONS` entry — see below |
| 3. re-freeze `verifiers.specification_bundle` | done, via `tools/refreeze_stage2.py` |
| 4. regenerate `docs/v19_stage2_semantic_review_packets.json` | done, via `tools/generate_review_packets.py` |
| 5. **re-run the Stage 2 semantic review** | **OUTSTANDING** |

Because 3 and 4 are done and 5 is not, the caution this document already stated
now applies in the other direction: the packets on disk are no longer the packets
any reviewer saw. Nothing may claim Stage 2 review has been satisfied until the
review is re-run against the current bundle. The three packet ids changed.

**Deviation from step 2 as written.** The correction is recorded as a new
`TextPolicy` field, `sentence_abbreviation_guard`, naming
`dci.verifiers.rules.ends_sentence`, rather than as an `INTENTIONAL_CORRECTIONS`
entry. The field is in `TextPolicy.state()` and therefore inside the Pair 3
specification hash, so the choice of guard is auditable from the object and a
future policy wanting the raw regex split has to declare it. The
`INTENTIONAL_CORRECTIONS` table continues to describe amendment A2's *verdict*
corrections against the inherited verifiers; this is a change to the frozen
policy itself, which is what the hash exists to record.

**Why the repair was made rather than deferred further.** The defect was
re-examined from first principles against the blinded human audit in
`exploratory/verifier_audit/` — human sentence counts recorded against real study
outputs with arm, condition and every verdict withheld. Over the 65 labelled
responses the inherited segmenter agrees 65/65 and the frozen v19 policy 46/65,
all 19 disagreements being over-counts. On the 43 labelled cases carrying a target
`n`, six (14%) have their F_A verdict flipped, and in every one the unguarded
policy is wrong against the human verdict — a false FAIL on a compliant answer.
The guard's own documented cost, a sentence ending in a bare capital letter read
as an initial, occurs 0 times in the 240-response corpus.

**Regression cover.** `tests/unit/test_segmentation_contract.py` states the
contract at the seam and runs the existing boundary banks through *both* layers.
All 39 prior boundary tests called only `rules.split_sentences`, and that
one-sidedness is why the two implementations drifted apart in the first place.

**Port to main (2026-09-13).** The repair above was merged into
`chore/repo-hardening-and-research-state` (PR #22) after that branch had already
been merged into `main` (PR #21). So `main` kept this defect, as a strict xfail,
until it was ported by cherry-picking the same four commits. The port changed the
scope, evidence and outstanding work as follows.

- **Two corrections to the scope stated above.**
  - The segmentation also feeds `p3.focal.increasing_lengths`, so both Pair 3
    verifiers change.
  - The Pair 1 and Pair 2 spec hashes move with the text-policy state; their
    behaviour does not.
- **Differential over 118,612 texts** (the audit corpus, cross-model rows and a
  v8.1 sample):
  - v19 changes on 253 texts;
  - the inherited splitter and the Pair 1 and Pair 2 verifiers are unchanged on
    all of them;
  - v19 now matches the inherited count on all but one text.
- **Residual.** That one text contains `H₂O.`. NFKC makes it `H2O.`, whose trailing
  `O.` the guard reads as an initial, so one boundary is lost. This is the guard's
  documented initial cost, realised once in 118,612 texts. It is inherited from
  `dci.verifiers.rules`, and changing it is a separate decision.
- **Step 5 above is still outstanding.** See `CHANGES_SCIENTIFIC.md`, 2026-09-13
  (v19).
