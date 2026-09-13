#!/usr/bin/env bash
# One v4r4 stage, for several replications, across both RX 7900 XTXs.
#
# The generalisation of `run_v4r4_gate2_dual_gpu.sh`, which is kept as the
# record of how Gate 2 was actually run. Gate 4 is the second use of the same
# two-lane shape and the fourth will be the confirmatory generation, so the
# lane assignment is an argument now rather than a literal.
#
# The only things this script decides are *where* and *when* each replication
# runs. It passes no scientific argument: `run_v4r4.py <stage>` takes `--model`
# and `--device` and reads everything else --- the cells, M, the topic set, the
# decoding plan, the completion cap, the slot map --- from signed records and
# registered constants. Nothing here can change what is measured.
#
# `dci1v4.generation.backend` takes an exclusive non-blocking flock per device
# and refuses immediately if the card is busy, so a lane must serialise within
# itself; the two lanes are independent. `HIP_VISIBLE_DEVICES` is set by the
# backend from `--device`, and inherited visibility variables are cleared.
#
# Failure isolation: a replication that fails stops neither its lane nor the
# other lane. Per-model outcomes are independent under the protocol
# (`DECISIONS_V4R4.md` E6) and the stage machine is per-replication, so a
# terminal outcome on one model is that model's result. The script's status is
# the number of replications that did not return 0.
#
#     ./tools/run_v4r4_dual_gpu.sh gate4 \
#         "gemma-3n-e2b-it" \
#         "gemma-3n-e4b-it qwen3-4b qwen3-4b-instruct-2507"
#
# Logs: dci1/reports/dci1v4r4/<stage>_logs/<model>.log, plus <model>.status.
set -u

STAGE="${1:?usage: run_v4r4_dual_gpu.sh <stage> [lane0 models] [lane1 models]}"
LANE0_SPEC="${2:-gemma-3n-e2b-it qwen3-4b}"
LANE1_SPEC="${3:-gemma-3n-e4b-it qwen3-4b-instruct-2507}"

DCI1="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$DCI1/.venv/bin/python"
LOGS="$DCI1/reports/dci1v4r4/${STAGE}_logs"
mkdir -p "$LOGS"

read -r -a LANE0 <<< "$LANE0_SPEC"
read -r -a LANE1 <<< "$LANE1_SPEC"

run_lane() {
  local device="$1"; shift
  for model in "$@"; do
    [ -n "$model" ] || continue
    echo "[gpu${device}] $(date -Is) start ${STAGE} ${model}" >&2
    "$PY" "$DCI1/tools/run_v4r4.py" "$STAGE" --model "$model" \
      --device "$device" > "$LOGS/${model}.log" 2>&1
    local status=$?
    echo "$status" > "$LOGS/${model}.status"
    echo "[gpu${device}] $(date -Is) done ${STAGE} ${model} exit=${status}" >&2
  done
}

run_lane 0 "${LANE0[@]}" &
PID0=$!
run_lane 1 "${LANE1[@]}" &
PID1=$!
wait $PID0 $PID1

failed=0
for model in "${LANE0[@]}" "${LANE1[@]}"; do
  [ -n "$model" ] || continue
  status="$(cat "$LOGS/${model}.status" 2>/dev/null || echo missing)"
  printf '%-24s exit=%s\n' "$model" "$status"
  [ "$status" = "0" ] || failed=$((failed + 1))
done
echo "replications that did not return 0: ${failed}"
exit "$failed"
