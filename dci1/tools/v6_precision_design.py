"""What Gate 4's verdict is measured with, and what a Gate-2.75 margin has to
absorb --- computed from the closed v5 record rather than assumed.

**Classification: DEVELOPMENT_EVIDENCE.** This reads v5 for *precision* only.
No effect quantity is estimated, compared or interpreted; no v5 verdict is
recomputed as a verdict; the four terminal statuses stand exactly as signed.
Per §30's precedent anything fitted here is prospectively tested by v6 and v6
may not claim it generalises.

Four questions, in the order the readiness memo's R2/R3/R5 chain needs them.

1. **How precise is one Gate-4 entry?** §13.14 takes a hard binary verdict
   against a fixed band on ``N_COMPOSED`` topics x ``M_CAL`` draws. The
   sampling unit is the *topic*, so what sets the precision is the
   between-topic variance of a topic's own M-draw compliance --- which the
   retained Gate-4 rows measure directly, on every cell x slot entry of all
   four replications.

2. **Is the calibration-to-composed "split transfer" a bias, or is it that
   same precision seen twice?** §6.2 cuts the pre-screen, calibration,
   composed, confirmatory and sequestered sets out of **one seeded per-area
   shuffle** (``dci1v4.topics.split.cut_area``), so the composed set and the
   calibration set are exchangeable draws from one stratified population and
   there is no systematic difference between them to absorb. That is a design
   property; this tool checks it against the realised movement instead of
   asserting it, by comparing the observed variance of the thirteen realised
   transfers with the sampling variance the two sample sizes imply.

3. **How often would Gate 4 terminate a replication that is in band?** A
   joint topic bootstrap over each replication's own realised entries ---
   joint because the entries share one topic set, so their sampling errors
   are not independent and a per-entry rate would understate the family.

4. **What, then, is left for a margin to cover?** Whatever survives (2), plus
   the stand-in-to-reference term for entries whose instrument does not exist
   when the probe runs. The two are reported separately because no lever
   moves both.

Nothing here chooses a value. It computes the table the choice has to be made
against, and it refuses to report anything unless its own baseline reproduces
the signed Gate-4 headroom tables and the signed terminal reports exactly.
"""
from __future__ import annotations

import json
import math
import random
import statistics as st
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v5.engine import context as ctx                    # noqa: E402
from dci1v5.engine import transitions                       # noqa: E402
from dci1v5.engine.paths import model_tree                  # noqa: E402
from dci1v6.protocol import constants as C                  # noqa: E402
from dci1v6.topics.bank import load_bank                    # noqa: E402

OUT = DCI1 / "reports" / "dci1v6" / "precision_design.json"
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")
#: §13.7's registered resample count, reused so the bootstrap here is the one
#: the protocol already runs rather than a second convention.
RESAMPLES = C.STABILITY_BOOTSTRAP_RESAMPLES
#: A fixed seed, because a design table that moves between runs is not one.
BOOTSTRAP_SEED = 20260825
#: §13.4's registered confidence level, as the z it is applied through.
Z_95 = 1.959963984540054
#: The composed-set sizes §6.2's per-area cut can express: `COMPOSED_PER_AREA`
#: is an integer per stratum, so the reachable sizes are its multiples.
CANDIDATE_PER_AREA = (2, 3, 4, 6, 8, 10)


def _tree(model_key: str):
    return model_tree(ctx.registered_context(), model_key)


def _rows(model_key: str, stage: str, run: str) -> list[dict[str, Any]]:
    path = _tree(model_key).backend_runs(stage) / run / "scored.jsonl"
    with path.open() as handle:
        return [json.loads(line) for line in handle]


def _per_topic(rows: Sequence[dict[str, Any]], cell_id: str, *,
               slot: str | None = None, kind: str | None = None,
               severity: int | None = None) -> dict[str, float]:
    """topic -> that topic's compliance, averaged over draws.

    The same match §13.14's own table uses --- a *present* score of the bound
    instrument --- keyed so that a cell carrying two constraints yields two
    entries rather than one pooled number.
    """
    acc: dict[str, list[float]] = {}
    for row in rows:
        if row["cell_id"] != cell_id:
            continue
        for score in row["scores"]:
            if not score["present"]:
                continue
            if slot is not None and score.get("slot") != slot:
                continue
            if kind is not None and (score["kind"] != kind
                                     or score["severity"] != severity):
                continue
            acc.setdefault(row["topic_id"], []).append(float(score["passed"]))
    return {t: sum(v) / len(v) for t, v in acc.items()}


