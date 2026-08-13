"""Stage 132 — migrated from notebook cell 132.py (model_backend_binding).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/132.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell


"""Backend binding. The HF loading/free code that lived in this cell moved
verbatim into dci.inference.hf_transformers (see migration ledger P6); this
stage now constructs the backend the execution config selects and preserves the
cell's public names (`load_model`, `free_model`, `tokenizer`, `model`)."""
from dci.inference import make_backend

S.BACKEND = make_backend()
S.load_model = S.BACKEND.load_model
S.free_model = S.BACKEND.free_model
S.tokenizer = None
S.model = None

print(f"Model loading is deferred and gated on Gate 0 and Gate M. Profile "
      f"{S.CFG.model_profile} pins {S.CFG.model_id} at {S.CFG.model_revision[:12]}. "
      f"backend={S.BACKEND.name}")
