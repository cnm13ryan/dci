#!/usr/bin/env python3
"""The v6 study-level closure record: how many replications survived, and the
one sentence §34 D25 registered before data for the case where one did.

    python3 tools/v6_closure.py [--check]

**Why this file exists at all.** §34 D25 registers, before any data, what v6
says at study level when exactly one replication reaches ``GATE_5_FREEZE``
identified. ``run.lifecycle.study_level_statement`` holds both admissible
sentences and refuses while D25 is open --- but until 2026-08-26 **no stage
called it**. The nineteen-stage lifecycle is per replication and its last
stage, ``FINAL_REPORT``, writes one report per model; a statement about the
study as a whole has no per-model stage to live in, so D25's closure was a
researcher act that changed no v6 artifact. A decision whose value cannot
reach an artifact is a decision the study does not actually take, which is
what the 2026-08-26 red team found.

This is the study's own closing act, and it follows the precedent of
``tools/v4r3_closure.py`` and ``reports/dci1v5/closure.json``: it reads every
replication's **signed** records, counts survivors, and writes
``reports/dci1v6/closure.json``.

**It counts and it quotes; it does not compute a result.** §6.1's firewall is
the reason: four replications are analysed separately and never pooled, and
no cross-model scalar carries a claim. So this reads a per-replication
outcome (does a passing ``GATE_5_FREEZE`` record exist, and is there a
terminal report) and nothing else. It performs no estimation, opens no
masked quantity and re-reads no row.

**It cannot be run early to see the count.** ``study_level_statement`` calls
``decisions.choice`` on D25, so the sentence is unavailable until the
researcher has closed it --- which is the point of registering it before
data. Running this tool before then reports the survivor count and refuses
the sentence, and says which decision is open.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DCI1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1_ROOT / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.engine.signing import verify_signed                  # noqa: E402
from dci1v4.models.registry import MODELS                        # noqa: E402
from dci1v4.protocol.hashing import sha_obj                      # noqa: E402
from dci1v6.engine.context import registered_context             # noqa: E402
from dci1v6.engine.paths import model_tree                       # noqa: E402
from dci1v6.protocol import constants as C                       # noqa: E402
from dci1v6.protocol import decisions                            # noqa: E402
from dci1v6.engine import paths, transitions                     # noqa: E402
from dci1v6.run import lifecycle                                 # noqa: E402

OUT = DCI1_ROOT / "reports" / "dci1v6" / "closure.json"


def _terminal_statuses(context, model_keys: list[str]) -> dict[str, str]:
    """Each non-surviving replication's §28 status, read from its report.

    **Verified, and unwrapped.** A terminal report is a *signed* record ---
    ``{"payload": ..., "record_hash": ..., "signature": ...}`` --- and this
    read the outer object, so ``status`` was never there and every terminal
    status in the study's closing record would have read ``UNKNOWN``. Nothing
    surfaced it because no v6 replication had ever terminated; the 2026-08-26
    apparatus fault put a report on the tree and the artifact went stale
    naming a status it could not read. It now goes through
    ``transitions.terminal_status``, the one reader that knows the shape, and
    verifies the signature first --- a closing record that repeated an
    unverifiable verdict would be worse than one that refused.
    """
    out: dict[str, str] = {}
    for model_key in model_keys:
        tree = model_tree(context, model_key)
        if not tree.terminal_report.exists():
            continue
        verify_signed(fs.read_json(tree.terminal_report),
                      context.signing_key_path,
                      where=f"{model_key}:terminal_report")
        out[model_key] = str(transitions.terminal_status(tree))
    return out


def _apparatus_faults(context) -> list[dict[str, object]]:
    """Every stage-1 readiness verdict this study retired (A15).

    Reported in the closing record because it is where a reader looks for
    what happened to each replication, and a retirement that appeared only in
    the registration manifest would be invisible to that reader.
    """
    out: list[dict[str, object]] = []
    for path in paths.apparatus_fault_records(Path(context.study_root)):
        body = json.loads(path.read_text())
        body = body.get("payload", body)
        out.append({k: body.get(k) for k in
                    ("model_key", "retired_record_hash", "retired_status",
                     "retired_gate", "reason", "defect", "amendment",
                     "retained_at", "retired_at")})
    return out


def _reached(context, model_keys: list[str]) -> dict[str, str]:
    """The last stage each replication recorded, for the closure's audit."""
    out: dict[str, str] = {}
    for model_key in model_keys:
        tree = model_tree(context, model_key)
        last = None
        for stage in C.STAGE_SEQUENCE:
            if tree.stage_record(stage).exists():
                last = stage
        out[model_key] = last or "NO_RECORD"
    return out


def build() -> dict[str, object]:
    context = registered_context()
    model_keys = sorted(m.model_key for m in MODELS)
    survivors = lifecycle.frozen_identified_replications(context, model_keys)
    terminal = _terminal_statuses(context, model_keys)
    payload: dict[str, object] = {
        "_what": "the v6 study-level closure record",
        "_classification": "REGISTERED_OUTCOME",
        "_reads": "signed per-replication stage records only. No estimation, "
                  "no pooling, no masked quantity, no row re-read",
        "study_id": context.study_id,
        "registered_replications": model_keys,
        "survivors": list(survivors),
        "n_survivors": len(survivors),
        "terminal_statuses": terminal,
        # A15. A retired apparatus fault is not a terminal status and never
        # appears above; it is reported separately so that a replication
        # whose stage-1 attempt was refused by a defect in the caller is
        # readable as exactly that, and never as a verdict about the model.
        "apparatus_faults": _apparatus_faults(context),
        "last_stage_recorded": _reached(context, model_keys),
        "firewall": "§6.1: four replications analysed separately and never "
                    "pooled; no cross-model scalar carries a claim, and §15 "
                    "registers no cross-model multiplicity family",
    }
    try:
        payload["study_level"] = lifecycle.study_level_statement(
            survivors=survivors, terminal=terminal)
    except decisions.DecisionOpenError as exc:
        payload["study_level"] = None
        payload["study_level_withheld"] = {
            "reason": str(exc),
            "why": "§34 D25 registers the one-survivor sentence BEFORE data. "
                   "Until it is closed the sentence does not exist, and this "
                   "record reports the count without one rather than "
                   "composing one after the count is known",
            "open_decisions": list(decisions.open_decisions()),
        }
    payload["payload_sha256"] = sha_obj(
        {k: v for k, v in sorted(payload.items()) if not k.startswith("_")})
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report whether the committed record is current, "
                         "and write nothing")
    args = ap.parse_args()
    payload = build()
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    if args.check:
        current = OUT.exists() and OUT.read_text() == text
        print(f"{OUT} is {'current' if current else 'STALE'}")
        return 0 if current else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    print(f"  survivors: {payload['n_survivors']} of "
          f"{len(payload['registered_replications'])}")
    if payload.get("study_level") is None:
        print("  study-level statement WITHHELD: §34 D25 is open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
