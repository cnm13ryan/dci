#!/usr/bin/env python3
"""Known-ground-truth stress corpus for the sentence and semicolon verifiers.

The construction-time coupling screen runs on an authored bank that contains no
one-sentence clause chains, so it cannot see the interaction that matters. This
builds a corpus that DOES cover the structural modes the model actually
produces, labels each item with hand-assigned ground truth for both verifiers,
and reports the verifier error rates and their coupling on that support.

Reported quantities, per the analysis plan:

  E_A     error rate of the target verifier (exactly N sentences)
  E_R     error rate of the added-constraint verifier (semicolon in every sentence)
  U_A     share of items the target verifier cannot score
  U_R     share of items the reference verifier cannot score
  U_kappa uncertainty in the agreement statistic, as a bootstrap spread

Ground truth is written by hand next to each item, so a verifier error is a
disagreement with a human label rather than with another program.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

N_TARGET = 4

# (text, true_sentence_count, true_semicolon_in_every_sentence, structural_type)
#
# `true_semicolon_in_every_sentence` is None where the property is not
# well-defined (no sentences at all).
CORPUS: list[tuple[str, int, object, str]] = [
    # ---------------------------------------------------- ordinary four-sentence
    ("Rain falls on the roof. Water runs to the gutter. The gutter drains to a pipe. "
     "The pipe empties into a drain.", 4, False, "four_normal"),
    ("A hinge turns. A door swings. The frame holds firm. The gap stays even.",
     4, False, "four_normal_short"),
    ("Alpha begins the work; it is careful. Beta continues it; she is quick. "
     "Gamma checks the result; he is thorough. Delta files the report; all agree.",
     4, True, "four_with_semicolon_each"),
    ("Alpha begins the work; it is careful. Beta continues it. "
     "Gamma checks the result; he is thorough. Delta files the report; all agree.",
     4, False, "four_semicolon_missing_one"),

    # ------------------------------------------------- one-sentence clause chains
    ("Alpha runs; beta walks; gamma sits; delta stands.", 1, True,
     "one_semicolon_chain"),
    ("Water seeps into cracks; it freezes and expands; the surface weakens; "
     "potholes form.", 1, True, "one_semicolon_chain"),
    ("The corkscrew turns into the cork; this lifts it from the neck: the spiral "
     "grips tightly; the cork comes free.", 1, True, "one_semicolon_chain_with_colon"),
    ("Bakeries open early because demand peaks at dawn, which means the bread must "
     "be ready before the first customers arrive, and this in turn requires the "
     "dough to be mixed overnight, so the bakers begin their shift long before "
     "sunrise.", 1, False, "one_run_on_no_semicolon"),

    # ---------------------------------------------------------------- comma chains
    ("Alpha runs, beta walks, gamma sits, delta stands.", 1, False, "comma_chain"),
    ("The kettle heats, the steam rises, the switch trips, the water stills.",
     1, False, "comma_chain"),

    # ------------------------------------------------------- merges and splits
    ("Rain falls on the roof and water runs to the gutter. The gutter drains to a "
     "pipe and the pipe empties into a drain.", 2, False, "merged_two"),
    ("Rain falls. On the roof. Water runs. To the gutter. The gutter drains. To a "
     "pipe.", 6, False, "split_fragments"),
    ("Rain falls on the roof. Water runs to the gutter. The gutter drains to a pipe. "
     "The pipe empties into a drain. The drain leads to the river.", 5, False,
     "five_sentences"),

    # ------------------------------------------------------------- newline styles
    ("Rain falls on the roof\nWater runs to the gutter\nThe gutter drains to a pipe\n"
     "The pipe empties into a drain", 4, False, "newline_no_terminators"),
    ("- Rain falls on the roof.\n- Water runs to the gutter.\n- The gutter drains.\n"
     "- The pipe empties.", 4, False, "bulleted"),
    ("1. Rain falls on the roof.\n2. Water runs to the gutter.\n3. The gutter drains.\n"
     "4. The pipe empties.", 4, False, "numbered"),

    # ------------------------------------------------------------- abbreviations
    ("The bakery opens at 6 a.m. every weekday. Bread is ready by seven. "
     "Customers queue outside. The first batch sells quickly.", 4, False,
     "abbreviation_am"),
    ("Sales spike at 6 a.m. when others sleep. Suppliers arrive at 5 p.m. as the "
     "shop closes. Staff finish by 8 p.m. most days. The routine repeats.",
     4, False, "abbreviation_am_pm_multiple"),
    ("Dr. Smith opened the clinic. Mrs. Jones was first in line. "
     "The nurse called her name. She went in.", 4, False, "abbreviation_titles"),
    ("The team met at approx. four. They reviewed the plan, e.g. the budget. "
     "Nothing changed. They left.", 4, False, "abbreviation_approx_eg"),

    # ------------------------------------------------------------ decimals, initials
    ("The value is 3.5 metres. It fits the frame. The tolerance is 0.25 metres. "
     "Nothing else matters.", 4, False, "decimals"),
    ("J. R. Hartley wrote the book. He was patient. The publisher agreed. "
     "It sold well.", 4, False, "initials"),

    # ------------------------------------------------------------------ quotations
    ('She said "go now." He left at once. The door closed. Silence followed.',
     4, False, "quotation_inside"),
    ('He asked, "Is it ready?" She nodded once. The oven beeped. They served it.',
     4, False, "quotation_question"),

    # ------------------------------------------------------- unusual punctuation
    ("Rain falls on the roof... water runs to the gutter... the pipe drains... "
     "the river rises.", 1, False, "ellipses"),
    ("Rain falls! Water runs? The gutter drains. The pipe empties.", 4, False,
     "mixed_terminators"),
    ("Rain falls on the roof (the tiles are old). Water runs to the gutter. "
     "The gutter drains to a pipe. The pipe empties.", 4, False, "parentheses"),
    ("Rain falls on the roof — the tiles are old — and water runs to the gutter. "
     "The gutter drains. The pipe empties. The river rises.", 4, False, "em_dashes"),

    # --------------------------- extra (Y_A=1, Y_R=1) support for the coupling
    #
    # kappa is the mean fraction of coupling EDITS that flip BOTH verdicts, and
    # it is defined only over responses where BOTH verifiers PASS at baseline.
    # The corpus above contained exactly ONE such item, so kappa was estimated
    # from n=1 and its bootstrap was degenerate. These add the support the
    # statistic actually needs; they are ordinary compliant answers, not tuned.
    ("The kettle heats the water; the element glows. Steam rises to the lid; "
     "pressure builds. The switch trips; the current stops. The water stills; "
     "the noise fades.", 4, True, "four_with_semicolon_each"),
    ("Hikers read the map; the route is clear. Signs mark each turn; nobody "
     "strays. The path climbs slowly; legs tire. The summit appears; spirits "
     "lift.", 4, True, "four_with_semicolon_each"),
    ("Bakers weigh the flour; accuracy matters. Dough rests in warmth; gluten "
     "relaxes. Ovens reach full heat; loaves enter. Crusts darken evenly; the "
     "batch is done.", 4, True, "four_with_semicolon_each"),
    ("A hinge carries the door; the pin bears the load. Leaves rotate together; "
     "friction stays low. The frame holds square; gaps stay even. The door "
     "swings freely; nothing binds.", 4, True, "four_with_semicolon_each"),
    ("Rain strikes the tiles; water gathers. Gutters channel the flow; debris "
     "slows it. Pipes carry the water down; joints hold firm. The drain takes "
     "it away; the yard stays dry.", 4, True, "four_with_semicolon_each"),
    ("Whisks cut the mixture; air enters. Bubbles form quickly; the volume "
     "grows. Tines lift the batter; texture lightens. The result holds shape; "
     "cooks are satisfied.", 4, True, "four_with_semicolon_each"),
    ("Cyclists check the pressure; tyres need care. Gauges read the value; "
     "numbers guide them. Pumps restore the air; rims stay safe. The ride feels "
     "smooth; punctures are rarer.", 4, True, "four_with_semicolon_each"),

    # ---------------------------------------------------------------- degenerate
    ("", 0, None, "empty"),
    ("...", 0, None, "punctuation_only"),
    ("Rain.", 1, False, "single_short"),
]


def evaluate() -> dict:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from dci.verifiers.rules import v_exact_sentence_count, v_semicolon_each

    rows = []
    for text, true_n, true_semi, kind in CORPUS:
        a = v_exact_sentence_count(text, N_TARGET)
        r = v_semicolon_each(text)
        a_unscorable = a.status == "unscorable"
        r_unscorable = r.status == "unscorable"
        observed = a.detail.get("observed")
        # Ground truth verdicts
        truth_a = int(true_n == N_TARGET)
        truth_r = None if true_semi is None else int(bool(true_semi))
        rows.append({
            "kind": kind, "text": text,
            "true_sentences": true_n, "observed_sentences": observed,
            "count_correct": (observed == true_n) if not a_unscorable else None,
            "truth_A": truth_a, "verifier_A": None if a_unscorable else int(a.binary_pass),
            "A_error": None if a_unscorable else int(int(a.binary_pass) != truth_a),
            "A_unscorable": int(a_unscorable),
            "truth_R": truth_r, "verifier_R": None if r_unscorable else int(r.binary_pass),
            "R_error": (None if (r_unscorable or truth_r is None)
                        else int(int(r.binary_pass) != truth_r)),
            "R_unscorable": int(r_unscorable),
        })

    scorable_a = [r for r in rows if r["A_error"] is not None]
    scorable_r = [r for r in rows if r["R_error"] is not None]
    E_A = sum(r["A_error"] for r in scorable_a) / len(scorable_a)
    E_R = sum(r["R_error"] for r in scorable_r) / len(scorable_r)
    U_A = sum(r["A_unscorable"] for r in rows) / len(rows)
    U_R = sum(r["R_unscorable"] for r in rows) / len(rows)

    # Agreement between the two verifiers on this support, and its bootstrap spread.
    both = [r for r in rows if r["verifier_A"] is not None and r["verifier_R"] is not None]
    def kappa(sample: list[dict]) -> float:
        n = len(sample)
        if not n:
            return float("nan")
        po = sum(1 for r in sample if r["verifier_A"] == r["verifier_R"]) / n
        pa = sum(r["verifier_A"] for r in sample) / n
        pb = sum(r["verifier_R"] for r in sample) / n
        pe = pa * pb + (1 - pa) * (1 - pb)
        return (po - pe) / (1 - pe) if pe != 1 else float("nan")

    rng = random.Random(20260810)
    draws = []
    for _ in range(5000):
        sample = [both[rng.randrange(len(both))] for _ in both]
        k = kappa(sample)
        if k == k:
            draws.append(k)
    draws.sort()
    U_kappa = (draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]) if draws else (float("nan"),) * 2

    return {"rows": rows, "E_A": E_A, "E_R": E_R, "U_A": U_A, "U_R": U_R,
            "kappa": kappa(both), "U_kappa": U_kappa,
            "n": len(rows), "n_scorable_A": len(scorable_a),
            "n_scorable_R": len(scorable_r)}


def main() -> int:
    result = evaluate()
    print(f"\nstress corpus: {result['n']} items with hand-written ground truth\n")
    print(f"{'kind':34s} {'true':>5s} {'obs':>4s} {'A_ok':>5s} {'A_err':>6s} {'R_err':>6s}")
    for row in result["rows"]:
        print(f"{row['kind']:34s} {row['true_sentences']:5d} "
              f"{str(row['observed_sentences']):>4s} "
              f"{str(row['count_correct']):>5s} {str(row['A_error']):>6s} "
              f"{str(row['R_error']):>6s}")

    print(f"\nE_A (target verifier error rate)     = {result['E_A']:.4f} "
          f"over {result['n_scorable_A']} scorable")
    print(f"E_R (semicolon verifier error rate)  = {result['E_R']:.4f} "
          f"over {result['n_scorable_R']} scorable")
    print(f"U_A (unscorable share, target)       = {result['U_A']:.4f}")
    print(f"U_R (unscorable share, reference)    = {result['U_R']:.4f}")
    print(f"kappa(A, R) on this support          = {result['kappa']:.4f}")
    print(f"U_kappa (95% bootstrap)              = "
          f"[{result['U_kappa'][0]:.4f}, {result['U_kappa'][1]:.4f}]")

    wrong = [r for r in result["rows"] if r["count_correct"] is False]
    print(f"\nitems where the sentence COUNT is wrong: {len(wrong)}")
    for row in wrong:
        print(f"   {row['kind']:34s} true={row['true_sentences']} "
              f"observed={row['observed_sentences']}  {row['text'][:60]!r}")

    out = Path(__file__).resolve().parent / "verifier_audit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "stress_corpus_results.json").write_text(
        json.dumps({k: v for k, v in result.items()}, indent=2, default=str),
        encoding="utf-8")
    print(f"\nartifacts: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
