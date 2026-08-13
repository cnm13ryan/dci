"""Stage 162 — migrated from notebook cell 162.py (coupling_and_response_bank).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/162.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.analysis.coupling_audit import kappa_is_degenerate  # noqa: F401
from dci.provenance.hashes import sha_text, stable_int  # noqa: F401
from dci.verifiers.rules import v_alliteration, v_alphabetical_starts, v_caps_sentence_count, v_caps_word, v_comma_and_min_words, v_commas_per_sentence, v_distinct_integers, v_exact_char_total, v_exact_integer_count, v_exact_sentence_count, v_forbid_word_set, v_increasing_lengths, v_integer_sum, v_long_word_each_sentence, v_max_integer_count, v_min_integer_count, v_min_long_words_per_sentence, v_min_sentence_words, v_no_char, v_no_digits, v_no_suffix, v_nondecreasing_lengths, v_paren_pairs, v_percent_count, v_question_sentence_count, v_quote_pairs, v_require_word, v_require_word_set, v_semicolon_each, v_sentence_ends_long, v_sentence_initial, v_sentence_initial_forbidden_word, v_unique_words, v_vowel_words_per_sentence, v_word_band  # noqa: F401

def run_verifier_tests() -> int:
    four = ("One begins here. Two continues clearly. "
            "Three adds useful context. Four concludes the response.")
    newline_four = ("Trees cool the street\nShade lowers surface heat\n"
                    "Canopy traps moisture\nCities gain resilience")
    bullet_four = ("- Trees cool the street.\n- Shade lowers heat.\n"
                   "- Canopy traps moisture.\n- Cities gain resilience.")

    checks = [
        # ---------------------------------------------- sentence-scoped
        (v_exact_sentence_count(four, 4).status, "full"),
        (v_exact_sentence_count(newline_four, 4).status, "full"),
        (v_exact_sentence_count(bullet_four, 4).status, "full"),
        (v_exact_sentence_count("One. Two. Three.", 4).status, "partial"),
        (v_exact_sentence_count("One. Two.", 4).status, "violation"),
        (v_exact_sentence_count("", 4).status, "unscorable"),
        (v_increasing_lengths("Birds fly. Small birds fly swiftly. "
                              "Many small birds fly swiftly above fields.").status, "full"),
        (v_increasing_lengths("Birds fly now. Fish swim fast. Clouds move away.").status,
         "violation"),
        (v_nondecreasing_lengths("Birds fly. Small birds fly. "
                                 "Many small birds fly high.").status, "full"),
        (v_nondecreasing_lengths("Many small birds fly high. Birds fly.").status,
         "violation"),
        (v_sentence_initial("Systems learn. Science advances.", "S").status, "full"),
        (v_sentence_initial("Systems learn. Evidence accumulates.", "S").status, "partial"),
        (v_min_sentence_words("This sentence contains at least eight clearly "
                              "separated words today.", 8).status, "full"),
        (v_min_sentence_words("Too short.", 8).status, "violation"),
        (v_alphabetical_starts("Agriculture expands. Bridges connect. "
                               "Cities develop.").status, "full"),
        (v_alphabetical_starts("Cities develop. Agriculture expands.").status, "violation"),
        (v_long_word_each_sentence("Migration patterns shift. "
                                   "Coastlines experience erosion.", 7).status, "full"),
        (v_long_word_each_sentence("Birds fly. Fish swim.", 7).status, "violation"),
        (v_sentence_ends_long("The tide reshapes the coastline. "
                              "Sailors respect the currents.", 7).status, "full"),
        (v_commas_per_sentence("First, we look. Second, we measure.", 1).status, "full"),
        (v_commas_per_sentence("We look. We measure.", 1).status, "violation"),
        (v_commas_per_sentence("First, we look, then we measure.", 2).status, "full"),
        (v_min_long_words_per_sentence(
            "Migration patterns influence coastline erosion patterns.", 7, 2).status, "full"),
        (v_min_long_words_per_sentence("Birds fly across migration routes.", 7, 2).status,
         "violation"),
        (v_word_band("Many small birds fly swiftly above the wide open fields "
                     "each morning.", 5, 20).status, "full"),
        (v_word_band("Birds fly.", 5, 20).status, "violation"),
        (v_semicolon_each("We look; we measure.").status, "full"),
        (v_semicolon_each("We look. We measure.").status, "violation"),
        (v_comma_and_min_words("After the tide turns, the fishers set their "
                               "nets again.", 8).status, "full"),
        # ------------------------------------------------- whole-text v12
        (v_unique_words("Alpha beta gamma delta.").status, "full"),
        (v_unique_words("Alpha beta alpha.").status, "partial"),
        (v_integer_sum("The values are 10, 20, and 30.", 3, 60).status, "full"),
        (v_distinct_integers("Examples include 4, 8, and 15.", 3).status, "full"),
        # ------------------------------------------ v13 unrelated targets
        # lexical
        (v_forbid_word_set("A calm and measured account.", ("very", "important", "process")).status,
         "full"),
        (v_forbid_word_set("A very calm account.", ("very", "important", "process")).status,
         "partial"),
        (v_forbid_word_set("A very important process.", ("very", "important", "process")).status,
         "violation"),
        (v_require_word_set("The evidence crossed a threshold after gradual change.",
                            ("evidence", "threshold", "gradual")).status, "full"),
        (v_require_word_set("The evidence was clear.",
                            ("evidence", "threshold", "gradual")).status, "partial"),
        (v_require_word_set("Nothing matches here.",
                            ("evidence", "threshold", "gradual")).status, "violation"),
        (v_no_suffix("Water moves down a slope.", "ly").status, "full"),
        (v_no_suffix("Water moves slowly down a slope.", "ly").status, "partial"),
        # Orthographic, not part of speech: these are nouns and verbs, and the
        # rule still catches them.
        (v_no_suffix("Family reply supply apply here.", "ly").status, "partial"),
        (v_no_suffix("Family reply supply apply.", "ly").status, "violation"),
        (v_alliteration("Pumps push packed particles past pipes.", "p", 4).status, "full"),
        (v_alliteration("Pumps push water.", "p", 4).status, "partial"),
        (v_caps_word("The NASA report is clear.", 1, 3).status, "full"),
        (v_caps_word("The report is clear.", 1, 3).status, "violation"),
        (v_caps_word("The NASA and ESA reports agree.", 1, 3).status, "partial"),
        # format
        (v_exact_char_total("We look; we measure; we report.", ";", 2).status, "full"),
        (v_exact_char_total("We look; we measure.", ";", 2).status, "partial"),
        (v_exact_char_total("We look. We measure.", ";", 2).status, "violation"),
        (v_exact_char_total("One thing: clarity.", ":", 1).status, "full"),
        (v_paren_pairs("The tide (twice daily) shapes the shore.", 1).status, "full"),
        (v_paren_pairs("The tide shapes the shore.", 1).status, "violation"),
        (v_paren_pairs("The tide (twice daily shapes the shore.", 1).status, "violation"),
        # One complete pair plus a stray opener: the count is right, the
        # balance is not, so it cannot pass.
        (v_paren_pairs("The tide (twice daily) shapes (the shore.", 1).status, "partial"),
        (v_paren_pairs("The tide (twice daily) shapes (the shore.", 1).binary_pass, 0),
        (v_quote_pairs('He called it "steady" flow.', 1).status, "full"),
        (v_quote_pairs('He called it steady flow.', 1).status, "violation"),
        (v_quote_pairs('He called it "steady flow.', 1).status, "violation"),
        (v_quote_pairs('He called it "steady" flow".', 1).status, "partial"),
        (v_quote_pairs("He called it “steady” flow.", 1).status, "full"),
        (v_no_char("We look and we measure.", ",").status, "full"),
        (v_no_char("We look, and we measure.", ",").status, "violation"),
        # numerical
        (v_exact_integer_count("There are 3 gates and 7 locks.", 2).status, "full"),
        (v_exact_integer_count("There are 3 gates.", 2).status, "partial"),
        (v_exact_integer_count("There are no numbers.", 2).status, "violation"),
        (v_distinct_integers("Values 2, 4, 6 and 8 apply.", 4).status, "full"),
        (v_distinct_integers("Values 2, 4, 6 and 6 apply.", 4).status, "partial"),
        (v_min_integer_count("Values of 12 and 18 appear.", 2).status, "full"),
        (v_min_integer_count("Only 12 appears.", 2).status, "partial"),
        (v_min_integer_count("No numbers appear.", 2).status, "violation"),
        (v_max_integer_count("No numbers appear.", 2).status, "full"),
        (v_max_integer_count("Values of 12 and 18 appear.", 2).status, "full"),
        (v_max_integer_count("Values 2 and 4 and 6 and 8 appear.", 2).status, "violation"),
        (v_no_digits("No numerals appear here.").status, "full"),
        (v_no_digits("There are 3 items.").status, "violation"),
        (v_integer_sum("Shares of 50, 30 and 20 make the whole.", 3, 100).status, "full"),
        (v_integer_sum("Shares of 50, 30 and 25 make the whole.", 3, 100).status, "partial"),
        (v_percent_count("About 40% of the flow returns.", 1).status, "full"),
        (v_percent_count("About 40% of 60% returns.", 1).status, "partial"),
        (v_percent_count("Most of the flow returns.", 1).status, "violation"),
        # bridge family
        (v_vowel_words_per_sentence("An open estimate is available always.", 3).status,
         "full"),
        (v_vowel_words_per_sentence("Rivers rise slowly here.", 3).status, "violation"),
        (v_caps_sentence_count("Rivers rise. The NASA report is clear.", 1, 3).status,
         "full"),
        (v_caps_sentence_count("Rivers rise. Levels settle.", 1, 3).status, "violation"),
        (v_caps_sentence_count("NASA agrees. The ESA report is clear.", 1, 3).status,
         "partial"),
        (v_sentence_initial_forbidden_word("Rivers rise. Levels settle.", "the").status,
         "full"),
        (v_sentence_initial_forbidden_word("The rivers rise. Levels settle.", "the").status,
         "partial"),
        (v_question_sentence_count("Rivers rise. What follows? Levels settle.", 1).status,
         "full"),
        (v_question_sentence_count("Rivers rise. Levels settle.", 1).status, "violation"),
        # screening partner
        (v_require_word("Overall the system holds.", "overall").status, "full"),
        (v_require_word("The system holds.", "overall").status, "violation"),
        # empty input is unscorable everywhere, never a silent pass
        (v_forbid_word_set("", ("very",)).status, "unscorable"),
        (v_exact_char_total("", ";", 2).status, "unscorable"),
        (v_percent_count("", 1).status, "unscorable"),
    ]
    for i, (got, want) in enumerate(checks):
        assert got == want, f"verifier test {i} failed: got {got}, expected {want}"
    print(f"All {len(checks)} verifier unit tests passed.")
    return len(checks)


S.N_VERIFIER_TESTS = run_verifier_tests()

# The screening partner must be mechanically inert against every U candidate:
# adding it may not by itself flip any candidate's verdict.
_INERT_BASE = ("Pressure pushes packed particles past pipes; flow persists; "
               'one point matters: "steady" (mostly) with 40 and 60 plus 12% '
               "evidence threshold gradual PUMP.")
for _uid in S.U_CANDIDATE_IDS:
    _before = S.verify(_INERT_BASE, _uid).binary_pass
    _after = S.verify(_INERT_BASE + " Overall it holds.", _uid).binary_pass
    if _before != _after:
        S.log_departure(
            "screening", f"N_NEUTRAL inert against {_uid}",
            "appending the neutral partner's satisfying text flips the verdict",
            "recorded; the screening composition result for this candidate is "
            "confounded with the partner and is reported alongside it")


# ------------------------------------------- response bank and probes
S.RESPONSE_BANK = [
    "Tides rise and fall twice each day. Coastal fishers plan around them. "
    "Some species feed only at high water. Local knowledge still matters.",
    "Glass recycling saves energy. Cullet melts at a lower temperature. "
    "Furnaces therefore burn less fuel. The saving compounds across batches.",
    "A sundial marks time by shadow. The gnomon casts a moving line. "
    "Hour marks are spaced unevenly. Latitude changes the layout.",
    "Forests regrow in stages after fire. Fast pioneers arrive first. "
    "Shade-tolerant trees follow later. The sequence takes decades.",
    "Canal locks raise and lower boats. Gates seal a chamber. "
    "Water enters or drains. The boat rides the level change.",
    "Migratory birds follow seasonal food. Daylight length triggers departure. "
    "Routes are learned and inherited. Weather can push flocks off course.",
    "Filters trap particles by size. Activated carbon adsorbs some chemicals. "
    "Membranes exclude smaller molecules. Maintenance keeps flow steady.",
    "Permeable pavement lets rain soak through. Runoff pressure drops. "
    "Storm drains overflow less often. Maintenance prevents clogging.",
    "Honey resists spoiling for years. Its sugar content binds water tightly. "
    "Microbes cannot grow without free moisture. Sealed jars keep it stable.",
    "Switchbacks reduce the gradient a vehicle must climb. Each turn trades "
    "distance for slope. Engines and brakes work less hard. Erosion control "
    "still demands attention.",
    "Coral reefs shelter enormous numbers of species. Their structure creates "
    "countless hiding places. Warm shallow water supports the algae inside "
    "the coral. Bleaching breaks that partnership.",
    "Paper begins as wood chips. Cooking separates the fibres from lignin. "
    "The pulp is screened and pressed. Drying sets the final sheet.",
    "A greenhouse traps warmth by limiting convection. Glass admits short "
    "wavelengths readily. Heat radiated back is slower to escape. Vents "
    "prevent overheating on bright days.",
    "Timetables build in recovery time deliberately. Small delays would "
    "otherwise cascade down the line. Slack absorbs the disruption. "
    "Passengers see a more reliable service.",
    "Kites stay aloft through steady airflow. The angled surface deflects air "
    "downward. Reaction lifts the frame. Tail drag keeps the nose pointed "
    "into the wind.",
    # v13 additions: punctuation, numerals and casing, so the new whole-text
    # verifiers have non-degenerate baselines in the probes below.
    'Pumps push packed particles past pipes; pressure persists. One point '
    'matters: "steady" flow (mostly) beats surges. Shares of 50, 30 and 20 '
    "describe the load. Overall about 12% returns as EVIDENCE of the threshold.",
    "Rails carry 2 loads and 4 axles; wear accumulates gradually. Grinding "
    'restores the profile: a "quiet" ride (usually) follows. Inspectors '
    "record 15% of defects. Maintenance windows are short.",
    # Four sentences of strictly increasing length. Without these the coupling
    # probe has no response where BOTH the target and the focal constraint pass
    # at baseline, so it can never observe a joint flip and kappa comes back
    # undefined for the one pair the study is about.
    "Locks lift boats. Gates hold the water back firmly. Chambers fill until "
    "the levels finally match exactly. Boats then move onward through the "
    "opened upper gates without any further delay.",
    "Rain falls. Gutters carry water away. Soakaways spread the flow across "
    "gravel beds. Slowly the ground absorbs what the drains would otherwise "
    "carry into the river.",
    "Kites rise. Steady wind lifts them. The angled surface deflects moving "
    "air downward. Reaction lifts the light frame while tail drag holds the "
    "nose steady.",
    "Filters trap grit. Carbon adsorbs some dissolved chemicals. Membranes "
    "exclude the smaller molecules from passing through. Regular maintenance "
    "keeps the flow steady and stops the pressure from climbing.",

    # ---------------------------------------------------------------- v14
    # Coupling is estimated only on responses where BOTH the target and the
    # candidate already pass, so a bank that never satisfies a candidate leaves
    # kappa undefined for it, drops it from the sensitivity regression, and
    # produces PRECISION_INSUFFICIENT for a reason that belongs to the bank
    # rather than to the study. v13 had four such responses for the focal pair
    # against a required minimum of twenty. These blocks are written to exactly
    # four sentences of strictly increasing length, and are graded through the
    # sentence-length ladder, the comma and semicolon patterns, the long-word
    # counts and the initial-letter rules, so that every candidate in the pool
    # has an estimable coupling with the target. They are prose on the same
    # subject matter as the rest of the bank, not generated feature strings.
    "Locks lift laden barges between two canal levels. Gates seal the stone "
    "chamber so that water cannot escape downstream. Sluices admit enough "
    "water from the upper reach to match the level above the gate. Keepers "
    "open the upper gates and the barge continues its journey along the next "
    "quiet reach without any further delay.",
    "Reed beds clean water without any pumps. Bacteria living on the roots "
    "break down most of the organic load. Gravel beneath the reeds spreads "
    "the flow so that no single channel carries all of it. The outflow leaves "
    "clear enough for a chalk river although it still needs watching through "
    "the warmest weeks of summer.",
    "Snow stores the winter precipitation. The timing of the melt matters "
    "more than the total depth. An early warm spell sends the whole store "
    "downstream while the reservoirs are still held low. A late and gradual "
    "melt instead spreads the same volume across the weeks when irrigation "
    "demand actually reaches its annual peak.",
    "Tides follow the moon. Spring tides arrive at syzygy each fortnight. "
    "Neap tides occur instead when the sun and the moon pull against each "
    "other. Harbour masters plan every deep-draught movement around the "
    "predicted maximum and around the hours on either side of it.",
    "Peat holds water and carbon. Drainage ditches cut through a bog release "
    "both. Blocking those ditches raises the water table and the surface "
    "begins to recover. Restoration costs little beside the value of the "
    "carbon that an eroding bog would otherwise continue to release for "
    "decades.",
    "Weirs raise the upstream level. They also block the fish that migrate "
    "through the reach. A fish pass returns a climbable gradient beside the "
    "structure without losing the head above it. Monitoring shows which "
    "designs suit which species and those results have already changed the "
    "way that new weirs are built.",
    "Bridges constrain a floodplain. Their approach embankments behave as "
    "dams in the largest events. Water backs up behind them and the opening "
    "beneath the deck accelerates whatever passes through. Scour protection "
    "around the piers is therefore designed for a velocity that the open "
    "river alongside would never once reach.",
    "Aquifers store water underground. Boreholes reach them through the "
    "overlying rock. Casings keep the shallow and contaminated layers out of "
    "the deeper supply. Drilling records tell later engineers exactly what "
    "was found at every depth and precisely where each seal was finally "
    "placed.",
    "Groundwater rises and falls across a year in a rhythm that irrigation "
    "can easily disturb. Monitoring wells record that rhythm cheaply and they "
    "give a decade of context to any single dry season. A licence written "
    "without those records treats an unusually wet decade as though it were "
    "the ordinary condition of the aquifer. Regulators who hold the longer "
    "series can instead set an abstraction limit that the resource will still "
    "support in the driest years of the record.",
    "Culverts beneath a road are sized for a storm that the designer has "
    "chosen in advance. The chosen storm reflects the traffic above and the "
    "damage that a failure would cause to the wider network. A blocked screen "
    "at the inlet reduces that design capacity to whatever the debris happens "
    "to leave open on the day. Inspection after every large rainfall is "
    "therefore worth more to the network than another increment of concrete "
    "diameter would ever be worth.",
    "Salt marshes absorb the first surge of an incoming storm tide. Their "
    "grasses slow the water and hold the fine sediment arriving with it. "
    "Behind them the sea wall faces a gentler load than it would face on a "
    "bare shore. Coastal engineers now plant new marsh wherever the ground "
    "level and the local tidal range together allow it to establish.",
    "Canal keepers open the lower gates when a laden barge waits below the "
    "lock. Water from the upper reach then floods slowly into the stone "
    "chamber beneath the gate. The barge rises with the level until its deck "
    "sits flush with the towpath above the lock. Keepers close the paddles "
    "again and the whole cycle begins once more for the next boat that is "
    "waiting.",
    "Aqueducts carry water across a valley on a gradient that is measured in "
    "centimetres for every kilometre of channel length. Roman surveyors "
    "reached that precision with sighting instruments and long patience "
    "rather than with any of the optics that a modern engineer expects. A "
    "channel falling too steeply would scour its own lining away within a few "
    "seasons and the repair would fall to the city that depended on it. A "
    "channel falling too gently would silt up instead and the city at the far "
    "end of it would slowly and quietly lose the supply that it had paid for.",
    "River gauges record a stage height rather than a discharge because the "
    "depth of water is very much simpler to measure reliably over many years. "
    "A rating curve then converts that recorded height into a flow using "
    "careful measurements taken right across the channel at many different "
    "levels of the river. The curve shifts whenever the bed scours or a "
    "gravel bar builds, so it has to be checked again after every large flood "
    "that passes through the reach. A forecaster who ignores that slow drift "
    "will publish flows that look precise and authoritative while the numbers "
    "themselves quietly wander away from the river that they claim to "
    "describe.",
    "Groundwater models divide an aquifer into a grid of cells and then solve "
    "for the hydraulic head in every one of those cells at each step of the "
    "whole of the simulated period. Each cell exchanges water with each of "
    "its neighbours according to the conductivity of the material that lies "
    "between them and according to the difference in head across that same "
    "shared boundary. Calibration then adjusts those conductivities one "
    "region at a time until the simulated heads agree with the water levels "
    "that have actually been observed in the monitoring wells scattered "
    "across the modelled area. A model that reproduces the past extremely "
    "well can still forecast very badly indeed whenever some future stress "
    "happens to fall outside the range of conditions that the calibration was "
    "ever able to see.",
    "After the rain, the culvert fills. Beneath the road, the pipe narrows "
    "and the flow speeds up. On the far side, the water spreads across a "
    "shallow basin and slows again. Within the hour, the basin has drained "
    "away and the grass beneath it is merely damp.",
    "In winter, ice narrows the channel. Along the banks, frozen shelves grow "
    "outward over the water. Under the remaining gap, the same discharge must "
    "pass through far less room. By late February, a thaw releases the "
    "shelves and the river carries them downstream in a slow crowd.",
    "First, the gate opens, and water enters. Next, the chamber fills, and "
    "the barge lifts steadily. Then, the upper gate swings, and the barge "
    "moves out onto the reach above. Finally, the paddles close, and the lock "
    "stands ready for the boat that follows behind it.",
    "Early, the tide turns, and the mud appears. Later, the waders arrive, "
    "and the flats fill with feeding birds. Afterwards, the flood returns, "
    "and the whole feeding ground disappears beneath it. Overnight, the cycle "
    "repeats, and the same birds gather again on the same falling tide.",
    "Whenever the reservoir approaches its top water level, the operators "
    "begin a controlled release downstream. The release is timed against the "
    "forecast, so that the drawdown finishes before the next rainfall "
    "arrives. Fisheries and navigation both constrain the rate, and the "
    "licence sets a ceiling that no forecast may override. Where those "
    "constraints conflict with an approaching flood, the operator records the "
    "decision and the reasoning behind it in the log that the regulator later "
    "reads.",
    "Rain falls; drains carry it. Soakaways spread the flow; gravel beds hold "
    "it. The ground absorbs the water slowly; the river never sees the surge. "
    "Maintenance keeps the gravel clear; without it the beds clog and the "
    "arrangement quietly stops working.",
    "Ice forms; the channel narrows. Shelves grow outward; the open water "
    "shrinks. Discharge continues unchanged; the velocity beneath the ice "
    "rises. Thaw arrives eventually; the shelves break free and drift down "
    "towards the estuary.",
    "Streams begin as seepage. Springs mark where the water table meets the "
    "surface. Sediment carried from the hillside settles wherever the current "
    "slackens enough. Slowly the channel deepens and the valley takes the "
    "shape that the water has been drawing for centuries.",
    "Sluices control the level. Screens keep the larger debris away from "
    "them. Silt still settles behind the structure and reduces the storage "
    "above it. Study of the deposition pattern tells the operator when the "
    "next dredging campaign will actually be needed.",
    "Aquifers hold water. Boreholes reach into them. Casings exclude the "
    "shallow contaminated layers above. Drilling records show later engineers "
    "where every seal was placed.",
    "The catchment splits into three gauged sub-basins. They contribute 10 "
    "and 20 and 30 units of the measured total. Together those shares make up "
    "the whole discharge recorded at the outlet gauge below. Any imbalance "
    "between them points either to an ungauged inflow or to a meter that has "
    "drifted out of calibration.",
    "Locks raise vessels. Gates seal chambers quietly. Sluices admit river "
    "water through narrow openings. Keepers watch levels rise until barges "
    "continue upstream past waiting crowds along old towpaths.",
    "Sediment transport governs morphology. Suspended particles settle "
    "whenever turbulence decreases sufficiently. Coarser material advances "
    "downstream through intermittent rolling rather than continuous "
    "suspension. Engineering interventions therefore redistribute deposition "
    "considerably beyond whatever reach the original construction actually "
    "occupied.",
    "Infiltration reduces runoff. Permeable surfaces increase infiltration "
    "considerably. Compacted subsoil beneath permeable paving frequently "
    "negates whatever improvement appeared. Investigations before "
    "installation therefore examine subsurface conditions carefully instead "
    "of assuming uniformly favourable permeability.",
    "Estuaries mix fresh water and salt water along a front that moves with "
    "the state of the tide. The position of that front governs where the "
    "finest sediment settles out of suspension each day. Dredging in the "
    "wrong reach therefore returns within a season and the navigation gains "
    "very little. Survey work that tracks the front across a spring and neap "
    "cycle tells the port where the effort will actually last.",
    "Reservoir operators balance supply against flood storage throughout the "
    "whole of the winter season. Holding a high level protects the summer "
    "supply but leaves very little room for a storm. Holding a low level "
    "protects the towns downstream and risks a shortage in the following "
    "August. The rule curve written into the licence fixes that trade in "
    "advance so no single storm forces an improvised choice.",
    "Once, the barrier closed, and the tide stopped. Again, the surge "
    "arrived, and the defence held firmly. Afterwards, the gates reopened, "
    "and the river resumed its ordinary course. Later, the record showed, and "
    "the engineers confirmed, that the margin had been comfortable.",
    "Slowly, the marsh accreted, and the level rose. Steadily, the creeks "
    "deepened, and the drainage improved. Eventually, the vegetation changed, "
    "and the higher plants colonised the surface. Finally, the whole flat "
    "stabilised, and the shore behind it needed far less maintenance.",
    "Levels fall; abstraction continues. Springs weaken; the headwaters "
    "shorten. Fisheries suffer first; the regulator receives complaints. "
    "Licences are reviewed at last; the aquifer recovers over the following "
    "several years.",
    "Gates lift; water enters. Chambers fill; the vessel rises. Upper gates "
    "swing open; the reach beyond lies level. Paddles close behind; the lock "
    "stands ready for the next boat downstream.",
    "Whenever a storm is forecast across the upper catchment, the duty "
    "officer reviews the reservoir level. If the forecast is confident "
    "enough, a controlled release begins, and the towns downstream are warned "
    "first. Where the forecast is uncertain, the officer holds the level, and "
    "accepts a smaller margin of flood storage. Either way, the decision and "
    "the forecast that supported it are recorded in a log that the regulator "
    "reads afterwards.",
    "Because the gauge sits above a stable bedrock section, the rating curve "
    "changes very slowly. During the largest floods, however, the water "
    "leaves the channel, and the rating no longer applies. For those events, "
    "the hydrologists survey the flood marks, and reconstruct the peak from "
    "the slope. Even then, the reconstructed peak carries an uncertainty that "
    "any sensible forecast will report alongside the number itself.",
    "Silt accumulates behind the barrier. Storage above it slowly disappears. "
    "Surveys measure the loss every few years. Sediment bypass systems can "
    "slow the process considerably.",
    "Shallow wells respond quickly. Storm recharge reaches them within days. "
    "Sustained drought empties them long before the deeper boreholes suffer. "
    "Supply planning therefore treats the two sources as genuinely different "
    "assets.",
    "Rivers carry gravel. Bars build where the current slackens. Gravel bars "
    "deflect the flow towards the outer bank. Erosion there proceeds until "
    "the bend eventually abandons its former alignment.",
    "Storms erode. Calm weather rebuilds. The beach oscillates around a slow "
    "trend. Nourishment schemes alter that trend without ever removing the "
    "oscillation.",
    "The estuary narrows sharply at the old crossing, and the current there "
    "runs fast. Ferry crews learned the timing of the slack water, and worked "
    "their crossings around it. The bridge that replaced them ignores the "
    "tide, but its piers still face the same current. Scour monitoring around "
    "those piers continues through every winter, and the results inform the "
    "maintenance programme.",
    "River restoration returns a straightened channel to something closer to "
    "its former planform over a reach of several kilometres. The work "
    "reintroduces meanders and riffles and pools that a century of drainage "
    "engineering had systematically removed from the valley floor. Floodplain "
    "connection returns with them, and the reach begins to store water during "
    "the events that once passed straight through it. Monitoring across the "
    "following decade shows whether the restored reach holds its new form or "
    "gradually reverts towards the straightened alignment that preceded it.",
]

S.MUTATIONS = {
    "drop_word": lambda t: re.sub(r"\b\w+\s", "", t, count=1),
    "swap_sentences": lambda t: " ".join(
        (lambda p: p[1:2] + p[0:1] + p[2:])(S._REAL_SPLIT(t))),
    "strip_final_period": lambda t: t.rstrip(".") if t.endswith(".") else t + " and more",
    "join_sentences": lambda t: t.replace(". ", ", ", 1),
    "add_digit": lambda t: t + " There are 7 cases.",
    "add_semicolon": lambda t: t.replace(". ", "; ", 1),
    "add_paren": lambda t: t + " (a further note)",
    "upper_first": lambda t: re.sub(r"\b([a-z]{4,})\b",
                                    lambda m: m.group(1).upper(), t, count=1),
}


def mutation_profile(constraint_id: str) -> dict[str, float]:
    """Fraction of bank responses whose verdict flips under controlled edits.

    Doubles as the output-space restrictiveness feature and as the boundary
    detector used to stratify the blinded reliability sample.
    """
    baseline = [S.verify(r, constraint_id).binary_pass for r in S.RESPONSE_BANK]
    flips, total = 0, 0
    for mutate in S.MUTATIONS.values():
        for response, base in zip(S.RESPONSE_BANK, baseline):
            try:
                mutated = mutate(response)
            except Exception:
                continue
            total += 1
            flips += int(S.verify(mutated, constraint_id).binary_pass != base)
    return {"base_pass_rate": float(np.mean(baseline)),
            "mutation_flip_rate": flips / max(total, 1)}


# The coupling probe's edit set is part of what kappa MEANS, so it is named,
# hashed, and frozen alongside the response bank.
COUPLING_EDITS: dict[str, Callable[[str], str]] = {
    "drop_boundary": lambda t: t.replace(". ", " "),
    "newline_boundary": lambda t: t.replace(". ", ".\n"),
    "semicolon_boundary": lambda t: t.replace(". ", "; "),
    "exclamation_boundary": lambda t: t.replace(". ", "! "),
    "append_clause": lambda t: t.rstrip(".") + " and so on",
}

S.RESPONSE_BANK_SHA256 = sha_text("\n\x00\n".join(S.RESPONSE_BANK))
S.MUTATION_SPEC_SHA256 = S.source_fingerprint(list(S.MUTATIONS.values()))
S.COUPLING_SPEC_SHA256 = S.source_fingerprint(list(COUPLING_EDITS.values()))


def verifier_coupling_detail(constraint_a: str, constraint_b: str) -> dict[str, float]:
    """Fraction of boundary-only edits that flip BOTH verifiers together.

    A rule stated on the verifier's field name would exclude the focal pair
    itself, because B shares A's segmentation span, so coupling is measured.
    Responses where either verifier already fails carry no information and are
    dropped rather than counted as non-flips, which is why the effective
    denominator is reported rather than assumed to be bank x edits.

    Uncertainty comes from resampling whole bank responses, because the edits
    applied to one response are not independent observations.
    """
    informative, per_response = [], []
    for response in S.RESPONSE_BANK:
        base_a = S.verify(response, constraint_a).binary_pass
        base_b = S.verify(response, constraint_b).binary_pass
        if not (base_a and base_b):
            continue
        informative.append(response)
        flips = 0
        for edit in COUPLING_EDITS.values():
            mutated = edit(response)
            flips += int(S.verify(mutated, constraint_a).binary_pass != base_a
                         and S.verify(mutated, constraint_b).binary_pass != base_b)
        per_response.append(flips / len(COUPLING_EDITS))

    n_info = len(per_response)
    denominator = n_info * len(COUPLING_EDITS)
    if n_info == 0:
        return {"kappa": float("nan"), "se": float("nan"),
                "n_informative_responses": 0, "n_contributing_mutations": 0,
                "effective_denominator": 0, "resolution": float("nan")}
    values = np.asarray(per_response, dtype=float)
    kappa = float(values.mean())
    if n_info >= 2:
        rng = np.random.default_rng(stable_int(f"kappa|{constraint_a}|{constraint_b}"))
        draws = np.array([values[rng.integers(0, n_info, n_info)].mean()
                          for _ in range(600)])
        se = float(draws.std(ddof=1))
    else:
        se = float("nan")
    return {"kappa": kappa, "se": se,
            "n_informative_responses": n_info,
            "n_contributing_mutations": int(values.sum() * len(COUPLING_EDITS)),
            "effective_denominator": denominator,
            "resolution": 1.0 / denominator}


with S.phase("feature_build"):
    MUTATION_TABLE = pd.DataFrame(
        [{"constraint_id": cid, **mutation_profile(cid)} for cid in S.CONSTRAINTS]
    ).set_index("constraint_id")
    COUPLING_TABLE = pd.DataFrame(
        [{"constraint_id": cid,
          **verifier_coupling_detail(S.CFG.target_id, cid)}
         for cid in (*S.CANDIDATE_IDS, S.CFG.focal_id)]).set_index("constraint_id")

S.COUPLING = COUPLING_TABLE["kappa"].rename("coupling_with_A")
S.COUPLING_SE = COUPLING_TABLE["se"].rename("coupling_se")
# v15.1: candidate-level support, so the eligibility audit can demand of every
# candidate exactly what makes the focal estimate usable.
S.COUPLING_N_INFORMATIVE = COUPLING_TABLE["n_informative_responses"].rename(
    "n_informative_responses")
# Is the statistic discriminating at all? A kappa that collapses onto one or two
# values makes an audit on it vacuous -- which is a measurement-design problem to
# fix in the probe, never a reason to widen or drop the declared tolerance.
S.COUPLING_DEGENERACY = kappa_is_degenerate(S.COUPLING, S.COUPLING_SE)

MUTATION_TABLE.to_csv(S.AUDIT_DIR / "mutation_profile.csv")
COUPLING_TABLE.to_csv(S.AUDIT_DIR / "verifier_coupling.csv")

display(MUTATION_TABLE.round(3))
display(COUPLING_TABLE.round(4))

S.FOCAL_COUPLING = float(S.COUPLING.get(S.CFG.focal_id, float("nan")))
S.FOCAL_COUPLING_SE = float(S.COUPLING_SE.get(S.CFG.focal_id, float("nan")))
S.FOCAL_COUPLING_N = int(COUPLING_TABLE.at[S.CFG.focal_id, "n_informative_responses"])

S.COUPLING_USABLE = bool(
    np.isfinite(S.FOCAL_COUPLING)
    and S.FOCAL_COUPLING_N >= S.CFG.min_informative_coupling_probes
    and np.isfinite(S.FOCAL_COUPLING_SE)
    and S.FOCAL_COUPLING_SE <= S.CFG.max_coupling_se)

print(f"""
Coupling with the target, focal constraint {S.CFG.focal_id}
  kappa                     : {S.FOCAL_COUPLING:.4f}
  standard error            : {S.FOCAL_COUPLING_SE:.4f}   (ceiling {S.CFG.max_coupling_se})
  informative bank responses: {S.FOCAL_COUPLING_N}        (minimum {S.CFG.min_informative_coupling_probes})
  effective denominator     : {int(COUPLING_TABLE.at[S.CFG.focal_id, 'effective_denominator'])}
  usable as a matched component: {S.COUPLING_USABLE}

