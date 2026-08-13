"""The exploratory slice: which A, which B, which C_j, which S — and the design.

Two things matter scientifically in this module and nothing else does:

1. **Reference selection never looks at an outcome.** The rule below is fixed in
   advance and is a function of the registry alone (eligibility, satisfiability,
   authored origin, constraint family, verifier coupling with A measured on the
   model-free response bank). It cannot be tuned toward an effect because no
   generation has happened when it runs.

2. **Focal and reference rows differ in exactly one instruction.** Same task,
   same background set, same instruction count, same position for the swapped
   slot, same wording index, same decoding. If that ever stops being true the
   contrast stops estimating interference and starts estimating whatever else
   moved.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence

from dci_exploratory import harvest

# v19 fixes these; they are imported rather than restated so a registry change
# cannot leave this module quietly disagreeing with the protocol.
from dci.v19.families import N_REFERENCES
from dci.v19.identity import LOADS, ORDERS
from dci.v19.pairs import PAIR_3

# The v19 pair this study measures. p1's verifiers are unimplemented and p2's
# registered measurement risk is logical impossibility of the composition.
TARGET_ID = "A"      # v15 id for v19:p3.target.exact_sentence_count
FOCAL_ID = "B"       # v15 id for v19:p3.focal.increasing_lengths

# o_A places the target before the added-slot occupant; o_Q reverses those two.
ORDER_TARGET_FIRST, ORDER_ADDED_FIRST = ORDERS      # ("o_A", "o_Q")


# ------------------------------------------------------------------ selection
@dataclass(frozen=True)
class Selection:
    """The chosen slice, plus the full audit trail that produced it."""
    target: str
    focal: str
    references: tuple[str, ...]
    background: tuple[str, ...]
    load: int
    candidate_audit: list[dict[str, Any]] = field(default_factory=list)
    background_audit: list[dict[str, Any]] = field(default_factory=list)
    satisfiability_audit: list[dict[str, Any]] = field(default_factory=list)
    rule: str = ""

    @property
    def arms(self) -> tuple[str, ...]:
        """Focal first, then references in frozen order — v19's ARMS shape."""
        return (self.focal, *self.references)

    def reference_weights(self) -> dict[str, float]:
        """UNIFORM, and deliberately so.

        v19 keeps primitive effects reference-specific with no primary averaging
        or weighting, and v15's stochastic weights are a Stage-3 output of a
        calibration run this study does not perform. There is therefore no fitted
        weight vector to reuse, and inventing one would fabricate precision. The
        uniform average is reported as a descriptive summary only; the primary
        quantities are the per-reference contrasts.
        """
        return {ref: 1.0 / len(self.references) for ref in self.references}


def _satisfiable(a_id: str, b_id: str, constraints) -> tuple[bool, str]:
    """The repository's own joint-satisfiability verdict for one pair."""
    from dci.constraints.satisfiability import pair_verdict
    verdict = pair_verdict(constraints[a_id], constraints[b_id])
    status = getattr(verdict, "status", verdict)
    reason = getattr(verdict, "reason", "")
    return (str(status) != "unsatisfiable"), f"{status}: {reason}".strip(": ")


