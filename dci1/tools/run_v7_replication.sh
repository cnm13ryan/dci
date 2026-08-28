#!/usr/bin/env bash
# Drive one DCI-1 v7 replication through §18's stage sequence, in order,
# on one card, stopping only where the registered lifecycle stops.
#
#     tools/run_v7_replication.sh <model_key> <device> <log_dir>
#
# Every stage is `python -m dci1v7.run.cli run --stage <next> --model <key>`,
# which refuses out-of-order, repeated or post-terminal attempts itself; this
# script only asks `status` what the next stage is, forwards `--device` to
# the stages whose runner takes one, and stops when
#   * the CLI reports no next stage (FINAL_REPORT written), or
#   * a terminal report exists (a registered §28 terminal status), or
#   * a stage fails for any other reason twice in a row (an apparatus fault
#     to be looked at by a person; the tree is left exactly where it was).
# A GPU stage waits for the card's flock to be free before it is launched, so
# two replications may share a card; the backend's own non-blocking lock is
# still the arbiter, and a "held by another run" refusal is simply retried.
# Nothing here reads an outcome, chooses a stage, or passes any argument that
# changes what is measured.
set -u
MODEL="$1"; DEVICE="$2"; LOGDIR="$3"
cd "$(dirname "$0")/.."                      # dci1/
PY=.venv/bin/python
ENV_CPU="rocm7.2/vllm0.15.1"
ENV_GPU="rocm7.2/vllm0.15.1/gpu${DEVICE}"
LOCK="evidence/.gpu-locks/gpu${DEVICE}.lock"
GPU_STAGES=" $($PY -c 'from dci1v7.run import cli; print(" ".join(cli.stages_accepting("device")))') "
mkdir -p "$LOGDIR"
DRV="$LOGDIR/${MODEL}.driver.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$MODEL gpu$DEVICE] $*" | tee -a "$DRV"; }

attempts=0
while true; do
  STATUS=$($PY -m dci1v7.run.cli status --model "$MODEL" 2>&1)
  NEXT=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["next_stage"] or "")' 2>/dev/null)
  TERM=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["terminal_status"] or "")' 2>/dev/null)
  REACHED=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["stage_reached"] or "")' 2>/dev/null)
  if [ -n "$TERM" ]; then log "TERMINAL $TERM at $REACHED; stopping"; exit 0; fi
  if [ -z "$NEXT" ]; then log "COMPLETE: reached $REACHED, no next stage"; exit 0; fi
  ARGS=(run --stage "$NEXT" --model "$MODEL")
  if [[ "$GPU_STAGES" == *" $NEXT "* ]]; then
    ARGS+=(--device "$DEVICE" --environment "$ENV_GPU")
    while ! flock -n "$LOCK" true 2>/dev/null; do sleep 30; done
  else
    ARGS+=(--environment "$ENV_CPU")
  fi
  OUT="$LOGDIR/${MODEL}.${NEXT}.$(date -u +%Y%m%dT%H%M%SZ).out"
  log "START $NEXT (attempt $((attempts+1))) -> $OUT"
  $PY -m dci1v7.run.cli "${ARGS[@]}" > "$OUT" 2>&1
  code=$?
  log "EXIT $NEXT code=$code"
  if [ $code -eq 0 ]; then attempts=0; continue; fi
  # The CLI prints {"error": ..., "message": ...} on failure.
  if grep -q '"message": "GPU lock' "$OUT"; then
    log "card busy; retrying $NEXT after 60s"; sleep 60; continue
  fi
  if $PY -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if "TerminalStatus" in d.get("error","") or "terminal" in d.get("message","").lower() else 1)' "$OUT" 2>/dev/null; then
    tail -c 1500 "$OUT" | tee -a "$DRV"; continue   # status re-read at the top of the loop
  fi
  attempts=$((attempts+1))
  tail -c 2500 "$OUT" | tee -a "$DRV"
  if [ $attempts -ge 2 ]; then log "STALLED at $NEXT after $attempts attempts; needs a person"; exit 1; fi
  log "retrying $NEXT after 120s"; sleep 120
done
