# The Stage 2 / Stage 10 boundary, and what Stage 2 still owes

This replaces `docs/v19_stage2_review_pack.md`, which is retained on
`invest/v19-stage2-adversarial` as investigation evidence. That document asked the
investigator to decide `ordering_depth` and to accept A1–A3; both have happened, and
two of its claims were wrong (see the *Superseded* section of
`v19_stage2_specification_amendments.md`). Porting it forward would carry the errors
with it.

## The boundary

An earlier version of this branch required `satisfiability.semantic_reviews` at Stage
2. That gate could never be satisfied: the compositions to review are Stage 8 and
Stage 10 outputs, so Stage 2 would wait on material that later stages produce. The
edge was introduced here; it is not an ambiguity in the protocol.

The preregistration divides the work explicitly:

| text | assignment |
|---|---|
| §14.2 | Stage 2 implements "verifier conjunction checks, semantic-review **triggers**, boundary/property tests, causal field roles, completeness ledger, and provenance" |
| §8.6 | every composition receives SATCERT "**before entering a frozen confirmatory bank**" |
| §14.10 | Stage 10 builds that bank, and "generate[s] and verif[ies] concrete satisfying witnesses automatically where deterministic coverage permits" |

So **Stage 2 certifies the machinery that decides when a human must review; Stage 10
certifies each composition the bank accepts.**

| slot | gate | why |
|---|---|---|
| `satisfiability.review_trigger` | Stage 2 requires and produces | §14.2's "triggers" |
| `satisfiability.semantic_reviews` | Stage 10 requires | per composition, and compositions do not exist yet |
| `satisfiability.certified_compositions` | Stage 10 produces | SATCERT is per arm |

### Nothing escapes review

The correction is only sound if certification still refuses an incompletely covered
composition with no review. That is **demonstrated, not argued**:
`_review_boundary_finding` certifies a real composition with `review=None` and
requires `Outcome.REVIEW_REQUIRED`. Moving the requirement moves *when* it is
checked, not *whether*.

### The trigger's four properties

Four hash-frozen adversarial fixtures, regenerated at certification time and compared
by record hash:

1. review triggers when deterministic coverage is incomplete;
2. a `COMPLETE` clause does **not** trigger — otherwise a reviewer's attention would
   carry no information;
3. a review keyed to the wrong witness is rejected — a review of a different text
   certifies a different thing;
4. reviewer disagreement does not certify without a third adjudicator.

## The review burden Stage 10 inherits

Recorded here because it is large and was not obvious.

**No composition the protocol can currently encode is fully covered.** Each pair has
exactly one `PARTIAL` clause:

| pair | incompletely covered clause | what the projection does not capture |
|---|---|---|
| 1 | focal, item precedence | that a reader would identify the item at a position **as** that item |
| 2 | focal, all words unique | confusables: a Cyrillic look-alike is a different string and NFKC does not merge it |
| 3 | target, exact sentence count | the frozen segmentation strips list markers and treats each line as a sentence |

So **every** Stage 10 composition needs its own review, and granularity is per
composition — two compositions differ in their witness, and a review is a judgement
about one concrete text. The `semantic_reviews` domain enforces that through the
witness binding rather than through a policy note, so it cannot be relaxed later on
workload grounds by editing a comment.

### Mechanically closable gaps: analysis, not action

The instruction to "close any mechanically solvable coverage gaps before Stage 10"
was assessed. Two of the three have a known mechanism, and **neither is closed here,
because closing it would be a specification change the investigator has not
authorised**:

- **Pair 2, confusables.** UTS #39 defines a normative confusable-skeleton mapping
  that would collapse Cyrillic `а` onto Latin `a`. But §10.6 assigns homoglyphs to
  human *audit material*, not to an automated rule, so adopting it would amend A2's
  just-accepted tokenisation contract.
- **Pair 3, segmentation.** Requiring terminal punctuation would stop a marker-stripped
  line counting as a sentence. That changes Pair 3 verdicts on every answer without a
  final period — again an amendment to A2.
- **Pair 1, item identification.** Not mechanically closable. Whether a reader sees
  the token `bravo` in a sentence *as the item bravo* is the semantic judgement §8.6
  exists to obtain.

Each would be a further prospective amendment with its own differential audit. They
are surfaced as candidate decisions, not applied.

## What Stage 2 still owes

Stage 2's **gate** is `READY`: every scientific decision is accepted and every
artifact the gate requires is produced and recorded.

Stage 2 is **not certified**. `certify_stage2` reports exactly one outstanding
requirement:

> `verifiers.tier1_reliability` — each of the six target and focal verifier units
> certified against the 5% Tier-1 ceiling on **72 human-adjudicated labels per truth
> class**, zero observed errors. 864 labels in total.

No amount of code produces those. Without this finding the gate would have reported
Stage 2 certified without them, which is why it was added rather than assumed.

## Verdict

`READY_FOR_STAGE_2_REVIEW` — not `STAGE_2_CERTIFIED`, and not until the Tier-1 audit
has been adjudicated under the strict fixed design A3 accepted.
