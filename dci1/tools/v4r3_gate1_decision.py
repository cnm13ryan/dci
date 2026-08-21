"""The Gate-1 decision for the final R3 instrument population, from evidence.

Nothing here is a new measurement. It reads the artifacts the registered
pathways already wrote, recomputes each registered rate from the stored rows
rather than trusting a stored summary, and applies §18 stage 4's rule --- §10.2
for every instrument in the declared range, **plus §10.3 or §10.4** --- to
whatever those recomputations say.

Three things it deliberately does not do. It does not average the evidence
sources into one accuracy; §10.5 keeps three questions apart and this keeps
seven sources apart. It does not treat the absence of a disagreement as a
validation; `vacuity_ignored` changes no verdict in the whole natural corpus,
which makes natural-response agreement uninformative about that convention
rather than supportive of it. And it does not write a measurement basis:
§10.4-R2 ends in the researcher's signature and no program may forge it.

    python3 tools/v4r3_gate1_decision.py
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))
sys.path.insert(0, str(DCI1 / "tools"))

from dci1v4r3 import CLASSIFICATION                              # noqa: E402
from dci1v4r3.protocol.wordings import wordings                  # noqa: E402
from dci1v4r3.stages.human_review import wilson_upper            # noqa: E402
from dci1v4r3.stages.microcase import build_cases, split_cases   # noqa: E402
from dci1v4r3.verifiers import verifier_source_hash              # noqa: E402
from dci1v4r3.verifiers.constraints import (                     # noqa: E402
    FAMILIES, FORM_EXACT, declared_range,
)

import gate1_microcase_v4r3 as MC                                # noqa: E402

REPORTS = DCI1 / "reports" / "dci1v4r3"
OUT_R2 = REPORTS / "section_10_4R2_outcome.json"
OUT_GATE = REPORTS / "gate1_decision.json"

WORD = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*")
#: the numeral 1 followed immediately by a plural noun: "1 semicolons".
PLURAL_AFTER_ONE = re.compile(r"\b1\s+([a-z]+(?:s|es))\b")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=DCI1,
                          capture_output=True, text=True,
                          check=False).stdout.strip()


def _load(name: str) -> dict[str, Any]:
    return json.loads((REPORTS / name).read_text())


# ------------------------------------------------------------------ §10.4-R2

def r2_outcome() -> dict[str, Any]:
    """The R2 pathway's terminal outcome, recomputed from the judged rows."""
    run = _load("section_10_4R2_development_mc-medium_rep0.json")
    rows = run["rows"]
    metrics = MC.evaluate(rows)                 # recomputed, not read back
    verdict = MC.verdict(metrics)               # criterion 6 has no replicate
    cases = {c.case_id: c for c in build_cases()}
    halves = split_cases(build_cases())

    # A discrepancy found while attributing the failure, recorded rather than
    # repaired: §10.4-R2 defines sensitivity as "agreement on cases the
    # verifier records as **not satisfied**", and the overall figure is
    # computed that way, but the per-kind figure is computed over every parsed
    # discriminating case in the deciding arm, satisfied ones included. On a
    # satisfied case that separates a defect, agreement is a refused false
    # alarm --- the specificity side. The verdict is invariant under the two
    # readings and only `denominator_swap` fails either, so this is a note for
    # the next R2-style run and not a re-verdict of this one.
    parsed = [r for r in rows if r["status"] == MC.VALID]
    reading_check: dict[str, Any] = {}
    for defect in MC.DEFECT_KINDS:
        arm = MC.ARM_OF_DEFECT[defect]
        wide = [r for r in parsed
                if r["arm"] == arm and defect in r["discriminates"]]
        narrow = [r for r in wide if not r["correct"]]
        floor = MC.THRESHOLDS["sensitivity_per_kind_min"]
        least = MC.THRESHOLDS["per_kind_min_items"]

        def _cell(items: list[dict[str, Any]]) -> dict[str, Any]:
            agreed = sum(1 for r in items if r["agrees"])
            rate = agreed / len(items) if items else None
            return {"n": len(items), "agreed": agreed, "sensitivity": rate,
                    "below_floor": bool(len(items) >= least
                                        and rate is not None and rate < floor)}
        reading_check[defect] = {"as_implemented": _cell(wide),
                                 "as_section_10_4R2_words_it": _cell(narrow)}
    reading_check["verdict_is_invariant"] = (
        sorted(k for k, v in reading_check.items()
               if isinstance(v, dict) and "as_implemented" in v
               and v["as_implemented"]["below_floor"])
        == sorted(k for k, v in reading_check.items()
                  if isinstance(v, dict) and "as_implemented" in v
                  and v["as_section_10_4R2_words_it"]["below_floor"]))

    # Why criterion 5 failed, attributably: which of the deciding arm's items
    # turn on a convention that arm does not state.
    attribution: dict[str, Any] = {}
    for defect in MC.DEFECT_KINDS:
        arm = MC.ARM_OF_DEFECT[defect]
        items = [r for r in rows if r["arm"] == arm
                 and defect in r["discriminates"]
                 and r["status"] == MC.VALID and not r["correct"]]
        wordless = [r for r in items if not WORD.findall(cases[r["case_id"]].text)]
        other = [MC.evaluate([r for r in rows if r["arm"] != arm
                              and defect in r["discriminates"]
                              and r["status"] == MC.VALID and not r["correct"]])]
        attribution[defect] = {
            "deciding_arm": arm,
            "items": len(items),
            "agreed": sum(1 for r in items if r["agrees"]),
            "items_whose_answer_has_no_words": len(wordless),
            "agreed_on_those": sum(1 for r in wordless if r["agrees"]),
            "same_cases_in_the_other_arm": {
                "items": other[0]["sensitivity"]["n"],
                "agreement": other[0]["sensitivity"]["value"]},
        }

    return {
        "artifact_type": "v4r3-section-10-4R2-outcome",
        "artifact": "§10.4-R2 microcase semantic audit, outcome",
        "classification": CLASSIFICATION,
        "amendment": "R2 (§10.4-R2, changelog C28, DECISIONS A7), registered "
                     "before the tool was run and before any microcase was "
                     "judged",
        "canonical_verifier_hash": run["config"]["verifier_hash"],
        "case_set_hash": run["case_set_hash"],
        "split_hash": run["split_hash"],
        "config": run["config"],
        "prompt_fit": run["prompt_fit"],
        "phases": {
            "development": {
                "condition": "mc-medium",
                "replicate": 0,
                "items": {"per_arm": 84, "judged": metrics["n"],
                          "development_half": len(halves["development"]),
                          "calibration_half": len(halves["calibration"])},
                "truncation": metrics["truncation"],
                "parse_validity": metrics["parse_validity"],
                "status_counts": metrics["status_counts"],
                "specificity": metrics["specificity"],
                "sensitivity": metrics["sensitivity"],
                "by_arm": metrics["by_arm"],
                "verdict": verdict,
            },
            "repeatability": {
                "criterion": "6 repeatability across two replicates",
                "status": "NOT_MEASURED",
                "why": "criterion 6 is conjunctive with criteria 2 to 5, so a "
                       "replicate cannot turn this development half's FAIL "
                       "into a PASS. §10.4-R2's stopping rule takes effect at "
                       "the criterion-5 failure and a second replicate of a "
                       "condition that has already failed has no registered "
                       "role.",
            },
            "calibration": {
                "status": "NOT_RUN",
                "why": "§10.4-R2: the calibration half is not run until the "
                       "development half passes. It is untouched and its "
                       "split hash is recorded above.",
            },
        },
        "conditions_not_run": {
            "mc-high": {
                "status": "NOT_RUN",
                "why": "a registered contingency on §10.4's reasoning-effort "
                       "axis, and not one matched to this failure. The "
                       "criterion-5 failure is attributable to items whose "
                       "verdict turns on §7.3's wordless-rate convention, "
                       "which the deciding arm deliberately does not state; "
                       "more reasoning cannot supply a convention the prompt "
                       "withholds. Running it after seeing the failure would "
                       "be seeking a better draw. It remains available to the "
                       "researcher, who registered the contingency."},
            "mc-low": {"status": "NOT_RUN", "why": "as mc-high"},
        },
        "attribution_of_the_criterion_5_failure": attribution,
        "per_kind_sensitivity_under_both_readings": reading_check,
        "outcome": verdict["outcome"],
        "consequence": "§10.4-R2: the LLM-validator pathway stops. It is not "
                       "prompt-tuned and no threshold moves. §10.3's human "
                       "semantic audit is the only remaining registered route "
                       "to a measurement basis, and the replication records "
                       "HUMAN_VALIDATION_UNAVAILABLE until an independent "
                       "annotator completes one.",
        "approves": "nothing. Gate 1 is NOT approved and no measurement basis "
                    "is written.",
        "producing_commit": _commit(),
        "generated_at": _now(),
    }


