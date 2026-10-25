"""Stand-alone pilot design: cells, prompts, seeds, row identities, counts.

Four conditions, and only these (§13 of the Batch 1 brief):

* ``task_only`` --- the question alone. Frame-invariant by construction (no
  instruction is rendered), so it is generated once per model and its rows
  carry ``frame = None``;
* ``A.however.N``, ``B.maxM`` and every reference variant, alone, per model
  and frame.

**No composed condition can be built.** ``render_prompt`` takes at most one
constraint and has no two-constraint template; ``Cell`` refuses a condition
that is not a single library constraint or ``task_only``. The refusal is on
the only path that produces prompts, so a composed row cannot reach a
generator through this package.

Seeds are a pure function of experimental identity --- domain, root, stage,
model id and revision, prompt hash, draw --- never of batch position, so a
resumed or re-ordered run asks for the same samples.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1.topics import Topic, TopicSplit
from dci.provenance.hashes import sha, sha_text

__all__ = ["TASK_ONLY", "STAGE1", "STAGE2", "Cell", "DesignError",
           "render_prompt", "generation_seed", "stage1_cells", "rows_for_cells",
           "plan_counts", "estimate", "condition_constraint",
           "design_digest", "DIGEST_FIELDS", "instruction_lines"]

TASK_ONLY = "task_only"
STAGE1, STAGE2 = "stage1", "stage2"


class DesignError(ValueError):
    """A pilot design request the protocol does not allow."""


def condition_constraint(condition: str) -> L.Constraint | None:
    if condition == TASK_ONLY:
        return None
    by_id = L.constraint_by_id()
    if condition not in by_id:
        raise DesignError(f"{condition!r} is not task_only or a single library "
                          "constraint; composed conditions are not part of "
                          "the pilot")
    return by_id[condition]


def render_prompt(question: str, constraint: L.Constraint | None,
                  frame: str | None) -> str:
    """The carried DCI-1 template with zero or one instruction line."""
    if isinstance(constraint, (list, tuple)):
        raise DesignError("the pilot renders at most one instruction; a "
                          "composed prompt cannot be built here")
    if constraint is None:
        if frame is not None:
            raise DesignError("a task-only prompt has no frame")
        return CFG.PROMPT_ZERO.format(question=question)
    if frame not in L.FRAMES:
        raise DesignError(f"frame {frame!r}")
    return CFG.PROMPT_ONE.format(question=question,
                                 c1=constraint.render(frame))


def generation_seed(cfg: CFG.PilotConfig, *, stage: str, model: CFG.ModelConfig,
                    prompt_hash: str, draw: int) -> int:
    for name, value in (("stage", stage), ("prompt_hash", prompt_hash)):
        if not value:
            raise DesignError(f"seed derivation is missing {name}")
    if draw < 0:
        raise DesignError("draw index must be non-negative")
    payload = "\x1f".join([cfg.seed_domain, str(cfg.generation_root_seed),
                           stage, model.model_id, model.revision, prompt_hash,
                           str(draw)])
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (1 << 31)


@dataclass(frozen=True)
class Cell:
    stage: str
    model: str
    frame: str | None
    condition: str

    def __post_init__(self):
        if self.stage not in (STAGE1, STAGE2):
            raise DesignError(f"stage {self.stage!r}")
        if self.model not in CFG.MODEL_BY_KEY:
            raise DesignError(f"model {self.model!r} is not configured")
        constraint = condition_constraint(self.condition)
        if constraint is None and self.frame is not None:
            raise DesignError("task_only cells carry no frame")
        if constraint is not None and self.frame not in L.FRAMES:
            raise DesignError(f"{self.condition} needs a frame")

    @property
    def cell_id(self) -> str:
        return f"{self.stage}|{self.model}|{self.frame or '-'}|{self.condition}"

    @property
    def estimate_key(self) -> tuple[str, str | None, str]:
        """The cell's identity across stages (what Stage 2 refines)."""
        return (self.model, self.frame, self.condition)


def _conditions(cfg: CFG.PilotConfig) -> list[str]:
    a = [c.cid for c in L.a_candidates() if c.p["n"] in cfg.a_counts]
    b = [c.cid for c in L.b_candidates() if c.p["m"] in cfg.b_limits]
    return a + b + [c.cid for c in L.reference_library()]


