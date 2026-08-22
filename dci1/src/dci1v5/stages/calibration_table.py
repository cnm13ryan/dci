"""The selection input, and the schema that makes §13.11 executable.

Everything the §13 rules read is **solo, chance and counterfactual-chance
quantities on the calibration topics, and nothing else**. ``CalibrationRow``
is the structure that makes that true rather than asserted: it has no field in
which a composed outcome could travel, and ``load_calibration_table`` refuses
a mapping that offers one *before a value is read*.

Three refusals, and each closes a different route:

1. **A composed field by name.** The forbidden list is deliberately generous:
   a near-miss spelling is refused too, because the point is to make the
   mistake impossible rather than to catch the exact word.
2. **An unknown field.** The schema is **closed**, so a new column cannot
   smuggle in a composed quantity under an unlisted name. This is the refusal
   that matters most, because the first one can only catch what it was told
   to look for.
3. **A permitted field whose source is wrong.** ``kappa_under_b`` and
   ``displacement`` are on the permitted list by name and are the two
   quantities in v5 that read rows produced *under B*. §13.11 therefore
   additionally requires the supplying rows to be load-one cells whose single
   present constraint is B, and ``KappaUnderBSource`` carries enough to refuse
   a row from the wrong load, treatment, model, operating point or split.

§22 records the standing of the two: kappa is pre-treatment for the companion
because it is measured where the companion is absent; kappa(R|B) is
pre-treatment for the companion in the same sense, and is *not* pre-treatment
with respect to the pair (c, B), which is stated plainly rather than glossed.
§13.6 registers its only use.
"""
from __future__ import annotations

from dataclasses import dataclass, fields as dataclass_fields
from typing import Any, Iterable, Mapping

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C
from dci1v5.stages.interaction import (
    KappaUnderBSource, assert_kappa_under_b_source, displacement,
    projected_compliance,
)
from dci1v5.verifiers.constraints import (
    FAMILIES, discourse_role, family_class, family_tier, feature_group,
)

__all__ = ["CalibrationRow", "load_calibration_table",
           "FORBIDDEN_CALIBRATION_FIELDS", "PERMITTED_UNDER_B_FIELDS",
           "instructed_compliance", "tie_key", "SPLITS"]

#: §13.9's splits, plus the pooled table §13.8 selects on.
SPLITS = (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")

#: §13.11. Any of these in a calibration table means the table has been built
#: from composed cells, and a selection rule must never see one.
FORBIDDEN_CALIBRATION_FIELDS = (
    "composed", "composed_compliance", "delivery_loss", "d_b_from", "loss",
    "delta_r", "delta_j", "delta", "xi", "companion", "pair", "joint",
    "joint_state", "joint_success", "uptake", "composed_uptake",
    "b_with", "with_b", "interference", "delta_difficulty", "residual",
    "ord_", "order_contrast", "headroom_table", "gate4", "gate_4",
)

#: The two fields whose rows are produced under B, permitted **by name** and
#: validated by source. Listed here so that the exemption is a registered
#: fact rather than a hole in the forbidden list.
PERMITTED_UNDER_B_FIELDS = ("kappa_under_b", "kappa_under_b_source",
                            "displacement", "projected_compliance")


def tie_key(value: float) -> float:
    """Registered tie-breaks fire on exact ties that binary floats do not
    represent. Every selection key is rounded through this first."""
    return round(value, 12)


def instructed_compliance(solo: float, chance: float) -> float:
    """§13.2's registered difficulty coordinate.

    ``(solo - chance) / (1 - chance)``: the share of the achievable
    improvement over chance that stating the constraint delivers. A negative
    value means stating the constraint made the model satisfy it *less* often
    than not stating it; that is a real measurement and §13.4's rules make
    such a rung inadmissible everywhere.

    A Tier-1 marker family is chance-free, so iota equals its raw solo
    compliance and carries **none** of the 1/(1-kappa) variance amplification.
    That is one of the four reasons §7.5 gives for the same-form pool, and it
    is why v5 can demote iota from the admission coordinate without losing the
    only coordinate comparable across classes.
    """
    if not 0.0 <= chance <= 1.0 or not 0.0 <= solo <= 1.0:
        raise ProtocolError(f"compliance out of range: solo={solo}, "
                            f"chance={chance}")
    if chance >= C.CHANCE_DEGENERACY_MAX:
        raise ProtocolError(
            f"chance compliance {chance} is at or above "
            f"{C.CHANCE_DEGENERACY_MAX}: iota is not defined and §11.2 "
            "records DIFFICULTY_COORDINATE_DEGENERATE instead")
    return (solo - chance) / (1.0 - chance)


@dataclass(frozen=True)
class CalibrationRow:
    """One candidate severity, measured on solo, unconstrained and B-solo cells.

    There is no field here in which a composed outcome could travel. That is
    the point (§13.11).
    """

    kind: str
    severity: int
    #: Which of §6.2's two disjoint 96-topic splits, or the pooled 192.
    split: str
    model_key: str
    #: §12.3's calibration at M_cal draws.
    solo_compliance: float
    #: §25's unconstrained cell on the same topics.
    chance_compliance: float
    solo_vacuity: float
    #: §13.6. R's verdict on the B-solo cell at m*, where R is ABSENT. None
    #: when it was not measured, which §13.6 treats as a failure and never as
    #: a pass.
    kappa_under_b: float | None = None
    kappa_under_b_source: KappaUnderBSource | None = None
    #: §7.7 and §10.7's structural properties, established before any rate.
    specification_complete: bool = True
    wording_within_caliper: bool = True
    parse_independent: bool = True
    witnesses_pass: bool = True
    #: §7.7's *realistic* witness: the joint witness against B at m* lies
    #: inside §8.5's stem band.
    realistic_witness_pass: bool = True
    #: Sample sizes for the Wilson and Newcombe intervals. The unit is the
    #: TOPIC, never the draw.
    n_topics: int = C.N_CALIBRATION
    n_draws: int = C.M_CAL
    #: §12.2's disjoint pre-screen table. Read by §12.7's Tier-3 measurement
    #: ORDERING and by nothing else --- no admission rule in §13 reads a
    #: pre-screen quantity, and v4r4's pre-screen distance caliper is deleted.
    prescreen_solo_compliance: float | None = None
    prescreen_chance_compliance: float | None = None
    #: §13.7's per-topic values, for the split-difference bootstrap.
    per_topic_solo: tuple[float, ...] = ()
    #: diagnostics, reported and never selected on
    median_words: float | None = None
    graded_mean: float | None = None

    def __post_init__(self):
        if self.split not in SPLITS:
            raise ProtocolError(
                f"{self.label}: {self.split!r} is not a registered split; "
                f"registered: {SPLITS}")
        if self.kind not in FAMILIES:
            raise ProtocolError(
                f"{self.kind!r} is not a registered v5 family; a calibration "
                "row describes a candidate companion")

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.severity}"

    @property
    def iota(self) -> float:
        return instructed_compliance(self.solo_compliance,
                                     self.chance_compliance)

    @property
    def lift(self) -> float:
        """§13.4's H_R = p_solo - kappa, the unnormalised form."""
        return self.solo_compliance - self.chance_compliance

    @property
    def displacement(self) -> float | None:
        if self.kappa_under_b is None:
            return None
        return displacement(self.chance_compliance, self.kappa_under_b)

    @property
    def projected_compliance(self) -> float | None:
        if self.kappa_under_b is None:
            return None
        return projected_compliance(self.kappa_under_b, self.iota)

    @property
    def prescreen_iota(self) -> float | None:
        if self.prescreen_solo_compliance is None or \
                self.prescreen_chance_compliance is None:
            return None
        return instructed_compliance(self.prescreen_solo_compliance,
                                     self.prescreen_chance_compliance)

    @property
    def structural_tier(self) -> int:
        return family_tier(self.kind)

    @property
    def feature_group(self) -> str:
        return feature_group(self.kind)

    @property
    def discourse_role(self) -> str:
        return discourse_role(self.kind)

    @property
    def constraint_class(self) -> str:
        return family_class(self.kind)


