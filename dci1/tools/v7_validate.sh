#!/usr/bin/env bash
# The v7 validation sequence, with the parallelism the machine allows.
#
#     tools/v7_validate.sh [workers]           # default 5
#
# Parallel across independent work only; sequential wherever a result feeds
# a later step or a governed artifact is written. Two phases of overlapping
# independent jobs, each pytest invocation with its own --basetemp (pytest
# wipes its basetemp at session start) and each tool writing its report
# atomically. Measured on this machine (24 CPUs): a walk is ~8 min and
# ~5.5 GB RSS, so phase B's six heavy processes are ~34 GB.
#
#   spec regeneration           sequential, governed, first
#   phase A: audit --workers W  || fast subset (xdist, worksteal)
#   phase B: synthetic module   || D6 module (W branch workers) || producer/consumer
#
# Nothing scientific runs differently: the same rules, scenarios and tests.
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
W="${1:-5}"
# The stages' own process pools (engine/parallel) inside each scenario or
# test process, bounded so W scenario processes share the cores.
export DCI1_V7_CPU_WORKERS="${DCI1_V7_CPU_WORKERS:-3}"
LOG="${LOG_DIR:-/tmp/v7-validate-$$}"; mkdir -p "$LOG"
T0=$(date +%s)
stamp() { echo "$(( $(date +%s) - T0 ))s  $*"; }

# The reference-design spec is bound by hash through the §32 chain; a
# regeneration that changes a byte must be followed by a chain record, so
# it is opt-in here (REGEN_SPEC=1) and never silent.
if [ "${REGEN_SPEC:-0}" = "1" ]; then
  stamp "== spec regeneration (sequential, governed, chain-bound)"
  $PY tools/v7_reference_design_spec.py | tail -1
else
  stamp "== spec regeneration skipped (REGEN_SPEC=1 to run; the spec hash is chain-bound)"
fi
stamp "== phase A: execution-path audit (--workers $W) || fast subset (xdist worksteal)"
( S=$(date +%s); $PY tools/v7_execution_path_audit.py --workers "$W" > "$LOG/audit.log" 2>&1; echo "audit exit=$? $(( $(date +%s) - S ))s" ) &
A1=$!
( S=$(date +%s); $PY -m pytest tests_v7 -q -p no:cacheprovider -m "not slow" -n 4 --dist worksteal --basetemp "$LOG/bt-fast" > "$LOG/fast.log" 2>&1; echo "fast-subset exit=$? $(( $(date +%s) - S ))s: $(tail -1 "$LOG/fast.log")" ) &
A2=$!
wait $A1 $A2
stamp "== phase B: synthetic lifecycle || D6 continuation ($W branch workers) || producer/consumer"
( S=$(date +%s); $PY -m pytest tests_v7/test_synthetic_lifecycle.py -q -p no:cacheprovider --basetemp "$LOG/bt-synth" > "$LOG/synth.log" 2>&1; echo "synthetic exit=$? $(( $(date +%s) - S ))s: $(tail -1 "$LOG/synth.log")" ) &
B1=$!
( S=$(date +%s); DCI1_V7_SCENARIO_WORKERS="$W" $PY -m pytest tests_v7/test_d6_continuation.py -q -p no:cacheprovider --basetemp "$LOG/bt-d6" > "$LOG/d6.log" 2>&1; echo "d6 exit=$? $(( $(date +%s) - S ))s: $(tail -1 "$LOG/d6.log")" ) &
B2=$!
( S=$(date +%s); $PY tools/v7_producer_consumer.py > "$LOG/pc.log" 2>&1; echo "producer-consumer exit=$? $(( $(date +%s) - S ))s" ) &
B3=$!
wait $B1 $B2 $B3
stamp "== done; logs in $LOG"
tail -3 "$LOG/audit.log"
