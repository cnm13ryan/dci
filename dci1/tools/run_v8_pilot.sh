#!/usr/bin/env bash
# Drive one DCI-1 v8 PILOT replication through its nine stages, in order, on
# one card, stopping only where the pilot lifecycle stops.
#
#     tools/run_v8_pilot.sh <model_key> <device> <root> <log_dir> [after_pids]
#
# Every stage is `python -m dci1v8dev.run.cli run --stage <next> --model <key>
# --root <root>` (pilot namespace: the pinned backend, the real model, every
# rule); the CLI refuses out-of-order, repeated or post-terminal attempts
# itself. This script asks `status` for the next stage, forwards --device to
# the stages whose runner takes one, and stops when the CLI reports no next
# stage (PILOT_REPORT written), a terminal report exists, or a stage fails
# twice in a row (an apparatus fault for a person to look at).
#
# <root> must lie outside every other study's tree (the CLI refuses
# otherwise); the convention is dci1/evidence/dci1v8-pilot. A generating
# stage runs under the same per-card driver lock the v7 driver uses
# (evidence/.gpu-locks/gpu<N>.driver.lock), so a v8 lane never interleaves
# with a v7 lane on one card. Nothing here reads an outcome, chooses a stage,
# or passes any argument that changes what is measured.
#
# DCI1_V7_CPU_WORKERS=<n> sizes the scoring pools (engine/parallel; the v8
# layer reuses v7's engine and its variable).
set -u
MODEL="$1"; DEVICE="$2"; ROOT="$3"; LOGDIR="$4"; AFTER="${5:-}"
cd "$(dirname "$0")/.."                      # dci1/
PY=.venv/bin/python
ENV_CPU="rocm7.2/vllm0.15.1"
ENV_GPU="rocm7.2/vllm0.15.1/gpu${DEVICE}"
LOCKDIR="evidence/.gpu-locks"; mkdir -p "$LOCKDIR"
DLOCK="$LOCKDIR/gpu${DEVICE}.driver.lock"
GPU_STAGES=" $($PY -c 'from dci1v8dev.run import cli; print(" ".join(cli.generating_stages()))') "
mkdir -p "$LOGDIR"
DRV="$LOGDIR/${MODEL}.driver.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [v8 $MODEL gpu$DEVICE] $*" | tee -a "$DRV"; }
log "V8 PILOT: --root $ROOT (study id dci1v8; a development candidate, not a registered study)"

for pid in ${AFTER//,/ }; do
  [ -z "$pid" ] && continue
  while kill -0 "$pid" 2>/dev/null; do sleep 15; done
  log "predecessor process $pid has exited"
done

# The namespace every stage runs in: "pilot" (default) or "topic-replicate"
# (the methodology-validation replicate, DCI1_V8_NAMESPACE=topic-replicate).
NAMESPACE="${DCI1_V8_NAMESPACE:-pilot}"
log "namespace $NAMESPACE"

attempts=0
while true; do
  STATUS=$($PY -m dci1v8dev.run.cli status --model "$MODEL" --root "$ROOT" --namespace "$NAMESPACE" 2>&1)
  NEXT=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["next_stage"] or "")' 2>/dev/null)
  TERM=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["terminal_status"] or "")' 2>/dev/null)
  REACHED=$(printf '%s' "$STATUS" | $PY -c 'import json,sys; d=json.load(sys.stdin); print(d["stage_reached"] or "")' 2>/dev/null)
  if [ -z "$NEXT" ] && [ -z "$REACHED" ] && [ -z "$TERM" ]; then log "status failed: $STATUS"; exit 1; fi
  if [ -n "$TERM" ]; then log "TERMINAL $TERM at $REACHED; stopping"; exit 0; fi
  if [ -z "$NEXT" ]; then log "COMPLETE: reached $REACHED, no next stage"; exit 0; fi
  ARGS=(run --stage "$NEXT" --model "$MODEL" --root "$ROOT" --namespace "$NAMESPACE")
  OUT="$LOGDIR/${MODEL}.${NEXT}.$(date -u +%Y%m%dT%H%M%SZ).out"
  if [[ "$GPU_STAGES" == *" $NEXT "* ]]; then
    ARGS+=(--device "$DEVICE" --environment "$ENV_GPU")
    log "WAIT card $DEVICE for $NEXT"
    flock "$DLOCK" bash -c '
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [v8 $1 gpu$2] START $3 (attempt $4) -> $5" | tee -a "$6"
      shift 6; exec "$@"' _ "$MODEL" "$DEVICE" "$NEXT" "$((attempts+1))" "$OUT" "$DRV" \
      $PY -m dci1v8dev.run.cli "${ARGS[@]}" > "$OUT" 2>&1
    code=$?
  else
    ARGS+=(--environment "$ENV_CPU")
    log "START $NEXT (attempt $((attempts+1))) -> $OUT"
    $PY -m dci1v8dev.run.cli "${ARGS[@]}" > "$OUT" 2>&1
    code=$?
  fi
  log "EXIT $NEXT code=$code"
  if [ $code -eq 0 ]; then attempts=0; continue; fi
  if grep -q '"message": "GPU lock' "$OUT"; then
    log "card busy; retrying $NEXT after 60s"; sleep 60; continue
  fi
  if $PY -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if "TerminalStatus" in d.get("error","") else 1)' "$OUT" 2>/dev/null; then
    tail -c 1500 "$OUT" | tee -a "$DRV"; continue
  fi
  attempts=$((attempts+1))
  tail -c 2500 "$OUT" | tee -a "$DRV"
  if [ $attempts -ge 2 ]; then log "STALLED at $NEXT after $attempts attempts; needs a person"; exit 1; fi
  log "retrying $NEXT after 120s"; sleep 120
done
