#!/bin/bash
# E1 cap-search grid (PREREGISTERED.md). Both 12288-max-len servers
# must be up (8555 GPU0, 8556 GPU1). High effort (slow) on GPU0;
# low+medium on GPU1. Each run stays wholly on one server.
set -eu
cd "$(dirname "$0")/../.."
I=.venv/bin/inspect
DS=dataset/exp1_cap.jsonl

run() { # effort cap port
  OPENAI_API_KEY=forensics $I eval task.py@forensics \
    -T effort="$1" -T dataset_path=$DS -T max_tokens="$2" \
    --model openai/gpt-oss-20b \
    --model-base-url "http://127.0.0.1:$3/v1" \
    --log-dir "logs_exp/exp1/$1_$2" --max-connections 4 \
    --display plain
}

( run high 4096 8555 && run high 8192 8555 && run high 2048 8555 ) &
( run low 4096 8556 && run low 8192 8556 && \
  run medium 4096 8556 && run medium 8192 8556 ) &
wait
echo "E1 grid complete"