_KNOWN_FIELDS = {f.name for f in dataclass_fields(CalibrationRow)}


def load_calibration_table(rows: Iterable[Mapping[str, Any]], *,
                           model_key: str, m_star: int, split: str
                           ) -> list[CalibrationRow]:
    """§13.11: build the selection input, refusing a composed field.

    The refusal is on the **schema**, before a value is read, so a table that
    merely carries a composed column is rejected even if no rule would have
    used it. ``kappa_under_b``'s source is then validated against the
    replication's own model, operating point and split, which is the check
    §19 test 2 registers.
    """
    if split not in SPLITS:
        raise ProtocolError(f"{split!r} is not a registered split")
    out: list[CalibrationRow] = []
    for row in rows:
        offending = sorted(
            k for k in row
            if k not in PERMITTED_UNDER_B_FIELDS
            and any(bad in k.lower() for bad in FORBIDDEN_CALIBRATION_FIELDS))
        if offending:
            raise ProtocolError(
                "§13.11: a selection rule may read only solo, chance and "
                "counterfactual-chance quantities on the calibration topics; "
                f"this table carries composed fields {offending}")
        unknown = sorted(set(row) - _KNOWN_FIELDS)
        if unknown:
            raise ProtocolError(
                f"unknown calibration fields {unknown}; the selection input "
                "schema is closed so that a new column cannot smuggle in a "
                "composed quantity under an unlisted name")
        record = CalibrationRow(**row)
        if record.split != split:
            raise ProtocolError(
                f"{record.label}: row declares split {record.split!r} and the "
                f"table is {split!r}")
        if record.model_key != model_key:
            raise ProtocolError(
                f"{record.label}: row declares model {record.model_key!r} and "
                f"the replication is {model_key!r}")
        if record.kappa_under_b is not None:
            if record.kappa_under_b_source is None:
                raise ProtocolError(
                    f"{record.label}: §13.11 admits kappa_under_b only with "
                    "the source of the rows that supplied it, so that the "
                    "load-one B-solo condition can be refused rather than "
                    "trusted")
            assert_kappa_under_b_source(
                record.kappa_under_b_source, model_key=model_key,
                m_star=m_star, split=split, candidate=record.label,
                where=f"§13.11:{record.label}")
        elif record.kappa_under_b_source is not None:
            raise ProtocolError(
                f"{record.label}: a kappa(R|B) source with no value")
        out.append(record)
    return out
