#!/usr/bin/env bash
# Log GPU memory and utilisation once a second, for peak memory during the
# smoke test and the pilot. Run it in its own tmux window; stop with Ctrl-C.
# Usage: gpu_monitor.sh LOG_FILE        (appends; CSV with a header)
set -euo pipefail
LOG="${1:?usage: gpu_monitor.sh LOG_FILE}"
exec nvidia-smi --query-gpu=timestamp,index,uuid,memory.used,memory.total,utilization.gpu,power.draw \
  --format=csv,nounits -l 1 >> "$LOG"
