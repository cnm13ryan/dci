"""Gate 1 human-annotation reviewer interface (workflow tooling).

Operational tooling around the registered Gate 1 pathway (§10, §25). It
reads the registered ``annotation_packet.jsonl`` and produces the exact
external annotations file that ``dci1v3.cli human-audit --annotations``
consumes (the preserved independent human-validation pathway, A2).
It defines no scientific rule: labels are the registered binary vocabulary
(``pass`` / ``fail``); flags, ordering, and timestamps are workflow
metadata that never enter the exported scientific file.
"""

INTERFACE_VERSION = "dci1v3-annotation/1.1.0"   # A1: single annotator
