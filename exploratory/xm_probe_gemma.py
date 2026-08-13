"""One-off probe: what does Gemma 4 actually emit on the real DCI prompts?

The smoke set showed content BEFORE the thought channel, which is the opposite
order from Qwen and Kimi and does not fit a reasoning-then-answer splice. Trivial
prompts and the study's own "do not explain your planning process" system message
could both explain it, so this asks the question on the prompts that matter, with
NO splice: one unbroken generation, printed raw.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch

from crossmodel import contract
from crossmodel.adapters import get_adapter
from dci_exploratory import extensions, harvest

extensions.register()
STATE = harvest.load()

MODEL = sys.argv[1] if len(sys.argv) > 1 else "google/gemma-4-E4B-it"
MAX_NEW = int(sys.argv[2]) if len(sys.argv) > 2 else 3000

adapter = get_adapter(MODEL, device_map="cuda:0")
adapter.load()
tokenizer = adapter._require_tokenizer()
model = adapter._require_model()

tasks = contract.resolve_tasks(STATE)[:3]
for task in tasks:
    for background in contract.BACKGROUNDS:
        ordered = [contract.FOCAL, contract.TARGET, background]
        user = harvest.compose_prompt(task["topic"], ordered,
                                      contract.PARAPHRASE_ID)
        for mode in ("NATURAL_REASONING", "NO_THINKING"):
            prompt = adapter.render_prompt(
                [{"role": "system", "content": STATE.SYSTEM_MESSAGE},
                 {"role": "user", "content": user}], mode)
            encoded = tokenizer(prompt, return_tensors="pt",
                                add_special_tokens=False).to(model.device)
            torch.manual_seed(4242)
            with torch.no_grad():
                out = model.generate(**encoded, max_new_tokens=MAX_NEW,
                                     do_sample=True, temperature=0.7,
                                     top_p=0.9, top_k=0,
                                     pad_token_id=tokenizer.pad_token_id)
            text = tokenizer.decode(out[0, encoded["input_ids"].shape[1]:],
                                    skip_special_tokens=False)
            print(f"\n{'=' * 78}\n{task['task_id']} | {background} | {mode}")
            print(f"--- RAW ({out.shape[1] - encoded['input_ids'].shape[1]} tok)")
            print(repr(text))
            sys.stdout.flush()
