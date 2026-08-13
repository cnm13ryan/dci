"""Decoding must be fully specified, and endpoint names must match their maths."""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.cpu

ROOT = Path(__file__).parents[2]
CONFIG = ROOT / "src/dci/pipeline/stages/c112_configuration_and_statuses.py"
PROVENANCE = ROOT / "src/dci/pipeline/stages/c122_runtime_provenance_gates.py"
FREEZE = ROOT / "src/dci/pipeline/stages/c342_freeze.py"
BACKEND = ROOT / "src/dci/inference/hf_transformers.py"
FALSIFICATION = ROOT / "src/dci/pipeline/stages/c382_gate4_falsification.py"


def test_top_k_is_declared_in_the_protocol_config():
    assert re.search(r"^\s{4}top_k: int = \d+", CONFIG.read_text(), re.M), (
        "top_k must be an explicit protocol field, not a library default")


def test_top_k_is_passed_to_generate():
    """Omitting it left the effective value to transformers or the model card."""
    text = BACKEND.read_text()
    call = re.search(r"model\.generate\(\s*\*\*padded.*?use_cache=True\)", text, re.S)
    assert call, "the batched generate() call was not found"
    assert "top_k=CFG.top_k" in call.group(0), call.group(0)


def test_top_k_enters_the_execution_fingerprint():
    """A behaviourally relevant decoding field must change the fingerprint."""
    assert '"top_k": S.CFG.top_k' in PROVENANCE.read_text()


def test_top_k_is_exported_in_the_frozen_protocol_fields():
    assert '_field("top_k", "decoding"' in FREEZE.read_text()


def test_fingerprint_changes_when_top_k_changes():
    from dci.provenance.hashes import sha
    base = {"do_sample": True, "temperature": 0.7, "top_p": 0.9, "top_k": 0}
    assert sha(base) != sha({**base, "top_k": 50})
    assert sha(base) == sha(dict(base))


def test_misleading_endpoint_name_is_gone():
    # Check the endpoint LITERAL used by the loop, not free prose: the module's
    # comments legitimately discuss the old name to explain the rename.
    text = FALSIFICATION.read_text()
    endpoints = re.search(r'for endpoint in \(([^)]*)\)', text)
    assert endpoints, "the endpoint loop was not found"
    names = re.findall(r'"([^"]+)"', endpoints.group(1))
    assert "strict_or_unscorable" not in names, (
        "`strict` already counts unscorable as failure, so the old name read as "
        "'strict plus extra failures' while the maths forgave partial compliance")
    assert names == ["strict", "violation_or_unscorable_partial_forgiven"], names


def test_endpoint_nesting_is_asserted_in_code():
    """The alternative endpoint is a SUBSET of strict, and the code enforces it."""
    text = FALSIFICATION.read_text()
    assert 'source["outcome"] <= source["fail"]' in text


def test_strict_counts_partial_as_failure():
    """Which is why nothing can be stricter than `strict`."""
    from dci.verifiers.rules import VerificationResult
    for status, binary in (("full", 1), ("partial", 0), ("violation", 0),
                           ("unscorable", 0)):
        res = VerificationResult(status, binary, 0.0, {})
        fail = 1 - res.binary_pass
        forgiving = int(status in ("violation", "unscorable"))
        assert forgiving <= fail, status
    # and the forgiving endpoint differs precisely on `partial`
    assert int("partial" in ("violation", "unscorable")) == 0
