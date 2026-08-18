#!/bin/bash
# E2 repeat-stability triple: THREE identical back-to-back runs of the
# 120-sample repeat subset at one effort and its safe cap C*(effort).
#
#   bash experiments/exp2_repeat/run.sh <effort> <cap> <port>
set -eu
cd "$(dirname "$0")/../.."
EFFORT=$1; CAP=$2; PORT=$3
for i in 1 2 3; do
  OPENAI_API_KEY=forensics .venv/bin/inspect eval task.py@forensics \
    -T effort="$EFFORT" -T dataset_path=dataset/exp2_repeat.jsonl \
    -T max_tokens="$CAP" \
    --model openai/gpt-oss-20b \
    --model-base-url "http://127.0.0.1:$PORT/v1" \
    --log-dir "logs_exp/exp2/${EFFORT}/run$i" --max-connections 4 \
    --display plain
done
echo "E2 triple complete: $EFFORT@$CAP"
