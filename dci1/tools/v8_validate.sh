#!/usr/bin/env bash
# The v8 validation sequence: CPU only, no GPU, no evidence root touched.
#
#     tools/v8_validate.sh
#
# Phase A (parallel): the rule-layer and execution-layer unit suite
# (tests_v8dev, not slow) || the merged v7 fast subset (tests_v7 -m "not
# slow": the engine the v8 layer reuses) || the coverage and frame-reference
# tools' --check.
# Phase B (parallel): the synthetic nine-stage pilot walk
# (tests_v8dev/test_pilot_lifecycle.py) || the producer/consumer report
# (tools/v8_pilot_walk.py) || the e2e rule validation
# (tools/v8_pipeline_validation.py --check-only when supported).
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
export DCI1_V7_CPU_WORKERS="${DCI1_V7_CPU_WORKERS:-3}"
LOG="${LOG_DIR:-/tmp/v8-validate-$$}"; mkdir -p "$LOG"
T0=$(date +%s)
stamp() { echo "$(( $(date +%s) - T0 ))s  $*"; }
stamp "== phase A: v8 unit suite || v7 fast subset || tool checks"
( S=$(date +%s); $PY -m pytest tests_v8dev -q -p no:cacheprovider -m "not slow" -n 4 --dist worksteal --basetemp "$LOG/bt-v8" > "$LOG/v8.log" 2>&1; echo "v8-suite exit=$? $(( $(date +%s) - S ))s: $(tail -1 "$LOG/v8.log")" ) &
A1=$!
( S=$(date +%s); $PY -m pytest tests_v7 -q -p no:cacheprovider -m "not slow" -n 4 --dist worksteal --basetemp "$LOG/bt-v7" > "$LOG/v7.log" 2>&1; echo "v7-fast exit=$? $(( $(date +%s) - S ))s: $(tail -1 "$LOG/v7.log")" ) &
A2=$!
( S=$(date +%s); $PY tools/v8_frame_reference.py --check > "$LOG/frame.log" 2>&1; echo "frame-reference exit=$? $(( $(date +%s) - S ))s" ) &
A3=$!
wait $A1 $A2 $A3
stamp "== phase B: synthetic pilot walk || producer/consumer report"
( S=$(date +%s); $PY -m pytest tests_v8dev/test_pilot_lifecycle.py tests_v8dev/test_frame_conditioning.py -m slow -q -p no:cacheprovider --basetemp "$LOG/bt-walk" > "$LOG/walk.log" 2>&1; echo "pilot-walk exit=$? $(( $(date +%s) - S ))s: $(tail -1 "$LOG/walk.log")" ) &
B1=$!
( S=$(date +%s); $PY tools/v8_pilot_walk.py > "$LOG/pc.log" 2>&1; echo "producer-consumer exit=$? $(( $(date +%s) - S ))s" ) &
B2=$!
wait $B1 $B2
stamp "== done; logs in $LOG"
