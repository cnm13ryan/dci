"""Human-vs-verifier validation report and sequential stopping decision.

    .venv/bin/python experiments/human_review/validation_report.py \
        --records experiments/human_review/records/calibration_Bryan.jsonl \
        --records experiments/human_review/records/extension1_Bryan.jsonl \
        --json experiments/human_review/validation_report.json

With no --records the report reads every non-reveal record file in
``experiments/human_review/records/``.

Reports the full human x verifier table, per-class error rates and
one-sided 95% Wilson upper bounds, overall accuracy, coverage and
abstentions, the discordant items, and how many further labels each class
needs to meet the 10% and 5% bounds.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import validation                                  # noqa: E402

RECORDS_DIR = HERE / "records"


def default_records() -> list[Path]:
    if not RECORDS_DIR.exists():
        return []
    return [p for p in sorted(RECORDS_DIR.glob("*.jsonl"))
            if not p.name.startswith("reveals_")
            and p.name != "digests.jsonl"]


def _pct(value):
    return "n/a" if value is None else f"{value:.1%}"


def render(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "# Human validation of the deterministic verifier",
        "",
        f"- criterion: {report['criterion']['quantity']}",
        f"- interval: {report['criterion']['interval']}; registered "
        f"target {report['criterion']['registered_target']:.0%}, "
        f"strengthened target "
        f"{report['criterion']['strengthened_target']:.0%}",
        f"- the bound is claimed on the "
        f"**{report['criterion']['claim_component']}** component only",
        "",
        f"- items presented: {counts['presented']}; human records: "
        f"{counts['records']} (response rate "
        f"{_pct(counts['response_rate'])})",
        f"- labelled: {counts['labelled']}; abstentions (UNSURE): "
        f"{counts['abstentions']}; coverage "
        f"{_pct(counts['coverage'])}",
        f"- overall accuracy (human == verifier, over labelled): "
        f"{_pct(report['overall_accuracy'])}",
        "",
        "## Human x verifier",
        "",
        "| human | verifier | count |",
        "|---|---|---|",
    ]
    for key, count in sorted(report["table_human_x_verifier"].items()):
        human, cls = key.split("|")
        lines.append(f"| {human} | {cls} | {count} |")

    lines += ["", "## Per-class bounds", "",
              "| component | verifier class | cases | disagreements | "
              "error rate | 95% Wilson upper | <=10% | <=5% | more for "
              "10% | more for 5% |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    # `--` marks rows no target applies to: the purposive boundary
    # component is an adversarial stress probe, not a population sample,
    # and `pooled` mixes the two designs.
    for component in ("representative", "boundary", "pooled"):
        for cls in ("pass", "fail"):
            b = report["by_component"][component][cls]

            def cell(key, fmt):
                if not b.get("target_applies", True) or not b["cases"]:
                    return "--"
                return fmt(b[key])
            lines.append(
                f"| {component} | {cls} | {b['cases']} | "
                f"{b['disagreements']} | {_pct(b['error_rate'])} | "
                f"{_pct(b['wilson_upper_one_sided_95'])} | "
                f"{cell('meets', lambda m: 'yes' if m['0.10'] else 'no')} | "
                f"{cell('meets', lambda m: 'yes' if m['0.05'] else 'no')} | "
                f"{cell('additional_labels_required', lambda a: a['0.10'])} | "
                f"{cell('additional_labels_required', lambda a: a['0.05'])} |")

    lines += ["", "## Discordant items", ""]
    if not report["discordant"]:
        lines.append("None: the human and the verifier agree on every "
                     "labelled item.")
    else:
        lines += ["| id | human | verifier | n | s0 | component | "
                  "boundary category |", "|---|---|---|---|---|---|---|"]
        for d in report["discordant"]:
            lines.append(
                f"| {d['id']} | {d['human']} | {d['verifier_class']} | "
                f"{d['target_n']} | {d['s0_count']} | {d['component']} | "
                f"{d['boundary_category']} |")

    op = report["operational"]
    lines += ["", "## Operational channel (never merged into a label)", "",
              f"- {op['note']}",
              f"- human abstentions: {op['human_abstentions']}",
              f"- pool finish_reason over reviewed items: "
              f"{op['pool_finish_reason']}",
              f"- registered judge statuses over reviewed items: "
              f"{op['registered_judge_statuses']}"]

    stop = report["stopping"]
    lines += ["", "## Sequential stopping decision", "",
              f"- **{stop['decision']}** — {stop['interpretation']}"]
    for cls, entry in stop["per_class"].items():
        lines.append(
            f"- verifier-{cls}: {entry['cases']} cases, "
            f"{entry['disagreements']} disagreements; "
            f"10% {entry['0.10']['status']} "
            f"(+{entry['0.10']['additional_labels_required']}), "
            f"5% {entry['0.05']['status']} "
            f"(+{entry['0.05']['additional_labels_required']})")
    lines.append(f"- next batch representative targets: "
                 f"{stop['next_batch_representative_targets']}")
    if stop["budget"]:
        b = stop["budget"]
        lines.append(
            f"- projected total labels {b['projected_total_labels']} "
            f"vs budget {b['max_total_labels']} "
            f"({'within' if b['within_budget'] else 'OVER'})")

    integrity = report["integrity"]
    lines += ["", "## Integrity", "",
              *[f"- record dir: pins {d['pins']}, chains {d['chains']}"
                for d in integrity["records"]],
              f"- sealed reserved set sha256: "
              f"{integrity['sealed_set_sha256']} (untouched; 0 sealed ids "
              f"labelled)"]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", action="append", type=Path)
    ap.add_argument("--allow-synthetic", action="store_true")
    ap.add_argument("--max-total-labels", type=int, default=150)
    ap.add_argument("--json", type=Path,
                    help="also write the machine-readable report here")
    args = ap.parse_args()

    records = args.records or default_records()
    if not records:
        raise SystemExit("no human records found")
    report = validation.build_report(
        review_dir=HERE, record_paths=records,
        allow_synthetic=args.allow_synthetic,
        max_total_labels=args.max_total_labels)
    if args.json:
        args.json.write_text(json.dumps(report, indent=1) + "\n")
    print(render(report))


if __name__ == "__main__":
    main()
