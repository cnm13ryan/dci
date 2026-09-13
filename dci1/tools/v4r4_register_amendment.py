"""What moved when the decisions register gained B6 and B7, and what did not.

`dci1/DECISIONS_V4R4.md` is one of four protocol documents, so its bytes are
inside `protocol_hash`. The researcher closed E3 and E5 after Gate 1 returned
PASS and before Gate 2 began, which means the register --- and therefore the
protocol hash --- moved away from the value Gate 1 sealed.

§10.6 forbids carrying a stale hash forward on the grounds that behaviour looks
unchanged. The remedy is not to rewrite the sealed record and not to re-run a
passed gate: it is to make the delta resolvable. Gate 1's record carries the
per-document hash table, so this tool recomputes both sides and states three
things a reader can check independently:

1. exactly which protocol documents changed, by hash, before and after;
2. that every measurement hash --- verifier, wordings, specification, mutation,
   measurement rule --- is identical, so no instrument, wording, predicate or
   criterion moved with the register;
3. that the sealed Gate-1 records still verify and still name the old hashes,
   because nothing rewrote them.

    ./.venv/bin/python tools/v4r4_register_amendment.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4r4.engine.context import registered_context           # noqa: E402
from dci1v4r4.engine.paths import model_tree                     # noqa: E402
from dci1v4r4.engine.transitions import read_stage_record        # noqa: E402
from dci1v4r4.protocol import constants as C                     # noqa: E402
from dci1v4r4.protocol.revision import (                         # noqa: E402
    PROTOCOL_DOCUMENTS, document_hashes, protocol_hash,
)
from dci1v4r4.stages.gate1 import measurement_rule_hash          # noqa: E402
from dci1v4r4.stages.mutation import mutation_hash               # noqa: E402
from dci1v4r4.stages.specification import (                      # noqa: E402
    specification_hash, wordings_hash,
)
from dci1v4r4.verifiers import verifier_source_hash              # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r4" / "register_amendment.json"

#: The commit whose tree Gate 1 ran against. Read off the sealed records rather
#: than assumed, so a mismatch is a finding and not a silent comparison against
#: the wrong tree.
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")


def _at_commit(commit: str, relative: str) -> str:
    blob = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=REPO,
                          capture_output=True)
    if blob.returncode != 0:
        return "MISSING"
    return hashlib.sha256(blob.stdout).hexdigest()


def main() -> int:
    context = registered_context()

    sealed: dict[str, dict[str, object]] = {}
    for model in MODELS:
        record = read_stage_record(model_tree(context, model), C.STAGE_GATE1)
        sealed[model] = {
            "protocol_hash": record["protocol_hash"],
            "documents": record["revision"]["documents"],
            "producing_commit": record["provenance"]["producing_commit"],
            "canonical_verifier_hash": record["canonical_verifier_hash"],
            "wordings_hash": record["wordings_hash"],
            "specification_hash": record["specification_hash"],
            "mutation_hash": record["mutation_hash"],
            "measurement_rule_hash": record["measurement_rule_hash"],
            "outcome": record["outcome"],
        }

    one = sealed[MODELS[0]]
    disagreeing = [m for m, s in sealed.items()
                   if s["protocol_hash"] != one["protocol_hash"]
                   or s["documents"] != one["documents"]]
    commit = str(one["producing_commit"])

    now_documents = document_hashes()
    moved = {relative: {"sealed": one["documents"][relative],   # type: ignore
                        "now": now_documents[relative],
                        "at_producing_commit": _at_commit(commit, relative)}
             for relative in PROTOCOL_DOCUMENTS
             if now_documents[relative] != one["documents"][relative]}  # type: ignore
    unchanged = [relative for relative in PROTOCOL_DOCUMENTS
                 if relative not in moved]

    measurement_now = {
        "canonical_verifier_hash": verifier_source_hash(),
        "wordings_hash": wordings_hash(),
        "specification_hash": specification_hash(),
        "mutation_hash": mutation_hash(),
        "measurement_rule_hash": measurement_rule_hash(),
    }
    measurement_moved = {k: {"sealed": one[k], "now": v}
                         for k, v in measurement_now.items()
                         if one[k] != v}

    problems: list[str] = []
    if disagreeing:
        problems.append(
            f"the four Gate-1 records do not agree on the protocol they "
            f"sealed: {disagreeing}")
    if measurement_moved:
        problems.append(
            "a measurement hash moved with the register, so this is not a "
            f"register-only amendment: {sorted(measurement_moved)}")
    if set(moved) - {"dci1/DECISIONS_V4R4.md"}:
        problems.append(
            "a protocol document other than the decisions register moved: "
            f"{sorted(set(moved) - {'dci1/DECISIONS_V4R4.md'})}")
    for relative, entry in moved.items():
        if entry["sealed"] != entry["at_producing_commit"]:
            problems.append(
                f"{relative} as sealed by Gate 1 is not what the producing "
                f"commit {commit[:12]} holds; the record and the tree "
                "disagree about what ran")

    report = {
        "artifact_type": "v4r4-register-amendment",
        "what_this_is":
            "the decisions register gained B6 and B7 after Gate 1 passed and "
            "before Gate 2 began. The register is a protocol document, so the "
            "protocol hash moved. This records the delta rather than "
            "absorbing it",
        "what_this_is_not":
            "a re-seal. No Gate-1 record is rewritten, no gate is re-run, and "
            "the sealed hashes below are read out of the signed records as "
            "they stand",
        "decisions_entered": {
            "B6": "closes E3: the requirement-verb construction is accepted, "
                  "so `needs {q}` reads as the registered `>= q`. It ratifies "
                  "the classification the specification module already "
                  "produced when Gate 1 ran; no wording, predicate or row "
                  "changes",
            "B7": "closes E5: §12.6's registered candidate expansion is not "
                  "invoked, and C4's zero leave-one-family-out margin on three "
                  "models is carried as a recorded limitation. Declining an "
                  "option changes no threshold and no candidate family",
        },
        "gate1_producing_commit": commit,
        "sealed_by_gate1": sealed,
        "protocol_hash": {
            "sealed_by_gate1": one["protocol_hash"],
            "now": protocol_hash(),
            "moved": one["protocol_hash"] != protocol_hash(),
        },
        "documents": {
            "moved": moved,
            "unchanged": unchanged,
            "rule": "the protocol hash covers the bytes of every document in "
                    "PROTOCOL_DOCUMENTS. A register that could change without "
                    "moving it would be a hole in the binding",
        },
        "measurement_hashes": {
            "sealed_and_recomputed": measurement_now,
            "moved": measurement_moved,
            "holds": not measurement_moved,
            "meaning": "the instrument, its wordings, its specification, its "
                       "mutation suite and the Gate-1 rule itself are "
                       "byte-identical to what the gate certified. The "
                       "amendment is confined to the decisions register",
        },
        "gate_2_may_run": not problems,
        "passed": not problems,
        "problems": problems,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"passed": report["passed"],
                      "problems": problems,
                      "protocol_hash": report["protocol_hash"],
                      "documents_moved": sorted(moved),
                      "measurement_hashes_moved": sorted(measurement_moved)},
                     indent=1))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
