"""§6.2's bank as a loadable, hashable, splittable object --- and the half of
it that does not exist.

v5's bank is v4's 528 released questions plus **96 newly authored ones**, eight
per subject area, which are Calibration-B. §13.7 --- v5's whole answer to the
winner's curse §12.2 measures --- estimates every selection quantity twice on
two disjoint 96-topic sets and admits a candidate only when the two agree
inside an equivalence bound. Both sets now exist: §34 D3 was taken on
2026-08-22 and ``topics/calibration_b.py`` carries the content and its
provenance.

**This module is still the infrastructure and not the content**, and it refuses
a bank that does not satisfy §6.2 however the decision closed. It can load a
bank,
validate its schema, hash it, cut it into the six registered sets, allocate
draws, bind a split identity into a calibration record and refuse every way
the two calibration sets could be confused with one another. It authors
nothing: ``calibration_b_questions`` raises while D3 is open, and raises again
if the bank it is handed is not 96 questions that each carry §6.2's four
authoring verifications.

**The confusion this module exists to make impossible.** §13.7's two
estimates are only independent if the two topic sets are disjoint, and every
quantity it compares is computed by the same functions on rows that differ
only in which topics produced them. A row that carried the wrong split label,
a pooled table that looked like a split table, or a Calibration-B question
that had also been used in Calibration-A would each turn the stability rule
into a self-comparison that always passes. So ``split_of_topic`` is derived
from the bank rather than from a row's own claim about itself,
``assert_rows_single_split`` refuses a mixed row set where it is read, and
``assert_calibration_sets_disjoint`` is checked at load, at split, and again
when a calibration record is bound.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_obj
from dci1v4.topics.split import split_topics as _v4_split

from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions

__all__ = ["TOPIC_FIELDS", "CALIBRATION_B_STATUS", "calibration_b_status",
           "CALIBRATION_SETS",
           "V4_SET_NAMES", "TopicBank", "assert_topic_schema",
           "topic_hash", "set_hash", "split_hash", "bank_hash",
           "load_bank", "calibration_b_questions", "assert_per_area",
           "assert_sets_disjoint", "assert_calibration_sets_disjoint",
           "assert_no_reserved_topic_spent", "split_of_topic",
           "assert_rows_single_split", "assert_not_pooled_as_split",
           "draw_allocation", "calibration_binding", "provenance"]

#: The schema every question in the bank satisfies. ``set`` is the registered
#: v5 set name, which is **not** always the v4 one: v4's ``solo`` split is
#: v5's Calibration-A, renamed because v5 has two calibration sets and
#: "solo" now names a *cell*, not a topic set.
TOPIC_FIELDS = ("topic_id", "area", "question", "set")

def calibration_b_status() -> str:
    """What can honestly be said about Calibration-B right now.

    Three states, not two, because "the questions do not exist" and "the
    questions exist and the decision to use them has not been taken" are
    different facts and only the first is work nobody has done:

    * ``NOT_AUTHORED`` --- the bank file is absent.
    * ``AUTHORED_PENDING_D3`` --- the file is there and §34 D3 is open.
    * ``AUTHORED`` --- the file is there and D3 is closed at
      ``author_before_adoption``, so the questions may enter a study bank.
    """
    from dci1v6.topics.calibration_b import DATA_PATH

    if not DATA_PATH.exists():
        return "NOT_AUTHORED"
    if decisions.value_of("D3") == "author_before_adoption":
        return "AUTHORED"
    return "AUTHORED_PENDING_D3"


#: The value at import. ``calibration_b_status()`` is the live one --- the
#: constant cannot see a decision closed later in the same process.
CALIBRATION_B_STATUS = "AUTHORED"

CALIBRATION_SETS = (C.CALIBRATION_A, C.CALIBRATION_B)

#: v4 set name -> v5 set name. The rename is recorded rather than applied
#: silently, because a carried row's ``set`` field says ``solo``.
V4_SET_NAMES = {"prescreen": "prescreen", "solo": C.CALIBRATION_A,
                "composed": "composed", "confirmatory": "confirmatory",
                "sequestered": "sequestered"}


# ------------------------------------------------------------------ schema

def assert_topic_schema(topic: Mapping[str, Any], *, where: str) -> None:
    """Every registered field present, non-empty, and of the right kind."""
    missing = [f for f in TOPIC_FIELDS if f not in topic]
    if missing:
        raise ProtocolError(f"{where}: topic is missing {missing}; §6.2's "
                            f"schema is {TOPIC_FIELDS}")
    for field in TOPIC_FIELDS:
        value = topic[field]
        if not isinstance(value, str) or not value.strip():
            raise ProtocolError(
                f"{where}: topic field {field!r} is {value!r}; every field is "
                "a non-empty string")
    if topic["area"] not in C.SUBJECT_AREAS:
        raise ProtocolError(
            f"{where}: {topic['area']!r} is not one of §6.2's twelve subject "
            f"areas")
    if topic["set"] not in C.TOPIC_SETS:
        raise ProtocolError(
            f"{where}: {topic['set']!r} is not a registered v5 topic set; "
            f"registered: {C.TOPIC_SETS}")


# ------------------------------------------------------------------ hashing

def topic_hash(topic: Mapping[str, Any]) -> str:
    """A question's content identity.

    Over the *text* as well as the identifier, so that a bank whose ids match
    and whose questions do not is a different bank. §6.2's sequestered eighth
    exists to this repository only as opaque identities, so a hash over ids
    alone would call two different banks the same.
    """
    return sha_obj({"topic_id": topic["topic_id"], "area": topic["area"],
                    "question": topic["question"]})


def set_hash(topics: Sequence[Mapping[str, Any]]) -> str:
    """One set's identity: its questions, in topic-id order."""
    return sha_obj([topic_hash(t) for t in
                    sorted(topics, key=lambda t: t["topic_id"])])


