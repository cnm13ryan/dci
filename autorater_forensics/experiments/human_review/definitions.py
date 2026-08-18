"""Fixed reviewer-facing definitions (PREREGISTERED.md E5/E6/E7).

These are the ONLY task-semantic texts a blind reviewer sees before
committing a judgment. They mirror the registered constraint semantics
of DCI-1 v3 (an occurrence-count instruction over the response text);
they deliberately do not mention the deterministic verifier, the model
judge, reasoning efforts, or any prior label.
"""

SATISFIES_DEF = (
    "SATISFIES: the response text obeys the instruction — the word "
    "'however' occurs in the response exactly the required number of "
    "times.")

VIOLATES_DEF = (
    "VIOLATES: the response text does not obey the instruction — the "
    "word 'however' occurs more or fewer times than required.")

EDGE_RULES = (
    "Edge-case rules (fixed in advance):\n"
    "  1. Count occurrences in the response text only, never in the "
    "instruction itself.\n"
    "  2. Counting is case-insensitive ('However' and 'HOWEVER' "
    "count).\n"
    "  3. The word counts with attached punctuation ('however,' "
    "'However.' count).\n"
    "  4. 'however' embedded inside a longer word does not count.\n"
    "  5. Count every occurrence, including in quotations, headings, "
    "lists, or repeated phrases.\n"
    "  6. If you cannot reach a judgment, answer U (unsure); this is "
    "recorded as an abstention, never converted to a label.")