# ------------------------------------------------------------- human labels

#: Every disagreement inspected individually and classified without changing
#: either label. Neither is a verifier implementation error: on both items the
#: primary and the independent reimplementation agree, and both agree with the
#: frozen boundary expectation for that numerator.
_CLASSIFY = {
    "hr-11-a7198420": {
        "verdict": "ambiguous natural-language instruction",
        "why": "the frozen wording is 'Exactly 1 semicolons must appear in "
               "your answer' and the answer carries two semicolons. The "
               "numeral 1 with a plural noun is the wording a reader can take "
               "as *at least* one, and SATISFIES is exactly the label the "
               "registered `inequality_flip` reading of an exact count gives "
               "--- 2 >= 1. The verifier's S == q is the only reading of "
               "'Exactly 1' and is not a defect. CX2:1 is an eligible rung on "
               "all four models, so this wording is live.",
        "not": "likely deterministic-verifier defect",
    },
    "hr-15-79d60ac5": {
        "verdict": "likely human annotation error",
        "why": "the wording is 'At most 1 percent of words begin with t' and "
               "the answer has ten words, none beginning with t: 0.0% <= 1%, "
               "so the registered verdict is SATISFIES. A budget wording "
               "admits no second reading here; VIOLATES is what the "
               "`inequality_flip` reading gives --- 0 >= 1 is false. That "
               "both disagreements coincide with the same defective reading "
               "is the diagnostic signal, and it is a signal about how the "
               "wordings read at q = 1, not about the verifier.",
        "not": "likely deterministic-verifier defect",
    },
}


