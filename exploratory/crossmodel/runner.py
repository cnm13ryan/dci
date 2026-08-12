"""The cross-model DCI transport runner.

One design, five checkpoints, one contract. This module builds the frozen slice
from `crossmodel.contract`, drives it through whichever `ModelAdapter` the
registry returns, and writes rows that carry their own provenance.

Determinism, in one place so it can be checked in one place:

* Rows are ordered by `row_id`, which is a hash of the design identity. That
  ordering is a property of the design, not of the file it was written to, the
  device it runs on, or the order the caller happened to iterate.
* Batches are contiguous chunks of that ordering, so batch composition is fixed
  before any device is chosen.
* Sharding across the two cards partitions WHOLE BATCHES round-robin. A row
  therefore sits in the same batch at the same offset whether the design runs on
  one card or two, and the merged output is identical either way.
"""
from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from crossmodel import contract, schema, seeds
from crossmodel.adapters.base import (Generation, GenerationConfig,
                                      ModelAdapter)
from crossmodel.contract import ReasoningMode
from crossmodel.schema import build_row


#: The two background members that raise the load from 3 to 5, verbatim from the
#: repository's own k=5 reasoning run (`stageS27_reasoning_k5_*/config.json`).
#: Held in a fixed position so raising the load does not also permute the
#: instructions the design is studying. No new difficulty is invented.
K5_FIXED_TAIL = ("U_LEX_FORBID3", "U_NUM_MAXINT")


def build_design(state: Any, stage: str, load: int = contract.LOAD) -> list[Any]:
    """The frozen 2 x 2 x 20 x 2 slice, from the repository's own builder."""
    from dci_exploratory import design as design_module

    slice_ = contract.resolve_slice(state)
    fixed_tail = () if load == contract.LOAD else K5_FIXED_TAIL
    rows = design_module.build_permutation_design(
        target=slice_.target,
        focals=[slice_.focal, slice_.reference],
        variants=list(slice_.backgrounds),
        tasks=[dict(task) for task in slice_.tasks],
        replicates=slice_.replicates,
        base_seed=contract.MASTER_SEED,
        stage=stage,
        paraphrase_id=slice_.paraphrase_id,
        permutations=(slice_.order,),
        fixed_tail=fixed_tail)
    observed = {r.load for r in rows}
    if observed != {contract.LOAD + len(fixed_tail)}:
        raise ValueError(f"rows report load {sorted(observed)}, expected "
                         f"{contract.LOAD + len(fixed_tail)}")
    if len(rows) != slice_.expected_rows:
        raise ValueError(
            f"design produced {len(rows)} rows, expected "
            f"{slice_.expected_rows}; the contract and the builder disagree")
    return order_rows(rows)


def order_rows(rows: Iterable[Any]) -> list[Any]:
    """The canonical execution order: by row_id, a hash of design identity."""
    return sorted(rows, key=lambda r: r.row_id)


def batches(rows: Sequence[Any], batch_size: int) -> list[list[Any]]:
    return [list(rows[i:i + batch_size])
            for i in range(0, len(rows), batch_size)]


def shard_batches(all_batches: Sequence[list[Any]], shard: int, of: int
                  ) -> list[list[Any]]:
    """Round-robin whole batches, so batch composition never depends on shard."""
    if of <= 0 or not (0 <= shard < of):
        raise ValueError(f"invalid shard {shard} of {of}")
    return [batch for index, batch in enumerate(all_batches)
            if index % of == shard]


@dataclass
class RunPlan:
    """Everything decided before generation starts, recorded before it starts."""

    run_id: str
    model_id: str
    model_revision: str
    reasoning_mode: str
    reasoning_control: str
    engineering_ceiling: Optional[int]
    envelope: Optional[dict]
    batch_size: int
    shard: int
    of: int
    expected_rows: int
    device_map: str

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def reasoning_control_for(adapter: ModelAdapter, mode: str) -> str:
    """A short, checkable description of HOW the mode was requested.

    Recorded per row because "natural reasoning" means different mechanisms on
    different checkpoints, and a reader comparing two models is entitled to see
    which lever was pulled rather than trust that they were equivalent.
    """
    kwargs = adapter.template_kwargs(mode) if hasattr(
        adapter, "template_kwargs") else {}
    if kwargs:
        rendered = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"chat_template({rendered})"
    return "chat_template(no reasoning argument; checkpoint always reasons)"


