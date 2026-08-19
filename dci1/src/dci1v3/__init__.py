"""DCI-1 v3 — scientifically independent implementation of
``user-notes/DCI-1_preregistration_v3.md``.

This package imports nothing from any earlier DCI implementation. The only
shared infrastructure is the protocol-version-independent vLLM backend seam
(``exploratory/vllm_backend``), crossed as a subprocess.
"""

PROTOCOL = "DCI-1"
PROTOCOL_VERSION = "3.0"
STUDY_ID = "dci1-v3"
SYNTHETIC_STUDY_ID = "dci1-v3-synthetic"
