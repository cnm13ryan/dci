"""Replicate every signed v4r4 stage record into the durable root.

`evidence/` is gitignored by this repository's design, so the durable mirror is
the only second copy the study has of a signed record. `_run_stage` mirrors as
part of every gate, but §18 stage 1's qualification record is written by its
own command, which never mirrored --- so four signed records existed in exactly
one place, and the integrity checker's fail-open clause did not notice.

This replicates what is already there and nothing else. `store.replicate`
copies only files whose bytes differ, verifies every byte it writes, and
`store.assert_replicated` refuses to return unless the two trees agree; a
record that already mirrors is not touched, so running this is idempotent and
cannot modify evidence.

    ./.venv/bin/python tools/v4r4_mirror_records.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.models.registry import MODEL_KEYS                    # noqa: E402
from dci1v4r4.engine.context import registered_context           # noqa: E402
from dci1v4r4.engine.paths import model_tree                     # noqa: E402
from dci1v4r4.protocol import constants as C                     # noqa: E402
from dci1v4r4.run.regime_screen import mirror_records            # noqa: E402

#: Every registered stage. The literal used to name the first four,
#: which was the study's furthest stage when this tool was written;
#: `C.STAGE_SEQUENCE` is the list that does not go stale.
STAGES = C.STAGE_SEQUENCE


def main() -> int:
    context = registered_context()
    mirrored: dict[str, list[str]] = {}
    for model_key in sorted(MODEL_KEYS):
        tree = model_tree(context, model_key)
        done = []
        for stage in STAGES:
            if not tree.stage_record(stage).exists():
                continue
            mirror_records(model_key, stage)        # verifies every byte
            done.append(stage)
        mirrored[model_key] = done
    print(json.dumps({"mirrored": mirrored,
                      "note": "idempotent; a record that already matched was "
                              "not rewritten"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
