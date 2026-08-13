"""spec — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class ConstraintSpec:
    constraint_id: str
    source_id: str
    name: str
    category: str
    mechanism: str
    generative_scope: Literal["sentence", "whole_text"]
    verifier_span: str
    role: Literal["target", "focal", "candidate", "unrelated", "neutral"]
    rule_family: str
    params: tuple[tuple[str, Any], ...] = ()
    origin: Literal["cse_pool", "shadow", "unrelated", "neutral"] = "cse_pool"
    pathway_removed: str = ""
    u_family: str = ""
    pathway_audit: str = ""
    # Declared logical relations, evaluated by hard eligibility without
    # inspecting any behaviour.
    incompatible_with: tuple[str, ...] = ()
    entails: tuple[str, ...] = ()
    # Bridge targets only: a sentence whose addition must not change the
    # verdict, which is what proves the rule does not read the sentence count.
    count_probe_sentence: str = ""

    @property
    def param_dict(self) -> dict[str, Any]:
        return dict(self.params)


def spec(*args, **kwargs) -> ConstraintSpec:
    return ConstraintSpec(*args, **kwargs)


def P(**kwargs) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted(kwargs.items()))
