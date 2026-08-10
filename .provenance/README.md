# Provenance for the v15 -> v15.1 repair

When the v15.1 repair was carried out this directory was not under version
control: the enclosing `/Users/cnm13ryan/git` was the repository, its `main`
branch had no commits, and `dci/` was untracked inside it. There was therefore no
version-control safety net, so the pre-repair tree was snapshotted here before
any edit.

`dci` has since been initialised as its own repository. The git history baselines
the **post-repair** state, so this snapshot remains the only in-repo copy of the
migrated-but-unrepaired code. Once a `v15.0.0` tag or branch carries that state
it becomes redundant and can be deleted.

    v15.0.0-pre-repair-src/     src/ as it stood before the repairs
    v15.0.0-pre-repair-tests/   tests/ as they stood before the repairs

To reproduce pre-repair behaviour:

    PYTHONPATH=.provenance/v15.0.0-pre-repair-src \
      python -m dci.cli run --profile configs/profiles/integration_pass.toml \
                            --data-root /tmp/pre-repair

`configs/` is unchanged by the snapshot boundary except for the ADDED
`integration_panel.toml`, so the pre-repair tree runs against the current configs.

## What v15.1 changes, and why artifacts are not comparable

`protocol_version` moved `v15` -> `v15.1`. The scientific design is unchanged:
same target A, same focal B, k=2, the same 6x2 replacement contrast, both orders
co-primary, task-level clustering, max-T simultaneous inference, J=6, unchanged
SESOI and unchanged primary wordings.

What changed is that declared rules became executed rules. Two of those changes
alter REFERENCE ADMISSION and one alters EFFECTIVE DECODING, so v15.1 artifacts
are not comparable with v15 artifacts and must never overwrite them:

| change | alters |
|---|---|
| kappa eligibility audit enforced | reference admission |
| reference-error certificate aggregated per family | reference admission |
| unsatisfiable candidate-U pairs excluded from calibration | reference admission (via g/r support) |
| `top_k` explicit (0, disabling top-k) | effective decoding + execution fingerprint |
| placebo clusters disjoint from confirmatory | falsification independence, not tau |
| claim rule fails closed | can turn a reported claim into INCONCLUSIVE_PRECISION |
| output-cap gate operational | can stop interpretation |
| `strict_or_unscorable` renamed | a secondary endpoint label |

## Recovering each behaviour

* **v15 as migrated (pre-repair)** — `.provenance/v15.0.0-pre-repair-src/`.
* **v15 notebook** — `notebook_source/cells/`, untouched by this work.
* **v15.1 (repaired)** — the live `src/`.
* **the v15 reference panel** — `tests/regression/fixture_dev_fast/config/freeze.json`
  records `S_SEMICOLON, C_W3, S_COMMA, S_MINWORDS15, C_L3, S_MINWORDS12`.
* **the v15.1 panel** — not yet determined; admission does not currently reach a
  six-reference panel in any dry-run fixture. See section C of the repair report.
* **which artifacts moved** — `V15_1_DIVERGENCES` in
  `tests/regression/test_baseline.py`, and the xfail test that enumerates them.

## Test provenance

`test_dev_fast_pipeline_matches_notebook_fixture` is retained as `xfail(strict)`.
It MUST fail: it compares v15.1 output against a frozen v15 fixture, and a green
result would mean the repairs had no effect. Re-baseline by capturing a v15.1
fixture, not by loosening the comparator.

Two failures on darwin/arm64 predate this work and are not caused by it:
* ~1e-9 float drift — `tests/regression/compare.py` assumes one container and one
  numpy build; this machine is neither.
* a `prescreen.csv` tie-ordering difference.
* `tests/integration/test_sharded_workers.py::test_two_workers_equal_one` also
  predates it: a 900 s subprocess timeout on this hardware, not a logic defect.

`GATE0_CHECKS_V15_0 = 110` is pinned in the baseline test with the four v15.1
additions listed separately, so a DROP in the invariant count is a test failure
rather than a re-baseline.
