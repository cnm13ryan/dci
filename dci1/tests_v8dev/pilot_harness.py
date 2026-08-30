"""The v8 pilot lifecycle, executed with no model and no science.

Builds an isolated, committed repository so every provenance rule runs
unwaived; drives the nine stages through the **production** runners in the
``dci1v8-synthetic`` namespace under a temporary root; supplies the one
substitution the synthetic namespace admits --- a scripted generator whose
text is engineered per cell from the row identity (v7's
``tests_v7.synthetic_lifecycle._compose``, reused: it knows every family's
predicate) --- and the scale knobs (a rung subset, a topic limit at Gate 2,
fewer bootstrap resamples). Nothing it writes can be read as pilot evidence:
the study id is ``dci1v8-synthetic`` and ``StudyContext`` refuses a root that
overlaps any real tree.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v7.protocol import constants as C
from dci1v7.topics.bank import load_bank
from dci1v7.verifiers.constraints import FAMILIES, Constraint
from dci1v8dev.run import (BASE_PREREGISTRATION, DESIGN_DOCUMENT,
                           FRAME_DOCUMENT, PILOT_DOCUMENT)
from dci1v8dev.run import stages as S
from dci1v8dev.run.context import model_tree, synthetic_context
from dci1v8dev.run.execute import fake_backend

from tests_v7 import synthetic_lifecycle as V7

MODEL_KEY = "qwen3-4b-instruct-2507"

_REAL_REPO_ROOT = Path(__file__).resolve().parents[2]

REPO_TREES = ("dci1/src/dci1v4", "dci1/src/dci1v7", "dci1/src/dci1v8dev")
REPO_FILES = ("dci1/uv.lock",)
DOCUMENTS = (DESIGN_DOCUMENT, PILOT_DOCUMENT, FRAME_DOCUMENT,
             BASE_PREREGISTRATION)

PLACEHOLDER = ("SYNTHETIC PLACEHOLDER --- NOT A DCI-1 ARTIFACT. Written by "
               "tests_v8dev/pilot_harness.py into a temporary repository so "
               "that the v8 pilot lifecycle can be walked in the "
               "dci1v8-synthetic namespace.")

#: The families the harness screens: every marker family (the spectrum's
#: pool), a Tier-2 family per feature group where one exists, and the
#: Tier-3 budget families the class arm and the chance basis need.
SCREEN_FAMILIES = ("MK1", "MK2", "MK3", "MK4", "MK5", "MK6", "MK7", "MK8",
                   "XC1", "XC2", "XC3", "RF1", "RF5", "RF6", "RF8", "CL7",
                   "CL8")


def synthetic_repo(root: Path, *, source: Path | None = None) -> tuple[Path, str]:
    src = Path(source) if source is not None else _REAL_REPO_ROOT
    repo = Path(root) / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    for rel in REPO_FILES:
        origin = src / rel
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if origin.is_file():
            shutil.copy2(origin, target)
        else:
            target.write_text(json.dumps({"_what": PLACEHOLDER}))
    for rel in DOCUMENTS:
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {PLACEHOLDER}\n\nstatus: PLACEHOLDER\n")
    for rel in REPO_TREES:
        shutil.copytree(src / rel, repo / rel,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    run = lambda *argv: subprocess.run(  # noqa: E731
        argv, cwd=repo, check=True, capture_output=True, text=True)
    run("git", "init", "-q", "-b", "synthetic")
    run("git", "config", "user.email", "harness@dci1v8-synthetic.invalid")
    run("git", "config", "user.name", "v8 pilot harness")
    run("git", "config", "commit.gpgsign", "false")
    run("git", "add", "-A")
    run("git", "commit", "-q", "-m", "synthetic producing commit")
    head = run("git", "rev-parse", "HEAD").stdout.strip()
    return repo, head


def present_of(cell_id: str) -> tuple[Constraint, ...]:
    """The stated constraint of a cell, from its id (``solo:MK1:3``)."""
    if not cell_id.startswith("solo:"):
        return ()
    label = cell_id.partition(":")[2]
    kind, _, severity = label.rpartition(":")
    q = int(severity)
    if kind == "A":
        return (Constraint("A", q),)
    if kind == "B":
        return (Constraint("B", q, extended=q in C.FOCAL_EXTENSION),)
    return (Constraint(kind, q, reserve=True),)


def scripted_generate(run_dir, plan, rows):
    """The synthetic seam: v7's per-cell composer, driven by the cell id.
    Frame-blind: the four frames behave identically up to which topics
    each frame happens to hold."""
    def responder(row: Mapping[str, Any]) -> str:
        return V7._compose(row["row_id"], present_of(row["cell_id"]))
    return fake_backend(responder)(run_dir, plan, rows)


def frame_of_design_row(row: Mapping[str, Any]) -> int:
    """The frame of a design row's block: ``<prefix>-<index>`` % N_WORDINGS
    (the same rule ``execute.SoloCell`` allocates by)."""
    return int(str(row["block_id"]).rpartition("-")[2]) % C.N_WORDINGS


def frame_effect_generate(effects: Mapping[str, Mapping[int, float]]):
    """A generator with a genuine frame effect: for family ``kind`` under
    frame ``f``, a scripted-compliant answer is spoiled with probability
    ``1 - effects[kind][f]`` (an extra marker word for an exact-count
    family; one over-long word for B), by a hash of the row id, so frame f
    reads that family as harder. Families and frames not named behave as
    the frame-blind composer. The verifier is unchanged: the effect is in
    the answers, exactly as a wording effect would be."""
    import hashlib

    def responder(row: Mapping[str, Any]) -> str:
        present = present_of(row["cell_id"])
        text = V7._compose(row["row_id"], present)
        if not present:
            return text
        constraint = present[0]
        keep = (effects.get(constraint.kind) or {}).get(frame_of_design_row(row))
        if keep is None:
            return text
        digest = hashlib.sha256(f"frame-effect|{row['row_id']}".encode()).hexdigest()
        u = int(digest[:12], 16) / float(16 ** 12)
        if u < keep:
            return text
        if constraint.kind == "B":
            return text.rstrip(".") + " " + "consideration" + "a" * 6 + "."
        marker = ("however" if constraint.kind == "A"
                  else FAMILIES[constraint.kind].marker)
        if marker:
            return text.rstrip(".") + f" {marker}."
        return text
    return fake_backend(responder)


def screen_rungs(families: Sequence[str] = SCREEN_FAMILIES) -> list[Constraint]:
    out = [Constraint(k, q) for k in families for q in FAMILIES[k].ladder]
    out += [Constraint("A", q) for q in C.TARGET_GRID]
    out += [Constraint("B", q) for q in C.FOCAL_GRID]
    return out


class WalkStopped(Exception):
    def __init__(self, **state):
        super().__init__("walk stopped")
        self.state = state


def walk(root: Path, *, topic_limit: int = 96, resamples: int = 200,
         families: Sequence[str] = SCREEN_FAMILIES,
         stop_after: str | None = None,
         repo_root: Path | None = None,
         generate=None) -> dict[str, Any]:
    """Every stage in order through the production runners. ``generate``
    defaults to the frame-blind scripted composer; ``frame_effect_generate``
    gives one with a frame effect."""
    generate = generate if generate is not None else scripted_generate
    from dci1v4.engine.signing import create_signing_key
    from dci1v8dev.run import (calibration, instrument, qualification,
                               references, regime, registration, report,
                               rescreen)

    if repo_root is None:
        repo_root, commit = synthetic_repo(root)
    else:
        from dci1v4.engine import gitinfo
        commit = gitinfo.head_commit(Path(repo_root))
    context = synthetic_context(root, repo_root=repo_root)
    tree = model_tree(context, MODEL_KEY)
    tree.root.mkdir(parents=True, exist_ok=True)
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    bank = load_bank()
    payloads: dict[str, Any] = {}

    def record(outcome):
        payloads[outcome.stage] = outcome.payload
        if stop_after is not None and outcome.stage == stop_after:
            raise WalkStopped(tree=tree, payloads=payloads, bank=bank,
                              commit=commit, context=context,
                              repo_root=repo_root)
        return outcome.payload

    env = "synthetic"
    record(registration.run_registration(
        tree, producing_commit=commit, environment_digest=env,
        repo_root=repo_root, bank=bank))
    record(qualification.run_qualification(
        tree, producing_commit=commit, environment_digest=env, bank=bank))
    record(qualification.run_gate0(
        tree, producing_commit=commit, environment_digest=env, bank=bank,
        generate=generate))
    record(regime.run_regime_screen(
        tree, producing_commit=commit, environment_digest=env, bank=bank,
        generate=generate, rungs=screen_rungs(families)))
    record(rescreen.run_second_pass(
        tree, producing_commit=commit, environment_digest=env, bank=bank,
        generate=generate))
    record(instrument.run_gate1(
        tree, producing_commit=commit, environment_digest=env,
        determinism_sample=64))
    record(calibration.run_gate2(
        tree, producing_commit=commit, environment_digest=env, bank=bank,
        generate=generate, topic_limit=topic_limit))
    record(references.run_gate3(
        tree, producing_commit=commit, environment_digest=env,
        resamples=resamples))
    record(report.run_report(
        tree, producing_commit=commit, environment_digest=env))
    return {"tree": tree, "payloads": payloads, "bank": bank,
            "commit": commit, "context": context, "repo_root": repo_root}
