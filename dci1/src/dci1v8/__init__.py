"""DCI-1 v8: the prospective instrument layer, and nothing else yet.

Only ``dci1v8.verifiers`` exists. It carries one registered change against
v7: **A and the eight Tier-1 marker families are counted by one shared
function**, ``verifiers.words.count_marker(text, marker)``, under §9.2's
lexical rule (segment the response as written, fold each word, compare). v7
counted A with ``dci1v4.verifiers.target.s0_count`` (fold the whole response,
then segment) and the markers with the lexical rule; the two disagree on
exactly one code point, U+0130 ``İ``, when it is adjacent to the marker inside
one alphabetic run.

There is no v8 preregistration, no v8 stage, no v8 seed domain and no v8
evidence tree. Nothing in this package reads or writes an evidence tree, and
no v7 module imports it. The change is prospective: v7's rows keep v7's
verdicts under v7's verifier hash, and ``dci1/reports/dci1v8/`` records what
the unified rule would have said about every stored response.
"""
