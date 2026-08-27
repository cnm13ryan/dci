# Incident: a probe-only stand-in had no admissible severity, and ended the stage

**Status: RESOLVED 2026-08-27 under amendment A17 — the stand-in is classified
`STANDIN_UNPLACEABLE` and recorded, the cells it carries are marked
`NOT_MEASURED_STANDIN_UNPLACEABLE`, and the determinate entries decide the
verdict as they already did.**

## What happened

The first `GATE_2_75_COMPOSED_PROBE` of the study, on `gemma-3n-e2b-it` at the
frozen m\* = 10, refused with a `ProtocolError` — not a registered terminal
status:

```
no severity of the stand-in 'PS1' has solo compliance inside §13.4's
[0.1, 0.9] on this replication, so it cannot stand in for a reference here.
Measured: {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0833, 8: 0.0417}
```

## The measurement

`PS1` is `capital_word` / `exact_count`, structural tier 2, ladder 1–8:
*"the answer must contain exactly q words that use a capital letter."* Its
measured solo compliance on the probe's ladder screen — 24 pre-screen topics
at `LADDER_SCREEN_DRAWS` — is 0.0 at severities 1–6, **0.0833** at 7 and
0.0417 at 8. §13.4's band floor is 0.10, so no severity is admissible.

**The instrument is sound.** §19's `witness_suite` and
`realistic_witness_suite` certified all 674 instruments at qualification, and
all four replications passed 17/17 checks. Exact-count constraints are hard by
construction: a normal answer capitalises its first word and any proper nouns,
so hitting an *exact* count is rare. This is a real measurement of a hard
instrument, not a verifier fault.

**It was never measured before adoption.** PS1–PS3 are new in v6 (A10) and no
v5 rows exist for them, so no evidence about their placeability existed when
v6 was adopted. The design authored three stand-ins and assumed each would be
placeable.

## Why the refusal was the defect

A5's P3 block registers *where* a stand-in goes — the severity of its own solo
ladder nearest Gate 2's measured `iota_A` and inside §13.4's band, because
§13.8 matches a reference's iota(R) to iota_A — and is silent on what happens
when no severity is inside it.

The probe's own declared refusals are not silent:

> `no_standin_entry_ends_a_replication` — *"an instrument that can never be
> selected as a reference cannot raise `COMPOSED_HEADROOM_UNREACHABLE`"*
> `standin_findings_gate_nothing`

A hard raise let an unplaceable `probe_only` instrument **end the stage** —
more power than any registered rule grants it, and exactly the power those
declarations exist to deny. The raise predates the A13/A15/A16 work
(introduced in `ad4eec7`).

## The rule adopted

`STANDIN_UNPLACEABLE` for the stand-in, with its measured ladder and the
reason placement failed. `NOT_MEASURED_STANDIN_UNPLACEABLE` for every
diagnostic cell requiring it; those cells are not generated and **do not enter
the Gate-2.75 feasibility verdict**. The stage continues on the genuine
determinate entries at the frozen m\*. Neither status is a §28 terminal status
nor a §18 stage-1 readiness refusal, asserted disjoint at import. The stand-in
is never clamped to a severity outside the band — the property the old refusal
protected, unchanged.

**The set that cannot be measured and the set that could never have entered
the verdict are the same set.** A13 already makes the verdict determinate-only
— `solo:A`, `solo:B` and both orders of `pair:A+B` — and every cell a stand-in
carries is stand-in-dependent by construction. A test asserts this over the
whole registered cell shape, including that with *all three* stand-ins
unplaceable what remains is exactly the unconstrained cell plus the
determinate four.

What is lost is diagnostic breadth: the §13.14 exposure classes that stand-in
carried go unmeasured on that replication, and the record names them.

**Direction.** Terminating would hand a `probe_only` instrument the power to
end a replication — the maximum. Recording denies it any. With respect to what
a stand-in may decide, recording is the closed direction.

## §32.2 disclosure

Written on 2026-08-27 after the stage refused, with PS1's measured ladder
already on the evidence tree, knowing PS1 was the instrument it would classify
and `gemma-3n-e2b-it` the replication. Chosen by the argument above and not by
computing which direction lets a replication continue.

## State preserved

No Gate-2.75 record and no terminal report were written; the failure was a
`ProtocolError` inside `compute`, so `run_stage` wrote nothing and the
replication's last transition row remained `PASS GATE_2_5_CANDIDATE_QUALIFICATION`.
The **576 ladder rows** the refused run generated are preserved and the
corrected stage reads those exact rows. No model output was regenerated.
