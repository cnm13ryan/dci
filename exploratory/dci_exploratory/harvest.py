"""Read-only adapter onto the validated v15/v19 definitions.

The stage modules in `dci.pipeline.stages` execute their bodies at import, the
way the notebook cells they were extracted from did. That is how the repository
builds `S.CONSTRAINTS`, the certified wordings, the verifier dispatch, the task
bank, the model-free response bank and the coupling table. This module runs that
prelude ONCE, in dry-run, and hands the results back.

The point is that this study invents no scientific content. Re-typing a wording,
a parameter or a verifier here would silently create a different experiment that
merely looked like the protocol's.

Nothing here loads a model: stages c112..c212 are all definition and audit work,
`dry_run_mode` is forced on, and the scratch data root exists only so the storage
stage has somewhere to write its journal.
"""
from __future__ import annotations

import contextlib
import importlib
import io
import os
from pathlib import Path
from typing import Any, Callable, Optional

# Stage prefix order, truncated at c212: that is the last stage that defines
# anything this study reuses (the reference machinery). Everything after it runs
# gates, spends inference budget, or both.
_STAGES = (
    "c112_configuration_and_statuses",
    "c122_runtime_provenance_gates",
    "c126_durable_storage",
    "c132_model_backend_binding",
    "c142_constraints_and_tasks",
    "c152_verifiers",
    "c162_coupling_and_response_bank",
    "c172_paraphrases_and_audit",
    "c182_design_builders",
    "c192_oracle_and_generation",
    "c202_statistics",
    "c212_reference_machinery",
)

_STATE: Optional[Any] = None
_COMPOSE_PROMPT: Optional[Callable[..., str]] = None
_STAGE_LOG: str = ""


def load(scratch_root: str | Path | None = None, quiet: bool = True):
    """Import the stage prelude once and return `dci.pipeline.state`.

    Idempotent: repeated calls return the same module object, because the stage
    modules are already in `sys.modules` and their bodies do not re-run.
    """
    global _STATE, _COMPOSE_PROMPT, _STAGE_LOG
    if _STATE is not None:
        return _STATE

    import matplotlib
    matplotlib.use("Agg")             # the stages import pyplot at module scope

    root = Path(scratch_root or os.environ.get(
        "DCI_EXPLORATORY_SCRATCH", Path.home() / ".cache" / "dci-exploratory-harvest"))
    root.mkdir(parents=True, exist_ok=True)

    from dci.config.loader import ACTIVE
    # dev_fast + dry_run is the cheapest configuration that still constructs
    # every definition. It pins NO model and loads NO weights; the model this
    # study actually uses is chosen in `config.py` and never comes from here.
    ACTIVE.model_profile = "dev_fast"
    ACTIVE.run_mode = "smoke"
    ACTIVE.dry_run_mode = True
    ACTIVE.use_google_drive = False
    ACTIVE.data_root = str(root)

    buffer = io.StringIO()
    ctx = contextlib.redirect_stdout(buffer) if quiet else contextlib.nullcontext()
    with ctx:
        for name in _STAGES:
            importlib.import_module(f"dci.pipeline.stages.{name}")
    _STAGE_LOG = buffer.getvalue()

    from dci.pipeline import state as S
    from dci.pipeline.stages.c182_design_builders import compose_prompt
    _COMPOSE_PROMPT = compose_prompt
    _STATE = S
    return S


def compose_prompt(topic: str, ordered_ids: list[str], paraphrase_id: int) -> str:
    """The protocol's exact prompt assembly, from stage c182."""
    if _COMPOSE_PROMPT is None:
        load()
    assert _COMPOSE_PROMPT is not None
    return _COMPOSE_PROMPT(topic, ordered_ids, paraphrase_id)


def stage_log() -> str:
    """Whatever the stage prelude printed, kept for the run record."""
    return _STAGE_LOG


def provenance() -> dict[str, Any]:
    """Identity of the reused definitions, for the run record.

    These hashes are the repository's own: if a wording, the response bank or a
    constraint set ever changes, the recorded hash changes with it and an old run
    directory stops claiming to describe the new definitions.
    """
    S = load()
    from dci.provenance.hashes import sha, sha_text

    return {
        "stages_imported": list(_STAGES),
        "n_constraints": len(S.CONSTRAINTS),
        "n_tasks": int(len(S.TASKS)),
        "response_bank_sha256": getattr(S, "RESPONSE_BANK_SHA256", None),
        "synthetic_corpus_size": len(getattr(S, "SYNTHETIC_CORPUS", [])),
        "system_message": S.SYSTEM_MESSAGE,
        "system_message_sha256": sha_text(S.SYSTEM_MESSAGE),
        "instructions_sha256": sha({
            cid: list(wordings) for cid, wordings in sorted(S.INSTRUCTIONS.items())}),
        "protocol_config_sha256": getattr(S, "PROTOCOL_SHA256", None),
        "exact_sentence_count": int(S.CFG.exact_sentence_count),
        "minimum_sentence_words": int(S.CFG.minimum_sentence_words),
        # Decoding values are READ from the frozen protocol config rather than
        # re-declared, so this study cannot silently decode differently from the
        # pipeline it is probing.
        "cfg_decoding": {
            "max_new_tokens": int(S.CFG.max_new_tokens),
            "temperature": float(S.CFG.temperature),
            "top_p": float(S.CFG.top_p),
            "top_k": int(S.CFG.top_k),
            "do_sample": bool(S.CFG.do_sample),
        },
    }
