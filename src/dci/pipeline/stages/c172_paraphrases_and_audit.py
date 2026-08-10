"""Stage 172 — migrated from notebook cell 172.py (paraphrases_and_audit).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/172.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.provenance.hashes import sha_file  # noqa: F401
from dci.verifiers.rules import word_tokens  # noqa: F401

S.SYSTEM_MESSAGE = (
    "Produce only the requested answer. Do not discuss, restate, enumerate, "
    "or explain the constraints or your planning process."
)

# Semantic invariants every wording in a family must preserve. These are the
# audit checklist: a paraphrase that changes any listed property is a different
# constraint, and a wording effect would then be indistinguishable from a
# constraint effect.
GENERIC_INVARIANTS = (
    "quantifier (all / at least one / exactly)",
    "threshold value and its units",
    "scope (per sentence vs whole answer)",
    "relational direction (more / fewer / before / after)",
    "exact vs minimum vs maximum semantics",
    "exceptions (none are permitted unless stated in every wording)",
)


@dataclass(frozen=True)
class RuleFamily:
    name: str
    invariants: tuple[str, ...]
    templates: tuple[str, ...]


def _f(name: str, extra: tuple[str, ...], *templates: str) -> RuleFamily:
    """Six escalation-pool wordings. Two held-out wordings are appended below."""
    assert len(templates) == 6, (
        f"family {name} declares {len(templates)} pool templates; six are required")
    return RuleFamily(name, GENERIC_INVARIANTS + extra, templates)


S.RULE_FAMILIES: dict[str, RuleFamily] = {

    "exact_sentence_count": _f(
        "exact_sentence_count", ("exactly, never at-least",),
        "Write exactly {n} sentences.",
        "Your entire answer must consist of exactly {n} sentences, no more and no fewer.",
        "Use precisely {n} sentences in total.",
        "The answer must contain {n} sentences exactly.",
        "Produce a response of exactly {n} sentences.",
        "Let the total number of sentences be exactly {n}."),

    "increasing_lengths": _f(
        "increasing_lengths", ("strict inequality, measured in words",),
        "Make each sentence strictly longer than the preceding sentence when "
        "measured by word count.",
        "Arrange the sentences so their word counts increase strictly from one "
        "sentence to the next.",
        "Every sentence after the first must contain more words than the "
        "sentence before it.",
        "Order the sentences so that word count rises strictly with each "
        "successive sentence.",
        "Each successive sentence must exceed the previous one in number of words.",
        "From first to last, sentence word counts must form a strictly "
        "increasing sequence."),

    "nondecreasing_lengths": _f(
        "nondecreasing_lengths", ("non-strict inequality, measured in words",),
        "Make each sentence at least as long as the preceding sentence when "
        "measured by word count.",
        "No sentence may contain fewer words than the sentence before it.",
        "Every sentence after the first must contain at least as many words as "
        "the one before it.",
        "Order the sentences so that word count never decreases from one "
        "sentence to the next.",
        "Sentence word counts must be non-decreasing from first to last.",
        "A sentence may match or exceed the previous sentence in word count, "
        "but never fall below it."),

    "sentence_initial_letter": _f(
        "sentence_initial_letter", ("first letter of the first word only",),
        "Begin every sentence with a word whose first letter is {letter_upper}.",
        "The first word of each sentence must start with the letter {letter_upper}.",
        "Every sentence must open with a word beginning with {letter_upper}.",
        "Start each sentence with a word whose initial letter is {letter_upper}.",
        "The opening word of every sentence must have {letter_upper} as its first letter.",
        "Each sentence's first word must begin with the letter {letter_upper}."),

    "min_words_per_sentence": _f(
        "min_words_per_sentence", ("minimum, per sentence, no maximum implied",),
        "Use at least {n} words in every sentence.",
        "Each sentence must contain no fewer than {n} words.",
        "Every sentence must have {n} words or more.",
        "No sentence may contain fewer than {n} words.",
        "Give each sentence a minimum of {n} words.",
        "Each sentence's word count must be at least {n}."),

    "alphabetical_starts": _f(
        "alphabetical_starts", ("non-strict ordering of first words",),
        "Order the sentences alphabetically by the first word of each sentence.",
        "The first words of successive sentences must appear in alphabetical order.",
        "Arrange the sentences so that their opening words run in alphabetical order.",
        "Each sentence's first word must come at or after the previous "
        "sentence's first word alphabetically.",
        "Sort the sentences by their opening words, alphabetically ascending.",
        "Reading the first word of each sentence in turn must give an "
        "alphabetically ordered list."),

    "long_word_per_sentence": _f(
        "long_word_per_sentence", ("at least one, per sentence, length in letters",),
        "Include at least one word of {letters} or more letters in every sentence.",
        "Every sentence must contain a word at least {letters} letters long.",
        "Each sentence must include a word of no fewer than {letters} letters.",
        "No sentence may lack a word of {letters} letters or longer.",
        "Give every sentence at least one word whose length is {letters} letters or more.",
        "Each sentence must hold a word spanning at least {letters} letters."),

    "sentence_ends_long": _f(
        "sentence_ends_long", ("final word only, length in letters",),
        "End every sentence with a word of {letters} or more letters.",
        "The final word of each sentence must be at least {letters} letters long.",
        "Every sentence must close on a word of no fewer than {letters} letters.",
        "The last word in each sentence must have {letters} letters or more.",
        "Finish each sentence with a word whose length is at least {letters} letters.",
        "No sentence may end on a word shorter than {letters} letters."),

    "commas_per_sentence": _f(
        "commas_per_sentence", ("exactly, per sentence",),
        "Use exactly {n} {noun_comma} in every sentence.",
        "Each sentence must contain precisely {n} {noun_comma}.",
        "Every sentence must have exactly {n} {noun_comma}, no more and no fewer.",
        "The comma count in each sentence must be exactly {n}.",
        "Include {n} {noun_comma} in each sentence, exactly.",
        "No sentence may contain more or fewer than {n} {noun_comma}."),

    "n_long_words_per_sentence": _f(
        "n_long_words_per_sentence", ("minimum count, per sentence, length in letters",),
        "Include at least {n} {noun_word} of {letters} or more letters in every sentence.",
        "Every sentence must contain at least {n} {noun_word} that are {letters} "
        "letters long or longer.",
        "Each sentence must include no fewer than {n} {noun_word} of at least "
        "{letters} letters.",
        "In every sentence, at least {n} {noun_word} must be {letters} letters or longer.",
        "Give each sentence a minimum of {n} {noun_word} with {letters} letters or more.",
        "No sentence may contain fewer than {n} {noun_word} of {letters} letters or more."),

    "word_band_per_sentence": _f(
        "word_band_per_sentence", ("inclusive band, per sentence",),
        "Use between {low} and {high} words in every sentence.",
        "Each sentence must contain no fewer than {low} and no more than {high} words.",
        "Every sentence must have at least {low} words and at most {high} words.",
        "Keep each sentence's word count within the range {low} to {high}, inclusive.",
        "No sentence may fall below {low} words or rise above {high} words.",
        "Each sentence's length in words must lie between {low} and {high} inclusive."),

    "semicolon_per_sentence": _f(
        "semicolon_per_sentence", ("at least one, per sentence",),
        "Use at least one semicolon in every sentence.",
        "Each sentence must contain a semicolon.",
        "Every sentence must include at least one semicolon.",
        "No sentence may be written without a semicolon.",
        "Place a semicolon in each sentence.",
        "Each sentence must carry one or more semicolons."),

    "comma_and_min_words": _f(
        "comma_and_min_words", ("conjunction of two requirements, per sentence",),
        "Give every sentence at least one comma and at least {n} words.",
        "Each sentence must contain a comma and no fewer than {n} words.",
        "Every sentence must include at least one comma and have {n} words or more.",
        "No sentence may lack a comma, and none may fall below {n} words.",
        "Each sentence needs a minimum of one comma and a minimum of {n} words.",
        "Every sentence must satisfy both: at least one comma, and at least {n} words."),

    "unique_words": _f(
        "unique_words", ("whole answer, case-insensitive",),
        "Do not repeat any word anywhere in the answer.",
        "Every word in the answer must be unique, ignoring capitalization.",
        "No word may appear more than once in the whole answer, regardless of case.",
        "Use each word at most once across the entire answer, treating upper "
        "and lower case alike.",
        "Across the whole answer, no word may occur twice, case-insensitively.",
        "Each word in the answer must be distinct from every other, ignoring "
        "letter case."),

    "integer_sum": _f(
        "integer_sum", ("exact count AND exact sum, whole answer, no other integers",),
        "Include exactly {count} integers whose sum is {total}. Do not include "
        "any other integers.",
        "Use precisely {count} integer tokens, totalling {total}, with no "
        "additional integers.",
        "The answer must contain exactly {count} integers and no others, and "
        "they must add up to {total}.",
        "Write exactly {count} integers, no more, whose total is {total}.",
        "Include {count} integers exactly, summing to {total}, and no further integers.",
        "Exactly {count} integers may appear in the answer, and their sum must "
        "equal {total}."),

    "distinct_integers": _f(
        "distinct_integers", ("exact count AND all different, whole answer",),
        "Include exactly {count} distinct integers and no other integers.",
        "Use precisely {count} different integer tokens; no additional integer "
        "tokens are allowed.",
        "The answer must contain exactly {count} integers, all different from "
        "one another.",
        "Write exactly {count} integers, each different, with no further integers.",
        "Exactly {count} integers may appear in the answer, and no two may be equal.",
        "Include {count} integers exactly, all distinct, and none besides."),

    "forbid_word_set": _f(
        "forbid_word_set", ("every listed word, whole answer, case-insensitive",),
        "Do not use the words {words_or} anywhere in the answer.",
        "None of the words {words_and} may appear in your answer.",
        "The answer must avoid all of these words: {words_list}.",
        "Exclude {words_or} from the answer entirely.",
        "No occurrence of {words_and} is permitted anywhere in the answer.",
        "Write the answer without ever using {words_or}."),

    "require_word_set": _f(
        "require_word_set", ("every listed word at least once, whole answer",),
        "Use the words {words_and} at least once each.",
        "Your answer must contain all of these words: {words_list}.",
        "Each of {words_and} must appear somewhere in the answer.",
        "Include every one of these words at least once: {words_list}.",
        "All of {words_and} must occur in the answer at least once.",
        "The answer must use each of the following at least once: {words_list}."),

    "require_word": _f(
        "require_word", ("at least one occurrence, whole answer",),
        'Use the word "{word}" at least once.',
        'Your answer must contain the word "{word}".',
        'The word "{word}" must appear somewhere in the answer.',
        'Include "{word}" at least once in the answer.',
        'Make sure "{word}" occurs somewhere in the answer.',
        'At least one occurrence of "{word}" is required.'),

    "no_suffix": _f(
        "no_suffix", ("orthographic ending, NOT a part-of-speech class",),
        'Do not use any word ending in the letters "{suffix}".',
        'No word in the answer may end with the letters "{suffix}".',
        'Avoid every word whose final letters are "{suffix}".',
        'The answer must contain no word terminating in "{suffix}".',
        'Exclude all words that finish with the letter sequence "{suffix}".',
        'Write the answer without any word that ends "{suffix}".'),

    "alliteration": _f(
        "alliteration", ("minimum count, whole answer, first letter of a word",),
        "Use at least {n} {noun_word} beginning with the letter {letter_upper}.",
        "At least {n} {noun_word} in the answer must start with {letter_upper}.",
        "The answer must include no fewer than {n} {noun_word} whose first "
        "letter is {letter_upper}.",
        "Include {n} or more {noun_word} that begin with {letter_upper}.",
        "A minimum of {n} {noun_word} must have {letter_upper} as their initial letter.",
        "Across the whole answer, {n} {noun_word} or more must start with {letter_upper}."),

    "caps_word": _f(
        "caps_word", ("exact count, whole answer, fully capitalised, minimum length",),
        "Include exactly {n} {noun_word} written entirely in capital letters, "
        "each of at least {letters} letters.",
        "Exactly {n} {noun_word} in the answer must be in all capitals and at "
        "least {letters} letters long.",
        "The answer must contain precisely {n} fully capitalised {noun_word} of "
        "{letters} letters or more.",
        "Use {n} {noun_word} in upper case throughout, each at least {letters} "
        "letters, and no others.",
        "Exactly {n} {noun_word} may appear in all capitals, and each must span "
        "at least {letters} letters.",
        "There must be {n} all-capitals {noun_word} of {letters} letters or "
        "more, no more and no fewer."),

    "exact_char_total": _f(
        "exact_char_total", ("exact count over the WHOLE answer, not per sentence",),
        "Use exactly {n} {noun_char} in the whole answer.",
        "The answer must contain precisely {n} {noun_char} in total.",
        "Across the entire answer, the number of {char_plural} must be exactly {n}.",
        "Include {n} {noun_char} overall, no more and no fewer.",
        "The total count of {char_plural} in the answer must equal {n}.",
        "Exactly {n} {noun_char} may appear anywhere in the answer."),

    "no_char": _f(
        "no_char", ("total absence over the WHOLE answer",),
        "Do not use any {char_plural} anywhere in the answer.",
        "The answer must contain no {char_plural} at all.",
        "Avoid {char_plural} entirely.",
        "No {char_singular} may appear anywhere in the answer.",
        "Write the answer without using a single {char_singular}.",
        "The count of {char_plural} in the answer must be zero."),

    "paren_pairs": _f(
        "paren_pairs", ("exact count of MATCHED pairs, whole answer, round brackets",),
        "Use exactly {n} {noun_pair} of round brackets in the whole answer.",
        "The answer must contain precisely {n} bracketed {noun_aside}, using "
        "round brackets.",
        "Across the entire answer, exactly {n} {noun_pair} of parentheses must "
        "appear, each opened and closed.",
        "Include {n} parenthetical {noun_aside} in round brackets, no more and no fewer.",
        "Exactly {n} {noun_pair} of round brackets may appear anywhere in the "
        "answer, each properly closed.",
        "The total number of matched round-bracket {noun_pair} in the answer "
        "must be {n}."),

    "quote_pairs": _f(
        "quote_pairs", ("exact count of MATCHED pairs, whole answer, double quotes",),
        "Use exactly {n} {noun_pair} of double quotation marks in the whole answer.",
        "The answer must contain precisely {n} quoted {noun_phrase}, marked "
        "with double quotation marks.",
        "Across the entire answer, exactly {n} {noun_pair} of double quotation "
        "marks must appear, each opened and closed.",
        "Include {n} double-quoted {noun_phrase} overall, no more and no fewer.",
        "Exactly {n} matched {noun_pair} of double quotation marks may appear "
        "anywhere in the answer.",
        "The total number of closed double-quotation {noun_pair} must be {n}."),

    "exact_integer_count": _f(
        "exact_integer_count", ("exact count over the WHOLE answer, duplicates allowed",),
        "Include exactly {n} {noun_integer} in the whole answer.",
        "The answer must contain precisely {n} {noun_integer} in total.",
        "Across the entire answer, exactly {n} {noun_integer} must appear.",
        "Use {n} {noun_integer} overall, no more and no fewer.",
        "The total count of integers in the answer must equal {n}.",
        "Exactly {n} {noun_integer} may appear anywhere in the answer."),

    "min_integer_count": _f(
        "min_integer_count", ("minimum over the WHOLE answer, no maximum implied",),
        "Include at least {n} {noun_integer} in the whole answer.",
        "The answer must contain no fewer than {n} {noun_integer} in total.",
        "Across the entire answer, {n} or more {noun_integer} must appear.",
        "Use {n} {noun_integer} or more overall.",
        "The total count of integers in the answer must be at least {n}.",
        "No fewer than {n} {noun_integer} may appear anywhere in the answer."),

    "max_integer_count": _f(
        "max_integer_count", ("maximum over the WHOLE answer, zero is allowed",),
        "Include at most {n} {noun_integer} in the whole answer.",
        "The answer must contain no more than {n} {noun_integer} in total.",
        "Across the entire answer, at most {n} {noun_integer} may appear.",
        "Use {n} {noun_integer} or fewer overall.",
        "The total count of integers in the answer must be at most {n}.",
        "No more than {n} {noun_integer} may appear anywhere in the answer."),

    # ------------------------------------------------- bridge family (v14)
    "vowel_words_per_sentence": _f(
        "vowel_words_per_sentence", ("minimum count, per sentence, first letter",),
        "Include at least {n} words beginning with a vowel in every sentence.",
        "Each sentence must contain no fewer than {n} words that start with a vowel.",
        "Every sentence must have {n} or more words whose first letter is a vowel.",
        "No sentence may contain fewer than {n} vowel-initial words.",
        "Give each sentence a minimum of {n} words starting with a vowel.",
        "In every sentence, at least {n} words must begin with a vowel."),

    "caps_sentence_count": _f(
        "caps_sentence_count",
        ("exact count of SENTENCES carrying a property, not of sentences",),
        "Exactly {n} {noun_sentence} must contain a word written entirely in "
        "capital letters of at least {letters} letters.",
        "Precisely {n} of the sentences must include a fully capitalised word "
        "of {letters} letters or more.",
        "Across the answer, exactly {n} {noun_sentence} may carry an "
        "all-capitals word of at least {letters} letters.",
        "The number of sentences containing a capitalised word of {letters} or "
        "more letters must be exactly {n}.",
        "Only {n} {noun_sentence} may hold a word in capitals of at least "
        "{letters} letters, no more and no fewer.",
        "Exactly {n} {noun_sentence} must feature a word of {letters} letters "
        "or more written in capitals."),

    "sentence_initial_forbidden_word": _f(
        "sentence_initial_forbidden_word", ("first word only, per sentence",),
        'No sentence may begin with the word "{word}".',
        'The first word of a sentence must never be "{word}".',
        'Do not start any sentence with "{word}".',
        'Every sentence must open with a word other than "{word}".',
        'Sentences beginning with "{word}" are not permitted.',
        'The opening word of each sentence must differ from "{word}".'),

    "question_sentence_count": _f(
        "question_sentence_count",
        ("exact count of SENTENCES ending in a question mark",),
        "Exactly {n} {noun_sentence} must end with a question mark.",
        "Precisely {n} of the sentences must be questions ending in a question mark.",
        "Across the answer, exactly {n} {noun_sentence} may finish with a "
        "question mark.",
        "The number of sentences ending in a question mark must be exactly {n}.",
        "Only {n} {noun_sentence} may close with a question mark, no more and "
        "no fewer.",
        "Exactly {n} {noun_sentence} must terminate in a question mark."),

    "no_digits": _f(
        "no_digits", ("total absence of numerals, whole answer",),
        "Do not use any digits.",
        "Your answer must contain no numerals.",
        "No digit may appear anywhere in the answer.",
        "Write the answer without using any numeric characters.",
        "The answer must be free of digits entirely.",
        "Avoid every numeral in the answer."),

    "percent_count": _f(
        "percent_count", ("exact count, whole answer, a number followed by %",),
        "Include exactly {n} percentage {noun_expr} in the whole answer, each "
        "written with a percent sign.",
        "The answer must contain precisely {n} {noun_expr} of the form 'a "
        "number followed by a percent sign'.",
        "Across the entire answer, exactly {n} percentage {noun_expr} must appear.",
        "Use {n} percentage {noun_expr} written with %, overall, no more and no fewer.",
        "Exactly {n} numeric percentage {noun_expr} using the % symbol may appear.",
        "The total number of percentage expressions (a number followed by %) "
        "must be {n}."),
}

# Two further wordings per family, authored separately and reserved for
# wording validation. They are appended at indices 6 and 7 and are never
# reachable by the escalation schedule.
HELD_OUT_TEMPLATES: dict[str, tuple[str, str]] = {
    "exact_sentence_count": (
        "Your answer must run to {n} sentences and stop there.",
        "Neither more nor fewer than {n} sentences are allowed."),
    "increasing_lengths": (
        "Each sentence must be longer, in words, than the one it follows.",
        "Word counts must climb with every sentence, never level and never fall."),
    "nondecreasing_lengths": (
        "Each sentence must be at least as long, in words, as the one it follows.",
        "Word counts may hold steady or climb from sentence to sentence, but "
        "never fall."),
    "sentence_initial_letter": (
        "Every sentence must lead with a word starting {letter_upper}.",
        "No sentence may begin with a word whose first letter is not {letter_upper}."),
    "min_words_per_sentence": (
        "Every sentence must reach {n} words or more.",
        "Sentences shorter than {n} words are not allowed."),
    "alphabetical_starts": (
        "Successive sentences must not go backwards alphabetically on their "
        "first words.",
        "Take the first word of each sentence in order; that sequence must be "
        "alphabetical."),
    "long_word_per_sentence": (
        "Somewhere in every sentence there must be a word of {letters} letters "
        "or more.",
        "Sentences without a word of at least {letters} letters are not allowed."),
    "sentence_ends_long": (
        "Every sentence's closing word must run to {letters} letters or more.",
        "Sentences ending on a word under {letters} letters are not allowed."),
    "commas_per_sentence": (
        "Every sentence must carry {n} {noun_comma} and no others.",
        "Sentences with any number of commas other than {n} are not allowed."),
    "n_long_words_per_sentence": (
        "Every sentence must carry {n} or more {noun_word} of at least "
        "{letters} letters.",
        "Sentences with fewer than {n} {noun_word} of {letters} letters or "
        "more are not allowed."),
    "word_band_per_sentence": (
        "Every sentence must run to at least {low} words and stop by {high}.",
        "Sentences shorter than {low} words or longer than {high} words are "
        "not allowed."),
    "semicolon_per_sentence": (
        "Every sentence must carry a semicolon somewhere in it.",
        "Sentences without a semicolon are not allowed."),
    "comma_and_min_words": (
        "Every sentence must carry a comma and reach {n} words or more.",
        "Sentences without a comma, or shorter than {n} words, are not allowed."),
    "unique_words": (
        "No word may be used twice anywhere in the answer, whatever its "
        "capitalisation.",
        "Repeating any word, in any case, is not allowed."),
    "integer_sum": (
        "The answer must carry {count} integers and nothing further, adding to {total}.",
        "Any number of integers other than {count}, or any total other than "
        "{total}, is not allowed."),
    "distinct_integers": (
        "The answer must carry {count} integers and nothing further, none repeated.",
        "Any number of integers other than {count}, or any repetition among "
        "them, is not allowed."),
    "forbid_word_set": (
        "Every one of {words_and} must be kept out of the answer.",
        "Using {words_or} anywhere in the answer is not allowed."),
    "require_word_set": (
        "Every one of {words_and} must be used somewhere in the answer.",
        "Leaving out any of {words_or} is not allowed."),
    "require_word": (
        'The answer must use "{word}" somewhere.',
        'Leaving "{word}" out of the answer is not allowed.'),
    "no_suffix": (
        'Every word in the answer must end in something other than "{suffix}".',
        'Using any word whose last letters are "{suffix}" is not allowed.'),
    "alliteration": (
        "The answer must carry {n} or more {noun_word} starting with {letter_upper}.",
        "Fewer than {n} {noun_word} beginning with {letter_upper} is not allowed."),
    "caps_word": (
        "The answer must carry {n} all-capitals {noun_word} of at least "
        "{letters} letters, and nothing further in capitals.",
        "Any number of fully capitalised {noun_word} of {letters} letters or "
        "more other than {n} is not allowed."),
    "exact_char_total": (
        "The answer as a whole must carry {n} {noun_char}.",
        "Any number of {char_plural} in the answer other than {n} is not allowed."),
    "no_char": (
        "The answer as a whole must carry no {char_plural}.",
        "Using a {char_singular} anywhere in the answer is not allowed."),
    "paren_pairs": (
        "The answer as a whole must carry {n} matched {noun_pair} of round brackets.",
        "Any number of matched round-bracket {noun_pair} other than {n}, or "
        "any unclosed bracket, is not allowed."),
    "quote_pairs": (
        "The answer as a whole must carry {n} matched {noun_pair} of double "
        "quotation marks.",
        "Any number of matched double-quotation {noun_pair} other than {n}, or "
        "any unclosed mark, is not allowed."),
    "exact_integer_count": (
        "The answer as a whole must carry {n} {noun_integer}.",
        "Any number of integers in the answer other than {n} is not allowed."),
    "min_integer_count": (
        "The answer as a whole must carry {n} {noun_integer} or more.",
        "Fewer than {n} integers in the answer is not allowed."),
    "max_integer_count": (
        "The answer as a whole must carry {n} {noun_integer} at most.",
        "More than {n} integers in the answer is not allowed."),
    "no_digits": (
        "The answer as a whole must carry no digits.",
        "Using a numeral anywhere in the answer is not allowed."),
    "vowel_words_per_sentence": (
        "Every sentence must carry {n} or more words that open with a vowel.",
        "Sentences with fewer than {n} vowel-initial words are not allowed."),
    "caps_sentence_count": (
        "The count of sentences carrying an all-capitals word of {letters} or "
        "more letters must be {n}.",
        "Any number of sentences containing a fully capitalised word of at "
        "least {letters} letters other than {n} is not allowed."),
    "sentence_initial_forbidden_word": (
        'Each sentence must start with something other than "{word}".',
        'Beginning a sentence with "{word}" is not allowed.'),
    "question_sentence_count": (
        "The count of sentences ending in a question mark must be {n}.",
        "Any number of sentences ending with a question mark other than {n} is "
        "not allowed."),
    "percent_count": (
        "The answer as a whole must carry {n} percentage {noun_expr}, each a "
        "number followed by %.",
        "Any number of percentage expressions other than {n} is not allowed."),
}

_no_holdout = sorted(set(S.RULE_FAMILIES) - set(HELD_OUT_TEMPLATES))
assert not _no_holdout, f"families without held-out wordings: {_no_holdout}"
S.RULE_FAMILIES = {
    name: RuleFamily(fam.name, fam.invariants,
                     fam.templates + HELD_OUT_TEMPLATES[name])
    for name, fam in S.RULE_FAMILIES.items()}

_missing_templates = sorted({c.rule_family for c in S.CONSTRAINTS.values()}
                            - set(S.RULE_FAMILIES))
assert not _missing_templates, (
    f"rule families without paraphrase templates: {_missing_templates}")

CHAR_NAMES = {";": ("semicolon", "semicolons"), ":": ("colon", "colons"),
              ",": ("comma", "commas"), ".": ("full stop", "full stops"),
              "%": ("percent sign", "percent signs")}


def _plural(n: int, singular: str, plural_form: Optional[str] = None) -> str:
    return singular if n == 1 else (plural_form or singular + "s")


def _join(words: Iterable[str], conjunction: str) -> str:
    quoted = [f'"{w}"' for w in words]
    if len(quoted) == 1:
        return quoted[0]
    return f"{', '.join(quoted[:-1])} {conjunction} {quoted[-1]}"


def param_view(spec_or_id: Any) -> dict[str, Any]:
    """Expand a constraint's parameters into template placeholders.

    Derived keys (plural agreement, quoted word lists, character names) are
    computed from the parameters rather than written into each template, so a
    threshold cannot drift between wordings: it is substituted, never retyped.
    """
    s = S.CONSTRAINTS[spec_or_id] if isinstance(spec_or_id, str) else spec_or_id
    view: dict[str, Any] = dict(s.param_dict)

    if "n" in view:
        n = int(view["n"])
        view.update(
            noun_comma=_plural(n, "comma"), noun_word=_plural(n, "word"),
            noun_integer=_plural(n, "integer"), noun_pair=_plural(n, "pair"),
            noun_aside=_plural(n, "aside"), noun_phrase=_plural(n, "phrase"),
            noun_expr=_plural(n, "expression"),
            noun_sentence=_plural(n, "sentence"))
    if "count" in view:
        view["noun_count_integer"] = _plural(int(view["count"]), "integer")
    if "letter" in view:
        view.update(letter_upper=str(view["letter"]).upper(),
                    letter_lower=str(view["letter"]).lower())
    if "char" in view:
        singular, plural = CHAR_NAMES[str(view["char"])]
        view.update(char_singular=singular, char_plural=plural,
                    noun_char=_plural(int(view.get("n", 1)), singular, plural))
    if "words" in view:
        words = tuple(view["words"])
        view.update(words_or=_join(words, "or"), words_and=_join(words, "and"),
                    words_list=", ".join(f'"{w}"' for w in words),
                    n_words=len(words))
    return view


def render_instruction(constraint_id: str, paraphrase_id: int) -> str:
    s = S.CONSTRAINTS[constraint_id]
    family = S.RULE_FAMILIES[s.rule_family]
    return family.templates[paraphrase_id].format(**param_view(s))


N_PARAPHRASES_AUTHORED = 8
assert all(len(f.templates) == N_PARAPHRASES_AUTHORED for f in S.RULE_FAMILIES.values())
S.PARAPHRASE_POOL = tuple(i for i in range(N_PARAPHRASES_AUTHORED)
                        if i not in S.CFG.paraphrase_holdout)
assert len(S.PARAPHRASE_POOL) >= max(S.CFG.paraphrase_schedule), (
    f"the escalation schedule reaches P={max(S.CFG.paraphrase_schedule)} but only "
    f"{len(S.PARAPHRASE_POOL)} non-held-out wordings are authored. Author more "
    "templates per family before raising the schedule; do not reuse the "
    "held-out wordings.")
assert set(S.CFG.paraphrase_holdout).isdisjoint(S.PARAPHRASE_POOL), (
    "the held-out wordings must not be reachable by the escalation schedule")

# Render every wording for every constraint once, so a broken placeholder is a
# load-time error rather than a mid-run one.
S.INSTRUCTIONS: dict[str, tuple[str, ...]] = {
    cid: tuple(render_instruction(cid, p) for p in range(N_PARAPHRASES_AUTHORED))
    for cid in S.CONSTRAINTS
}
# v15.1: instruction FORM statistics, reachable downstream.
#
# Pre-repair this was a bare module local computed from wording 0 only, never
# assigned to shared state, so nothing downstream could read it -- it was not
# merely unmatched, it was unreachable. It is now per-wording and on S.
#
# It is REPORTED, never matched. Whether instruction length is part of the
# treatment or a nuisance depends on an UNRESOLVED scientific question recorded
# in S.OPEN_ESTIMAND_QUESTIONS: is DCI the effect of the actual issued
# instruction, including its linguistic form, or of the underlying semantic rule
# independently of phrasing? Under the first reading, matching length away would
# remove part of the treatment. Under the second, an imbalance is a confound.
# The question is not decided in code, and adding length to the reference
# signature would decide it silently.
S.INSTRUCTION_FORM = pd.DataFrame([
    {"constraint_id": cid, "paraphrase_id": p,
     "instruction_tokens": len(word_tokens(text)),
     "instruction_chars": len(text)}
    for cid, wordings in S.INSTRUCTIONS.items()
    for p, text in enumerate(wordings)])
S.INSTRUCTION_TOKENS = (S.INSTRUCTION_FORM.query("paraphrase_id == 0")
                        .set_index("constraint_id")["instruction_tokens"]
                        .rename("instruction_tokens"))
INSTRUCTION_TOKENS = S.INSTRUCTION_TOKENS       # kept: pre-repair local name


def instruction_form_balance(focal: str, references: Iterable[str],
                            paraphrase_ids: Iterable[int]) -> pd.DataFrame:
    """Focal-versus-reference instruction length, averaged over the wordings used.

    A balance artefact, not an adjustment. It exists so that a reader can see the
    imbalance the primary estimand carries rather than having to derive it.
    """
    used = S.INSTRUCTION_FORM[S.INSTRUCTION_FORM["paraphrase_id"].isin(list(paraphrase_ids))]
    per = used.groupby("constraint_id")[["instruction_tokens", "instruction_chars"]].mean()
    if focal not in per.index:
        return pd.DataFrame()
    rows = []
    for ref in references:
        if ref not in per.index:
            continue
        rows.append({
            "reference": ref,
            "focal_tokens": float(per.at[focal, "instruction_tokens"]),
            "reference_tokens": float(per.at[ref, "instruction_tokens"]),
            "token_gap": float(per.at[focal, "instruction_tokens"]
                               - per.at[ref, "instruction_tokens"]),
            "focal_chars": float(per.at[focal, "instruction_chars"]),
            "reference_chars": float(per.at[ref, "instruction_chars"]),
            "char_gap": float(per.at[focal, "instruction_chars"]
                              - per.at[ref, "instruction_chars"]),
        })
    return pd.DataFrame(rows)
S.instruction_form_balance = instruction_form_balance

# The scientific question this reporting deliberately does NOT answer.
S.OPEN_ESTIMAND_QUESTIONS = {
    "instruction_level_vs_semantic_rule": (
        "Is DCI intended to describe the effect of the ACTUAL ISSUED INSTRUCTION, "
        "including its linguistic form, or of the UNDERLYING SEMANTIC CONSTRAINT "
        "independently of how it is phrased? Under the instruction-level reading "
        "the wording is part of the treatment and its length must NOT be matched "
        "away. Under the semantic-rule reading an instruction-length imbalance "
        "between B and the panel is an alternative explanation and needs balanced "
        "paraphrases, a length-matched negative control, or independent "
        "manipulation of form. v15.1 reports the imbalance and leaves the "
        "estimand undecided; the primary wordings are unchanged."),
}


# ==================================================== the audit artefacts
# Two paths, never one. The template is generated only when it is absent, so
# rerunning this cell can never blank a completed audit. The signed artifact is
# an explicit input that this notebook only ever reads.
S.PARAPHRASE_TEMPLATE_PATH = S.AUDIT_DIR / "paraphrase_audit_template.csv"
S.PARAPHRASE_SIGNED_PATH = S.AUDIT_DIR / "paraphrase_audit_signed.csv"

# Point this at a completed audit to sign off. Leave as None until one exists.
PARAPHRASE_AUDIT_SIGNED_INPUT: Optional[str] = None

_audit_rows = []
for cid, s in S.CONSTRAINTS.items():
    fam = S.RULE_FAMILIES[s.rule_family]
    for p in range(N_PARAPHRASES_AUTHORED):
        _audit_rows.append({
            "constraint_id": cid,
            "rule_family": fam.name,
            "paraphrase_id": p,
            "role": "held_out" if p in S.CFG.paraphrase_holdout else "escalation_pool",
            "wording": S.INSTRUCTIONS[cid][p],
            "invariants": " | ".join(fam.invariants),
            "semantically_equivalent": "",   # reviewer writes yes / no
            "reviewer_note": "",
        })
S.PARAPHRASE_AUDIT_TEMPLATE = pd.DataFrame(_audit_rows)
REQUIRED_AUDIT_KEYS = set(
    zip(S.PARAPHRASE_AUDIT_TEMPLATE["constraint_id"],
        S.PARAPHRASE_AUDIT_TEMPLATE["paraphrase_id"]))

def write_template_if_absent(path: Path, frame: pd.DataFrame) -> str:
    """Generate a template only when none exists.

    A cell that unconditionally writes a blank template to a fixed path can
    destroy a completed human audit on any rerun. This is the guard, and Gate 0
    tests it directly.
    """
    if Path(path).exists():
        return "present"
    frame.to_csv(path, index=False)
    return "written"
S.write_template_if_absent = write_template_if_absent


_template_state = S.write_template_if_absent(S.PARAPHRASE_TEMPLATE_PATH,
                                           S.PARAPHRASE_AUDIT_TEMPLATE)
print(f"audit template {_template_state}: {S.PARAPHRASE_TEMPLATE_PATH}")

if S.CFG.integration_autosign_audits and not S.PARAPHRASE_SIGNED_PATH.exists():
    # integration_pass only. The wordings in this profile are generated from one
    # template with declared substitutions, so their semantic equivalence is a
    # property of the fixture rather than a human judgement. Signing it here
    # lets the self-test REACH Gate M; every other gate still has to pass on its
    # own terms, and the artifact is stamped so it can never be mistaken for a
    # human audit.
    _auto = S.PARAPHRASE_AUDIT_TEMPLATE.copy()
    _auto["semantically_equivalent"] = "yes"
    _auto["reviewer"] = "SYNTHETIC_INTEGRATION_SELF_TEST"
    _auto["notes"] = "auto-adjudicated by the integration_pass profile; not evidence"
    _auto.to_csv(S.PARAPHRASE_SIGNED_PATH, index=False)
    print("integration_pass: paraphrase audit auto-adjudicated (SYNTHETIC).")

if S.PARAPHRASE_SIGNED_PATH.exists() and PARAPHRASE_AUDIT_SIGNED_INPUT is None:
    PARAPHRASE_AUDIT_SIGNED_INPUT = str(S.PARAPHRASE_SIGNED_PATH)


def evaluate_paraphrase_audit(path: Optional[str]) -> dict[str, Any]:
    """Read a signed audit and decide whether every used wording is approved.

    Never writes to `path`. Missing rows and unapproved rows are reported
    separately, because they call for different action: one is unfinished work,
    the other is a wording the reviewer rejected and which must be rewritten.
    """
    result: dict[str, Any] = {
        "signed_path": path, "present": False, "sha256": None,
        "n_rows": 0, "missing_rows": [], "unapproved": [], "passed": False,
        "wording_mismatches": []}
    if not path or not Path(path).exists():
        return result
    result["present"] = True
    result["sha256"] = sha_file(Path(path))
    signed = pd.read_csv(path)
    needed = {"constraint_id", "paraphrase_id", "semantically_equivalent"}
    if not needed <= set(signed.columns):
        result["missing_rows"] = ["FILE MISSING REQUIRED COLUMNS"]
        return result
    signed["paraphrase_id"] = signed["paraphrase_id"].astype(int)
    result["n_rows"] = len(signed)
    have = set(zip(signed["constraint_id"], signed["paraphrase_id"]))
    result["missing_rows"] = sorted(f"{c}|p{p}" for c, p in REQUIRED_AUDIT_KEYS - have)

    verdict = (signed["semantically_equivalent"].astype(str).str.strip().str.lower())
    approved = set(zip(signed.loc[verdict.isin({"yes", "y", "true"}), "constraint_id"],
                       signed.loc[verdict.isin({"yes", "y", "true"}), "paraphrase_id"]))
    result["unapproved"] = sorted(f"{c}|p{p}" for c, p in REQUIRED_AUDIT_KEYS - approved)

    # The signed file must describe the wordings this notebook actually renders.
    if "wording" in signed.columns:
        rendered = {(c, p): S.INSTRUCTIONS[c][p] for c, p in REQUIRED_AUDIT_KEYS}
        for _, row in signed.iterrows():
            key = (row["constraint_id"], int(row["paraphrase_id"]))
            if key in rendered and str(row["wording"]).strip() != rendered[key].strip():
                result["wording_mismatches"].append(f"{key[0]}|p{key[1]}")
    result["passed"] = bool(not result["missing_rows"] and not result["unapproved"]
                            and not result["wording_mismatches"])
    return result
S.evaluate_paraphrase_audit = evaluate_paraphrase_audit


S.PARAPHRASE_AUDIT = S.evaluate_paraphrase_audit(PARAPHRASE_AUDIT_SIGNED_INPUT)
S.PARAPHRASE_AUDIT_PASSED = bool(S.PARAPHRASE_AUDIT["passed"])
S.PARAPHRASE_AUDIT_SHA256 = S.PARAPHRASE_AUDIT["sha256"]

print(f"\n{len(S.RULE_FAMILIES)} rule families x {N_PARAPHRASES_AUTHORED} wordings "
      f"= {len(S.PARAPHRASE_AUDIT_TEMPLATE)} constraint-wording rows")
print(f"escalation pool paraphrase ids : {S.PARAPHRASE_POOL}")
print(f"permanently held out           : {tuple(S.CFG.paraphrase_holdout)}")
print(f"signed audit                   : "
      f"{'PRESENT' if S.PARAPHRASE_AUDIT['present'] else 'ABSENT'}"
      f"  -> {'APPROVED' if S.PARAPHRASE_AUDIT_PASSED else 'NOT APPROVED'}")
if S.PARAPHRASE_AUDIT["present"] and not S.PARAPHRASE_AUDIT_PASSED:
    print(f"  missing rows       : {len(S.PARAPHRASE_AUDIT['missing_rows'])}"
          f"  e.g. {S.PARAPHRASE_AUDIT['missing_rows'][:5]}")
    print(f"  unapproved wordings: {len(S.PARAPHRASE_AUDIT['unapproved'])}"
          f"  e.g. {S.PARAPHRASE_AUDIT['unapproved'][:5]}")
    print(f"  wording mismatches : {len(S.PARAPHRASE_AUDIT['wording_mismatches'])}")
if not S.PARAPHRASE_AUDIT_PASSED:
    print(f"""
The semantic audit is a GATE, not an export label. Complete
  {S.PARAPHRASE_TEMPLATE_PATH}
WITHOUT looking at any model performance, save it as
  {S.PARAPHRASE_SIGNED_PATH}
and rerun. Gate M refuses to pass until every wording this notebook renders has
been approved, and no empirical generation is permitted before Gate M passes.
""")
