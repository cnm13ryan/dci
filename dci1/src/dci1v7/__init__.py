"""DCI-1 protocol v7: the composed contrast is estimated, not gated.

**Status: ADOPTED 2026-08-28** (drafted 2026-08-27; §13.14 revised as V10 on
2026-08-28 before adoption). ``protocol/manifest.assert_documents_adopted``
reads what each governed document says about itself, ``document_hashes``
refuses a missing one, and ``protocol/decisions`` refuses every path that
depends on a §34 decision the researcher has not recorded on
``reports/dci1v7/researcher_decisions.json`` --- which now closes all
twenty-six. Adoption is a researcher act no code performs; registration is
§18 stage 1 and binds this package's commit.

**Why there is a v7.** v6 ran on 2026-08-26/27 and every replication is
terminal without a confirmatory row: ``qwen3-4b`` and
``qwen3-4b-instruct-2507`` at ``GATE_2_75_COMPOSED_PROBE`` with
``COMPOSED_HEADROOM_UNREACHABLE`` --- B's compliance *rose* under A, from
0.747 to 0.891 and from 0.779 to 0.924, and the projected Gate-4 interval
crossed 0.95; ``gemma-3n-e4b-it`` at ``GATE_4_COMPOSED_CONTRAST`` with
``COMPOSED_HEADROOM_FAILURE`` on ``solo:CL`` = 0.958, a companion slot in a
solo cell that enters no primary estimand; and ``gemma-3n-e2b-it`` at
``PREFREEZE_AUDIT`` because the preregistration had been amended after
registration and the lifecycle had no legal way to say so.

**What this package changes, and nothing else.** §13.14's absolute
composed-headroom band is no longer a terminal criterion anywhere. The
quantity the study exists to estimate is a paired contrast between composed
cells --- ``Delta_R = mean_j P(B | B+R_j) - P(B | B+A)`` per configuration ---
and a composed rate near 0 or 1 does not make that contrast undefined. What it
can do is make one *direction* of it unattainable at the smallest effect of
interest, make one arm's sampling uncertainty invisible to a block bootstrap,
or, when every differenced cell sits at the same exact boundary, make the
contrast a structural zero. Each of those is a property of the **contrast**
and each is now measured and recorded as one: ``analysis/boundary.py`` at the
confirmatory analysis, and the same rule projected on Gate 4's 24-topic
composed set and Gate 2.75's 192-topic probe, both of which now record and
neither of which terminates. The two statuses that did terminate are
withdrawn from the vocabulary. §32.3 froze §13 from v6's first Gate-2.5
record, so this cannot be a v6 amendment; it is a superseding registration,
and ``protocol/revision.py`` enumerates every difference where the code can
check it.

**Amended in place on 2026-08-28 (A6, A7, A8), after v7 ran.** All four v7
replications passed every scientific gate and terminated at
``PREFREEZE_AUDIT`` on one artifact check that required §13.15's support to
have been *met* --- against §13.15, §18 stage 10, §28.2 and the closed §34
D6, all of which say a non-identified replication continues. A6 replaces
that check with the registered invariant (the record of §13.15, D6's
disposition, the exact non-identified member set, the arm set, no
rehabilitation path, every empty freeze field explained); A7 scopes §12.6's
coverage conditions to the arm each exists for (C1/C3/C5/C6 gate the core
arm, C2/C4 gate the spectrum arm; no value moves), because every v7
replication lost C4 alone with three matched references in hand; A8 states
D6's meaning once. ``protocol/revision.py`` V11-V13 check each; the §32
chain (A4) binds the amended documents; the four terminal reports stand.

**Isolation, in every direction.** ``STUDY_ID`` is ``dci1v7``. It satisfies no
earlier revision's admission prefix, and ``FOREIGN_STUDY_PREFIXES`` names
every earlier study and screen **including ``dci1v6``**, whose evidence is
closed and enters v7 only as ``HISTORICAL_OUTCOME`` or
``DEVELOPMENT_EVIDENCE`` through ``protocol/reuse_ledger.py``. No v6 row may
enter a v7 estimand and no v6 stage record may satisfy a v7 stage: v7 runs its
pre-composed stages again under its own seeds.

**What v7 does not claim.** The measurement basis its Gate 1 can write is
``deterministic_measurement_validated``, exactly as v5's and v6's were. That
is not ``human_validated``, so ``SCOPE_SENTENCE`` attaches to every analysis
record under it, permanently.
"""
from __future__ import annotations

