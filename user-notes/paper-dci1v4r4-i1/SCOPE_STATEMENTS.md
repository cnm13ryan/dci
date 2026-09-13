# SCOPE_STATEMENTS

Sentences that must appear in the paper verbatim or near-verbatim, with their
source and the place they belong. These are not stylistic preferences: three of
the four are registered obligations that travel with the records, and the
fourth is a provenance boundary the paper would otherwise misstate.

---

## 1. §10.5's scope sentence — permanent, attaches to every claim

**Verbatim:**

> the outcomes are verifier-defined and support no claim about compliance as an
> independent human would judge it

**Source.** `paper/v4r4_bundle/tier1_protocol_and_gates/reports/gate1_decision.json`
→ `scope_sentence`; identical string at
`dci1v4r4.protocol.constants.SCOPE_SENTENCE`; carried on both analysis records
at `UA:<model>` → `payload.scope_sentence` and on
`final_results.json` → `analysed.<model>.scope_sentence`.

**Why it is permanent.** The measurement basis is
`deterministic_measurement_validated` and never `human_validated`
[`gate1_decision.json` → `measurement_basis`]. The same record states the
consequence:

> the basis is not human_validated, so §10.5's scope sentence attaches to every
> analysis record, every claim at every rung and the final report, and no later
> stage may remove it

[`gate1_decision.json` → `scope_sentence_is_permanent`]

**Where it belongs in the paper.**

| location | treatment |
|---|---|
| Abstract | near-verbatim, one clause: the outcomes are verifier-defined |
| §1 Introduction | verbatim, at the **first statement of either claim**. In the revised outline ¶3 is C2 and ¶4 is C1, so it lands in ¶3. It applies to **both** claims: C2's admission verdicts, ι values and equivalence diagnostics are all verifier-derived, so the scope sentence is not C1-only |
| §5.0 opening | verbatim |
| §6.1 Limitations, item (ii) | verbatim, with the `measurement_basis` field named |
| Every table caption reporting an estimate (Table 1) | near-verbatim, one clause |
| Appendix G | verbatim, with the field path |

**Not optional.** A paper that reports these estimates without this sentence
misrepresents the measurement basis of every one of them.

---

## 2. §11.4's position caveat — per L1 statement

**The registered rule, verbatim** [`user-notes/DCI1_preregistration_v4r3.md`
lines 1923–1935, carried into v4r4 by reference]:

> A solo cell states its single constraint in position one. $D(c \leftarrow g)$
> is therefore position-matched to its baseline only in the configuration where
> $c$ is stated first; in the other configuration it confounds added load with a
> change of position. […] every emitted L1 statement names the position of the
> outcome constraint; the L1 claim in the position-shifted configuration is
> stated as "composition and position change together"

**The fixed phrase** [`dci1v4r4.protocol.constants.POSITION_WORDING`]:

> composition and position change together

**How it applies to each emitted L1, one row per statement.** `POSITION_CONFOUNDED`
is attached by the analysis to every `outcome_second` statement
[`UA:<model>` → `payload.claims.outcome_second.position_status`].

| checkpoint run | configuration | emitted L1 member | position of the outcome constraint | required wording |
|---|---|---|---|---|
| `gemma-3n-e4b-it` | `outcome_first` | `D(A<-B)` | *A* stated first — position-matched | name the position; no confound clause |
| `gemma-3n-e4b-it` | `outcome_second` | `D(B<-A)` | *B* stated second — position-shifted | name the position **and** state *composition and position change together* |
| `qwen3-4b` | `outcome_first` | `D(A<-B)` | *A* stated first — position-matched | name the position; no confound clause |
| `qwen3-4b` | `outcome_second` | `D(A<-B)` | outcome stated second — position-shifted | name the position **and** state *composition and position change together* |

**Where it belongs.** §5.4, on each emitted statement; Table 1, as a column or
a footnote marking the two `outcome_second` rows; §6.1 Limitations item (iv).

**Consequence the paper must not lose.** §11.4 says the position-clean
quantities are `Delta_R` and `delta_difficulty` — *"which are position-clean,
are the quantities that carry the companion-identity claim"*. Both are
`NOT_IDENTIFIED`. So the paper has no position-clean quantity at all, and §5.4
says so.

---

## 3. §28.1's *Configuration dependence* — the registered reading of L4

**Verbatim** [`final_results.json` →
`analysed.gemma-3n-e4b-it.l4_registered_reading.registered_reading`]:

> Configuration dependence (§28.1): the quantity is configuration-dependent; the
> table is reported and no pooled scalar is quoted

**The field it replaces**, quoted verbatim so the reader sees both
[`UA:gemma-3n-e4b-it` → `payload.claims.L4.statement`, record hash
`1dbebbe2a02a1eed…`]:

> the same classification holds in every registered configuration: ['L1']

**The three fields that invalidate it** [`final_results.json` →
`analysed.gemma-3n-e4b-it.l4_registered_reading`]:

- `licensed_by_the_registered_rule: false`
- `agrees_with_the_emitted_field: false`
- `members_replicating: []`, and
  `members_differing_across_configurations: ["F1:D(A<-B)", "F1:D(B<-A)"]`

**The recorded defect**, verbatim from the same field:

> analysis.claims.emit_l4 compares the set of levels reached, not the level each
> named member reached. Where the members that reach a level swap places across
> configurations, the sets match and the emitted L4 says the result replicates
> when §3.2's per-member gate says it is configuration-dependent

