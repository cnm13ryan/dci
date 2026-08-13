# v19 Stage 2 implementation-gap audit

Stage 2 is section 14.2: "Implement/reconcile all deterministic verifiers,
structured feature encodings, Z3 conjunctions where applicable, automatic witness
generation, verifier conjunction checks, semantic-review triggers,
boundary/property tests, causal field roles, completeness ledger, and provenance.
Pair 1 bullet-count/transitive-order support must be built; Pair 2 and Pair 3
existing verifier code may be reused only after hash/semantic audit. Freeze the
exact inherited binomial reliability implementation or resolve it as a pre-freeze
output before dependent reliability audits."

This audit was written before implementation, against
`DCI_Pilot_Preregistration_v19_REVISED_FINAL.tex`
(SHA-256 `3868172470a25115fd310efd016c163ab0fc0f660435c9620f41d27954dc1bf0`)
and the merged PR #12 tree at `6ebe324`.

Status vocabulary, from strongest to weakest:

| Status | Meaning |
|---|---|
| `ENFORCED_AND_HASHED` | produced, enforced at a boundary, and bound to a scientific hash |
| `ENFORCED` | a production caller fails closed on it |
| `SEMANTICALLY_VERIFIED` | implemented and audited against the v19 text |
| `IMPLEMENTED_UNAUDITED` | code exists; its v19 semantics have not been checked |
| `PRODUCED_NOT_ENFORCED` | an artifact exists but nothing gates on it |
| `REPRESENTED_NOT_PRODUCED` | the registry names the slot; no procedure fills it |
| `DECLARED_ONLY` | named in prose or a docstring; no representation |
| `MISSING` | absent |

---

## A. Requirement table

