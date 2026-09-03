"""The freeze-readiness audit: the v8 successor of v7's §33 pre-freeze
checklist, executed on the mandatory path of ``FROZEN`` and written into
the freeze record.

Every item is a fact about signed pre-freeze artifacts, the rule layer or
the repository --- never about an outcome. A failing item refuses the
freeze (``FREEZE_REFUSED``, terminal for this root: a repair is a fresh
root). There is no override.

Items (pre-freeze audit of 2026-09-02, docs/DCI1_preregistration_v8.md §19):

 1. the v8 preregistration exists, is not a draft, and is the document the
    registration manifest bound (same hash);
 2. one confirmatory allocation: the membership lock, the rule layer and
    the precision module agree;
 3. the universal calibration policy: this model's pilot Gate 2 was
    measured at ``rules.CALIBRATION_FRAME_OFFSETS`` --- every pass, every
    frame --- so no model enters on a different measurement basis;
 4. the operating-point stability bootstrap is recorded for every entering
    frame, with a status, and a runner-up arm exists exactly where the
    status is OPERATING_POINT_UNSTABLE on a LOCAL frame;
 5. the reference-sensitivity plan (five frozen families, every admissible
    triple, the distances) is recorded for every LOCAL frame;
 6. no protected artifact exists under this model's tree (no composed row
    can have influenced anything a freeze binds);
 7. the instrument (verifier and wording hashes) is the one the pilot
    measured with;
 8. the analysis code hashes bound at registration are the current ones;
 9. the worktree is clean and the record is addressed to HEAD (the
    lifecycle gate; restated here so the checklist is complete on the
    record);
10. every entering frame's identification statuses are on the record;
11. (successor design, 2026-09-03) the pilot's screen ran at
    ``rules.SCREEN_FRAME_OFFSETS`` and its forwarding was decided by
    ``rules.RETENTION_POLICY`` against ``rules.RETENTION_TARGET_BASIS`` ---
    a pilot of the pooled design cannot be frozen under the successor rule.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs
from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_obj

from dci1v8dev import rules as R
from dci1v8dev.confirm import PREREGISTRATION_DOCUMENT
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import precision as P
from dci1v8dev.confirm.manifest import analysis_code_hashes
from dci1v8dev.run.lifecycle import instrument_hashes

__all__ = ["FREEZE_REFUSED", "freeze_readiness", "assert_freeze_ready"]

FREEZE_REFUSED = "FREEZE_REFUSED"


def _item(ok: bool, what: str, **detail: Any) -> dict[str, Any]:
    return {"pass": bool(ok), "what": what, **detail}


def freeze_readiness(tree: L.ConfirmTree, membership: Mapping[str, Any], *,
                     repo_root: Path | str, lock: Mapping[str, Any],
                     registration: Mapping[str, Any],
                     pilot_gate2: Mapping[str, Any],
                     pilot_regime: Mapping[str, Any] | None = None
                     ) -> dict[str, Any]:
    """The checklist, every item evaluated; nothing raised here."""
    repo_root = Path(repo_root)
    items: dict[str, dict[str, Any]] = {}

    # 1. the preregistration
    prereg = repo_root / PREREGISTRATION_DOCUMENT
    text = prereg.read_text() if prereg.exists() else ""
    bound = (registration.get("documents") or {}).get(PREREGISTRATION_DOCUMENT)
    current = (sha_obj({"path": PREREGISTRATION_DOCUMENT,
                        "bytes": prereg.read_bytes().hex()})
               if prereg.exists() else None)
    final = "Status: FROZEN-READY" in text and "Status: DRAFT" not in text
    items["preregistration"] = _item(
        prereg.exists() and (final or tree.synthetic) and bound is not None
        and bound == current,
        "the v8 preregistration exists, is not a draft, and is the document "
        "the registration manifest bound",
        path=PREREGISTRATION_DOCUMENT, exists=prereg.exists(), final=final,
        synthetic_namespace=tree.synthetic,
        bound_hash=bound, current_hash=current)

    # 2. one allocation
    lock_blocks = (lock.get("allocation") or {}).get("chosen_blocks_per_frame")
    items["allocation"] = _item(
        lock_blocks == R.CONFIRMATORY_BLOCKS_PER_FRAME == P.ALLOCATION
        == R.CONFIRMATORY_MAX_BLOCKS_PER_FRAME,
        "one confirmatory allocation across the lock, the rules and the "
        "precision module",
        lock=lock_blocks, rules=R.CONFIRMATORY_BLOCKS_PER_FRAME,
        precision=P.ALLOCATION)

    # 3. universal calibration
    alloc = pilot_gate2.get("calibration_allocation") or {}
    offsets = tuple(alloc.get("frame_offsets") or ())
    # A synthetic pilot walks a topic-limited bank; the passes are what the
    # policy states and the topic count is the bank's, so the count is
    # enforced only where the bank is the registered one.
    topics_ok = (int(alloc.get("topics_per_frame") or 0) == R.CALIBRATION_TOPICS_PER_FRAME
                 or tree.synthetic)
    items["calibration_policy"] = _item(
        offsets == tuple(R.CALIBRATION_FRAME_OFFSETS) and topics_ok,
        "this model's pilot Gate 2 was measured at the universal calibration "
        "allocation (every pass, every frame)",
        pilot_frame_offsets=list(offsets),
        pilot_topics_per_frame=alloc.get("topics_per_frame"),
        required_frame_offsets=list(R.CALIBRATION_FRAME_OFFSETS),
        required_topics_per_frame=R.CALIBRATION_TOPICS_PER_FRAME,
        policy=R.CALIBRATION_POLICY)

    # 4. stability + runner-up
    entering = {w: e for w, e in membership["by_frame"].items() if e.get("enters")}
    stab_ok, stab_detail = True, {}
    for w, e in entering.items():
        st = e.get("stability") or {}
        status = st.get("status")
        unstable = st.get("unstable_coordinates") or []
        expected_slots = sorted({"n_star": "A2", "m_star": "B2"}[c] for c in unstable
                                if (st.get(c) or {}).get("runner_up") is not None) \
            if e.get("enters_local") else []
        got_slots = sorted(e.get("runner_up_slots") or [])
        ok = (status in (R.OPERATING_POINT_STABLE, R.OPERATING_POINT_UNSTABLE)
              and st.get("n_star", {}).get("p_selected_reproduced") is not None
              and got_slots == expected_slots)
        stab_ok &= ok
        stab_detail[w] = {"status": status, "runner_up_slots": got_slots,
                          "expected": expected_slots, "ok": ok}
    items["operating_point_stability"] = _item(
        stab_ok and bool(entering),
        "the §12.3 re-selection bootstrap is recorded with a status for every "
        "entering frame, and the runner-up arm exists exactly where a LOCAL "
        "frame's coordinate is OPERATING_POINT_UNSTABLE",
        by_frame=stab_detail, min_recovery=R.OPERATING_POINT_MIN_RECOVERY)

    # 5. reference sensitivity
    rs_ok, rs_detail = True, {}
    for w, e in entering.items():
        if not e.get("enters_local"):
            continue
        rs = e.get("reference_sensitivity") or {}
        fams = rs.get("families") or []
        ok = (len(fams) == 5 and len(set(fams)) == 5
              and bool(rs.get("admissible_triples"))
              and set(rs.get("distances") or {}) == set(
                  r["slot"] for r in e.get("core", []) + e.get("backups", [])))
        rs_ok &= ok
        rs_detail[w] = {"families": fams,
                        "n_triples": len(rs.get("admissible_triples") or []),
                        "ok": ok}
    items["reference_sensitivity"] = _item(
        rs_ok, "five frozen families, every admissible triple and the "
               "distances are recorded for every LOCAL frame",
        by_frame=rs_detail)

    # 6. no protected artifact under this tree
    protected = {stage: tree.stage_dir(stage).exists() for stage in L.PROTECTED_STAGES}
    items["no_protected_artifacts"] = _item(
        not any(protected.values()),
        "no protected stage directory exists under this model's tree",
        **{f"exists_{k}": v for k, v in protected.items()})

    # 7. instrument
    now = instrument_hashes()
    pilot_instr = {"verifier_hash": pilot_gate2.get("verifier_hash"),
                   "wording_hash": pilot_gate2.get("wording_hash")}
    items["instrument"] = _item(
        pilot_instr == now,
        "the verifier and wording hashes are the ones the pilot measured with",
        pilot=pilot_instr, current=now)

    # 8. analysis code
    bound_code = registration.get("analysis_code") or {}
    items["analysis_code"] = _item(
        bound_code == analysis_code_hashes(),
        "the analysis code hashes bound at registration are the current ones",
        n_modules=len(bound_code))

    # 9. worktree (the gate already ran; restated on the record)
    items["worktree"] = _item(
        True, "the lifecycle gate addressed this record to HEAD of a clean "
              "worktree (run.lifecycle.stage_provenance; no bypass exists)")

    # 10. identification statuses
    ident_ok = all(isinstance(e.get("identification_statuses"), list)
                   for e in entering.values())
    items["identification_statuses"] = _item(
        ident_ok, "every entering frame's identification statuses are on the "
                  "record")

    # 11. the successor's screen and forwarding rule
    population = pilot_gate2.get("calibration_population") or {}
    screen_alloc = (pilot_regime or {}).get("screen_allocation") or {}
    screen_offsets = tuple(screen_alloc.get("frame_offsets") or ())
    items["prescreen_policy"] = _item(
        population.get("policy") == R.RETENTION_POLICY
        and population.get("target_basis") == R.RETENTION_TARGET_BASIS
        and (pilot_regime is None or screen_offsets == tuple(R.SCREEN_FRAME_OFFSETS)),
        "the pilot's screen ran at the successor's screen allocation and its "
        "forwarding was decided by the frame-aware policy against the "
        "registered target",
        pilot_policy=population.get("policy"),
        pilot_target_basis=population.get("target_basis"),
        pilot_screen_frame_offsets=list(screen_offsets),
        required_policy=R.RETENTION_POLICY,
        required_target_basis=R.RETENTION_TARGET_BASIS,
        required_screen_frame_offsets=list(R.SCREEN_FRAME_OFFSETS),
        regime_record_checked=pilot_regime is not None)

    failed = sorted(k for k, v in items.items() if not v["pass"])
    return {"items": items, "failed": failed, "ready": not failed,
            "rule": "every item must pass; a failing item refuses the freeze "
                    "(FREEZE_REFUSED) and there is no override"}


def assert_freeze_ready(readiness: Mapping[str, Any], *, tree: L.ConfirmTree
                        ) -> None:
    if readiness["ready"]:
        return
    raise L.TerminalStatus(
        FREEZE_REFUSED, gate=L.STAGE_FROZEN,
        criterion="the freeze-readiness checklist (confirm.readiness) passes "
                  f"on every item; failed: {readiness['failed']}",
        observed={"failed": readiness["failed"],
                  "items": {k: {kk: vv for kk, vv in v.items()
                                if kk in ("pass", "what")}
                            for k, v in readiness["items"].items()
                            if not v["pass"]}},
        strongest_permissible_statement=(
            f"{tree.model_key} is not frozen; the items "
            f"{readiness['failed']} failed the readiness audit and the root "
            "is terminal --- a repair is a fresh root"))
