@dataclass(frozen=True)
class ConstraintSpec:
    constraint_id: str
    source_id: str
    name: str
    category: str
    mechanism: str
    generative_scope: Literal["sentence", "whole_text"]
    verifier_span: str
    role: Literal["target", "focal", "candidate", "unrelated", "neutral"]
    rule_family: str
    params: tuple[tuple[str, Any], ...] = ()
    origin: Literal["cse_pool", "shadow", "unrelated", "neutral"] = "cse_pool"
    pathway_removed: str = ""
    u_family: str = ""
    pathway_audit: str = ""
    # Declared logical relations, evaluated by hard eligibility without
    # inspecting any behaviour.
    incompatible_with: tuple[str, ...] = ()
    entails: tuple[str, ...] = ()
    # Bridge targets only: a sentence whose addition must not change the
    # verdict, which is what proves the rule does not read the sentence count.
    count_probe_sentence: str = ""

    @property
    def param_dict(self) -> dict[str, Any]:
        return dict(self.params)


def spec(*args, **kwargs) -> ConstraintSpec:
    return ConstraintSpec(*args, **kwargs)


def P(**kwargs) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted(kwargs.items()))


NEUTRAL_A = "Rivers keep their level through the night."
NEUTRAL_VOWEL = "An open estimate of every autumn is around us anyway."

