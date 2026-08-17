"""Registered annotator-facing materials (§25): written instructions and
twelve worked examples, plus the face-validity statement of §10.

The instructions ask for the plain reading of the constraint as written;
they deliberately teach no verifier mechanics (run boundaries, substring
rules, class structure), so the human judgment stays an independent
measurement of the same requirement. The worked examples demonstrate the
plain reading on uncontroversial cases and leave genuinely ambiguous edges
to the annotator's own judgment.
"""
from __future__ import annotations

RUBRIC_VERSION = "1.0.0"

INSTRUCTIONS = """\
You will judge a series of items. Each item shows one rule and one
response. Your task, for every item, is to answer a single question:

    Taken as a whole, exactly as shown, does the response satisfy the
    rule as written?

Press 1 for SATISFIES, 2 for VIOLATES. Every item needs one of these two
answers. Press F to flag an item you want to come back to; a flag is a
note to yourself and is not an answer. You can move back and forth and
change any answer until you submit.

Judge only the rule shown. Ignore the response's style, factual accuracy,
completeness, or quality. Read the whole response, including any opening
or closing remarks; the rule applies to all of it. Count by reading; do
not use search tools or scripts. There is no trick: the rule means what
it plainly says.

Work at your own pace. Your answers are saved as you go and belong to you
alone; nobody else's answers are visible here, and nothing about how any
item was produced or pre-scored is shown to you.
"""

#: Twelve worked examples (§25): the plain reading on clear cases.
PRACTICE_EXAMPLES = (
    {"constraint": "Use the word however exactly 2 times.",
     "response": "The plan was sound. However, the costs rose sharply. "
                 "However, the team pressed on.",
     "answer": "SATISFIES",
     "note": "Reading the whole response, the word appears twice, and the "
             "rule asks for exactly two."},
    {"constraint": "Use the word however exactly 2 times.",
     "response": "The plan was sound and the costs stayed low.",
     "answer": "VIOLATES",
     "note": "The word never appears; the rule asked for exactly two."},
    {"constraint": "Use the word however exactly 1 time.",
     "response": "However you look at it, the answer is the same.",
     "answer": "SATISFIES",
     "note": "It appears once, at the start of a sentence; a capital "
             "letter does not make it a different word."},
    {"constraint": "Use the word however exactly 1 time.",
     "response": "The result, however, surprised us. It was, however, "
                 "welcome news.",
     "answer": "VIOLATES",
     "note": "It appears twice; the rule asked for exactly one."},
    {"constraint": "Use the word however exactly 3 times.",
     "response": "Rivers shape valleys slowly. However, floods can act "
                 "fast. However, ice works faster still; however, wind "
                 "outlasts them all.",
     "answer": "SATISFIES",
     "note": "Three appearances; commas and semicolons around the word "
             "do not change the count."},
    {"constraint": "Use the word however exactly 2 times.",
     "response": "Maps grew more accurate over time. However, early "
                 "sailors managed well without them.",
     "answer": "VIOLATES",
     "note": "Only one appearance; the rule asked for exactly two."},
    {"constraint": "Use the word however exactly 1 time.",
     "response": "",
     "answer": "VIOLATES",
     "note": "An empty response contains the word zero times."},
    {"constraint": "Use the word however exactly 2 times.",
     "response": "**However** the picture improves with light. However "
                 "briefly, colours deepen at dusk.",
     "answer": "SATISFIES",
     "note": "Formatting marks around the word do not remove it; it "
             "appears twice."},
    {"constraint": "Use the word however exactly 1 time.",
     "response": "I cannot help with that request.",
     "answer": "VIOLATES",
     "note": "Whatever else the response is, the word appears zero "
             "times."},
    {"constraint": "Use the word however exactly 4 times.",
     "response": "Bread rises from yeast. However, heat sets the crumb. "
                 "However, steam softens crust. However, salt slows "
                 "yeast. However, time deepens flavour.",
     "answer": "SATISFIES",
     "note": "Four appearances, as the rule requires."},
    {"constraint": "Use the word however exactly 1 time.",
     "response": "Tides follow the moon closely, and the weather howev",
     "answer": "VIOLATES",
     "note": "The response breaks off before the word is complete; the "
             "word itself never appears."},
    {"constraint": "Use the word however exactly 2 times.",
     "response": "HOWEVER the cost fell. However, time ran short.",
     "answer": "SATISFIES",
     "note": "Capital letters do not make it a different word; it "
             "appears twice."},
)
assert len(PRACTICE_EXAMPLES) == 12

#: §10 face validity: the plain-language statement of the primary scoring
#: rule, judged against the constraint template after all items are done.
FACE_VALIDITY_STATEMENT = (
    "The automated score reads the complete response text, including any "
    "preamble or trailing remark, without regard to letter case; it counts "
    "how many times the word however appears as a whole word; and it "
    "passes the response exactly when that count equals the number stated "
    "in the constraint.")

FACE_VALIDITY_CONSTRAINT_TEMPLATE = "Use the word however exactly n times."

FACE_VALIDITY_QUESTION = (
    "Does this statement match the constraint text as written?")
