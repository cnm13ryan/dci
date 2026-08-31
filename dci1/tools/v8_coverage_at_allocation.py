#!/usr/bin/env python3
"""What the confirmatory allocation amendment does to already-recorded
SPECTRUM coverage verdicts, stated rather than left implicit.

`spectrum.coverage`'s condition 4 asks that the selected design's projected
SE of §11.8's common slope be at most `SPECTRUM_MAX_SE_BETA`, computed at
the confirmatory blocks a frame will hold. That block count is the design's,
so §4e's amendment (`rules.CONFIRMATORY_FRAME_OFFSETS`, three passes, 288
blocks per frame) moves it — and a projected SE falls as 1/sqrt(blocks), so
condition 4 becomes reachable for designs with less within-family leverage.
The threshold does not move; the allocation the threshold is evaluated at
does.

r8 and r9 were run and signed at one pass. **They are not recomputed, not
reopened and not overwritten**: this file reads their signed Gate-3 records
and says, for each frame, what condition 4 would have said at the amended
allocation, so that the change is on the record instead of being discovered
later. `projected_se_beta` is exact under rescaling --- the within-family
leverage is a property of the selected points and does not move with the
block count, and `se = se_point_at(blocks) * sqrt(1 - rho) / sqrt(leverage)`
--- so the recomputation uses the recorded leverage and the production
function, not a re-derivation.

Nothing here reads a composed outcome; Gate 3 has none to offer.

    python3 tools/v8_coverage_at_allocation.py --roots dci1v8-pilot-r8 dci1v8-pilot-r9

Writes `reports/dci1v8dev/coverage_at_<blocks>.{md,json}`.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dci1v8dev import rules as R                                    # noqa: E402
from dci1v8dev.run import eligibility as EL                         # noqa: E402
from dci1v8dev.run import stages as S                               # noqa: E402
from dci1v8dev.spectrum import precision                            # noqa: E402
from dci1v8dev.spectrum.coverage import FRAME_COVERAGE_RULE         # noqa: E402

LABEL = "PROJECTION_NOT_REGISTERED_FOR_INFERENCE"


def gate3_records(root: pathlib.Path) -> dict[str, Any]:
    out = {}
    base = root / "evidence" / "dci1v8"
    for model_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        path = model_dir / S.STAGE_GATE3 / "gate3_references.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text())
        out[model_dir.name] = doc.get("payload", doc)
    return out


def restate(record: dict[str, Any], *, n_blocks: int) -> list[dict[str, Any]]:
    rows = []
    for key, entry in sorted(record.get("by_frame", {}).items(),
                             key=lambda kv: int(kv[0])):
        survival = entry.get("survival")
        if not survival:
            rows.append({"frame": int(key), "state": entry.get("state"),
                         "recorded_status": None, "note": "no operating point"})
            continue
        cov_proj_blocks = survival.get("n_blocks_projected")
        se_recorded = survival.get("projected_se_beta")
        leverage = entry.get("coverage_leverage")
        row: dict[str, Any] = {
            "frame": int(key),
            "state": entry.get("state"),
            "recorded_n_blocks": cov_proj_blocks,
            "recorded_se_beta": se_recorded,
            "recorded_identified": survival.get("coverage_identified"),
            "recorded_status": survival.get("coverage_status"),
            "recorded_reasons": list(survival.get("coverage_reasons") or []),
            "amended_n_blocks": n_blocks,
            # r8/r9 predate the field, so it is recomputed here by the
            # production rule from the survival facts they do record --- the
            # same function ``survival_summary`` now calls.
            "local_supported": EL.local_support(
                survival, frame=int(key))["local_supported"],
        }
        if se_recorded is None or not cov_proj_blocks:
            row["amended_se_beta"] = None
            row["condition_4_at_amended"] = None
        else:
            scaled = se_recorded * (precision.se_point_at(n_blocks)
                                    / precision.se_point_at(cov_proj_blocks))
            row["amended_se_beta"] = scaled
            row["condition_4_at_amended"] = scaled <= FRAME_COVERAGE_RULE.max_se_beta
        # Only condition 4 moves with the allocation. Every other refusal is
        # a statement about the selected points and is unchanged.
        other = [r for r in row["recorded_reasons"]
                 if not r.startswith("projected SE(beta)")]
        row["reasons_not_about_the_allocation"] = other
        row["amended_identified"] = (
            None if row["condition_4_at_amended"] is None
            else (not other) and row["condition_4_at_amended"])
        row["status_changes"] = (row["amended_identified"] is not None
                                 and bool(row["amended_identified"])
                                 != bool(row["recorded_identified"]))
        rows.append(row)
    return rows


def render(payload: dict[str, Any]) -> str:
    n = payload["amended_blocks_per_frame"]
    lines = [
        f"# DCI-1 v8 — recorded SPECTRUM coverage restated at {n} blocks per frame",
        "",
        f"Produced by `tools/v8_coverage_at_allocation.py`. **Projection only**, "
        f"labelled `{LABEL}`. r8 and r9 were run and signed at "
        f"{payload['single_pass_blocks_per_frame']} blocks per frame (one "
        "confirmatory pass); their records are read, never rewritten. This "
        "file exists so that §4e's allocation amendment does not silently "
        "change what an existing SPECTRUM verdict would have been.",
        "",
        "Only **condition 4** of `spectrum.coverage` moves with the block "
        f"count: `SPECTRUM_MAX_SE_BETA` = {FRAME_COVERAGE_RULE.max_se_beta} is "
        "unchanged, the within-family leverage of a selected design is "
        "unchanged, and the projected SE falls as 1/√blocks. Every other "
        "refusal — points, families, offsets, span, coordinate SE — is a "
        "statement about the selected points and is reproduced verbatim.",
        "",
        "The **LOCAL** arm reads no block count (`local_validity`, §13.8's "
        "core kernel, §13.15's family count, `admissible_backups`), so no "
        "LOCAL support verdict in this table moves. It is shown for contrast.",
        "",
        "| root | model | frame | recorded status | SE(β) recorded | SE(β) at "
        f"{n} | condition 4 at {n} | other refusals | verdict changes? | LOCAL |",
        "|---|---|---|---|---:|---:|---|---|---|---|",
    ]
    changed = 0
    for root, models in sorted(payload["by_root"].items()):
        for model, rows in sorted(models.items()):
            for r in rows:
                if r.get("recorded_status") is None:
                    lines.append(f"| `{root}` | `{model}` | f{r['frame']} | "
                                 f"{r.get('note') or '—'} | — | — | — | — | no | — |")
                    continue
                changed += bool(r["status_changes"])
                other = r["reasons_not_about_the_allocation"]
                lines.append(
                    f"| `{root}` | `{model}` | f{r['frame']} | "
                    f"`{r['recorded_status']}` | "
                    f"{r['recorded_se_beta']:.4f} | {r['amended_se_beta']:.4f} | "
                    f"{'meets' if r['condition_4_at_amended'] else 'fails'} | "
                    f"{len(other)}{' (' + '; '.join(o.split(';')[0] for o in other[:2]) + ')' if other else ''} | "
                    f"{'**YES**' if r['status_changes'] else 'no'} | "
                    f"{'supported' if r['local_supported'] else 'unsupported'} |")
    lines += [
        "",
        f"**{changed} of the recorded frame verdicts would differ** at the "
        "amended allocation. A frame whose verdict changes was refused for "
        "the projected slope precision alone; a frame that stays refused was "
        "refused for something the allocation cannot buy.",
        "",
        "These frames are **not** re-verdicted. r8 and r9 stand as run: their "
        "SPECTRUM verdicts are conservative with respect to the amended "
        "design, and the next replication measured under it will say what it "
        "says on its own record.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--evidence", default=str(ROOT / "evidence"))
    args = ap.parse_args(argv)
    n = R.CONFIRMATORY_BLOCKS_PER_FRAME
    payload: dict[str, Any] = {
        "label": LABEL,
        "amended_blocks_per_frame": n,
        "amended_passes": R.CONFIRMATORY_FRAME_PASSES,
        "single_pass_blocks_per_frame": R.CONFIRMATORY_MAX_BLOCKS_PER_FRAME
        // len(S.FRAMES),
        "max_se_beta": FRAME_COVERAGE_RULE.max_se_beta,
        "by_root": {},
    }
    for name in args.roots:
        root = pathlib.Path(args.evidence) / name
        payload["by_root"][name] = {
            model: restate(rec, n_blocks=n)
            for model, rec in gate3_records(root).items()}
    out_dir = ROOT / "reports" / "dci1v8dev"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"coverage_at_{n}.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n")
    md = out_dir / f"coverage_at_{n}.md"
    md.write_text(render(payload))
    print(f"wrote {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