CONSTRAINTS: dict[str, ConstraintSpec] = {
    # ------------------------------------------------------------- target
    "A": spec("A", "S2", "Exact sentence count", "structural", "global_count",
              "sentence", "sentence_segmentation", "target",
              "exact_sentence_count", P(n=CFG.exact_sentence_count)),

    # -------------------------------------------------------------- focal
    "B": spec("B", "O1", "Increasing sentence lengths", "ordering",
              "cross_sentence_comparison", "sentence",
              "sentence_segmentation+word_counts", "focal",
              "increasing_lengths"),
    "B_SOFT": spec("B_SOFT", "O1-soft", "Non-decreasing sentence lengths",
                   "ordering", "cross_sentence_comparison", "sentence",
                   "sentence_segmentation+word_counts", "focal",
                   "nondecreasing_lengths", entails=("B",)),

    # ------------------------------------------- sentence-scoped candidates
    "C_L3": spec("C_L3", "L3", "Sentence-initial letter S", "lexical",
                 "local_check", "sentence", "sentence_segmentation+initials",
                 "candidate", "sentence_initial_letter", P(letter="S")),
    "C_W3": spec("C_W3", "W3", "Minimum words per sentence", "word_level",
                 "sustained_maintenance", "sentence",
                 "sentence_segmentation+word_counts", "candidate",
                 "min_words_per_sentence", P(n=CFG.minimum_sentence_words)),
    "C_O2": spec("C_O2", "O2", "Alphabetical sentence starts", "ordering",
                 "cross_sentence_comparison", "sentence",
                 "sentence_segmentation+first_words", "candidate",
                 "alphabetical_starts"),
    "S_LONGWORD": spec("S_LONGWORD", "shadow", "One long word per sentence",
                       "lexical", "local_check", "sentence",
                       "sentence_segmentation+word_lengths", "candidate",
                       "long_word_per_sentence", P(letters=CFG.long_word_letters),
                       "shadow", "cross-sentence length comparison"),
    "S_ENDLONG": spec("S_ENDLONG", "shadow", "Sentence ends on a long word",
                      "lexical", "local_check", "sentence",
                      "sentence_segmentation+final_word", "candidate",
                      "sentence_ends_long", P(letters=CFG.long_word_letters),
                      "shadow", "cross-sentence length comparison"),
    "S_COMMA": spec("S_COMMA", "shadow", "Exactly one comma per sentence",
                    "format", "local_check", "sentence",
                    "sentence_segmentation+punctuation", "candidate",
                    "commas_per_sentence", P(n=1),
                    "shadow", "cross-sentence length comparison"),
    "S_MINWORDS12": spec("S_MINWORDS12", "shadow", "At least 12 words per sentence",
                         "word_level", "sustained_maintenance", "sentence",
                         "sentence_segmentation+word_counts", "candidate",
                         "min_words_per_sentence", P(n=CFG.shadow_min_words_a),
                         "shadow", "cross-sentence length comparison"),
    "S_MINWORDS15": spec("S_MINWORDS15", "shadow", "At least 15 words per sentence",
                         "word_level", "sustained_maintenance", "sentence",
                         "sentence_segmentation+word_counts", "candidate",
                         "min_words_per_sentence", P(n=CFG.shadow_min_words_b),
                         "shadow", "cross-sentence length comparison"),
    "S_MINWORDS20": spec("S_MINWORDS20", "shadow", "At least 20 words per sentence",
                         "word_level", "sustained_maintenance", "sentence",
                         "sentence_segmentation+word_counts", "candidate",
                         "min_words_per_sentence", P(n=CFG.shadow_min_words_c),
                         "shadow", "cross-sentence length comparison"),
    "S_MINWORDS25": spec("S_MINWORDS25", "shadow", "At least 25 words per sentence",
                         "word_level", "sustained_maintenance", "sentence",
                         "sentence_segmentation+word_counts", "candidate",
                         "min_words_per_sentence", P(n=CFG.shadow_min_words_d),
                         "shadow", "cross-sentence length comparison"),
    "S_MINWORDS30": spec("S_MINWORDS30", "shadow", "At least 30 words per sentence",
                         "word_level", "sustained_maintenance", "sentence",
                         "sentence_segmentation+word_counts", "candidate",
                         "min_words_per_sentence", P(n=CFG.shadow_min_words_e),
                         "shadow", "cross-sentence length comparison"),
    "S_TWOLONG": spec("S_TWOLONG", "shadow", "Two long words per sentence",
                      "lexical", "local_check", "sentence",
                      "sentence_segmentation+word_lengths", "candidate",
                      "n_long_words_per_sentence",
                      P(letters=CFG.long_word_letters, n=CFG.shadow_long_word_count),
                      "shadow", "cross-sentence length comparison"),
    "S_THREELONG": spec("S_THREELONG", "shadow", "Three long words per sentence",
                        "lexical", "local_check", "sentence",
                        "sentence_segmentation+word_lengths", "candidate",
                        "n_long_words_per_sentence",
                        P(letters=CFG.long_word_letters,
                          n=CFG.shadow_long_word_count_high),
                        "shadow", "cross-sentence length comparison"),
    "S_BAND1525": spec("S_BAND1525", "shadow", "Sentence length inside a band",
                       "word_level", "sustained_maintenance", "sentence",
                       "sentence_segmentation+word_counts", "candidate",
                       "word_band_per_sentence",
                       P(low=CFG.band_low, high=CFG.band_high),
                       "shadow", "cross-sentence length comparison"),
    "S_TWOCOMMA": spec("S_TWOCOMMA", "shadow", "Exactly two commas per sentence",
                       "format", "local_check", "sentence",
                       "sentence_segmentation+punctuation", "candidate",
                       "commas_per_sentence", P(n=CFG.two_commas),
                       "shadow", "cross-sentence length comparison"),
    "S_SEMICOLON": spec("S_SEMICOLON", "shadow", "A semicolon in every sentence",
                        "format", "local_check", "sentence",
                        "sentence_segmentation+punctuation", "candidate",
                        "semicolon_per_sentence", (),
                        "shadow", "cross-sentence length comparison"),
    "S_COMMA12": spec("S_COMMA12", "shadow", "A comma and twelve words per sentence",
                      "word_level", "sustained_maintenance", "sentence",
                      "sentence_segmentation+word_counts+punctuation", "candidate",
                      "comma_and_min_words", P(n=CFG.comma_min_words),
                      "shadow", "cross-sentence length comparison"),

    # ------------------------------------------ whole-text candidates
    "C_W1": spec("C_W1", "W1", "All words unique", "word_level",
                 "sustained_maintenance", "whole_text", "token_stream",
                 "candidate", "unique_words"),
    "C_N1": spec("C_N1", "N1", "Integers summing to a total", "numerical",
                 "global_count", "whole_text", "token_stream", "candidate",
                 "integer_sum", P(count=3, total=60)),
    "C_N3": spec("C_N3", "N3", "Exact distinct integer count", "numerical",
                 "global_count", "whole_text", "token_stream", "candidate",
                 "distinct_integers", P(count=3)),

    # =============================== unrelated targets: whole-answer families
    "U_LEX_FORBID3": spec(
        "U_LEX_FORBID3", "u-lex-1", "Three forbidden words", "lexical",
        "local_check", "whole_text", "token_stream", "unrelated",
        "forbid_word_set", P(words=CFG.u_forbidden_words), "unrelated",
        u_family="lexical",
        pathway_audit="Token membership over the whole answer. Never segments."),
    "U_LEX_REQUIRE3": spec(
        "U_LEX_REQUIRE3", "u-lex-2", "Three mandatory words", "lexical",
        "local_check", "whole_text", "token_stream", "unrelated",
        "require_word_set", P(words=CFG.u_required_words), "unrelated",
        u_family="lexical",
        pathway_audit="Token membership. Adds at most three tokens."),
    "U_LEX_NOLY": spec(
        "U_LEX_NOLY", "u-lex-3", "No word ending in -ly", "lexical",
        "local_check", "whole_text", "token_stream", "unrelated",
        "no_suffix", P(suffix="ly"), "unrelated", u_family="lexical",
        pathway_audit="Orthographic suffix test on individual tokens."),
    "U_LEX_ALLIT_P": spec(
        "U_LEX_ALLIT_P", "u-lex-4", "Four words beginning with P", "lexical",
        "local_check", "whole_text", "token_stream", "unrelated",
        "alliteration",
        P(letter=CFG.u_alliteration_letter, n=CFG.u_alliteration_count),
        "unrelated", u_family="lexical",
        pathway_audit="Counts initial letters over the whole answer."),
    "U_LEX_CAPWORD": spec(
        "U_LEX_CAPWORD", "u-lex-5", "Exactly one all-capitals word", "lexical",
        "local_check", "whole_text", "token_stream", "unrelated",
        "caps_word", P(n=1, letters=3), "unrelated", u_family="lexical",
        pathway_audit="Case test on individual tokens."),

    "U_FMT_SEMI2": spec(
        "U_FMT_SEMI2", "u-fmt-1", "Exactly two semicolons in the answer",
        "format", "global_count", "whole_text", "character_stream", "unrelated",
        "exact_char_total", P(char=";", n=CFG.u_semicolon_total), "unrelated",
        u_family="format",
        pathway_audit="Whole-answer character count, deliberately not "
                      "per-sentence, unlike S_SEMICOLON."),
    "U_FMT_PAREN1": spec(
        "U_FMT_PAREN1", "u-fmt-2", "Exactly one parenthetical", "format",
        "global_count", "whole_text", "character_stream", "unrelated",
        "paren_pairs", P(n=1), "unrelated", u_family="format",
        pathway_audit="Bracket pairing over the whole answer."),
    "U_FMT_COLON1": spec(
        "U_FMT_COLON1", "u-fmt-3", "Exactly one colon", "format",
        "global_count", "whole_text", "character_stream", "unrelated",
        "exact_char_total", P(char=":", n=CFG.u_colon_total), "unrelated",
        u_family="format", pathway_audit="Whole-answer character count."),
    "U_FMT_QUOTE1": spec(
        "U_FMT_QUOTE1", "u-fmt-4", "Exactly one quoted phrase", "format",
        "global_count", "whole_text", "character_stream", "unrelated",
        "quote_pairs", P(n=CFG.u_quote_pairs), "unrelated", u_family="format",
        pathway_audit="Quotation-mark pairing over the whole answer."),
    "U_FMT_NOCOMMA": spec(
        "U_FMT_NOCOMMA", "u-fmt-5", "No commas anywhere", "format",
        "local_check", "whole_text", "character_stream", "unrelated",
        "no_char", P(char=","), "unrelated", u_family="format",
        pathway_audit="Character absence. Watch for a length side-effect: "
                      "comma avoidance can shorten clauses."),

    "U_NUM_TWOINT": spec(
        "U_NUM_TWOINT", "u-num-1", "Exactly two integers", "numerical",
        "global_count", "whole_text", "token_stream", "unrelated",
        "exact_integer_count", P(n=CFG.u_integer_count_small), "unrelated",
        u_family="numerical", pathway_audit="Counts integer tokens."),
    "U_NUM_NODIGIT": spec(
        "U_NUM_NODIGIT", "u-num-2", "No digits", "numerical", "local_check",
        "whole_text", "token_stream", "unrelated", "no_digits", (), "unrelated",
        u_family="numerical",
        pathway_audit="Digit absence. Retained as a deliberate negative "
                      "control on the screen: v12 measured 1 failure in 352."),
    "U_NUM_FOURDISTINCT": spec(
        "U_NUM_FOURDISTINCT", "u-num-3", "Four distinct integers", "numerical",
        "global_count", "whole_text", "token_stream", "unrelated",
        "distinct_integers", P(count=CFG.u_integer_count_large), "unrelated",
        u_family="numerical", pathway_audit="Counts and de-duplicates integers."),
    "U_NUM_SUM100": spec(
        "U_NUM_SUM100", "u-num-4", "Three integers summing to 100", "numerical",
        "global_count", "whole_text", "token_stream", "unrelated",
        "integer_sum",
        P(count=CFG.u_integer_sum_count, total=CFG.u_integer_sum_target),
        "unrelated", u_family="numerical",
        pathway_audit="Arithmetic on integer tokens."),
    "U_NUM_ONEPCT": spec(
        "U_NUM_ONEPCT", "u-num-5", "Exactly one percentage", "numerical",
        "global_count", "whole_text", "token_stream", "unrelated",
        "percent_count", P(n=CFG.u_percent_count), "unrelated",
        u_family="numerical", pathway_audit="Counts percentage expressions."),
    "U_NUM_MININT": spec(
        "U_NUM_MININT", "u-num-6", "At least two integers", "numerical",
        "global_count", "whole_text", "token_stream", "unrelated",
        "min_integer_count", P(n=CFG.u_integer_min), "unrelated",
        u_family="numerical",
        pathway_audit="Bounded below rather than exactly: every exact-count "
                      "numerical candidate is hard, and a family with no "
                      "spread cannot be screened."),
    "U_NUM_MAXINT": spec(
        "U_NUM_MAXINT", "u-num-7", "At most two integers", "numerical",
        "global_count", "whole_text", "token_stream", "unrelated",
        "max_integer_count", P(n=CFG.u_integer_max), "unrelated",
        u_family="numerical", pathway_audit="Bounded above rather than exactly."),

    # ============================== unrelated targets: bridge family (v14)
    # Sentence-scoped, and therefore sharing A's segmentation span. Admissible
    # for validation and test only. Each must survive both behavioural probes:
    # invariance to appending its declared neutral sentence (no dependence on
    # the sentence COUNT, which is A) and invariance to reversing sentence
    # order (no cross-sentence comparison, which is B).
    "U_BRG_VOWEL3": spec(
        "U_BRG_VOWEL3", "u-brg-1", "Three vowel-initial words per sentence",
        "lexical", "local_check", "sentence", "sentence_segmentation+initials",
        "unrelated", "vowel_words_per_sentence", P(n=CFG.u_bridge_vowel_min),
        "unrelated", u_family="bridge", count_probe_sentence=NEUTRAL_VOWEL,
        pathway_audit="Counts vowel-initial words WITHIN each sentence. Does "
                      "not read the number of sentences and never compares one "
                      "sentence with another. Shares A's segmentation span by "
                      "design: that is what makes it a transport probe."),
    "U_BRG_CAPS1": spec(
        "U_BRG_CAPS1", "u-brg-2", "Exactly one sentence carries a capitalised word",
        "lexical", "global_count", "sentence",
        "sentence_segmentation+word_case", "unrelated",
        "caps_sentence_count", P(n=CFG.u_bridge_caps_sentences, letters=3),
        "unrelated", u_family="bridge", count_probe_sentence=NEUTRAL_A,
        pathway_audit="Counts sentences WITH a property, not sentences. Adding "
                      "a sentence without that property leaves it unchanged, "
                      "which the count-invariance probe verifies."),
    "U_BRG_NOTHE": spec(
        "U_BRG_NOTHE", "u-brg-3", "No sentence begins with 'the'", "lexical",
        "local_check", "sentence", "sentence_segmentation+first_words",
        "unrelated", "sentence_initial_forbidden_word", P(word="the"),
        "unrelated", u_family="bridge", count_probe_sentence=NEUTRAL_A,
        pathway_audit="Per-sentence first-word test. No count, no comparison."),
    "U_BRG_QMARK": spec(
        "U_BRG_QMARK", "u-brg-4", "Exactly one sentence ends in a question mark",
        "format", "global_count", "sentence",
        "sentence_segmentation+final_punctuation", "unrelated",
        "question_sentence_count", P(n=1), "unrelated", u_family="bridge",
        count_probe_sentence=NEUTRAL_A,
        pathway_audit="Counts sentences ending in '?', not sentences."),

    # ------------------------------------------------- screening partner
    "N_NEUTRAL": spec(
        "N_NEUTRAL", "neutral", "Mandatory word (screening partner)", "lexical",
        "local_check", "whole_text", "token_stream", "neutral",
        "require_word", P(word=CFG.u_neutral_word), "neutral",
        pathway_audit="'overall' has no -ly suffix, is not in the forbidden "
                      "set, carries no digits and adds no punctuation, so it "
                      "cannot mechanically satisfy or violate any U candidate."),
}

