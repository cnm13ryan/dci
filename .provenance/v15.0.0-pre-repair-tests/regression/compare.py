"""Artifact comparator: migrated package vs the notebook fixture run.

Deterministic artifacts must match exactly; the only permitted differences are
volatile identity fields (timestamps, run ids, attempt ids, wall-clock,
machine paths). Floating-point columns are compared exactly first and reported
at 1e-9 relative tolerance if exactness fails, because both runs execute the
same interpreter, numpy build and seed path in this container: a genuine
difference means a behavioral divergence, not numerics.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

VOLATILE_JSON_KEYS = {
    "created_utc", "recorded_utc", "frozen_utc", "started_utc", "utc",
    "run_id", "run_attempt_id", "wall_seconds", "seconds", "hostname",
    "path", "signed_path", "durable_base", "python", "platform",
    "cpu_ram_gb", "disk_free_gb",
}
VOLATILE_CSV_COLS = {
    "recorded_utc", "started_utc", "wall_seconds", "run_attempt_id",
    "tokenize_seconds", "generate_seconds", "decode_seconds", "h2d_seconds",
}
PATH_RE = re.compile(r"/[\w./-]*?(?:scratch|artifacts)[\w./-]*")


def normalize_text(text: str) -> str:
    return PATH_RE.sub("<PATH>", text)


def load_csv_table(path: Path) -> list[dict]:
    import csv
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for c in list(r):
            if c in VOLATILE_CSV_COLS:
                r[c] = "<VOLATILE>"
            else:
                r[c] = normalize_text(r[c] or "")
    return rows


def compare_csv(a: Path, b: Path, rel_tol: float = 1e-9) -> list[str]:
    ra, rb = load_csv_table(a), load_csv_table(b)
    problems = []
    if len(ra) != len(rb):
        return [f"{a.name}: row count {len(ra)} vs {len(rb)}"]
    if ra and set(ra[0]) != set(rb[0]):
        return [f"{a.name}: columns differ: "
                f"{sorted(set(ra[0]) ^ set(rb[0]))}"]
    for i, (x, y) in enumerate(zip(ra, rb)):
        for c in x:
            if x[c] == y[c]:
                continue
            try:
                fx, fy = float(x[c]), float(y[c])
                if math.isnan(fx) and math.isnan(fy):
                    continue
                if math.isclose(fx, fy, rel_tol=rel_tol, abs_tol=1e-12):
                    problems.append(
                        f"{a.name}[{i}].{c}: {x[c]} vs {y[c]} (within 1e-9; "
                        "investigate, exactness expected)")
                    continue
            except (TypeError, ValueError):
                pass
            problems.append(f"{a.name}[{i}].{c}: {x[c]!r} vs {y[c]!r}")
            if len(problems) > 20:
                return problems
    return problems


def _strip_json(obj):
    if isinstance(obj, dict):
        return {k: ("<VOLATILE>" if k in VOLATILE_JSON_KEYS
                    else _strip_json(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_json(v) for v in obj]
    if isinstance(obj, str):
        return normalize_text(obj)
    return obj


def compare_json(a: Path, b: Path) -> list[str]:
    ja = _strip_json(json.loads(a.read_text()))
    jb = _strip_json(json.loads(b.read_text()))
    if ja == jb:
        return []
    return [f"{a.name}: JSON differs after volatile stripping"]


GATE_CSVS = [
    "gate0_selftest.csv", "u_screening.csv", "prescreen.csv",
    "hard_eligibility_full.csv", "hard_eligibility_declared.csv",
    "reference_selection.csv", "individual_reference_validation.csv",
    "panel_residual_validation.csv", "wording_validation.csv",
    "falsification_individual.csv", "falsification_panel.csv",
    "common_support.csv", "pool_dependence_audit.csv", "eligibility_log.csv",
    "architecture_comparison.csv",
]
SCORE_CSVS = [
    "calipers.csv", "calibration_signature.csv", "tau_matrix.csv",
    "primary_effects.csv", "condition_failure_rates.csv",
    "paraphrase_escalation.csv", "sensitivity_diagnostics.csv",
    "caliper_precision.csv", "signature_gaps.csv", "order_effects.csv",
    "claim_rule.csv",
]
# Source-derived provenance hashes legitimately changed when the code moved
# out of the notebook: they fingerprint SOURCE TEXT, the migration rewrote
# shared names to S.* and relocated functions, and forging the old hashes
# would be false provenance. Behavioral identity is established by every
# other artifact in this suite. The comparator pins EXACTLY this allowlist so
# any further drift still fails. Ledger: L-hash-relocation.
RELOCATED_HASH_FIELDS = {
    "verifier_source_sha256", "analysis_sha256", "caliper_rule_sha256",
    "coupling_mutation_sha256", "coupling_edit_sha256",
}
RELOCATED_EXPORT_KEYS = {"plan_sha256"}

GATE_JSONS = [
    "gate_0_implementation.json", "gate_M_measurement.json",
    "gate_1_u_bank.json", "gate_2_feasibility.json", "gate_2a_precision.json",
    "gate_3_validation.json", "gate_3b_wording.json",
    "gate_4_falsification.json", "u_split.json", "pseudo_focal_freeze.json",
    "wording_validation.json",
]


def compare_runs(fixture: Path, run: Path) -> tuple[list[str], list[str]]:
    problems, compared = [], []
    for name in GATE_CSVS:
        fa, fb = fixture / "gates" / name, run / "gates" / name
        if fa.exists() and fb.exists():
            compared.append(f"gates/{name}")
            problems += compare_csv(fa, fb)
        elif fa.exists() != fb.exists():
            problems.append(f"gates/{name}: present in only one run")
    for name in SCORE_CSVS:
        fa, fb = fixture / "scores" / name, run / "scores" / name
        if fa.exists() and fb.exists():
            compared.append(f"scores/{name}")
            problems += compare_csv(fa, fb)
        elif fa.exists() != fb.exists():
            problems.append(f"scores/{name}: present in only one run")
    fa, fb = fixture / "gates" / "export_status.json", run / "gates" / "export_status.json"
    if fa.exists() and fb.exists():
        compared.append("gates/export_status.json")
        ja = {k: v for k, v in _strip_json(json.loads(fa.read_text())).items()
              if k not in RELOCATED_EXPORT_KEYS}
        jb = {k: v for k, v in _strip_json(json.loads(fb.read_text())).items()
              if k not in RELOCATED_EXPORT_KEYS}
        if ja != jb:
            problems.append("export_status.json differs beyond plan_sha256")
    for name in GATE_JSONS:
        fa, fb = fixture / "gates" / name, run / "gates" / name
        if fa.exists() and fb.exists():
            compared.append(f"gates/{name}")
            problems += compare_json(fa, fb)
    fa = fixture / "config" / "protocol_fields.json"
    fb = run / "config" / "protocol_fields.json"
    if fa.exists() and fb.exists():
        compared.append("config/protocol_fields.json")
        pa = {d["field"]: d for d in json.loads(fa.read_text())}
        pb = {d["field"]: d for d in json.loads(fb.read_text())}
        if set(pa) != set(pb):
            problems.append(f"protocol fields differ: {sorted(set(pa) ^ set(pb))}")
        for k in set(pa) & set(pb):
            va, vb = _strip_json(pa[k]), _strip_json(pb[k])
            if k in RELOCATED_HASH_FIELDS:
                if va["value"] == vb["value"]:
                    problems.append(
                        f"protocol_fields.{k}: expected a relocated hash, got "
                        "identical values; the allowlist is stale")
                va = {**va, "value": "<RELOCATED>"}
                vb = {**vb, "value": "<RELOCATED>"}
            if va != vb:
                problems.append(f"protocol_fields.{k}: {va} vs {vb}")
    return problems, compared


if __name__ == "__main__":
    import sys
    problems, compared = compare_runs(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"compared {len(compared)} artifacts")
    for p in problems:
        print("DIFF:", p)
    print("RESULT:", "IDENTICAL" if not problems else f"{len(problems)} differences")
    sys.exit(0 if not problems else 1)
