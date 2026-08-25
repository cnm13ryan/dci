#!/usr/bin/env python3
"""§13.15's support criterion, run by the **production** code on closed data.

    python3 tools/v6_reference_feasibility.py [--check]

**What this replaces.** READINESS §7 step 3 specified a development pilot that
asks whether the extension's reserve rungs land inside
``p_solo in [0.10, 0.90]``. That is one clause of one component of §13.1's
V(R). Passing it does not mean a library can support a reference set, and v5
is the demonstration: three replications lost §12.6's C4 at the screen and
the fourth reached Gate 4 with §13.15 met and no spare. A prescreen that
evaluates a proxy for the registered criterion cannot predict the registered
gate, so this evaluates **the criterion itself**, through
``dci1v6.stages.feasibility`` --- the same functions Gate 3A, Gate 3B and
Gate 3C run.

**It introduces no measurement.** Every number here is read from the four
signed v5 records. §13.7's calibration, §13.8-§13.12's selection and §13.15's
counts are pure functions of what Gate 2 and Gate 2.5 already measured, which
is why the registered lifecycle can afford them and why a development report
over them costs nothing. Two validations run before anything is reported: the
selection must reproduce each signed slot map exactly, and the support verdict
must reproduce each signed §13.15 block exactly. The run aborts if either
disagrees --- a development report whose baseline does not reproduce is a
report about the reimplementation, not the library.

**Classification: DEVELOPMENT_EVIDENCE. Nothing here re-opens v5.** No record
is written, mutated or re-verdicted. §34 D6 is irreversible and the four
terminal outcomes stand exactly as signed. What is new is the *margin*: how
far each replication was from §13.15's minima, per requirement, which the
support verdict's boolean does not carry and which is the quantity a library
has to move before it is frozen.

**What this may not be read as.** It reports the criterion on the libraries and
the measurements v5 actually had. It says nothing about a *changed* library:
a new Tier-1 family's compliance on these models has not been measured, and
whether it would qualify is not knowable from closed data. That measurement is
the one thing here that requires new rows, and it is not taken.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))
sys.path.insert(0, str(DCI1))

from dci1v5.engine import context as v5ctx                   # noqa: E402
from dci1v5.engine.paths import model_tree                   # noqa: E402
from dci1v5.protocol import constants as C5                  # noqa: E402
from dci1v6.protocol import constants as C                   # noqa: E402
from dci1v6.protocol import decisions                        # noqa: E402
from dci1v6.stages import feasibility                        # noqa: E402

OUT = DCI1 / "reports" / "dci1v6" / "reference_feasibility.json"

#: §34 D6 decides what an unmet §13.15 does, and ``evaluate_support`` refuses
#: to name a disposition while it is open. **v6 has taken no decision and this
#: does not give it one.** What is applied here is *v5's own signed record*,
#: to re-read *v5's own data* under the disposition v5 ran --- the same move
#: ``v6_expansion_dryrun.py`` makes when it reads U4's resolution off the
#: record whose table it is replaying. Nothing is written, and the v6 record
#: path is untouched: it still does not exist and no code may create it.
V5_DECISIONS = DCI1 / "reports" / "dci1v5" / "researcher_decisions.json"
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")


def _apply_v5_closures() -> list[str]:
    """v5's decisions, for re-reading v5's data. Not a v6 closure."""
    if not V5_DECISIONS.exists():
        raise SystemExit(f"{V5_DECISIONS} is missing; this report re-reads "
                         "v5's data under v5's own recorded decisions and "
                         "will not supply a value in their place")
    return list(decisions.apply_recorded_closures(V5_DECISIONS))


def _records(model_key: str) -> dict:
    """The signed v5 records. Hash and signature verified on read."""
    from dci1v5.engine import transitions as v5tx

    tree = model_tree(v5ctx.registered_context(), model_key)
    return {stage: v5tx.read_stage_record(tree, stage)
            for stage in (C5.STAGE_REGIME, C5.STAGE_GATE2, C5.STAGE_GATE2_5,
                          C5.STAGE_GATE3A, C5.STAGE_GATE3B, C5.STAGE_GATE3C)}


def evaluate(model_key: str) -> dict:
    rec = _records(model_key)
    g3a, g3b, g3c = (rec[C5.STAGE_GATE3A], rec[C5.STAGE_GATE3B],
                     rec[C5.STAGE_GATE3C])
    calibration = {
        "pooled_table": g3a["pooled_table"], "m_star": g3a["m_star"],
        "iota_a": g3a["iota_a"],
        "solo_compliance_a": g3a["solo_compliance_a"],
        "stability": g3a.get("stability") or {},
        "qualified_families": rec[C5.STAGE_GATE2_5]["qualified_families"]}
    chosen = feasibility.selection_at(calibration, model_key=model_key)
    supported = feasibility.support_at(
        chosen, model_key=model_key, calibration=calibration,
        regime_record=rec[C5.STAGE_REGIME])
    report = supported["report"]

    # ---- validation: the production kernels must reproduce the signature
    signed_slots = {k: list(v) for k, v in g3b["slot_map"].items()}
    if chosen["slot_map"] != signed_slots:
        raise SystemExit(
            f"{model_key}: §13.8-§13.12 recomputed a different slot map than "
            "the signed record; refusing to report a feasibility study whose "
            "baseline does not reproduce")
    signed_support = g3c["support"]
    if (report["support_met"] != signed_support["support_met"]
            or report["realised"] != signed_support["realised"]
            or report["failures"] != signed_support["failures"]):
        raise SystemExit(
            f"{model_key}: §13.15 recomputed a different support block than "
            "the signed record; refusing to report")

    margin = feasibility.support_margin(report)
    return {
        "m_star": g3a["m_star"],
        "baseline_reproduces_signed_record": True,
        "support_met": report["support_met"],
        "signed_support_met": signed_support["support_met"],
        "realised": report["realised"],
        "requirements": report["requirements"],
        "failures": report["failures"],
        "margin": margin,
        "admitted_arms": supported["arms"],
        "n_qualified_families": len(
            set(calibration["qualified_families"])),
    }


def build() -> dict:
    applied = _apply_v5_closures()
    per_model = {m: evaluate(m) for m in MODELS}
    binding: dict[str, int] = {}
    for entry in per_model.values():
        for name in entry["margin"]["binding"]:
            binding[name] = binding.get(name, 0) + 1
    return {
        "_what": "§13.15's support criterion, evaluated by the production "
                 "kernels in dci1v6.stages.feasibility, on the four signed "
                 "v5 records",
        "_classification": "DEVELOPMENT_EVIDENCE",
        "_generates_no_rows": (
            "§13.7, §13.8-§13.12 and §13.15 are pure functions of what Gate "
            "2 and Gate 2.5 measured. Nothing here generates, and nothing "
            "here reads a composed outcome"),
        "_not_evidence_about": [
            "Delta_R", "Delta_j", "Xi", "any v5 replication's verdict",
            "whether a library the researcher has not authored would qualify",
        ],
        "_v5_is_unchanged": (
            "no v5 record is written, mutated or re-verdicted; §34 D6 is "
            "irreversible and the four terminal outcomes stand as signed. "
            "The recomputations are validated against those records before "
            "anything is reported"),
        "_generated_by": "dci1/tools/v6_reference_feasibility.py",
        "_decisions_applied": {
            "source": "dci1/reports/dci1v5/researcher_decisions.json",
            "n_applied": len(applied),
            "standing": "v5's own closures, applied in this process to "
                        "re-read v5's own data. v6 has taken no decision; "
                        "there is no v6 researcher-decision record and no "
                        "code may create one"},
        "_one_implementation": (
            "the registered stages, this report and the operating-point "
            "search call dci1v6.stages.feasibility. There is no development "
            "copy of the criterion to drift from the registered one"),
        "requirements": {
            "min_structurally_eligible_tier12_families":
                C.MIN_STRUCTURALLY_ELIGIBLE_TIER12_FAMILIES,
            "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
            "n_core_references": C.N_CORE_REFERENCES,
            "min_tier1_core": C.MIN_TIER1_CORE,
            "n_core_feature_groups": C.N_CORE_FEATURE_GROUPS,
            "n_backup_families": C.N_BACKUP_FAMILIES,
        },
        "binding_requirement_counts": binding,
        "reading": (
            "the boolean §13.15 records answers 'did this qualify'. The "
            "margin answers 'by how much', which is the question a library "
            "has to pass before it is frozen, and on these four replications "
            "the binding requirement is not the family count"),
        "what_still_needs_new_data": (
            "whether a Tier-1 family the researcher adds would pass the full "
            "V(R) on these models. Nothing in the closed data measures an "
            "unauthored instrument, and no proxy for it is reported here"),
        "per_model": per_model,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed report is stale")
    args = parser.parse_args()
    payload = build()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT} is stale; re-run without --check")
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