_ALL_CANDIDATES = tuple(k for k, v in CONSTRAINTS.items() if v.role == "candidate")
_FOCAL_SCOPE = CONSTRAINTS[CFG.focal_id].generative_scope
CANDIDATE_IDS = tuple(
    c for c in _ALL_CANDIDATES
    if not CFG.scope_restricted_pool
    or CONSTRAINTS[c].generative_scope == _FOCAL_SCOPE)
U_CANDIDATE_IDS = tuple(k for k, v in CONSTRAINTS.items() if v.role == "unrelated")
BRIDGE_IDS = tuple(u for u in U_CANDIDATE_IDS if CONSTRAINTS[u].u_family == "bridge")

for _uid in U_CANDIDATE_IDS:
    _u = CONSTRAINTS[_uid]
    assert _u.u_family in CFG.u_families, f"{_uid}: unknown family {_u.u_family!r}"
    assert _u.pathway_audit, f"{_uid} has no written pathway audit"
    if _u.u_family == "bridge":
        assert _u.generative_scope == "sentence" and _u.count_probe_sentence, (
            f"{_uid} is a bridge target and must declare a neutral probe sentence")
    else:
        assert _u.generative_scope == "whole_text", (
            f"{_uid} is {_u.generative_scope}-scoped outside the bridge family")

