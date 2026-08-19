"""Independent reimplementation of the registered target rule (A2).

A second implementation of the plain-language S0 rule that shares the
registered character predicate (Unicode ``str.isalpha``, the rule's own
definition of a letter) but none of the segmentation or counting code of
``verifiers/words.py`` / ``verifiers/target.py``: it maps non-letters to
spaces and splits, instead of scanning runs. It exists solely for the
Gate 1 reimplementation-concordance check: any disagreement with the
primary implementation on any reservoir response is an implementation
defect and fails the gate closed. It never scores anything.
"""
from __future__ import annotations


def s0_count_independent(text: str) -> int:
    """Lower-case, replace every non-letter with a space, split on
    whitespace, count words equal to 'however'."""
    lowered = text.lower()
    separated = "".join(ch if ch.isalpha() else " " for ch in lowered)
    return sum(1 for word in separated.split() if word == "however")


def concordance(items: list[dict]) -> dict:
    """Compare the primary and independent implementations on every item
    ({"item_id", "response_text"}); exact agreement is required."""
    from dci1v3.verifiers.target import s0_count

    mismatches = [item["item_id"] for item in items
                  if s0_count(item["response_text"])
                  != s0_count_independent(item["response_text"])]
    return {"items": len(items), "mismatches": mismatches,
            "agreement": 1.0 if not mismatches else
            1.0 - len(mismatches) / len(items)}
