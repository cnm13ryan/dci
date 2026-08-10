VERIFIER_TEMPLATE_PATH = AUDIT_DIR / "verifier_audit_template.csv"
VERIFIER_SIGNED_PATH = AUDIT_DIR / "verifier_audit_signed.csv"
VERIFIER_KEY_PATH = AUDIT_DIR / "verifier_audit_key.csv"
VERIFIER_STRATA_PATH = AUDIT_DIR / "verifier_audit_strata.csv"

# Point this at a completed audit to sign off. Leave as None until one exists.
VERIFIER_AUDIT_SIGNED_INPUT: Optional[str] = None

# =====================================================================
# Reliability architecture (v15)
#
# v14 audited all 45 constraint ids independently and sized the audit from a
# formula the gate did not use. Two things are wrong with that.
#
#  1. The size was unattainable. Gate M decides on a two-sided Wilson upper
#     bound within each human-ground-truth class; v14 sized from a one-sided
#     zero-error formula on the audit TOTAL. Its own gate could not pass.
#  2. Auditing 45 ids buys nothing over auditing the distinct verifier
#     implementations they share: 45 ids run 31 implementations, and a defect
#     lives in an implementation, not in a parameter value.
#
# v15 audits two tiers, and says plainly that they are different claims.
#
#   tier 1  A and B, individually, at verifier_error_ceiling. A carries the
#           primary outcome and B defines the focal contrast.
#   tier 2  every other verifier IMPLEMENTATION as its own stratum, at the
#           coarser stratum_error_ceiling, plus a POOLED certificate across all
#           tier-2 strata at verifier_error_ceiling.
#
# What tier 2 establishes is that the reference/target verifier system as a
# whole is below the strict ceiling, and that no individual implementation is
# above the coarse one. It does NOT establish that each implementation is
# individually below the strict ceiling. That stronger claim is implemented and
# costed in the compute budget; it needs roughly 4,500 adjudicated labels and
# was not adopted for the workshop. The ceiling was not lowered to save labels.
# =====================================================================
VERIFIER_IMPLEMENTATION: dict[str, str] = {
    cid: CONSTRAINTS[cid].rule_family for cid in CONSTRAINTS}

# Every constraint that could ever be selected, screened or measured.
SELECTABLE_IDS = tuple(sorted(
    {CFG.target_id, CFG.focal_id, *CANDIDATE_IDS, *U_CANDIDATE_IDS,
     CFG.u_screen_partner_id}))
TIER1_IDS = tuple(c for c in CFG.always_audited_ids if c in CONSTRAINTS)
TIER2_STRATA = tuple(sorted(
    {VERIFIER_IMPLEMENTATION[c] for c in SELECTABLE_IDS if c not in TIER1_IDS}))

# Coverage is a property that must hold, not an aspiration: every selectable
# constraint has to be reachable from an audited stratum.
_TIER1_STRATA = {VERIFIER_IMPLEMENTATION[c] for c in TIER1_IDS}
AUDIT_COVERAGE = {
    cid: ("tier1" if cid in TIER1_IDS else
          ("tier2:" + VERIFIER_IMPLEMENTATION[cid]
           if VERIFIER_IMPLEMENTATION[cid] in TIER2_STRATA else
           "tier1-shared:" + VERIFIER_IMPLEMENTATION[cid]
           if VERIFIER_IMPLEMENTATION[cid] in _TIER1_STRATA else ""))
    for cid in SELECTABLE_IDS}
UNCOVERED_IDS = sorted(c for c, s in AUDIT_COVERAGE.items() if not s)
assert not UNCOVERED_IDS, (
    f"{UNCOVERED_IDS} are selectable but belong to no audited stratum. Every "
    "constraint that can enter a scientific design must be covered.")

# Parameter extremes inside a stratum are where an off-by-one lives, so the
# sample is forced to contain them rather than left to chance.
_STRATUM_MEMBERS: dict[str, list[str]] = {}
for _c in SELECTABLE_IDS:
    _STRATUM_MEMBERS.setdefault(VERIFIER_IMPLEMENTATION[_c], []).append(_c)


