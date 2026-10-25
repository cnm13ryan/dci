"""What a run root is allowed to contain, recomputed from Freeze 1.

Three checks, each on the path the production code takes:

**Design authentication** (``authenticate_design``). The rows a generator
receives are compared, field by field, with the design regenerated from the
frozen protocol: Stage 1 from Freeze 1 alone, Stage 2 from Freeze 1 and a
Stage 2 selection that is itself recomputed from complete Stage 1 evidence.
Nothing stored in the row is trusted --- not ``condition``, not ``load``, not
``prompt_hash``: the prompt is re-rendered from the frozen topic, condition
and frame, its hash is recomputed from its bytes, the seed is re-derived,
and the number of instruction lines is read from the prompt text. A row id
repeated in the request, a row outside the frozen design, or any field that
differs is refused before a backend is started.

**Stage evidence** (``stage_evidence``). A stage is complete when every
frozen design row has exactly one accepted generation (``outcomes``: VALID
or EMPTY), exactly one scored record derived from that generation (its
``generation_hash``) under the current verifier bundle, and nothing else.
Technical failures logged in ``rejected.jsonl`` and not yet regenerated
make the stage incomplete. An incomplete stage refuses; there is no partial
completion rule (D06).

**Provenance** (``provenance_summary``). Every backend run is an event in
the group's ``provenance.jsonl``, naming the generator the runner used and
the live environment identity it ran under. A real root accepts only seam
runs under the attested environment of Freeze 1, and only rows carrying the
seam's full schema; a synthetic root only stand-in runs. Freeze 2 binds the
hash of every event, so relabelling a synthetic root as real (``RUN.json``)
or editing its provenance is refused or detected (re-audit R4.1).

**Selection binding.** The Stage 2 selection records the hash of the exact
Stage 1 evidence it was computed from. Any later change to a Stage 1
response, score or design row changes that hash, and Stage 2 planning,
execution and finalisation refuse the stale selection.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dci.batch1 import calibration as CAL
from dci.batch1 import config as CFG
from dci.batch1 import design as D
from dci.batch1 import library as L
from dci.batch1 import outcomes as OUT
from dci.batch1 import scoring as S
from dci.batch1 import topics as TOP
from dci.batch1 import verifiers as V
from dci.batch1.store import (
    RunError, canonical, index_rows, read_jsonl, record_hash,
)
from dci.provenance.hashes import sha, sha_text

__all__ = ["IncompleteEvidence", "DesignAuthenticationError", "config_of",
           "split_of", "expected_design", "authenticate_design",
           "StageEvidence", "stage_evidence", "stage1_selection",
           "stored_selection", "tables_for", "rejected_summary",
           "load_generation", "provenance_summary", "namespace_of",
           "SEAM_GENERATOR", "SYNTHETIC_GENERATOR"]

SEAM_GENERATOR, SYNTHETIC_GENERATOR = "vllm_backend", "stand-in"


class IncompleteEvidence(RunError):
    """A stage whose frozen design is not fully generated and scored."""


class DesignAuthenticationError(RunError):
    """Design rows that are not the frozen protocol's rows."""


def config_of(freeze1: Mapping[str, Any]) -> CFG.PilotConfig:
    return CFG.PilotConfig(**{k: tuple(v) if isinstance(v, list) else v
                              for k, v in freeze1["config"].items()})


def split_of(cfg: CFG.PilotConfig) -> TOP.TopicSplit:
    return TOP.split_bank(TOP.load_bank(), pilot_topics=cfg.pilot_topics,
                          stage1_topics=cfg.stage1_topics)


def _plan_path(root: Path, stage: str) -> Path:
    return Path(root) / "plan" / f"{stage}_design.jsonl"


def _selection_path(root: Path) -> Path:
    return Path(root) / "plan" / "stage2_selection.json"


# ------------------------------------------------------------------- design

def _expected_stage1(freeze1: Mapping[str, Any]) -> list[dict[str, Any]]:
    cfg = config_of(freeze1)
    rows = D.rows_for_cells(D.stage1_cells(cfg), split_of(cfg), cfg,
                            protocol_hash=freeze1["manifest_hash"])
    if D.design_digest(rows) != freeze1["stage1"]["design_hash"]:
        raise DesignAuthenticationError(
            "the Stage 1 design this code renders differs from the one "
            "Freeze 1 authorises")
    return rows