| # | Requirement | Governing section | Existing code | Status before this work | Required action | Scientific risk if wrong |
|---|---|---|---|---|---|---|
| 1 | Pair 1 exact-bullet-count verifier | §4.1 table row 1; §4.2; §10.9; §14.2 | none | `MISSING` (`pairs.PAIR_1.target.verifier.callable_name == ""`) | build | the primary outcome `F_A` for one third of the design is unmeasurable |
| 2 | Pair 1 transitive-order verifier | §4.1; §4.2; §14.2 | none | `MISSING` | build | focal compliance for Pair 1 is unmeasurable, so the manipulation cannot be shown to have landed |
| 3 | Pair 1 shared structural parser, explicit | §4.2 ("both the count and ordering verifiers may parse the same list representation") | none | `MISSING` | build as a separate, inspectable stage | shared-parser failure is recorded as genuine interference — the exact confound §4.2 names |
| 4 | Pair 2 target verifier (mandatory words) | §4.1; §4.3 | `rules.v_require_word_set` | `IMPLEMENTED_UNAUDITED` | audit, adapt, hash | see D-2 below: an accented mandatory word is unsatisfiable |
| 5 | Pair 2 focal verifier (all words unique) | §4.1; §4.3 | `rules.v_unique_words` | `IMPLEMENTED_UNAUDITED` | audit, adapt, hash | see D-1: a zero-width space defeats uniqueness |
| 6 | Pair 3 target verifier (exact sentence count) | §4.1; §4.4 | `rules.v_exact_sentence_count` | `IMPLEMENTED_UNAUDITED` | audit, adapt, hash | see D-3: a bullet list scores as N sentences |
| 7 | Pair 3 focal verifier (increasing lengths) | §4.1; §4.4 | `rules.v_increasing_lengths` | `IMPLEMENTED_UNAUDITED` | audit, adapt, hash | the length unit is ASCII word tokens (D-2) |
| 8 | Verifier specification hashes | §14.2; Appendix I ("invariant … verifier … hashes"); Appendix J | none | `MISSING` | add | a verifier whose semantics change mid-study is undetectable |
| 9 | Common verifier result representation | §10.1 | `rules.VerificationResult` | `IMPLEMENTED_UNAUDITED` | adapt | see D-4: the inherited status merges three orthogonal v19 fields |
| 10 | Structured constraint encoding | §8.6 ("machine-expressible clauses"); §14.2 | `constraints/spec.py` (`ConstraintSpec`, untyped `params`) | `IMPLEMENTED_UNAUDITED` | build a canonical typed encoding | an encoding that cannot represent the clause silently narrows what was proved |
| 11 | Z3 encoding | §8.6 | none | `MISSING` (z3 was not even a dependency) | build | no abstract satisfiability evidence exists at all |
| 12 | Solver invocation with `sat`/`unsat`/`unknown` separation | §8.6 | none | `MISSING` | build, fail closed on `unsat`/`unknown`/timeout/absent output | `unknown` read as `sat` admits impossible compositions into the bank |
| 13 | Automatic witness generation | §8.6; §14.10 | `satisfiability.corpus_witness` (searches a corpus; does not construct) | `PRODUCED_NOT_ENFORCED` | build a deterministic constructor | solver `sat` alone would become the acceptance criterion, which §8.6 forbids |
| 14 | All-verifier conjunction validation | §8.6 step (2); §14.2 | none | `MISSING` | build, completeness-first | a conjunction over the *available* subset certifies less than it claims |
| 15 | Semantic-review trigger | §8.6 | none | `MISSING` | build | the coding model becomes the scientific reviewer |
| 16 | Semantic-review artifact schema | §8.6 ("two independent reviews, third adjudicates") | `pools.semantic_duplicate_review` (a different review, §8.7) | `MISSING` for §8.6 | build | an unresolved disagreement must fail certification, not default to pass |
| 17 | Boundary/property test harness | §8.7; §10.6 | scattered per-verifier unit tests | `IMPLEMENTED_UNAUDITED` | build the v19 harness | untested parser edges are exactly where coupling hides |
| 18 | Mutation/replay harness, ≥1,000 per template | §8.7 | none | `REPRESENTED_NOT_PRODUCED` (`verifiers.boundary_mutations`) | build | the count can be met with whitespace noise that tests nothing |
| 19 | Inherited exact binomial reliability procedure | §10.4; §14.2 | `measurement/audit_sizing.py` (Wilson) | `IMPLEMENTED_UNAUDITED` → **blocked**, see B-1 | recover, then *stop* | a normal-approximation ceiling certified as exact overstates verifier reliability |
| 20 | Stage 2 registry-resolution path | §14.2; §1.3 | `artifacts.VERIFIER_SLOTS` (4 slots) | `REPRESENTED_NOT_PRODUCED` | extend and wire | code existing is not the same as an artifact certified |
| 21 | Stage 2 completeness/provenance artifact | §8.6 ("archive the exact composition, structured encoding, solver input/output, candidate/winning witness, verifier results, semantic reviews … hashes, and construction commit"); Appendix J | none | `MISSING` | build | certification that cannot be re-derived is not evidence |
| 22 | Stage 2 readiness gate | §14.2; §14 ordering | `registry.STAGE_GATES["stage_2_verifiers"]` requires one slot | `ENFORCED` but under-specified | extend | Stage 2 could report READY with no Pair 1 verifier in existence |
| 23 | Causal field roles | §11.8; §14.2 | `v19/field_roles.py` (PR #12) | `ENFORCED_AND_HASHED` | reuse; classify verifier evidence as diagnostic | verifier diagnostics becoming primary covariates changes the estimand |

Requirement 23 is the one item §14.2 lists that PR #12 already delivered. It is
listed so the table matches section 14.2's enumeration exactly rather than
quietly dropping a satisfied clause.

---

## B. Blockers found while auditing

### B-1. The inherited reliability interval is Wilson, not an exact binomial interval

§10.4: "The 5% Tier-1 ceiling, 20% Tier-2 per-stratum ceiling, pooled 5% system
certificate, and inherited 73-per-truth-class Tier-1 planning count are
preserved. The exact two-sided binomial interval implementation used by the
inherited gate must be recovered from the authoritative code/specification and
frozen at Stage 2; if it is not uniquely recoverable, its choice is a \PFD within
register item D9 rather than an implementer decision."

Recovery succeeds and is unambiguous. The only interval in the inherited code is
`measurement.audit_sizing.wilson_interval`, and it is the *default* bound of
`required_cases_for_ceiling`, which the inherited gate inverts. Running that
inversion reproduces v19's preserved planning count exactly:

```
required_cases_for_ceiling(0.05, 0.95, wilson_interval) == 73
wilson_interval(0, 73, 0.95)[1] == 0.049992…   ≤ 0.05
wilson_interval(0, 72, 0.95)[1] == 0.050651…   > 0.05
```

So "73" is not an inherited convention of unknown origin: it is the Wilson score
interval inverted at a 5% ceiling and 95% confidence. The Clopper–Pearson
zero-error upper bound reaches 0.05 at **n = 72**, not 73.

§10.4 confirms this a second time without meaning to. It states that six
target/focal units at 73 per truth class "implies 876 adjudicated labels", and
73 × 6 × 2 = 876 exactly. Under Clopper–Pearson the same arithmetic gives
72 × 6 × 2 = 864. Both preserved numbers in that paragraph are Wilson's.

The conflict is therefore in the preregistration's own sentence. The interval is
uniquely recoverable, and what it recovers to is a **normal-approximation**
interval — the very family §6.2 rejects, citing Brown, Cai and DasGupta, when it
requires "the exact two-sided 95% Clopper–Pearson interval" for parameter
calibration. Preserving 73 and calling the implementation an "exact two-sided
binomial interval" cannot both hold.

Two consistent resolutions exist, and both are investigator decisions:

1. **Freeze Wilson.** Preserves the inherited 73 that §10.4 says is preserved.
   Requires accepting that the Tier-1 reliability ceiling is enforced with a
   normal-approximation interval while parameter calibration uses an exact one.
2. **Adopt Clopper–Pearson.** Satisfies "exact two-sided binomial" and matches
   §6.2's stated rationale. Changes the preserved Tier-1 planning count from 73
   to 72, contradicting §10.4's "preserved".

`verifiers.binomial_interval_implementation` is therefore left unresolved and
re-declared `PENDING_DECISION` (it was `PENDING_EMPIRICAL`, which would have
implied a procedure was merely unrun). Both interval implementations and the
inversion are implemented and tested so the decision can be made on arithmetic
rather than recollection; neither is selected in code.

Secondary defect in the same sentence: §10.4 assigns this to "register item D9",
but D9 in the §17 register is "Construction bootstrap — complete `U_i` clusters;
exactly 10,000 replicates". No register row covers the reliability interval. The
decision needs a register row before Stage 14 can freeze it.

### B-2. v19 fixes no Pair 1 list-parsing semantics

Every occurrence of "bullet" or "transitive" in the preregistration is at lines
357, 365, 367, 394, 773, 1336, 1447 and 1547. Together they fix the two
statements — "Produce exactly $N$ bullet-list items" and "Place the items in the
correct transitive order" — the family labels, the coupling risk, and the fact
that the verifiers must be built. They fix none of the following, each of which
changes verdicts:

| Open question | Why it is scientifically material |
|---|---|
| which markers open a list item | `+ item` and `1. item` either count or do not |
| whether numbered lists are bullet-list items | changes the observed count on any enumerated answer |
| whether nested items count individually | changes the count on any indented answer |
| whether a non-marker line continues the previous item | changes the count on any wrapped answer |
| whether a marker with no content is an item | decides the verdict on trailing `- ` |
| leading/trailing prose | a chat preamble either is an item or is not |
| Unicode normalisation before parsing | decides whether `•` variants and combining marks are markers |
| how an item is matched to a declared entity | the ordering verifier cannot run without this |
| what `ordering_depth` (declared in `pairs.PAIR_1`) ranges over | it is a calibrated parameter with no stated meaning |

The inherited code contains one recoverable candidate: `rules.LIST_MARKER`,
`^\s*(?:[-*•‣▪]|\(?\d{1,2}[.)])\s+`. It is already load-bearing — `split_sentences`
strips it — so reusing it keeps Pair 1 and Pair 3 on one frozen segmentation
rather than two. It answers the marker question and, incidentally, three others.
It answers none of the remaining five.

Resolution taken: the parser is implemented against an **explicit, hashable
`ListPolicy`**, with no default anywhere, so no call site can drift. The candidate
policy that reproduces the inherited regex is provided and named as a candidate.
`verifiers.p1.list_policy` is declared `PENDING_DECISION` and Pair 1
certification fails closed on it. This is not a hidden default: the code cannot
be invoked without naming a policy, and each undetermined field is asserted to
change the policy hash, so answering one differently is visible in the freeze.

---

## C. Defects found in the inherited verifiers

Each was reproduced against the merged tree before any change.

**D-1. A zero-width space defeats Pair 2's uniqueness rule.**
`WORD_PATTERN = [A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*` is ASCII-only and
`normalize_text` collapses only `\s`, which excludes U+200B.

```
v_unique_words("wo​rd word")  ->  full, binary_pass=1
    tokens ['wo', 'rd', 'word'] — three distinct tokens from two identical words
v_unique_words("аpple apple")      ->  full, binary_pass=1     (Cyrillic а)
    tokens ['pple', 'apple']
```

The focal constraint of Pair 2 can be satisfied while repeating a word. §10.6
names "zero-width characters" and "homoglyphs" as required audit material, so
this is a defect the protocol anticipates rather than an out-of-scope input.

**D-2. An accented mandatory word can never be satisfied.**

```
v_require_word_set("Café", ("café",))    ->  violation      (tokens ['Caf'])
v_require_word_set("naïve", ("naive",))  ->  violation      (tokens ['na','ve'])
```

Under §4.3 a parameter realisation that makes the composition impossible is
"outside the DCI estimand". An accented mandatory word is such a realisation, so
either the sampled word set is restricted to ASCII or the tokeniser changes. The
same ASCII restriction is the length unit for Pair 3's focal rule.

**D-3. A bullet list scores as exactly N sentences.**
`split_sentences` strips list markers and treats each line as a sentence:

```
"- alpha\n- beta gamma\n- delta epsilon zeta"
  split_sentences -> ['alpha', 'beta gamma', 'delta epsilon zeta']
  v_exact_sentence_count(..., 3) -> full, pass=1
  v_increasing_lengths(...)      -> full, pass=1
```

This is the inherited frozen segmentation, and §4.4 defers to "the frozen
sentence segmentation", so it is reported rather than changed. Two consequences
must be recorded: Pair 3's target can be satisfied by an answer containing no
sentence-final punctuation at all, and Pair 1's parser shares this span, so
Pair 1 and Pair 3 are coupled through one regex. §4.4 already names shared
segmentation as Pair 3's principal measurement risk.

**D-4. The inherited status merges three orthogonal v19 fields.**
`OutcomeStatus = full | partial | violation | unscorable` carries both §10.1's
secondary compliance field (`FULL`, `PARTIAL`, `VIOLATION`) and part of its
generation state (`unscorable`). §10.1 requires the constraint verdict, the
generation state and the secondary compliance field to be recorded separately,
and the user directive adds that a verifier crash must never become a behavioural
`FAIL`. The inherited binary verdict is already correct — `_unscorable` returns
`binary_pass=0`, which matches §10.1's "an exact requirement that cannot be
demonstrated as satisfied receives `FAIL`" — so the repair is representational
and differential agreement on the binary verdict is preservable.

**D-5. Numbered items are capped at two digits.**
`\d{1,2}` means `100. item` is not a list marker. Material only if a calibrated
`n_items` can exceed 99; recorded so the Stage 5 grid cannot silently exceed the
parser.

---

## D. What this audit does not cover

Out of scope by the task definition: Stage 2A runtime qualification, GPU
certification, model inference, the reasoning controller, checkpoint
qualification, reference selection, parameter calibration, the exact-$\epsilon$
decision, background proposal draws, budget selection, and all Stage 4–17
execution machinery. The verifier-coupling *calibration* of §7.7 (the 2,000-output
probe bank) is Stage 6; only the Stage 2 structural coupling tests are built here.
