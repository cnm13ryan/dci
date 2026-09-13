# §13.2's admission rule: the question, and why the protocol already answers it

**Classification: protocol interpretation.** Not a stage, not an amendment, not
a screen. Nothing registered changes here: no threshold, caliper, band,
criterion, ladder, wording or grid moves, and the canonical verifier hash is
unchanged at `f5d4f7e74e757769ec43d7007b012168…`. Machine-readable artifact:
`resolution.json`.

---

## 1. The question, as it was raised

§13.2 admits a reference severity subject to six conditions. Condition 2 reads:

> the same absolute difference is at most 0.15 on the disjoint 24 pre-screen
> topics.

Two non-confirmatory screens reported that some rungs had no such measurement,
and concluded that the protocol does not say whether an unmeasurable condition
**abstains** (apply the other five and record condition 2 as not evaluated) or
**fails** (reject the rung). The dispositions differ materially: on the
calibration screen's floored-stem arms, abstain admits 3/4/1/4 families from the
registered pool and reject admits 1/2/1/2.

`dci1/reports/cal_screen_v4/REPORT.md` §6 called this "a preregistration gap, not
a measurement" and "a researcher decision of the same kind as §12.4's graded
clause". `dci1/reports/INVESTIGATION_2026-08-20.md` called it the smallest
remaining blocker, because it decides the reference pool and the pool is Gate 1's
binding item.

**Both statements are wrong, and this report withdraws them.**

## 2. The resolution

The case does not arise in the registered pipeline, so there is nothing to
choose between.

| step | registered text | consequence |
|---|---|---|
| §12.2 | "the pre-screen measures on the 24 pre-screen topics, one draw per cell: the full $n$ grid for $A$, the full $m$ grid for $B$, and **all 94 reference ladder severities** … and produces the shortlist of at most three ladder severities per family" | every rung, and $A$'s whole $n$ grid, have a pre-screen value |
| §12.3 | "the full $n$ grid, the full $m$ grid, and **every shortlisted reference severity** are measured" on the 96 solo-calibration topics | only shortlisted rungs get a 96-topic value |
| §13.2 cond. 1 | "at most 0.10 **on the 96 solo-calibration topics**" | a rung §12.3 never measured cannot be a §13.2 candidate |

So §13.2's feasible set is a **subset of §12.2's shortlist**, and every member of
that shortlist carries a pre-screen value by construction. Condition 2 always has
its input, and its anchor — $A$ at $n^*$ on the pre-screen topics — is there too,
because §12.2 measures the full $n$ grid.

**Verified against the registered records, not asserted.** All four models
completed `REGIME_SCREEN` (`evidence/dci1-v4/*/regime_screen.json`, one draw per
cell as §12.2 registers):

| model | registered rungs | rungs measured on the pre-screen topics | shortlisted rungs | shortlisted with no pre-screen value |
|---|---:|---:|---:|---:|
| gemma-3n-e2b-it | 94 | **94** | 24 | **0** |
| gemma-3n-e4b-it | 94 | **94** | 24 | **0** |
| qwen3-4b | 94 | **94** | 24 | **0** |
| qwen3-4b-instruct-2507 | 94 | **94** | 24 | **0** |

## 3. And where the case is constructed anyway, the implementation decides it

`gates.admit_family` reads `pre = prescreen.get(q)` and, when it is `None`,
appends the rejection reason `"no pre-screen measurement"`. The registered
disposition is **reject**. `resolution.json` executes it on a probe whose two
runs are identical in every other respect:

| rung | pre-screen value | admissible | reasons |
|---|---|---|---|
| RF1:1 | present, distance 0 | **yes** | — |
| RF1:1 | absent | **no** | `["no pre-screen measurement"]` |

Abstain appears nowhere in the registered code. It was invented by the screens
for their own use and is not a reading of §13.2.

## 4. Why the screens met the case at all

Two reasons, both properties of the screens.

1. **They admitted rungs outside the §12.2 shortlist.** The calibration screen
   measured whole candidate ladders and the registered families' shortlist on
   the 96 topics, then ran §13.2 over all of it. Rungs the registered pipeline
   would never present to §13.2 have no pre-screen value because §12.2 was never
   asked for one under those conditions.
2. **Their floored-stem pre-screen was partial.** The FORM × STEM screen measured
   only the current-stem caliper rungs under the floored stem, so a floored-stem
   §13.2 had a pre-screen input for some rungs and not others. That is a gap in
   one screen's data, not in the protocol.

**Under a changed prompt stem the resolution still holds.** A stem change is a
change of experimental condition, and Amendment A's own §5.1 says so: "the dense
ladder screen (§12.2), $n^*$ and $m^*$ (§12.3) and the §13.2 reference admission
are all measured under the current stem … every one of them is re-measured."
§12.2 re-run under any stem supplies condition 2's input for all 94 rungs exactly
as it does now. **This resolution is therefore neutral between the stems and is
not an argument for or against Amendment A.**

## 5. What is now on the mandatory path

`regime.assert_shortlist_is_measured` refuses to write a `REGIME_SCREEN` record
whose shortlist names a rung the ladder curves do not carry, or whose shortlist
exceeds three per family. `regime_screen_payload` calls it, so the guarantee
§13.2 depends on is a checked precondition of the record §13.2 reads rather than
a property of having run the stages in the right order.

Tests in `tests_v4/test_t6_stage_machine.py`:

- `test_a_shortlist_naming_an_unmeasured_rung_is_refused`
- `test_a_shortlist_longer_than_three_is_refused`
- `test_the_regime_record_cannot_be_written_without_that_guarantee`
- `test_admit_family_rejects_a_rung_with_no_prescreen_value` — pins **reject**,
  so a later change to abstain has to be visible as a change to §13.2
- `test_every_registered_regime_record_satisfies_the_invariant` — over the four
  records on disk

One existing fixture asserted `regime_screen_payload` would accept a shortlist
with `ladder_curves={}`. That record shape is one the registered pipeline cannot
produce, and it is exactly the shape that hands §13.2 an unevaluable condition.
The fixture now supplies the curves its own shortlist was built from.

## 6. What this does not decide

- **Not** whether any amendment is adopted.
- **Not** which family or severity is admitted on any model — Gate 3 is stage 6
  and Gate 2 has not run.
- **Not** $n^*$, $m^*$, or any threshold.
- **Not** §12.4's graded-degeneracy clause, which is a separate and still-open
  reading (§7 below).

## 7. The other reading, which this does not resolve

§12.4 requires that "the graded distribution of each outcome constraint is
non-degenerate, meaning it is not concentrated above 0.99 or below 0.01", and
`gates.gate2_payload` compares one float per constraint without saying which.
The two candidate readings are the cell's **mean graded score** and the **share
of draws above 0.99**.

The textual evidence favours the share reading: "distribution" and "concentrated"
are both statements about mass, a mean is not a distribution, and the code's own
parameter is named `graded_distribution`. There is also a structural argument
that needs no data — B's graded score $1-(\text{words over } m)/(\text{total
words})$ and A's $\max(0, 1-|s_0-n|/n)$ are incommensurable forms sharing one
threshold, so under the mean reading the clause is inert for A by construction
and near-binding for B by construction.

That is suggestive, not decisive, and this report does not take the decision.
**It is also not currently binding**: under the registered prompt stem §12.4
already fails on B's solo vacuity alone on all four models, at every rung of the
grid, whichever reading is used. The graded clause becomes decision-relevant only
under a stem amendment that is not adopted.
