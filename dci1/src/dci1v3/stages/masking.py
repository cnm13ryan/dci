"""Masking custody (§19, items 43–47): persistently single-shot mask
creation and unmasking, with pilot_mask and confirmatory_mask as disjoint
namespaces.

Mask creation: an exclusive cross-process writer lock is held by the
dispatcher; an immutable durable reservation is written BEFORE any mask
randomness is generated; existing reservation, key, or masked view makes a
second attempt fail before key generation. The key is written once
(O_EXCL) and its content hash recorded at write time. The permuted labels
must differ from the true labels in at least half of the blocks.

Unmasking: reservation before key access; ``open_mask_key`` is the single
named function that opens the key file, exactly once per run; the unmask
record carries timestamp, mask-key hash, and analysis-code hash. Re-masking
after unmasking fails before mutation.
"""
from __future__ import annotations

import builtins
import json
import secrets
from pathlib import Path
from typing import Any

from dci1v3.engine import fs, store
from dci1v3.engine.paths import ModelTree
from dci1v3.errors import CustodyError, IntegrityError
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_file, sha_obj

#: Fields whose values would reveal the true arm to the masked phase.
MASKED_VIEW_EXCLUDED = ("row_id", "cell_id", "kind", "prompt_hash", "seed",
                        "constraint_id", "severity", "draw_index",
                        "dependency_digest", "interpreter",
                        "record_hash")


def analysis_code_hash() -> str:
    """Hash of the analysis package sources (§19 executable check 3)."""
    import dci1v3.analysis as pkg
    root = Path(pkg.__file__).resolve().parent
    return sha_obj({p.name: sha_file(p) for p in sorted(root.glob("*.py"))})


def _assert_no_prior_mask(tree: ModelTree, ns: str) -> None:
    for path in (tree.mask_reservation(ns), tree.mask_key_path(ns),
                 tree.masked_view(ns)):
        if path.exists():
            raise CustodyError(
                f"{ns}: existing mask state at {path.name}; a second mask "
                f"attempt fails before key generation")


def create_mask(tree: ModelTree, ns: str,
                primary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Permute the four primary arm labels independently within each block
    using system randomness; write key, masked view, and events."""
    _assert_no_prior_mask(tree, ns)
    if ns == "confirmatory_mask" and \
            tree.unmask_reservation("confirmatory_mask").exists():
        raise CustodyError("re-masking after unmasking fails before "
                           "mutation")
    # Immutable durable reservation BEFORE any randomness is generated.
    fs.write_json_once(tree.mask_reservation(ns),
                       {"namespace": ns, "state": "reserved"})
    store.replicate(tree.mask_dir(ns),
                    tree.durable / "masking" / ns)

    rng = secrets.SystemRandom()
    blocks = sorted({row["block_id"] for row in primary_rows
                     if row["arm"] in C.PRIMARY_ARMS})
    key: dict[str, dict[str, str]] = {}
    changed = 0
    for block_id in blocks:
        permuted = list(C.PRIMARY_ARMS)
        rng.shuffle(permuted)
        key[block_id] = dict(zip(C.PRIMARY_ARMS, permuted))
        if any(a != b for a, b in zip(C.PRIMARY_ARMS, permuted)):
            changed += 1
    if changed < C.MASK_MIN_CHANGED_FRACTION * len(blocks):
        raise CustodyError(
            f"permuted labels differ in {changed}/{len(blocks)} blocks, "
            f"below the registered half; mask construction fails closed")

    key_record = {"namespace": ns, "key": key}
    fs.write_json_once(tree.mask_key_path(ns), key_record)
    key_hash = sha_file(tree.mask_key_path(ns))

    masked_rows = []
    for row in primary_rows:
        masked_arm = (key[row["block_id"]][row["arm"]]
                      if row["arm"] in C.PRIMARY_ARMS else row["arm"])
        masked = {k: v for k, v in row.items()
                  if k not in MASKED_VIEW_EXCLUDED}
        verdicts = dict(masked.get("verdicts", {}))
        verdicts.pop("verifier_source_hash", None)
        masked["verdicts"] = verdicts
        masked["arm"] = masked_arm
        masked["masked_row_id"] = f"{row['block_id']}:{masked_arm}"
        masked_rows.append(masked)
    view = tree.masked_view(ns)
    view.parent.mkdir(parents=True, exist_ok=True)
    view.write_text("".join(
        json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
        for r in masked_rows))
    fs.append_jsonl(tree.mask_event_log(ns), {
        "event": "mask_created", "namespace": ns,
        "mask_key_hash": key_hash, "blocks": len(blocks),
        "blocks_changed": changed,
        "masked_view_hash": sha_file(view)})
    # Key, view, and events become durable now, so no later operation ever
    # needs to copy (and hence open) the key file again.
    store.replicate(tree.mask_dir(ns), tree.durable / "masking" / ns)
    return {"namespace": ns, "mask_key_hash": key_hash,
            "blocks": len(blocks), "blocks_changed": changed,
            "masked_view_hash": sha_file(view)}


def masked_rows(tree: ModelTree, ns: str) -> list[dict[str, Any]]:
    view = tree.masked_view(ns)
    if not view.exists():
        raise CustodyError(f"{ns}: no masked view exists")
    return fs.read_jsonl(view)


def open_mask_key(tree: ModelTree, ns: str) -> dict[str, dict[str, str]]:
    """THE single named function that opens the mask key file."""
    with builtins.open(tree.mask_key_path(ns)) as handle:
        record = json.load(handle)
    if record["namespace"] != ns:
        raise CustodyError("mask key namespace mismatch")
    return record["key"]


def unmask(tree: ModelTree, ns: str, *, timestamp: str) -> dict[str, Any]:
    """Single-shot unmask: reservation before key access; records
    timestamp, mask-key hash, and analysis-code hash."""
    if not tree.mask_key_path(ns).exists():
        raise CustodyError(f"{ns}: no mask key exists")
    # Immutable durable reservation BEFORE the key is opened (item 46).
    fs.write_json_once(tree.unmask_reservation(ns),
                       {"namespace": ns, "state": "unmask_reserved",
                        "timestamp": timestamp})
    store.replicate(tree.mask_dir(ns), tree.durable / "masking" / ns)

    key = open_mask_key(tree, ns)
    record = {
        "event": "unmasked", "namespace": ns, "timestamp": timestamp,
        "mask_key_hash": sha_file(tree.mask_key_path(ns)),
        "analysis_code_hash": analysis_code_hash(),
    }
    fs.append_jsonl(tree.mask_event_log(ns), record)
    return {"key": key, "record": record}


def apply_key(rows: list[dict[str, Any]],
              key: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """Map masked labels back to true labels."""
    inverse = {block: {v: k for k, v in mapping.items()}
               for block, mapping in key.items()}
    unmasked = []
    for row in rows:
        if row["arm"] in C.PRIMARY_ARMS:
            true_arm = inverse[row["block_id"]][row["arm"]]
        else:
            true_arm = row["arm"]
        unmasked.append({**row, "arm": true_arm})
    return unmasked


def assert_namespace_untouched(before: dict[str, str],
                               after: dict[str, str], ns: str) -> None:
    """Executable §19/§17 check: a mask cycle in one namespace leaves the
    other namespace byte-identical."""
    if before != after:
        raise IntegrityError(f"{ns} namespace changed during a foreign "
                             f"mask cycle")
