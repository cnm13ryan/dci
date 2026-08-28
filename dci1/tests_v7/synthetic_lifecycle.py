"""An end-to-end walk of the v5 lifecycle with no model and no science.

**This is an engineering harness. Nothing it produces is evidence.** It runs
in the ``synthetic`` namespace --- study id ``dci1v7-synthetic``, its own
signing key, its own evidence root under a temporary directory --- and
``engine/context.StudyContext`` refuses a synthetic root that overlaps the
registered one or any historical study's. Every row it generates carries
``synthetic: true`` and a study id that no v5 estimator, gate or manifest
will accept.

It exists to find the defects that only appear when a path executes:

* a consumer field with no producer;
* a malformed or drifted record schema;
* a freeze field nobody fills;
* a stage transition that is legal in prose and illegal in code;
* a namespace leak;
* a design/cell mismatch between what a gate admitted and what a runner built.

**The decisions are closed here and only here.** ``resolved_manifest`` closes
all nineteen §34 decisions and resolves the blocking specification question
with ``decided_by="synthetic lifecycle harness"``, and the fixture restores
every one afterwards. That is what makes the lifecycle executable without
making any of it adopted: a closure lives durably only in a *signed
registration manifest*, which this harness writes into a temporary directory
that is deleted with the test.

**The Calibration-B questions here are placeholders, not content.** §34 D3
asks the researcher to author 96 research questions; these are 96 strings
that say in their own text that they are fixtures. They exercise the loader,
the hashing, the split identity and the disjointness rules, and they are
unusable as research questions by construction.
"""
from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v7 import PREREGISTRATION, REFERENCE_DESIGN_SPEC
from dci1v7.protocol.reuse_ledger import ARTIFACT_TEXT_GLOBS
from dci1v7.engine.context import REPO_ROOT as _REAL_REPO_ROOT
from dci1v7.engine.context import synthetic_context
from dci1v7.engine.paths import model_tree
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions, open_items
from dci1v7.run import (analysis_run, confirmatory_run, freeze_run, gates_run,
                        prefreeze_run, qualification_run, regime_run)
from dci1v7.run.execute import fake_backend
from dci1v7.topics.bank import load_bank
from dci1v7.verifiers.constraints import (FAMILIES, Constraint,
                                          FORM_RATE_LOWER_BOUND,
                                          LOWER_BOUND_FORMS,
                                          RATE_FORMS)
from dci1v7.verifiers.realistic_witness import pad_to_band

MODEL_KEY = "gemma-3n-e2b-it"

#: The two documents §18 stage 1 binds by content hash. Always seeded as
#: labelled placeholders, never copied: see `synthetic_repo`.
GOVERNED_DOCUMENTS: tuple[str, ...] = (PREREGISTRATION,
                                       REFERENCE_DESIGN_SPEC)

#: The files a production reader opens **relative to the repository root**:
#: the two documents §18 stage 1 binds by hash, and the §30 ledger's
#: non-glob sources. ``synthetic_repo`` copies exactly these, plus the v5
#: source tree, into an isolated repository and commits them, so that
#: ``clean_worktree``, ``commit_hashable``, ``tracked_implementation``,
#: ``producing_commit_clean`` and ``protocol_hashes_agree`` run **unweakened**
#: against a genuinely clean tree at a genuinely resolvable commit.
REPO_FILES: tuple[str, ...] = (
    PREREGISTRATION,
    REFERENCE_DESIGN_SPEC,
    # §30's non-glob sources that exist on disk: v6's closure record and the
    # carried v4r4 segmenter. `dci1/src/dci1v6` is a tree and is recorded
    # `missing` in the synthetic repository, as v5's was under v6.
    "dci1/reports/dci1v6/closure.json",
    "dci1/src/dci1v4r4/verifiers/statistics.py",
    "dci1/src/dci1v4r4/verifiers/words.py",
    "dci1/uv.lock",
)

#: The v5 artifact texts §33 check 15 scans, taken from the same declaration
#: the production check uses rather than from a second list that could drift
#: away from it.
REPO_GLOBS: tuple[str, ...] = ARTIFACT_TEXT_GLOBS

#: The producing code itself. Copied so the declared producing commit really
#: does contain the implementation that wrote the records --- which is the
#: whole content of the provenance rule, not a formality about git state.
REPO_TREES: tuple[str, ...] = ("dci1/src/dci1v7",)


#: The two documents §18 stage 1 binds by content. The synthetic walk builds
#: its own repository in a tmpdir and those files are not in it, so
#: ``manifest.document_hashes`` would refuse to build a manifest --- which is
#: the correct refusal and is exercised against a bare root by
#: ``test_lifecycle``.
#:
#: The walk therefore seeds a placeholder for each **inside the temporary
#: repository it builds**, so the lifecycle can be exercised. The placeholder
#: says what it is in its first line, it lives in a pytest
#: tmpdir, it is never written to the repository, and the walk runs in the
#: ``dci1v7-synthetic`` namespace whose study id no v6 gate or estimator
#: accepts. A hash over a placeholder is a hash over a placeholder; it is not
#: a registration.
PLACEHOLDER_BANNER = (
    "SYNTHETIC PLACEHOLDER --- NOT A DCI-1 v6 ARTIFACT. Written by "
    "tests_v7/synthetic_lifecycle.py into a temporary repository so that the "
    "lifecycle can be walked in the dci1v7-synthetic namespace. The adoption "
    "marker below is part of the stand-in: it says nothing about the real "
    "governed documents, whose own status is read by "
    "manifest.assert_documents_adopted from the files themselves.")