_family_counts = pd.Series(
    [CONSTRAINTS[u].u_family for u in U_CANDIDATE_IDS]).value_counts()
for _fam in CFG.u_build_families:
    assert _family_counts.get(_fam, 0) >= CFG.u_min_eligible_per_family, (
        f"family {_fam} needs at least {CFG.u_min_eligible_per_family} authored "
        f"candidates before screening can admit that many")
assert len(BRIDGE_IDS) >= 2, "at least two bridge candidates are needed (val and test)"

print(f"reference candidate pool : {len(CANDIDATE_IDS)} of {len(_ALL_CANDIDATES)}")
print(f"unrelated-target bank    : {len(U_CANDIDATE_IDS)} candidates")
print(_family_counts.to_string())


# ========================================================== task splits
def make_task(task_id: str, split: str, topic: str) -> dict[str, str]:
    return {"task_id": task_id, "split": split, "topic": topic}


BURNED_TOPICS = [
    "Explain how shade changes the temperature of a city street.",
    "Explain why maintaining a research log is useful.",
    "Describe how a household can reduce food waste.",
    "Explain how a map legend helps a reader.",
    "Describe why backups are useful for research data.",
    "Explain how feedback can improve a draft.",
    "Describe how insulation affects a building.",
    "Explain why naming variables clearly helps programmers.",
    "Explain how urban trees improve city resilience.",
    "Explain why consistent sleep routines can improve daytime functioning.",
    "Describe how electricity grids integrate variable renewable energy.",
    "Explain the value of version control in collaborative research.",
    "Describe how wetlands reduce flood risk.",
    "Explain why calibration matters in probabilistic forecasting.",
    "Describe how public libraries support local communities.",
    "Explain the purpose of randomized controlled experiments.",
    "Describe how composting changes organic waste.",
    "Explain why software tests are useful during refactoring.",
    "Describe how vaccines train immune memory in general terms.",
    "Explain how maps simplify complex spatial information.",
    "Describe how peer review can improve a research manuscript.",
    "Explain how demand response can support an electricity system.",
    "Describe why metadata is important for reusable datasets.",
    "Explain how spaced practice supports durable learning.",
    "Explain how a lighthouse helps ships navigate at night.",
    "Describe why bicycle lanes change how a street is used.",
    "Explain how bread dough rises during proofing.",
    "Describe why museums rotate items in their collections.",
    "Explain how a thermostat keeps a room at one temperature.",
    "Describe why crop rotation helps a farm over many seasons.",
    "Explain how noise-cancelling headphones reduce background sound.",
    "Describe why harbours need regular dredging.",
    "Explain how a compost thermometer guides a gardener.",
    "Describe why bridges include expansion joints.",
    "Explain how tidal patterns affect coastal fishing.",
    "Describe why glass recycling reduces energy use.",
    "Explain how a sundial indicates the time of day.",
    "Describe why forests regrow differently after a fire.",
    "Explain how a canal lock moves a boat between water levels.",
    "Describe why some birds migrate over long distances.",
    "Explain how a water filter removes impurities.",
    "Describe why cities install permeable pavement.",
    "Explain how a kite stays airborne in steady wind.",
    "Describe why lighthouses were automated over time.",
    "Explain how honey resists spoiling for long periods.",
    "Describe why train timetables include recovery time.",
    "Explain how a greenhouse retains warmth for plants.",
    "Describe why coral reefs support many marine species.",
    "Explain how paper is made from wood pulp.",
    "Describe why mountain roads use switchbacks.",
]