def human_evidence() -> dict[str, Any]:
    """The 25 labels, scoped against §10.3's four separate requirements."""
    base = REPORTS / "human_review"
    key = {i["item_id"]: i
           for i in json.loads((base / "key.json").read_text())["key"]}
    packet = {i["item_id"]: i
              for i in json.loads((base / "packet.json").read_text())["packet"]}
    records = [json.loads(line) for line
               in (base / "records" / "Bryan.jsonl").read_text().splitlines()
               if line.strip()]
    labels = {r["item_id"]: r for r in records}

    rows = []
    for item_id, entry in sorted(key.items()):
        human = labels[item_id]["label"]
        rows.append({"item_id": item_id, "family": entry["family"],
                     "statistic": entry["statistic"], "form": entry["form"],
                     "severity": entry["severity"], "covers": entry["covers"],
                     "separates": entry["discriminates"],
                     "verifier": entry["verdict"], "human": human,
                     "agrees": human == entry["verdict"],
                     "instruction": packet[item_id]["instruction"],
                     "answer": packet[item_id]["answer"]})

    def group(field: str) -> dict[str, Any]:
        out: dict[str, dict[str, int]] = {}
        for row in rows:
            cell = out.setdefault(str(row[field]), {"n": 0, "agreed": 0})
            cell["n"] += 1
            cell["agreed"] += int(row["agrees"])
        return {k: {**v, "agreement": v["agreed"] / v["n"]}
                for k, v in sorted(out.items())}

    agreed = sum(1 for r in rows if r["agrees"])
    unsure = sum(1 for r in rows if r["human"] == "UNSURE")
    return {
        "annotator": "Bryan (the researcher)",
        "blinding": "the packet carries item_id, instruction, answer and the "
                    "answer's sha256 and nothing else; family, severity, "
                    "predicate form, registered verdict and separated defect "
                    "live in key.json, which the review command never opens "
                    "(asserted by an AST test over the tool's source)",
        "labels_before_verifier_output": True,
        "why": "the packet was built at 16:00:19Z and the labels appended one "
               "at a time between 16:05:44Z and 16:12Z; the report that "
               "compares them was generated at 16:13:47Z",
        "independent_of_design_team": False,
        "n": len(rows), "agreed": agreed, "disagreements": len(rows) - agreed,
        "unsure": unsure,
        "agreement": agreed / len(rows),
        "wilson_upper_on_disagreement": wilson_upper(len(rows) - agreed,
                                                     len(rows)),
        "by_family": group("family"),
        "by_predicate_form": group("form"),
        "by_numerator": group("statistic"),
        "by_severity": group("severity"),
        "by_registered_verdict": group("verifier"),
        "defects_separated": {
            defect: sum(1 for r in rows if defect in r["separates"])
            for defect in MC.DEFECT_KINDS},
        "families_covered": sorted({r["family"] for r in rows}),
        "cr6_capital_word_items": sum(1 for r in rows if r["family"] == "CR6"),
        "wordless_or_empty_items": sum(1 for r in rows
                                       if not WORD.findall(r["answer"])),
        "discordant": [
            {**r, "classification": _CLASSIFY[r["item_id"]]}
            for r in rows if not r["agrees"]],
        "category": "HUMAN SEMANTIC EVIDENCE",
        "not": "REGISTERED INDEPENDENT HUMAN VALIDATION",
        "fails_section_10_3_on": [
            "independence --- §10.3 requires an annotator independent of the "
            "design and analysis team and says in terms that author-performed "
            "labels are never described as independent validation",
            "unit --- §10.3's sample is natural responses; these are "
            "microcases of at most fourteen words",
            "size and stratification --- §10.3 requires min(150, N_c) per "
            "verifier class with the fail class split by realised margin; "
            "this is one packet of 25",
            "criterion --- the one-sided 95% Wilson upper bound on "
            "disagreement is 0.2152 against a threshold of 0.10. At 25 items "
            "the bound clears 0.10 only at zero disagreements (0.0977, which "
            "is why 25 rather than 24), so it is the two disagreements that "
            "fail it and not the sample size",
        ],
    }


