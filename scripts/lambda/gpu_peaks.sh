#!/usr/bin/env bash
# Peak memory.used (MiB) per GPU in a gpu_monitor.sh log, optionally between
# two timestamps as nvidia-smi prints them ("2026/10/25 15:30:00.000").
# Usage: gpu_peaks.sh LOG_FILE [FROM] [TO]
set -euo pipefail
LOG="${1:?usage: gpu_peaks.sh LOG_FILE [FROM] [TO]}"
awk -F', ' -v from="${2:-}" -v to="${3:-}" '
  $1 == "timestamp" { next }
  (from == "" || $1 >= from) && (to == "" || $1 <= to) {
    if (!($2 in peak) || $4 + 0 > peak[$2]) { peak[$2] = $4 + 0; total[$2] = $5 }
  }
  END { for (g in peak) printf "gpu %s peak %d MiB of %s MiB\n", g, peak[g], total[g] }
' "$LOG" | sort
