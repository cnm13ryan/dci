#!/usr/bin/env python3
"""Post-confirmatory audit: are the scored rows the v8.1 analysis read the rows
that generation produced?

The signed CONFIRMATORY_GENERATION record binds the row count, the identity
completeness and the verifier and wording hashes, not the content of the
``scored.jsonl`` files, and the frozen analysis re-counts rows without
authenticating their content (dci1v8dev/confirm/analysis.py,
``analysis_payload``). The frozen code is not amended. This tool asks, on the
stored evidence, whether any scored row could differ from what generation
wrote. It reads the evidence root read-only and writes one JSON report.

Per backend run (every current ``scored.jsonl`` of every model):

1. **Mirror.** The SHA-256 of ``scored.jsonl``, ``rows.jsonl`` and
   ``design.jsonl`` equals the copy under ``durable/``, which was written when
   the generation stage completed.
2. **Time.** The modification time and the inode change time of every
   ``scored.jsonl`` and ``rows.jsonl`` precede the signed generation record's
   ``recorded_at``. A content write moves the change time, and the change time
   cannot be set back without changing the system clock.
3. **Derivation.** Row by row, the scored row, the backend's raw row
   (``rows.jsonl``) and the planned design row carry the same ``row_id`` and
   ``generation_identity`` in the same order. The scored ``raw_response``,
   ``truncated``, ``finish_reason`` and ``token_count`` equal the backend's
   ``final_answer``, ``answer_truncated``, ``finish_reason`` and
   ``total_generated_tokens``. The row's verifier and wording hashes equal the
   signed generation record's. ``observation_identity`` recomputes.
4. **Rescore.** The frozen v8 verifier (``score_generation``) applied to the
   backend's answer reproduces every stored score field and the row's
   ``empty``, ``word_count`` and ``in_stem_band``.

Per model, the rows on disk are then re-read the way the analysis reads them.
Every per-block (non-refit) member of every per-frame family is re-formed, and
its mean must equal the estimate in the signed CONFIRMATORY_ANALYSIS record.

    dci1/.venv/bin/python dci1/tools/v8p1_scored_row_authentication_audit.py \\
        --root dci1/evidence/dci1v8p1-confirm \\
        --out dci1/reports/dci1v8dev/postconfirm/audits/scored_row_authentication.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))

from dci1v4.engine.signing import verify_signed                     # noqa: E402
from dci1v4.errors import IntegrityError                             # noqa: E402
from dci1v4.protocol.hashing import sha_obj                          # noqa: E402
from dci1v7.protocol import constants as C                           # noqa: E402
from dci1v7.verifiers.constraints import Constraint                  # noqa: E402
from dci1v8dev.confirm.analysis import frame_members, frame_table    # noqa: E402
from dci1v8dev.run.context import current_files                      # noqa: E402
from dci1v8dev.verifiers.compliance import score_generation          # noqa: E402

MODELS = ("qwen3-4b", "qwen3-4b-instruct-2507", "gemma-3n-e2b-it", "gemma-3n-e4b-it")
STUDY_ID = "dci1v8"
SCORE_FIELDS = ("kind", "severity", "statistic", "passed", "graded", "non_vacuous",
                "vacuous_pass", "present", "position", "processing_failure")
EXAMPLES = 5


def signed(root: Path, model: str, stage: str, name: str) -> tuple[dict[str, Any], str]:
    rec = json.loads((root / "evidence" / STUDY_ID / model / stage / "records" / name).read_text())
    payload = verify_signed(rec, root / "evidence" / STUDY_ID / "keys" / "signing.key",
                            where=f"{model}:{stage}")
    if payload.get("study_id") != STUDY_ID or payload.get("layer") != "confirm":
        raise IntegrityError(f"{model}:{stage} is not a {STUDY_ID} confirmatory record")
    return payload, rec["record_hash"]


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def constraint(kind: str, severity: int) -> Constraint:
    for kw in ({}, {"extended": True}, {"reserve": True}):
        try:
            return Constraint(kind, int(severity), **kw)
        except Exception:                               # noqa: BLE001 - try the next grid
            continue
    raise IntegrityError(f"{kind}:{severity} is on no registered grid")


def _init() -> None:
    try:
        os.nice(19)
    except OSError:                                     # pragma: no cover
        pass


def audit_run(task: tuple[str, str, str, str, float]) -> dict[str, Any]:
    evidence_dir, durable_dir, verifier_hash, wording_hash, recorded_at = task
    ev, du = Path(evidence_dir), Path(durable_dir)
    out: dict[str, Any] = {"run": str(ev.name), "checks": {}, "failures": {}, "examples": {}}

    def fail(check: str, detail: Any) -> None:
        out["failures"][check] = out["failures"].get(check, 0) + 1
        ex = out["examples"].setdefault(check, [])
        if len(ex) < EXAMPLES:
            ex.append(detail)

    for name in ("scored.jsonl", "rows.jsonl", "design.jsonl"):
        a, b = sha256(ev / name), sha256(du / name)
        out["checks"][f"mirror:{name}"] = {"evidence_sha256": a, "durable_sha256": b}
        if a is None or a != b:
            fail("mirror", {"file": name, "evidence": a, "durable": b})
    for name in ("scored.jsonl", "rows.jsonl"):
        st = (ev / name).stat()
        out["checks"][f"time:{name}"] = {"mtime": st.st_mtime, "ctime": st.st_ctime}
        if not (st.st_mtime <= recorded_at and st.st_ctime <= recorded_at):
            fail("time", {"file": name, "mtime": st.st_mtime, "ctime": st.st_ctime,
                          "generation_recorded_at": recorded_at})

    scored = [json.loads(x) for x in (ev / "scored.jsonl").read_text().splitlines() if x.strip()]
    raw = [json.loads(x) for x in (ev / "rows.jsonl").read_text().splitlines() if x.strip()]
    design = [json.loads(x) for x in (ev / "design.jsonl").read_text().splitlines() if x.strip()]
    out["rows"] = len(scored)
    if not (len(scored) == len(raw) == len(design)):
        fail("row_counts", {"scored": len(scored), "raw": len(raw), "design": len(design)})
    for s, r, d in zip(scored, raw, design):
        rid = s.get("row_id")
        if not (rid == r.get("row_id") == d.get("row_id")):
            fail("row_id", {"scored": rid, "raw": r.get("row_id"), "design": d.get("row_id")})
        if not (s.get("generation_identity") == r.get("generation_identity") == d.get("generation_identity")):
            fail("generation_identity", rid)
        text = r.get("final_answer") or ""
        if s.get("raw_response") != text:
            fail("text", rid)
        if (bool(s.get("truncated")) != bool(r.get("answer_truncated"))
                or s.get("finish_reason") != r.get("finish_reason")
                or s.get("token_count") != r.get("total_generated_tokens")):
            fail("generation_fields", rid)
        if s.get("verifier_hash") != verifier_hash or s.get("wording_hash") != wording_hash:
            fail("instrument_hashes", rid)
        labels = sorted(f"{x['kind']}:{x['severity']}" for x in s["scores"])
        if sha_obj({"generation": s["generation_identity"], "verifier_hash": s["verifier_hash"],
                    "instances": labels}) != s.get("observation_identity"):
            fail("observation_identity", rid)
        present = sorted((x for x in s["scores"] if x["present"]), key=lambda x: x["position"])
        absent = [x for x in s["scores"] if not x["present"]]
        try:
            g = score_generation(
                text, present=[constraint(x["kind"], x["severity"]) for x in present],
                absent=[constraint(x["kind"], x["severity"]) for x in absent],
                truncated=bool(r.get("answer_truncated")), finish_reason=r.get("finish_reason"),
                token_count=r.get("total_generated_tokens"))
        except Exception as exc:                        # noqa: BLE001 - a refusal is a finding
            fail("rescore_error", {"row_id": rid, "error": repr(exc)})
            continue
        stored = [{k: x[k] for k in SCORE_FIELDS} for x in present + absent]
        fresh = [{k: getattr(c, k) for k in SCORE_FIELDS} for c in g.scores]
        if stored != fresh:
            fail("rescore_scores", rid)
        if (g.empty, g.word_count, g.in_stem_band) != (s.get("empty"), s.get("word_count"), s.get("in_stem_band")):
            fail("rescore_row_flags", rid)
    return out


def estimates_from_rows(root: Path, model: str, analysis: dict[str, Any], freeze: dict[str, Any],
                        n_rows: int) -> dict[str, Any]:
    run_root = root / "evidence" / STUDY_ID / model / "CONFIRMATORY_GENERATION" / "backend_runs"
    rows: list[dict[str, Any]] = []
    for path in current_files(run_root, "scored.jsonl"):
        rows.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    if len(rows) != n_rows:
        raise IntegrityError(f"{model}: {len(rows)} rows on disk, the record says {n_rows}")
    design = freeze["design"]
    frames = {int(w): e for w, e in design["frames"].items()}
    compared = mismatched = 0
    examples: list[dict[str, Any]] = []
    for w, e in sorted(frames.items()):
        t = frame_table(rows, w, m_draws=int(design["draws"]))
        for cfg in C.CONFIGURATIONS:
            members = frame_members(t, e, cfg)
            members.pop("_spectrum_point", None)
            recorded = analysis["frames"][str(w)]["configurations"][cfg]
            for family, fm in members.items():
                for name, vec in fm.items():
                    if callable(vec):
                        continue
                    rec = ((recorded.get(family) or {}).get("members") or {}).get(name)
                    if rec is None:
                        continue
                    compared += 1
                    mean = sum(vec) / len(vec)
                    if not math.isclose(mean, rec["estimate"], rel_tol=0.0, abs_tol=1e-12):
                        mismatched += 1
                        if len(examples) < EXAMPLES:
                            examples.append({"frame": w, "configuration": cfg, "family": family,
                                             "member": name, "from_rows": mean, "recorded": rec["estimate"]})
    return {"members_compared": compared, "mismatched": mismatched, "examples": examples}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="*", default=list(MODELS))
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    root, out = Path(args.root).resolve(), Path(args.out).resolve()
    report: dict[str, Any] = {"audit": "scored-row authentication", "evidence_root": str(root), "models": {}}
    for model in args.models:
        t0 = time.time()
        gen, gen_hash = signed(root, model, "CONFIRMATORY_GENERATION", "confirmatory_generation.json")
        ana, ana_hash = signed(root, model, "CONFIRMATORY_ANALYSIS", "confirmatory_analysis.json")
        freeze, freeze_hash = signed(root, model, "FROZEN", "freeze.json")
        if ana["inputs"]["generation_record_hash"] != gen_hash or ana["inputs"]["freeze_hash"] != freeze_hash:
            raise IntegrityError(f"{model}: the analysis record does not name these records")
        recorded_at = datetime.fromisoformat(gen["recorded_at"]).timestamp()
        ev_root = root / "evidence" / STUDY_ID / model / "CONFIRMATORY_GENERATION" / "backend_runs"
        du_root = root / "durable" / STUDY_ID / model / "CONFIRMATORY_GENERATION" / "backend_runs"
        tasks = [(str(p.parent), str(du_root / p.parent.relative_to(ev_root)), gen["verifier_hash"],
                  gen["wording_hash"], recorded_at)
                 for p in current_files(ev_root, "scored.jsonl")]
        with Pool(args.workers, initializer=_init) as pool:
            runs = pool.map(audit_run, tasks, chunksize=1)
        failures: dict[str, int] = {}
        for r in runs:
            for k, v in r["failures"].items():
                failures[k] = failures.get(k, 0) + v
        n_rows = sum(r.get("rows", 0) for r in runs)
        report["models"][model] = {
            "record_hashes": {"CONFIRMATORY_GENERATION": gen_hash, "CONFIRMATORY_ANALYSIS": ana_hash,
                              "FROZEN": freeze_hash},
            "generation_recorded_at": gen["recorded_at"], "analysis_recorded_at": ana.get("recorded_at"),
            "runs": len(runs), "rows_audited": n_rows, "generation_record_rows": gen["n_rows"],
            "failures": failures,
            "failing_runs": [{k: r[k] for k in ("run", "failures", "examples")} for r in runs if r["failures"]],
            "run_checks": {r["run"]: r["checks"] for r in runs},
            "estimates_from_rows": estimates_from_rows(root, model, ana, freeze, int(gen["n_rows"])),
            "seconds": round(time.time() - t0, 1)}
        print(model, "rows", n_rows, "failures", failures,
              "estimates", {k: v for k, v in report["models"][model]["estimates_from_rows"].items()
                            if k != "examples"},
              report["models"][model]["seconds"], "s", flush=True)
    ms = report["models"].values()
    report["summary"] = {
        "models": len(report["models"]),
        "runs": sum(m["runs"] for m in ms),
        "rows_audited": sum(m["rows_audited"] for m in ms),
        "rows_match_generation_records": all(m["rows_audited"] == m["generation_record_rows"] for m in ms),
        "failures": {k: sum(m["failures"].get(k, 0) for m in ms)
                     for k in sorted({k for m in ms for k in m["failures"]})},
        "members_compared_to_record": sum(m["estimates_from_rows"]["members_compared"] for m in ms),
        "members_mismatched": sum(m["estimates_from_rows"]["mismatched"] for m in ms),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
