"""A blinded human-review packet for the instruments §7.0-R3 added.

**What this is, exactly.** The v3 record contains a 56-item blind calibration
in which the deterministic verifier agreed with a human on 56 of 56, while
every autorater configuration scored between 71 and 98 per cent on the same
labels. That is the strongest evidence this programme has that the verifiers
measure what the instructions mean --- and every one of those 56 items is
`solo:A:n`. It anchors A, whose counting rule §7.0-R3 leaves untouched, and it
anchors nothing else. The ten families the amendment added have no human label
anywhere, and they are where the semantic doubt actually is: nobody has ever
labelled *"At most 12 percent of words may begin with a vowel"*, and the
sentence rule carries two over-counts registered as known and accepted.

So this packet points a human at those instruments and at nothing else.

**What this is not.** It is not §10.3. §10.3 requires an annotator independent
of the design and analysis team, marking features on natural responses, at
min(150, N_c) per verifier class --- and says in terms that author-performed
labels are never described as independent validation. A packet the study author
answers has exactly the standing the v3 record gave itself: *real, but not
independent external validation*. It cannot write `measurement_basis` and this
module offers no way to.

**Blinding.** The reviewer sees an instruction, an answer, and an opaque id.
The family, the severity, the verifier's verdict, the defect a case separates
and the case's own identifier all live in a separate key file that the review
command never opens. `assert_packet_blinded` checks that rather than trusting
it, because the identifier `mc-rf9-03-...` names the family in its second
field.

**Which cases it may draw from.** The §10.4-R2 calibration half is excluded, so
the held-out material for the autorater pathway stays untouched. What remains
overlaps the development half on purpose: the same items are being judged by a
program, so once both are in, human and judge are comparable item by item ---
which is what the v3 forensics could do and is the reason its conclusion was
possible.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import canonical_json, sha_text

from dci1v4r3.stages.microcase import (
    CONVENTIONS_TEXT, DEFECT_KINDS, Microcase, _pool, build_cases, split_cases,
)
from dci1v4r3.verifiers.constraints import FAMILIES, R3_FAMILY_IDS

__all__ = ["LABELS", "REVIEWER_BRIEF", "PACKET_FIELDS", "KEY_ONLY_FIELDS",
           "SELECTION_SEED", "candidates", "select", "build_packet",
           "assert_packet_blinded", "wilson_upper", "agreement_report"]

#: E8's vocabulary, carried so the two reviews are comparable item for item.
LABELS = ("SATISFIES", "VIOLATES", "UNSURE")

#: §14.2's ordering seed, reused so the presentation order is reproducible and
#: is not a function of anything about the cases.
SELECTION_SEED = 20260821

PACKET_FIELDS = ("item_id", "instruction", "answer", "answer_sha256")
#: Everything a reviewer must not see. Checked, not trusted.
KEY_ONLY_FIELDS = ("case_id", "family", "statistic", "severity", "form",
                   "correct", "discriminates", "covers", "verdict")

REVIEWER_BRIEF = f"""\
You are deciding whether a short ANSWER satisfies a short INSTRUCTION.

Answer SATISFIES, VIOLATES, or UNSURE. Use UNSURE only when the instruction
genuinely does not determine the case --- not when the case is merely fiddly.

Judge only the instruction as written. The answers are fragments: do not judge
topic, usefulness, style or length.

{CONVENTIONS_TEXT}

Nothing tells you which checker produced which verdict, and nothing will until
every item is committed.
"""


def candidates() -> list[Microcase]:
    """Every §7.0-R3 microcase outside §10.4-R2's held-out half."""
    held_out = {c.case_id for c in split_cases(build_cases())["calibration"]}
    return [c for c in _pool(list(R3_FAMILY_IDS))
            if c.case_id not in held_out]


def _priority(case: Microcase, covered: set[str]) -> tuple:
    """Prefer a case that separates a defect kind not yet in the packet."""
    fresh = [d for d in case.discriminates if d not in covered]
    return (0 if fresh else 1, -len(fresh), case.case_id)


