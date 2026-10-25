"""Write the D01 v2 candidate library specification (revision 2026-10).

A specification, not an implementation: every candidate names an existing
verifier family (new parameter values) or a NEW family to be implemented and
tested before any measurement. Difficulty is never assumed: every candidate
is screened (Stage A) before it can be matched.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "candidate_library_v2.json"
MAN = json.loads((Path(__file__).resolve().parents[2] / "library_manifest.json").read_text())
existing = {r["cid"]: r for r in MAN["references"]}

EXISTING_SHORT = ["indeed", "instead", "perhaps", "although", "moreover"]
NEW_WORDS = ["thus", "hence", "besides", "anyway", "likewise", "overall", "notably", "namely"]
COUNTS = [2, 3, 4, 5, 6]
rows = []

def add(cid, family, verifier, operation, obj, params, population, rationale, new_family=False):
    rows.append({"cid": cid, "status": "existing" if cid in existing else "candidate",
                 "family_id": family, "verifier_id": verifier,
                 "verifier_status": "NEW (to implement and self-test)" if new_family else "existing family, new parameters" if cid not in existing else "existing",
                 "operation": operation, "object_type": obj, "params": params,
                 "intended_population": population, "rationale": rationale})

# 1. Same operation and object as A (exact count of a target word): G2, matched into G1 (P1).
for w in EXISTING_SHORT + NEW_WORDS:
    for n in COUNTS:
        add(f"ew.{w}.{n}", "exact_word_count", "b1.exact_word_count", "exact_count", "word",
            {"word": w, "n": n}, "G2 (P1); G1 when matched",
            "count ladder on a discourse connective of <= 8 letters, so compatible with both B limits; "
            "a 5-level ladder per word gives each word several chances to land within +/-0.10 of A in every model-frame")
for cid in ("ew.therefore.2", "ew.therefore.4", "ew.therefore.6", "ew.nonetheless.2", "ew.nonetheless.4",
            "ew.consequently.2", "ew.consequently.4"):
    add(cid, "exact_word_count", "b1.exact_word_count", "exact_count", "word", existing[cid]["params"],
        "G2 (P1) where compatible", "kept unchanged; incompatible with B 8 (all three) and B 10 (nonetheless, consequently) by proof")

# 2. Same operation, other object types (P2).
for ch, name, ns in ((";", "semicolon", [1, 2, 3, 4]), (":", "colon", [1, 2, 3]), ("?", "question", [1, 2, 3]),
                     ("!", "exclaim", [1, 2, 3]), ("(", "paren", [1, 2, 3]), (",", "comma", [3, 6])):
    for n in ns:
        add(f"ec.{name}.{n}", "exact_char_count", "b1.exact_char_count", "exact_count", "punctuation",
            {"char": ch, "n": n}, "G4 (P2 other object); G3 when matched",
            "punctuation-count ladder; no word, so compatible with any B limit")
for n in (3, 4, 5, 6, 7, 8, 9):
    add(f"es.{n}", "exact_sentence_count", "b1.exact_sentence_count", "exact_count", "sentence", {"n": n},
        "G4 (P2 other object); G3 when matched", "sentence-count ladder; Qwen models were at ceiling at 4 and 7, Gemma at 0.2-0.7")
for n in (2, 3, 4, 5, 6):
    add(f"ep.{n}", "exact_paragraph_count", "b1.exact_paragraph_count", "exact_count", "paragraph", {"n": n},
        "G4 (P2 other object); G3 when matched", "2 and 3 were at 1.00 everywhere; 4-6 paragraphs in 60-120 words are untested")
for n in (1, 2, 3):
    add(f"en.{n}", "exact_numeral_count", "b1.exact_numeral_count (NEW)", "exact_count", "numeral", {"n": n},
        "G4 (P2 other object); G3 when matched",
        "a new object type: tokens written as digits; digits are not letters, so B is unaffected", new_family=True)

# 3. Other operations (P3).
for L in ("z", "b", "q", "x", "j", "k", "v"):
    add(f"pro.letter.{L}", "forbid_letter", "b1.forbid_letter", "prohibition", "letter", {"letter": L},
        "G6 (P3 other operation); G5 when matched", "letter-avoidance ladder ordered by English letter frequency (z 0.5-0.7 and b 0.0-0.1 measured)")
for ws in (["the"], ["very", "really", "just"], ["also"], ["this"]):
    add("pro.word." + "+".join(ws), "forbid_words", "b1.forbid_words", "prohibition", "word", {"words": ws},
        "G6 (P3 other operation); G5 when matched", "word-avoidance ladder; candidate words must not occur in any topic (hygiene)")
for ws in (["simple"], ["window", "garden"], ["silver", "morning", "quiet"], ["remarkable"],
           ["pebble", "velvet"], ["meadow", "candle", "ribbon"], ["walnut", "saddle", "beacon", "canyon"],
           ["harbor", "marble", "feather", "thimble", "ember"]):
    add("inc." + "+".join(ws), "include_words", "b1.include_words", "required_inclusion", "word", {"words": ws},
        "G6 (P3 other operation); G5 when matched", "inclusion ladder by number of unrelated words (1-3 were at 0.7-1.0); every word <= 8 letters and absent from all topics")
for bound, k in (("max", 6), ("max", 8), ("max", 10), ("max", 12), ("max", 20), ("min", 10), ("min", 12), ("min", 14), ("min", 16)):
    add(f"nb.{bound}{k}", "sentence_word_bound", "b1.sentence_word_bound", "numerical_bound", "sentence",
        {"bound": bound, "k": k}, "G6 (P3 other operation); G5 when matched", "sentence-length ladder (max 12/20 near ceiling; min 10 at 0.16-1.0)")
for ml in (4, 5, 6, 7):
    add(f"unq.word{ml}", "no_repeated_words", "b1.no_repeated_words", "uniqueness", "word", {"min_letters": ml},
        "G6 (P3 other operation); G5 when matched", "uniqueness ladder by word length (5 letters was at floor); vacuity rule min_words applies")
add("unq.bigram", "no_repeated_bigrams", "b1.no_repeated_bigrams", "uniqueness", "word_sequence", {}, "G6 (P3)", "kept")
for ms in (3, 4, 5, 6):
    add(f"unq.opener{ms}", "distinct_openers", "b1.distinct_openers", "uniqueness", "sentence", {"min_sentences": ms},
        "G6 (P3 other operation); G5 when matched", "distinct-opener ladder (3 was at 0.5-1.0)")
for d, ms in (("inc", 3), ("inc", 4), ("inc", 6), ("dec", 3), ("dec", 4)):
    add(f"ord.{d}{ms}", "length_order", "b1.length_order", "ordering", "sentence",
        {"direction": "increasing" if d == "inc" else "decreasing", "min_sentences": ms},
        "G6 (P3 other operation); G5 when matched", "length-order ladder: 4 and 6 were at floor, so 3 is added")
for ms in (3, 4, 5):
    add(f"ord.alpha{ms}", "alphabetical_openers", "b1.alphabetical_openers", "ordering", "sentence", {"min_sentences": ms},
        "G6 (P3 other operation); G5 when matched", "alphabetical-opener ladder (4 was at 0.0-0.5)")
for fam, short, ms in (("chain_word", "word", 2), ("chain_word", "word", 3), ("chain_letter", "letter", 2), ("chain_letter", "letter", 3)):
    add(f"rel.{short}{ms}", fam, f"b1.{fam}", "relational_dependency", "sentence_pair", {"min_sentences": ms},
        "G6 (P3 other operation); G5 when matched", "chain ladder: 3 sentences were at floor, so 2 is added")
for ml, ms in ((3, 3), (4, 3), (5, 3), (4, 4)):
    add(f"rel.share{ml}" + ("" if ms == 3 else f".s{ms}"), "adjacent_shared_word", "b1.adjacent_shared_word",
        "relational_dependency", "sentence_pair", {"min_letters": ml, "min_sentences": ms},
        "G6 (P3 other operation); G5 when matched", "shared-word ladder (4 letters, 3 sentences was at 0.06-0.54)")
for cid, params, why in (("pos.start.word", {"word": "today"}, "begin the answer with a named word (<= 8 letters, absent from topics)"),
                         ("pos.end.question", {}, "end the answer with a question"),
                         ("pos.end.word", {"word": "onward"}, "end the answer with a named word")):
    add(cid, "positional", "b1.positional (NEW)", "positional", "answer_boundary", params,
        "G6 (P3 other operation); G5 when matched", why + "; a new operation that the brief lists and the library lacked", new_family=True)

seen = {r["cid"] for r in rows}
missing = sorted(set(existing) - seen)
assert not missing, missing
doc = {"schema": "dci.batch1/candidate-library/v2-proposal", "status": "PROPOSAL awaiting the researcher (D01 revision); nothing measured",
       "rules": ["every word target and required word has <= 8 letters, so no candidate is incompatible with B 8 or B 10 by proof (except the 7 kept long-word references)",
                 "every target word, required word and forbidden word must occur in no topic (bank v1, the reserved 480, and the fresh pilot topics); checked by the hygiene report before Freeze 1",
                 "every candidate's B compatibility is established by a constructed witness (compatibility.py), never by model behaviour",
                 "no candidate is assumed matched: Stage A measures it on fresh screening topics, and only Stage C topics decide membership",
                 "ladders give graded difficulty; parameters were chosen from where the existing families sat (floor/ceiling), not from where A sits"],
       "counts": {}, "candidates": rows}
from collections import Counter
doc["counts"] = {"total": len(rows), "existing": sum(r["status"] == "existing" for r in rows),
                 "new": sum(r["status"] == "candidate" for r in rows),
                 "by_operation_object": {f"{k[0]}/{k[1]}": v for k, v in sorted(Counter((r["operation"], r["object_type"]) for r in rows).items())},
                 "new_verifier_families": sorted({r["verifier_id"] for r in rows if "NEW" in r["verifier_id"]})}
OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(json.dumps(doc["counts"], indent=1))