def split_hash(split: Mapping[str, Sequence[Mapping[str, Any]]]) -> str:
    """The whole cut's identity, per set."""
    return sha_obj({name: set_hash(members)
                    for name, members in sorted(split.items())})


def bank_hash(bank: Sequence[Mapping[str, Any]]) -> str:
    return sha_obj([topic_hash(t) for t in
                    sorted(bank, key=lambda t: t["topic_id"])])


# ---------------------------------------------------------------- structure

def assert_per_area(topics: Sequence[Mapping[str, Any]], *, expected: int,
                    where: str) -> dict[str, int]:
    """§6.2's stratification: the same count in every one of twelve areas."""
    counts = {area: 0 for area in C.SUBJECT_AREAS}
    for topic in topics:
        area = topic["area"]
        if area not in counts:
            raise ProtocolError(f"{where}: unknown subject area {area!r}")
        counts[area] += 1
    wrong = {a: n for a, n in counts.items() if n != expected}
    if wrong:
        raise ProtocolError(
            f"{where}: §6.2 allocates {expected} topics per area and this set "
            f"carries {wrong}. A set that is not stratified makes every "
            "per-area mean a different weighted average")
    return counts


def assert_sets_disjoint(split: Mapping[str, Sequence[Mapping[str, Any]]]
                         ) -> None:
    """No topic id and no question text appears in two sets.

    Both, because the two failures look different on disk and mean the same
    thing: an id collision is a mis-cut and a text collision is a duplicated
    question authored twice.
    """
    by_id: dict[str, str] = {}
    by_text: dict[str, tuple[str, str]] = {}
    for name in sorted(split):
        for topic in split[name]:
            tid = topic["topic_id"]
            if tid in by_id:
                raise ProtocolError(
                    f"topic {tid!r} appears in both {by_id[tid]} and {name}; "
                    "§6.2's splits are disjoint and a topic a set spends is "
                    "spent")
            by_id[tid] = name
            text = " ".join(str(topic["question"]).lower().split())
            if text in by_text:
                other, other_set = by_text[text]
                raise ProtocolError(
                    f"topic {tid!r} in {name} repeats the question text of "
                    f"{other!r} in {other_set}; two topics with one question "
                    "are one topic counted twice, and §13.7's two splits stop "
                    "being independent")
            by_text[text] = (tid, name)