**`qwen3-4b` is different and the paper must say so.** There,
`licensed_by_the_registered_rule: true`, `agrees_with_the_emitted_field: true`,
`defect: null`, `members_replicating: ["F1:D(A<-B)"]`. **One registered L4 result
therefore survives.** The paper makes no *study-wide* replication claim; it must
not say "every level above L1 is withheld", which is false.

**Where it belongs.** §5.5 (what is withheld) and §6.1 Limitations, which is
where the L4 episode moved when §6 was cut; every place the word "replicate"
would otherwise appear. **Both
artifacts must be cited wherever L4 is discussed** — `final_results.json` for
the registered reading and `UNMASKED_ANALYSIS.signed_record.json` for the
emitted field.

---

## 4. The `lifecycle_integrity.json` coverage boundary

**The sentence the paper must carry, drafted:**

> `lifecycle_integrity.json` reports `passed: true` with an empty `problems`
> list, and it covers stage records through `GATE_4_COMPOSED_HEADROOM` only; the
> freeze, confirmatory-generation, masked, unmask and unmasked records are
> verified individually, by content hash and HMAC signature under the study
> signing key, and by the evidence manifest.

**Why this exact boundary.** The report's `furthest_stage` for
`gemma-3n-e4b-it` is `GATE_4_COMPOSED_HEADROOM` and its recorded `head` is
`bbe5b8f24fd3974a507ea509a24accb9176e2216`, so it predates Gate 5
[`paper/v4r4_bundle/tier1_protocol_and_gates/reports/lifecycle_integrity.json`
→ `models.gemma-3n-e4b-it.furthest_stage`, `working_tree.head`].

**What does cover the later records.** All 24 signed records bundled for this
paper verify by content hash and HMAC-SHA256 signature under
`dci1/evidence/dci1v4r4/keys/signing.key` via the study's own
`dci1v4.engine.signing.verify_signed`, which has no hash-only variant; and
`tools/v4r4_evidence_manifest.py --verify` returns `"status": "OK"` with zero
missing and zero changed files
[`paper/v4r4_bundle/MANIFEST.md` §4, checks V1–V3].

**Where it belongs.** Appendix G (Reproducibility and artifact statement), and
one sentence in §6.1 Limitations item (vii). **Do not write** "an integrity
report certifies the lifecycle" without the boundary — that sentence is false
as stated.

---

## 5. Two further registered sentences the body will need

Recorded here so they are not paraphrased into something weaker.

**The non-identification note** [`final_results.json` → `not_identified_note`],
belongs in §4.10 and in the caption of Figure 1's right panel:

> these are registered quantities this design does not identify. They are not
> null results, not zero, and not missing by accident, and no post-hoc estimate
> of them exists

**The terminal sentence** [`TERM:<model>` → `terminal_sentence`;
`dci1v4r4.protocol.constants.TERMINAL_SENTENCE`], belongs wherever
`gemma-3n-e2b-it` or `qwen3-4b-instruct-2507` is discussed:

> a terminal pre-confirmatory status carries no evidence about the effect

**And the class sentence** [`dci1v4r4.protocol.constants.CLASS_SENTENCE`;
carried on every emitted statement at `UA:<model>` →
`payload.claims.<cfg>.statements[*].class_sentence`], which the paper carries
even though no L3 statement is emitted, because it describes the pool:

> the reference pool is budget class and A is production class, so this excess
> is relative to budget-class companions matched on instructed compliance and is
> not an excess relative to companions of A's own structural class


---

## 6. What the signatures establish, and what they do not

**The sentence the paper must carry, drafted:**

> Every stage record is signed with HMAC-SHA256 under a study signing key created
> at registration and held by the researcher. That establishes integrity **only
> against parties who do not hold the key**: a reader without the key cannot alter
> a record undetected, and one key signed the whole chain. It establishes nothing
> against the key-holder, so it does **not** establish authorship, and it does
> **not** establish that a record existed before unmasking — a key-holder can
> generate a valid HMAC over any content at any time.

**Verified state of the anchors, at commit `3d57ad2` and re-checked at `3c14d66`;
no v4r4 artifact changed between them.**

- The key is at `dci1/evidence/dci1v4r4/keys/signing.key`, 64 bytes, mode 0600.
  It is **gitignored and untracked** (`git ls-files dci1/evidence/dci1v4r4/keys/`
  returns nothing), so it is not distributed with the repository. It is also not
  independently escrowed.
- The freeze commit `450a049` is in the local git history but **on no remote
  ref** (`git branch -r --contains 450a049` returns nothing), and `HEAD` is 115
  commits ahead of `origin/main`. **The v4r4 chain currently has no external
  immutable anchor.**

**What this means for the paper.** The temporal ordering — rules fixed before
data, analysis sealed before labels were visible — rests on local git history
plus a locally-held symmetric key. That is adequate for a reader who trusts the
researcher and wants to check internal consistency; it is not a cryptographic
proof of precedence to a reader who does not.

**Where it belongs.** Appendix G, as a paragraph of its own, and one clause in
§6.1. **Do not write** that the signatures prove the analysis was fixed in
advance.

**The cheap remedy, and its exact limit.** Pushing the freeze commit to the
remote, or publishing a timestamped digest of the freeze and masked records,
makes the **current** state externally checkable from that moment on: a third
party can then verify that the content has not changed since publication. It
**cannot retroactively establish that those records existed before unmasking** —
publishing today anchors today, not the freeze date. So the remedy is worth
doing and does not upgrade the temporal claim; the sentence above stands either
way. Not required for the draft; recorded in `GAPS.md` G15.