def run_slice(adapter: ModelAdapter, design_rows: Sequence[Any],
              state: Any, reasoning_mode: str, run_id: str,
              batch_size: int = 8, shard: int = 0, of: int = 1,
              master_seed: int = contract.MASTER_SEED,
              progress: bool = True,
              generation_ceiling: Optional[int] = None
              ) -> tuple[list[dict], RunPlan]:
    """Generate the slice for one checkpoint in one reasoning mode.

    `generation_ceiling` caps total tokens per request, reasoning and answer
    together. Passing it changes the RECORDED condition to
    THINKING_ENABLED_BOUNDED, because a ceiling a request can actually reach is
    a different experimental condition from one that never binds, and a run must
    not be able to quietly acquire a binding limit while still calling itself
    natural reasoning. The MECHANISM is unchanged — the adapter is still asked
    for `reasoning_mode` and still renders the same template.
    """
    adapter.require_mode(reasoning_mode)
    metadata = adapter.execution_metadata()
    system_message = state.SYSTEM_MESSAGE

    ordered = order_rows(design_rows)
    seeds.assert_seed_regime(ordered, master_seed)

    rendered = {
        row.row_id: adapter.render_prompt(
            [{"role": "system", "content": system_message},
             {"role": "user", "content": row.user_prompt}], reasoning_mode)
        for row in ordered}

    envelope = None
    ceiling = 0
    if reasoning_mode != ReasoningMode.NO_THINKING:
        envelope = adapter.natural_reasoning_ceiling(
            list(rendered.values()), contract.ANSWER_TOKENS)
        ceiling = envelope["derived_ceiling"]

    recorded_mode = reasoning_mode
    if generation_ceiling and reasoning_mode != ReasoningMode.NO_THINKING:
        bounded = generation_ceiling - contract.ANSWER_TOKENS
        if bounded <= 0:
            raise ValueError(f"generation ceiling {generation_ceiling} leaves "
                             "no room for reasoning")
        envelope = dict(envelope or {}, envelope_ceiling=ceiling,
                        generation_ceiling=generation_ceiling,
                        derived_ceiling=bounded)
        ceiling = bounded
        recorded_mode = ReasoningMode.THINKING_ENABLED_BOUNDED

    config = GenerationConfig(
        reasoning_mode=reasoning_mode,
        max_answer_tokens=contract.ANSWER_TOKENS,
        temperature=contract.TEMPERATURE, top_p=contract.TOP_P,
        top_k=contract.TOP_K, max_reasoning_tokens=ceiling)
    # What the adapter is asked for vs. what the row says was run. They differ
    # only in the label, and only when a binding ceiling was imposed.
    record_config = GenerationConfig(
        reasoning_mode=recorded_mode,
        max_answer_tokens=contract.ANSWER_TOKENS,
        temperature=contract.TEMPERATURE, top_p=contract.TOP_P,
        top_k=contract.TOP_K, max_reasoning_tokens=ceiling)

    all_batches = batches(ordered, batch_size)
    mine = shard_batches(all_batches, shard, of)
    expected = sum(len(batch) for batch in mine)

    plan = RunPlan(
        run_id=run_id, model_id=metadata["model_id"],
        model_revision=metadata["model_revision"],
        reasoning_mode=recorded_mode,
        reasoning_control=reasoning_control_for(adapter, reasoning_mode),
        engineering_ceiling=config.engineering_ceiling, envelope=envelope,
        batch_size=batch_size, shard=shard, of=of, expected_rows=expected,
        device_map=metadata["device_configuration"])

    control = plan.reasoning_control
    records: list[dict] = []
    started = time.perf_counter()
    for index, batch in enumerate(mine):
        prompts = [rendered[row.row_id] for row in batch]
        pairs = [(seeds.seed_for_row(row, master_seed, seeds.REASONING_PHASE),
                  seeds.seed_for_row(row, master_seed, seeds.ANSWER_PHASE))
                 for row in batch]
        generations = _generate_with_recovery(adapter, prompts, pairs, config,
                                              index)

        for row, generation, (seed_r, _) in zip(batch, generations, pairs):
            record = build_row(
                run_id=run_id, design_row=row, generation=generation,
                adapter_metadata=metadata, config=record_config,
                reasoning_control=control, scientific_seed=seed_r)
            record["not_generated"] = False
            record["not_generated_reason"] = ""
            record["generation_ceiling"] = (generation_ceiling
                                            or ceiling + contract.ANSWER_TOKENS)
            record["final_answer_status"] = schema.final_answer_status(record)
            records.append(record)

        if progress:
            done = len(records)
            rate = done / max(time.perf_counter() - started, 1e-6)
            print(f"  {done}/{expected} rows  ({rate * 60:.1f} rows/min)",
                  flush=True)

    if len(records) != expected:
        raise RuntimeError(
            f"wrote {len(records)} rows, expected {expected}")
    return records, plan


