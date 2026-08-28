"""The v4r3 instrument layer and its canonical verifier hash (§10.6).

The hash covers every source whose bytes can change what a registered v4r3
verifier computes. Two of those sources live in ``dci1v4`` and are carried
unchanged -- the raw word segmenter ``alpha_runs`` and the exact-count rule --
so the hash covers them **by path**, not by re-export. A thin local wrapper
that merely imported them would hash its own bytes and let the carried source
drift underneath it, which is exactly the failure the §10.6 binding exists to
prevent.

``dci1v4/statistics.py`` is hashed too, though v4r3 no longer calls it: the
§7.3 composition correction is stated as an equivalence against those exact
functions (``statistics.assert_agrees_with_v4r2``), so a change in their bytes
changes the meaning of a v4r3 claim and must change the v4r3 hash.

The hash is distinct from, and never replaces, the frozen v3 and v4r2
verifier hashes. Rows of any earlier study stay auditable under their own
recorded hash and are never treated as newly valid.

It changes relative to v4r2 by construction: v4r3 adds the rate and
lower-bound predicates and the §7.2 focal extension, both of which are
scoring semantics. That is why §10.2 re-opens and why the pool amendment had
to be adopted before Gate 1 rather than after it.
"""
from __future__ import annotations

from pathlib import Path

import dci1v4.verifiers as _v4_verifiers
from dci1v4.protocol.hashing import sha_file, sha_obj

#: Modules of this package whose bytes define what a v4r4 verifier computes.
SEMANTIC_MODULES = ("constraints.py", "statistics.py", "compliance.py",
                    "words.py")

#: Sources carried unchanged from the v4r2 instrument layer, hashed at their
#: own location so that a change there is a v4r3 hash change here.
CARRIED_MODULES = ("words.py", "target.py", "statistics.py")


def source_hashes() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    there = Path(_v4_verifiers.__file__).resolve().parent
    carried = {f"dci1v4/{name}": sha_file(there / name)
               for name in CARRIED_MODULES}
    local = {f"dci1v7/{name}": sha_file(here / name)
             for name in SEMANTIC_MODULES}
    return {**carried, **local}


def verifier_source_hash() -> str:
    """The one canonical v4r4 verifier hash, recorded on every generation row
    and re-verified at every §10.6 entry point.

    It differs from v4r3's because `constraints.py` differs: §7.0-R4 removed
    CP4 and CP7. Nothing about the *computation* changed --- every counting
    predicate, every form and every threshold reading is byte-identical --- and
    the hash moves anyway, because it covers the source and not the behaviour.
    That is the intended reading of §10.6: a stale hash may never be carried
    forward on the grounds that behaviour looks unchanged.
    """
    return sha_obj(source_hashes())


__all__ = ["SEMANTIC_MODULES", "CARRIED_MODULES", "source_hashes",
           "verifier_source_hash"]