def _seed_placeholder(target: Path, rel: str) -> None:
    """A labelled stand-in, in the tmpdir repository the walk builds.

    It carries an ``ADOPTED`` marker because ``assert_documents_adopted``
    refuses a draft, and a walk that stopped at stage 1 would exercise
    nothing. The marker is inside a pytest tmpdir, under a study id no v6
    gate accepts, one line below a banner saying what the file is --- the
    same trade the placeholder itself already makes for ``document_hashes``.
    It is a stand-in for the real governed documents and never a copy of
    them; what those declare about themselves is read from the files.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix == ".json":
        target.write_text(json.dumps(
            {"_what": PLACEHOLDER_BANNER, "_path": rel,
             "_status": "ADOPTED (placeholder; see _what)"}, indent=2) + "\n")
    else:
        target.write_text(
            f"# {PLACEHOLDER_BANNER}\n\nstatus: ADOPTED\n\n(no content)\n")


def synthetic_repo(root: Path, *, source: Path | str | None = None
                   ) -> tuple[Path, str]:
    """An isolated repository at a clean synthetic producing commit.

    v4r4's integration tests ran the provenance checks against the
    developer's worktree, which has uncommitted changes by construction, and
    the only way to get green was to waive them --- so the rule that a run's
    declared producing commit must contain the code that produced it was the
    one rule the lifecycle never actually exercised.

    This builds the thing the rule describes instead. The v5 source tree and
    every repo-root-relative file a production reader opens are copied into a
    fresh repository, committed, and the resulting head is the synthetic
    producing commit. No check is waived, skipped or made conditional; they
    run against a tree that satisfies them.

    The v4r4 **evidence** directories the §30 ledger registers are not copied
    --- they are 718 MB and nothing reads their contents here --- so the
    synthetic ledger records them ``present: False``. That is the honest
    reading: the ledger records a fact about the tree it was built over, and
    §33 check 11 asks whether the declaration is unambiguous, not whether
    this particular tree holds every artifact.
    """
    import shutil
    import subprocess

    src = Path(source) if source is not None else _REAL_REPO_ROOT
    repo = Path(root) / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    for rel in REPO_FILES:
        origin = src / rel
        if not origin.is_file() or rel in GOVERNED_DOCUMENTS:
            # The two documents §18 stage 1 binds are **always** seeded, never
            # copied, whether or not the repository has them. A walk that
            # copied the real preregistration would be exercising the
            # lifecycle against the study's actual protocol text --- and would
            # start passing or failing stage 1 according to a marker in a
            # document this harness has no business depending on.
            _seed_placeholder(repo / rel, rel)
            continue
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
    for pattern in REPO_GLOBS:
        for origin in sorted(src.glob(pattern)):
            rel = str(origin.relative_to(src))
            if rel in GOVERNED_DOCUMENTS:
                continue          # seeded above; a glob may not overwrite it
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, target)
    for rel in REPO_TREES:
        shutil.copytree(src / rel, repo / rel,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    run = lambda *argv: subprocess.run(  # noqa: E731
        argv, cwd=repo, check=True, capture_output=True, text=True)
    run("git", "init", "-q", "-b", "synthetic")
    run("git", "config", "user.email", "harness@dci1v7-synthetic.invalid")
    run("git", "config", "user.name", "synthetic lifecycle harness")
    run("git", "config", "commit.gpgsign", "false")
    run("git", "add", "-A")
    run("git", "commit", "-q", "-m",
        "synthetic producing commit: the v5 implementation under test")
    head = run("git", "rev-parse", "HEAD").stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                           capture_output=True, text=True).stdout.strip()
    if dirty:                                               # pragma: no cover
        raise AssertionError(
            f"the synthetic repository is not clean after its own commit: "
            f"{dirty.splitlines()[:5]}")
    return repo, head

#: The rungs the harness screens. A subset, because the point is the
#: plumbing: the full 326-rung round-0 screen would put the runtime of an
#: integration test into the tens of minutes without exercising one extra
#: code path.
#: §12.6's C6 needs eight eligible Tier-1/Tier-2 families from six feature
#: groups, C8 needs three Tier-2 rungs from three groups, and C7 needs an
#: eligible Tier-3 BUDGET rung near iota_A. Screening five markers and one
#: budget family could meet none of them --- which nothing noticed while the
#: coverage criterion was evaluated on an empty row set.
SCREEN_FAMILIES = ("MK1", "MK2", "MK3", "MK4", "MK5", "MK6", "MK7", "MK8",
                   "XC1", "XC2", "XC3", "RF5", "RF1")

#: The §34 closures this harness makes, **all of them test-only and none of
#: them a researcher decision**.
#:
#: The suite runs against a FIXTURE record --- v5's, carried into this
#: directory --- rather than against
#: ``reports/dci1v7/researcher_decisions.json``, so that v6's own D19-D26 are
#: open at the start of every test and their refusal branches stay reachable.
#: This harness then supplies a value for each so that the lifecycle can be
#: walked at all.
#:
#: Three things keep that honest. ``restore()`` reopens the registry after
#: every walk, so no closure survives a test; ``resolved_manifest`` **defers
#: to the record in force** for any decision it already carries; and
#: ``_harness_values`` reads the researcher's own record for the VALUE it
#: supplies, so the walk exercises the study that was registered rather than
#: a fixture of it. A harness value is never durable and never evidence that
#: anybody decided anything.
#: Closures the fixture record carries (v5's D0-D18). The harness never
#: supplies a bare value for one of these: ``conftest.harness_decisions``
#: applies them from ``fixture_v5_carried_decisions.json``, which is what lets
#: §34 D17's floor --- whose parameters live in a record, not in the source ---
#: be exercised at all.
RESEARCHER_CLOSED: tuple[str, ...] = tuple(f"D{i}" for i in range(19))
#: The researcher's own record, at its real path --- read for VALUES only.
#: ``decisions.RECORD_PATH`` is monkeypatched to the fixture for the whole
#: suite, so this names the file the study actually registered.
_REAL_RECORD = (Path(__file__).resolve().parents[1] / "reports" / "dci1v7"
                / "researcher_decisions.json")

#: v6's six carried into v7 plus v7's D27, as **fallback** values so the
#: synthetic walk has a branch to take when nobody has decided. None of them
#: is a recommendation. v6's D23 and D26 are withdrawn (v7 A1) and have no
#: entry.
_HARNESS_FALLBACK: dict[str, Any] = {
    "D19": "reachability_only",
    "D20": "calibration_with_measured_transfer",
    "D21": "as_registered",
    "D22": "per_replication",
    "D24": "probe_only_in_library",
    "D25": "survivor_ladder_only",
    "D27": "retain_the_probe_stage",
}


def _harness_values() -> dict[str, Any]:
    """v7's open seven, preferring **the researcher's own record** where it exists.

    The fixture record is v5's and deliberately carries nothing for D19-D26,
    so the harness has to supply something or the walk stops at stage 1 with
    a message about the wrong thing. Which value it supplies matters:

    * **Before adoption** these were open, and any value here was arbitrary.
      ``D26 = 0.05`` in particular was a number the code path needed, not a
      defensible magnitude.
    * **After adoption** the researcher's record names them, and a harness
      that kept its own literals would exercise a study nobody registered ---
      the 19-stage walk and the execution-path audit would be auditing D26 at
      0.05 while the study runs at 0.0142.

    So the recorded value wins where there is one, and the fallback is used
    only where there is not. Reading is all this does: nothing is written to
    the record, and the values still enter the registry as harness closures
    marked non-durable.
    """
    out = dict(_HARNESS_FALLBACK)
    try:
        recorded = {e["id"]: e["value"] for e in
                    decisions.recorded_closures(_REAL_RECORD)}
    except Exception:                                   # noqa: BLE001
        return out
    for key in out:
        if key in recorded:
            out[key] = recorded[key]
    return out


#: Resolved at import so the assertions below have something to check, and
#: re-read per walk by ``resolved_manifest``.
TEST_CLOSURES: dict[str, Any] = _harness_values()
assert not set(TEST_CLOSURES) & set(RESEARCHER_CLOSED)
assert set(TEST_CLOSURES) | set(RESEARCHER_CLOSED) == set(
    decisions.DECISION_IDS), (
    "every §34 decision needs either a fixture closure or a harness value; a "
    "decision with neither makes the walk stop at stage 1 with a message "
    "about the wrong thing")

#: Fixture stand-in **severities** for ``GATE_2_75_COMPOSED_PROBE``. The
#: families are the registered ``probe_only`` ones, so the instrument identity
#: here is production; what is fixture is the severity, which production reads
#: per replication from each stand-in's own solo ladder at iota_A. Passing
#: them explicitly lets a scenario skip the ladder measurement, and
#: ``gates_run.assert_synthetic_only`` refuses the override outside a
#: synthetic study id. The ordinary walk does **not** use it: it runs the
#: production path so the ladder and the placement rule are exercised.
FIXTURE_STANDINS = (Constraint("PS1", 4), Constraint("PS2", 3),
                    Constraint("PS3", 5))

#: Every declared severity of every registered stand-in, so a scripted
#: backend can answer the probe's solo ladder.
def probe_only_rungs() -> list[Constraint]:
    from dci1v7.verifiers.constraints import (PROBE_ONLY_FAMILY_IDS,
                                              registered_severities)
    return [Constraint(kind, q) for kind in PROBE_ONLY_FAMILY_IDS
            for q in registered_severities(kind)]

#: v5's researcher-decision record, carried into ``tests_v7`` as a fixture.
#: See ``conftest``'s module note. Reading a *record* is the only way §34
#: D17's floor --- whose parameters live in a record rather than in the
#: source --- can be exercised at all, and the suite runs against this one
#: rather than the researcher's so that v6's own D19-D26 stay OPEN at the
#: start of every test and their refusal branches remain reachable.
FIXTURE_RECORD = Path(__file__).resolve().parent / \
    "fixture_v5_carried_decisions.json"


_HELD_RECORD_PATH: Any = None


def use_fixture_record() -> None:
    """Point ``decisions`` at the fixture record, and put **only** it in force.

    The fixture is v5's own record, carried into this directory. Reading a
    *record* rather than supplying bare values is what lets §34 D17's floor
    --- whose quantity, value, semantics and derivation deliberately live in a
    record and not in the source --- be exercised at all.

    **It reopens first, and that is the point.** Since 2026-08-26 the real
    ``decisions.RECORD_PATH`` exists and closes all twenty-seven, so a suite
    that merely *added* the fixture on top would run its "this path refuses
    while D-x is open" tests against a registry where nothing is open --- and
    they would pass for the wrong reason, or not at all depending on which
    test ran first. Reopening against the fixture makes every test start from
    the same state: v5's nineteen closed, v6's eight open, whatever the
    researcher has since recorded.

    ``restore`` puts the real path back. Nothing here writes to it.
    """
    global _HELD_RECORD_PATH
    if _HELD_RECORD_PATH is None:
        _HELD_RECORD_PATH = decisions.RECORD_PATH
    decisions.RECORD_PATH = FIXTURE_RECORD
    # `reopen_all_for_testing` blanks the registry and re-applies whatever
    # RECORD_PATH now names, which is the fixture.
    decisions.reopen_all_for_testing()
    open_items.reopen_all_for_testing()


def resolved_manifest(*, eligibility_formulation: str | None = None) -> None:
    """Close every §34 decision, for this process only.

    ``eligibility_formulation`` names which of U4's two constructions this
    process runs. ``None`` --- the default --- takes the researcher's
    recorded resolution, which since A5 is E2. Naming the other one is a
    coverage parameter and never an adoption: a scenario that exercises E1
    exercises a construction the researcher did not take.
    """
    use_fixture_record()
    still_open = [d for d in RESEARCHER_CLOSED if not decisions.is_closed(d)]
    if still_open:
        raise AssertionError(
            f"{still_open} are carried from v5's record and it does not hold "
            "them; conftest's `harness_decisions` applies the fixture record "
            "and this harness will not supply a bare value in its place")
    for decision_id, value in _harness_values().items():
        if not decisions.is_closed(decision_id):
            decisions.close(
                decision_id, value,
                evidence="synthetic lifecycle harness; not a researcher "
                         "decision and never durable",
                decided_by="synthetic lifecycle harness",
                decided_on="synthetic")
    # §33's specification questions. The harness runs against the FIXTURE
    # record, so it supplies a value for each blocking one that the fixture
    # leaves open. Every value is the reading the researcher took for v5, so
    # the walk exercises the adopted protocol rather than an alternative
    # nobody chose --- and none of it is durable or a re-adoption.
    for item_id, resolution in (("U2", "A2"), ("U4", "E2"),
                                ("P1", "confirmed")):
        if item_id == "U4" and eligibility_formulation is not None:
            continue
        if open_items.get_item(item_id).resolution is None:
            open_items.resolve(
                item_id, resolution,
                resolved_by="synthetic lifecycle harness; not a researcher "
                            "resolution and never durable",
                resolved_on="synthetic")
    # U4 --- what makes a pre-screen rung eligible for §12.6's coverage
    # criterion --- is a RESEARCHER decision, taken at E2 in A5 and carried
    # by `researcher_decisions.json`. The harness never supplies a value for
    # it; a scenario that wants the non-adopted construction names it, and
    # naming it is coverage rather than adoption.
    if eligibility_formulation is not None:
        if "U4" in open_items.blocking_items():
            open_items.resolve(
                "U4", eligibility_formulation,
                resolved_by="synthetic lifecycle harness; a named "
                            "construction exercised for coverage, NOT an "
                            "adoption of this reading",
                resolved_on="synthetic")
        elif open_items.get_item("U4").resolution != eligibility_formulation:
            raise AssertionError(
                f"the record resolves U4 at "
                f"{open_items.get_item('U4').resolution!r} and this scenario "
                f"asked for {eligibility_formulation!r}; a change is an "
                "amendment, not a fixture argument")


def restore() -> None:
    global _HELD_RECORD_PATH
    if _HELD_RECORD_PATH is not None:
        decisions.RECORD_PATH = _HELD_RECORD_PATH
        _HELD_RECORD_PATH = None
    decisions.reopen_all_for_testing()
    open_items.reopen_all_for_testing()


def calibration_b_fixtures() -> list[dict[str, Any]]:
    """96 placeholder strings. Not research questions, and they say so."""
    out = []
    for area in C.SUBJECT_AREAS:
        for index in range(C.CALIBRATION_B_PER_AREA):
            slug = area.replace(" ", "-")
            out.append({
                "topic_id": f"synthetic-calb-{slug}-{index:02d}",
                "area": area,
                "question": (f"SYNTHETIC LIFECYCLE FIXTURE {slug} {index:02d}: "
                             "this string is plumbing for an integration test "
                             "and is not a research question"),
                "set": C.CALIBRATION_B,
                "synthetic_fixture": True,
                "authoring_rules_verified": {r: True
                                             for r in C.AUTHORING_RULES},
            })
    return out


def bank():
    return load_bank(calibration_b=calibration_b_fixtures())


# ------------------------------------------------------------- the backend

_WORDS = ("reply", "text", "point", "case", "study", "answer", "matter",
          "reason", "detail", "note", "part", "value", "line", "field")
#: The marker word is an attribute of the family, not a metadata field: the
#: thirteen §7.3 fields describe the family's *structure* and the word itself
#: is the instrument. Reading it from the metadata gave None for every family
#: and produced answers with no markers at all, which the harness surfaced as
#: a candidate pool with zero solo compliance.
_MARKERS = {f.marker for f in FAMILIES.values() if f.marker}


def _u(row_id: str, salt: str = "") -> float:
    digest = hashlib.sha256(f"{row_id}|{salt}".encode()).digest()
    return int.from_bytes(digest[:6], "big") / float(1 << 48)


def scripted_backend(cells: Sequence[Any]):
    """A deterministic generator whose text is engineered per cell.

    For each row it decides, from a hash of the row identity, whether each
    stated constraint should be satisfied, then constructs an answer with
    exactly that many occurrences of the relevant marker or character and a
    longest word inside or outside the stated budget. It is not a model and
    the rates it produces are not behaviour --- they are a fixture chosen so
    that every gate has something to decide.
    """
    by_row: dict[str, Any] = {}
    for cell in cells:
        for draw in range(cell.draws):
            by_row[f"{cell.block_id}:{cell.cell_id}:{draw}"] = cell

    def responder(row: Mapping[str, Any]) -> str:
        cell = by_row.get(row["row_id"])
        present = tuple(cell.present) if cell is not None else ()
        return _compose(row["row_id"], present)

    return fake_backend(responder)


#: The draws a fixture topic is quantised over. §12.3 and §13.7 measure at
#: M_cal = 4, so a per-topic mean is a multiple of a quarter whatever the
#: fixture does; making that explicit keeps the between-topic variance small
#: and known instead of letting an unstructured hash produce split estimates
#: that §13.7's equivalence bound then rejects for a reason that is about the
#: fixture and not about the rule.
FIXTURE_DRAWS = 4


def _satisfies(row_id: str, label: str, rate: float) -> bool:
    """Whether this row satisfies ``label``, at a controlled per-topic mean.

    Each topic satisfies ``floor(rate*4)`` or ``ceil(rate*4)`` of its four
    draws, the second with probability ``frac(rate*4)``, and which draws is a
    fixed rotation of the topic. So every topic's mean is within a quarter of
    the target, the mean over topics is the target, and the variance between
    topics is the smallest a four-draw design admits.
    """
    block, _, tail = row_id.partition(":")
    try:
        draw = int(tail.rpartition(":")[2])
    except ValueError:                                       # pragma: no cover
        draw = 0
    target = rate * FIXTURE_DRAWS
    base = int(target)
    extra = 1 if _u(block, label + "|topic") < (target - base) else 0
    keep = min(FIXTURE_DRAWS, base + extra)
    rotation = int(_u(block, label + "|offset") * FIXTURE_DRAWS)
    return ((draw + rotation) % FIXTURE_DRAWS) < keep


#: The word count `_render` builds before padding. The rate forms need a
#: denominator to turn a percentage into a count, and guessing one produced
#: an answer whose realised rate was on the wrong side of its own severity.
_TARGET_WORDS = 70

#: Filler that ends in `y`, so a `y_final` target is met by choosing words
#: rather than by appending an unrelated tail. Every one is at most six
#: letters, so B's budget still admits it at m = 7.
_Y_WORDS = ("daily", "early", "likely", "ready", "steady", "reply", "study")


def _scripted_count(constraint: Constraint, *, satisfy: bool,
                    words: int = _TARGET_WORDS) -> int:
    """How many of the family's feature a scripted row must contain.

    **Form-aware, which it was not.** The harness used to emit ``severity``
    to satisfy and ``severity + 1`` to violate, which is right for an exact
    count and for a budget and **wrong for a lower bound**: one more than the
    bound still satisfies ``>= q``. Every ``count_lower_bound`` family in the
    library --- CL7, CL8 and now the probe's PS2 --- was therefore scripted to
    pass on every row it was meant to fail, and its fixture solo compliance
    was 1.0 whatever ``_target_rate`` asked for.
    """
    form = FAMILIES[constraint.kind].form
    q = constraint.severity
    if form in RATE_FORMS:
        # 100 * S / W against q, so the count that meets it depends on the
        # denominator the renderer is about to build.
        exact = q * words / 100.0
        if form == FORM_RATE_LOWER_BOUND:
            need = int(math.ceil(exact))
            return need if satisfy else max(0, need - 1)
        under = int(math.floor(exact))
        return under if satisfy else under + 1
    if form in LOWER_BOUND_FORMS:
        return q if satisfy else max(0, q - 1)
    return q if satisfy else q + 1


def _compose(row_id: str, present: Sequence[Constraint]) -> str:
    """Build one answer satisfying the chosen subset of ``present``."""
    marker_counts: dict[str, int] = {}
    max_letters: int | None = None
    semicolons = commas = sentences = None
    capitals = y_words = None
    violate_at: int | None = None
    for constraint in present:
        family = FAMILIES.get(constraint.kind)
        satisfy = _satisfies(row_id, constraint.label,
                             _target_rate(constraint, load=len(present)))
        if constraint.kind == "A":
            marker_counts["however"] = (constraint.severity if satisfy
                                        else constraint.severity + 1)
            continue
        if constraint.kind == "B":
            if satisfy:
                max_letters = constraint.severity
            else:
                # B is stated and this row is scripted to fail it. That is a
                # different thing from B being absent, and conflating them is
                # what made kappa_B flat: an answer that has to violate
                # `at most m letters` needs a word longer than m, while an
                # answer nobody constrained needs whatever length it would
                # naturally have had.
                violate_at = constraint.severity
            continue
        if family is None:
            continue
        marker = family.marker
        statistic = family.statistic_id
        count = _scripted_count(constraint, satisfy=satisfy)
        if marker:
            marker_counts[marker] = count
        elif statistic == "semicolon":
            semicolons = count
        elif statistic == "comma":
            commas = count
        elif statistic == "sentence":
            sentences = count
        elif statistic == "capital_word":
            capitals = count
        elif statistic == "y_final":
            y_words = count
    # §9.3: a pass by a response under twenty words is a VACUOUS pass. The
    # scenario suite needs one replication whose B is vacuous, because that
    # is §12.4 condition 2 and the only production route to REGIME_NOT_FOUND.
    short = any(c.label in SHORT_ANSWER_LABELS for c in present)
    return _render(row_id, marker_counts, max_letters, semicolons, commas,
                   sentences, violate_at=violate_at, short=short,
                   capitals=capitals, y_words=y_words)


#: Scenario knobs. Empty for the ordinary walk, so the default fixture is
#: exactly what it was; a scenario sets one, runs, and clears it. They shape
#: the FIXTURE, never a rule: the point is to put the production path into a
#: registered branch it otherwise never reaches, and then watch the
#: production path decide.
#:
#: ``RATE_OVERRIDES``      label -> solo compliance for that rung
#: ``COMPOSED_OVERRIDES``  label -> compliance when two constraints are stated
#: ``SHORT_ANSWER_LABELS`` labels whose presence makes the answer too short to
#:                         be a non-vacuous pass (§9.3's 20-word predicate)
RATE_OVERRIDES: dict[str, float] = {}
COMPOSED_OVERRIDES: dict[str, float] = {}
SHORT_ANSWER_LABELS: set[str] = set()


def clear_overrides() -> None:
    RATE_OVERRIDES.clear()
    COMPOSED_OVERRIDES.clear()
    SHORT_ANSWER_LABELS.clear()


def _target_rate(constraint: Constraint, *, load: int = 1) -> float:
    """A fixture compliance rate that keeps every band populated.

    Chosen so that the outcome grids fall through their bands with severity
    and the candidate rungs straddle A --- which is what gives §12.3, §13.4,
    §13.8 and §13.12 something to select rather than nothing.
    """
    if load > 1 and constraint.label in COMPOSED_OVERRIDES:
        return COMPOSED_OVERRIDES[constraint.label]
    if constraint.label in RATE_OVERRIDES:
        return RATE_OVERRIDES[constraint.label]
    if constraint.kind == "A":
        return _clamp(0.85 - 0.06 * constraint.severity)
    if constraint.kind == "B":
        return _clamp(0.30 + 0.06 * constraint.severity)
    ladder = FAMILIES[constraint.kind].ladder
    position = (ladder.index(constraint.severity)
                if constraint.severity in ladder else len(ladder) - 1)
    # §12.6's C4 wants a family straddling iota_A with at least three
    # eligible rungs spanning 0.40 in iota, and C1/C2 want rungs on BOTH
    # sides of it. The earlier 0.04 step gave a 0.28 span and put every rung
    # below A, so the coverage criterion could not be met by construction ---
    # which nothing noticed while the criterion was evaluated on an empty
    # set. The step here is a fixture number and nothing reads it as
    # evidence; what it buys is a harness in which C1-C8 can both pass and
    # fail.
    return _clamp(0.88 - 0.075 * position, low=0.12, high=0.88)


def _clamp(rate: float, *, low: float = 0.22, high: float = 0.78) -> float:
    """Keep every fixture rate inside §13.4's admission band, and far enough
    inside it that a Wilson interval on 48 topics is too.

    A fixture rate outside it empties the qualified pool --- a correct verdict
    about a fixture, and a useless one: the walk exists to exercise the
    stages after it. (v7 no longer terminates on a composed rate at Gate 4,
    so the band's other v6 role is gone; the clamp stays for §13.4.)
    """
    return max(low, min(high, rate))


#: P(longest word <= m) for an answer nobody constrained, as a CDF over the
#: focal grid and its extension. Shaped after the measured development curve
#: in `reports/dci1v5/d17_b_strength_decision.md` --- flat and near zero over
#: v4r4's grid, alive across v5's extension --- because §34 D17's floor reads
#: exactly this quantity and a fixture with no curve cannot exercise it.
#: These are fixture numbers, not measurements, and nothing reads them as
#: evidence: what they buy is a harness in which the floor can both pass and
#: refuse.
_NATURAL_LENGTH_CDF: tuple[tuple[int, float], ...] = (
    (9, 0.00), (10, 0.01), (11, 0.07), (12, 0.28), (13, 0.66),
    (14, 0.86), (15, 0.96), (16, 0.99),
)


def _natural_longest(row_id: str) -> int:
    """The longest word an unconstrained answer of this row would contain."""
    u = _u(row_id, "natural-length")
    for length, cdf in _NATURAL_LENGTH_CDF:
        if u < cdf:
            return length
    return 17


def _letters(n: int) -> str:
    """A deterministic alphabetic token of exactly ``n`` letters.

    The verifier counts letters, so what the token *says* does not matter ---
    but it must not be a registered marker and must not contain a hyphen,
    because §9.2 splits on one.
    """
    stem = "consideration"
    if n <= len(stem):
        return stem[:n]
    return stem + "a" * (n - len(stem))


def _render(row_id: str, markers: Mapping[str, int], max_letters: int | None,
            semicolons: int | None, commas: int | None,
            sentences: int | None, *, violate_at: int | None = None,
            short: bool = False, capitals: int | None = None,
            y_words: int | None = None) -> str:
    words: list[str] = []
    for marker, count in sorted(markers.items()):
        words.extend([marker] * count)
    pool = [w for w in _WORDS
            if (max_letters is None or len(w) <= max_letters)
            and w not in _MARKERS]
    if y_words is not None:
        # A y-final target has to be met exactly, so the filler must not
        # contribute any of its own. Two of `_WORDS` end in y.
        pool = [w for w in pool if not w.endswith("y")]
        chosen = [w for w in _Y_WORDS
                  if max_letters is None or len(w) <= max_letters]
        if chosen:
            words.extend([chosen[i % len(chosen)] for i in range(y_words)])
    if not pool:
        pool = ["a", "an", "of"]
    index = int(_u(row_id, "fill") * len(pool))
    target_words = 8 if short else _TARGET_WORDS
    while len(words) < target_words:
        words.append(pool[index % len(pool)])
        index += 1
    if capitals is not None:
        # `words_with_capital` counts alpha runs carrying an upper-case
        # character, and nothing else here produces one --- the renderer
        # never capitalises a sentence opening --- so capitalising exactly
        # this many filler words gives exactly this statistic.
        plain = [i for i, w in enumerate(words)
                 if w not in _MARKERS and w.isalpha()]
        for i in plain[:capitals]:
            words[i] = words[i].capitalize()
    if violate_at is not None:
        # Stated and scripted to fail: one word past the budget, so B's solo
        # compliance is exactly the rate `_target_rate` asks for.
        words.append(_letters(violate_at + 1))
    elif max_letters is None:
        # Not stated at all. This is the row kappa_B is measured on, so its
        # longest word is drawn from the natural-length distribution rather
        # than fixed --- a fixed one gives a step function and no curve.
        words.append(_letters(_natural_longest(row_id)))
    text = " ".join(words)
    if commas is None:
        # An answer nobody constrained still has commas, and how many is a
        # property of the answer. A fixture whose unconstrained text has
        # none makes every comma BUDGET family satisfied by chance, which is
        # chance-degenerate and drops the whole Tier-3 budget class out of
        # the pre-screen --- and with it §12.6's C7.
        commas = 2 + int(_u(row_id, "natural-commas") * 7)
    if commas:
        text = text.replace(" ", ", ", commas)
    if semicolons:
        text = text.replace(" ", "; ", semicolons)
    if not text.endswith("."):
        text += "."
    if short:
        # Deliberately below §9.3's twenty-word predicate and therefore
        # below §8.5's stem band too: `pad_to_band` would lift it back over
        # both, and a vacuous pass is the thing this answer exists to be.
        return text
    text = pad_to_band(text)
    if sentences:
        # After padding, not before: `pad_to_band` appends filler, and an
        # exact-count sentence family scored on padded text was counting the
        # filler's periods. XC3 measured iota 0.000 on every rung and Tier 2
        # never had three eligible feature groups, which is §12.6's C8.
        text = _with_sentences(text, sentences)
    return text


def _with_sentences(text: str, sentences: int) -> str:
    """Exactly ``sentences`` sentences, without changing the word count."""
    words = [w.rstrip(".") for w in text.split()]
    if not words:
        return text
    count = max(1, min(sentences, len(words)))
    cuts = sorted({min(len(words) - 1, int(round(i * len(words) / count)) - 1)
                   for i in range(1, count)} | {len(words) - 1})
    for at in cuts:
        words[at] = words[at] + "."
    return " ".join(words)


def _generate(run_dir, plan, rows):
    """The backend seam for stages whose cells this harness does not hold.

    Falls back to a text that depends only on the row identity. Stages that
    need engineered rates pass ``scripted_backend`` instead.
    """
    def responder(row: Mapping[str, Any]) -> str:
        return _render(row["row_id"], {}, 8, None, None, None)
    return fake_backend(responder)(run_dir, plan, rows)


# ------------------------------------------------------------ the lifecycle

def screen_rungs() -> list[Constraint]:
    out: list[Constraint] = []
    for kind in SCREEN_FAMILIES:
        for severity in FAMILIES[kind].ladder:
            out.append(Constraint(kind, severity))
    out.extend(Constraint("A", q) for q in C.TARGET_GRID)
    out.extend(Constraint("B", q) for q in C.FOCAL_GRID)
    return out


class WalkStopped(Exception):
    """A prefix walk reached its ``stop_after`` stage.

    Carries the live tree and everything a caller needs to continue from it,
    so a conditional scenario branches from a **real signed prefix** rather
    than from a record somebody assembled by hand.
    """

    def __init__(self, **state: Any):
        payloads = state.get("payloads") or {}
        reached = list(payloads)[-1] if payloads else "nothing"
        super().__init__(f"walk stopped after {reached}")
        self.state = state


def walk(root: Path, *, block_limit: int = 4, topic_limit: int = 96,
         repo_root: Path | str | None = None, resamples: int = 200,
         source_repo: Path | str | None = None,
         probe_block_limit: int = 24,
         stop_after: str | None = None) -> dict[str, Any]:
    """Run every stage in order and return each stage's payload.

    ``repo_root`` defaults to an isolated repository this function builds and
    commits (``synthetic_repo``), so every provenance rule runs unwaived. Pass
    one explicitly only to point the walk at a repository you built yourself.
    """
    if repo_root is None:
        repo_root, commit = synthetic_repo(root, source=source_repo)
    else:
        from dci1v4.engine import gitinfo
        commit = gitinfo.head_commit(Path(repo_root))
    context = synthetic_context(root, repo_root=repo_root)
    tree = model_tree(context, MODEL_KEY)
    tree.root.mkdir(parents=True, exist_ok=True)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    from dci1v4.engine.signing import create_signing_key
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)

    the_bank = bank()
    payloads: dict[str, Any] = {}

    def record(outcome):
        payloads[outcome.stage] = outcome.payload
        if stop_after is not None and outcome.stage == stop_after:
            raise WalkStopped(tree=tree, payloads=payloads, bank=the_bank,
                              commit=commit, context=context,
                              repo_root=repo_root)
        return outcome.payload

    from dci1v7.run.registration_run import registration_payload
    from dci1v7.run.lifecycle import run_stage
    record(run_stage(
        tree, C.STAGE_REGISTERED,
        compute=lambda _p: registration_payload(
            tree, producing_commit=commit,
            adoption={"status": "SYNTHETIC", "note": "integration harness"},
            repo_root=repo_root, bank=the_bank),
        producing_commit=commit, environment_digest="synthetic"))

    record(run_stage(
        tree, C.STAGE_QUALIFIED,
        compute=lambda _p: _qualification(context, the_bank, commit),
        producing_commit=commit, environment_digest="synthetic"))

    record(qualification_run.run_gate0(
        tree, producing_commit=commit, environment_digest="synthetic",
        arms=C.ARMS, bank=the_bank, generate=_generate))

    rungs = screen_rungs()
    record(run_stage(
        tree, C.STAGE_REGIME,
        compute=lambda _p: regime_run.regime_payload(
            tree, producing_commit=commit, bank=the_bank,
            generate=_scripted_for(rungs), rungs=rungs),
        producing_commit=commit, environment_digest="synthetic"))

    # Gate 1's corpus is the regime screen's own responses, read from disk
    # by the runner. The harness passes none, which is what a real run does.
    record(regime_run.run_gate1(
        tree, producing_commit=commit, environment_digest="synthetic",
        bank=the_bank, determinism_sample=64, verdict_sample=256))

    record(gates_run.run_gate2(
        tree, producing_commit=commit, environment_digest="synthetic",
        bank=the_bank, generate=_scripted_for(rungs),
        topic_limit=topic_limit))

    record(gates_run.run_gate2_5(tree, producing_commit=commit,
                                 environment_digest="synthetic"))
    # Gate 2.75 composes B with the fixture stand-ins, so the backend needs
    # to satisfy pairs from here on.
    record(gates_run.run_gate2_75(
        tree, producing_commit=commit, environment_digest="synthetic",
        bank=the_bank,
        block_limit=probe_block_limit, resamples=resamples,
        generate=_scripted_for(list(rungs) + probe_only_rungs())))
    record(gates_run.run_gate3a(tree, producing_commit=commit,
                                environment_digest="synthetic",
                                bank=the_bank, resamples=resamples))
    record(gates_run.run_gate3b(tree, producing_commit=commit,
                                environment_digest="synthetic"))
    record(gates_run.run_gate3c(tree, producing_commit=commit,
                                environment_digest="synthetic"))
    # From here the cells are composed, so the backend has to satisfy pairs.
    # The lookup is the screened rungs plus whatever Gate 3B actually bound.
    designed = rungs + _bound_constraints(tree)
    record(gates_run.run_gate4(tree, producing_commit=commit,
                               environment_digest="synthetic", bank=the_bank,
                               resamples=resamples,
                               generate=_scripted_for(designed)))
    try:
        record(prefreeze_run.run_prefreeze_audit_stage(
            tree, producing_commit=commit, environment_digest="synthetic",
            repo_root=repo_root, bank=the_bank))
    except Exception as exc:                                # pragma: no cover
        observed = getattr(exc, "observed", None)
        if observed is None:
            raise
        raise AssertionError(
            "the synthetic pre-freeze audit did not pass:\n"
            + json.dumps(observed, indent=1, default=str)[:6000]) from exc
    record(freeze_run.run_freeze(tree, producing_commit=commit,
                                 environment_digest="synthetic"))
    record(confirmatory_run.run_confirmatory(
        tree, producing_commit=commit, environment_digest="synthetic",
        bank=the_bank, generate=_scripted_for(designed),
        block_limit=block_limit))
    record(analysis_run.run_masked_analysis(
        tree, producing_commit=commit, environment_digest="synthetic",
        entropy=0))
    record(analysis_run.run_unmasking(tree, producing_commit=commit,
                                      environment_digest="synthetic"))
    record(analysis_run.run_unmasked_analysis(
        tree, producing_commit=commit, environment_digest="synthetic"))
    record(analysis_run.run_final_report(
        tree, producing_commit=commit, environment_digest="synthetic"))
    return {"tree": tree, "payloads": payloads, "bank": the_bank}


def _qualification(context, the_bank, commit: str) -> dict[str, Any]:
    """§19's qualification checks, none of them waived.

    An earlier revision of this harness waived ``clean_worktree``, because a
    developer's worktree is dirty by construction. ``synthetic_repo`` removes
    the reason: the context's repo root is a repository this harness built and
    committed, so the check passes on its own terms.
    """
    results = qualification_run.run_checks(context, bank=the_bank)
    failed = [r for r in results if not r["passed"]]
    if failed:
        raise AssertionError(
            f"synthetic qualification failed on {[r['check'] for r in failed]}")
    return {
        "stage": C.STAGE_QUALIFIED,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_QUALIFIED],
        "outcome": "PASS",
        "inputs": {"registration": {"stage": C.STAGE_REGISTERED}},
        "producing_commit": commit,
        "canonical_verifier_hash": results and __import__(
            "dci1v7.verifiers", fromlist=["x"]).verifier_source_hash(),
        "instrument_population": C.N_INSTRUMENTS,
        "checks": results,
        "waived": [],
        "waiver_statement":
            "nothing is waived; the synthetic repository is a real clean "
            "repository at a real resolvable commit",
        "reads_no_behavioural_rate": True,
        "topic_split_identity": the_bank.split_identity,
    }


def _bound_constraints(tree) -> list[Constraint]:
    """Whatever Gate 3B bound to a slot, plus the two outcome constraints."""
    from dci1v7.engine import transitions
    from dci1v7.run.gates_run import slot_map_from_record

    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    probe = transitions.read_stage_record(tree, C.STAGE_GATE2_75)
    gate3b = transitions.read_stage_record(tree, C.STAGE_GATE3B)
    bound = list(slot_map_from_record(gate3b).values())
    bound.append(Constraint("A", gate2["n_star"]))
    from dci1v7.run.gates_run import focal_constraint

    # Gate 2.75 may have re-selected m*, so B is bound at the probe's value.
    bound.append(focal_constraint(probe["m_star"]))
    return bound


def _scripted_for(rungs: Sequence[Constraint]):
    """A backend that engineers rates for whichever cells it is shown.

    It reconstructs the present constraints from the prompt cell registry the
    runner built, which is why ``run/execute`` writes the design file: the
    row identity is the join key between a plan and the rows it produced.

    The wording table is rendered **once** per backend rather than once per
    row. It used to be rendered inside the per-row scan, so a walk paid
    ``rows x instruments x 4`` calls to ``wording`` --- which was tolerable at
    v5's cell counts and is not once the probe generates fifteen cells a
    severity over a library of forty families.
    """
    table = _wording_table(rungs)

    def generate(run_dir, plan, rows):
        def responder(row: Mapping[str, Any]) -> str:
            present = _present_from_prompt(row["user_prompt"], table)
            return _compose(row["row_id"], present)
        return fake_backend(responder)(run_dir, plan, rows)
    return generate


def _wording_table(rungs: Sequence[Constraint]
                   ) -> list[tuple[Constraint, tuple[str, ...]]]:
    """Every instance's four rendered wordings, rendered once."""
    from dci1v7.protocol.wordings import wording

    out: list[tuple[Constraint, tuple[str, ...]]] = []
    for constraint in {r.label: r for r in rungs}.values():
        lines = tuple(
            line for line in
            (wording(constraint.kind, index, constraint.severity)
             for index in range(C.N_WORDINGS)) if line)
        out.append((constraint, lines))
    return out


def _present_from_prompt(prompt: str,
                         table: Sequence[tuple[Constraint, tuple[str, ...]]]
                         ) -> list[Constraint]:
    """Which registered instances a rendered prompt states.

    Reads the rendered wording rather than being told, because that is the
    only thing a backend actually receives --- and it makes the harness fail
    if a wording stops naming its own severity, which is a real defect in the
    thing the model is asked.
    """
    return [constraint for constraint, lines in table
            if any(line in prompt for line in lines)]