SCREENING_TOPICS = [
    "Explain how a pressure cooker shortens cooking time.",
    "Describe why airports use holding patterns.",
    "Explain how a sourdough starter stays alive between bakes.",
    "Describe why some roads are built with a camber.",
    "Explain how a metronome helps a musician practise.",
    "Describe why warehouses use barcode labels.",
    "Explain how a French press separates coffee grounds.",
    "Describe why orchestras tune to a single note.",
    # v15: screening precision is the binding constraint on the U bank, and the
    # remedy the gate itself names is more screening CLUSTERS. Sixteen further
    # topics were authored so that remedy is actually available.
    "Explain how a lock keeper decides when to open a gate.",
    "Describe why libraries shelve books by subject.",
    "Explain how a kiln reaches an even temperature.",
    "Describe why bridges are fitted with expansion joints.",
    "Describe why bakeries proof dough twice.",
    "Explain how a marine chronometer keeps time at sea.",
    "Explain how a sundial's shadow marks the hours.",
    "Describe why ships carry ballast water.",
    "Explain how a thermostat keeps a room steady.",
    "Describe why maps use contour lines.",
    "Explain how a windmill turns grain into flour.",
    "Describe why hospitals colour-code their corridors.",
    "Explain how a beekeeper harvests honey without harming the hive.",
    "Describe why railways use ballast beneath the sleepers.",
    "Explain how a lighthouse produces a distinctive flash pattern.",
    "Describe why museums control humidity in their galleries.",
]

PRESCREEN_TOPICS = [
    "Explain how a zip fastener holds two edges together.",
    "Describe why kitchens separate raw and cooked food.",
    "Explain how a pendulum clock keeps regular time.",
    "Describe why airlines weigh baggage before loading.",
    "Explain how a magnifying glass enlarges an image.",
    "Describe why cyclists wear reflective clothing at dusk.",
]

