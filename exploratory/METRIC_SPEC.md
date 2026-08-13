# Structural-strategy metric specification (frozen 2026-08-11)

The measures the mechanism claims are built on. Frozen here so that a later
change is a visible amendment rather than a silent drift, and so that every
reported number can be traced to an exact definition.

Implementation: `dci_exploratory/extensions.py` (`splice_count`) and
`dci_exploratory/mechanism.py` (`clause_chain_features`).
Tests: `tests/test_metric_spec.py`.

---

## 1. What counts as a detected splice

A **splice** is one occurrence of a non-terminal punctuation mark standing
immediately before a word that can begin a clause.

    _ANY_MARK = re.compile(r"--|[;,:—–]")
    MIN_CLAUSE_WORDS = 4

`splice_count(text, mark)` scans the **marks themselves**, and for each
occurrence of a character registered for `mark` takes the segment that follows,
up to the next mark or terminator, stripped of leading brackets and quotes. The
occurrence counts as a splice when **either**

1. the first word of that segment is in the closed set `CLAUSE_INITIAL`, **or**
2. the segment contains at least `MIN_CLAUSE_WORDS` (= 4) words.

Clause 2 is what separates a clause join from a list item: `a spring` is two
words, `the staple is pushed into the paper with force` is nine. It makes no
grammatical claim and needs no part-of-speech tagger.

### Supported marks

| mark | characters |
|---|---|
| `semicolon` | `;` |
| `colon` | `:` |
| `dash` | `—` (em), `–` (en), `--` (double hyphen) |
| `comma` | `,` |

The alternation places `--` first so a double hyphen is matched whole rather
than as two failed single-hyphen attempts.

### `CLAUSE_INITIAL` — a closed list, pronouns and connectives only

    this these those it they he she we you there then thus therefore
    however otherwise meanwhile instead consequently nevertheless
    afterwards subsequently

**Determiners are excluded from this list.** `The parts are a lever; a spring; a
base.` is a list, not a clause join, and `; a` cannot distinguish the two. The
list alone under-counted badly (see §6); the segment-length clause now recovers
determiner-initial joins without readmitting list items.

### What this measure explicitly does NOT claim

It does not decide whether both sides of the mark are independent clauses. That
is a grammatical judgement this study cannot make automatically, and no result
is stated as if it had been made.

---

## 2. Formulas

Let, for one response text:

* `S` = `splice_count(text, "semicolon")`
* `C` = `splice_count(text, "colon")`
* `D` = `splice_count(text, "dash")`
* `M` = `splice_count(text, "comma")`
* `T` = number of matches of `[.!?]` in the text (**terminal marks**)
* `Bd` = `S + C + D` (**boundary-capable** splices; the comma is excluded — see §5)

Then

    splice_share = S / (S + T)                  if S + T > 0 else NaN
    chain_share  = Bd / (Bd + T)                if Bd + T > 0 else NaN

`splice_share` is the **semicolon-specific** strategy measure.
`chain_share` is the **mark-agnostic** one.

Both are read as: *of the clause boundaries this text realises, what fraction
were realised by a non-terminal mark rather than by a sentence terminator?*

### Range and reference points

| text | splice_share | chain_share |
|---|---|---|
| `Rain falls. Rivers rise. Wind blows. Leaves turn.` | 0.000 | 0.000 |
| four sentences, one semicolon join in each | 0.500 | 0.500 |
| one sentence chaining five clauses with semicolons | 0.800 | 0.800 |

---

## 3. Edge cases and undefined behaviour

| case | behaviour |
|---|---|
| empty or whitespace-only text | `row_features` returns `{}`; the row carries no metric columns and is excluded from every metric mean |
| text with no terminal mark and no splice | denominator 0 → **NaN**, not 0 |
| text with splices and no terminal mark | share = 1.0 |
| text with terminal marks and no splice | share = 0.0 |
| `None` | `splice_count` returns 0; `row_features` returns `{}` |
| abbreviation full stops (`a.m.`, `Dr.`) | **counted as terminal marks.** `T` is a raw `[.!?]` count and does not use the sentence segmenter, so it over-counts terminals in abbreviation-bearing text and therefore **under**-states the share. Deliberate: it keeps the metric independent of the segmenter, whose repair was the subject of Round 4 |
| decimal points, ellipses | same — counted in `T`, biasing the share down |
| a mark inside a quotation or a URL | counted; no lexical filtering is applied |