#: The study identity written into every v7 manifest and stage record.
#: Deliberately hyphen-free and deliberately not a prefix-extension of any
#: earlier identifier: see the isolation note above.
STUDY_ID = "dci1v7"

#: What this package's artifacts are, for any reader that meets one.
#: ``run/execute`` stamps it onto every generated row, so it has to say what
#: is true at the moment the row is written. It moved when the researcher
#: adopted v7 on 2026-08-28, and not before (V5-E3's fix, carried).
CLASSIFICATION = "DCI-1 PROTOCOL v7 (ADOPTED 2026-08-28)"
#: Empty, and its emptiness is the fact: no v7 manifest has been signed and
#: no v7 row has been written, so no reader can meet a superseded label.
SUPERSEDED_CLASSIFICATIONS: tuple[str, ...] = ()

#: The revision this one follows, and how it ended. v6 **closed**: all four
#: replications reached a §28 terminal status before any confirmatory row.
#: Per-replication terminal statuses live in
#: ``dci1/reports/dci1v6/closure.json`` and are read only as historical
#: outcomes and development evidence.
SUPERSEDES = "dci1v6"
#: Three different stages ended v6's four replications; the one this revision
#: is a response to is named, and the others are on the closure record.
SUPERSEDES_TERMINAL_STAGE = "GATE_2_75_COMPOSED_PROBE"
SUPERSEDES_TERMINAL_STATUS = "CLOSED_WITHOUT_CONFIRMATORY_GENERATION"
#: The v6 terminal statuses whose criterion v7 withdraws. Historical labels
#: for v6's terminations; v7 never emits them and has no raise path for them.
SUPERSEDED_TERMINAL_STATUSES = ("COMPOSED_HEADROOM_UNREACHABLE",
                                "COMPOSED_HEADROOM_FAILURE")

#: The evidence tree, a sibling of every other study's and of every screen's.
EVIDENCE_DIRNAME = "dci1v7"

#: The preregistration this package implements, by repository path.
PREREGISTRATION = "user-notes/DCI1_preregistration_v7.md"

#: The machine-readable statement of §13's rule and of the composed-contrast
#: rule, generated from this code by ``tools/v7_reference_design_spec.py``.
#: Where it and the preregistration disagree, the preregistration governs.
REFERENCE_DESIGN_SPEC = "dci1/reports/dci1v7/reference_design_spec.json"

#: Study identifier prefixes whose artifacts this package refuses as input
#: (§14.2). ``dci1v6`` is the entry that matters: v6 produced signed rows
#: through Gate 4 on two replications and four terminal reports, and none of
#: them may satisfy a v7 stage or reach a v7 estimator.
FOREIGN_STUDY_PREFIXES = ("dci1-v2", "dci1-v3", "dci1-v4", "dci1v4r3",
                          "dci1v4r4", "dci1v5", "dci1v6", "br-pilot",
                          "fs-screen", "bgrid-screen", "matrix-screen",
                          "dci1-cal-screen")

__all__ = ["STUDY_ID", "CLASSIFICATION", "SUPERSEDED_CLASSIFICATIONS",
           "EVIDENCE_DIRNAME", "PREREGISTRATION", "REFERENCE_DESIGN_SPEC",
           "FOREIGN_STUDY_PREFIXES", "SUPERSEDES", "SUPERSEDES_TERMINAL_STAGE",
           "SUPERSEDES_TERMINAL_STATUS", "SUPERSEDED_TERMINAL_STATUSES"]