def _moments(values: Iterable[float]) -> dict[str, float]:
    vals = list(values)
    n = len(vals)
    p = sum(vals) / n
    s2 = st.variance(vals) if n > 1 else 0.0
    return {"n_topics": n, "p": p, "s2_topic": s2, "se": math.sqrt(s2 / n)}


def _icc(p: float, s2: float, draws: int) -> float | None:
    """The topic-level intraclass correlation ``s2`` implies.

    Var(topic mean of M draws) = p(1-p)(1 + (M-1)rho)/M. Reported because it
    is the one number that says whether topics or draws are the scarce
    resource: at rho = 0 more draws would buy precision, at rho = 1 only more
    topics can.
    """
    denom = p * (1.0 - p)
    if denom <= 0:
        return None
    return (draws * s2 / denom - 1.0) / (draws - 1)


# ------------------------------------------------------- 1. Gate-4 precision

def _entries_for(model_key: str) -> list[dict[str, Any]]:
    rows = _rows(model_key, C.STAGE_GATE4, "composed")
    slots_by_cell: dict[str, set[str]] = {}
    for row in rows:
        present = {s["slot"] for s in row["scores"]
                   if s["present"] and s.get("slot")}
        slots_by_cell.setdefault(row["cell_id"], set()).update(present)
    entries = []
    for cell_id in sorted(slots_by_cell):
        for slot in sorted(slots_by_cell[cell_id]):
            topics = _per_topic(rows, cell_id, slot=slot)
            moments = _moments(topics.values())
            entries.append({
                "cell": cell_id, "slot": slot, **moments,
                "icc": _icc(moments["p"], moments["s2_topic"], C.M_CAL),
                "in_band": (C.COMPOSED_HEADROOM_BAND[0] <= moments["p"]
                            <= C.COMPOSED_HEADROOM_BAND[1]),
                "_topic_values": [topics[t] for t in sorted(topics)],
            })
    return entries


def _check_baseline(model_key: str, entries: Sequence[dict[str, Any]]) -> int:
    """Reproduce the signed verdict, or refuse to report anything."""
    tree = _tree(model_key)
    computed = {(e["cell"], e["slot"]): e["p"] for e in entries}
    checked = 0
    try:
        record = transitions.read_stage_record(tree, C.STAGE_GATE4)
    except Exception:
        record = None
    if record is not None:
        for cell_id, entry in record["headroom_table"].items():
            for slot, value in entry.items():
                if slot == "unconstrained":
                    continue
                got = computed.get((cell_id, slot))
                if got is None or abs(got - float(value)) > 1e-9:
                    raise SystemExit(
                        f"{model_key} {cell_id}/{slot}: recomputed {got} "
                        f"against the signed {value}")
                checked += 1
        return checked
    # The two replications that raised wrote no Gate-4 record. Their signed
    # terminal report carries the failing entries and those must reproduce.
    path = tree.root / "terminal_report.json"
    report = json.loads(path.read_text())
    observed = (report.get("payload") or report).get("observed") or []
    if not observed:
        raise SystemExit(f"{model_key}: nothing signed to check against")
    for failure in observed:
        got = computed.get((failure["cell"], failure["slot"]))
        if got is None or abs(got - float(failure["compliance"])) > 1e-9:
            raise SystemExit(
                f"{model_key} {failure['cell']}/{failure['slot']}: recomputed "
                f"{got} against the signed {failure['compliance']}")
        checked += 1
    return checked