def select(pool: Sequence[Microcase], *, items: int) -> list[Microcase]:
    """The registered selection. Deterministic, and reads no label.

    Equal shares per **numerator**, because the numerator is what the
    amendment added and what has no anchor; the remainder goes to the
    numerators with the largest candidate pools, alphabetically among ties.
    Within a numerator the scarce verdict is served first --- `semicolon` has
    one satisfying case in the whole pool, and a rule that alternated blindly
    would drop it --- and then cases that separate a defect kind the packet
    does not yet cover. Ties break on the case id.

    A final pass levels the two verdicts to within one, swapping the fewest
    items and taking from the numerator with the largest surplus. The balance
    is load bearing: a reviewer who answers SATISFIES to everything must score
    near one half, not near one.
    """
    by_statistic: dict[str, list[Microcase]] = {}
    for case in pool:
        by_statistic.setdefault(FAMILIES[case.kind].statistic_id,
                                []).append(case)
    statistics = sorted(by_statistic)
    if not statistics:
        raise ProtocolError("no §7.0-R3 candidates to draw from")

    share, remainder = divmod(items, len(statistics))
    extra = sorted(statistics, key=lambda s: (-len(by_statistic[s]), s))
    quota = {s: share + (1 if s in extra[:remainder] else 0)
             for s in statistics}

    covered: set[str] = set()
    chosen: dict[str, list[Microcase]] = {}
    for statistic in sorted(statistics,
                            key=lambda s: (min(
                                sum(1 for c in by_statistic[s] if c.correct),
                                sum(1 for c in by_statistic[s]
                                    if not c.correct)), s)):
        taken: list[Microcase] = []
        sides = {True: [c for c in by_statistic[statistic] if c.correct],
                 False: [c for c in by_statistic[statistic] if not c.correct]}
        want = min(sides, key=lambda k: (len(sides[k]), not k))
        while len(taken) < quota[statistic] and (sides[True] or sides[False]):
            queue = sides[want] or sides[not want]
            queue.sort(key=lambda c: _priority(c, covered))
            case = queue.pop(0)
            taken.append(case)
            covered.update(case.discriminates)
            want = not want
        chosen[statistic] = taken

    return _level(chosen, by_statistic, covered)


def _level(chosen: dict[str, list[Microcase]],
           by_statistic: Mapping[str, list[Microcase]],
           covered: set[str]) -> list[Microcase]:
    """Bring the two verdicts to within one of each other."""
    flat = [c for group in chosen.values() for c in group]
    while True:
        satisfied = sum(1 for c in flat if c.correct)
        gap = 2 * satisfied - len(flat)
        if abs(gap) <= 1:
            break
        over = gap > 0
        picked = sorted((s for s in chosen
                         if any(c.correct is over for c in chosen[s])
                         and any(c.correct is not over
                                 and c not in chosen[s]
                                 for c in by_statistic[s])),
                        key=lambda s: (-sum(1 for c in chosen[s]
                                            if c.correct is over), s))
        if not picked:
            break
        statistic = picked[0]
        drop = next(c for c in chosen[statistic] if c.correct is over)
        add = min((c for c in by_statistic[statistic]
                   if c.correct is not over and c not in chosen[statistic]),
                  key=lambda c: _priority(c, covered))
        chosen[statistic] = [add if c is drop else c
                             for c in chosen[statistic]]
        flat = [c for group in chosen.values() for c in group]
    return flat


def build_packet(items: int = 25) -> dict[str, Any]:
    """The blinded packet and its sealed key, as one object with two halves."""
    selected = select(candidates(), items=items)
    order = list(range(len(selected)))
    random.Random(SELECTION_SEED).shuffle(order)

    packet: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    for position, index in enumerate(order):
        case = selected[index]
        item_id = f"hr-{position:02d}-" + hashlib.sha256(
            f"{SELECTION_SEED}|{case.case_id}".encode()).hexdigest()[:8]
        packet.append({
            "item_id": item_id,
            "instruction": case.instruction,
            "answer": case.text,
            "answer_sha256": hashlib.sha256(case.text.encode()).hexdigest()})
        family = FAMILIES[case.kind]
        key.append({
            "item_id": item_id, "case_id": case.case_id,
            "family": case.kind, "statistic": family.statistic_id,
            "form": family.form, "severity": case.severity,
            "verdict": "SATISFIES" if case.correct else "VIOLATES",
            "correct": case.correct,
            "discriminates": list(case.discriminates),
            "covers": case.covers})
    assert_packet_blinded(packet)
    return {"packet": packet, "key": key,
            "packet_hash": sha_text(canonical_json(packet)),
            "key_hash": sha_text(canonical_json(key)),
            "items": len(packet),
            "satisfies": sum(1 for k in key if k["correct"]),
            "violates": sum(1 for k in key if not k["correct"]),
            "statistics": sorted({k["statistic"] for k in key}),
            "defects_separated": sorted(
                {d for k in key for d in k["discriminates"]}),
            "achievable_upper_bound_at_zero_disagreements":
                wilson_upper(0, len(packet))}


