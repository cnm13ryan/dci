#!/usr/bin/env bash
# Gate 2 (§12.3, §12.4) for all four replications across both RX 7900 XTXs.
#
# The only thing this script decides is *where* and *when* each replication
# runs. It passes no scientific argument: `run_v4r4.py gate2` takes `--model`
# and `--device` and reads everything else --- the calibration cells, M_CAL,
# the 96 solo topics, the decoding plan, the completion cap --- from the signed
# regime record and the registered constants. Nothing here can change what is
# measured.
#
# Two lanes, one per card. `dci1v4.generation.backend` takes an exclusive
# non-blocking flock per device and refuses immediately if the card is busy, so
# the lanes must serialise within themselves; they are independent of each
# other. `HIP_VISIBLE_DEVICES` is set by the backend from `--device`, and
# inherited visibility variables are cleared first.
#
# Failure isolation: a replication that fails does not stop its lane or the
# other lane. Per-model outcomes are independent under the protocol
# (`DECISIONS_V4R4.md` E6), and the stage machine is per-replication, so a
# terminal outcome on one model is that model's result. Exit codes are
# collected and printed at the end; the script's own status is the number of
# replications that did not return 0.
#
#     ./tools/run_v4r4_gate2_dual_gpu.sh
#
# Logs: dci1/reports/dci1v4r4/gate2_logs/<model>.log, plus <model>.status.
set -u

DCI1="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$DCI1/.venv/bin/python"
LOGS="$DCI1/reports/dci1v4r4/gate2_logs"
mkdir -p "$LOGS"

# One gemma and one qwen per card, so neither lane carries both large models.
LANE0=(gemma-3n-e2b-it qwen3-4b)
LANE1=(gemma-3n-e4b-it qwen3-4b-instruct-2507)

run_lane() {
  local device="$1"; shift
  for model in "$@"; do
    echo "[gpu${device}] $(date -Is) start ${model}" >&2
    "$PY" "$DCI1/tools/run_v4r4.py" gate2 --model "$model" --device "$device" \
      > "$LOGS/${model}.log" 2>&1
    local status=$?
    echo "$status" > "$LOGS/${model}.status"
    echo "[gpu${device}] $(date -Is) done ${model} exit=${status}" >&2
  done
}

run_lane 0 "${LANE0[@]}" &
PID0=$!
run_lane 1 "${LANE1[@]}" &
PID1=$!
wait $PID0 $PID1

failed=0
for model in "${LANE0[@]}" "${LANE1[@]}"; do
  status="$(cat "$LOGS/${model}.status" 2>/dev/null || echo missing)"
  printf '%-24s exit=%s\n' "$model" "$status"
  [ "$status" = "0" ] || failed=$((failed + 1))
done
echo "replications that did not return 0: ${failed}"
exit "$failed"
