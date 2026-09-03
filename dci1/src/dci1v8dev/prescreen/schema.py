"""The pre-screen input: a closed schema with no field a composed outcome fits.

§13.11 makes the *calibration* table's schema closed so that no composed
quantity can reach a selection rule. The screen redesigned here reads an even
smaller table --- **counts** of solo compliance, unconstrained-chance compliance
and vacuity on the pre-screen topics, plus structure --- and the same three
refusals apply, before any value is read:

1. a field whose name matches a composed quantity is refused, generously;
2. an unknown field is refused, so a composed quantity cannot enter under an
   unlisted name;
3. counts must be integers inside their sample sizes, so a *rate* copied from
   somewhere else cannot masquerade as a measurement.

The unit of every count is a **draw**, and the table records how many topics
and how many draws per topic produced it, because §12.2's screen is one draw
per topic and a re-screen batch may add draws or topics: the effective sample
size (``statistics.effective_n``) depends on which.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v7.stages.calibration_table import FORBIDDEN_CALIBRATION_FIELDS
from dci1v7.verifiers.constraints import (
    FAMILIES,
    LADDERS,
    RESERVES,
    family_class,
    family_tier,
    feature_group,
    is_probe_only,
)

__all__ = [
    "FORBIDDEN_PRESCREEN_FIELDS",
    "ARung",
    "PrescreenRung",
    "a_rung_from_rates",
    "load_prescreen_table",
    "rung_from_rates",
]

#: §13.11's list, plus the names a *pre-screen* table could plausibly be
#: handed by mistake: anything from a composed cell, an estimate of an
#: estimand, or a later-stage verdict.
FORBIDDEN_PRESCREEN_FIELDS = tuple(sorted(set(FORBIDDEN_CALIBRATION_FIELDS) | {
    "b_plus", "plus_b", "r_plus_b", "b_plus_r", "d_b", "d_a",
    "delta_diff", "delta_difficulty", "beta_hat", "slope_hat",
    "calibration_", "calibrated", "gate2", "gate_2", "gate3",
    "gate_3", "survived", "survival", "c4_at_calibration",
    "stability", "v_stab", "v_diff", "admitted", "selected",
}))


@dataclass(frozen=True)
class PrescreenRung:
    """One candidate rung's pre-screen counts. Draws are the unit.

    ``solo_k`` of ``solo_n`` draws satisfied the constraint with it stated;
    ``chance_k`` of ``chance_n`` unconstrained draws satisfied it absent;
    ``vacuous_k`` of ``solo_n`` solo draws passed vacuously. ``n_topics`` and
    ``draws_per_topic`` say how the solo draws were laid out.
    """

    kind: str
    severity: int
    solo_k: int
    solo_n: int
    #: The chance count may be a real-valued *effective* count: §12.2's
    #: recorded chance rate is a topic-mean over every row in which the
    #: instance was absent (``run/execute.instance_rates``), so it is not a
    #: k-of-n draw count; it is carried as ``rate x chance_n`` on the stated
    #: basis (``chance_n`` topics by default, the conservative unit).
    chance_k: float
    chance_n: float
    vacuous_k: int = 0
    n_topics: int = 24
    draws_per_topic: int = 1
    #: True when the rung is a §7.10 reserve severity admitted by a re-screen
    #: rather than a round-0 ladder rung.
    reserve: bool = False

    def __post_init__(self):
        if self.kind not in FAMILIES:
            raise ProtocolError(
                f"{self.kind!r} is not a registered candidate family")
        if is_probe_only(self.kind):
            raise ProtocolError(
                f"{self.kind!r} is a §34 D24 probe-only stand-in; the screen "
                "may not see it (it enters no coverage count)")
        if self.severity not in RESERVES[self.kind] and \
                self.severity not in LADDERS[self.kind]:
            raise ProtocolError(
                f"{self.label}: severity outside the family's declared range "
                f"(ladder {list(LADDERS[self.kind])}, reserve "
                f"{list(RESERVES[self.kind])}); the screen can only pick, "
                "never author")
        for name in ("solo_k", "solo_n", "vacuous_k", "n_topics",
                     "draws_per_topic"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise ProtocolError(f"{self.label}: {name} must be an integer "
                                    f"count, got {value!r}")
        for name in ("chance_k", "chance_n"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ProtocolError(f"{self.label}: {name} must be a number, "
                                    f"got {value!r}")
        if self.solo_n <= 0 or self.chance_n <= 0:
            raise ProtocolError(f"{self.label}: sample sizes must be positive")
        if not 0 <= self.solo_k <= self.solo_n:
            raise ProtocolError(f"{self.label}: solo_k outside [0, solo_n]")
        if not 0 <= self.chance_k <= self.chance_n:
            raise ProtocolError(f"{self.label}: chance_k outside "
                                "[0, chance_n]")
        if not 0 <= self.vacuous_k <= self.solo_n:
            raise ProtocolError(f"{self.label}: vacuous_k outside "
                                "[0, solo_n]")
        if self.n_topics * self.draws_per_topic != self.solo_n:
            raise ProtocolError(
                f"{self.label}: n_topics x draws_per_topic = "
                f"{self.n_topics * self.draws_per_topic} but solo_n = "
                f"{self.solo_n}; the layout has to account for every draw")

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.severity}"

    @property
    def structural_tier(self) -> int:
        return family_tier(self.kind)

    @property
    def feature_group(self) -> str:
        return feature_group(self.kind)

    @property
    def constraint_class(self) -> str:
        return family_class(self.kind)

    @property
    def solo_rate(self) -> float:
        return self.solo_k / self.solo_n

    @property
    def chance_rate(self) -> float:
        return self.chance_k / self.chance_n

    @property
    def vacuity_rate(self) -> float:
        return self.vacuous_k / self.solo_n

    def merged(self, other: PrescreenRung, *,
               layout: str | None = None) -> PrescreenRung:
        """Pool a re-screen batch into this rung's counts.

        Topic layout: when the batch adds *draws* on the same topics the
        topic count stays and the draws-per-topic grows; when it adds
        *topics* the topic count grows. Mixed layouts are refused --- the
        effective sample size would not be computable.

        ``layout`` (``"topics"`` / ``"draws"``) states which the batch is.
        Without it the layout is *inferred* from the counts: a batch whose
        topic count equals the table's is taken for repeated draws. That
        inference is the legacy behaviour and is kept as it was; note that
        the legacy second pass measures 24 fresh Calibration-A topics into
        a 24-topic table and is therefore read as a second *draw* on the
        pre-screen topics (``draws_per_topic`` grows, ``n_topics`` stays;
        the ICC design effect then discounts the fresh topics ---
        ``reports/dci1v8dev/frame_aware_prescreen/legacy_prescreen_characterization.md``).
        The frame-aware loop passes the batch's declared layout.
        """
        if (other.kind, other.severity) != (self.kind, self.severity):
            raise ProtocolError("cannot merge counts of different rungs")
        if layout not in (None, "topics", "draws"):
            raise ProtocolError(f"unknown batch layout {layout!r}")
        if layout == "topics" or (layout is None
                                  and other.n_topics != self.n_topics):
            if other.draws_per_topic != self.draws_per_topic:
                raise ProtocolError(
                    f"{self.label}: a batch must add draws on the same topics "
                    "or topics at the same draw count, not both")
            n_topics, dpt = self.n_topics + other.n_topics, \
                self.draws_per_topic
        elif layout == "draws" or other.n_topics == self.n_topics:
            if other.n_topics != self.n_topics:
                raise ProtocolError(
                    f"{self.label}: a draws batch must cover the table's "
                    "topics")
            n_topics, dpt = self.n_topics, self.draws_per_topic + \
                other.draws_per_topic
        else:                                               # pragma: no cover
            raise ProtocolError(
                f"{self.label}: a batch must add draws on the same topics "
                "or topics at the same draw count, not both")
        return PrescreenRung(
            kind=self.kind, severity=self.severity,
            solo_k=self.solo_k + other.solo_k,
            solo_n=self.solo_n + other.solo_n,
            chance_k=self.chance_k + other.chance_k,
            chance_n=self.chance_n + other.chance_n,
            vacuous_k=self.vacuous_k + other.vacuous_k,
            n_topics=n_topics, draws_per_topic=dpt,
            reserve=self.reserve or other.reserve)


@dataclass(frozen=True)
class ARung:
    """A's grid at one severity on the pre-screen: solo and chance counts."""

    severity: int
    solo_k: int
    solo_n: int
    chance_k: float
    chance_n: float
    n_topics: int = 24
    draws_per_topic: int = 1

    def __post_init__(self):
        if self.solo_n <= 0 or self.chance_n <= 0:
            raise ProtocolError(f"A:{self.severity}: sample sizes must be "
                                "positive")
        if not 0 <= self.solo_k <= self.solo_n or \
                not 0 <= self.chance_k <= self.chance_n:
            raise ProtocolError(f"A:{self.severity}: counts outside range")

    @property
    def solo_rate(self) -> float:
        return self.solo_k / self.solo_n

    @property
    def chance_rate(self) -> float:
        return self.chance_k / self.chance_n


