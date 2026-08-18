"""Path registry. The registered evidence tree is READ-ONLY here:
nothing in this package may write beneath EVIDENCE."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # autorater_forensics/
REPO = ROOT.parent                                  # git repo root
EVIDENCE = REPO / "dci1" / "evidence" / "dci1-v3"   # READ-ONLY
DCI_CONSTANTS = (REPO / "dci1" / "src" / "dci1v3" / "protocol"
                 / "constants.py")                  # READ-ONLY reference

DATASET = ROOT / "dataset"
LOGS = ROOT / "logs"
ANALYSIS_OUT = ROOT / "analysis" / "out"
SCAN_RESULTS = ROOT / "scans" / "results"

MODEL_KEYS = ("gemma-3n-e2b-it", "qwen3-4b", "qwen3-4b-instruct-2507",
              "gemma-3n-e4b-it")

#: The three registered development rounds (per model, relative to the
#: model tree). Low and medium are parked supersessions; high is the
#: active round. All are read as bytes only.
ROUND_JUDGMENTS = {
    "low": "gate1/autorater/superseded/881d78927247/dev/judgments.jsonl",
    "medium":
        "gate1/autorater/superseded/1b1b4df78a17/dev/judgments.jsonl",
    "high": "gate1/autorater/dev/judgments.jsonl",
}

SERVER_BASE_URL = "http://127.0.0.1:8555/v1"
SERVED_MODEL_NAME = "gpt-oss-20b"
JUDGE_REVISION = "6cee5e81ee83917806bbde320786a8fb61efebee"