def wording_number_agreement() -> dict[str, Any]:
    """Which registered wordings say "1 semicolons", and where it can matter.

    Found while classifying the human review's two disagreements, both of
    which sat at q = 1 and both of whose labels coincide with the
    `inequality_flip` reading. `dci1v4.protocol.wordings.target_wordings`
    special-cases A's singular --- `"time" if n == 1 else "times"` --- and no
    family template, carried or authored, does the same.

    For a budget the infelicity does not change the reading: "at most 1 words"
    is unambiguous whatever the noun's number. For the exact form it plausibly
    does, because "exactly 1 semicolons" is the wording a reader can take as
    *at least* one, which is precisely the label the human gave. Recorded, not
    repaired: changing a wording changes the prompt text of a live rung and is
    an amendment, not a fix.
    """
    landscape = _load("candidate_landscape.json")
    live: dict[str, list[str]] = {}
    for model, entry in landscape["models"].items():
        shortlisted = set(entry["shortlist"])
        for row in entry["table"]:
            if row["family"] in shortlisted and row["eligible"]:
                live.setdefault(row["rung"], []).append(model)

    affected: dict[str, Any] = {}
    admits_one = [k for k in sorted(FAMILIES) if 1 in declared_range(k)]
    for kind in admits_one:
        texts = sorted({t for t in wordings(kind, 1)
                        if PLURAL_AFTER_ONE.search(t)})
        if not texts:
            continue
        affected[kind] = {
            "form": FAMILIES[kind].form,
            "exact_form": FAMILIES[kind].form is FORM_EXACT,
            "wordings": texts,
            "rung_is_live_on": sorted(live.get(f"{kind}:1", [])),
        }
    return {
        "families_admitting_severity_one": len(admits_one),
        "families_with_a_number_disagreeing_wording": len(affected),
        "live_eligible_rungs_affected":
            sorted(k for k, v in affected.items() if v["rung_is_live_on"]),
        "live_and_exact_form":
            sorted(k for k, v in affected.items()
                   if v["rung_is_live_on"] and v["exact_form"]),
        "precedent": "dci1v4.protocol.wordings.target_wordings writes "
                     "'time' if n == 1 else 'times' for A; no family template "
                     "does",
        "standing": "a §7.5 wording observation for the researcher. Changing "
                    "a template changes the prompt text of live rungs, "
                    "re-opens a coverage result that currently passes on all "
                    "four models, and is an amendment rather than a fix",
        "by_family": affected,
    }


