"""The v4 instrument re-scores the recorded evidence (read-only).

Three validations of the seam against real generations, all evidence
read-only, all skipped cleanly where the machine-local trees are absent:

  1. Every B+R pilot row (576 per Gemma): the v4 boolean pass reproduces
     the recorded reference verdict, the v4 exact-count statistic
     reproduces the recorded s0, and the v4-scored focal outcomes
     reproduce the reported pilot cell rates, joint states, order table
     and diagnostics in reports/br_pilot_v4/result.json (pre-freeze check
     C13 of DCI1_v4r2_prefreeze_checks.md).

  2. Every v3 confirmatory AB row (6,144 per Gemma) and every reused
     Gate 2A solo row: v4 passes equal the recorded verdicts and the
     pinned pass counts.

  3. The demoted-diagnostic identity (pre-freeze check C18): the A-side
     companion swap computed from v4-scored raw text at the registered
     primary draw reproduces the recorded v3 ``pooled_swap_effect``
     (-0.009548611111111082 and +0.0651041666666667) on the rows.

Nothing here writes; the v3 evidence tree and the pilot cache stay
byte-identical.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest
from dci1v3.protocol.seeds import primary_draw_index
from dci1v4.verifiers.compliance import compliance_vector, score_constraint
from dci1v4.verifiers.constraints import Constraint

DCI1 = Path(__file__).resolve().parents[1]
V3_EVIDENCE = DCI1 / "evidence" / "dci1-v3"
PILOT_EVIDENCE = DCI1 / "evidence" / "br-pilot-v4"
PILOT_RESULT = DCI1 / "reports" / "br_pilot_v4" / "result.json"

pytestmark = pytest.mark.skipif(
    not (V3_EVIDENCE / "gemma-3n-e2b-it" / "gate2a" / "cache.jsonl").exists()
    or not (PILOT_EVIDENCE / "gemma-3n-e2b-it" / "cache.jsonl").exists(),
    reason="machine-local evidence trees not present")

#: Frozen v3 operating points (gate3_freeze.json, pinned in tests_v3).
N_STAR = {"gemma-3n-e2b-it": 5, "gemma-3n-e4b-it": 7}
M_STAR = {"gemma-3n-e2b-it": 7, "gemma-3n-e4b-it": 7}

#: v3 registered record (analysis/unmasked/result.json secondary block).
POOLED_SWAP_EFFECT = {"gemma-3n-e2b-it": -0.009548611111111082,
                      "gemma-3n-e4b-it": 0.0651041666666667}

#: Reused confirmatory AB pins (rows, added_pass count), from tests_v3.
CONFIRMATORY_AB = {"gemma-3n-e2b-it": (6144, 2115),
                   "gemma-3n-e4b-it": (6144, 2730)}

GEMMAS = tuple(sorted(N_STAR))


def _rows(path: Path, keep) -> list[dict]:
    out = []
    with path.open() as fh:
        for line in fh:
            if keep(line):
                out.append(json.loads(line))
    return out


@pytest.mark.parametrize("model", GEMMAS)
def test_pilot_rows_rescore_and_reproduce_the_report(model):
    reported = json.loads(PILOT_RESULT.read_text())["models"][model]
    b = Constraint("B", M_STAR[model])
    refs = [(family, int(q)) for family, q in reported["references"]]

    rows = _rows(PILOT_EVIDENCE / model / "cache.jsonl", lambda _: True)
    assert len(rows) == 576

    b_pass: dict[tuple, list[float]] = defaultdict(list)
    by_order: dict[tuple, dict[str, list[float]]] = defaultdict(
        lambda: {"B_first": [], "R_first": []})
    joint = defaultdict(lambda: [0, 0, 0, 0])
    truncated = short = accidental = 0
    for row in rows:
        key = (row["constraint_id"], row["severity"])
        assert key in set(refs), row["row_id"]
        is_truncated = row["finish_reason"] == "length"
        record = compliance_vector(
            [b, Constraint(*key)], row["raw_response"],
            truncated=is_truncated, finish_reason=row["finish_reason"])
        b_score, r_score = record.scores

        # v4 pass == the recorded frozen-instrument verdicts, row by row.
        assert r_score.passed == bool(row["verdicts"]["added_pass"]), \
            row["row_id"]
        assert record.accidental_s0 == row["verdicts"]["s0"], row["row_id"]

        b_pass[key].append(float(b_score.passed))
        by_order[key][row["order"]].append(float(b_score.passed))
        joint[key][(1 - b_score.passed) * 2 + (1 - r_score.passed)] += 1
        truncated += is_truncated
        short += len(row["raw_response"].split()) < 3  # the pilot's measure
        accidental += row["verdicts"]["s0"] > 0

    # Aggregates reproduce the reported result.json exactly (C13).
    diag = reported["diagnostics"]
    assert truncated == diag["truncated"]
    assert short == diag["short"]
    assert accidental == diag["accidental_s0"]
    for family, q in refs:
        label = f"{family}@{q}"
        values = b_pass[(family, q)]
        assert len(values) == 192
        assert sum(values) / 192 == pytest.approx(
            reported["point"][f"P_B_given_{label}"], abs=1e-12)
        both, b_only, r_only, neither = joint[(family, q)]
        recorded = diag["joint_states_B_R"][label]
        assert [both, b_only, r_only, neither] == [
            recorded["both_pass"], recorded["B_only"],
            recorded["R_only"], recorded["neither"]]
        for order in ("B_first", "R_first"):
            values = by_order[(family, q)][order]
            assert len(values) == 96
            assert sum(values) / 96 == pytest.approx(
                diag["P_B_given_R_by_order"][label][order], abs=1e-12)


@pytest.mark.parametrize("model", GEMMAS)
def test_v3_solo_grid_rescores_under_the_v4_instrument(model):
    """The complete Gate 2A solo grid: A at every n, B at every m, every
    family at every v3 severity — v4 passes equal the recorded verdicts."""
    rows = _rows(V3_EVIDENCE / model / "gate2a" / "cache.jsonl",
                 lambda line: '"solo:' in line)
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        _, kind, sev = row["kind"].split(":")
        counts[row["kind"]] += 1
        score = score_constraint(Constraint(kind, int(sev)),
                                 row["raw_response"],
                                 truncated=row["finish_reason"] == "length")
        if kind == "A":
            assert score.passed == bool(row["verdicts"]["target_pass"]), \
                row["row_id"]
            assert score.statistic == row["verdicts"]["s0"], row["row_id"]
        else:
            assert score.passed == bool(row["verdicts"]["added_pass"]), \
                row["row_id"]
    assert len(counts) == 44          # 8 A + 4 B + 8 families x 4 severities
    assert all(n == 96 for n in counts.values())


@pytest.mark.parametrize("model", GEMMAS)
def test_v3_confirmatory_ab_rescores_to_the_pinned_counts(model):
    rows = _rows(V3_EVIDENCE / model / "confirmatory" / "cache.jsonl",
                 lambda line: '"arm": "AB"' in line)
    expected_rows, expected_passes = CONFIRMATORY_AB[model]
    assert len(rows) == expected_rows
    b = Constraint("B", M_STAR[model])
    passes = 0
    for row in rows:
        assert row["arm"] == "AB"
        score = score_constraint(b, row["raw_response"],
                                 truncated=row["finish_reason"] == "length")
        assert score.passed == bool(row["verdicts"]["added_pass"]), \
            row["row_id"]
        passes += score.passed
    assert passes == expected_passes


@pytest.mark.parametrize("model", GEMMAS)
def test_demoted_swap_diagnostic_identity_on_rows(model):
    """C18: v4-scored raw text reproduces the v3 pooled_swap_effect."""
    n_star = N_STAR[model]
    a = Constraint("A", n_star)
    fail: dict[str, dict[str, float]] = defaultdict(dict)
    rows = _rows(V3_EVIDENCE / model / "confirmatory" / "cache.jsonl",
                 lambda line: ('"arm": "AB"' in line
                               or '"arm": "AR' in line))
    for row in rows:
        if row["arm"] not in ("AB", "AR1", "AR2", "AR3"):
            continue
        if row["draw_index"] != primary_draw_index(row["model_id"],
                                                   row["prompt_hash"]):
            continue
        score = score_constraint(a, row["raw_response"],
                                 truncated=row["finish_reason"] == "length")
        assert score.statistic == row["verdicts"]["s0"], row["row_id"]
        fail[row["block_id"]][row["arm"]] = 0.0 if score.passed else 1.0
    assert len(fail) == 384
    assert all(len(arms) == 4 for arms in fail.values())
    swap = sum(arms["AB"] - (arms["AR1"] + arms["AR2"] + arms["AR3"]) / 3
               for arms in fail.values()) / 384
    assert swap == pytest.approx(POOLED_SWAP_EFFECT[model], abs=1e-12)
