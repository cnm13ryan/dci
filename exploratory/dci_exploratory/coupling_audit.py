"""Why did the construction-time coupling screen score S_SEMICOLON at 0.00?

The screen is `S.COUPLING`, computed in stage c162 from `S.RESPONSE_BANK` — a
model-free corpus of authored responses. It measures whether two verifiers agree
across that corpus. A verifier interaction it never sees, it cannot score.

This module compares the STRUCTURAL TYPES present in the authored bank with the
ones the model actually produced, and checks the specific claim: that the bank
contains no answer in which semicolons stand where sentence boundaries would.

This is an exploratory methodological finding about the construction procedure.
Nothing here modifies the confirmatory pipeline.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd


def _classify(text: str, n_target: int) -> str:
    """Structural type of one response, using the protocol's own segmenter."""
    from dci.verifiers.rules import split_sentences, word_tokens

    sentences = split_sentences(text)
    n = len(sentences)
    semis = text.count(";")
    if n == 0:
        return "empty"
    if n == 1:
        if semis >= 1:
            return "one_sentence_semicolon_chain"
        if len(word_tokens(text)) > 40:
            return "one_sentence_run_on"
        return "one_short_sentence"
    if n == n_target:
        return ("n_sentences_with_semicolons" if semis >= 1
                else "n_normal_sentences")
    if n < n_target:
        return "under_target_2_to_3"
    return "over_target"


def audit(run_dir: Path) -> dict[str, Any]:
    from dci_exploratory import harvest

    S = harvest.load()
    run_dir = Path(run_dir)
    frame = pd.read_json(run_dir / "generations.jsonl", lines=True)
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    n_target = int(config["harvest_provenance"]["exact_sentence_count"])

    bank = list(S.RESPONSE_BANK)
    corpus = list(getattr(S, "SYNTHETIC_CORPUS", []))
    generated = [t for t in frame["response"].dropna().tolist() if t.strip()]

    def tally(texts: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for text in texts:
            counts[_classify(text, n_target)] = counts.get(
                _classify(text, n_target), 0) + 1
        return counts

    bank_counts, corpus_counts, gen_counts = (
        tally(bank), tally(corpus), tally(generated))

    # The specific gap: answers where a semicolon stands where a sentence
    # boundary would, i.e. one segment containing at least one semicolon.
    def chain_share(texts: list[str]) -> float:
        if not texts:
            return float("nan")
        return sum(1 for t in texts
                   if _classify(t, n_target) == "one_sentence_semicolon_chain") / len(texts)

    # What the screen would have said had the bank contained the observed mode.
    effect: dict[str, Any] = {}
    for cid in ("S_SEMICOLON", "B", "C_L3", "C_O2", "C_W3"):
        rows = frame[(frame["arm"] == cid)
                     & frame["condition"].isin(["focal", "reference"])
                     & frame["scorable"]]
        effect[cid] = {
            "construction_coupling_with_A": float(S.COUPLING.get(cid, float("nan"))),
            "observed_A_failure_rate": (float(rows["a_failure"].mean())
                                        if len(rows) else None),
            "observed_semicolon_chain_share": chain_share(
                [t for t in rows["response"].dropna().tolist() if t.strip()]),
        }

    types = sorted(set(bank_counts) | set(corpus_counts) | set(gen_counts))
    table = pd.DataFrame([{
        "response_structure": t,
        "in_coupling_bank": bank_counts.get(t, 0),
        "in_synthetic_corpus": corpus_counts.get(t, 0),
        "in_model_generations": gen_counts.get(t, 0),
    } for t in types])
    table["present_in_bank"] = table["in_coupling_bank"] > 0
    table["present_in_generations"] = table["in_model_generations"] > 0
    table["gap"] = (~table["present_in_bank"]) & table["present_in_generations"]

    return {
        "n_response_bank": len(bank),
        "n_synthetic_corpus": len(corpus),
        "n_model_generations": len(generated),
        "semicolon_chain_share_in_bank": chain_share(bank),
        "semicolon_chain_share_in_corpus": chain_share(corpus),
        "semicolon_chain_share_in_generations": chain_share(generated),
        "bank_texts_containing_a_semicolon": sum(1 for t in bank if ";" in t),
        "corpus_texts_containing_a_semicolon": sum(1 for t in corpus if ";" in t),
        "table": table,
        "per_constraint": effect,
    }


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Coupling-bank coverage audit.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)
    result = audit(args.run_dir)
    pd.set_option("display.width", 200)

    print("\n=== COUPLING-BANK COVERAGE ===")
    print(f"authored response bank   : {result['n_response_bank']} texts, "
          f"{result['bank_texts_containing_a_semicolon']} contain a ';'")
    print(f"synthetic probe corpus   : {result['n_synthetic_corpus']} texts, "
          f"{result['corpus_texts_containing_a_semicolon']} contain a ';'")
    print(f"model generations        : {result['n_model_generations']} texts")
    print()
    print(result["table"].to_string(index=False))
    print()
    print("share of texts that are a ONE-SENTENCE SEMICOLON CHAIN:")
    print(f"  authored coupling bank : {result['semicolon_chain_share_in_bank']:.4f}")
    print(f"  synthetic corpus       : {result['semicolon_chain_share_in_corpus']:.4f}")
    print(f"  model generations      : {result['semicolon_chain_share_in_generations']:.4f}")
    print()
    print("=== construction-time score vs observed behaviour ===")
    print(pd.DataFrame(result["per_constraint"]).T.to_string())

    out = Path(args.run_dir) / "forensics"
    out.mkdir(parents=True, exist_ok=True)
    result["table"].to_csv(out / "coupling_bank_coverage.csv", index=False)
    (out / "coupling_bank_audit.json").write_text(json.dumps(
        {k: v for k, v in result.items() if k != "table"}, indent=2, default=str),
        encoding="utf-8")
    print(f"\nartifacts: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