def select(load: int = 5, n_references: int = N_REFERENCES,
           arms_override: Optional[Sequence[str]] = None) -> Selection:
    """Apply the pre-stated selection rule and return the slice with its audit.

    `arms_override` replaces the four selected references with an explicitly
    named set. It exists for the follow-up DIAGNOSTICS (the anti-collapse
    intervention and the semicolon-variant sweep), which deliberately compare a
    named subset or a named variant family rather than the admitted panel. It is
    never used for the primary contrast, and the override is recorded in the run
    config so no run can silently claim to be the admitted design.
    """
    S = harvest.load()
    constraints = S.CONSTRAINTS

    if load not in LOADS:
        raise ValueError(f"load {load} is not one of the preregistered loads {LOADS}")

    # --- step 1: the repository's construction-time eligibility -------------
    eligible_table = S.hard_eligible_universe(S.CANDIDATE_IDS)
    coupling = S.COUPLING

    audit: list[dict[str, Any]] = []
    for cid in S.CANDIDATE_IDS:
        spec = constraints[cid]
        row = eligible_table.loc[cid]
        sat_a, why_a = _satisfiable(TARGET_ID, cid, constraints)
        sat_b, why_b = _satisfiable(FOCAL_ID, cid, constraints)
        audit.append({
            "constraint_id": cid,
            "name": spec.name,
            "category": spec.category,
            "mechanism": spec.mechanism,
            "origin": spec.origin,
            "generative_scope": spec.generative_scope,
            "hard_eligible": bool(row["hard_eligible"]),
            "rejection_reasons": str(row["rejection_reasons"]),
            "agreement_with_A": float(row["agreement_with_A"]),
            "agreement_with_B": float(row["agreement_with_B"]),
            "coupling_with_A": float(coupling.get(cid, float("nan"))),
            "satisfiable_with_A": sat_a, "satisfiability_A": why_a,
            "satisfiable_with_B": sat_b, "satisfiability_B": why_b,
            "instruction": S.INSTRUCTIONS[cid][0],
        })

    viable = [r for r in audit
              if r["hard_eligible"] and r["satisfiable_with_A"] and r["satisfiable_with_B"]]

    # --- step 2: the whole non-shadow authored pool -------------------------
    chosen = sorted(r["constraint_id"] for r in viable if r["origin"] == "cse_pool")

    # --- step 3: top up with shadows that add a MISSING constraint family,
    #             tie-broken by lowest coupling with A, then by id ------------
    covered = {constraints[c].category for c in chosen}
    shadows = [r for r in viable if r["origin"] == "shadow"]
    shadows.sort(key=lambda r: (r["coupling_with_A"], r["constraint_id"]))
    for row in shadows:
        if len(chosen) >= n_references:
            break
        if row["category"] not in covered:
            chosen.append(row["constraint_id"])
            covered.add(row["category"])
    # Only if family coverage still cannot fill the slots do we relax it.
    for row in shadows:
        if len(chosen) >= n_references:
            break
        if row["constraint_id"] not in chosen:
            chosen.append(row["constraint_id"])

    if len(chosen) != n_references:
        raise ValueError(
            f"selection produced {len(chosen)} references, not {n_references}: "
            f"{chosen}. Exactly four references per pair is fixed by v19 (D3).")
    references = tuple(sorted(chosen))
    if arms_override is not None:
        unknown = [c for c in arms_override if c not in constraints]
        if unknown:
            raise ValueError(f"unknown constraint ids in arms_override: {unknown}")
        if TARGET_ID in arms_override or FOCAL_ID in arms_override:
            raise ValueError("arms_override lists the target or the focal; the "
                             "focal arm is always added automatically")
        references = tuple(arms_override)

    # --- step 4: background set S, only if the load calls for one -----------
    background, background_audit = _select_background(
        S, load=load, used=(TARGET_ID, FOCAL_ID, *references))

    # --- step 5: every pair that will actually share a prompt is satisfiable -
    everything = [TARGET_ID, FOCAL_ID, *references, *background]
    sat_audit = []
    for i, first in enumerate(everything):
        for second in everything[i + 1:]:
            ok, why = _satisfiable(first, second, constraints)
            sat_audit.append({"a": first, "b": second, "satisfiable": ok, "verdict": why})
    unsat = [r for r in sat_audit if not r["satisfiable"]]
    if unsat:
        raise ValueError(
            "the selected slice contains a jointly unsatisfiable pair, which "
            f"would measure impossibility rather than interference: {unsat}")

    return Selection(
        target=TARGET_ID, focal=FOCAL_ID, references=references,
        background=background, load=load,
        candidate_audit=audit, background_audit=background_audit,
        satisfiability_audit=sat_audit,
        rule=("hard-eligible under S.hard_eligible_universe AND jointly satisfiable "
              "with A and B; take the whole non-shadow (cse_pool) candidate pool; "
              "top up to N_REFERENCES with shadow candidates adding a missing "
              "constraint family, tie-broken by lowest verifier coupling with A "
              "then by constraint id. No outcome is consulted."))


