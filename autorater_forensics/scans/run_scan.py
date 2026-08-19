"""Run the registered Scout scanners over the forensics Inspect logs.

    .venv/bin/python scans/run_scan.py [logs_subdir ...]

Defaults to scanning all three effort runs. Results are written under
scans/results/ (raw Inspect logs are never modified)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inspect_scout import scan, transcripts_from  # noqa: E402

from scans.scanners import reasoning_final_contradiction  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    subdirs = sys.argv[1:] or ["low", "medium", "high"]
    locations = [str(ROOT / "logs" / d) for d in subdirs]
    status = scan(
        scanners=[reasoning_final_contradiction()],
        transcripts=transcripts_from(locations),
        scans=str(ROOT / "scans" / "results"),
    )
    print(status)