def gate4_precision(per_model_entries: dict[str, list[dict[str, Any]]]
                    ) -> dict[str, Any]:
    flat = [e for entries in per_model_entries.values() for e in entries]
    iccs = [e["icc"] for e in flat if e["icc"] is not None]
    ses = [e["se"] for e in flat]
    upper = [e for e in flat if e["p"] >= 0.75]
    return {
        "_question": "how precise is one §13.14 cell x slot entry?",
        "n_entries": len(flat),
        "n_topics": C.N_COMPOSED, "draws": C.M_CAL,
        "sampling_unit": "the topic; draws within a topic are correlated and "
                         "M_CAL of them do not make M_CAL independent "
                         "observations",
        "se_median": st.median(ses), "se_mean": sum(ses) / len(ses),
        "se_max": max(ses),
        "se_median_upper_region": (st.median([e["se"] for e in upper])
                                   if upper else None),
        "n_entries_upper_region": len(upper),
        "icc_median": st.median(iccs) if iccs else None,
        "icc_mean": (sum(iccs) / len(iccs)) if iccs else None,
        "what_icc_says": "rho is the fraction of a topic's compliance that is "
                         "the topic rather than the draw. At the measured rho "
                         "the fourth draw buys little and only topics buy "
                         "precision, which is why every policy below moves "
                         "N_COMPOSED and none moves M_CAL",
        "per_model": {
            m: {"n_entries": len(entries),
                "entries": [{k: v for k, v in e.items()
                             if not k.startswith("_")} for e in entries]}
            for m, entries in per_model_entries.items()},
    }


# ------------------------------------------------------ 2. the split transfer

def split_transfer(per_model_entries: dict[str, list[dict[str, Any]]]
                   ) -> dict[str, Any]:
    """Bias, or the same sampling error seen from both sides?"""
    memo = json.loads(
        (DCI1 / "reports/dci1v6/readiness_evidence.json").read_text())
    observations = []
    for obs in memo["split_transfer"]["observations"]:
        model_key = obs["model_key"]
        kind, severity = obs["instrument"].split(":")
        severity = int(severity)
        composed = next(e for e in per_model_entries[model_key]
                        if e["cell"] == f"solo:{obs['slot']}"
                        and e["slot"] == obs["slot"])
        calibration = None
        for run in ("grid-A", "grid-B", "candidates"):
            try:
                rows = _rows(model_key, C.STAGE_GATE2, run)
            except FileNotFoundError:
                continue
            topics = _per_topic(rows, f"solo:{kind}:{severity}",
                                kind=kind, severity=severity)
            if topics:
                calibration = _moments(topics.values())
                break
        if calibration is None:
            raise SystemExit(f"{model_key}: no calibration rows for "
                             f"{obs['instrument']}")
        transfer = composed["p"] - calibration["p"]
        if abs(transfer - obs["transfer"]) > 1e-9:
            raise SystemExit(
                f"{model_key} {obs['instrument']}: recomputed transfer "
                f"{transfer} against the memo's {obs['transfer']}")
        observations.append({
            "model_key": model_key, "instrument": obs["instrument"],
            "slot": obs["slot"], "p_calibration": calibration["p"],
            "p_composed": composed["p"], "transfer": transfer,
            "n_calibration": calibration["n_topics"],
            "n_composed": composed["n_topics"],
            "var_sampling": (calibration["s2_topic"] / calibration["n_topics"]
                             + composed["s2_topic"] / composed["n_topics"]),
            "s2_calibration": calibration["s2_topic"],
            "s2_composed": composed["s2_topic"],
        })
    transfers = [o["transfer"] for o in observations]
    sampling = [o["var_sampling"] for o in observations]
    n = len(transfers)
    var_observed = st.variance(transfers)
    var_sampling = sum(sampling) / n
    residual = var_observed - var_sampling
    # A chi-square upper bound on the total, so the residual is reported with
    # its own uncertainty rather than as a point estimate of zero.
    upper_total = var_observed * (n - 1) / _chi2_lower_tail(n - 1, 0.05)
    by_model = {m: st.mean([o["transfer"] for o in observations
                            if o["model_key"] == m]) for m in MODELS}
    return {
        "_question": "is the calibration -> composed movement a bias, or the "
                     "sampling error of a 24-topic verdict?",
        "design_property": (
            "§6.2 cuts all five sets from ONE seeded per-area shuffle "
            "(dci1v4.topics.split.cut_area), so the composed and calibration "
            "sets are exchangeable draws from one stratified population. "
            "There is no systematic difference between them for a margin to "
            "absorb; what a margin would be absorbing is sampling error."),
        "n_observations": n,
        "observations": observations,
        "mean_transfer": sum(transfers) / n,
        "mean_absolute_transfer": sum(abs(t) for t in transfers) / n,
        "max_absolute_transfer": max(abs(t) for t in transfers),
        "variance_observed": var_observed,
        "variance_expected_from_sampling": var_sampling,
        "residual_point_estimate": residual,
        "residual_sd_point_estimate": math.sqrt(residual) if residual > 0
                                      else 0.0,
        "residual_upper_95": max(0.0, upper_total - var_sampling),
        "residual_sd_upper_95": math.sqrt(max(0.0, upper_total - var_sampling)),
        "mean_transfer_by_model": by_model,
        "why_by_model": "all instruments of one replication share one composed "
                        "topic set, so a real set effect would appear as a "
                        "common per-model shift and not as instrument noise",
        "verdict": ("consistent with sampling" if residual <= 0 else
                    "a residual component survives"),
        "caveat": "thirteen observations, all solo cells, on four "
                  "replications. This bounds the residual; it does not "
                  "measure a small one precisely.",
    }