def stratum_parameter_extremes(stratum: str) -> list[str]:
    """The member ids at the extremes of the stratum's parameter range."""
    members = sorted(_STRATUM_MEMBERS.get(stratum, []))
    if len(members) <= 2:
        return members
    def _key(cid: str) -> float:
        values = [v for v in CONSTRAINTS[cid].param_dict.values()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)]
        return float(values[0]) if values else float("nan")
    numeric = [c for c in members if not math.isnan(_key(c))]
    if len(numeric) < 2:
        return members[:2]
    ordered = sorted(numeric, key=_key)
    return sorted({ordered[0], ordered[-1], members[len(members) // 2]})


def _case_stratum(text: str, cid: str) -> str:
    """Boundary cases are the ones that discriminate between verifiers."""
    result = verify(text, cid)
    if result.status == "partial" or 0.0 < float(result.continuous_score) < 1.0:
        return "boundary"
    base = int(result.binary_pass)
    for mutate in MUTATIONS.values():
        try:
            if verify(mutate(text), cid).binary_pass != base:
                return "boundary"
        except Exception:
            continue
    return "clear_pass" if base == 1 else "clear_fail"


# Realistic malformations. The verifier will meet these in real output, and an
# audit drawn only from well-formed authored prose does not test the code paths
# that actually break. When a non-evidence pilot model is available its own
# outputs are added here; until then these are constructed to the same shapes.
def malformed_variants(text: str, rng) -> list[str]:
    body = normalize_text(text)
    if not body:
        return []
    head = body[: max(20, int(len(body) * 0.6))]
    return [
        head,                                        # cut off mid-sentence
        body + " ...",                               # trailing ellipsis
        body.replace(". ", ".  ").replace(",", " ,"),  # loose spacing
        "1. " + body.replace(". ", "\n2. ", 1),      # numbered-list framing
        body.upper(),                                # casing collapse
        body.replace(".", "!"),                      # alternative terminators
        '"' + body,                                  # unbalanced quote
        body + " (continued",                        # unbalanced bracket
        body.replace(" ", " ", 3),              # non-breaking spaces
        "Sure! Here is the answer:\n\n" + body,      # chat preamble
    ]


def near_miss_variants(text: str, cid: str) -> list[str]:
    """Minimal targeted edits that flip THIS constraint's verdict.

    Generic mutations never flip a rule like "the answer must contain the word
    'overall'", so such a verifier reaches the audit with no boundary cases at
    all and the part of it most likely to be wrong is never shown to a reviewer.
    These edits are derived from the constraint's own declared parameters.
    """
    body = normalize_text(text)
    if not body:
        return []
    words: list[str] = []
    for value in CONSTRAINTS[cid].param_dict.values():
        if isinstance(value, str) and value.isalpha():
            words.append(value)
        elif isinstance(value, (tuple, list)):
            words += [v for v in value if isinstance(v, str) and v.isalpha()]
    out = []
    for word in words[:4]:
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        if pattern.search(body):
            out.append(pattern.sub("", body, count=1))
            out.append(pattern.sub("", body))
        else:
            out.append(body.rstrip(".") + f" {word}.")
            out.append(f"{word.capitalize()}, " + body[0].lower() + body[1:])
    return [t for t in dict.fromkeys(out) if normalize_text(t)]


def build_measurement_cases() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Deterministic blinded audit sample. Needs no model and no GPU.

    Returns (reviewer, key, strata_plan). The sample is sized per TRUTH CLASS,
    and because the truth class is unknown before adjudication it is
    approximated by the automatic verdict and then over-drawn on both sides, so
    that a reasonable disagreement rate still leaves both denominators above
    what the ceiling requires.
    """
    pool = list(dict.fromkeys(list(RESPONSE_BANK) + list(SYNTHETIC_CORPUS)
                              + list(PILOT_AUDIT_OUTPUTS)))
    plan_rows, rows = [], []

    def _draw_for(unit: str, ids: list[str], per_class: int, tier: str) -> None:
        rng = np.random.default_rng(CFG.base_seed + stable_int(f"audit15|{unit}", 99991))
        # Over-draw so that adjudication disagreements cannot starve a class.
        target_class = int(math.ceil(per_class / (1.0 - CFG.audit_overdraw_margin)))
        buckets: dict[str, list[tuple[str, str]]] = {
            "boundary": [], "clear_pass": [], "clear_fail": [], "malformed": []}
        for cid in ids:
            for text in pool:
                buckets[_case_stratum(text, cid)].append((text, cid))
            for text in pool[:30]:
                base = verify(text, cid).binary_pass
                for mutate in MUTATIONS.values():
                    try:
                        mutated = mutate(text)
                    except Exception:
                        continue
                    if verify(mutated, cid).binary_pass != base:
                        buckets["boundary"].append((mutated, cid))
            for text in pool[:12]:
                for variant in malformed_variants(text, rng):
                    buckets["malformed"].append((variant, cid))
            for text in pool[:12]:
                base = verify(text, cid).binary_pass
                for variant in near_miss_variants(text, cid):
                    if verify(variant, cid).binary_pass != base:
                        buckets["boundary"].append((variant, cid))
        for name in buckets:
            buckets[name] = list(dict.fromkeys(buckets[name]))

        # Split each bucket by automatic verdict, then fill both classes.
        def by_auto(name: str, want_pass: bool) -> list[tuple[str, str]]:
            return [(t, c) for t, c in buckets[name]
                    if bool(verify(t, c).binary_pass) == want_pass]

        n_boundary = int(math.ceil(CFG.review_boundary_share * target_class))
        n_malformed = int(math.ceil(CFG.review_malformed_share * target_class))
        n_clear = max(0, target_class - n_boundary - n_malformed)
        chosen: list[tuple[str, str, str]] = []
        for want_pass in (False, True):
            clear = "clear_pass" if want_pass else "clear_fail"
            for name, k in (("boundary", n_boundary), ("malformed", n_malformed),
                            (clear, n_clear)):
                items = by_auto(name, want_pass)
                if not items or k <= 0:
                    continue
                idx = rng.permutation(len(items))[:k]
                chosen += [(items[i][0], items[i][1], name) for i in idx]
            # Top up this class from anywhere that the verifier decides the
            # same way, so the class denominator is not silently short.
            have = sum(1 for t, c, _ in chosen
                       if bool(verify(t, c).binary_pass) == want_pass)
            if have < target_class:
                spare = [(t, c) for t, c in
                         (buckets["boundary"] + buckets["malformed"]
                          + buckets["clear_pass"] + buckets["clear_fail"])
                         if bool(verify(t, c).binary_pass) == want_pass
                         and (t, c) not in {(a, b) for a, b, _ in chosen}]
                idx = rng.permutation(len(spare))[:target_class - have]
                chosen += [(spare[i][0], spare[i][1], "topup") for i in idx]

        drawn_pass = sum(1 for t, c, _ in chosen if verify(t, c).binary_pass)
        plan_rows.append({
            "audit_unit": unit, "tier": tier, "member_ids": ";".join(ids),
            "cases_per_truth_class_required": per_class,
            "cases_drawn": len(chosen),
            "drawn_auto_pass": drawn_pass, "drawn_auto_fail": len(chosen) - drawn_pass,
            "ceiling": (CFG.verifier_error_ceiling if tier == "tier1"
                        else CFG.stratum_error_ceiling)})
        for text, cid, stratum in chosen:
            result = verify(text, cid)
            rows.append({"audit_unit": unit, "tier": tier, "constraint_id": cid,
                         "stratum": stratum,
                         "rule_text": INSTRUCTIONS[cid][0], "response_text": text,
                         "auto_status": result.status,
                         "auto_binary_pass": int(result.binary_pass)})

    for cid in TIER1_IDS:
        _draw_for(cid, [cid], CASES_PER_TRUTH_CLASS, "tier1")
    for stratum in TIER2_STRATA:
        _draw_for(stratum, stratum_parameter_extremes(stratum),
                  STRATUM_CASES_PER_TRUTH_CLASS, "tier2")

    frame = pd.DataFrame(rows)
    rng = np.random.default_rng(CFG.base_seed + 31337)
    frame = frame.iloc[rng.permutation(len(frame))].reset_index(drop=True)
    frame.insert(0, "case_id", [f"V{i:05d}" for i in range(1, len(frame) + 1)])

    # Reviewer-facing: the rule and the response, nothing that reveals the arm,
    # the condition, the stratum or what the verifier decided.
    reviewer = frame[["case_id", "rule_text", "response_text"]].copy()
    reviewer["manual_verdict"] = ""       # reviewer writes pass / fail
    reviewer["reviewer_note"] = ""
    key = frame[["case_id", "audit_unit", "tier", "constraint_id", "stratum",
                 "auto_status", "auto_binary_pass"]].copy()
    return reviewer, key, pd.DataFrame(plan_rows)


def _class_bounds(auto: np.ndarray, human: np.ndarray) -> dict[str, Any]:
    """Both conditional error rates with their denominators, never faked.

    n_true_fail and n_true_pass are reported as they are. v14 divided by
    max(n, 1), which turns "no examples of this truth class" into "zero errors
    out of one", i.e. into apparent evidence. A denominator of zero is a
    missing denominator, and the bound is NaN.
    """
    n_true_fail = int((human == 0).sum())
    n_true_pass = int((human == 1).sum())
    false_pass = int(((auto == 1) & (human == 0)).sum())
    false_fail = int(((auto == 0) & (human == 1)).sum())
    fp_rate = false_pass / n_true_fail if n_true_fail else float("nan")
    ff_rate = false_fail / n_true_pass if n_true_pass else float("nan")
    _, fp_upper = (wilson_interval(false_pass, n_true_fail, CFG.verifier_audit_confidence)
                   if n_true_fail else (float("nan"), float("nan")))
    _, ff_upper = (wilson_interval(false_fail, n_true_pass, CFG.verifier_audit_confidence)
                   if n_true_pass else (float("nan"), float("nan")))
    return {"n_true_fail": n_true_fail, "n_true_pass": n_true_pass,
            "false_pass": false_pass, "false_fail": false_fail,
            "false_pass_rate": fp_rate, "false_pass_upper": fp_upper,
            "false_fail_rate": ff_rate, "false_fail_upper": ff_upper}


def evaluate_verifier_reliability(signed_path: Optional[str],
                                  key: pd.DataFrame) -> dict[str, Any]:
    """Per-unit conditional error bounds plus a pooled tier-2 certificate."""
    out: dict[str, Any] = {
        "present": False, "sha256": None, "table": pd.DataFrame(),
        "pooled": {}, "passed": False, "status": GateStatus.AUDIT_MISSING,
        "reason": "no signed audit supplied", "missing_units": [],
        "class_short_units": []}
    if not signed_path or not Path(signed_path).exists():
        return out
    out["present"] = True
    out["sha256"] = sha_file(Path(signed_path))
    signed = pd.read_csv(signed_path)
    if not {"case_id", "manual_verdict"} <= set(signed.columns):
        out["reason"] = "signed audit is missing required columns"
        return out
    merged = signed.merge(key, on="case_id", how="inner")
    merged["human_pass"] = (merged["manual_verdict"].astype(str).str.strip().str.lower()
                            .isin({"pass", "yes", "1", "true"})).astype(int)

    report = []
    for unit, group in merged.groupby("audit_unit"):
        human = group["human_pass"].to_numpy()
        auto = group["auto_binary_pass"].to_numpy()
        tier = str(group["tier"].iloc[0])
        ceiling = (CFG.verifier_error_ceiling if tier == "tier1"
                   else CFG.stratum_error_ceiling)
        required = (CASES_PER_TRUTH_CLASS if tier == "tier1"
                    else STRATUM_CASES_PER_TRUTH_CLASS)
        bounds = _class_bounds(auto, human)
        observed = float((human == auto).mean())
        expected = sum(float((human == v).mean() * (auto == v).mean()) for v in (0, 1))
        kappa = (float("nan") if math.isclose(expected, 1.0)
                 else (observed - expected) / (1 - expected))
        boundary = int((group["stratum"] == "boundary").sum())
        malformed = int((group["stratum"] == "malformed").sum())
        class_ok = (bounds["n_true_fail"] >= required
                    and bounds["n_true_pass"] >= required)
        report.append({
            "audit_unit": unit, "tier": tier, "ceiling": ceiling,
            "n": len(group), "n_boundary": boundary, "n_malformed": malformed,
            "cases_per_class_required": required, **bounds,
            "agreement": observed, "kappa": kappa,
            "class_support_ok": class_ok,
            "boundary_target": int(math.floor(
                CFG.review_boundary_share * required * 0.8)),
            # A requirement that cannot be met is recorded as unmet, not waived
            # silently: where the corpus and the declared edits produce no case
            # that flips this verifier, the audit says so.
            "boundary_coverage": (
                "met" if boundary >= max(1, int(math.floor(
                    CFG.review_boundary_share * required * 0.8)))
                else "none_reachable" if boundary == 0 else "short"),
            "meets_boundary_coverage": bool(
                boundary >= max(1, int(math.floor(
                    CFG.review_boundary_share * required * 0.8)))
                or boundary == 0)})
    table = pd.DataFrame(report)
    if table.empty:
        out["reason"] = "no audited cases matched the key file"
        return out

    # A bound that does not exist cannot satisfy a ceiling. NaN is not <= x.
    table["error_bounds_ok"] = (
        (table["false_pass_upper"] <= table["ceiling"])
        & (table["false_fail_upper"] <= table["ceiling"])).fillna(False)
    table["passes"] = (table["class_support_ok"] & table["meets_boundary_coverage"]
                       & (table["kappa"] >= CFG.verifier_kappa_floor)
                       & table["error_bounds_ok"])

    tier2 = merged.query("tier == 'tier2'")
    pooled = _class_bounds(tier2["auto_binary_pass"].to_numpy(),
                           tier2["human_pass"].to_numpy()) if len(tier2) else {}
    pooled_ok = bool(
        pooled
        and pooled["n_true_fail"] >= CASES_PER_TRUTH_CLASS
        and pooled["n_true_pass"] >= CASES_PER_TRUTH_CLASS
        and pooled["false_pass_upper"] <= CFG.verifier_error_ceiling
        and pooled["false_fail_upper"] <= CFG.verifier_error_ceiling)
    pooled["passes"] = pooled_ok
    pooled["required_per_class"] = CASES_PER_TRUTH_CLASS
    pooled["ceiling"] = CFG.verifier_error_ceiling

    expected_units = set(TIER1_IDS) | set(TIER2_STRATA)
    missing = sorted(expected_units - set(table["audit_unit"]))
    class_short = sorted(table.query("not class_support_ok")["audit_unit"])
    reliability_failed = sorted(
        table.query("class_support_ok and not error_bounds_ok")["audit_unit"])

    out["table"] = table
    out["pooled"] = pooled
    out["missing_units"] = missing
    out["class_short_units"] = class_short
    out["reliability_failed_units"] = reliability_failed
    out["passed"] = bool(table["passes"].all() and not missing
                         and (pooled_ok or not CFG.require_pooled_system_ceiling))

    if out["passed"]:
        out["status"], out["reason"] = GateStatus.PASS, "every audit unit met its criteria"
    elif missing:
        out["status"] = GateStatus.AUDIT_MISSING
        out["reason"] = f"{len(missing)} audit units have no adjudicated cases"
    elif reliability_failed:
        # A demonstrated defect. More labels cannot move a bound that is already
        # above the ceiling with an adequate denominator.
        out["status"] = GateStatus.VERIFIER_RELIABILITY_FAILED
        out["reason"] = f"{len(reliability_failed)} units exceeded their error ceiling"
    elif class_short:
        out["status"] = GateStatus.AUDIT_CLASS_SUPPORT_INSUFFICIENT
        out["reason"] = (f"{len(class_short)} units lack enough adjudicated cases "
                         "in one truth class to certify a conditional rate")
    elif CFG.require_pooled_system_ceiling and not pooled_ok:
        out["status"] = GateStatus.AUDIT_UNDERPOWERED
        out["reason"] = "the pooled tier-2 system certificate is not established"
    else:
        out["status"] = GateStatus.AUDIT_UNDERPOWERED
        out["reason"] = "the audit does not yet support the declared ceilings"
    return out


AUDIT_LABEL_BUDGET = {
    "tier1_units": len(TIER1_IDS),
    "tier1_labels": len(TIER1_IDS) * 2 * CASES_PER_TRUTH_CLASS,
    "tier2_strata": len(TIER2_STRATA),
    "tier2_labels": len(TIER2_STRATA) * 2 * STRATUM_CASES_PER_TRUTH_CLASS,
    "total_labels": (len(TIER1_IDS) * 2 * CASES_PER_TRUTH_CLASS
                     + len(TIER2_STRATA) * 2 * STRATUM_CASES_PER_TRUTH_CLASS),
    "strict_per_implementation_alternative": (
        (len(TIER1_IDS) + len(TIER2_STRATA)) * 2 * CASES_PER_TRUTH_CLASS),
    "v14_per_constraint_at_v14_size": len(SELECTABLE_IDS) * VERIFIER_AUDIT_SIZE,
}

print(f"""Measurement architecture
  selectable constraints      : {len(SELECTABLE_IDS)}
  distinct implementations    : {len(set(VERIFIER_IMPLEMENTATION[c] for c in SELECTABLE_IDS))}
  tier 1 (individually, {CFG.verifier_error_ceiling:.0%})  : {list(TIER1_IDS)} at {CASES_PER_TRUTH_CLASS} per truth class
  tier 2 ({len(TIER2_STRATA)} strata, {CFG.stratum_error_ceiling:.0%})  : {STRATUM_CASES_PER_TRUTH_CLASS} per truth class, pooled at {CFG.verifier_error_ceiling:.0%}
  human labels required       : {AUDIT_LABEL_BUDGET['total_labels']}
  strict per-implementation alternative: {AUDIT_LABEL_BUDGET['strict_per_implementation_alternative']} labels

Every selectable constraint is covered by an audited unit. Reviewers see the
rule and the response only: the automatic verdict, the stratum, the tier and
the constraint identity live in a separate key file.""")