def assert_packet_blinded(packet: Sequence[Mapping[str, Any]]) -> None:
    """No packet item may carry anything that names the instrument.

    The microcase identifier names the family in its second field, so this is
    not a hypothetical: `mc-rf9-03-...` would tell a reviewer the numerator
    before they read the instruction.
    """
    for item in packet:
        stray = [f for f in KEY_ONLY_FIELDS if f in item]
        if stray:
            raise ProtocolError(
                f"{item.get('item_id')}: the packet carries key-only "
                f"field(s) {stray}")
        if set(item) != set(PACKET_FIELDS):
            raise ProtocolError(
                f"{item.get('item_id')}: a packet item carries exactly "
                f"{PACKET_FIELDS}, not {sorted(item)}")
        for family in FAMILIES:
            if family.lower() in item["item_id"].lower():
                raise ProtocolError(
                    f"{item['item_id']} names the family {family} in the one "
                    "string the reviewer sees for every item")


def wilson_upper(disagreements: int, n: int, z: float = 1.6448536269514722
                 ) -> float:
    """§10.3's statistic: the one-sided 95% Wilson upper bound."""
    if n <= 0:
        raise ProtocolError("no items")
    p = disagreements / n
    denominator = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denominator
    return centre + half


def agreement_report(key: Sequence[Mapping[str, Any]],
                     labels: Mapping[str, str]) -> dict[str, Any]:
    """Human against the deterministic verifier, per numerator and pooled.

    `UNSURE` is neither an agreement nor a disagreement: it is coverage the
    review did not deliver, and it is reported as its own number rather than
    folded into either side, exactly as the v3 review's frozen rules do for a
    judge's operational failure.
    """
    by_statistic: dict[str, dict[str, int]] = {}
    unsure: list[str] = []
    discordant: list[dict[str, Any]] = []
    agreed = compared = 0
    for entry in key:
        label = labels.get(entry["item_id"])
        bucket = by_statistic.setdefault(
            entry["statistic"], {"n": 0, "agreed": 0, "unsure": 0})
        bucket["n"] += 1
        if label is None:
            continue
        if label == "UNSURE":
            bucket["unsure"] += 1
            unsure.append(entry["item_id"])
            continue
        compared += 1
        if label == entry["verdict"]:
            agreed += 1
            bucket["agreed"] += 1
        else:
            discordant.append({"item_id": entry["item_id"],
                               "family": entry["family"],
                               "statistic": entry["statistic"],
                               "severity": entry["severity"],
                               "covers": entry["covers"],
                               "human": label, "verifier": entry["verdict"],
                               "separates": entry["discriminates"]})
    disagreements = compared - agreed
    return {
        "labelled": sum(1 for e in key if e["item_id"] in labels),
        "compared": compared, "unsure": len(unsure), "unsure_items": unsure,
        "agreed": agreed, "disagreements": disagreements,
        "agreement": agreed / compared if compared else None,
        "wilson_upper_on_disagreement":
            wilson_upper(disagreements, compared) if compared else None,
        "section_10_3_threshold": 0.10,
        "meets_threshold_numerically": (
            compared > 0
            and wilson_upper(disagreements, compared) <= 0.10),
        "per_statistic": {
            s: {**v, "agreement": (v["agreed"] / (v["n"] - v["unsure"]))
                if v["n"] - v["unsure"] else None}
            for s, v in sorted(by_statistic.items())},
        "discordant": discordant,
        "standing": (
            "author-performed unless the annotator is independent of the "
            "design and analysis team; §10.3 says in terms that "
            "author-performed labels are never described as independent "
            "validation. This is a diagnostic anchor for the instruments "
            "§7.0-R3 added, of the same standing the v3 record gave its own "
            "56-item review, and it does not write a measurement basis"),
        "scope": (
            "microcases, not natural responses, and one packet rather than "
            "min(150, N_c) per verifier class. Even at zero disagreements "
            "this is not a §10.3 pass; the bound is reported because it is "
            "§10.3's own statistic and makes the two reviews comparable"),
        "defect_kinds": list(DEFECT_KINDS),
    }