# ----------------------------------- 2b. the one component that is not sampling

def authored_subsplit(per_model_entries: dict[str, list[dict[str, Any]]]
                      ) -> dict[str, Any]:
    """calibration_a against calibration_b, paired by instrument.

    **This is the only structural threat to exchangeability and it is
    measurable in-stage.** §6.2 cuts the pre-screen, calibration_a, composed,
    confirmatory and sequestered sets from one seeded per-area shuffle, so
    calibration_a and the composed set are exchangeable by construction ---
    but §34 D3's ``calibration_b`` is **newly authored**, not part of that
    cut, and it supplies half of the 192 topics the probe would measure on.
    A probe that predicts a composed-set value from the pooled calibration
    mean therefore carries half of whatever difference the authored half
    introduces.

    The contrast is paired, same instrument, same stage, same draws, so it
    isolates that difference from everything else. It is the quantity §34
    D20's ``calibration_with_measured_transfer`` branch puts on the record,
    and the variance component it identifies is what a residual margin --- and
    nothing else --- has to cover.
    """
    memo = json.loads(
        (DCI1 / "reports/dci1v6/readiness_evidence.json").read_text())
    observations = []
    for obs in memo["split_transfer"]["observations"]:
        model_key = obs["model_key"]
        kind, severity = obs["instrument"].split(":")
        severity = int(severity)
        acc: dict[str, dict[str, list[float]]] = {}
        for run in ("grid-A", "grid-B", "candidates"):
            try:
                rows = _rows(model_key, C.STAGE_GATE2, run)
            except FileNotFoundError:
                continue
            for row in rows:
                if row["cell_id"] != f"solo:{kind}:{severity}":
                    continue
                for score in row["scores"]:
                    if (score["present"] and score["kind"] == kind
                            and score["severity"] == severity):
                        (acc.setdefault(row["topic_split"], {})
                            .setdefault(row["topic_id"], [])
                            .append(float(score["passed"])))
            if acc:
                break
        if set(acc) != {C.CALIBRATION_A, C.CALIBRATION_B}:
            raise SystemExit(f"{model_key} {obs['instrument']}: the two "
                             f"calibration sub-splits are {sorted(acc)}")
        halves = {name: _moments([sum(v) / len(v) for v in per.values()])
                  for name, per in acc.items()}
        a, b = halves[C.CALIBRATION_A], halves[C.CALIBRATION_B]
        observations.append({
            "model_key": model_key, "instrument": obs["instrument"],
            "slot": obs["slot"],
            "p_calibration_a": a["p"], "p_calibration_b": b["p"],
            "a_minus_b": a["p"] - b["p"],
            "n_a": a["n_topics"], "n_b": b["n_topics"],
            "var_sampling": (a["s2_topic"] / a["n_topics"]
                             + b["s2_topic"] / b["n_topics"]),
        })
    diffs = [o["a_minus_b"] for o in observations]
    n = len(diffs)
    var_observed = st.variance(diffs)
    var_sampling = sum(o["var_sampling"] for o in observations) / n
    residual = max(0.0, var_observed - var_sampling)
    return {
        "_question": "how far apart are the split-derived and the newly "
                     "authored halves of the calibration set, on the same "
                     "instrument?",
        "why_it_matters":
            "calibration_a and the composed set come from one seeded per-area "
            "shuffle and are exchangeable. calibration_b is authored under "
            "§34 D3 and is not. A probe measuring on the pooled 192 predicts "
            "a composed value that is calibration_a-like, so it carries HALF "
            "of the authored half's instrument-specific offset --- and that "
            "half is the entire non-sampling term in the error budget.",
        "n_observations": n,
        "observations": observations,
        "mean_a_minus_b": sum(diffs) / n,
        "mean_absolute_a_minus_b": sum(abs(d) for d in diffs) / n,
        "max_absolute_a_minus_b": max(abs(d) for d in diffs),
        "variance_observed": var_observed,
        "variance_expected_from_sampling": var_sampling,
        "residual_variance": residual,
        "residual_sd": math.sqrt(residual),
        "carried_by_a_pooled_probe": {
            "factor": 0.5,
            "sd": math.sqrt(residual) / 2,
            "variance": residual / 4,
            "why": "pooled = (a + b)/2, and the composed set is a-like, so "
                   "the offset a pooled estimate carries is (b - a)/2",
        },
        "measured_in_stage_under_d20":
            "§34 D20's calibration_with_measured_transfer branch has the "
            "probe measure every cell on BOTH sub-splits, so this quantity is "
            "recorded per entry at the moment the margin is applied instead "
            "of being assumed from this table",
    }


