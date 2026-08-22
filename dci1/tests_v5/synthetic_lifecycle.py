"""An end-to-end walk of the v5 lifecycle with no model and no science.

**This is an engineering harness. Nothing it produces is evidence.** It runs
in the ``synthetic`` namespace --- study id ``dci1v5-synthetic``, its own
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

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v5 import PREREGISTRATION, REFERENCE_DESIGN_SPEC
from dci1v5.protocol.reuse_ledger import ARTIFACT_TEXT_GLOBS
from dci1v5.engine.context import REPO_ROOT as _REAL_REPO_ROOT
from dci1v5.engine.context import synthetic_context
from dci1v5.engine.paths import model_tree
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions, open_items
from dci1v5.run import (analysis_run, confirmatory_run, freeze_run, gates_run,
                        prefreeze_run, qualification_run, regime_run)
from dci1v5.run.execute import fake_backend
from dci1v5.topics.bank import load_bank
from dci1v5.verifiers.constraints import FAMILIES, Constraint
from dci1v5.verifiers.realistic_witness import pad_to_band

MODEL_KEY = "gemma-3n-e2b-it"

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
    "dci1/reports/dci1v5/development/d2_kappa_under_b.json",
    "dci1/reports/dci1v5/development/d3_split_half_stability.json",
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
REPO_TREES: tuple[str, ...] = ("dci1/src/dci1v5",)


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
        if not origin.is_file():                            # pragma: no cover
            continue
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
    for pattern in REPO_GLOBS:
        for origin in sorted(src.glob(pattern)):
            target = repo / origin.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, target)
    for rel in REPO_TREES:
        shutil.copytree(src / rel, repo / rel,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    run = lambda *argv: subprocess.run(  # noqa: E731
        argv, cwd=repo, check=True, capture_output=True, text=True)
    run("git", "init", "-q", "-b", "synthetic")
    run("git", "config", "user.email", "harness@dci1v5-synthetic.invalid")
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
SCREEN_FAMILIES = ("MK1", "MK2", "MK3", "MK4", "MK5", "XC1", "XC2",
                   "XC3", "RF1")

#: The §34 closures this harness makes, all of them test-only. **D6, D16 and
#: D18 are not here**: the researcher has taken them and they are in force
#: from ``reports/dci1v5/researcher_decisions.json``, so the synthetic walk
#: runs the adopted protocol for those three rather than a harness value that
#: happened to agree --- or, worse, one that did not.
RESEARCHER_CLOSED = ("D6", "D16", "D18")
TEST_CLOSURES: dict[str, Any] = {
    "D0": "adopt", "D1": "four_models_56_cells", "D2": "no_load_three",
    "D3": "author_before_adoption", "D4": "approve_eight",
    "D5": "lexicographic", "D7": 0.90,
    "D8": 0.75, "D9": "unavailable", "D10": "one_companion", "D11": "carry",
    "D12": "direction_and_sesoi_only", "D13": "primary_tier",
    "D14": "iota_primary", "D15": "both_transfer",
    "D17": "no_floor",
}
assert not set(TEST_CLOSURES) & set(RESEARCHER_CLOSED)


def resolved_manifest() -> None:
    """Close every §34 decision and resolve U2, for this process only."""
    still_open = [d for d in RESEARCHER_CLOSED if not decisions.is_closed(d)]
    if still_open:
        raise AssertionError(
            f"{still_open} are researcher closures and the record does not "
            "carry them; the harness will not supply a value for a decision "
            "somebody was supposed to take")
    for decision_id, value in TEST_CLOSURES.items():
        if not decisions.is_closed(decision_id):
            decisions.close(
                decision_id, value,
                evidence="synthetic lifecycle harness; not a researcher "
                         "decision and never durable",
                decided_by="synthetic lifecycle harness",
                decided_on="synthetic")
    if "U2" in open_items.blocking_items():
        open_items.resolve("U2", "A2",
                           resolved_by="synthetic lifecycle harness",
                           resolved_on="synthetic")


def restore() -> None:
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


def _compose(row_id: str, present: Sequence[Constraint]) -> str:
    """Build one answer satisfying the chosen subset of ``present``."""
    marker_counts: dict[str, int] = {}
    max_letters: int | None = None
    semicolons = commas = sentences = None
    for constraint in present:
        family = FAMILIES.get(constraint.kind)
        satisfy = _satisfies(row_id, constraint.label,
                             _target_rate(constraint))
        if constraint.kind == "A":
            marker_counts["however"] = (constraint.severity if satisfy
                                        else constraint.severity + 1)
            continue
        if constraint.kind == "B":
            max_letters = constraint.severity if satisfy else None
            continue
        if family is None:
            continue
        marker = family.marker
        statistic = family.statistic_id
        if marker:
            marker_counts[marker] = (constraint.severity if satisfy
                                     else constraint.severity + 1)
        elif statistic == "semicolon":
            semicolons = (constraint.severity if satisfy
                          else constraint.severity + 1)
        elif statistic == "comma":
            commas = (constraint.severity if satisfy
                      else constraint.severity + 1)
        elif statistic == "sentence":
            sentences = (constraint.severity if satisfy
                         else constraint.severity + 1)
    return _render(row_id, marker_counts, max_letters, semicolons, commas,
                   sentences)


def _target_rate(constraint: Constraint) -> float:
    """A fixture compliance rate that keeps every band populated.

    Chosen so that the outcome grids fall through their bands with severity
    and the candidate rungs straddle A --- which is what gives §12.3, §13.4,
    §13.8 and §13.12 something to select rather than nothing.
    """
    if constraint.kind == "A":
        return _clamp(0.85 - 0.06 * constraint.severity)
    if constraint.kind == "B":
        return _clamp(0.30 + 0.06 * constraint.severity)
    ladder = FAMILIES[constraint.kind].ladder
    position = (ladder.index(constraint.severity)
                if constraint.severity in ladder else len(ladder) - 1)
    return _clamp(0.78 - 0.04 * position)


def _clamp(rate: float) -> float:
    """Keep every fixture rate inside §13.14's composed-headroom band, and
    far enough inside it that a Wilson interval on 48 topics is too (§13.4).

    A fixture rate outside those bands terminates the harness at Gate 4 or
    empties the qualified pool --- a correct verdict about a fixture, and a
    useless one: the walk exists to exercise the stages after them.
    """
    return max(0.22, min(0.78, rate))


def _render(row_id: str, markers: Mapping[str, int], max_letters: int | None,
            semicolons: int | None, commas: int | None,
            sentences: int | None) -> str:
    words: list[str] = []
    for marker, count in sorted(markers.items()):
        words.extend([marker] * count)
    pool = [w for w in _WORDS
            if (max_letters is None or len(w) <= max_letters)
            and w not in _MARKERS]
    if not pool:
        pool = ["a", "an", "of"]
    index = int(_u(row_id, "fill") * len(pool))
    while len(words) < 70:
        words.append(pool[index % len(pool)])
        index += 1
    if max_letters is None:
        words.append("extraordinarily")
    text = " ".join(words)
    if commas:
        text = text.replace(" ", ", ", commas)
    if semicolons:
        text = text.replace(" ", "; ", semicolons)
    if sentences and sentences > 1:
        parts = text.split(" ")
        step = max(1, len(parts) // sentences)
        rebuilt = []
        for i, word in enumerate(parts):
            rebuilt.append(word)
            if (i + 1) % step == 0 and rebuilt.count(".") < sentences - 1:
                rebuilt[-1] = word + "."
        text = " ".join(rebuilt)
    if not text.endswith("."):
        text += "."
    return pad_to_band(text)


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


def walk(root: Path, *, block_limit: int = 4, topic_limit: int = 96,
         repo_root: Path | str | None = None, resamples: int = 200,
         source_repo: Path | str | None = None) -> dict[str, Any]:
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
        return outcome.payload

    from dci1v5.run.registration_run import registration_payload
    from dci1v5.run.lifecycle import run_stage
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
                               generate=_scripted_for(designed)))
    record(prefreeze_run.run_prefreeze_audit_stage(
        tree, producing_commit=commit, environment_digest="synthetic",
        repo_root=repo_root, bank=the_bank))
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
            "dci1v5.verifiers", fromlist=["x"]).verifier_source_hash(),
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
    from dci1v5.engine import transitions
    from dci1v5.run.gates_run import slot_map_from_record

    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    gate3b = transitions.read_stage_record(tree, C.STAGE_GATE3B)
    bound = list(slot_map_from_record(gate3b).values())
    bound.append(Constraint("A", gate2["n_star"]))
    bound.append(Constraint("B", gate2["m_star"]))
    return bound


def _scripted_for(rungs: Sequence[Constraint]):
    """A backend that engineers rates for whichever cells it is shown.

    It reconstructs the present constraints from the prompt cell registry the
    runner built, which is why ``run/execute`` writes the design file: the
    row identity is the join key between a plan and the rows it produced.
    """
    lookup = {r.label: r for r in rungs}

    def generate(run_dir, plan, rows):
        def responder(row: Mapping[str, Any]) -> str:
            present = _present_from_prompt(row["user_prompt"], lookup)
            return _compose(row["row_id"], present)
        return fake_backend(responder)(run_dir, plan, rows)
    return generate


def _present_from_prompt(prompt: str, lookup: Mapping[str, Constraint]
                         ) -> list[Constraint]:
    """Which registered instances a rendered prompt states.

    Reads the rendered wording rather than being told, because that is the
    only thing a backend actually receives --- and it makes the harness fail
    if a wording stops naming its own severity, which is a real defect in the
    thing the model is asked.
    """
    from dci1v5.protocol.wordings import wording

    present: list[Constraint] = []
    for constraint in lookup.values():
        for index in range(C.N_WORDINGS):
            line = wording(constraint.kind, index, constraint.severity)
            if line and line in prompt:
                present.append(constraint)
                break
    return present
