"""Unregistered near-miss sensitivity over the registered v3 rows.

Read-only diagnostic behind RESULTS_V3.md §6: reclassifies |s0 - n*| == 1
failures as passes ("tolerant" rule) and decomposes the registered
contrast into near-miss and far-miss parts, per model and order stratum.
It never writes into the evidence tree, and it asserts that the exact
rule reproduces the registered point estimates before reporting any
sensitivity number. The bootstrap uses a fresh, deliberately
unregistered seed (0) and reports marginal percentile intervals — not
the registered simultaneous machinery.

Run:  dci1/.venv/bin/python dci1/tools/nearmiss_sensitivity_v3.py
Writes: dci1/reports/nearmiss_sensitivity_v3.json (and prints it).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

DCI1_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = DCI1_ROOT / "evidence" / "dci1-v3"
OUT = DCI1_ROOT / "reports" / "nearmiss_sensitivity_v3.json"

#: model -> (registered n*, registered per-stratum tau under the exact
#: rule, from <model>/analysis/unmasked/result.json family F1)
MODELS = {
    "gemma-3n-e2b-it": (5, {"target_first": 0.006944444444444478,
                            "added_first": -0.026041666666666644}),
    "gemma-3n-e4b-it": (7, {"target_first": 0.09027777777777783,
                            "added_first": 0.03993055555555559}),
}
ORDERS = ("target_first", "added_first")
ARMS = ("AB", "AR1", "AR2", "AR3")
RESAMPLES = 10_000
SEED = 0  # unregistered


def main() -> None:
    out = {"note": "unregistered read-only sensitivity; see RESULTS_V3.md §6",
           "seed": SEED, "resamples": RESAMPLES, "models": {}}
    for model, (n, registered_tau) in MODELS.items():
        rows_path = EVIDENCE / model / "analysis/unmasked/unmasked_rows.jsonl"
        rows = [json.loads(line) for line in rows_path.open()]
        blocks: dict[str, dict[str, int]] = {}
        orders: dict[str, str] = {}
        for r in rows:
            if r["arm"] not in ARMS:
                continue
            blocks.setdefault(r["block_id"], {})[r["arm"]] = \
                r["verdicts"]["s0"]
            orders[r["block_id"]] = r["order"]
        bids = sorted(blocks)
        assert all(set(blocks[b]) == set(ARMS) for b in bids)
        s0 = np.array([[blocks[b][a] for a in ARMS] for b in bids], int)
        order = np.array([orders[b] for b in bids])

        fail_exact = (s0 != n).astype(float)
        near = (np.abs(s0 - n) == 1).astype(float)
        far = (np.abs(s0 - n) > 1).astype(float)
        assert np.array_equal(fail_exact, near + far)

        def tau(f):
            d = f[:, 0] - f[:, 1:4].mean(axis=1)
            return {o: float(d[order == o].mean()) for o in ORDERS}

        def boot_ci(f, o):
            rng = np.random.default_rng(SEED)
            d = f[:, 0] - f[:, 1:4].mean(axis=1)
            idx = np.flatnonzero(order == o)
            draws = d[idx[rng.integers(0, idx.size,
                                       (RESAMPLES, idx.size))]].mean(axis=1)
            return [float(np.quantile(draws, 0.025)),
                    float(np.quantile(draws, 0.975))]

        tau_exact = tau(fail_exact)
        for o in ORDERS:
            assert abs(tau_exact[o] - registered_tau[o]) < 1e-12, \
                f"{model}/{o}: exact rule does not reproduce the " \
                f"registered estimate"

        out["models"][model] = {
            "n_star": n,
            "blocks": len(bids),
            "tau_registered_exact": tau_exact,
            "tau_tolerant_pass_within_1": tau(far),
            "tau_nearmiss_component": tau(near),
            "tolerant_ci_unregistered": {o: boot_ci(far, o) for o in ORDERS},
            "arm_failure_rates": {
                a: {"exact_fail": float(fail_exact[:, i].mean()),
                    "near_miss": float(near[:, i].mean()),
                    "far_miss": float(far[:, i].mean()),
                    "near_share_of_failures": float(
                        near[:, i].sum() / max(fail_exact[:, i].sum(), 1))}
                for i, a in enumerate(ARMS)},
        }
    text = json.dumps(out, indent=1)
    OUT.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
