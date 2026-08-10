"""The single authoritative expectation for Gate 0's self-test inventory.

Two tests assert on this inventory - the baseline regression and the sharded
worker traversal - and they disagreed: the baseline tracked the v15.1 total
while the sharding test still asserted the v15.0 value of 110 in two places, so
a passing repair broke an unrelated slow test. Copying a count is the defect;
one registry is the fix.

The assertion is deliberately an INVARIANT rather than a total. What matters is
that every required check ran and passed, and that the inventory never shrinks:
growth is what a repair looks like, shrinkage is an invariant being removed. The
historical totals stay here as labelled lineage, not as the pass condition.
"""
from __future__ import annotations

# LINEAGE: the count the v15 notebook migration froze.
GATE0_CHECKS_V15_0 = 110

# The invariants the v15.1 repairs added. Named, because a name that disappears
# is a specific invariant that stopped running, which a total cannot tell you.
GATE0_CHECKS_ADDED_V15_1 = {
    "power_planner_covers_the_actual_primary_family",
    "both_orders_is_never_easier_than_one_order",
    "feature_roles_match_the_caliper_machinery",
    "mechanism_and_post_treatment_features_are_never_matched",
}

# LINEAGE: the v15.1 total. Reported in failure messages; never the criterion.
GATE0_CHECKS_EXPECTED = GATE0_CHECKS_V15_0 + len(GATE0_CHECKS_ADDED_V15_1)

# Checks that must be present in any conforming run, whatever the total.
REQUIRED_CHECKS = frozenset(GATE0_CHECKS_ADDED_V15_1)


def assert_gate0_healthy(table, *, floor: int = GATE0_CHECKS_V15_0) -> None:
    """Every emitted check passed, every required check ran, nothing was lost.

    `table` is the gate0_selftest frame (columns `check` and `passed`).
    """
    names = set(table["check"])
    failed = table.loc[~table["passed"].astype(bool), "check"].tolist()
    assert not failed, f"gate 0 checks failed: {failed}"

    missing = REQUIRED_CHECKS - names
    assert not missing, (
        f"gate 0 is missing required checks {sorted(missing)}. These are named "
        "invariants, so their absence is a capability that stopped running.")

    assert len(table) >= floor, (
        f"gate 0 emitted {len(table)} checks, below the {floor} recorded for "
        f"v15.0 (v15.1 expected {GATE0_CHECKS_EXPECTED}). A DROP means an "
        "invariant was removed and must be justified, not re-baselined.")
    assert len(names) == len(table), (
        f"gate 0 emitted duplicate check names: "
        f"{sorted(n for n in names if list(table['check']).count(n) > 1)}")
