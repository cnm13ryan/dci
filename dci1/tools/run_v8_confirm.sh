#!/usr/bin/env bash
# Drive one DCI-1 v8 CONFIRMATORY replication through its seven stages, in
# order, on one card, stopping where the lifecycle stops.
#
#     tools/run_v8_confirm.sh <model_key> <device> <root> <log_dir> [through_stage]
#
# Every stage is `python -m dci1v8dev.confirm.cli run --stage <next> --model
# <key> --root <root>`; the CLI refuses out-of-order, repeated or post-terminal
# attempts itself. CONFIRM_REGISTERED needs the pilot roots bound once per
# root (`--pilot-root MODEL=DIR`, read from $V8_PILOT_ROOTS as a space-separated
# list). Generating stages run under the per-card driver lock the pilot
# driver uses. [through_stage] stops after that stage (e.g. MEMBERSHIP, so
# the membership lock can be written before FROZEN).
set -u
MODEL="$1"; DEVICE="$2"; ROOT="$3"; LOGDIR="$4"; THROUGH="${5:-}"
cd "$(dirname "$0")/.."
PY=.venv/bin/python
ENV_CPU="rocm7.2/vllm0.15.1"
ENV_GPU="rocm7.2/vllm0.15.1/gpu${DEVICE}"
LOCKDIR="evidence/.gpu-locks"; mkdir -p "$LOCKDIR"
DLOCK="$LOCKDIR/gpu${DEVICE}.driver.lock"
GPU_STAGES=" $($PY -c 'from dci1v8dev.confirm import cli; print(" ".join(cli.generating_stages()))') "
mkdir -p "$LOGDIR"
DRV="$LOGDIR/${MODEL}.confirm.driver.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [v8-confirm $MODEL gpu$DEVICE] $*" | tee -a "$DRV"; }
PILOT_ARGS=()
for kv in ${V8_PILOT_ROOTS:-}; do PILOT_ARGS+=(--pilot-root "$kv"); done
attempts=0
while true; do
  STATUS=$($PY -m dci1v8dev.confirm.cli status --model "$MODEL" --root "$ROOT" 2>&1)
  NEXT=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["next_stage"] or "")' 2>/dev/null)
  TERM=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["terminal_status"] or "")' 2>/dev/null)
  REACHED=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["stage_reached"] or "")' 2>/dev/null)
  if [ -z "$NEXT" ] && [ -z "$REACHED" ] && [ -z "$TERM" ]; then log "status failed: $STATUS"; exit 1; fi
  if [ -n "$TERM" ]; then log "TERMINAL $TERM at $REACHED; stopping"; exit 0; fi
  if [ -z "$NEXT" ]; then log "COMPLETE: reached $REACHED"; exit 0; fi
  if [ -n "$THROUGH" ] && [ "$REACHED" = "$THROUGH" ]; then log "reached $THROUGH; stopping as asked"; exit 0; fi
  ARGS=(run --stage "$NEXT" --model "$MODEL" --root "$ROOT")
  [ "$NEXT" = "CONFIRM_REGISTERED" ] && ARGS+=("${PILOT_ARGS[@]}")
  OUT="$LOGDIR/${MODEL}.${NEXT}.$(date -u +%Y%m%dT%H%M%SZ).out"
  if [[ "$GPU_STAGES" == *" $NEXT "* ]]; then
    ARGS+=(--device "$DEVICE" --environment "$ENV_GPU")
    log "WAIT card $DEVICE for $NEXT"
    flock "$DLOCK" bash -c '
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [v8-confirm $1 gpu$2] START $3 -> $4" | tee -a "$5"
      shift 5; exec "$@"' _ "$MODEL" "$DEVICE" "$NEXT" "$OUT" "$DRV" \
      $PY -m dci1v8dev.confirm.cli "${ARGS[@]}" > "$OUT" 2>&1
    code=$?
  else
    ARGS+=(--environment "$ENV_CPU")
    log "START $NEXT -> $OUT"
    $PY -m dci1v8dev.confirm.cli "${ARGS[@]}" > "$OUT" 2>&1
    code=$?
  fi
  log "EXIT $NEXT code=$code"
  if [ $code -eq 0 ]; then attempts=0; continue; fi
  if grep -q '"message": "GPU lock' "$OUT"; then log "card busy; retry in 60s"; sleep 60; continue; fi
  if $PY -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if "TerminalStatus" in d.get("error","") else 1)' "$OUT" 2>/dev/null; then
    tail -c 1500 "$OUT" | tee -a "$DRV"; continue
  fi
  attempts=$((attempts+1)); tail -c 2500 "$OUT" | tee -a "$DRV"
  if [ $attempts -ge 2 ]; then log "STALLED at $NEXT; needs a person"; exit 1; fi
  log "retrying $NEXT after 120s"; sleep 120
done