def stage1_cells(cfg: CFG.PilotConfig = CFG.DEFAULT_CONFIG) -> list[Cell]:
    cells = [Cell(STAGE1, m, None, TASK_ONLY) for m in cfg.models]
    cells += [Cell(STAGE1, m, f, cond) for m in cfg.models for f in cfg.frames
              for cond in _conditions(cfg)]
    return cells


def _draws(cfg: CFG.PilotConfig, cell: Cell) -> int:
    if cell.stage == STAGE1:
        return cfg.task_only_draws if cell.condition == TASK_ONLY \
            else cfg.stage1_draws
    return cfg.stage2_draws


def rows_for_cells(cells: Iterable[Cell], split: TopicSplit,
                   cfg: CFG.PilotConfig = CFG.DEFAULT_CONFIG, *,
                   protocol_hash: str = "") -> list[dict[str, Any]]:
    """Every design row, in a deterministic order, with identity and seed."""
    rows: list[dict[str, Any]] = []
    for cell in sorted(cells, key=lambda c: c.cell_id):
        topics: Sequence[Topic] = split.stage1 if cell.stage == STAGE1 \
            else split.stage2
        constraint = condition_constraint(cell.condition)
        model = CFG.MODEL_BY_KEY[cell.model]
        for topic in topics:
            prompt = render_prompt(topic.question, constraint, cell.frame)
            prompt_hash = sha_text(prompt)
            for draw in range(_draws(cfg, cell)):
                identity = {"study_id": CFG.STUDY_ID, "stage": cell.stage,
                            "model": cell.model, "model_id": model.model_id,
                            "model_revision": model.revision,
                            "frame": cell.frame, "condition": cell.condition,
                            "topic_id": topic.topic_id, "draw": draw}
                row_id = "b1-" + sha(["batch1/row", identity])[:24]
                rows.append({
                    "row_id": row_id, "cell_id": cell.cell_id, **identity,
                    "load": 0 if constraint is None else 1,
                    "user_prompt": prompt, "prompt_hash": prompt_hash,
                    "scientific_seed": generation_seed(
                        cfg, stage=cell.stage, model=model,
                        prompt_hash=prompt_hash, draw=draw),
                    "protocol_hash": protocol_hash,
                    "identity_hash": sha(["batch1/identity", identity,
                                          prompt_hash, protocol_hash]),
                })
    ids = [r["row_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise DesignError("the design repeats a row identity")
    if any(r["load"] > 1 for r in rows):
        raise DesignError("a composed row reached the pilot design")
    return rows


#: Every field of a design row that decides what is generated. The digest
#: leaves out ``protocol_hash`` and ``identity_hash`` (which embed the Freeze 1
#: hash) so Freeze 1 can carry the digest of the design it authorises.
DIGEST_FIELDS = ("row_id", "cell_id", "study_id", "stage", "model", "model_id",
                 "model_revision", "frame", "condition", "topic_id", "draw",
                 "load", "user_prompt", "prompt_hash", "scientific_seed")


def design_digest(rows: Iterable[dict[str, Any]]) -> str:
    return sha(["batch1/design-digest/v2",
                [[r[k] for k in DIGEST_FIELDS]
                 for r in sorted(rows, key=lambda r: r["row_id"])]])


def instruction_lines(prompt: str) -> int:
    """Numbered instruction lines in a rendered prompt, read from its bytes."""
    return sum(1 for line in prompt.splitlines()
               if line[:1].isdigit() and ". " in line[:4])


def plan_counts(cells: Iterable[Cell], split: TopicSplit,
                cfg: CFG.PilotConfig = CFG.DEFAULT_CONFIG) -> dict[str, Any]:
    by_model: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    total = 0
    for cell in cells:
        n = (len(split.stage1) if cell.stage == STAGE1 else len(split.stage2)) \
            * _draws(cfg, cell)
        total += n
        by_model[cell.model] = by_model.get(cell.model, 0) + n
        kind = cell.condition if cell.condition == TASK_ONLY else \
            condition_constraint(cell.condition).role
        by_kind[kind] = by_kind.get(kind, 0) + n
    return {"rows": total, "by_model": dict(sorted(by_model.items())),
            "by_condition_kind": dict(sorted(by_kind.items()))}


#: Bytes per stored row, used only for the storage estimate. The scored and
#: design figures are ceilings on what the synthetic end-to-end run measures
#: (``tests/batch1/test_end_to_end.py`` asserts it); the generated-row figure
#: allows for real responses, which carry the rendered prompt, the raw
#: generation and engine fields.
BYTES_PER_GENERATED_ROW = 3_000
BYTES_PER_SCORED_ROW = 4_000
BYTES_PER_DESIGN_ROW = 1_000


def _worst_case_hours(cfg: CFG.PilotConfig, rows: int, cap: int) -> float:
    hours, left = 0.0, rows
    for model in sorted((CFG.MODEL_BY_KEY[k] for k in cfg.models),
                        key=lambda m: m.historical_rows_per_second):
        take = min(left, cap)
        hours += take / model.historical_rows_per_second / 3600
        left -= take
    return round(hours, 3)


def estimate(cfg: CFG.PilotConfig = CFG.DEFAULT_CONFIG,
             *, split: TopicSplit) -> dict[str, Any]:
    """Generation counts, storage and a historical-throughput runtime."""
    s1 = plan_counts(stage1_cells(cfg), split, cfg)
    per_model_cells = len(cfg.frames) * len(_conditions(cfg))
    s2_cells = min(cfg.stage2_max_cells, per_model_cells * len(cfg.models))
    s2_rows = s2_cells * len(split.stage2) * cfg.stage2_draws
    s2_model_cap = min(cfg.stage2_max_cells, per_model_cells) * \
        len(split.stage2) * cfg.stage2_draws
    per_model = {}
    for key in cfg.models:
        model = CFG.MODEL_BY_KEY[key]
        s1_rows = s1["by_model"][key]
        even = s2_rows // len(cfg.models)
        rate = model.historical_rows_per_second
        per_model[key] = {
            "stage1_rows": s1_rows,
            "stage2_rows_if_even": even,
            "stage2_rows_max": s2_model_cap,
            "historical_rows_per_second": rate,
            "stage1_hours_at_historical_rate": round(s1_rows / rate / 3600, 3),
            "stage2_hours_if_even": round(even / rate / 3600, 3),
            "stage2_hours_max": round(s2_model_cap / rate / 3600, 3),
        }
    total_max = s1["rows"] + s2_rows
    return {
        "stage1_rows": s1["rows"], "stage1_by_kind": s1["by_condition_kind"],
        "stage2_max_cells": s2_cells, "stage2_max_rows": s2_rows,
        "total_max_rows": total_max, "per_model": per_model,
        "storage_bytes_max": total_max * (BYTES_PER_GENERATED_ROW
                                          + BYTES_PER_SCORED_ROW
                                          + BYTES_PER_DESIGN_ROW),
        "stage1_hours_at_historical_rates": round(sum(
            v["stage1_hours_at_historical_rate"] for v in per_model.values()), 3),
        "stage2_hours_if_even": round(sum(
            v["stage2_hours_if_even"] for v in per_model.values()), 3),
        # Every Stage 2 row on the slowest model, as far as its cap allows,
        # and the remainder on the next slowest: the generation-time ceiling.
        "stage2_hours_worst_case": _worst_case_hours(cfg, s2_rows,
                                                     s2_model_cap),
        "caveats": [
            "rates are v8.1 confirmatory rows/s on one AMD RX 7900 XTX at "
            "chunk size 64 and ~130 response tokens; they exclude model "
            "load (~2-5 min per backend run) and are not a property of any "
            "NVIDIA or Lambda instance",
            "Stage 2 is bounded by stage2_max_cells; its split across "
            "models is decided by Stage 1 data, so 'if_even' is illustrative "
            "and 'max' is the per-model ceiling",
            "a cloud estimate needs an authorised throughput smoke test on "
            "the chosen instance type (rows/s per model at this cap and "
            "chunk size, model load time, and truncation share)",
        ],
    }
