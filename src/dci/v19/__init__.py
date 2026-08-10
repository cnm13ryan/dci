"""The v19 protocol namespace.

v19 occupies its own versioned namespace (preregistration section 1.2). Low-level
provenance, verifier, satisfiability and schema components from v15/v15.1 may be
reused only where their semantics agree with v19; the scientific spine does not
carry over, because v19 changes it:

    v15.1                            v19
    ------------------------------   -----------------------------------------
    J = 6 references                 J = 4 independently admitted references
    studentised max-T bootstrap      MP-EB and WSR-PP candidates only
    one target-focal pair            three fixed pairs
    single load                      paired loads k in {2, 5} within superblock
    task-level clustering            independent with-replacement superblock law
    zero-SE members dropped          zero variance is an ordinary case

Nothing here may import the v15.1 claim-bearing inference. The max-T machinery
in dci.analysis remains for historical reproduction and as a non-claim-bearing
diagnostic; preregistration section 1.2 forbids restoring it as claim-bearing
inference.
"""
from __future__ import annotations

PROTOCOL_VERSION = "v19-pilot"

# Exact supports, fixed by the protocol and never inferred from observed data.
PRIMITIVE_SUPPORT = (-1.0, 1.0)          # section 12.3: D in [-1, 1], width 2
SECONDARY_SUPPORT = (-2.0, 2.0)          # section 12.3: Q in [-2, 2], width 4

# Familywise level for every confirmatory family. v19 makes SEPARATE guarantees
# per family; there is deliberately no joint level across families.
ALPHA = 0.05

# The two candidate claim-bearing procedures. No third may be introduced after
# comparison data exist (section 12.4).
CANDIDATE_METHODS = ("MP-EB", "WSR-PP")

# Stage 1 floor. The exact value is a pre-freeze decision produced by the signed
# prospective procedure in section 11.9, never by design optimisation.
SESOI_FLOOR = 0.06