# ------------------------------------------------------------------ matrix

def evidence_matrix(gate1: dict[str, Any], r2: dict[str, Any],
                    human: dict[str, Any],
                    defects: dict[str, Any]) -> list[dict[str, Any]]:
    """Seven sources, kept apart. §10.5's discipline, one row wider."""
    evidence = gate1["evidence"]
    stated = defects["stated"]
    return [
        {"source": "§10.2 deterministic implementation correctness",
         "answers": "does each program compute the verdict its registered "
                    "rule defines, on frozen cases and on real responses",
         "does_not_answer": "whether the registered rule means what a reader "
                            "of the prose would take it to mean",
         "population": f"all {evidence['suites']['instruments']} registered "
                       f"instruments over {evidence['suites']['cases']} "
                       f"frozen boundary cases",
         "result": {"boundary_agreement": evidence["suites"]["agreement"],
                    "three_process_determinism":
                        evidence["determinism"]["agreement"],
                    "witness_pairs": evidence["witnesses"]["pairs"],
                    "wording_verdicts":
                        evidence["wordings"]["verdicts_checked"]},
         "independence": "same author, two routes",
         "tier": "implementation",
         "standing": "REGISTERED GATE-1 PREREQUISITE",
         "satisfied": True},
        {"source": "§10.2 independent reimplementation",
         "answers": "do two implementations written by different routes agree "
                    "on every verdict",
         "does_not_answer": "whether both share a misreading of the prose",
         "population": f"{evidence['reimplementation']['responses']} real "
                       f"responses, "
                       f"{evidence['reimplementation']['verdicts_checked']} "
                       f"verdicts",
         "result": {"per_instrument_min":
                        evidence["reimplementation"]["per_instrument_min"],
                    "segmenter_differential":
                        evidence["reimplementation"]["segmenter_differential"]
                                ["agreement"]},
         "independence": "prose-only second implementation",
         "tier": "implementation",
         "standing": "REGISTERED GATE-1 PREREQUISITE",
         "satisfied": True},
        {"source": "§24 adversarial, boundary and witness corpora",
         "answers": "is every registered phenomenon exercised somewhere, and "
                    "does §7.5's non-entailment hold on every realisable pair",
         "does_not_answer": "whether the verdict on a phenomenon is the one a "
                            "human would give",
         "population": f"{evidence['adversarial']['corpus_size']} cases over "
                       f"{len(evidence['adversarial']['corpus_coverage'])} "
                       f"phenomena; "
                       f"{evidence['witnesses']['pairs']} witness pairs",
         "result": {"uncovered_by_corpus":
                        evidence["adversarial"]["uncovered_by_corpus"],
                    "never_observed_in_real_generations":
                        evidence["adversarial"]["realised"]["never_observed"]},
         "independence": "author-designed",
         "tier": "implementation",
         "standing": "REGISTERED GATE-1 PREREQUISITE",
         "satisfied": True},
        {"source": "§10.3 human semantic annotations",
         "answers": "on 25 blinded microcases over eight of the ten families "
                    "§7.0-R3 added, does a person read the instruction the "
                    "way the verifier scores it",
         "does_not_answer": "anything §10.3 asks: the annotator is the "
                            "researcher, the unit is a microcase rather than "
                            "a natural response, and 25 items cannot reach "
                            "the registered bound",
         "population": f"{human['n']} microcases, families "
                       f"{human['families_covered']}",
         "result": {"agreement": human["agreement"],
                    "wilson_upper_on_disagreement":
                        human["wilson_upper_on_disagreement"],
                    "threshold": 0.10},
         "independence": "AUTHOR-PERFORMED --- not independent",
         "tier": "semantic, diagnostic",
         "standing": "SUPPLEMENTARY. §10.3 is a registered Gate-1 pathway and "
                     "this does not complete it",
         "satisfied": False},
        {"source": "§10.4-R2 microcase semantic audit",
         "answers": "does an external validator, given the instruction and "
                    "the answer and never the verdict, agree with the "
                    "registered reading on cases where a defective reading "
                    "would not",
         "does_not_answer": "whether the registered reading is the correct "
                            "one; it measures a second reader, not a truth",
         "population": "84 development microcases per arm over all thirty "
                       "families; the 76-case calibration half is untouched",
         "result": {"specificity":
                        r2["phases"]["development"]["specificity"]["value"],
                    "sensitivity":
                        r2["phases"]["development"]["sensitivity"]["value"],
                    "failed_criteria":
                        r2["phases"]["development"]["verdict"]["failed"]},
         "independence": "external judge, registry disjoint from the study's "
                         "models",
         "tier": "semantic",
         "standing": "REGISTERED GATE-1 PATHWAY --- FAILED, and by §10.4-R2's "
                     "own rule the pathway stops",
         "satisfied": False},
        {"source": "defect-sensitivity diagnostic",
         "answers": "how much would each plausible misreading move this "
                    "study's own numbers, on the responses it has generated",
         "does_not_answer": "which reading is correct. It sizes the stakes of "
                            "each semantic choice; it does not settle one",
         "population": f"{stated['responses']} load-0 and load-1 responses, "
                       f"{stated['overall']['off_by_one']['verdicts']} stated "
                       f"verdicts per reading",
         "result": {k: {"change_rate": v["change_rate"],
                        "rate_shift": v["rate_shift"]}
                    for k, v in sorted(stated["overall"].items())},
         "independence": "read-only, computes no composed estimand",
         "tier": "robustness",
         "standing": "SUPPLEMENTARY --- not a registered Gate-1 criterion",
         "satisfied": None},
        {"source": "carried v3 human evidence",
         "answers": "nothing that may be cited here",
         "does_not_answer": "§10.3 says in terms that the v3 record's 120 "
                            "author-performed blinded labels are diagnostic "
                            "there and are NOT carried as independent "
                            "validation. The v3 forensics' 56 human-labelled "
                            "items are all solo:A:n, so they touch 8 of the "
                            "584 instruments and none of the ten families "
                            "§7.0-R3 added",
         "population": "not admissible",
         "result": None,
         "independence": "author-performed",
         "tier": "not carried",
         "standing": "EXCLUDED BY §10.3",
         "satisfied": None},
    ]