CALIBRATION_TOPICS = [
    "Explain how a kettle knows when to switch off.",
    "Describe why supermarkets rotate stock on shelves.",
    "Explain how a bicycle chain transfers pedalling force.",
    "Describe why hospitals label medicines carefully.",
    "Explain how a rain gauge measures rainfall.",
    "Describe why theatres darken the auditorium.",
    "Explain how a spirit level shows whether a surface is flat.",
    "Describe why bakeries score the tops of loaves.",
    "Explain how a chimney draws smoke upward.",
    "Describe why swimming pools test water regularly.",
    "Explain how a padlock shackle resists cutting.",
    "Describe why nurseries harden off young plants.",
    "Explain how a wind vane shows the wind direction.",
    "Describe why chefs rest meat after cooking.",
    "Explain how a sluice gate controls a stream.",
    "Describe why divers ascend in stages.",
    # v15: the precision gate's own remedy is more calibration CLUSTERS, and at
    # sixteen it could not be taken. Sixteen further topics were authored so the
    # escalation the notebook prescribes is actually available.
    "Explain how a cable car keeps tension on its haul rope.",
    "Describe why concrete is cured slowly rather than dried.",
    "Explain how a paper mill screens fibre from pulp.",
    "Describe why aircraft wings are given dihedral.",
    "Explain how a water tower maintains mains pressure.",
    "Describe why cheese is aged at controlled humidity.",
    "Explain how a seed drill spaces a crop evenly.",
    "Describe why telescopes are built on high dry sites.",
    "Explain how a heat exchanger transfers energy between fluids.",
    "Describe why timber is seasoned before it is used.",
    "Explain how a fish ladder helps salmon pass a weir.",
    "Describe why tunnels need forced ventilation.",
    "Explain how a wind tunnel measures drag on a model.",
    "Describe why glaciers carve U-shaped valleys.",
    "Explain how a printing press registers colours in sequence.",
    "Describe why coastal dunes are planted with marram grass.",
    "Explain how a canal aqueduct carries water over a road.",
    "Describe why blast furnaces run continuously.",
    "Explain how a rotary kiln makes cement clinker.",
    "Describe why vineyards are planted on slopes.",
    "Explain how a hydraulic ram pump lifts water without power.",
    "Describe why salt is spread on roads before frost.",
    "Explain how a centrifuge separates cream from milk.",
    "Describe why observatories use adaptive optics.",
    "Explain how a chain ferry crosses a tidal river.",
    "Describe why orchards are netted before harvest.",
    "Explain how a reed bed treats waste water.",
    "Describe why steel is galvanised before outdoor use.",
    "Explain how a funicular railway balances two cars.",
    "Describe why bread crusts brown in the oven.",
    "Explain how a tide mill stored energy between tides.",
    "Describe why aircraft de-icing is done at the gate.",
    "Explain how a sand filter clarifies drinking water.",
    "Describe why forests are thinned as they mature.",
    "Explain how a gearbox matches engine speed to load.",
    "Describe why quarries work in benches.",
    "Explain how a solar chimney drives ventilation.",
    "Describe why cargo is lashed to a specific pattern.",
    "Explain how a rain gauge corrects for wind.",
    "Describe why bricks are fired rather than dried.",
    "Explain how a swing bridge carries its own weight when open.",
    "Describe why potatoes are stored in the dark.",
    "Explain how a stethoscope amplifies body sounds.",
    "Describe why runways are grooved.",
    "Explain how a millpond regulates a waterwheel.",
    "Describe why laboratory glassware is annealed.",
    "Explain how a snow fence changes where drifts form.",
    "Describe why cables are laid with slack on the seabed.",
]

# Gate 3b runs here. Disjoint from calibration and from confirmation, so the
# held-out wordings are evaluated on tasks that determined nothing.
WORDING_TOPICS = [
    "Explain how a squeegee clears water from glass.",
    "Describe why bakers weigh ingredients rather than measuring volume.",
    "Explain how a ratchet allows motion in one direction.",
    "Describe why gardeners mulch around young trees.",
    "Explain how a siphon moves liquid over a rim.",
    "Describe why sailors reef a sail in strong wind.",
    "Explain how a thermos lid reduces heat loss.",
    "Describe why bricklayers stagger the joints in a wall.",
]

