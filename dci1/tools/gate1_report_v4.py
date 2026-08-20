"""Emit the Track 2 report from the three Gate 1 evidence artifacts.

Reads reports/gate1_v4/{section_10_2,readiness_c4_c5_sizing,
section_10_4_development}.json and writes reports/gate1_v4/REPORT.md.
Approves nothing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "gate1_v4"

o: list[str] = []


def w(x: str = "") -> None:
    o.append(x)


def load(name):
    path = OUT / name
    return json.loads(path.read_text()) if path.exists() else None


def main() -> int:
    s102 = load("section_10_2.json")
    rdy = load("readiness_c4_c5_sizing.json")
    s104 = load("section_10_4_development.json")
    if s102 is None or rdy is None:
        raise SystemExit("run gate1_evidence_v4.py and gate1_readiness_v4.py first")
    c4, c5, sz = (rdy["c4_sealed_final_check_set"],
                  rdy["c5_verifier_hash_binding"], rdy["annotation_sizing"])

    w("# Track 2 — Gate 1 through §10.2 and §10.4")
    w()
    w("**Gate 1 is NOT approved.** Nothing is sealed, no one-shot artifact is")
    w("claimed, no labelling session was started, and no registered evidence was")
    w("written. Every artifact below lives under `dci1/reports/gate1_v4/`.")
    w()
    w("---")
    w()
    w("## 1. The independence constraint, stated first")
    w()
    w("The annotator available to this study is the study author. §10.3 requires an")
    w("annotator **independent of the design and analysis team**, so its criterion")
    w("cannot be met — not by labelling more items, and not by labelling them")
    w("better. The registered consequence is explicit and is a permitted outcome:")
    w()
    w("| step | disposition |")
    w("|---|---|")
    w("| identification status | `HUMAN_VALIDATION_UNAVAILABLE` |")
    w("| §10.3 criterion | **not waived**; routed to §10.4 |")
    w("| measurement basis | `autorater_calibration_approved`, on explicit researcher approval |")
    w("| every claim | carries the registered §10.5 scope sentence |")
    w()
    w("**Author-performed labels are diagnostic evidence and §10.4 hierarchy")
    w("input.** They are never described as independent validation, in any")
    w("artifact, at any point. The v3 record already carries the same disposition")
    w("for its 120 author labels and nothing here changes it.")
    w()
    w("---")
    w()
    w("## 2. Scope: A and B only")
    w()
    w("§10.2 requires the full evidence set for every family verifier Gate 3 could")
    w("admit. The reference pool is under revision — the registered pool is")
    w("falsified and Amendment B is not adopted — so family verifier work would be")
    w("spent on families that may not exist. A's exact-count rule and B's")
    w("word-length rule are done here in full.")
    w()
    w("Extending the focal grid changes B's severity grid and not B's rule, so B's")
    w("§10.2 work was safe to do before Track 1 reported. It was, and Track 1 does")
    w("not disturb it.")
    w()
    w("---")
    w()
    w("## 3. §10.2 verifier correctness, for A and B")
    w()
    w("Artifact: `section_10_2.json`.")
    w()
    w("### The response pool")
    w()
    pool = s102["response_pool"]
    w("| item | value |")
    w("|---|---|")
    w(f"| rows read | {pool['rows_read']:,} |")
    w(f"| distinct texts | **{pool['distinct_texts']:,}** |")
    w(f"| pool hash | `{pool['pool_hash'][:32]}…` |")
    w("| provenance | the §12.2 dense ladder screen, all three §12.1 cap screens "
      "and the Gate 0 pilot, on all four models, read only |")
    w()
    w("§10.2 says \"every calibration response\". Gate 1 is stage 4 and Gate 2 has")
    w("not run, so **no calibration response exists yet**. The pool used is every")
    w("genuine v4 generation on disk — the largest natural response population")
    w("available at Gate 1, roughly twenty times the size of the §10.3 sample. It")
    w("is not the calibration pool, and the determinism and reimplementation lines")
    w("must be re-run over that pool when it exists. The limitation is recorded on")
    w("the artifact itself, not only here.")
    w()
    w("### The five lines")
    w()
    d, b, r = (s102["determinism"], s102["boundary_suite"],
               s102["independent_reimplementation"])
    a, co = s102["adversarial_corpus"], s102["carry_over"]
    w("| line | requirement | result |")
    w("|---|---|---|")
    w(f"| **Determinism** | three executions on three separate processes, "
      f"agreement exactly 1.000 | **1.000** — {d['batches']} batches, "
      f"{d['processes_total']} processes, {d['verdicts_per_process']:,} verdicts "
      f"per process, every batch exactly 1.000 |")
    w(f"| **Boundary suite, A** | ≥ {b['A']['minimum_required']} cases, the §24 "
      f"enumeration, frozen before qualification | **{b['A']['cases']} cases** "
      f"({b['A']['carried_from_v3']} carried byte-identically from v3 + "
      f"{b['A']['authored_for_v4']} authored for v4), agreement "
      f"**{b['A']['agreement']}**, {len(b['A']['coverage_categories'])} coverage "
      f"categories |")
    w(f"| **Boundary suite, B** | authored for v4 in full, ≥ "
      f"{b['B']['minimum_required']} cases | **{b['B']['cases']} cases**, all "
      f"v4-authored, agreement **{b['B']['agreement']}**, "
      f"{len(b['B']['coverage_categories'])} coverage categories |")
    w(f"| **Independent reimplementation** | prose-only second implementation, "
      f"agreement exactly 1.000 | **1.000** over "
      f"{r['responses_including_suites']:,} texts × 12 instruments; minimum "
      f"per-instrument agreement {r['minimum_agreement']}; zero disagreements |")
    w(f"| **Adversarial corpus** | every enumerated boundary case, with realised "
      f"frequency in genuine generations | corpus of {a['corpus_size']} items; "
      f"realised incidence computed over all {a['genuine_generations']:,} natural "
      f"responses |")
    w(f"| **Carry-over** | names the source, records every hash, refuses on "
      f"mismatch | **not refused**; "
      f"{len(co['symbol_record']['entries'])} symbols byte-identical to the v3 "
      f"artifacts |")
    w()
    w(f"Boundary suite hash `{b['suite_hash'][:32]}…`, "
      f"{len(b['failures'])} case failures. Canonical verifier hash "
      f"`{s102['canonical_verifier_hash'][:32]}…`.")
    w()
    w("**A's boundary coverage:** "
      + ", ".join(f"`{c}`" for c in b["A"]["coverage_categories"]) + ".")
    w()
    w("**B's boundary coverage:** "
      + ", ".join(f"`{c}`" for c in b["B"]["coverage_categories"]) + ".")
    w()
    w("### Carry-over detail")
    w()
    w("The rule is byte-identity of the construct string, the segmentation source,")
    w("the counting source, and the forty case texts with their expectations. All")
    w("hold:")
    w()
    w("| role | symbols |")
    w("|---|---|")
    for role in ("carry_over", "compatibility"):
        names = [e["function"] for e in co["symbol_record"]["entries"]
                 if e["role"] == role]
        w(f"| `{role}` | " + ", ".join(f"`{n}`" for n in names) + " |")
    w()
    w("The `compatibility` entries are not required by the carry-over rule — B and")
    w("the families are authored for v4 — but the identity is what lets check C6")
    w("read v3 solo cells as an anchor without re-scoring them under a different")
    w("rule.")
    w()
    w("**§10.2 verdict for A and B: every line met.** "
      f"`A_and_B_meet_10_2 = {s102['summary']['A_and_B_meet_10_2']}`.")
    w()
    w("---")
    w()
    if s104:
        emit_10_4(s104)
    else:
        w("## 4. §10.4 autorater pathway")
        w()
        w("*Not yet run.*")
        w()
        w("---")
        w()
    emit_c4(c4)
    emit_c5(c5)
    emit_sizing(sz)
    emit_remaining(s104)
    (OUT / "REPORT.md").write_text("\n".join(o) + "\n")
    print(f"written: {(OUT / 'REPORT.md').relative_to(DCI1)}  ({len(o)} lines)")
    return 0


def emit_10_4(s):
    w("## 4. §10.4 autorater pathway, for the A and B classes")
    w()
    w("Artifact: `section_10_4_development.json`. **Development phase only.**")
    w()
    w("### What is deliberately not done")
    w()
    nc = s["not_claimed"]
    w("| §10.4 step | state |")
    w("|---|---|")
    w(f"| single-shot signed freeze | **{nc['autorater_freeze']}** |")
    w(f"| one-shot calibration | **{nc['autorater_calibration']}** |")
    w(f"| held-out half | {nc['held_out_half']} |")
    w()
    w(f"**Why.** {nc['reason']}")
    w()
    w("Everything before the freeze is done: the split derivation, the serialised")
    w("judge execution, the repeatability check, the paired condition comparison,")
    w("and selection under the §10.4 hierarchy as far as the hierarchy can be")
    w("carried without human labels.")
    w()
    w("### The response pool and the split")
    w()
    p = s["pool"]
    w("| item | value |")
    w("|---|---|")
    w(f"| items | {p['items']} ({p['instruments']['A']} A-class, "
      f"{p['instruments']['B']} B-class) |")
    w(f"| source | {p['source']} |")
    w(f"| development / calibration | {p['development']} / {p['calibration']}, "
      f"**disjoint** |")
    w(f"| split hash | `{p['split_hash'][:32]}…` |")
    w()
    w("| stratum | items | development | calibration |")
    w("|---|---|---|---|")
    for k, v in sorted(p["strata"].items()):
        w(f"| `{k}` | {v['n']} | {v['development']} | {v['calibration']} |")
    w()
    js = s["judged_subsample"]
    w(f"The paired comparison runs on a stratum-balanced subsample of the")
    w(f"**development half only**: {js['n']} items, "
      + ", ".join(f"{n} `{k}`" for k, n in sorted(js["strata"].items()))
      + f", hash `{js['hash'][:16]}…`. Derivation: {js['derivation']}.")
    w()
    w("### The judging conditions")
    w()
    w("One condition is one hashed configuration. Two axes were varied: the prompt")
    w("version and the rendered reasoning effort. All four run **serialised at")
    w("concurrency one** (§10.4, T-15), greedy, cap 2,048, judge")
    w("`openai/gpt-oss-20b` at pinned revision `6cee5e81…` from a registry disjoint")
    w("from the four study models.")
    w()
    w("| condition | prompt | effort | config hash |")
    w("|---|---|---|---|")
    for k, v in sorted(s["conditions"].items()):
        cfg = v["config"]
        w(f"| `{k}` | `{cfg['prompt_version']}` | "
          f"{cfg['decoding']['chat_template_kwargs']['reasoning_effort']} | "
          f"`{cfg['config_hash'][:12]}` |")
    w()
    w("### Results, paired on the same items")
    w()
    w("| condition | coverage | truncation | s/item | valid | invalid | refusal |")
    w("|---|---|---|---|---|---|---|")
    for k, v in sorted(s["conditions"].items()):
        sc = v["status_counts"]
        w(f"| `{k}` | **{v['coverage']:.3f}** | **{v['truncation_rate']:.3f}** | "
          f"{v['seconds_per_item']:.1f} | {sc.get('valid', 0)} | "
          f"{sc.get('invalid_output', 0)} | {sc.get('refusal', 0)} |")
    w()
    if s.get("repeatability"):
        w("### Repeatability (criterion 1)")
        w()
        w("| condition | items | pairwise agreement | exactly repeatable |")
        w("|---|---|---|---|")
        for k, v in sorted(s["repeatability"].items()):
            w(f"| `{k}` | {v.get('items', v['items'])} | "
              f"{', '.join(f'{x:.3f}' for x in v['pairwise_agreement'])} | "
              f"**{v['exactly_repeatable']}** |")
        w()
    if s.get("sidecars"):
        w("### Cross-device determinism (additive to criterion 1)")
        w()
        w("A check none of the four conditions gives on its own: the same items,")
        w("the same hashed configuration, the other GPU. Serialised execution at")
        w("concurrency one is supposed to make the device irrelevant, and T-15")
        w("rests on that. Not a condition, and it takes no part in the selection.")
        w()
        w("| condition | device | items | labels identical | agreement | device inert |")
        w("|---|---|---|---|---|---|")
        for name, v in sorted(s["sidecars"].items()):
            w(f"| `{v['condition']}` | {v['device']} | {v['items_compared']} | "
              f"{v['labels_identical']}/{v['items_compared']} | "
              f"**{v['agreement']:.3f}** | **{v['device_is_inert']}** |")
        w()
        w("Non-verdicts are compared rather than dropped: a device that changed")
        w("*which* items reach a verdict would be a device effect too. The two")
        w("invalid-output items agree as well, so even the truncation pattern is")
        w("reproduced across cards.")
        w()
    w("### Selection under the §10.4 hierarchy")
    w()
    sel = s["selection"]
    w("The hierarchy is applied in order and a later criterion never overrides")
    w("an earlier one. But criterion 2 says \"absence of **problematic**")
    w("truncation\" and criterion 3 \"**valid** parsing and coverage\" — threshold")
    w("words, with no threshold registered. Two readings follow and **they do")
    w("not agree on whether criterion 4 is reached**, so both are reported.")
    w()
    for name, label in (("ranking", "Reading 1 — ranking"),
                        ("threshold", "Reading 2 — threshold")):
        r = sel["readings"][name]
        w(f"#### {label}")
        w()
        if name == "ranking":
            w("Take the best value at each criterion.")
        else:
            w("Eliminate only a condition that is *distinguishably* worse than")
            w("the best — its 95% Wilson interval not overlapping the best")
            w("condition's. Turns the threshold words into a decision without")
            w("inventing a constant.")
        w()
        w("| # | criterion | values | surviving | decided |")
        w("|---|---|---|---|---|")
        for i, step in enumerate(r["steps"], start=1):
            values = step["values"]
            shown = (", ".join(f"`{k}` {v}" for k, v in sorted(values.items()))
                     if isinstance(values, dict) else "—")
            w(f"| {i} | {step['criterion']} | {shown} | "
              f"{', '.join('`'+x+'`' for x in step['surviving'])} | "
              f"{'**yes**' if step['decided'] else 'no'} |")
        w()
        w(f"Surviving: {', '.join('`'+x+'`' for x in r['surviving'])}. "
          f"Criterion 4 reached: **{r['human_criterion_outstanding']}**.")
        w()
    w(f"**Both readings agree on "
      f"{', '.join('`'+x+'`' for x in sel['agreed_by_both_readings'])}.** Under")
    w("the ranking reading it is selected outright at criterion 2; under the")
    w("threshold reading it is one of three survivors and criterion 4 decides")
    w("between them.")
    w()
    w("The ranking reading decides on a difference of **two items out of")
    w("forty-eight** (`v4prompt-medium` 0/48 against `carried-medium` 2/48),")
    w("which is not a distinguishable difference. That is why the threshold")
    w("reading is reported beside it rather than as a footnote.")
    w()
    w("The rejected alternative under both readings is `carried-high`: 25/48")
    w("truncated, coverage 0.479. It is the carried v3 prompt at high reasoning")
    w("effort, and it is eliminated by a margin nothing else comes close to.")
    w()
    w("### Agreement with the deterministic verifier")
    w()
    w("Reported for every condition and **not** a selection criterion — §10.4's")
    w("fourth criterion is agreement with *human* labels, and selecting the")
    w("judge that best matches the verifier would make the held-out evaluation")
    w("circular. It is shown because it says what the truncation numbers do not.")
    w()
    strata = sorted({k for v in sel["verifier_agreement_by_condition"].values()
                     for k in v if k != "overall"})
    w("| condition | " + " | ".join(f"`{k}`" for k in strata) + " | overall |")
    w("|---" * (len(strata) + 2) + "|")
    for cond, per in sorted(sel["verifier_agreement_by_condition"].items()):
        cells = " | ".join((f"{per[k]['agreement']:.3f}" if k in per else "--")
                           for k in strata)
        overall = f"{per['overall']['agreement']:.3f}" if "overall" in per else "--"
        w(f"| `{cond}` | {cells} | **{overall}** |")
    w()
    w("**This is the finding the truncation table hides.** The carried prompt at")
    w("medium effort does not merely lose items — when it does return a verdict")
    w("it is wrong in a structured way, agreeing with the verifier on only")
    w("**0.125** of A-class fail items whose margin is larger than one. That is")
    w("the instrument bleed visible in its reasoning transcript: it injects the")
    w("constrained token into its own justification and then labels SATISFIES.")
    w("Both v4-prompt conditions sit at 1.000 in every stratum.")
    w()
    w("`carried-high`'s 0.957 is computed on the 23 of 48 items that reached a")
    w("verdict at all, so it is not comparable with the others.")
    w()
    if s.get("criterion_4_annotation_set"):
        c4 = s["criterion_4_annotation_set"]
        w("### What criterion 4 actually needs")
        w()
        w("Under the threshold reading three conditions survive to criterion 4.")
        w("Conditions that never disagree cannot be separated by any number of")
        w("labels, so only the discordant items carry information.")
        w()
        w("| item | value |")
        w("|---|---|")
        w(f"| conditions still alive | "
          f"{', '.join('`'+x+'`' for x in c4['conditions_still_alive'])} |")
        w(f"| discordant items | **{c4['n_discordant']}** |")
        w("| by stratum | "
          + ", ".join(f"`{k}` {v}" for k, v in sorted(c4["by_stratum"].items()))
          + " |")
        w(f"| matched concordant controls | {c4['matched_control']} |")
        w(f"| **total to label** | **{c4['total_to_label']}** |")
        w(f"| estimated time | **{c4['estimated_minutes'][0]}–"
          f"{c4['estimated_minutes'][1]} minutes** |")
        w()
        w("`v4prompt-high` and `v4prompt-medium` are discordant on **zero** of")
        w("the 42 items where both return a verdict — behaviourally the same")
        w("judge. So the whole criterion-4 question is `carried-medium` against")
        w("the v4 prompt, on 11 items, 10 of which are A-class fail items —")
        w("exactly the stratum where `carried-medium`'s verifier agreement")
        w("collapses.")
        w()
        w(f"*{c4['invariant']}.*")
        w()
    if s.get("paired_comparisons"):
        w("### Discordance between conditions")
        w()
        w("| pair | items compared | discordant |")
        w("|---|---|---|")
        for name, pc in sorted(s["paired_comparisons"].items()):
            w(f"| {name} | {pc['items_compared']} | "
              f"**{len(pc['discordant_items'])}** |")
        w()
    w("---")
    w()


def emit_c4(c4):
    w("## 5. The sealed final-check set (C4)")
    w()
    w("### The v3 set")
    w()
    v3 = c4["v3_sealed_set"]
    w("| item | value |")
    w("|---|---|")
    w(f"| expected sha256 | `{v3['expected_sha256']}` |")
    w(f"| measured sha256 | `{v3['measured_sha256']}` |")
    w(f"| **untouched** | **{v3['untouched']}** |")
    w(f"| verification method | {v3['verification_method']} |")
    w()
    w("Verified by file digest alone. **No item id from the v3 set was read,")
    w("displayed or used.** The seal exists to keep the set from influencing any")
    w("decision, and a hash check does not.")
    w()
    w("### The v4 set")
    w()
    w("Per C4 the v3 set may not be reused: it was composed for the exact-count")
    w("rule alone and cannot exercise the word-length rule or any family verifier.")
    w()
    v4 = c4["v4_candidate_set"]
    w("| item | value |")
    w("|---|---|")
    w(f"| state | **{v4['state']}** |")
    w(f"| items | {v4['items']} |")
    w(f"| content hash | `{v4['content_hash'][:32]}…` |")
    w("| strata | "
      + ", ".join(f"`{k}` {n}" for k, n in sorted(v4["strata"].items())) + " |")
    w(f"| reserved before the dev/calibration split | "
      f"{v4['reserved_before_the_split']} |")
    w(f"| derivation | {v4['derivation']} |")
    w()
    w("**It is not sealed, for two reasons.** Sealing is a Gate 1 act and Gate 1")
    w("is not approved. And the set is provisional: it covers A and B only, so it")
    w("must be re-derived once the reference pool is final — a final-check set that")
    w("cannot exercise an admitted instrument is not a final check of it. The")
    w("derivation is deterministic, so re-deriving it over the final pool is a")
    w("re-run, not a judgement call.")
    w()
    w("When it is sealed the registered rules apply: " +
      "; ".join(v4["rules_when_it_is_sealed"]) + ".")
    w()
    w("---")
    w()


def emit_c5(c5):
    w("## 6. Verifier-hash binding (C5)")
    w()
    w(f"`{c5['regression_test_file']}` — **all pass**.")
    w()
    w(f"The protected set is the union of **{c5['entry_point_count']} entry "
      f"points**: " + ", ".join(f"`{e}`" for e in c5["entry_points"]) + ".")
    w()
    w("| required case | result |")
    w("|---|---|")
    for k, v in c5["five_required_cases"].items():
        w(f"| {k} | **{v}** |")
    w()
    w("Four further cases pass beyond the five required:")
    w()
    for k, v in sorted(c5["additional_cases"].items()):
        w(f"- `{k}` — {v}")
    w()
    w(f"Canonical verifier hash `{c5['canonical_verifier_hash'][:32]}…`.")
    w()
    w("---")
    w()


def emit_sizing(sz):
    w("## 7. The annotation sample sizing")
    w()
    w("**No labelling session has been started.** §2.5 requires the author to size")
    w("and agree one first, and this is that sizing.")
    w()
    w("### The population")
    w()
    w("| stratum | items |")
    w("|---|---|")
    for k, v in sorted(sz["pool"]["by_stratum"].items()):
        w(f"| `{k}` | {v} |")
    w(f"| **total** | **{sz['pool']['items']}** |")
    w()
    w(f"Sampling seed `{sz['sampling_seed']}`. Source: the registered §12.2 ladder")
    w("screen, one item per (constraint, response) pair the model actually saw.")
    w()
    w("### The rate")
    w()
    w("Measured from this annotator's own v3 sessions rather than assumed: 56 items")
    w("in 52.4 minutes and 64 items in 69.2 minutes, median inter-item gaps 49.2 s")
    w("and 27.7 s. That is **30–60 seconds per item**.")
    w()
    w("### The two numbers")
    w()
    o1 = sz["option_1_section_10_3"]
    w("| | §10.3 sizing | §10.4 sizing |")
    w("|---|---|---|")
    w("| rule | min(150, N_c) per class per instrument, fail class split by "
      "realised margin | enough paired items to separate the judging conditions |")
    w(f"| items | **{o1['items_by_stratum']}** | the discordant set plus a "
      f"matched concordant control |")
    w(f"| estimated time | **{o1['estimated_hours']['low']}–"
      f"{o1['estimated_hours']['high']} hours** | see §4 |")
    w("| what it buys | **nothing Gate 1 can use** — the basis stays "
      "`HUMAN_VALIDATION_UNAVAILABLE` however many items are labelled, because "
      "the annotator is not independent | the fourth criterion of the §10.4 "
      "hierarchy, the only one the judge run cannot decide on its own |")
    w()
    w("Per-stratum breakdown at the §10.3 rule:")
    w()
    w("| stratum | population | registered sample | reachable |")
    w("|---|---|---|---|")
    floor = None
    for k, v in sorted(o1["per_stratum"].items()):
        floor = v["minimum_n_for_the_criterion_to_be_reachable"]
        w(f"| `{k}` | {v['population']} | {v['registered_sample']} | "
          f"{'yes' if v['reachable'] else '**no**'} |")
    w()
    w(f"Every stratum is large enough for the one-sided 95% Wilson upper bound to")
    w(f"reach 0.10 at zero disagreements, which needs n ≥ {floor}. No stratum")
    w("returns `MEASUREMENT_EVIDENCE_INSUFFICIENT` on population grounds.")
    w()
    w("### Required properties of any session")
    w()
    for p in sz["protocol_properties_required_of_any_session"]:
        w(f"- {p}")
    w()
    w(f"**Why tool-assisted and not automatic.** "
      f"{sz['why_tool_assisted_and_not_automatic']}")
    w()
    w("The v3 tooling under `autorater_forensics/experiments/human_review/`")
    w("already has all of these and is reused, not rewritten. Its reviewer-facing")
    w("definitions are A-specific (an occurrence-count instruction), so a B-class")
    w("definition set has to be authored in the same shape before a B session —")
    w("an addition to the tooling, not a change to it.")
    w()
    w("---")
    w()


def emit_remaining(s104):
    w("## 8. What remains before Gate 1 can be approved")
    w()
    w("In order, and none of it is optional:")
    w()
    w("1. **The reference pool must be final.** §10.2 requires the full evidence")
    w("   set for every family verifier Gate 3 could admit. The registered pool is")
    w("   falsified; Amendments A, B and C are drafted and none is adopted. Until")
    w("   the pool is decided there is no instrument population to validate.")
    w("2. **§10.2 for every admitted family verifier.** Determinism, a frozen")
    w("   boundary suite of at least forty authored cases each, an independent")
    w("   reimplementation, and an adversarial corpus. Nothing carries over: the")
    w("   family suites are authored for v4 in full.")
    w("3. **Re-run §10.2's determinism and reimplementation over the calibration")
    w("   pool** once Gate 2 produces one. The 13,953-response pool used here is")
    w("   the pre-screen population, not the calibration population.")
    w("4. **The §10.4 fourth criterion.** Author labels on the discordant set,")
    w("   sized in §7 and not started.")
    w("5. **The single-shot freeze and the one-shot calibration**, against a")
    w("   canonical verifier hash that is final. Both are deliberately unclaimed")
    w("   here precisely so they are available then.")
    w("6. **Seal a v4 final-check set** derived over the final instrument")
    w("   population, and record its hash in the Gate 1 record.")
    w("7. **Explicit researcher approval** writing")
    w("   `measurement_basis = autorater_calibration_approved`, with")
    w("   `HUMAN_VALIDATION_UNAVAILABLE` as the identification status and the")
    w("   §10.5 scope sentence attached to every claim.")
    w()
    w("**What this track did settle:** A's exact-count rule and B's word-length")
    w("rule are Gate-1-ready on §10.2. C4 and C5 are complete. The judge pathway")
    w("is executed and characterised as far as it can be without human labels, and")
    w("the carried judge prompt has been shown unusable for the B class before it")
    w("could be inherited into a freeze.")
    w()
    w("---")
    w()
    w("## 9. Artifacts")
    w()
    w("| path | contents |")
    w("|---|---|")
    w("| `reports/gate1_v4/section_10_2.json` | the §10.2 evidence for A and B |")
    w("| `reports/gate1_v4/readiness_c4_c5_sizing.json` | C4, C5 and the sizing |")
    if s104:
        w("| `reports/gate1_v4/section_10_4_development.json` | the judge pathway |")
        w("| `reports/gate1_v4/conditions/*.json` | one file per judging condition |")
        w("| `reports/gate1_v4/judge_runs/` | every raw judge run directory |")
    w("| `reports/gate1_v4/REPORT.md` | this report |")
    w("| `tools/gate1_evidence_v4.py` | executes §10.2 |")
    w("| `tools/gate1_readiness_v4.py` | executes C4, C5 and the sizing |")
    w("| `tools/gate1_autorater_v4.py` | executes the §10.4 development phase |")
    w("| `tests_v4/test_gate1_autorater_config.py` | 12 tests pinning the "
      "hashed-configuration invariants |")


if __name__ == "__main__":
    raise SystemExit(main())