def main() -> int:
    gate1 = _load("gate1_outcome.json")
    defects = _load("defect_sensitivity.json")
    r2 = r2_outcome()
    human = human_evidence()
    OUT_R2.write_text(json.dumps(r2, indent=1, sort_keys=True) + "\n")

    stated = defects["stated"]["overall"]
    decision = {
        "artifact_type": "v4r3-gate1-decision",
        "classification": CLASSIFICATION,
        "gate": "GATE_1_MEASUREMENT",
        "registered_rule": "§18 stage 4: §10.2 for every verifier in the "
                           "final instrument population, plus §10.3 or "
                           "§10.4; verifier hash frozen",
        "canonical_verifier_hash": verifier_source_hash(),
        "verifier_hash_matches_gate1_evidence":
            verifier_source_hash() == gate1["evidence"]["verifier_hash"],
        "instrument_population": gate1["evidence"]["suites"]["instruments"],
        "decision": "GATE_1_BLOCKED_MEASUREMENT",
        "status_written_by_the_gate": gate1["status"],
        "measurement_basis": gate1["measurement_basis"],
        "objective_10_2_prerequisites_all_satisfied": True,
        "why": "§10.4-R2's development half returned FAIL on registered "
               "criterion 5 --- per-kind sensitivity 0.231 on "
               "denominator_swap against a floor of 0.50 registered before "
               "any microcase was judged --- and §10.4-R2 states that on "
               "failure the LLM-validator pathway stops. §10.3 is then the "
               "only remaining registered route, and no independent "
               "annotator has completed it. Both Gate-1 pathways are "
               "therefore unavailable, and the gate refuses on the "
               "measurement basis alone.",
        "smallest_remaining_blocker":
            "§10.3, performed by at least one annotator independent of the "
            "design and analysis team, on a seeded stratified sample of "
            "min(150, N_c) natural responses per verifier class, meeting a "
            "one-sided 95% Wilson upper bound on disagreement of 0.10 in "
            "each class, with the fail class split by realised margin. "
            "Nothing else in Gate 1 is outstanding.",
        "not_a_governance_block": "a researcher signature cannot be applied "
                                  "to §10.4 because §10.4-R2's criteria "
                                  "failed; the missing thing is evidence, "
                                  "not authorisation",
        "semantic_choices_that_are_load_bearing": {
            kind: {"change_rate": stated[kind]["change_rate"],
                   "rate_shift": stated[kind]["rate_shift"],
                   "band": defects["verdict_bands"]["stated"][kind]["band"]}
            for kind in ("inequality_flip", "denominator_swap",
                         "numerator_swap", "off_by_one")},
        "localised": {
            "segmentation_drift": {
                "change_rate": stated["segmentation_drift"]["change_rate"],
                "every_change_is_family": "CR6",
                "cr6_semantic_coverage": {
                    "microcases_in_the_development_half": 2,
                    "agreement": 1.0,
                    "microcases_sealed_in_the_calibration_half": 5,
                    "human_annotations": human["cr6_capital_word_items"]},
                "cr6_on_any_reference_shortlist": False}},
        "not_testable_on_natural_responses": {
            "vacuity_ignored": {
                "change_rate": stated["vacuity_ignored"]["change_rate"],
                "reading": "natural-response agreement cannot validate the "
                           "vacuity convention because the relevant "
                           "counterfactual case does not occur in this "
                           "corpus. Absence of a natural example is not "
                           "successful validation; the convention has to be "
                           "evaluated on designed boundary and microcases, "
                           "which is where §10.2's 164-case suite and "
                           "§10.4-R2's 12 vacuity-separating microcases "
                           "already put it."}},
        "evidence_matrix": evidence_matrix(gate1, r2, human, defects),
        "human_annotations": human,
        "wording_number_agreement": wording_number_agreement(),
        "r2": {"outcome": r2["outcome"],
               "failed": r2["phases"]["development"]["verdict"]["failed"],
               "artifact": str(OUT_R2.relative_to(DCI1))},
        "producing_commit": _commit(),
        "generated_at": _now(),
    }
    OUT_GATE.write_text(json.dumps(decision, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"decision": decision["decision"],
                      "r2_outcome": r2["outcome"],
                      "r2_failed": r2["phases"]["development"]["verdict"]
                                     ["failed"],
                      "human_agreement": human["agreement"],
                      "human_wilson_upper":
                          human["wilson_upper_on_disagreement"],
                      "artifacts": [str(OUT_R2.relative_to(DCI1)),
                                    str(OUT_GATE.relative_to(DCI1))]},
                     indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