CONFIRMATORY_TOPICS = [
    "Explain how a lock keeper manages water on a canal.",
    "Describe why cargo ships carry ballast water.",
    "Explain how a solar panel converts light into electricity.",
    "Describe why beekeepers use smoke at a hive.",
    "Explain how a sewing machine forms a stitch.",
    "Describe why some bridges are painted continuously.",
    "Explain how a refrigerator moves heat outward.",
    "Describe why hedgerows support farmland wildlife.",
    "Explain how a barometer signals a change in weather.",
    "Describe why potters fire clay twice.",
    "Explain how a car differential lets wheels turn at different speeds.",
    "Describe why archives control humidity in storage rooms.",
    "Explain how a windmill converts wind into rotation.",
    "Describe why marathon runners take on fluids gradually.",
    "Explain how a telescope gathers faint light.",
    "Describe why builders allow concrete to cure slowly.",
    "Explain how a smoke alarm detects a fire.",
    "Describe why fisheries set minimum landing sizes.",
    "Explain how a bicycle gear changes pedalling effort.",
    "Describe why cities sweep streets before heavy rain.",
    "Explain how a vacuum flask keeps drinks hot.",
    "Describe why vineyards prune vines in winter.",
    "Explain how a compass needle finds north.",
    "Describe why airports de-ice aircraft wings.",
    "Explain how a dam spillway protects the structure.",
    "Describe why museums dim the lights near old textiles.",
    "Explain how a microphone turns sound into a signal.",
    "Describe why farmers leave field margins uncut.",
    "Explain how a pressure gauge reads tyre inflation.",
    "Describe why bakeries inject steam into the oven.",
    "Explain how a whistle produces a steady tone.",
    "Describe why railways grind their rails periodically.",
    "Explain how a sponge holds and releases water.",
    "Describe why hospitals stagger appointment times.",
    "Explain how a camera aperture controls exposure.",
    "Describe why orchards plant more than one variety.",
    "Explain how a fire door slows the spread of flames.",
    "Describe why canals need towpath maintenance.",
    "Explain how a pulley reduces the force needed to lift.",
    "Describe why cheesemakers control ripening temperature.",
    "Explain how a rudder steers a boat.",
    "Describe why libraries catalogue by subject as well as author.",
    "Explain how a heat pump warms a building efficiently.",
    "Describe why rivers are monitored upstream of towns.",
    "Explain how a violin bow makes a string sound.",
    "Describe why airports mark runways with numbers.",
    "Explain how a water tower maintains supply pressure.",
    "Describe why foresters thin young plantations.",
]

# The pilot profile draws only from here, so inspecting pilot outcomes cannot
# reach any topic the study will later use.
PILOT_TOPICS = [
    "Explain how a corkscrew removes a cork.",
    "Describe why campers hang food away from the ground.",
    "Explain how a hinge lets a door swing.",
    "Describe why runners warm up before a race.",
    "Explain how a funnel speeds up pouring.",
    "Describe why shopkeepers rotate window displays.",
    "Explain how a whisk incorporates air into a mixture.",
    "Describe why walkers carry a spare layer.",
    "Explain how a doorbell circuit completes a sound.",
    "Describe why potholes form after a cold winter.",
    "Explain how a colander drains water from food.",
    "Describe why cyclists check tyre pressure regularly.",
    "Explain how a stapler binds sheets of paper.",
    "Describe why bakeries open early in the morning.",
    "Explain how a spirit thermometer registers a change.",
    "Describe why swimmers exhale underwater.",
    "Explain how a broom gathers dust into a pile.",
    "Describe why gardeners water plants in the evening.",
    "Explain how a paper clip grips without adhesive.",
    "Describe why hikers follow marked routes.",
    "Explain how a tap washer stops a drip.",
    "Describe why removal firms label every box.",
    "Explain how a shoelace knot holds under tension.",
    "Describe why libraries keep a quiet reading room.",
]

TASK_BANK = (
    [make_task(f"BRN{i:02d}", "burned", t) for i, t in enumerate(BURNED_TOPICS, 1)]
    + [make_task(f"SCR{i:02d}", "screening", t) for i, t in enumerate(SCREENING_TOPICS, 1)]
    + [make_task(f"PRE{i:02d}", "prescreen", t) for i, t in enumerate(PRESCREEN_TOPICS, 1)]
    + [make_task(f"CAL{i:02d}", "calibration", t) for i, t in enumerate(CALIBRATION_TOPICS, 1)]
    + [make_task(f"WRD{i:02d}", "wording", t) for i, t in enumerate(WORDING_TOPICS, 1)]
    + [make_task(f"CNF{i:02d}", "confirmatory", t) for i, t in enumerate(CONFIRMATORY_TOPICS, 1)]
    + [make_task(f"PLT{i:02d}", "pilot", t) for i, t in enumerate(PILOT_TOPICS, 1)]
)

TASKS = pd.DataFrame(TASK_BANK)
assert TASKS["task_id"].is_unique
assert TASKS["topic"].is_unique, (
    "topic reuse across splits would break the split: "
    f"{TASKS['topic'][TASKS['topic'].duplicated()].tolist()}")
_by_split = {s: set(g["topic"]) for s, g in TASKS.groupby("split")}
for _a, _b in itertools.combinations(sorted(_by_split), 2):
    assert _by_split[_a].isdisjoint(_by_split[_b]), f"splits {_a}/{_b} overlap"