def _chi2_lower_tail(df: int, alpha: float) -> float:
    """The chi-square quantile at ``alpha``, by bisection on the CDF.

    Written out rather than imported: this repository's runtime carries no
    scipy, and a design table that depends on an optional dependency is a
    design table that stops reproducing.
    """
    def cdf(x: float) -> float:
        # Regularised lower incomplete gamma P(df/2, x/2), series form.
        k, half = df / 2.0, x / 2.0
        if half <= 0:
            return 0.0
        term = 1.0 / k
        total = term
        for i in range(1, 2000):
            term *= half / (k + i)
            total += term
            if term < 1e-16 * total:
                break
        return total * math.exp(-half + k * math.log(half)
                                - math.lgamma(k))
    low, high = 1e-9, float(df) * 10 + 50
    for _ in range(200):
        mid = (low + high) / 2
        if cdf(mid) < alpha:
            low = mid
        else:
            high = mid
    return (low + high) / 2


# ------------------------------------------- 3. how often Gate 4 would fire

def false_termination(per_model_entries: dict[str, list[dict[str, Any]]],
                      *, sizes: Sequence[int]) -> dict[str, Any]:
    """P(some entry leaves §13.14's band) under a joint topic bootstrap.

    Joint, because one replication's entries are measured on **one** topic
    set: resampling each entry independently would treat correlated errors as
    independent and understate the rate the replication actually faces.

    Sizes above ``N_COMPOSED`` resample with replacement from the 24 topics
    that exist, so they carry the variance of those topics and not of the
    topics an enlarged set would add. That is an extrapolation and is
    labelled as one.
    """
    low, high = C.COMPOSED_HEADROOM_BAND
    out: dict[str, Any] = {}
    for model_key, entries in per_model_entries.items():
        columns = [e["_topic_values"] for e in entries]
        n_have = len(columns[0])
        per_size = {}
        for size in sizes:
            rng = random.Random(BOOTSTRAP_SEED)
            fired = 0
            for _ in range(RESAMPLES):
                idx = [rng.randrange(n_have) for _ in range(size)]
                for column in columns:
                    value = sum(column[i] for i in idx) / size
                    if not (low <= value <= high):
                        fired += 1
                        break
            per_size[str(size)] = fired / RESAMPLES
        out[model_key] = {
            "n_entries": len(entries),
            "entries_outside_band_as_measured":
                sum(1 for e in entries if not e["in_band"]),
            "p_some_entry_outside_band": per_size,
        }
    return {
        "_question": "how often does a 24-topic verdict fire on a replication "
                     "whose entries are where v5 measured them?",
        "method": f"joint topic bootstrap, {RESAMPLES} resamples, seed "
                  f"{BOOTSTRAP_SEED}, over each replication's own realised "
                  "entries",
        "registered_size": C.N_COMPOSED,
        "sizes": list(sizes),
        "extrapolation_warning":
            "sizes above N_COMPOSED resample the 24 topics that exist; they "
            "show the sampling arithmetic, not the topics an enlarged set "
            "would contain",
        "per_model": out,
        "reading": "the rate at the realised entry counts (6 to 45). The "
                   "full five-arm set audits 95 entries and no replication "
                   "ran it, so that rate is not measurable from v5.",
    }


# -------------------------------------------------- 4. what a margin covers

