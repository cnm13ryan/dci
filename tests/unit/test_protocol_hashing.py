"""The protocol hash must be a function of protocol CONTENT, nothing else.

A frozen protocol is identified by `sha`. Two processes that hold the same
protocol must therefore agree on its digest, and two different protocols must
never collide. `default=str` broke both directions at once: an object without a
value-based repr serialized to "<C object at 0x...>", which varies by process
(so a resume is refused) and is shared by every instance of the class (so
distinct protocols collide).
"""
import subprocess
import sys
from pathlib import Path

import pytest

from dci.provenance.hashes import (UnhashableProtocolValue, canonicalize, sha,
                                   stable_int)

pytestmark = pytest.mark.cpu


class _Opaque:
    """Stands in for any object with no value-based serialization."""


def test_unsupported_object_is_refused_not_guessed():
    with pytest.raises(UnhashableProtocolValue, match="_Opaque"):
        sha({"engine": _Opaque()})


def test_two_distinct_opaque_objects_no_longer_collide_or_diverge():
    """Both failure directions of `default=str`, closed by the same refusal.

    "<_Opaque object at 0x...>" made the digest a function of allocation: the
    same logical payload hashed to three different values under three
    PYTHONHASHSEEDs (measured), while two genuinely distinct objects collided
    whenever the allocator reused an address. Refusing is the only answer that
    is both reproducible and honest.
    """
    for payload in ({"a": _Opaque()}, {"a": _Opaque()}):
        with pytest.raises(UnhashableProtocolValue):
            sha(payload)


def test_supported_non_json_types_have_canonical_forms():
    assert canonicalize(Path("/a/b")) == "/a/b"
    assert canonicalize(("x", 1)) == ["x", 1]
    assert canonicalize({"s": {"b", "a"}}) == {"s": ["a", "b"]}
    # Set order is not a protocol fact, so the two literals must agree.
    assert sha({"s": {"a", "b"}}) == sha({"s": {"b", "a"}})


def test_numpy_scalars_reduce_to_python_scalars():
    np = pytest.importorskip("numpy")
    assert sha({"n": np.int64(3)}) == sha({"n": 3})
    assert sha({"x": np.float64(1.5)}) == sha({"x": 1.5})


def test_non_string_keys_are_refused():
    with pytest.raises(UnhashableProtocolValue, match="dict key"):
        sha({("a", "b"): 1})


def test_content_still_drives_the_digest():
    base = {"protocol_version": "v15.1", "top_k": 0, "temperature": 0.7}
    assert sha(base) == sha(dict(reversed(list(base.items()))))
    assert sha(base) != sha({**base, "top_k": 50})


_CROSS_PROCESS = """
import json, sys
from pathlib import Path
from dci.provenance.hashes import sha
payload = {"paths": [Path("/content/dci"), Path("/lambda/nfs/x")],
           "seeds": (11, 22, 33),
           "members": {"S_COMMA", "C_W3", "S_SEMICOLON"},
           "nested": {"b": {"members": frozenset({"y", "x"})}, "a": None},
           "version": "v15.1"}
print(sha(payload))
"""


@pytest.mark.parametrize("seed", ["0", "1", "12345"])
def test_digest_is_stable_across_processes_and_hash_seeds(seed):
    """PYTHONHASHSEED changes set iteration order; it must not change the hash."""
    digests = set()
    for _ in range(2):
        proc = subprocess.run([sys.executable, "-c", _CROSS_PROCESS],
                              capture_output=True, text=True, timeout=120,
                              env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin",
                                   "PYTHONPATH": str(Path(__file__).resolve()
                                                     .parents[2] / "src")})
        assert proc.returncode == 0, proc.stderr
        digests.add(proc.stdout.strip())
    assert len(digests) == 1
    # And it must equal what this process computes for the same content.
    assert digests == {sha({"paths": [Path("/content/dci"), Path("/lambda/nfs/x")],
                           "seeds": (11, 22, 33),
                           "members": {"S_COMMA", "C_W3", "S_SEMICOLON"},
                           "nested": {"b": {"members": frozenset({"y", "x"})},
                                      "a": None},
                           "version": "v15.1"})}


def test_stable_int_is_seed_independent():
    assert stable_int("S_COMMA") == stable_int("S_COMMA")
    assert stable_int("S_COMMA") != stable_int("S_SEMICOLON")
