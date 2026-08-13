#!/usr/bin/env python3
"""Corrected reliability/coupling audit, and a full old-vs-corrected rescore.

Two jobs.

**Reliability (plan step 8).** Recompute the verifier-validation quantities on a
ground-truth corpus with adequate structural support, using the names the
preregistration actually uses:

  E_A, E_R   verifier error rates against hand-written ground truth
  U_A, U_R   unscorable shares
  kappa      the PREREGISTERED coupling statistic — the mean fraction of coupling
             EDITS that flip BOTH verdicts at once. It is a rate in [0, 1] and can
             never be negative. Round 3 reported a Cohen's-kappa agreement
             coefficient under this symbol and quoted it as -0.132; that was the
             wrong statistic under the right name and is withdrawn here.
  U_kappa    bootstrap spread of kappa over resampled bank responses.

A signed agreement coefficient is still useful as a diagnostic, so it is
computed and reported under a DIFFERENT name: `agreement_phi`.

**Rescore (plan steps 9-10).** Re-score every stored generation with the repaired
verifier without regenerating anything, preserve both columns, and report which
conclusions move.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

N_TARGET = 4
RUNS = {
    "stageB": "stageB_20260810T183206Z",
    "D2": "stageD2_anticollapse_20260810T192423Z",
    "D3": "stageD3_semicolon_20260810T192430Z",
}


# ------------------------------------------------------------------ reliability
def reliability() -> dict:
    from dci.verifiers.rules import v_exact_sentence_count, v_semicolon_each
    from stress_corpus import CORPUS

    rows = []
    for text, true_n, true_semi, kind in CORPUS:
        a = v_exact_sentence_count(text, N_TARGET)
        r = v_semicolon_each(text)
        a_uns, r_uns = a.status == "unscorable", r.status == "unscorable"
        truth_a = int(true_n == N_TARGET)
        truth_r = None if true_semi is None else int(bool(true_semi))
        rows.append({
            "kind": kind, "true_sentences": true_n,
            "observed": a.detail.get("observed"),
            "A_unscorable": a_uns, "R_unscorable": r_uns,
            "verifier_A": None if a_uns else int(a.binary_pass),
            "verifier_R": None if r_uns else int(r.binary_pass),
            "truth_A": truth_a, "truth_R": truth_r,
            "A_error": None if a_uns else int(int(a.binary_pass) != truth_a),
            "R_error": (None if (r_uns or truth_r is None)
                        else int(int(r.binary_pass) != truth_r)),
            "count_correct": None if a_uns else (a.detail.get("observed") == true_n),
        })

    scorable_a = [x for x in rows if x["A_error"] is not None]
    scorable_r = [x for x in rows if x["R_error"] is not None]
    unscorable_kinds = [x["kind"] for x in rows if x["A_error"] is None]

    # ---- the PREREGISTERED kappa: joint-flip rate under the coupling edits ----
    # Reimplemented here over the stress corpus rather than the authored bank,
    # because the question is what kappa says on a support that CONTAINS the
    # one-sentence clause chain. The edit set mirrors c162's role: small
    # structure-preserving perturbations.
    def edit_append_sentence(t: str) -> str:
        return t.rstrip() + " The work then stops."

    def edit_drop_last_sentence(t: str) -> str:
        parts = t.rsplit(". ", 1)
        return parts[0] + "." if len(parts) > 1 else t

    def edit_period_to_semicolon(t: str) -> str:
        return t.replace(". ", "; ", 1)

    def edit_semicolon_to_period(t: str) -> str:
        return t.replace("; ", ". ", 1)

    def edit_lengthen(t: str) -> str:
        return t.replace(". ", ", which matters here. ", 1)

    EDITS = {
        "append_sentence": edit_append_sentence,
        "drop_last_sentence": edit_drop_last_sentence,
        "period_to_semicolon": edit_period_to_semicolon,
        "semicolon_to_period": edit_semicolon_to_period,
        "lengthen_clause": edit_lengthen,
    }

    def verdicts(text: str) -> tuple[int, int]:
        return (int(v_exact_sentence_count(text, N_TARGET).binary_pass),
                int(v_semicolon_each(text).binary_pass))

    per_response = []
    for text, _true_n, _semi, _kind in CORPUS:
        if not text.strip():
            continue
        base_a, base_r = verdicts(text)
        if not (base_a and base_r):
            continue                      # informative only if both pass at baseline
        flips = sum(
            int(verdicts(edit(text))[0] != base_a and verdicts(edit(text))[1] != base_r)
            for edit in EDITS.values())
        per_response.append(flips / len(EDITS))

    if per_response:
        kappa = sum(per_response) / len(per_response)
        rng = random.Random(20260810)
        draws = sorted(
            sum(per_response[rng.randrange(len(per_response))]
                for _ in per_response) / len(per_response)
            for _ in range(2000))
        u_kappa = (draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1])
    else:
        kappa, u_kappa = float("nan"), (float("nan"), float("nan"))

    # ---- the SIGNED agreement coefficient, under its own name ----------------
    both = [x for x in rows if x["verifier_A"] is not None and x["verifier_R"] is not None]
    n = len(both)
    po = sum(1 for x in both if x["verifier_A"] == x["verifier_R"]) / n
    pa = sum(x["verifier_A"] for x in both) / n
    pb = sum(x["verifier_R"] for x in both) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    agreement_phi = (po - pe) / (1 - pe) if pe != 1 else float("nan")

    return {
        "n_items": len(rows),
        "E_A": sum(x["A_error"] for x in scorable_a) / len(scorable_a),
        "n_scorable_A": len(scorable_a),
        "E_R": sum(x["R_error"] for x in scorable_r) / len(scorable_r),
        "n_scorable_R": len(scorable_r),
        "U_A": sum(x["A_unscorable"] for x in rows) / len(rows),
        "U_R": sum(x["R_unscorable"] for x in rows) / len(rows),
        "unscorable_kinds": unscorable_kinds,
        "kappa_prereg_jointflip": kappa,
        "U_kappa": u_kappa,
        "n_informative_for_kappa": len(per_response),
        "agreement_phi_signed_diagnostic": agreement_phi,
        "count_errors": [x["kind"] for x in rows if x["count_correct"] is False],
    }


# --------------------------------------------------------------------- rescore
def rescore() -> dict:
    from dci.verifiers.rules import v_exact_sentence_count

    out: dict = {}
    for tag, run in RUNS.items():
        rows = [json.loads(l) for l in
                (HERE / "runs" / run / "generations.jsonl").read_text(
                    encoding="utf-8").splitlines() if l.strip()]
        rescored = []
        for row in rows:
            old_observed = (row.get("verifier_detail") or {}).get("observed")
            old_fail = row.get("a_failure")
            if row.get("scorable") and row.get("response"):
                result = v_exact_sentence_count(row["response"], N_TARGET) \
                    if row["measured"] == "A" else None
                new_observed = result.detail.get("observed") if result else old_observed
                new_fail = (1 - int(result.binary_pass)) if result else old_fail
            else:
                new_observed, new_fail = old_observed, old_fail
            rescored.append({**row, "observed_old": old_observed,
                             "observed_corrected": new_observed,
                             "a_failure_old": old_fail,
                             "a_failure_corrected": new_fail})
        # never overwrite the historical file
        (HERE / "runs" / run / "generations_rescored.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rescored),
            encoding="utf-8")
        out[tag] = rescored
    return out


def contrast(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["condition"] in ("focal", "reference")
            and r["scorable"] and r["measured"] == "A"]


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else float("nan")


def boot(pairs, n_boot=10000, seed=20260810):
    by = defaultdict(list)
    for cluster, value in pairs:
        by[cluster].append(value)
    keys = sorted(by)
    if len(keys) < 2:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    draws = []
    for _ in range(n_boot):
        picked = [keys[rng.randrange(len(keys))] for _ in keys]
        vals = [v for k in picked for v in by[k]]
        draws.append(sum(vals) / len(vals))
    draws.sort()
    return draws[int(0.025 * n_boot)], draws[int(0.975 * n_boot) - 1]


def main() -> int:
    print("=" * 90)
    print("STEP 8 — RELIABILITY AND COUPLING, CORRECTLY NAMED")
    print("=" * 90)
    rel = reliability()
    print(f"  corpus items                     : {rel['n_items']}")
    print(f"  E_A  (target verifier error)     : {rel['E_A']:.4f} "
          f"over {rel['n_scorable_A']} scorable")
    print(f"  E_R  (semicolon verifier error)  : {rel['E_R']:.4f} "
          f"over {rel['n_scorable_R']} scorable")
    print(f"  U_A / U_R (unscorable share)     : {rel['U_A']:.4f} / {rel['U_R']:.4f}")
    print(f"  items excluded from the E_A denominator ({rel['n_items']} - "
          f"{rel['n_scorable_A']}): {rel['unscorable_kinds']}")
    print(f"  sentence-COUNT errors remaining  : {rel['count_errors']}")
    print()
    print(f"  kappa (PREREGISTERED joint-flip rate, in [0,1]) : "
          f"{rel['kappa_prereg_jointflip']:.4f} "
          f"over {rel['n_informative_for_kappa']} informative responses")
    print(f"  U_kappa (95% bootstrap)                         : "
          f"[{rel['U_kappa'][0]:.4f}, {rel['U_kappa'][1]:.4f}]")
    print(f"  agreement_phi (signed diagnostic, NOT kappa)    : "
          f"{rel['agreement_phi_signed_diagnostic']:.4f}")

    print()
    print("=" * 90)
    print("STEPS 9-10 — RESCORE, AND WHICH CONCLUSIONS MOVE")
    print("=" * 90)
    data = rescore()

    for tag, rows in data.items():
        c = contrast(rows)
        changed = sum(1 for r in c if r["observed_old"] != r["observed_corrected"])
        flipped = sum(1 for r in c if r["a_failure_old"] != r["a_failure_corrected"])
        trans = Counter((r["observed_old"], r["observed_corrected"]) for r in c
                        if r["observed_old"] != r["observed_corrected"])
        print(f"\n### {tag}: {len(c)} contrast rows | counts changed {changed} | "
              f"F_A flipped {flipped}")
        print(f"    transitions old->corrected: {dict(sorted(trans.items()))}")
        cells = defaultdict(lambda: {"n": 0, "old": 0, "new": 0, "coll_old": 0,
                                     "coll_new": 0})
        for r in c:
            key = (r.get("scaffold", "") or "none", r["order"], r["arm"])
            cell = cells[key]
            cell["n"] += 1
            cell["old"] += r["a_failure_old"]
            cell["new"] += r["a_failure_corrected"]
            cell["coll_old"] += int(r["observed_old"] <= 2)
            cell["coll_new"] += int(r["observed_corrected"] <= 2)
        print(f"    {'cell':42s} {'n':>4s} {'F_A old':>8s} {'F_A corr':>9s} "
              f"{'delta':>7s} {'coll old':>9s} {'coll corr':>10s}")
        for key in sorted(cells):
            cell = cells[key]
            o, nw = cell["old"] / cell["n"], cell["new"] / cell["n"]
            co, cn = cell["coll_old"] / cell["n"], cell["coll_new"] / cell["n"]
            print(f"    {'/'.join(key):42s} {cell['n']:4d} {o:8.3f} {nw:9.3f} "
                  f"{nw - o:+7.3f} {co:9.3f} {cn:10.3f}")

    # ---------------- claims A-E -------------------------------------------
    print("\n" + "=" * 90)
    print("CLAIM SURVIVAL UNDER CORRECTED SCORING")
    print("=" * 90)
    b = contrast(data["stageB"])
    outcome = {}
    for which in ("old", "corrected"):
        outcome[which] = {(r["pair_key"], r["arm"]): r[f"a_failure_{which}"] for r in b}
    keys = {k for k, _ in outcome["old"]}
    task_of = {r["pair_key"]: r["task_id"] for r in b}

    print("\nClaim A — B and S_SEMICOLON disproportionately produce collapse (<=2):")
    for arm in ("B", "S_SEMICOLON", "C_L3", "C_O2", "C_W3"):
        sel = [r for r in b if r["arm"] == arm]
        print(f"    {arm:12s} collapse old={mean(int(r['observed_old'] <= 2) for r in sel):.3f} "
              f"corrected={mean(int(r['observed_corrected'] <= 2) for r in sel):.3f}")

    print("\nClaim B — ordinary references fail by a DIFFERENT mode (overshoot):")
    for arm in ("B", "S_SEMICOLON", "C_L3", "C_O2", "C_W3"):
        sel = [r for r in b if r["arm"] == arm and r["a_failure_corrected"] == 1]
        over = sum(1 for r in sel if r["observed_corrected"] > N_TARGET)
        coll = sum(1 for r in sel if r["observed_corrected"] <= 2)
        print(f"    {arm:12s} corrected failures={len(sel):3d}  overshoot={over:3d}  "
              f"collapse={coll:3d}")

    print("\nClaim D — the order asymmetry on the focal arm:")
    for order in ("o_A", "o_Q"):
        sel = [r for r in b if r["arm"] == "B" and r["order"] == order]
        print(f"    {order}: old={mean(r['a_failure_old'] for r in sel):.4f} "
              f"corrected={mean(r['a_failure_corrected'] for r in sel):.4f}")

    print("\n  tau_j (B - reference), pooled, with corrected CIs:")
    for reference in ("C_L3", "C_O2", "C_W3", "S_SEMICOLON"):
        pairs_old, pairs_new = [], []
        for k in keys:
            if (k, "B") in outcome["old"] and (k, reference) in outcome["old"]:
                pairs_old.append(outcome["old"][(k, "B")] - outcome["old"][(k, reference)])
                pairs_new.append((task_of[k],
                                  outcome["corrected"][(k, "B")]
                                  - outcome["corrected"][(k, reference)]))
        lo, hi = boot(pairs_new)
        print(f"    B - {reference:12s} old={mean(pairs_old):+.4f}  "
              f"corrected={mean(v for _, v in pairs_new):+.4f}  "
              f"CI [{lo:+.4f}, {hi:+.4f}]")

    print("\nClaim C — scaffold removes B's excess over C_L3 (D2):")
    d2 = contrast(data["D2"])
    for scaffold in ("", "one_sentence_per_line"):
        for order in ("o_A", "o_Q"):
            ctrl = {r["pair_key"]: r for r in d2
                    if r.get("scaffold", "") == scaffold and r["order"] == order
                    and r["arm"] == "C_L3"}
            for arm in ("B", "S_SEMICOLON"):
                sel = {r["pair_key"]: r for r in d2
                       if r.get("scaffold", "") == scaffold and r["order"] == order
                       and r["arm"] == arm}
                shared = sorted(set(ctrl) & set(sel))
                old = mean(sel[k]["a_failure_old"] - ctrl[k]["a_failure_old"]
                           for k in shared)
                new_pairs = [(sel[k]["task_id"],
                              sel[k]["a_failure_corrected"]
                              - ctrl[k]["a_failure_corrected"]) for k in shared]
                lo, hi = boot(new_pairs)
                print(f"    {(scaffold or 'none'):22s} {order} {arm:12s} "
                      f"old={old:+.4f} corrected={mean(v for _, v in new_pairs):+.4f} "
                      f"CI [{lo:+.4f}, {hi:+.4f}]")

    print("\nClaim E — corrected verifier on collapse-relevant structures:")
    print(f"    sentence-count errors on the gold corpus: {rel['count_errors'] or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
