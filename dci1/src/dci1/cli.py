"""DCI-1 study command line.

    python -m dci1.cli <command> [--model KEY] [--device N] ...

Commands: check, smoke, qualify, pilot, calibrate, freeze, readiness,
generate, select-primary, greedy, mask, analyze, pseudo, sensitivity,
baseline-packet, release.

Confirmatory generation (`generate`) is locked behind the §9 readiness gate:
it refuses while any gate, qualification, pilot, freeze or pending human
measurement is unresolved. That refusal is the fail-closed rule, not an
inconvenience to work around.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dci1.evidence.store import (
    DURABLE_ROOT,
    EVIDENCE_ROOT,
    append_run_record,
    mirror_to_durable,
    read_json,
    read_jsonl,
    write_json,
)
from dci1.models.adapters import MODEL_KEYS, get_model
from dci1.protocol.constants import ProtocolError, study_config
from dci1.protocol.hashing import sha
from dci1.protocol.seeds import bootstrap_seed


def model_dirs(model_key: str) -> tuple[Path, Path]:
    from dci1.evidence.layout import (durable_apparatus_dir,
                                      model_apparatus_dir)

    return model_apparatus_dir(model_key), durable_apparatus_dir(model_key)


def _print(payload) -> None:
    print(json.dumps(payload, indent=1, sort_keys=True, default=str))


def cmd_check(_args) -> int:
    """CPU protocol checks: measurement, witnesses, structure, codebook."""
    from dci1.analysis.estimators import assert_block_indexed_signatures
    from dci1.constraints.definitions import assert_parse_independence
    from dci1.constraints.witnesses import certify_composition
    from dci1.design.blocks import assert_block_plan
    from dci1.design.plan import confirmatory_blocks
    from dci1.protocol.codebook import (
        assert_constraining_checks_exist,
        assert_primary_fields,
    )
    from dci1.verifiers.boundary_suite import evaluate_suite
    from dci1.verifiers.registry import assert_blindness

    boundary = evaluate_suite()
    if boundary["failures"]:
        raise ProtocolError(f"boundary suite failed: {boundary['failures']}")
    assert_parse_independence()
    assert_blindness()
    assert_block_indexed_signatures()
    assert_primary_fields()
    assert_constraining_checks_exist()
    plan = assert_block_plan(confirmatory_blocks())
    certified = 0
    for n in (1, 2, 3):
        for cid in [f"C{i}" for i in range(1, 13)]:
            certify_composition(cid, n)
            certified += 1
        for m in (7, 8, 9, 10):
            certify_composition("B", n, m)
            certified += 1
    _print({"boundary_suite": f"{boundary['handled_as_specified']}/40",
            "block_plan": plan, "witness_certifications": certified,
            "status": "OK"})
    return 0


def cmd_smoke(_args) -> int:
    from dci1.pilot.smoke import run_smoke

    report = run_smoke()
    _print(report)
    return 0 if report["passed"] else 1


def cmd_dry_run(_args) -> int:
    from dci1.masking.dry_run import run_blind_dry_run

    report = run_blind_dry_run()
    _print(report)
    return 0 if report["passed"] else 1


def cmd_verify_evidence(args) -> int:
    from dci1.evidence.layout import PREFREEZE_PILOT_ID, StudyTree
    from dci1.evidence.verify import verify_evidence

    tree = StudyTree(model_slug=args.model,
                     freeze_id=args.freeze or PREFREEZE_PILOT_ID)
    report = verify_evidence(tree)
    _print(report)
    return 0


def reconciliation_conflicts() -> int:
    """Unresolved conflicts in the Addendum-A reconciliation (block freeze)."""
    doc = (Path(__file__).resolve().parents[2] / "docs"
           / "addendum_a_reconciliation.md")
    if not doc.exists():
        return 999
    return doc.read_text().count("| conflict (unresolved)")


def cmd_qualify(args) -> int:
    from dci1.models.qualification import qualify

    spec = get_model(args.model)
    model_dir, durable = model_dirs(args.model)
    report = qualify(spec, config=study_config(), model_dir=model_dir,
                     device=args.device)
    append_run_record(model_dir, {"event": "qualification",
                                  "verdict": report["verdict"]})
    mirror_to_durable(model_dir / "qualification", durable / "qualification")
    _print({"verdict": report["verdict"], "problems": report["problems"]})
    return 0 if report["verdict"] == "QUALIFIED" else 1


def cmd_pilot(args) -> int:
    from dci1.pilot.runner import run_pilot

    spec = get_model(args.model)
    model_dir, durable = model_dirs(args.model)
    report = run_pilot(spec, config=study_config(), model_dir=model_dir,
                       durable_dir=durable, device=args.device)
    _print({"passed": report["passed"],
            "inspected": report["inspected_quantities"],
            "conditions": report["conditions"]})
    return 0 if report["passed"] else 1


def cmd_calibrate(args) -> int:
    from dci1.calibration.gate1 import run_gate1
    from dci1.calibration.gate2 import evaluate_gate2, solo_rates
    from dci1.design.plan import calibration_cells
    from dci1.evidence.store import AppendOnceJsonl
    from dci1.generation.pools import build_pools, pool_path

    spec = get_model(args.model)
    model_dir, durable = model_dirs(args.model)
    stage_dir = model_dir / "calibration"
    cells = calibration_cells()
    build_pools(spec, cells, stream="calibration", stage_dir=stage_dir,
                config=study_config(), model_dir=model_dir,
                device=args.device)
    rows = AppendOnceJsonl(pool_path(stage_dir)).rows()
    rates = solo_rates(rows)
    write_json(stage_dir / "solo_rates.json",
               {"rates": rates["rates"], "counts": rates["counts"]})
    gate1 = run_gate1(rows, rates["per_topic_target"],
                      stage_dir / "gate1", spec.model_key,
                      human_labels_path=(Path(args.human_labels)
                                         if args.human_labels else None))
    write_json(stage_dir / "gate1.json", gate1)
    gate2 = evaluate_gate2(rates["rates"])
    write_json(stage_dir / "gate2.json", gate2)
    append_run_record(model_dir, {
        "event": "calibration", "gate1_status": gate1["status"],
        "gate2_passed": gate2["passed"],
        "selected_n": gate2.get("selected_n"),
        "selected_m": gate2.get("selected_m"),
        "references": gate2.get("references")})
    mirror_to_durable(stage_dir, durable / "calibration")
    _print({"gate1": gate1["status"], "gate2_passed": gate2["passed"],
            "n": gate2.get("selected_n"), "m": gate2.get("selected_m"),
            "references": gate2.get("references"),
            "failure_reasons": gate2.get("failure_reasons")})
    return 0 if gate2["passed"] else 1


def cmd_freeze(args) -> int:
    from dci1.design.plan import confirmatory_blocks
    from dci1.freeze.record import build_freeze_record, write_freeze
    from dci1.topics.split import split_bank

    spec = get_model(args.model)
    model_dir, durable = model_dirs(args.model)
    gate0 = read_json(model_dir / "pilot_report.json")
    gate1 = read_json(model_dir / "calibration" / "gate1.json")
    gate2 = read_json(model_dir / "calibration" / "gate2.json")
    qualification = read_json(model_dir / "qualification_report.json")
    split = split_bank()
    split_ids = {k: [t["topic_id"] for t in v] for k, v in split.items()}
    blocks = confirmatory_blocks()
    block_plan_hash = sha([{f: getattr(b, f) for f in
                            ("index", "block_id", "topic_id", "order",
                             "wording_target", "wording_added")}
                           for b in blocks])
    record = build_freeze_record(
        spec, config=study_config(), gate0=gate0, gate1=gate1, gate2=gate2,
        qualification=qualification, topic_split_ids=split_ids,
        block_plan_hash=block_plan_hash)
    if gate1.get("status") != "PASSED":
        # Gates run in order (§18): the immutable record may not be written
        # while Gate 1 is unresolved. A complete, validated PREVIEW is
        # recorded instead so the freeze content is inspectable; the real
        # write happens only once Gate 1 has passed.
        preview = model_dir / "freeze" / "freeze_preview.json"
        write_json(preview, {"PREVIEW_NOT_A_FREEZE_RECORD": True, **record})
        append_run_record(model_dir, {"event": "freeze_preview",
                                      "gate1_status": gate1.get("status")})
        _print({"preview": str(preview),
                "gate1_status": gate1.get("status"),
                "note": "immutable freeze deferred until Gate 1 passes"})
        return 1
    path = write_freeze(model_dir, record)
    append_run_record(model_dir, {"event": "freeze",
                                  "freeze_hash": record["freeze_hash"]})
    mirror_to_durable(model_dir / "freeze", durable / "freeze")
    _print({"frozen": str(path), "freeze_hash": record["freeze_hash"],
            "n": record["constraints"]["n"], "m": record["constraints"]["m"],
            "references": record["constraints"]["references"]})
    return 0


def readiness_report(model_key: str) -> dict:
    """The §9 readiness list — the single authority on unlocking generation."""
    model_dir, _ = model_dirs(model_key)
    items: dict[str, bool | str] = {}
    items["module_architecture"] = True
    items["mapping_complete"] = (Path(__file__).resolve().parents[2]
                                 / "MAPPING.md").exists()
    qual = model_dir / "qualification_report.json"
    items["no_thinking_qualified"] = (
        qual.exists() and read_json(qual).get("verdict") == "QUALIFIED")
    try:
        cmd_check(None)
        items["verifier_scoring_witness_checks"] = True
    except Exception as error:                      # noqa: BLE001
        items["verifier_scoring_witness_checks"] = f"FAILED: {error}"
    from dci1.evidence.layout import synthetic_dir

    smoke = synthetic_dir("smoke") / "smoke_report.json"
    items["synthetic_smoke_passed"] = (smoke.exists() and
                                       read_json(smoke).get("passed") is True)
    pilot = model_dir / "pilot_report.json"
    items["procedural_pilot_passed"] = (pilot.exists() and
                                        read_json(pilot).get("passed") is True)
    gate1_path = model_dir / "calibration" / "gate1.json"
    gate1_status = (read_json(gate1_path).get("status")
                    if gate1_path.exists() else "MISSING")
    items["gate1"] = gate1_status if gate1_status != "PASSED" else True
    gate2_path = model_dir / "calibration" / "gate2.json"
    items["gate2_passed"] = (gate2_path.exists() and
                             read_json(gate2_path).get("passed") is True)
    freeze_file = model_dir / "freeze" / "freeze_record.json"
    frozen = False
    if freeze_file.exists():
        try:
            from dci1.freeze.record import assert_freeze_matches, load_freeze

            record = load_freeze(model_dir)
            assert_freeze_matches(record, get_model(model_key),
                                  study_config())
            frozen = True
        except ProtocolError as error:
            frozen = f"INVALID: {error}"
    items["freeze_record"] = frozen
    items["resampling_fields_frozen"] = bool(frozen is True)
    conflicts = reconciliation_conflicts()
    items["reconciliation_zero_conflicts"] = (True if conflicts == 0
                                              else f"{conflicts} unresolved")
    dry_report = synthetic_dir("dryrun") / "dry_run_report.json"
    items["blind_dry_run_passed"] = (dry_report.exists() and
                                     read_json(dry_report).get("passed")
                                     is True)
    unlocked = all(v is True for v in items.values())
    return {"model_key": model_key, "items": items, "unlocked": unlocked}


def cmd_readiness(args) -> int:
    report = readiness_report(args.model)
    _print(report)
    return 0 if report["unlocked"] else 1


def _frozen_design(model_key: str):
    from dci1.design.plan import confirmatory_blocks, confirmatory_cells
    from dci1.freeze.record import assert_freeze_matches, load_freeze

    spec = get_model(model_key)
    model_dir, _ = model_dirs(model_key)
    record = load_freeze(model_dir)
    assert_freeze_matches(record, spec, study_config())
    n = record["constraints"]["n"]
    m = record["constraints"]["m"]
    references = tuple(record["constraints"]["references"])
    return (spec, model_dir, record, n, m, references,
            confirmatory_cells(n, m, references), confirmatory_blocks())


def cmd_generate(args) -> int:
    report = readiness_report(args.model)
    if not report["unlocked"]:
        _print({"refused": "confirmatory generation is locked; the §9 "
                           "readiness gate is not satisfied",
                "items": report["items"]})
        return 1
    from dci1.generation.pools import build_pools

    (spec, model_dir, record, n, m, references, cells, _blocks) = \
        _frozen_design(args.model)
    pool_report = build_pools(spec, cells, stream="confirmatory",
                              stage_dir=model_dir / "confirmatory",
                              config=study_config(), model_dir=model_dir,
                              device=args.device)
    _, durable = model_dirs(args.model)
    mirror_to_durable(model_dir / "confirmatory" / "pool",
                      durable / "confirmatory" / "pool")
    _print(pool_report)
    return 0


def cmd_select_primary(args) -> int:
    from dci1.evidence.integrity import validate_accepted
    from dci1.resampling.primary import build_primary, load_accepted

    (spec, model_dir, record, n, m, references, cells, _blocks) = \
        _frozen_design(args.model)
    stage_dir = model_dir / "confirmatory"
    result = build_primary(spec, cells, stream="confirmatory",
                           stage_dir=stage_dir, config=study_config())
    accepted = load_accepted(stage_dir)
    validate_accepted(
        accepted, cells, spec, stream="confirmatory", config=study_config(),
        frozen_backend_config_hash=record["backend"]["backend_config_hash"],
        frozen_verifier_hash=record["verifiers"]["source_hash"])
    _, durable = model_dirs(args.model)
    mirror_to_durable(stage_dir / "primary", durable / "confirmatory" /
                      "primary")
    _print(result)
    return 0


def cmd_greedy(args) -> int:
    from dci1.design.plan import greedy_cells
    from dci1.generation.pools import build_pools

    (spec, model_dir, record, n, m, references, _cells, _blocks) = \
        _frozen_design(args.model)
    cells = greedy_cells(n, m, references)
    report = build_pools(spec, cells, stream="greedy",
                         stage_dir=model_dir / "greedy",
                         config=study_config(), model_dir=model_dir,
                         device=args.device)
    _print(report)
    return 0


def cmd_mask(args) -> int:
    from dci1.masking.mask import construct_mask
    from dci1.resampling.primary import load_accepted

    (spec, model_dir, record, n, m, references, cells, _blocks) = \
        _frozen_design(args.model)
    accepted = load_accepted(model_dir / "confirmatory")
    result = construct_mask(accepted, model_dir / "analysis", model_dir)
    _print(result)
    return 0


def cmd_analyze(args) -> int:
    from dci1.analysis.run import analyze
    from dci1.masking.mask import unmask

    (spec, model_dir, record, n, m, references, cells, blocks) = \
        _frozen_design(args.model)
    analysis_dir = model_dir / "analysis"
    masked_rows = read_jsonl(analysis_dir / "masked_accepted.jsonl")
    seed = bootstrap_seed(study_config().bootstrap_seed, spec.model_id,
                          "confirmatory")
    if args.phase == "masked":
        result = analyze(masked_rows, blocks, n=n, m=m,
                         references=references, bootstrap_seed_value=seed,
                         masked=True)
        write_json(analysis_dir / "masked_result.json", result)
    else:
        true_rows = unmask(masked_rows, analysis_dir / "mask_key.json",
                           model_dir)
        result = analyze(true_rows, blocks, n=n, m=m,
                         references=references, bootstrap_seed_value=seed,
                         masked=False)
        write_json(analysis_dir / "unmasked_result.json", result)
    _, durable = model_dirs(args.model)
    mirror_to_durable(analysis_dir, durable / "analysis")
    _print({"status": result["status"], "phase": args.phase})
    return 0


def cmd_pseudo(args) -> int:
    from dci1.analysis.sensitivity import point_estimates, run_sensitivity
    from dci1.analysis.tables import score_table
    from dci1.resampling.primary import load_accepted

    (spec, model_dir, record, n, m, references, cells, blocks) = \
        _frozen_design(args.model)
    stage_dir = model_dir / "confirmatory"
    primary_scored = score_table(load_accepted(stage_dir), blocks, n=n, m=m,
                                 references=references)
    summary = run_sensitivity(
        spec, cells, blocks, stage_dir=stage_dir, config=study_config(),
        n=n, m=m, references=references,
        primary_estimates=point_estimates(primary_scored),
        bootstrap_seed_value=bootstrap_seed(
            study_config().bootstrap_seed, spec.model_id, "sensitivity"),
        pseudo_runs=args.runs)
    _print({"pseudo_runs": summary["pseudo_runs"],
            "primary_invariant": summary["primary_invariant"]})
    return 0


def cmd_baseline_packet(args) -> int:
    from dci1.reports.human_baseline import build_packet

    (spec, model_dir, record, n, m, references, _cells, _blocks) = \
        _frozen_design(args.model)
    result = build_packet(model_dir / "human", n=n, m=m,
                          reference=references[0], model_key=spec.model_key)
    _print(result)
    return 0


def cmd_release(args) -> int:
    from dci1.reports.release import release_manifest

    model_dir, _ = model_dirs(args.model)
    _print(release_manifest(model_dir))
    return 0


COMMANDS = {
    "check": cmd_check, "smoke": cmd_smoke, "dry-run": cmd_dry_run,
    "verify-evidence": cmd_verify_evidence, "qualify": cmd_qualify,
    "pilot": cmd_pilot, "calibrate": cmd_calibrate, "freeze": cmd_freeze,
    "readiness": cmd_readiness, "generate": cmd_generate,
    "select-primary": cmd_select_primary, "greedy": cmd_greedy,
    "mask": cmd_mask, "analyze": cmd_analyze, "pseudo": cmd_pseudo,
    "baseline-packet": cmd_baseline_packet, "release": cmd_release,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dci1", description=__doc__)
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--model", choices=list(MODEL_KEYS))
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--phase", choices=["masked", "unmasked"],
                        default="masked")
    parser.add_argument("--runs", type=int, default=None)
    parser.add_argument("--human-labels", default=None)
    parser.add_argument("--freeze", default=None,
                        help="freeze_id of the addendum evidence tree")
    args = parser.parse_args(argv)
    needs_model = args.command not in ("check", "smoke", "dry-run")
    if needs_model and not args.model:
        parser.error(f"{args.command} requires --model")
    try:
        return COMMANDS[args.command](args)
    except ProtocolError as error:
        print(f"FAIL-CLOSED: {error}", file=sys.stderr)
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
