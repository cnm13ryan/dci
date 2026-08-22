"""§10 source manifest: every artifact these diagnostics read, with its hash,
producing stage and registration status. Writes 00_source_manifest.json.
"""
import json, sys, pathlib, hashlib
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4.models.registry import MODEL_KEYS
from dci1v4r4.engine.context import registered_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.protocol import constants as C

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "00_source_manifest.json"
ctx = registered_context()


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(path, stage, status, note=""):
    p = pathlib.Path(path)
    d = {"path": str(p.relative_to(DCI1.parent)), "producing_stage": stage,
         "status": status, "exists": p.exists()}
    if p.exists():
        d["sha256"] = sha(p)
        d["bytes"] = p.stat().st_size
        if p.suffix == ".json":
            try:
                j = json.loads(p.read_text())
                if isinstance(j, dict):
                    for k in ("record_hash", "signature"):
                        if k in j:
                            d[k] = j[k]
            except Exception:
                pass
    if note:
        d["note"] = note
    return d


items = []
for m in MODEL_KEYS:
    t = model_tree(ctx, m)
    for stage in C.STAGE_SEQUENCE:
        rp = t.stage_record(stage)
        if rp.exists():
            items.append(entry(rp, stage, "REGISTERED (signed stage record)"))
    if t.terminal_report.exists():
        items.append(entry(t.terminal_report, "TERMINAL",
                           "REGISTERED (signed terminal report)"))
    root = t.root
    for sub in sorted(root.rglob("scored.jsonl")):
        items.append(entry(sub, sub.relative_to(root).parts[0],
                           "REGISTERED (scored generation rows)"))
    for sub in sorted(root.rglob("resolved.jsonl")):
        items.append(entry(sub, sub.relative_to(root).parts[0],
                           "REGISTERED (resolved rows; the analysis input)"))
    for sub in sorted(root.rglob("rows.jsonl")):
        items.append(entry(sub, sub.relative_to(root).parts[0],
                           "REGISTERED (raw generation rows)"))
for name, note in [
        ("final_results.json", "assembled from signed UNMASKED_ANALYSIS records"),
        ("prefreeze_audit.json", "assembled from signed records"),
        ("post_freeze_delta.json", "re-assembles the freeze under current code"),
        ("evidence_manifest.json", "content manifest of the evidence tree"),
        ("durability.json", "§26 durability gate"),
        ("backend_provenance.json", "§18.1 provenance fields"),
        ("EXECUTION_REPORT.md", "prose report")]:
    items.append(entry(DCI1 / "reports" / "dci1v4r4" / name, "reporting tool",
                       "PRE-REGISTERED DIAGNOSTIC (derived artifact)", note))
items.append(entry(DCI1 / "reports" / "dci1v4r4" /
                   "SCIENTIFIC_FOLLOWUP_EVIDENCE.md",
                   "followup evidence gathering",
                   "POST-HOC DIAGNOSTIC (this report)"))
for p in sorted(HERE.glob("*.json")):
    if p.name == OUT.name:
        continue
    items.append(entry(p, "followup diagnostic script",
                       "POST-HOC DIAGNOSTIC (produced by this task)"))
for p in sorted(HERE.glob("_*.py")):
    items.append(entry(p, "followup diagnostic script",
                       "POST-HOC DIAGNOSTIC (script, produced by this task)"))

SOURCE = ["src/dci1v4r4/stages/selection.py", "src/dci1v4r4/stages/gates.py",
          "src/dci1v4r4/stages/freeze.py", "src/dci1v4r4/stages/confirmatory.py",
          "src/dci1v4r4/analysis/estimators.py",
          "src/dci1v4r4/analysis/observations.py",
          "src/dci1v4r4/analysis/claims.py", "src/dci1v4r4/analysis/masking.py",
          "src/dci1v4r4/analysis/bootstrap.py",
          "src/dci1v4r4/analysis/spectrum.py", "src/dci1v4r4/analysis/run.py",
          "src/dci1v4r4/run/analysis_run.py",
          "src/dci1v4r4/run/confirmatory_run.py",
          "src/dci1v4r4/run/freeze_run.py", "src/dci1v4r4/run/gates_run.py",
          "src/dci1v4r4/protocol/constants.py",
          "src/dci1v4r4/protocol/wordings.py",
          "src/dci1v4r4/design/cells.py", "tools/v4r4_final_report.py"]
for rel in SOURCE:
    items.append(entry(DCI1 / rel, "source", "SOURCE CODE (inspected)"))
for rel in ["user-notes/DCI1_preregistration_v4r1.md",
            "user-notes/DCI1_preregistration_v4r2.md",
            "user-notes/DCI1_preregistration_v4r3.md",
            "user-notes/DCI1_preregistration_v4r4.md",
            "CHANGES_SCIENTIFIC.md", "RESEARCH_STATE.md"]:
    items.append(entry(DCI1.parent / rel, "preregistration / documentation",
                       "PREREGISTRATION (inspected)"))

rec = {"_provenance": "POST-HOC DIAGNOSTIC manifest for the follow-up "
                      "evidence package",
       "n_items": len(items),
       "status_legend": {
           "REGISTERED": "produced by a preregistered stage of v4r4",
           "PRE-REGISTERED DIAGNOSTIC": "a derived artifact of the registered "
                                        "pipeline's own reporting tools",
           "POST-HOC DIAGNOSTIC": "produced by this follow-up task; never "
                                  "preregistered, never confirmatory",
           "SOURCE CODE / PREREGISTRATION": "read, not produced"},
       "items": items}
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name, len(items), "items")
