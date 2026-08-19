#!/bin/bash
# One fixed TP=1 vLLM OpenAI server for the forensics diagnostic.
# Same pinned environment, checkpoint, and revision as the registered
# judge; GPU selectable (default 0). Diagnostic-only: the production
# Gate 1 serving architecture (offline subprocess seam) is unchanged.
#
#   bash server/launch_server.sh [device] [port] [max-model-len]
#
# max-model-len defaults to 4096 (the original diagnostic runs); the
# E1 cap-search servers use 12288 so 8192-token completions fit.
#
# NOTE: while this server holds a GPU, do not start registered backend
# runs on the same device (the production GpuLock does not see it).
set -eu
DEVICE=${1:-0}
PORT=${2:-8555}
MAXLEN=${3:-4096}
B=/home/cnm13ryan/git/dci/dci1/environments/backend/.venv
LOG=$(dirname "$0")/vllm_server_p${2:-8555}.log

env -u ROCR_VISIBLE_DEVICES -u CUDA_VISIBLE_DEVICES \
    HIP_VISIBLE_DEVICES=$DEVICE \
    VLLM_WORKER_MULTIPROC_METHOD=spawn \
    NCCL_P2P_DISABLE=1 \
    HF_HUB_OFFLINE=1 \
    VLLM_LOGGING_LEVEL=DEBUG \
    "$B/bin/vllm" serve openai/gpt-oss-20b \
    --revision 6cee5e81ee83917806bbde320786a8fb61efebee \
    --served-model-name gpt-oss-20b \
    --dtype bfloat16 \
    --max-model-len "$MAXLEN" \
    --gpu-memory-utilization 0.85 \
    --enforce-eager \
    --no-enable-prefix-caching \
    --seed 20260817 \
    --host 127.0.0.1 --port "$PORT" \
    > "$LOG" 2>&1
