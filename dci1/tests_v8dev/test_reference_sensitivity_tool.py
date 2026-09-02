"""`tools/v8_reference_sensitivity.py` --- the reference-triple sensitivity
tool's core functions.

The tool re-runs §13.8's ranking over a frame's LOCAL-valid families under a
topic bootstrap, so two things have to hold before any number it prints
means anything:

1.  **the ranking it re-runs is the registered one.** ``select_core``
    mirrors ``dci1v7.stages.selection.admit_core_references``' selection
    loop at ``require_spectrum=False`` --- the call Gate 3 makes. Tested
    against the production kernel on constructed calibration tables, and
    against the signed pilot records where one is on disk;
2.  **the bootstrap is reproducible.** The seed comes from
    ``seeds.bootstrap_seed`` and the draws from ``random.Random``, so the
    output must be byte-identical in a second process under a different
    ``PYTHONHASHSEED``. That is asserted by running the bootstrap in a
    subprocess twice and comparing the JSON bytes.

The SE helpers are checked against the production ``_se_iota``.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dci1v7.protocol import constants as C
from dci1v7.stages import selection as v7_selection
from dci1v7.stages.calibration_table import instructed_compliance
from dci1v8dev.confirm.membership import admissible_triples
from dci1v8dev.run import seeds
from dci1v8dev.spectrum.validity import _se_iota

from tests_v8dev.conftest import EVIDENCE, calibration_row

TOOL_PATH = Path(__file__).resolve().parents[1] / "tools" / "v8_reference_sensitivity.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("v8_reference_sensitivity",
                                                  TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


T = _load_tool()


# --------------------------------------------------------------- the mirror
def _table(spec, *, iota_a: float, chance: float = 0.0):
    """Calibration rows whose iota is the requested distance from iota_A.

    §13.7's V_stab is computed by another stage and read by
    ``evaluate_validity``; an unevaluated component is not a satisfied one,
    so the fixture supplies a passing split verdict per candidate the way
    Gate 3 supplies the real one.
    """
    rows, stability = [], {}
    for kind, severity, distance in spec:
        iota = iota_a + distance
        solo = iota * (1.0 - chance) + chance
        rows.append(calibration_row(kind, severity, solo=solo, chance=chance,
                                    per_topic=(solo,) * 8))
        stability[f"{kind}:{severity}"] = {"passed": True, "reason": None}
    return rows, stability


def _points(rows, iota_a: float):
    by_family: dict[str, list] = {}
    for row in rows:
        by_family.setdefault(row.kind, []).append(T.Rung(
            family=row.kind, severity=row.severity,
            iota=instructed_compliance(row.solo_compliance,
                                       row.chance_compliance),
            chance=row.chance_compliance,
            per_topic=tuple(row.per_topic_solo)))
    observed = {r.label: r.iota for rungs in by_family.values() for r in rungs}
    return [T.best_rung(rungs, observed, iota_a)
            for _, rungs in sorted(by_family.items())]


@pytest.mark.parametrize("spec", [
    # the geometry of a real frame: five qualifying families a few
    # hundredths apart, two of them sharing a discourse role so §13.8's
    # substitution has to fire
    (("MK1", 4, 0.009), ("XC3", 10, 0.027), ("MK8", 2, 0.032),
     ("MK2", 3, 0.031), ("MK6", 6, 0.042)),
    # a Tier-2 family ranked first, so the Tier-1 look-ahead binds
    (("XC1", 2, 0.001), ("XC3", 4, 0.002), ("MK1", 3, 0.030),
     ("MK3", 2, 0.031), ("MK5", 5, 0.033)),
    # two rungs of one family: only the closer one may enter
    (("MK1", 3, 0.040), ("MK1", 4, 0.010), ("MK2", 3, 0.020),
     ("MK6", 6, 0.025), ("XC3", 8, 0.028)),
])
def test_select_core_mirrors_the_registered_kernel(spec):
    iota_a, solo_a = 0.67, 0.67
    rows, stability = _table(spec, iota_a=iota_a)
    reference = v7_selection.admit_core_references(
        rows, iota_a=iota_a, solo_compliance_a=solo_a,
        n_topics_a=C.N_CALIBRATION, stability_by_candidate=stability,
        require_spectrum=False)
    assert reference["references_identified"]
    expected = [e["family"] for e in reference["core_references"]]
    got = [p.family for p in T.select_core(_points(rows, iota_a))]
    assert got == expected, (got, expected)
    # and the within-family rung, not only the family
    expected_q = {e["family"]: e["severity"]
                  for e in reference["core_references"]}
    assert {p.family: p.severity
            for p in T.select_core(_points(rows, iota_a))} == expected_q


def test_select_core_returns_nothing_when_the_pool_cannot_meet_13_8():
    # three families, one feature group short (two markers of one group do
    # not exist, so use one family per group but only two groups available)
    iota_a = 0.67
    rows, _ = _table((("MK1", 4, 0.01), ("MK1", 5, 0.02)), iota_a=iota_a)
    assert T.select_core(_points(rows, iota_a)) == ()


def test_the_primary_triple_is_always_an_admissible_triple():
    iota_a = 0.67
    spec = (("MK1", 4, 0.009), ("XC3", 10, 0.027), ("MK8", 2, 0.032),
            ("MK2", 3, 0.031), ("MK6", 6, 0.042))
    points = _points(_table(spec, iota_a=iota_a)[0], iota_a)
    primary = T.select_core(points)
    refs = [{"slot": f"R{i + 1}", "family": p.family}
            for i, p in enumerate(points)]
    keys = {tuple(sorted(t["families"])) for t in admissible_triples(refs)}
    assert tuple(sorted(p.family for p in primary)) in keys


# ------------------------------------------------------------------- the SEs
def test_se_iota_matches_the_production_statistic():
    vector = (0.0, 0.25, 0.5, 0.75, 1.0, 0.5, 0.25, 0.75, 1.0, 0.0)
    for chance in (0.0, 0.13, 0.4):
        row = calibration_row("MK1", 3, solo=sum(vector) / len(vector),
                              chance=chance, per_topic=vector)
        assert T.se_iota(vector, chance) == pytest.approx(_se_iota(row),
                                                          rel=0, abs=1e-15)


def test_se_iota_is_undefined_on_a_vector_of_one():
    assert T.se_iota((0.5,), 0.0) is None
    assert T.se_iota((), 0.0) is None


def test_the_paired_se_of_the_difference_is_zero_when_the_frames_agree():
    vector = (0.0, 0.5, 1.0, 0.25, 0.75, 0.5)
    assert T.se_difference(vector, 0.0, vector, 0.0) == pytest.approx(0.0)
    # and it is smaller than the sum of the marginals when the two move
    # together, which is why the tool pairs them
    other = tuple(min(1.0, v + 0.1) for v in vector)
    paired = T.se_difference(other, 0.0, vector, 0.0)
    marginal = (T.se_iota(other, 0.0) ** 2 + T.se_iota(vector, 0.0) ** 2) ** 0.5
    assert paired < marginal
    assert T.se_difference(vector[:3], 0.0, vector, 0.0) is None


# ------------------------------------------------------------- determinism
_DRIVER = '''
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("tool", sys.argv[1])
T = importlib.util.module_from_spec(spec)
sys.modules["tool"] = T
spec.loader.exec_module(T)

n = 48
families = {}
for i, (kind, sev) in enumerate((("MK1", 4), ("MK2", 3), ("MK6", 6),
                                 ("MK8", 2), ("XC3", 10), ("MK5", 5))):
    vec = tuple(((i * 7 + t * 13) % 5) / 4.0 for t in range(n))
    families[kind] = [T.Rung(family=kind, severity=sev,
                             iota=sum(vec) / n, chance=0.05, per_topic=vec)]
a_vector = [((t * 11) % 4) / 3.0 for t in range(n)]
points = {k: T.best_rung(v, {r.label: r.iota for r in v}, 0.6)
          for k, v in sorted(families.items())}
refs = [{"slot": "R%d" % (i + 1), "family": f}
        for i, f in enumerate(sorted(points))]
from dci1v8dev.confirm.membership import admissible_triples
keys = [tuple(sorted(t["families"])) for t in admissible_triples(refs)]
primary = tuple(sorted(p.family for p in T.select_core(list(points.values()))))
out = T._bootstrap(families, a_vector=a_vector, kappa_a=0.05, n_topics=n,
                   keys=keys, primary_key=primary,
                   seed=int(sys.argv[2]), resamples=300)
sys.stdout.write(json.dumps(T._jsonable(out), indent=1, sort_keys=True))
'''


def _run_driver(tmp_path: Path, hashseed: str, seed: int) -> bytes:
    tmp_path.mkdir(parents=True, exist_ok=True)
    driver = tmp_path / "driver.py"
    driver.write_text(_DRIVER)
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = hashseed
    env["PYTHONPATH"] = os.pathsep.join(
        [str(TOOL_PATH.parents[1] / "src"), env.get("PYTHONPATH", "")])
    proc = subprocess.run([sys.executable, str(driver), str(TOOL_PATH),
                           str(seed)], capture_output=True, env=env,
                          cwd=str(tmp_path))
    assert proc.returncode == 0, proc.stderr.decode()
    return proc.stdout


def test_the_bootstrap_is_byte_identical_across_processes(tmp_path):
    seed = seeds.bootstrap_seed("reference_sensitivity:frame0", "qwen3-4b")
    first = _run_driver(tmp_path / "a", "0", seed)
    second = _run_driver(tmp_path / "b", "1", seed)
    assert first == second
    assert first  # and it produced something
    payload = json.loads(first)
    assert payload["p_selected"]
    assert abs(sum(payload["p_selected"].values()) - 1.0) < 1e-9


def test_a_different_seed_gives_a_different_draw(tmp_path):
    a = _run_driver(tmp_path / "s0",
                    "0", seeds.bootstrap_seed("reference_sensitivity:frame0",
                                              "qwen3-4b"))
    b = _run_driver(tmp_path / "s1",
                    "0", seeds.bootstrap_seed("reference_sensitivity:frame1",
                                              "qwen3-4b"))
    assert a != b


def test_the_seed_is_domain_separated_per_frame_and_model():
    drawn = {seeds.bootstrap_seed(f"reference_sensitivity:frame{f}", model)
             for f in range(C.N_WORDINGS)
             for model in ("qwen3-4b", "gemma-3n-e2b-it")}
    assert len(drawn) == 2 * C.N_WORDINGS
    # and it is not the operating-point stability draw of the same frame
    assert seeds.bootstrap_seed("reference_sensitivity:frame0", "qwen3-4b") != \
        seeds.bootstrap_seed("operating_point_stability:frame0", "qwen3-4b")


# ------------------------------------------------- against a signed record
def _pilot(root_name: str, model: str):
    root = EVIDENCE / root_name
    if not (root / "durable" / "dci1v8" / model).exists():
        pytest.skip(f"no stored pilot root at {root} (evidence is gitignored)")
    return root


@pytest.mark.parametrize("root_name,model", [
    ("dci1v8-pilot-r9", "qwen3-4b"),
    ("dci1v8-pilot-r11", "gemma-3n-e4b-it"),
])
def test_the_tool_reproduces_the_recorded_core_on_every_frame(root_name, model,
                                                              tmp_path):
    root = _pilot(root_name, model)
    report = T.model_report(root, model, resamples=25)
    checked = 0
    for block in report["by_frame"].values():
        if not block.get("supported") or not block["primary"]["families"]:
            continue
        assert block["primary"]["reproduces_record"], block["frame"]
        assert block["primary"]["families"] == block["primary"]["recorded_core"]
        # every reported triple really is admissible, and the frozen count
        # never exceeds the count over the whole LOCAL-valid pool
        assert (block["n_admissible_triples_frozen_five"]
                <= block["n_admissible_triples_all_valid"]
                or block["n_frozen_families"] > block["n_local_valid_families"])
        assert 0.0 <= block["p_primary_reselected"] <= 1.0
        checked += 1
    assert checked