def custom_selection(target: str, focal: str, references: Sequence[str],
                     load: int = 5,
                     background: Optional[Sequence[str]] = None) -> Selection:
    """A matched design around an ARBITRARY target and arm set.

    `select()` above answers one question — what does v19's own construction-time
    rule admit for pair 3 — and it is deliberately not parameterised, because a
    selection rule you can steer is not outcome-blind.

    The Round 4 experiments ask a different question: given a mechanism proposed
    by the pair-3 result, does it hold for other targets (N = 3, 5, 6; paragraphs
    instead of sentences), other arms (colon, dash, comma, whole-answer marks)
    and other constraint families? Those arms are chosen BY HYPOTHESIS, and this
    function says so in its name and in the `rule` string it writes into every
    run config. It is not, and must not be reported as, the admitted panel.

    What it still enforces is the part that makes any contrast a contrast: the
    background is identical across arms, every pair that shares a prompt is
    jointly satisfiable, and no arm is the target.
    """
    S = harvest.load()
    constraints = S.CONSTRAINTS

    references = tuple(references)
    unknown = [c for c in (target, focal, *references, *(background or ()))
               if c not in constraints]
    if unknown:
        raise ValueError(f"unknown constraint ids: {unknown}")
    if target in (focal, *references):
        raise ValueError(f"the target {target!r} cannot also be an arm")
    if focal in references:
        raise ValueError(f"the focal {focal!r} is added automatically; "
                         "listing it again would duplicate the arm")
    if len(set(references)) != len(references):
        raise ValueError(f"duplicate references: {references}")

    if background is None:
        chosen, background_audit = _select_background(
            S, load=load, used=(target, focal, *references))
    else:
        chosen, background_audit = tuple(background), [
            {"constraint_id": c, "name": constraints[c].name, "selected": True,
             "rejection_reasons": "explicitly named on the command line"}
            for c in background]
        if len(chosen) != max(load - 2, 0) and load >= 0:
            # The S3 ordering design names SEVERAL background-slot variants at
            # load 3, because the variant is a treatment there rather than a
            # fixed context. `build_permutation_design` places exactly one of
            # them in any given prompt, so the realised load is still 3.
            if not (load == 3 and len(chosen) >= 2):
                raise ValueError(
                    f"load {load} needs {max(load - 2, 0)} background "
                    f"instructions (target + one added slot + background); "
                    f"{len(chosen)} were named")

    everything = [target, focal, *references, *chosen]
    sat_audit = []
    for i, first in enumerate(everything):
        for second in everything[i + 1:]:
            ok, why = _satisfiable(first, second, constraints)
            sat_audit.append({"a": first, "b": second, "satisfiable": ok, "verdict": why})
    unsat = [r for r in sat_audit if not r["satisfiable"]]
    if unsat:
        raise ValueError(
            "the requested slice contains a jointly unsatisfiable pair, which "
            f"would measure impossibility rather than interference: {unsat}")

    # The registry's screen is written pair by pair and misses the general form;
    # see `extensions.punctuation_conflicts`. Any design that mixes punctuation
    # arms with a punctuation background must be checked by the general rule as
    # well, or it will silently measure logical impossibility.
    from dci_exploratory import extensions
    target_n = dict(constraints[target].params).get("n")
    clashes = extensions.punctuation_conflicts(
        everything, int(target_n) if target_n is not None else None)
    if clashes:
        raise ValueError(
            "the requested slice mixes a whole-answer punctuation budget with a "
            "per-sentence demand for the same mark, which no output can satisfy "
            f"at this target count: {clashes}")

    return Selection(
        target=target, focal=focal, references=references, background=chosen,
        load=load, candidate_audit=[], background_audit=background_audit,
        satisfiability_audit=sat_audit,
        rule=("HYPOTHESIS-DRIVEN, NOT the admitted v19 panel. Target, focal and "
              "references were named explicitly to test a mechanism proposed by "
              "an earlier exploratory run. Joint satisfiability and an identical "
              "background across arms are still enforced; construction-time "
              "eligibility and outcome-blind reference selection are NOT claimed."))


