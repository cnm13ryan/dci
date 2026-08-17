"""Backend-environment probe: is the chat template's thinking switch live or
inert for a checkpoint? Runs under the PINNED backend interpreter with
``cwd = exploratory/`` so it uses the shared backend's own tokenizer path.

    <backend python> template_probe_script.py <model_id> <revision> \
        <trust_remote_code:0|1>

Prints one JSON object:
  renders_identical_plain_vs_true   plain render == enable_thinking=True
  renders_identical_true_vs_false   enable_thinking=True == False
  rendered_tail_plain/true/false    last 200 chars of each render
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    model_id, revision, trust = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
    from vllm_backend import engine
    from vllm_backend.contract import GenerationRequest
    from vllm_backend.registry import ModelCard

    card = ModelCard(model_id=model_id, family="probe",
                     trust_remote_code=trust)
    tokenizer = engine.load_tokenizer(card, revision)
    request = GenerationRequest(row_id="probe",
                                user_prompt="Name one colour.\n\nAnswer:")
    plain = engine.render_prompt(tokenizer, request, {})
    with_true = engine.render_prompt(tokenizer, request,
                                     {"enable_thinking": True})
    with_false = engine.render_prompt(tokenizer, request,
                                      {"enable_thinking": False})
    print(json.dumps({
        "model_id": model_id,
        "revision": revision,
        "tokenizer_acquisition": getattr(tokenizer, "_dci_acquisition", ""),
        "renders_identical_plain_vs_true": plain == with_true,
        "renders_identical_true_vs_false": with_true == with_false,
        "rendered_tail_plain": plain[-200:],
        "rendered_tail_true": with_true[-200:],
        "rendered_tail_false": with_false[-200:],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