def _is_oom(error: BaseException) -> bool:
    text = f"{type(error).__name__}: {error}".lower()
    return ("out of memory" in text or "outofmemory" in text
            or "hip error" in text and "memory" in text)


def _generate_with_recovery(adapter: ModelAdapter, prompts: Sequence[str],
                            pairs: Sequence[tuple[int, int]],
                            config: GenerationConfig, index: int
                            ) -> list[Generation]:
    """Generate a batch, halving it on OOM rather than losing the cells.

    Reasoning length is chosen by the model, so a batch's peak KV footprint is
    not knowable in advance — Qwen3.5's natural traces run an order of magnitude
    longer than the checkpoint this study was built on. Splitting on OOM keeps
    the row set complete. It does change batch composition for the affected
    rows, and therefore their realised sample, so the split is announced rather
    than silent.

    A batch that fails for any OTHER reason is recorded as a technical failure
    per row and never dropped: a silently short output file is indistinguishable
    from a design that never had those cells.
    """
    try:
        return adapter.generate(prompts, pairs, config)
    except Exception as error:                          # noqa: BLE001
        if _is_oom(error) and len(prompts) > 1:
            import gc

            import torch

            half = len(prompts) // 2
            print(f"  batch {index}: out of memory at size {len(prompts)}, "
                  f"splitting into {half} + {len(prompts) - half} "
                  "(batch composition changes for these rows)", flush=True)
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return (_generate_with_recovery(adapter, prompts[:half],
                                            pairs[:half], config, index)
                    + _generate_with_recovery(adapter, prompts[half:],
                                              pairs[half:], config, index))

        detail = f"{type(error).__name__}: {error}"
        print(f"  batch {index} FAILED — {detail[:200]}")
        traceback.print_exc()
        return [Generation(
            prompt=prompt, raw_generation="", reasoning_text="",
            final_answer="", reasoning_tokens=0, final_answer_tokens=0,
            finish_reason="error", natural_reasoning_closed=False,
            reasoning_cap_hit=False, answer_truncated=False,
            technical_failure=True, technical_failure_reason=detail[:500])
            for prompt in prompts]


def write_rows(records: Sequence[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def merge_shards(paths: Sequence[Path], expected_rows: Optional[int] = None
                 ) -> list[dict]:
    """Merge shard files by stable row id, refusing overlaps and gaps."""
    seen: dict[str, dict] = {}
    duplicates: list[str] = []
    for path in paths:
        for line in Path(path).open():
            record = json.loads(line)
            key = f"{record['row_id']}|{record['reasoning_mode']}"
            if key in seen:
                duplicates.append(key)
            seen[key] = record
    if duplicates:
        raise ValueError(
            f"shards overlap on {len(duplicates)} row(s): {duplicates[:5]}")
    merged = sorted(seen.values(), key=lambda r: r["row_id"])
    if expected_rows is not None and len(merged) != expected_rows:
        raise ValueError(
            f"merged {len(merged)} rows, expected {expected_rows}")
    return merged