_KNOWN_FIELDS = {f.name for f in dataclass_fields(PrescreenRung)}


def load_prescreen_table(rows: Iterable[Mapping[str, Any]]
                         ) -> list[PrescreenRung]:
    """Build the screen's input, refusing a composed field before any value."""
    out: list[PrescreenRung] = []
    for row in rows:
        offending = sorted(
            k for k in row
            if any(bad in k.lower() for bad in FORBIDDEN_PRESCREEN_FIELDS))
        if offending:
            raise ProtocolError(
                "a pre-screen rule may read only solo, unconstrained-chance "
                "and vacuity counts on the pre-screen topics, family "
                f"structure and severity; this table carries {offending}")
        unknown = sorted(set(row) - _KNOWN_FIELDS)
        if unknown:
            raise ProtocolError(
                f"unknown pre-screen fields {unknown}; the schema is closed "
                "so that a composed quantity cannot enter under an unlisted "
                "name")
        out.append(PrescreenRung(**row))
    return out


def rung_from_rates(kind: str, severity: int, *, solo: float, chance: float,
                    vacuity: float = 0.0, n_topics: int = 24,
                    draws_per_topic: int = 1, chance_n: int | None = None,
                    reserve: bool = False) -> PrescreenRung:
    """Recover counts from the rates a §12.2 ``difficulty_table`` records.

    The registered table stores rates over ``n_topics`` at one draw, so the
    count is exact after rounding to the nearest draw; a rate that is not a
    multiple of 1/n is refused rather than silently rounded across a draw.
    """
    n = n_topics * draws_per_topic
    cn = chance_n if chance_n is not None else n

    def _count(rate: float, size: int, what: str) -> int:
        k = round(rate * size)
        if abs(k - rate * size) > 1e-6:
            raise ProtocolError(f"{kind}:{severity}: {what} rate {rate} is "
                                f"not a multiple of 1/{size}")
        return int(k)

    if not 0.0 <= chance <= 1.0:
        raise ProtocolError(f"{kind}:{severity}: chance rate {chance} outside "
                            "[0, 1]")
    return PrescreenRung(kind=kind, severity=severity,
                         solo_k=_count(solo, n, "solo"), solo_n=n,
                         chance_k=float(chance) * float(cn),
                         chance_n=float(cn),
                         vacuous_k=_count(vacuity, n, "vacuity"),
                         n_topics=n_topics, draws_per_topic=draws_per_topic,
                         reserve=reserve)


def a_rung_from_rates(severity: int, *, solo: float, chance: float,
                      n_topics: int = 24, draws_per_topic: int = 1,
                      chance_n: int | None = None) -> ARung:
    n = n_topics * draws_per_topic
    cn = chance_n if chance_n is not None else n
    k = round(solo * n)
    if abs(k - solo * n) > 1e-6:
        raise ProtocolError(f"A:{severity}: solo rate {solo} is not a "
                            f"multiple of 1/{n}")
    if not 0.0 <= chance <= 1.0:
        raise ProtocolError(f"A:{severity}: chance rate outside [0, 1]")
    return ARung(severity=severity, solo_k=int(k), solo_n=n,
                 chance_k=float(chance) * float(cn), chance_n=float(cn),
                 n_topics=n_topics, draws_per_topic=draws_per_topic)