def assert_calibration_sets_disjoint(
        split: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    """§13.7's precondition, checked on its own rather than inside the rest.

    §13.7 estimates every selection quantity twice and admits a candidate
    only when the two agree. If a question reached both sets the two
    estimates share data and the rule degenerates to comparing a set with
    itself, which always agrees. That failure is silent everywhere else, so
    it gets its own named check and its own call sites.
    """
    a = list(split.get(C.CALIBRATION_A, ()))
    b = list(split.get(C.CALIBRATION_B, ()))
    ids_a, ids_b = {t["topic_id"] for t in a}, {t["topic_id"] for t in b}
    shared = sorted(ids_a & ids_b)
    if shared:
        raise ProtocolError(
            f"§13.7: {len(shared)} topic(s) are in Calibration-A and "
            f"Calibration-B, first {shared[:3]}. The two splits must be "
            "disjoint or the stability rule compares a set with itself")
    texts_a = {" ".join(str(t["question"]).lower().split()) for t in a}
    leaked = sorted(t["topic_id"] for t in b
                    if " ".join(str(t["question"]).lower().split()) in texts_a)
    if leaked:
        raise ProtocolError(
            f"§13.7: Calibration-B question(s) {leaked[:3]} repeat "
            "Calibration-A question text under a different id. A re-authored "
            "duplicate is a leak, not a new topic")
    return {"n_a": len(a), "n_b": len(b), "disjoint": True,
            "calibration_a_hash": set_hash(a) if a else None,
            "calibration_b_hash": set_hash(b) if b else None}


def assert_no_reserved_topic_spent(
        used_topic_ids: Iterable[str],
        split: Mapping[str, Sequence[Mapping[str, Any]]], *,
        stage: str) -> None:
    """§12.5: only development sets may be inspected before the freeze."""
    permitted: set[str] = set()
    for name in C.DEVELOPMENT_TOPIC_SETS:
        permitted |= {t["topic_id"] for t in split.get(name, ())}
    reserved = {t["topic_id"]: name for name in C.RESERVED_TOPIC_SETS
                for t in split.get(name, ())}
    spent = sorted({t for t in used_topic_ids if t in reserved})
    if spent:
        raise ProtocolError(
            f"{stage}: {len(spent)} reserved topic(s) would be spent, first "
            f"{[(t, reserved[t]) for t in spent[:3]]}. §12.5 permits "
            f"{C.DEVELOPMENT_TOPIC_SETS} before the freeze and nothing else")
    unknown = sorted({t for t in used_topic_ids
                      if t not in permitted and t not in reserved})
    if unknown:
        raise ProtocolError(
            f"{stage}: topic(s) {unknown[:3]} are in no registered set")


# ------------------------------------------------------------------- bank

@dataclass(frozen=True)
class TopicBank:
    """One loaded bank, cut into §6.2's six sets and hashed."""

    sets: dict[str, tuple[dict[str, Any], ...]]
    calibration_b_status: str

    @property
    def complete(self) -> bool:
        return self.calibration_b_status == "AUTHORED"

    def topics(self, set_name: str) -> tuple[dict[str, Any], ...]:
        if set_name not in C.TOPIC_SETS:
            raise ProtocolError(f"{set_name!r} is not a registered set")
        return self.sets[set_name]

    def all_topics(self) -> tuple[dict[str, Any], ...]:
        return tuple(t for name in C.TOPIC_SETS for t in self.sets[name])

    @property
    def hashes(self) -> dict[str, str | None]:
        return {name: (set_hash(self.sets[name]) if self.sets[name] else None)
                for name in C.TOPIC_SETS}

    @property
    def split_identity(self) -> dict[str, Any]:
        """What a stage record binds so a later reader can prove which
        questions produced a number."""
        return {
            "split_hash": split_hash({k: v for k, v in self.sets.items()
                                      if v}),
            "set_hashes": self.hashes,
            "set_counts": {k: len(v) for k, v in self.sets.items()},
            "calibration_b_status": self.calibration_b_status,
            "complete": self.complete,
            "split_seed": "v4r2's, carried unchanged (§6.2)",
        }


def calibration_b_questions(
        questions: Sequence[Mapping[str, Any]] | None = None
) -> tuple[dict[str, Any], ...]:
    """§6.2's 96 newly authored questions, checked rather than trusted.

    §34 D3 gates adoption on them and this refuses while D3 is open. Now that
    it is closed the bank must **still** be 96 questions, eight per area, each
    carrying §6.2's four authoring verifications and passing the one rule that
    is mechanically checkable --- because closing a decision is not the same
    as doing the work it names, and this is the function that knows the
    difference.
    """
    from dci1v6.topics import assert_authoring_rules

    def _author_before() -> tuple[dict[str, Any], ...]:
        if questions is None:
            raise ProtocolError(
                "§34 D3 was closed at 'author before adoption' and no bank "
                f"was supplied. §6.2 needs {C.N_CALIBRATION_B} newly authored "
                "questions, eight per subject area, each verified "
                "individually against the four authoring rules")
        rows = [dict(q) for q in questions]
        for row in rows:
            row.setdefault("set", C.CALIBRATION_B)
            assert_topic_schema(row, where="calibration_b")
            if row["set"] != C.CALIBRATION_B:
                raise ProtocolError(
                    f"{row['topic_id']!r} declares set {row['set']!r}; a "
                    "Calibration-B question belongs to Calibration-B and to "
                    "no other set")
        if len(rows) != C.N_CALIBRATION_B:
            raise ProtocolError(
                f"§6.2: Calibration-B is {C.N_CALIBRATION_B} questions and "
                f"this bank is {len(rows)}")
        assert_per_area(rows, expected=C.CALIBRATION_B_PER_AREA,
                        where="calibration_b")
        assert_authoring_rules(questions)
        return tuple(rows)

    def _author_after() -> tuple[dict[str, Any], ...]:
        raise ProtocolError(
            "§34 D3 was closed at 'author after adoption'. Nothing "
            "downstream of Gate 3A can run until the bank exists, and this "
            "returns no questions rather than an empty split that would look "
            "like one")

    return decisions.choice("D3", {"author_before_adoption": _author_before,
                                   "author_after_adoption": _author_after},
                            where="topics.bank.calibration_b_questions")()


def load_bank(calibration_b: Sequence[Mapping[str, Any]] | None = None,
              *, v4_bank: Sequence[Mapping[str, Any]] | None = None
              ) -> TopicBank:
    """v4's released split under v5's set names, plus Calibration-B.

    ``calibration_b`` is passed through ``calibration_b_questions``, so a
    caller cannot get a complete bank while §34 D3 is open however good its
    questions are. With none supplied the authored bank is loaded from disk
    **when D3 permits it**, and otherwise the bank loads with an empty
    Calibration-B and says so in ``calibration_b_status`` --- which is the
    honest state whenever the questions do not exist or the decision to use
    them has not been taken, and is what every stage before Gate 3A can
    legitimately run on.
    """
    if v4_bank is not None:
        carried = _cut_supplied(v4_bank)
    else:
        carried = {V4_SET_NAMES[k]: [dict(t) for t in v]
                   for k, v in _v4_split().items() if k in V4_SET_NAMES}
        # §6.2's sequestered eighth is not in the released bank; it exists as
        # opaque identities and is never materialised here.
        carried.setdefault("sequestered", [])
    for name, members in carried.items():
        for topic in members:
            topic["set"] = name
            assert_topic_schema(topic, where=f"bank:{name}")
    sets: dict[str, tuple[dict[str, Any], ...]] = {
        name: tuple(sorted(carried.get(name, ()),
                           key=lambda t: t["topic_id"]))
        for name in C.TOPIC_SETS}
    status = calibration_b_status()
    if calibration_b is None and status == "AUTHORED":
        from dci1v6.topics.calibration_b import load_calibration_b

        calibration_b = load_calibration_b()
    if calibration_b is not None:
        sets[C.CALIBRATION_B] = tuple(
            sorted(calibration_b_questions(calibration_b),
                   key=lambda t: t["topic_id"]))
        status = "AUTHORED"
    for name in C.TOPIC_SETS:
        if name == C.CALIBRATION_B and status != "AUTHORED":
            continue
        if name == "sequestered" and not sets[name]:
            continue                       # opaque, never materialised
        if len(sets[name]) != C.SET_SIZES[name]:
            raise ProtocolError(
                f"§6.2 registers {C.SET_SIZES[name]} {name} topics; this bank "
                f"carries {len(sets[name])}")
        assert_per_area(sets[name],
                        expected=C.SET_SIZES[name] // C.N_AREAS,
                        where=f"bank:{name}")
    populated = {k: v for k, v in sets.items() if v}
    assert_sets_disjoint(populated)
    assert_calibration_sets_disjoint(populated)
    return TopicBank(sets=sets, calibration_b_status=status)


def _cut_supplied(bank: Sequence[Mapping[str, Any]]
                  ) -> dict[str, list[dict[str, Any]]]:
    """Cut a supplied bank by its own declared set labels, v4 names mapped."""
    out: dict[str, list[dict[str, Any]]] = {}
    for topic in bank:
        row = dict(topic)
        name = V4_SET_NAMES.get(row.get("set", ""), row.get("set", ""))
        if name not in C.TOPIC_SETS:
            raise ProtocolError(
                f"{row.get('topic_id')!r} declares set {row.get('set')!r}, "
                f"which is not a registered v5 set")
        out.setdefault(name, []).append(row)
    return out


# ------------------------------------------------- split identity on rows

def split_of_topic(bank: TopicBank) -> dict[str, str]:
    """topic id -> registered set, derived from the bank.

    Derived, never read off a row. A row's own ``split`` field is what the
    producer believed; this is what the bank says, and §13.7 needs the second.
    """
    return {t["topic_id"]: name
            for name in C.TOPIC_SETS for t in bank.sets[name]}


def assert_rows_single_split(rows: Iterable[Mapping[str, Any]],
                             bank: TopicBank, *, split: str,
                             where: str) -> dict[str, Any]:
    """Every row in this table came from the split it claims to be.

    The check that stops §13.7's two estimates from sharing rows. It reads
    the bank rather than the row's label, so a mislabelled row is caught by
    the thing that decides the truth rather than by the thing that repeated
    the claim.
    """
    if split not in CALIBRATION_SETS:
        raise ProtocolError(
            f"{where}: {split!r} is not a calibration split; §13.7's two "
            f"splits are {CALIBRATION_SETS}")
    lookup = split_of_topic(bank)
    rows = list(rows)
    foreign: list[tuple[str, str]] = []
    unknown: list[str] = []
    for row in rows:
        tid = row.get("topic_id")
        actual = lookup.get(tid)
        if actual is None:
            unknown.append(str(tid))
        elif actual != split:
            foreign.append((str(tid), actual))
    if unknown:
        raise ProtocolError(
            f"{where}: {len(unknown)} row(s) name topics that are in no "
            f"registered set, first {unknown[:3]}")
    if foreign:
        raise ProtocolError(
            f"{where}: {len(foreign)} row(s) claim split {split!r} and their "
            f"topics belong to another set, first {foreign[:3]}. §13.7's two "
            "estimates are independent only if their rows are")
    return {"split": split, "n_rows": len(rows),
            "n_topics": len({r.get("topic_id") for r in rows})}


def assert_not_pooled_as_split(rows: Iterable[Mapping[str, Any]],
                               bank: TopicBank, *, where: str) -> None:
    """A pooled table may never be presented as one split's table.

    §13.7 compares two split estimates and §13.8 selects on the pooled one.
    Handing the pooled rows to the split comparison would make both sides
    identical, which is the one way the stability rule can pass without
    having been tested.
    """
    lookup = split_of_topic(bank)
    seen = {lookup.get(r.get("topic_id")) for r in rows}
    seen.discard(None)
    present = sorted(s for s in seen if s in CALIBRATION_SETS)
    if len(present) > 1:
        raise ProtocolError(
            f"{where}: these rows span {present}; a pooled calibration table "
            "is not a split table and §13.7's comparison would compare a set "
            "with itself")


# -------------------------------------------------------- draw allocation

def draw_allocation(topics: Sequence[Mapping[str, Any]], *, draws: int,
                    stage: str) -> dict[str, Any]:
    """§12.3/§13.7's per-topic draw plan, as an auditable object.

    Every topic gets the same number of draws and every draw is kept: the
    topic is the unit of §11.1's averaging, so an unequal allocation makes
    the topic mean a weighted average nobody registered.
    """
    if draws < 1:
        raise ProtocolError(f"{stage}: draws must be positive, got {draws}")
    ids = [t["topic_id"] for t in topics]
    if len(set(ids)) != len(ids):
        raise ProtocolError(f"{stage}: the topic list repeats an id")
    return {"stage": stage, "n_topics": len(ids), "draws_per_topic": draws,
            "n_rows_per_cell": len(ids) * draws,
            "allocation": "equal; every draw kept, none selected",
            "topic_ids": sorted(ids)}


# --------------------------------------------------- record binding

def calibration_binding(bank: TopicBank, *, split: str,
                        rows: Sequence[Mapping[str, Any]] | None = None,
                        draws: int | None = None) -> dict[str, Any]:
    """What a calibration record binds about the topics that produced it.

    A calibration number with no topic identity cannot be reproduced and
    cannot be shown to be independent of the other split's. This is the field
    that makes both checkable later, from the record alone.
    """
    if split not in CALIBRATION_SETS and split != "pooled":
        raise ProtocolError(
            f"{split!r} is not a calibration split; §13.7's two splits are "
            f"{CALIBRATION_SETS} and their union is 'pooled'")
    if split == "pooled":
        members = tuple(bank.sets[C.CALIBRATION_A]) + \
            tuple(bank.sets[C.CALIBRATION_B])
    else:
        members = bank.sets[split]
    if not members:
        raise ProtocolError(
            f"the {split!r} split is empty. Calibration-B is "
            f"{bank.calibration_b_status}: §34 D3 is the decision and §13.7 "
            "does not work without it")
    binding: dict[str, Any] = {
        "split": split, "n_topics": len(members),
        "topic_set_hash": set_hash(members),
        "topic_ids": sorted(t["topic_id"] for t in members),
        "calibration_b_status": bank.calibration_b_status,
        "disjointness": assert_calibration_sets_disjoint(
            {k: v for k, v in bank.sets.items() if v}),
    }
    if rows is not None and split in CALIBRATION_SETS:
        binding["rows"] = assert_rows_single_split(
            rows, bank, split=split, where=f"calibration_binding:{split}")
    elif rows is not None:
        assert_no_reserved_topic_spent(
            (r.get("topic_id") for r in rows), bank.sets, stage="calibration")
    if draws is not None:
        binding["draws"] = draw_allocation(members, draws=draws,
                                           stage=f"calibration:{split}")
    return binding


def provenance(bank: TopicBank) -> dict[str, Any]:
    """§6.2's declaration: where each set came from and what it may be used
    for, including the fact that Calibration-A is not naive."""
    return {
        "prescreen": {"source": "v4 split, unchanged",
                      "use": "cap selection, the high-recall screen, Gate-1 "
                             "material"},
        C.CALIBRATION_A: {
            "source": "v4's solo-calibration split, unchanged, renamed",
            "use": "solo, chance and counterfactual-chance quantities; one "
                   "half of §13.7",
            "naive": False,
            "declaration":
                "twenty-nine rungs per model of v4r4's library were measured "
                "on these topics and the researcher has seen the "
                "measurements; they are development data under §12.5 and §30's "
                "ledger records per family whether a prior measurement exists"},
        C.CALIBRATION_B: {
            "source": "newly authored for v5",
            "use": "the same quantities on disjoint topics; the other half of "
                   "§13.7",
            "naive": True, "status": bank.calibration_b_status,
            "decision": "§34 D3"},
        "composed": {"source": "v4 split, unchanged",
                     "use": "composed-headroom viability only"},
        "confirmatory": {"source": "v4 split, unchanged",
                         "use": "the frozen confirmatory experiment"},
        "sequestered": {"source": "v4 split, never materialised here",
                        "use": "a future uncontaminated rerun only"},
        "split_identity": bank.split_identity,
    }
