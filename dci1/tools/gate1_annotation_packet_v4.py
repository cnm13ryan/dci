"""Build the §10.4 criterion-4 annotation packet. Prepares; never labels.

The researcher chose the §10.4 sizing over the §10.3 sizing: 11 discordant
items plus matched concordant controls, rather than 692 items for a
`human_validated` basis that is unreachable because the annotator is the study
author.

**Blinding is stronger here than in v3.** The v3 sample file carries `model` and
`verifier_class` on every sample and relies on the review app not rendering
them; anyone who opens the JSON sees the answers. This writes two files: a
**blind packet** carrying only id, constraint and response, and a **sealed key**
carrying model, verifier class, margin, stratum, both conditions' labels and
whether the item is discordant. The key has its own hash and is opened only
after every label is committed. The annotator cannot see the answer even by
reading the packet.

**What this does NOT do.** It starts no session. §10.3's tool-assisted protocol
requires the annotator to mark each qualifying feature with the interface
tallying the annotator's own marks, and the v3 review app does not do that -- it
takes a bare S/V/U judgment. That marking interface is an addition the v3
tooling needs before a session can satisfy the registered protocol, and it is
recorded here as outstanding rather than quietly skipped.

Usage:
  PYTHONPATH=src python tools/gate1_annotation_packet_v4.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))
sys.path.insert(0, str(DCI1 / "tools"))

from dci1v4.protocol.hashing import sha_obj, sha_text                # noqa: E402
from dci1v4.protocol.seeds import GATE1_SAMPLE_SEED                  # noqa: E402

import gate1_autorater_v4 as ar                                      # noqa: E402

OUT = DCI1 / "reports" / "gate1_v4" / "annotation"
SEED_DOMAIN = "gate1:annotation:v4"


class _Stream:
    """The v3 sampling stream, re-derived: sha256 chaining from a seeded root."""

    def __init__(self, seed: int, label: str):
        self._state = hashlib.sha256(
            f"{SEED_DOMAIN}:{seed}:{label}".encode()).digest()

    def _next(self) -> int:
        self._state = hashlib.sha256(self._state).digest()
        return int.from_bytes(self._state[:8], "big")

    def sample(self, candidates: list, k: int) -> list:
        pool = list(candidates)
        out = []
        for _ in range(min(k, len(pool))):
            out.append(pool.pop(self._next() % len(pool)))
        return out


def build() -> dict[str, Any]:
    development = ar.split_pool(ar.build_items())["development"]
    sample = ar.subsample(development, 48)
    index = {i["item_id"]: i for i in sample}

    conditions = {}
    for name in ("carried-medium", "v4prompt-medium", "v4prompt-high"):
        path = DCI1 / "reports" / "gate1_v4" / "conditions" / f"{name}.json"
        conditions[name] = json.loads(path.read_text())["judgments"]

    # Discordance among the conditions that survive to criterion 4 under the
    # threshold reading. An item counts only where BOTH conditions returned a
    # verdict; a missing verdict is a coverage fact, not a disagreement.
    names = sorted(conditions)
    discordant, concordant = set(), set()
    for item_id in index:
        labels = {n: conditions[n].get(item_id) for n in names}
        present = [v for v in labels.values() if v is not None]
        if len(present) < 2:
            continue
        (discordant if len(set(present)) > 1 else concordant).add(item_id)

    def by_stratum(ids):
        out: dict[str, list[str]] = {}
        for i in sorted(ids):
            out.setdefault(ar.stratum(index[i]), []).append(i)
        return out

    want = {k: len(v) for k, v in by_stratum(discordant).items()}
    pool = by_stratum(concordant)
    stream = _Stream(GATE1_SAMPLE_SEED, "controls")
    controls: list[str] = []
    shortfall: dict[str, int] = {}
    for name in sorted(want):
        take = stream.sample(pool.get(name, []), want[name])
        controls += take
        if len(take) < want[name]:
            shortfall[name] = want[name] - len(take)
        pool[name] = [i for i in pool.get(name, []) if i not in take]
    # Top up from any stratum, so the control arm matches the discordant arm in
    # size even where a stratum is nearly all discordant.
    remaining = sorted(i for v in pool.values() for i in v)
    controls += stream.sample(remaining, sum(shortfall.values()))

    items = sorted(discordant) + sorted(controls)

    # **The presentation id is opaque.** The real item id is
    # "<model>:ladder:<kind>:<severity>:<topic>", which names the model, and
    # §10.3 requires the model label not be visible. The v3 packet carried ids
    # of the same shape ("gemma-3n-e2b-it::gate1_validation:geography-05:solo:
    # A:3:0"), so v3's blinding hid the verdict but not the model. This mints a
    # deterministic opaque label instead and puts the mapping in the sealed key.
    def opaque(item_id: str) -> str:
        digest = hashlib.sha256(
            f"{SEED_DOMAIN}:presentation:{GATE1_SAMPLE_SEED}:{item_id}"
            .encode()).hexdigest()
        return f"g1c4-{digest[:12]}"

    labels_out = {i: opaque(i) for i in items}
    if len(set(labels_out.values())) != len(items):
        raise SystemExit("opaque presentation ids collided")
    blind = [{"id": labels_out[i],
              "constraint": index[i]["constraint"],
              "response": index[i]["response"]}
             for i in items]
    stream2 = _Stream(GATE1_SAMPLE_SEED, "presentation")
    order = stream2.sample(blind, len(blind))       # discordant/control mixed
    key = {labels_out[i]: {"item_id": i,
               "model": index[i]["model_key"],
               "instrument": index[i]["instrument"],
               "severity": index[i]["severity"],
               "verifier_class": index[i]["verifier_class"],
               "margin": index[i]["margin"],
               "stratum": ar.stratum(index[i]),
               "arm": "discordant" if i in discordant else "control",
               "condition_labels": {n: conditions[n].get(i) for n in names},
               "response_sha256": sha_text(index[i]["response"])}
           for i in items}

    return {
        "packet": {
            "artifact": "§10.4 criterion-4 annotation packet (BLIND)",
            "set_name": "gate1-v4-criterion4",
            "seed": GATE1_SAMPLE_SEED, "seed_domain": SEED_DOMAIN,
            "items": len(order),
            "samples": order,
            "contains": ("an opaque presentation id, the constraint "
                         "and the response, and nothing else"),
            "excluded_from_this_file": ("the real item id, the model, the "
                                        "verifier class, the margin, the "
                                        "stratum, the arm, and every "
                                        "condition's label -- all in the "
                                        "sealed key"),
        },
        "key": {
            "artifact": "§10.4 criterion-4 annotation key (SEALED)",
            "open_after": "every label is committed, and never before",
            "items": len(key), "key": key,
        },
        "manifest": {
            "artifact": "§10.4 criterion-4 annotation packet manifest",
            "classification": ("Gate 1 input evidence. No session started. "
                               "Author labels are diagnostic evidence and "
                               "§10.4 hierarchy input, NEVER independent "
                               "validation."),
            "chosen_sizing": "§10.4",
            "rejected_sizing": {
                "rule": "§10.3, min(150, N_c) per class per instrument",
                "items": 692, "hours": [5.8, 11.5],
                "why_rejected": ("§10.3 requires an annotator independent of "
                                 "the design and analysis team; the annotator "
                                 "is the study author, so the basis stays "
                                 "HUMAN_VALIDATION_UNAVAILABLE however many "
                                 "items are labelled"),
            },
            "conditions_compared": names,
            "discordant": {"n": len(discordant), "by_stratum": want},
            "controls": {"n": len(controls),
                         "by_stratum": {k: len(v) for k, v in
                                        by_stratum(controls).items()},
                         "stratum_shortfall": shortfall,
                         "shortfall_note": (
                             "A:fail:margin_larger is 7 of 8 discordant, so "
                             "matched concordant controls do not exist in that "
                             "stratum; the shortfall is topped up from the "
                             "concordant pool at large and recorded rather "
                             "than hidden")},
            "total_to_label": len(order),
            "estimated_minutes": [round(len(order) * 30 / 60),
                                  round(len(order) * 60 / 60)],
            "presentation_order": "seeded; discordant and control interleaved",
            "presentation_ids_are_opaque": True,
            "blinding_note": ("the v3 packet's ids named the model "
                              "(\"gemma-3n-e2b-it::gate1_validation:...\"), so "
                              "v3 blinded the verdict but not the model label. "
                              "This packet mints opaque ids and keeps the "
                              "mapping in the sealed key."),
            "packet_hash": sha_obj(order),
            "key_hash": sha_obj(key),
            "outstanding_before_a_session_can_run": [
                ("the tool-assisted marking interface: §10.3 requires the "
                 "annotator to mark each qualifying feature with the interface "
                 "tallying the annotator's OWN marks, and the v3 review app "
                 "takes a bare S/V/U judgment instead. This is the registered "
                 "fix for v3's failure mode -- all four v3 disagreements were "
                 "unaided off-by-one counting errors at margin one, and four "
                 "independent recounts reproduced the verifier every time."),
                ("a B-class reviewer definition set: the v3 definitions are "
                 "A-specific (an occurrence-count instruction) and 1 of the 22 "
                 "items is B-class"),
                "explicit researcher agreement to run the session",
            ],
            "protocol_properties_required": [
                "blind: no arm, model label, companion, verifier verdict or "
                "other annotator's work visible",
                "tool-assisted marking, no automatic detection or counting",
                "chained, hash-pinned records",
                "seeded stratified sample, per instrument",
                "fail-class stratification by realised margin, reported "
                "separately",
            ],
        },
    }


def main() -> int:
    built = build()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, payload in (("packet_blind.json", built["packet"]),
                          ("key_sealed.json", built["key"]),
                          ("manifest.json", built["manifest"])):
        (OUT / name).write_text(
            json.dumps(payload, indent=1, sort_keys=True) + "\n")
    m = built["manifest"]
    print(json.dumps({k: m[k] for k in
                      ("discordant", "controls", "total_to_label",
                       "estimated_minutes", "packet_hash", "key_hash")},
                     indent=1))
    print("written:", ", ".join(sorted(p.name for p in OUT.iterdir())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