def stored_selection(root: Path) -> dict[str, Any]:
    path = _selection_path(root)
    if not path.exists():
        raise IncompleteEvidence("no Stage 2 selection; run select-refinement "
                                 "after Stage 1 is complete")
    return json.loads(path.read_text())


def _expected_stage2(root: Path, freeze1: Mapping[str, Any]
                     ) -> list[dict[str, Any]]:
    selection = stored_selection(root)
    ev1 = stage_evidence(root, freeze1, D.STAGE1)
    if selection.get("stage1_evidence_hash") != ev1.evidence_hash:
        raise RunError("the Stage 2 selection was computed from Stage 1 "
                       "evidence that has since changed (or was edited)")
    fresh = stage1_selection(ev1, config_of(freeze1))
    if canonical(fresh) != canonical(selection):
        raise RunError("the stored Stage 2 selection differs from the one "
                       "Stage 1 reproduces; it was edited")
    return _stage2_rows(selection, freeze1)


def _stage2_rows(selection: Mapping[str, Any], freeze1: Mapping[str, Any]
                 ) -> list[dict[str, Any]]:
    cfg = config_of(freeze1)
    cells = [D.Cell(D.STAGE2, c["model"], c["frame"], c["condition"])
             for c in selection["cells"]]
    return D.rows_for_cells(cells, split_of(cfg), cfg,
                            protocol_hash=freeze1["manifest_hash"])


def expected_design(root: Path, freeze1: Mapping[str, Any], stage: str
                    ) -> list[dict[str, Any]]:
    if stage == D.STAGE1:
        return _expected_stage1(freeze1)
    if stage == D.STAGE2:
        return _expected_stage2(root, freeze1)
    raise DesignAuthenticationError(f"stage {stage!r}")


def _instruction_strings() -> set[str]:
    return {c.render(f) for c in L.all_constraints() for f in L.FRAMES}


def _check_prompt(row: Mapping[str, Any], expected: Mapping[str, Any],
                  instructions: set[str]) -> None:
    prompt = row.get("user_prompt")
    if not isinstance(prompt, str):
        raise DesignAuthenticationError(f"{row.get('row_id')}: no prompt")
    if sha_text(prompt) != expected["prompt_hash"]:
        raise DesignAuthenticationError(
            f"{row['row_id']}: the prompt is not the frozen rendering")
    stated = sum(prompt.count(text) for text in instructions)
    lines = D.instruction_lines(prompt)
    want = 0 if expected["condition"] == D.TASK_ONLY else 1
    if lines != want or stated != want:
        raise DesignAuthenticationError(
            f"{row['row_id']}: the prompt carries {lines} instruction lines "
            f"({stated} library instructions); the pilot allows {want}")


def authenticate_design(root: Path, freeze1: Mapping[str, Any],
                        design: Sequence[Mapping[str, Any]]
                        ) -> dict[str, dict[str, dict[str, Any]]]:
    """Refuse any row that is not, byte for byte, a frozen design row.

    Returns the full expected design per stage, keyed by row id."""
    stages = sorted({r.get("stage") for r in design})
    expected = {stage: {r["row_id"]: r
                        for r in expected_design(root, freeze1, stage)}
                for stage in stages}
    instructions = _instruction_strings()
    seen: set[str] = set()
    for row in design:
        rid = row.get("row_id")
        if rid in seen:
            raise DesignAuthenticationError(f"{rid} is requested twice")
        seen.add(rid)
        want = expected[row["stage"]].get(rid)
        if want is None:
            raise DesignAuthenticationError(
                f"{rid} is not a row of the frozen {row['stage']} design")
        if canonical(dict(row)) != canonical(want):
            fields = sorted(k for k in set(row) | set(want)
                            if row.get(k) != want.get(k))
            raise DesignAuthenticationError(
                f"{rid} differs from the frozen design in {fields}")
        _check_prompt(row, want, instructions)
    return expected


# ----------------------------------------------------------------- evidence