---

## 4. Why these are independent of target success

The target outcome is `n_sentences != N`, computed by
`dci.verifiers.rules.split_sentences`.

`splice_share` and `chain_share` are computed from **punctuation character
counts only**. They never call the segmenter, never read `N`, never read the
target id, and never read a verdict. A text can score high on either and satisfy
any target, or score zero and fail any target.

This is not merely an argument from construction; both off-diagonal quadrants
are populated in the corpus:

| condition | share | target failure |
|---|---|---|
| E4b `X_COLON_TOTAL4` `o_A` | 0.673 | 0.875 |
| E4b `X_COLON_TOTAL4` `o_Q` | 0.218 | 0.175 |
| E4b `X_DASH_TOTAL4` | 0.249–0.384 | 0.300–0.475 |
| E4b `X_SEMICOLON_TOTAL2` | 0.303 | 0.225 |
| E4b `X_SEMICOLON_TOTAL4/6` | 0.708–0.835 | 0.975–1.000 |
| E4b `X_COMMA_TOTAL4`, `C_L3` | 0.000 | 0.000–0.050 |

and, decisively, **high share with target success** — E5a's semicolon arm under a
paragraph-count target, and every `q = 2` cell in R6-A, which reach 0.27–0.50
share at 0.21–0.35 failure.

**This makes the metric non-circular. It does not make it a validated causal
mediator.** No mediator-blocking intervention has succeeded (three instruments
have failed), so `chain_share` is used as *suggestive mechanism* evidence and
never as an identified mediator. See the evidence taxonomy in
`CLAIM_EVIDENCE_MATRIX.md`.

---

## 5. Why the comma is excluded from `chain_share`

A comma cannot stand where a sentence terminator stands in standard written
English; joining two independent clauses with one is an error. Including it
would put a mark that *cannot* substitute for a boundary into a measure of
boundary substitution.

`n_comma_splices` is still computed and reported separately, because a
comma-chained run-on is a real and distinct strategy (B produces it) and needs
to be visible as *something other than* the boundary-substitution strategy.

---

## 6. Change log

| date | change | effect |
|---|---|---|
| 2026-08-11 | first implementation, `_AFTER_MARK = [;,]` | colon and dash splice counts were **structurally 0 for every input** |
| 2026-08-11 | corrected to `(--\|[;,:—–])` | rescored all 20,184 stored generations: **1,279 rows (6.34%)** changed `chain_share`, max absolute change 0.923. **0** semicolon splice counts changed, so every result resting on `splice_share` is unaffected. No number computed with the buggy version was ever reported: the fix landed before any colon or dash splice figure was published. Full diff: `metric_bugdiff.py` |
| 2026-08-11 | frozen by this document and `tests/test_metric_spec.py` | — |
| 2026-08-11 | **segment-length clause added** after the Stage 0.3 human audit | The closed-list-only rule had **precision 18/18 but badly biased recall.** The worst case in the audit was a one-sentence answer carrying six semicolon joins that scored **0.000**, because its clauses began `the`, `once` and `(this` — and `; (this` did not match the old mark-plus-letter anchor at all. Recall therefore depended on the model's lexical style rather than on the structure being measured. Re-auditing the same 18 outputs under the revised rule: the two severe false negatives are repaired (0.000 → 0.857 and 0.000 → 0.167), every true negative stays at 0.000, and 11 of 18 rise. **No conclusion moved**: the `chain_share` ordering across arms is preserved and the separation widens (E4b: controls 0.000, `q=2` 0.30, dash 0.25–0.38, colon `o_A` 0.67 / `o_Q` 0.22, `q≥4` 0.71–0.84, against failures 0.00, 0.25, 0.30–0.48, 0.88/0.18, 0.98–1.00). |
