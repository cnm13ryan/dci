# Pair 3 target verifier: abbreviations are not protected under the frozen v19 policy

**Status:** open. Blocks the v19 Stage 2 freeze. Not repairable without a re-freeze
and a re-audit, which is why this is a record and not a patch.

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

## Why it is not fixed here

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
