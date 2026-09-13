"""§12.5's topic-reservation audit for every v4r3 row on disk.

    ./.venv/bin/python tools/v4r3_topic_audit.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4r3 import EVIDENCE_DIRNAME                            # noqa: E402
from dci1v4r3.stages.audit import (                              # noqa: E402
    assert_reserved_sets_unspent, audit_evidence_tree,
)

OUT = REPO / "reports" / "dci1v4r3"


def main() -> int:
    report = audit_evidence_tree(REPO / "evidence" / EVIDENCE_DIRNAME)
    report = assert_reserved_sets_unspent(report)
    OUT.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT / "topic_audit.json", report)
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
