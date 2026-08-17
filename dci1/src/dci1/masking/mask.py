"""Masked analysis machinery (prereg §19).

After confirmatory generation and before any analysis, the arm labels of the
four primary arms are permuted independently within each block using the
system random source (never the study's seeded streams). The permuted table is
the only thing the masked phase reads; the true mapping lives in the mask key
file, whose content hash is recorded at the moment it is written.

`unmask` is the single named function that applies the key. Its invocation
writes a timestamped run-record entry with the content hash of the analysis
code at that moment. The key file is opened nowhere else in this package —
asserted by a test that counts opens of the key path during a full run.
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from dci1.evidence.store import append_run_record, atomic_write
from dci1.protocol.constants import PRIMARY_ARMS, ProtocolError
from dci1.protocol.hashing import sha_file, sha_text

_SYSTEM_RANDOM = secrets.SystemRandom()


def analysis_code_hash() -> str:
    """SHA-256 over every source file of this package, sorted by path."""
    src_root = Path(__file__).resolve().parents[1]
    parts = []
    for path in sorted(src_root.rglob("*.py")):
        parts.append(f"{path.relative_to(src_root)}\x1f{sha_file(path)}")
    return sha_text("\n".join(parts))


def build_permutations(block_ids: list[str]
                       ) -> tuple[dict[str, dict[str, str]], int]:
    """One system-random permutation of the four primary arms per block
    (v2 §19). Returns (true-arm → masked-arm per block, changed count)."""
    permutations: dict[str, dict[str, str]] = {}
    changed = 0
    for block_id in sorted(block_ids):
        arms = list(PRIMARY_ARMS)
        shuffled = list(arms)
        _SYSTEM_RANDOM.shuffle(shuffled)
        mapping = dict(zip(arms, shuffled))
        permutations[block_id] = mapping
        if any(a != b for a, b in mapping.items()):
            changed += 1
    return permutations, changed


def construct_mask(accepted_rows: list[dict[str, Any]], out_dir: Path,
                   model_dir: Path) -> dict[str, str]:
    """Write the permuted table and the mask key; record the key's hash."""
    out_dir = Path(out_dir)
    by_block: dict[str, list[dict[str, Any]]] = {}
    for row in accepted_rows:
        by_block.setdefault(row["block_id"], []).append(row)

    permutations, changed_blocks = build_permutations(sorted(by_block))
    masked_rows: list[dict[str, Any]] = []
    for block_id in sorted(by_block):
        mapping = permutations[block_id]
        for row in by_block[block_id]:
            masked = dict(row)
            if row["arm"] in mapping:
                masked["arm"] = mapping[row["arm"]]
            masked_rows.append(masked)

    if changed_blocks < len(by_block) / 2:
        raise ProtocolError(
            f"mask permutations differ from true labels in only "
            f"{changed_blocks}/{len(by_block)} blocks — below the §19 "
            f"half-of-blocks requirement; mask construction failed")

    masked_path = out_dir / "masked_accepted.jsonl"
    key_path = out_dir / "mask_key.json"
    atomic_write(masked_path,
                 "".join(json.dumps(r, sort_keys=True) + "\n"
                         for r in masked_rows))
    key_payload = json.dumps({"permutations": permutations}, indent=2,
                             sort_keys=True)
    atomic_write(key_path, key_payload)
    key_hash = sha_text(key_payload)
    append_run_record(model_dir, {
        "event": "mask_constructed", "masked_table": str(masked_path),
        "mask_key_hash": key_hash, "blocks": len(by_block),
        "blocks_with_changed_labels": changed_blocks})
    return {"masked_table": str(masked_path), "mask_key": str(key_path),
            "mask_key_hash": key_hash}


def unmask(masked_rows: list[dict[str, Any]], key_path: Path,
           model_dir: Path) -> list[dict[str, Any]]:
    """THE single unmask function (§19). Applies the key, records the moment."""
    key_path = Path(key_path)
    # The only open of the key file, routed through builtins.open so the §19
    # single-open audit can instrument it.
    with open(key_path) as handle:
        key = json.load(handle)
    inverse = {block: {masked: true for true, masked in mapping.items()}
               for block, mapping in key["permutations"].items()}
    restored = []
    for row in masked_rows:
        out = dict(row)
        mapping = inverse.get(row["block_id"])
        if mapping and row["arm"] in mapping:
            out["arm"] = mapping[row["arm"]]
        restored.append(out)
    append_run_record(model_dir, {
        "event": "unmasked",
        "mask_key_hash": sha_text(json.dumps(key, indent=2, sort_keys=True)),
        "analysis_code_hash": analysis_code_hash()})
    return restored