class TaskBankInsufficient(RuntimeError):
    """A stage asked for more task clusters than its bank can supply."""


# Pilot allocation is explicit and checked, not a set of hand-written offsets
# that silently overlap or run past the end of the bank. v14's offsets were
# {0, 4, 8, 14, 16} against stage sizes that could exceed them, so pilot
# calibration and pilot wording could share topics, and .head(n) returned fewer
# rows than requested without saying so.
_PILOT_STAGE_ORDER = ("screening", "prescreen", "calibration", "wording",
                      "confirmatory")


def _pilot_allocation(sizes: dict[str, int]) -> dict[str, tuple[int, int]]:
    """Contiguous disjoint slices in a fixed order. Complete or it raises."""
    available = int((TASKS["split"] == "pilot").sum())
    needed = sum(sizes[s] for s in _PILOT_STAGE_ORDER)
    if needed > available:
        raise TaskBankInsufficient(
            f"the pilot task bank has {available} topics and the declared "
            f"pilot design needs {needed}: "
            + ", ".join(f"{s}={sizes[s]}" for s in _PILOT_STAGE_ORDER)
            + ". Author more pilot topics or reduce the declared design. "
              "Returning fewer rows than requested would silently shrink the "
              "clustering structure that every interval depends on.")
    out, cursor = {}, 0
    for stage in _PILOT_STAGE_ORDER:
        out[stage] = (cursor, cursor + sizes[stage])
        cursor += sizes[stage]
    return out


_STAGE_SIZES = {"screening": CFG.screening_tasks, "prescreen": CFG.prescreen_tasks,
                "calibration": CFG.calibration_tasks, "wording": CFG.wording_tasks,
                "confirmatory": CFG.confirmatory_tasks}
PILOT_ALLOCATION = _pilot_allocation(_STAGE_SIZES) if PILOT_MODEL_SPECIFIC else {}


def _take(split: str, n: int) -> list[dict[str, str]]:
    """Pilot runs on its own topics so its outcomes cannot inform the study."""
    if PILOT_MODEL_SPECIFIC:
        start, stop = PILOT_ALLOCATION[split]
        frame = TASKS.query("split == 'pilot'").iloc[start:stop]
    else:
        frame = TASKS.query("split == @split").head(n)
    rows = frame.to_dict("records")
    if len(rows) != n:
        raise TaskBankInsufficient(
            f"stage {split!r} asked for {n} task clusters and the "
            f"{'pilot' if PILOT_MODEL_SPECIFIC else split} bank supplied "
            f"{len(rows)}. Uncertainty is a task-cluster bootstrap, so a short "
            "allocation silently widens every interval that follows.")
    return rows


SCREENING_TASKS = _take("screening", CFG.screening_tasks)
PRESCREEN_TASKS = _take("prescreen", CFG.prescreen_tasks)
CALIBRATION_TASKS = _take("calibration", CFG.calibration_tasks)
WORDING_TASKS = _take("wording", CFG.wording_tasks)
CONFIRMATORY_TASKS = _take("confirmatory", CFG.confirmatory_tasks)
if CFG.placebo_tasks > CFG.confirmatory_tasks:
    raise TaskBankInsufficient(
        f"{CFG.placebo_tasks} U_test clusters requested from "
        f"{CFG.confirmatory_tasks} confirmatory clusters")
PLACEBO_TASKS = CONFIRMATORY_TASKS[:CFG.placebo_tasks]

# Completeness and disjointness, asserted rather than assumed.
STAGE_TASK_SETS = {
    "screening": {t["task_id"] for t in SCREENING_TASKS},
    "prescreen": {t["task_id"] for t in PRESCREEN_TASKS},
    "calibration": {t["task_id"] for t in CALIBRATION_TASKS},
    "wording": {t["task_id"] for t in WORDING_TASKS},
    "confirmatory": {t["task_id"] for t in CONFIRMATORY_TASKS},
}
for _a, _b in itertools.combinations(STAGE_TASK_SETS, 2):
    _shared = STAGE_TASK_SETS[_a] & STAGE_TASK_SETS[_b]
    assert not _shared, f"stages {_a} and {_b} share task clusters {sorted(_shared)}"
for _stage, _want in _STAGE_SIZES.items():
    assert len(STAGE_TASK_SETS[_stage]) == _want, (
        f"stage {_stage} holds {len(STAGE_TASK_SETS[_stage])} distinct clusters, "
        f"not the declared {_want}")

print()
print(TASKS.groupby("split").size().to_string())
print(f"\nin use ({'PILOT bank' if PILOT_MODEL_SPECIFIC else 'study bank'}): "
      f"{len(SCREENING_TASKS)} screening, {len(PRESCREEN_TASKS)} prescreen, "
      f"{len(CALIBRATION_TASKS)} calibration, {len(WORDING_TASKS)} wording, "
      f"{len(CONFIRMATORY_TASKS)} confirmatory, {len(PLACEBO_TASKS)} U_test")
