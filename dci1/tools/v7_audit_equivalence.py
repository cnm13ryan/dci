#!/usr/bin/env python3
"""Compare two execution-path audit artifacts for semantic equivalence.

    python3 tools/v7_audit_equivalence.py serial.json parallel.json

The parallel audit runs the same rules and scenarios as the serial one in
separate processes. This establishes that the two artifacts agree on every
rule's status, detail and agreement flag, on the contract counts and
defects, on the scenario set, and on every scenario's result --- after
normalising the values that differ between any two runs of the SAME path:
temporary paths, content hashes and commit ids of throw-away synthetic
repositories, wall-clock seconds and the execution block itself. A
difference that survives the normalisation is substantive and exits 1.
"""
from __future__ import annotations

import json
import re
import sys

VOLATILE_KEYS = {"_seconds", "execution", "decisions_the_walk_ran_under"}
_HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
_HEX40 = re.compile(r"\b[0-9a-f]{40}\b")
_TMP = re.compile(r"/tmp/[^\s\"',)\]]+")


def normalise(value):
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in sorted(value.items())
                if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [normalise(v) for v in value]
    if isinstance(value, str):
        value = _HEX64.sub("<sha256>", value)
        value = _HEX40.sub("<sha1>", value)
        return _TMP.sub("<tmp>", value)
    return value


def _diff(a, b, path="", out=None):
    out = [] if out is None else out
    if type(a) is not type(b):
        out.append(f"{path}: type {type(a).__name__} != {type(b).__name__}")
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}.{k}: present in one artifact only")
            else:
                _diff(a[k], b[k], f"{path}.{k}", out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            _diff(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append(f"{path}: {str(a)[:80]!r} != {str(b)[:80]!r}")
    return out


def compare(serial: dict, parallel: dict) -> dict:
    findings: list[str] = []
    for key in ("n_rules", "n_agreeing", "by_status", "contract",
                "contract_defects"):
        findings += _diff(normalise(serial.get(key)),
                          normalise(parallel.get(key)), key)
    rules_a = {r["id"]: r for r in serial["rules"]}
    rules_b = {r["id"]: r for r in parallel["rules"]}
    if list(rules_a) != list(rules_b):
        findings.append("rules: order or membership differs")
    for rid in rules_a:
        if rid in rules_b:
            findings += _diff(normalise(rules_a[rid]),
                              normalise(rules_b[rid]), f"rules[{rid}]")
    if list(serial["scenarios"]) != list(parallel["scenarios"]):
        findings.append("scenarios: order or membership differs")
    for name in serial["scenarios"]:
        if name in parallel["scenarios"]:
            findings += _diff(normalise(serial["scenarios"][name]),
                              normalise(parallel["scenarios"][name]),
                              f"scenarios[{name}]")
    return {"equivalent": not findings, "findings": findings,
            "n_rules": serial["n_rules"], "n_scenarios":
            len(serial["scenarios"]),
            "serial_execution": serial.get("execution"),
            "parallel_execution": parallel.get("execution")}


def main() -> int:
    serial = json.load(open(sys.argv[1]))
    parallel = json.load(open(sys.argv[2]))
    result = compare(serial, parallel)
    print(json.dumps(result, indent=1, default=str))
    return 0 if result["equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