role: {S.CFG.coupling_role}

A control may not be held to a stricter coupling standard than the focal
constraint, so coupling is matched to it rather than capped.

With role='matched' kappa is a quantitative signature component with its own
caliper and its own uncertainty, and an unusable focal estimate stops the run
with PRECISION_INSUFFICIENT rather than quietly disappearing, which is what v13
did. With role='audit' kappa leaves the signature and becomes a hard
measurement-coupling audit at |kappa_C - kappa_B| <= {S.CFG.coupling_audit_max};
that demotion is a declared protocol choice and is recorded in the hash.

v15.1: that audit is now ENFORCED in admit_candidates (it was declared, printed
here, and consumed nowhere), and candidates must satisfy the same support rules
that decide whether the focal estimate is usable.

kappa discrimination: {S.COUPLING_DEGENERACY['n_distinct']} distinct values over
{S.COUPLING_DEGENERACY['n_estimates']} constraints, spread
{S.COUPLING_DEGENERACY['spread']:.4f}, median SE {S.COUPLING_DEGENERACY['median_se']:.4f}.
  degenerate: {S.COUPLING_DEGENERACY['degenerate']}
A degenerate kappa makes the audit vacuous. The remedy is a better coupling
probe, never a wider tolerance.

response bank {S.RESPONSE_BANK_SHA256[:12]} | mutations {S.MUTATION_SPEC_SHA256[:12]} | coupling edits {S.COUPLING_SPEC_SHA256[:12]}
""")
