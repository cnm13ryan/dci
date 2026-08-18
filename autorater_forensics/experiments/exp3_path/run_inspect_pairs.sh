#!/bin/bash
# E3.1 — serialized vs concurrent Inspect runs on the 61 controls,
# cap 2048, same server. Efforts low and high (the flip-affected ones).
#
#   bash experiments/exp3_path/run_inspect_pairs.sh <port>
set -eu
cd "$(dirname "$0")/../.."
PORT=${1:-8556}
run() { # effort connections
  OPENAI_API_KEY=forensics .venv/bin/inspect eval task.py@forensics \
    -T effort="$1" -T dataset_path=dataset/exp3_controls.jsonl \
    -T max_tokens=2048 \
    --model openai/gpt-oss-20b \
    --model-base-url "http://127.0.0.1:$PORT/v1" \
    --log-dir "logs_exp/exp3/$1_conc$2" --max-connections "$2" \
    --display plain
}
run low 1
run low 4
run high 1
run high 4
echo "E3.1 pairs complete"