# Background members excluded by hand, with the reason. Each exclusion is a
# declared interaction with the dimension this pair is measured on, taken from
# the registry's OWN written pathway audit — not a judgement invented here.
_BACKGROUND_EXCLUSIONS = {
    "U_FMT_NOCOMMA": ("its pathway audit declares a length side-effect ('comma "
                      "avoidance can shorten clauses'). Sentence length is "
                      "exactly what B orders, so this would sit in the "
                      "background pushing on the focal mechanism in every arm."),
}

# One background instruction per authored family, so the background block cannot
# push the answer in one direction the way three punctuation rules would.
_BACKGROUND_FAMILIES = ("format", "lexical", "numerical")

# Rule families that FORBID something rather than REQUIRE specific content.
#
# Stage A evidence (runs/stageA5_20260810T182442Z) forced this preference. The
# first background drawn — "exactly 4 distinct integers", "4 words beginning with
# P", "1 colon" — was outcome-blind and correctly matched across arms, but it
# dictated the content of the answer rather than merely loading it: responses
# degenerated into "1234: 1234 / 1234 / 1234 / 1234" and into dense P-alliteration
# in every arm. Background that writes the answer leaves nothing for the focal
# manipulation to act on and makes the raw outputs unreadable, which the manual
# audit depends on.
#
# A prohibition adds a constraint to satisfy without deciding what the text says,
# so it loads composition while leaving the generation free. This changes the
# apparatus, not the contrast: S is identical in the focal and every reference
# arm either way and so cannot move tau in any direction.
_PROHIBITION_FAMILIES = frozenset({
    "no_digits", "no_suffix", "no_char", "forbid_word_set",
    "sentence_initial_forbidden_word", "max_integer_count",
})