def policies(transfer: dict[str, Any],
             precision: dict[str, Any]) -> dict[str, Any]:
    """Every composed-set size §6.2's cut can express, and what each buys.

    ``materialised`` is the load-bearing column. §6.2's sequestered eighth
    exists in this repository **only as opaque identities** --- ``load_bank``
    carries zero sequestered questions and ``topic_hash`` says why --- so a
    policy that takes topics from it is not a change to a constant. It
    requires authoring topics that do not exist.
    """
    bank = load_bank()
    materialised_spare = len(bank.sets.get("sequestered", ()))
    s2 = st.mean([o["s2_composed"] for o in transfer["observations"]])
    s2_cal = st.mean([o["s2_calibration"] for o in transfer["observations"]])
    residual = max(0.0, transfer["residual_point_estimate"])
    rows = []
    for per_area in CANDIDATE_PER_AREA:
        n_composed = per_area * C.N_AREAS
        spent = (C.N_PRESCREEN + C.N_CALIBRATION + n_composed
                 + C.N_CONFIRMATORY)
        sequestered = C.N_TOPICS - spent
        extra = n_composed - C.N_COMPOSED
        var = residual + s2_cal / C.N_CALIBRATION + s2 / n_composed
        rows.append({
            "composed_per_area": per_area,
            "n_composed": n_composed,
            "n_sequestered_nominal": sequestered,
            "topics_that_must_be_authored": max(0, extra - materialised_spare),
            "materialisable_today": extra <= materialised_spare,
            "se_of_one_entry": math.sqrt(s2 / n_composed),
            "sd_of_the_transfer": math.sqrt(var),
            "delta_per_entry_95": Z_95 * math.sqrt(var),
            "delta_familywise_95_over_6": _z(0.05 / (2 * 6)) * math.sqrt(var),
            "gate4_rows_per_cell": n_composed * C.M_CAL,
        })
    return {
        "_question": "which composed-set sizes exist, and what does each do "
                     "to the quantity a margin would have to cover?",
        "materialised_sequestered_topics": materialised_spare,
        "sequestered_use": "§6.2: a future uncontaminated rerun only. The "
                           "eighth was never materialised in this repository, "
                           "so enlarging the composed set from it means "
                           "authoring topics, which is a governed bank change",
        "s2_composed_mean": s2, "s2_calibration_mean": s2_cal,
        "residual_used": residual,
        "delta_ceiling_from_registered_constants":
            C.COMPOSED_HEADROOM_BAND[1] - C.FOCAL_AIM,
        "why_that_ceiling":
            "a margin wider than 0.95 - FOCAL_AIM refuses, on its solo B cell "
            "alone and before any composition, an operating point sitting "
            "exactly where §12.3 aims. A probe that refuses the registered "
            "aim is not a feasibility check",
        "familywise_k": 6,
        "why_k_is_6": "§13.14's verdict is a conjunction over entries, so a "
                      "margin meant to make a probe pass IMPLY a Gate-4 pass "
                      "is family-wise over the entries it covers. Six is the "
                      "base arm's entry count: solo:A, solo:B and both "
                      "orders of A with B, which are the only Gate-4 entries "
                      "whose instruments both exist when the probe runs",
        "rows": rows,
    }


def _z(tail: float) -> float:
    """The standard-normal quantile at ``1 - tail``, by bisection."""
    def cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    low, high = 0.0, 10.0
    for _ in range(200):
        mid = (low + high) / 2
        if cdf(mid) < 1.0 - tail:
            low = mid
        else:
            high = mid
    return (low + high) / 2


# ------------------------------- 5. what the derived rule does to m*