def load_generation(root: Path, stage: str
                    ) -> tuple[dict[str, dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    for model_dir in sorted((Path(root) / "generation" / stage).glob("*")):
        rows += read_jsonl(model_dir / "rows.jsonl")
    return index_rows(rows, what=f"{stage} generation")


def rejected_summary(root: Path, stage: str,
                     accepted: Iterable[str] = (), *,
                     max_technical_attempts: int | None = None
                     ) -> dict[str, Any]:
    """Technical attempts, kept apart from evidence; open ones are those
    whose row has no accepted generation yet, and exhausted ones those that
    reached the retry limit (D04)."""
    records: list[dict[str, Any]] = []
    for model_dir in sorted((Path(root) / "generation" / stage).glob("*")):
        records += read_jsonl(model_dir / "rejected.jsonl")
    accepted = set(accepted)
    by_reason: dict[str, int] = {}
    technical: dict[str, int] = {}
    for r in records:
        by_reason[r["reason"]] = by_reason.get(r["reason"], 0) + 1
        if str(r["reason"]).startswith(OUT.TECHNICAL + ":"):
            technical[r["row_id"]] = technical.get(r["row_id"], 0) + 1
    open_ids = sorted({r["row_id"] for r in records} - accepted)
    exhausted = sorted(rid for rid in open_ids
                       if max_technical_attempts is not None
                       and technical.get(rid, 0) >= max_technical_attempts)
    return {"attempts": len(records), "by_reason": dict(sorted(by_reason.items())),
            "open_rows": len(open_ids), "open_row_ids": open_ids[:20],
            "exhausted_rows": len(exhausted),
            "exhausted_row_ids": exhausted[:20],
            "hash": record_hash(sorted((r["row_id"], r["attempt"], r["reason"])
                                       for r in records))}


def namespace_of(root: Path) -> str:
    marker = Path(root) / "RUN.json"
    if not marker.exists():
        raise RunError(f"{root} has no RUN.json; it is not a run root")
    return json.loads(marker.read_text())["namespace"]


def provenance_summary(root: Path, stage: str, freeze1: Mapping[str, Any],
                       namespace: str) -> dict[str, Any]:
    """Every provenance event of the stage, checked against the namespace,
    and their hash."""
    want = {"real": SEAM_GENERATOR, "synthetic": SYNTHETIC_GENERATOR}.get(
        namespace)
    if want is None:
        raise RunError(f"namespace {namespace!r} holds no pilot evidence")
    locked = (freeze1.get("execution_environment") or {}).get("identity_hash")
    events: dict[str, list[dict[str, Any]]] = {}
    runs, identities = 0, set()
    for model_dir in sorted((Path(root) / "generation" / stage).glob("*")):
        mine = read_jsonl(model_dir / "provenance.jsonl")
        events[model_dir.name] = mine
        for e in mine:
            if e.get("event") != "backend_run":
                continue
            runs += 1
            where = f"{model_dir / 'provenance.jsonl'} attempt {e.get('attempt')}"
            if e.get("generator") != want:
                raise RunError(f"{where}: generator {e.get('generator')!r} in "
                               f"a {namespace} root (expected {want!r})")
            if namespace == "real":
                if not locked or e.get("environment_identity_hash") != locked:
                    raise RunError(f"{where}: not run under the environment "
                                   "attested in Freeze 1")
                identities.add(e["environment_identity_hash"])
    return {"namespace": namespace, "generator": want, "backend_runs": runs,
            "environment_identity_hashes": sorted(identities),
            "hash": record_hash(events)}


@dataclass
class StageEvidence:
    stage: str
    design: list[dict[str, Any]]
    generation: dict[str, dict[str, Any]]
    scored: dict[str, dict[str, Any]]
    repeats_collapsed: int
    rejected: dict[str, Any]
    classes: dict[str, int] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def generation_hash(self) -> str:
        return record_hash(sorted((rid, record_hash(r))
                                  for rid, r in self.generation.items()))

    @property
    def scored_hash(self) -> str:
        return record_hash(sorted((rid, record_hash(r))
                                  for rid, r in self.scored.items()))

    @property
    def evidence_hash(self) -> str:
        return sha(["batch1/stage-evidence", self.stage,
                    D.design_digest(self.design), self.generation_hash,
                    self.scored_hash, self.repeats_collapsed])

    def manifest(self) -> dict[str, Any]:
        return {"stage": self.stage, "design_rows": len(self.design),
                "design_digest": D.design_digest(self.design),
                "generation_hash": self.generation_hash,
                "scored_hash": self.scored_hash,
                "evidence_hash": self.evidence_hash,
                "outcome_classes": dict(sorted(self.classes.items())),
                "repeats_collapsed": self.repeats_collapsed,
                "technical_attempts": self.rejected,
                "provenance": self.provenance}


def stage_evidence(root: Path, freeze1: Mapping[str, Any], stage: str, *,
                   verify_scores: bool = False) -> StageEvidence:
    """The complete, authenticated evidence of one stage, or a refusal."""
    root = Path(root)
    design = expected_design(root, freeze1, stage)
    plan = read_jsonl(_plan_path(root, stage))
    if canonical(plan) != canonical(design):
        raise DesignAuthenticationError(
            f"{_plan_path(root, stage)} differs from the frozen {stage} design")
    want = {r["row_id"]: r for r in design}
    generation, repeats = load_generation(root, stage)
    extra = sorted(set(generation) - set(want))
    if extra:
        raise RunError(f"{stage}: generated rows outside the frozen design: "
                       f"{extra[:3]}")
    namespace = namespace_of(root)
    classes: dict[str, int] = {}
    for rid, raw in generation.items():
        if raw.get("identity_hash") != want[rid]["identity_hash"]:
            raise RunError(f"{rid}: generated under another identity")
        cls = OUT.classify(raw)
        if not cls.behavioural:
            raise RunError(f"{rid}: rows.jsonl holds a non-evidence row "
                           f"({cls.reason})")
        if namespace == "real" and not OUT.SEAM_ROW_KEYS <= set(raw):
            raise RunError(f"{rid}: a real root holds a row without the seam "
                           "schema; it was not produced by the vLLM seam")
        classes[cls.kind] = classes.get(cls.kind, 0) + 1
    provenance = provenance_summary(root, stage, freeze1, namespace)
    rejected = rejected_summary(
        root, stage, generation,
        max_technical_attempts=config_of(freeze1).max_technical_attempts)
    missing = [rid for rid in want if rid not in generation]
    if missing:
        raise IncompleteEvidence(
            f"{stage} is incomplete: {len(missing)} of {len(want)} design rows "
            f"have no accepted generation ({rejected['open_rows']} with open "
            f"technical failures, {rejected['exhausted_rows']} of them at the "
            "retry limit); resume generation. No partial-completion "
            "rule exists (D06)")
    scored_path = root / "scored" / f"{stage}.jsonl"
    scored, srepeats = index_rows(read_jsonl(scored_path), what=f"{stage} scores")
    if srepeats:
        raise RunError(f"{scored_path}: a row is scored twice")
    if set(scored) != set(generation):
        raise IncompleteEvidence(f"{stage}: scoring is missing or stale; run "
                                 "score")
    bundle = V.verifier_bundle_hash()
    for rid, row in scored.items():
        if row.get("generation_hash") != record_hash(generation[rid]):
            raise RunError(f"{rid}: its score was not computed from the stored "
                           "response (edited or stale); re-run score")
        if row.get("verifier_bundle_hash") != bundle:
            raise RunError(f"{rid}: scored under another verifier bundle")
    if verify_scores:
        fresh = S.score_rows(generation.values(), design)
        for row in fresh:
            if canonical(row) != canonical(scored[row["row_id"]]):
                raise RunError(f"{row['row_id']}: the stored score differs "
                               "from the one its response reproduces")
    return StageEvidence(stage, design, generation, scored, repeats, rejected,
                         classes, provenance)


def tables_for(evidences: Iterable[StageEvidence], *, synthetic: bool
               ) -> S.PilotTables:
    evidences = list(evidences)
    scored = [r for ev in evidences for r in ev.scored.values()]
    designs = [r for ev in evidences for r in ev.design]
    return S.build_tables(scored, designs, synthetic=synthetic)


def stage1_selection(ev1: StageEvidence, cfg: CFG.PilotConfig
                     ) -> dict[str, Any]:
    """The D06 selection, bound to the Stage 1 evidence it reads."""
    if ev1.stage != D.STAGE1:
        raise RunError("the Stage 2 selection reads Stage 1 evidence only")
    synthetic = False  # the namespace does not change the rule
    selection = CAL.select_stage2(tables_for([ev1], synthetic=synthetic), cfg)
    selection = json.loads(json.dumps(selection))
    selection["stage1_evidence_hash"] = ev1.evidence_hash
    selection["stage1_rows"] = len(ev1.design)
    return selection