def _select_background(S, load: int, used: Iterable[str]
                       ) -> tuple[tuple[str, ...], list[dict[str, Any]]]:
    """The shared background set S, identical in focal and reference arms.

    Drawn from the authored 'unrelated target' bank, whose members carry written
    pathway audits establishing that they neither read the sentence COUNT (which
    is A) nor compare one sentence with another (which is B). A background
    instruction that did either would be a second copy of the treatment.

    Because S is identical across arms it cannot bias `tau` by itself. It can
    still destroy the experiment's sensitivity — a background that floors A in
    every arm leaves nothing to interfere with — which is why it is spread across
    families and why a declared length side-effect disqualifies a member.
    """
    used = set(used)
    n_background = load - 2                     # A + one added slot + background
    audit: list[dict[str, Any]] = []
    if n_background <= 0:
        return (), audit

    # Round-robin over families so the quota is spread rather than taken
    # alphabetically from whichever family sorts first.
    quota = {family: 0 for family in _BACKGROUND_FAMILIES}
    per_family = -(-n_background // len(_BACKGROUND_FAMILIES))

    # Prohibitions first, then the rest; within each tier, by constraint id. The
    # order is total and fixed, so the background is still a deterministic
    # function of the registry and not of anything observed.
    ranked = sorted(S.U_CANDIDATE_IDS,
                    key=lambda c: (S.CONSTRAINTS[c].rule_family not in _PROHIBITION_FAMILIES,
                                   c))
    chosen: list[str] = []
    for cid in ranked:
        spec = S.CONSTRAINTS[cid]
        reasons = []
        if cid in used:
            reasons.append("already used as target, focal or reference")
        if spec.generative_scope != "whole_text":
            # Sentence-scoped 'bridge' members share A's segmentation span.
            reasons.append(f"generative scope {spec.generative_scope}, not whole_text")
        if cid in _BACKGROUND_EXCLUSIONS:
            reasons.append(_BACKGROUND_EXCLUSIONS[cid])
        if spec.u_family not in quota:
            reasons.append(f"family {spec.u_family!r} is not a background family")
        elif quota[spec.u_family] >= per_family:
            reasons.append(f"family {spec.u_family} quota ({per_family}) already filled")
        if not reasons:
            for other in [*used, *chosen]:
                ok, why = _satisfiable(cid, other, S.CONSTRAINTS)
                if not ok:
                    reasons.append(f"not jointly satisfiable with {other} ({why})")
                    break
        selected = not reasons and len(chosen) < n_background
        if selected:
            chosen.append(cid)
            quota[spec.u_family] += 1
        audit.append({"constraint_id": cid, "name": spec.name,
                      "u_family": spec.u_family, "rule_family": spec.rule_family,
                      "prohibition": spec.rule_family in _PROHIBITION_FAMILIES,
                      "pathway_audit": spec.pathway_audit,
                      "selected": selected,
                      "rejection_reasons": "; ".join(reasons)})

    if len(chosen) != n_background:
        raise ValueError(f"needed {n_background} background instructions, "
                         f"found {len(chosen)}: {chosen}")
    return tuple(chosen), audit


# --------------------------------------------------------------------- design
@dataclass(frozen=True)
class Row:
    """One generation request. `pair_key` is what links matched observations."""
    row_id: str
    stage: str
    task_id: str
    topic: str
    condition: str            # "focal" | "reference" | "primitive"
    arm: str                  # focal/reference: the added constraint id
    measured: str             # the constraint whose compliance is scored
    order: str
    load: int
    replicate: int
    ordered_ids: tuple[str, ...]
    paraphrase_id: int
    user_prompt: str
    pair_key: str             # (task, order, replicate) — matched across arms
    scaffold: str = ""        # system-message variant; "" is the protocol default
    variant: str = ""         # background-slot occupant, for the S3 ordering design

    def as_dict(self) -> dict[str, Any]:
        out = self.__dict__.copy()
        out["ordered_ids"] = list(self.ordered_ids)
        return out


def _row_id(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:20]


def _ordered(selection: Selection, added: str, order: str) -> tuple[str, ...]:
    """Target and added occupant swap the FIRST TWO slots; background is fixed.

    Keeping the background block in one fixed position is what makes o_A and o_Q
    differ in exactly the thing v19 says they differ in.
    """
    head = ((selection.target, added) if order == ORDER_TARGET_FIRST
            else (added, selection.target))
    return (*head, *selection.background)


def build_design(selection: Selection, tasks: list[dict[str, str]],
                 replicates: int, base_seed: int, stage: str,
                 paraphrase_id: int = 0,
                 orders: Optional[tuple[str, ...]] = None,
                 include_primitives: bool = True,
                 scaffolds: Sequence[str] = ("",)) -> list[Row]:
    """Matched focal/reference rows for every task, plus isolated primitives.

    For each task X_i, each order and each replicate there is exactly ONE focal
    row and one row per reference, all sharing a `pair_key`. That key is what the
    analysis pairs on; nothing downstream is allowed to pair by position.
    """
    orders = orders or ORDERS
    rows: list[Row] = []

    for task in tasks:
        for scaffold in scaffolds:
            # The scaffold is part of the matching key: a focal row is compared
            # with the reference rows generated under the SAME system message,
            # never across the intervention.
            tag = "" if not scaffold else f"|{scaffold}"
            for order in orders:
                for replicate in range(replicates):
                    pair_key = f"{task['task_id']}|{order}|r{replicate}{tag}"
                    for added in selection.arms:
                        ordered_ids = _ordered(selection, added, order)
                        condition = ("focal" if added == selection.focal
                                     else "reference")
                        row_id = _row_id(stage, task["task_id"], condition, added,
                                         order, replicate, paraphrase_id,
                                         base_seed, scaffold)
                        rows.append(Row(
                            row_id=row_id, stage=stage, task_id=task["task_id"],
                            topic=task["topic"], condition=condition, arm=added,
                            measured=selection.target, order=order,
                            load=selection.load, replicate=replicate,
                            ordered_ids=ordered_ids, paraphrase_id=paraphrase_id,
                            user_prompt=harvest.compose_prompt(
                                task["topic"], list(ordered_ids), paraphrase_id),
                            pair_key=pair_key, scaffold=scaffold))

            if not include_primitives:
                continue
            # Isolated single-instruction rows. A alone answers "can the model do
            # A at all?"; each added constraint alone gives its own difficulty,
            # which is the cheap probe of whether the references are matched to B
            # on anything more than construction.
            #
            # Generated once PER SCAFFOLD, and carrying the scaffold, because a
            # scaffold that changes primitive A-compliance is exactly what the
            # intervention needs to know. Emitting them once with a fixed id
            # collided as soon as two scaffolds were crossed.
            for replicate in range(replicates):
                for cid in (selection.target, *selection.arms):
                    row_id = _row_id(stage, task["task_id"], "primitive", cid,
                                     "isolated", replicate, paraphrase_id,
                                     base_seed, scaffold)
                    rows.append(Row(
                        row_id=row_id, stage=stage, task_id=task["task_id"],
                        topic=task["topic"], condition="primitive", arm=cid,
                        measured=cid, order="isolated", load=1,
                        replicate=replicate,
                        ordered_ids=(cid,), paraphrase_id=paraphrase_id,
                        user_prompt=harvest.compose_prompt(
                            task["topic"], [cid], paraphrase_id),
                        pair_key=f"{task['task_id']}|primitive|r{replicate}{tag}",
                        scaffold=scaffold))

    ids = [r.row_id for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("design rows are not uniquely identified")
    return rows


def assert_matched(rows: list[Row], selection: Selection) -> None:
    """Every check that, if it failed, would silently invalidate the contrast.

    Called by the runner before any generation and by the tests. It is cheaper to
    refuse to run than to discover afterwards that focal and reference rows were
    not comparable.
    """
    groups: dict[str, list[Row]] = {}
    for row in rows:
        if row.condition in ("focal", "reference"):
            groups.setdefault(row.pair_key, []).append(row)

    expected_arms = set(selection.arms)
    for pair_key, group in groups.items():
        arms = {r.arm for r in group}
        if arms != expected_arms:
            raise ValueError(f"{pair_key}: arms {sorted(arms)} != {sorted(expected_arms)}")
        if len({r.task_id for r in group}) != 1:
            raise ValueError(f"{pair_key}: matched rows span several tasks")
        if len({r.topic for r in group}) != 1:
            raise ValueError(f"{pair_key}: matched rows span several topics")
        if len({r.order for r in group}) != 1:
            raise ValueError(f"{pair_key}: matched rows span several orders")
        if len({r.paraphrase_id for r in group}) != 1:
            raise ValueError(f"{pair_key}: matched rows span several wordings")
        if len({len(r.ordered_ids) for r in group}) != 1:
            raise ValueError(f"{pair_key}: instruction COUNT differs across arms")
        if len({r.measured for r in group}) != 1:
            raise ValueError(f"{pair_key}: rows do not all measure the same constraint")
        for row in group:
            if row.measured != selection.target:
                raise ValueError(f"{row.row_id}: measures {row.measured}, not the target")
            if selection.target not in row.ordered_ids:
                raise ValueError(f"{row.row_id}: the target instruction is not in the prompt")
            if row.arm not in row.ordered_ids:
                raise ValueError(f"{row.row_id}: the arm's instruction is not in the prompt")
            # The one instruction that differs between arms must be the arm's.
            others = tuple(c for c in row.ordered_ids if c != row.arm)
            expected = (selection.target, *selection.background)
            if tuple(sorted(others)) != tuple(sorted(expected)):
                raise ValueError(
                    f"{row.row_id}: non-arm instructions are {others}, expected "
                    f"{expected}; focal and reference prompts differ in more than "
                    "the swapped slot")
            # Position of the swapped slot must match the declared order.
            index = row.ordered_ids.index(row.arm)
            target_index = row.ordered_ids.index(selection.target)
            if row.order == ORDER_TARGET_FIRST and not target_index < index:
                raise ValueError(f"{row.row_id}: order {row.order} but target is not first")
            if row.order == ORDER_ADDED_FIRST and not index < target_index:
                raise ValueError(f"{row.row_id}: order {row.order} but added is not first")


# ------------------------------------------------------- S3 ordering designs
#: The six orderings of three roles. `A` is the target, `Q` the focal-slot
#: occupant (B or its matched reference), `C` the background-slot occupant (the
#: colon instruction or its control).
PERMUTATIONS = ("AQC", "ACQ", "QAC", "QCA", "CAQ", "CQA")


def build_permutation_design(target: str, focals: Sequence[str],
                             variants: Sequence[str], tasks: list[dict[str, str]],
                             replicates: int, base_seed: int, stage: str,
                             paraphrase_id: int = 0,
                             permutations: Sequence[str] = PERMUTATIONS,
                             fixed_tail: Sequence[str] = ()) -> list[Row]:
    """Every ordering of (target, focal-slot, background-slot), crossed.

    `design.build_design` can only swap the target with ONE added instruction,
    because that is the contrast v19 defines. It cannot move a background member
    through the prompt, and the question of whether the colon's position matters
    is exactly a question about moving a background member.

    Matching: rows sharing (task, permutation, variant, replicate) form a
    `pair_key`, so the focal/reference contrast is taken **within** an ordering
    and within a background variant. Nothing is ever paired across orderings.
    """
    S = harvest.load()
    rows: list[Row] = []
    for task in tasks:
        for permutation in permutations:
            for variant in variants:
                for replicate in range(replicates):
                    pair_key = (f"{task['task_id']}|{permutation}|{variant}"
                                f"|r{replicate}")
                    for focal in focals:
                        roles = {"A": target, "Q": focal, "C": variant}
                        # `fixed_tail` holds the remaining background members in
                        # a FIXED position, so that raising the load does not
                        # also permute instructions the design is not studying.
                        ordered = (tuple(roles[r] for r in permutation)
                                   + tuple(fixed_tail))
                        rows.append(Row(
                            row_id=_row_id(stage, task["task_id"], permutation,
                                           variant, focal, replicate,
                                           paraphrase_id, base_seed,
                                           "+".join(fixed_tail)),
                            stage=stage, task_id=task["task_id"],
                            topic=task["topic"],
                            condition="focal" if focal == focals[0] else "reference",
                            arm=focal, measured=target, order=permutation,
                            load=len(ordered), replicate=replicate,
                            ordered_ids=ordered, paraphrase_id=paraphrase_id,
                            user_prompt=harvest.compose_prompt(
                                task["topic"], list(ordered), paraphrase_id),
                            pair_key=pair_key, variant=variant))
    ids = [r.row_id for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("permutation design rows are not uniquely identified")
    assert_permutation_matched(rows, target)
    return rows


def assert_permutation_matched(rows: list[Row], target: str) -> None:
    """Within a pair_key, rows differ in the focal slot and in nothing else."""
    groups: dict[str, list[Row]] = {}
    for row in rows:
        groups.setdefault(row.pair_key, []).append(row)
    for pair_key, group in groups.items():
        for field in ("task_id", "order", "variant", "paraphrase_id", "measured"):
            values = {getattr(r, field) for r in group}
            if len(values) != 1:
                raise ValueError(f"{pair_key}: {field} varies across the group: "
                                 f"{sorted(values)}")
        if len({len(r.ordered_ids) for r in group}) != 1:
            raise ValueError(f"{pair_key}: instruction COUNT differs across arms")
        for row in group:
            if row.measured != target or target not in row.ordered_ids:
                raise ValueError(f"{row.row_id}: target missing or not measured")
            if row.arm not in row.ordered_ids:
                raise ValueError(f"{row.row_id}: the arm is not in the prompt")
            # the position of each ROLE must match the declared permutation
            roles = {"A": target, "Q": row.arm, "C": row.variant}
            expected = tuple(roles[r] for r in row.order)
            if row.ordered_ids[:3] != expected:
                raise ValueError(f"{row.row_id}: ordered_ids {row.ordered_ids} "
                                 f"!= permutation {row.order} -> {expected}")