def operating_point_feasibility() -> dict[str, Any]:
    """Would any operating point survive the rule, on the four closed curves?

    A design rule that no replication can satisfy is not conservative, it is
    broken, and that is not a thing to discover after registration. This
    applies ``composed_probe``'s **own** determinate test to each
    replication's measured solo-B curve and to that severity's own
    between-topic variance --- ``solo:B`` is a determinate entry, so this is
    the production rule and not a model of it.

    It is a statement about the RULE, computed on development evidence. It is
    not a re-verdict, not a claim that the rule would have saved anything, and
    not evidence that it generalises: §30's precedent applies and v6 tests it
    prospectively.
    """
    from dci1v6.stages import composed_probe

    out: dict[str, Any] = {}
    for model_key in MODELS:
        record = transitions.read_stage_record(_tree(model_key), C.STAGE_GATE2)
        rows = _rows(model_key, C.STAGE_GATE2, "grid-B")
        per_severity: dict[str, Any] = {}
        for severity in sorted({s["severity"] for row in rows
                                for s in row["scores"]
                                if s["present"] and s["kind"] == "B"}):
            topics = _per_topic(rows, f"solo:B:{severity}", kind="B",
                                severity=severity)
            moments = _moments(topics.values())
            verdict = composed_probe.entry_verdict(
                {"compliance": moments["p"], "s2_topic": moments["s2_topic"],
                 "n_topics": moments["n_topics"]},
                cell_id="solo:B", slot="B", cell_slots=("B",),
                residual_sd=0.0)
            per_severity[str(severity)] = {
                "compliance": moments["p"], "s2_topic": moments["s2_topic"],
                "half_width": verdict["half_width"],
                "half_width_familywise": verdict["half_width_familywise"],
                "passes": verdict["passes"],
                "passes_familywise": verdict["passes_familywise"]}
        passing = sorted(int(q) for q, v in per_severity.items()
                         if v["passes"])
        out[model_key] = {
            "m_star": int(record["m_star"]),
            "m_star_passes": bool(per_severity[str(record["m_star"])]
                                  ["passes"]),
            # Counterfactual since 2026-08-26: m* is frozen at Gate 2 and v6
            # measures composed headroom at m* alone, so no v6 rule reads
            # these. Recorded so the frozen m* can be read against its own
            # curve.
            "counterfactual_passing_severities": passing,
            "per_severity": per_severity}
    return {
        "_question": "applied to the closed v5 solo-B curves, does the "
                     "derived determinate rule pass at the frozen m*?",
        "_not_a_re_verdict":
            "v5's records, verdicts and terminal statuses stand exactly as "
            "signed. This applies a v6 rule to a v5 measurement and says "
            "nothing about what v5 should have done",
        "residual_used": 0.0,
        "residual_note": "0.0, so this isolates the projection from §34 D23's "
                         "reading and §34 D26's magnitude. That isolation is "
                         "deliberate and it is also a LIMIT: this table "
                         "establishes feasibility at one value only, and the "
                         "2026-08-26 red team observed that the value it "
                         "establishes it at is the one it was used to "
                         "justify. `reports/dci1v6/residual_sensitivity.json` "
                         "sweeps the others",
        "swept_elsewhere": "reports/dci1v6/residual_sensitivity.json",
        "_the_operating_point_is_frozen":
            "m* is selected once, by §12.3 at GATE_2_FOCAL_CALIBRATION, and "
            "GATE_2_75_COMPOSED_PROBE cannot move it (researcher decision, "
            "2026-08-26). So the question this table answers is whether the "
            "FROZEN m* passes; `counterfactual_passing_severities` is "
            "recorded and read by nothing",
        "per_model": out,
        "every_frozen_m_star_passes":
            all(v["m_star_passes"] for v in out.values()),
        "replications_whose_frozen_m_star_fails": sorted(
            k for k, v in out.items() if not v["m_star_passes"]),
    }


def main() -> None:
    per_model_entries = {m: _entries_for(m) for m in MODELS}
    checks = sum(_check_baseline(m, e) for m, e in per_model_entries.items())
    precision = gate4_precision(per_model_entries)
    transfer = split_transfer(per_model_entries)
    payload = {
        "_what": "the precision design behind READINESS R2, R3 and R5",
        "_classification": "DEVELOPMENT_EVIDENCE",
        "_reads": "signed v5 stage records and the scored rows they were "
                  "computed from; hash and signature verified on read",
        "_not_evidence_about": [
            "Delta_j, Delta_R or Xi",
            "whether any v5 replication should have passed Gate 4",
            "anything a v5 terminal status says or does not say",
        ],
        "_baseline_checks_against_signed_records": checks,
        "gate4_precision": precision,
        "split_transfer": transfer,
        "authored_subsplit": authored_subsplit(per_model_entries),
        "false_termination": false_termination(
            per_model_entries, sizes=(24, 48, 96, 192)),
        "policies": policies(transfer, precision),
        "operating_point_feasibility": operating_point_feasibility(),
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(f"{OUT}  ({checks} baseline checks against signed records)")


if __name__ == "__main__":
    main()
