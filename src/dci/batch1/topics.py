"""The Batch 1 topic bank: new questions, a pilot/confirmatory split, and the
checks that keep the two apart and away from the historical DCI-1 bank.

``data/topics_source.json`` holds 576 questions, 48 in each of the twelve
historical subject areas, written for this study and never used by an
earlier DCI revision. The split is a pure function of the topic ids and a
fixed seed:

* within each area the topics are ordered by ``sha(seed, topic_id)``; the
  first ``pilot_topics / 12`` (8) go to the pilot and the rest (40) are the
  **reserved confirmatory bank**, which no Batch 1 code path reads;
* the 96 pilot topics are ordered the same way and dealt round-robin across
  areas; the first ``stage1_topics`` (32) are Stage 1, the next
  ``stage2_topics`` (64) Stage 2.

``overlap_report`` compares the bank with every historical DCI question bank
in the repository (``HISTORICAL_SOURCES``: DCI-1 v2, v3 and its candidate
list, v4, the v5-v7 calibration banks, and the v15/v19 task bank of
``src/dci``), the sequestered v3 and v4 hash manifests, and itself:

* exact matches after normalisation, and sequestered-hash matches, always
  block;
* a **screen** flags every pair whose word-set Jaccard is at least
  ``WORDSET_SCREEN``, whose stemmed content-word Jaccard is at least
  ``CONTENT_SCREEN``, or that shares at least ``RARE_STEM_MIN_SHARED``
  *rare* content stems (``RARE_STEM_MIN_LETTERS`` letters or more, in at
  most ``RARE_STEM_DF`` distinct questions of the bank and the history
  together: "popcorn" and "burst", "lightning" and "thunder"). The rare-stem
  rule was added after the re-audit (R1) found restatements the two Jaccard
  screens could not see. Lexical similarity is not proof of reuse, and
  reuse can hide behind low similarity, so every flagged pair needs a
  recorded review decision in ``data/topics_review.json`` (``kept_distinct``
  with a rationale, bound to both questions' text). A flagged pair without
  a decision keeps the report unclean. A question judged a re-use is
  rewritten under the same topic id, so the split does not move;
* the **semantic review** (``data/topics_semantic_review.json``) records a
  reading of every bank question against every historical question, for
  restatements that share no rare words at all. A finding marked
  RESTATEMENT whose question is still in the bank keeps the report
  unclean; the file's hash is bound.

``hygiene_report`` checks question form (one interrogative line ending in
``?``), instruction-like content (imperatives, format directives), library
target words (the focal word and every word a reference requires or
forbids, except *the*), and reports the characteristics of the Stage 1,
Stage 2 and reserved sets side by side.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import statistics
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from dci.batch1 import text as T
from dci.provenance.hashes import sha, sha_file

__all__ = ["Topic", "SOURCE_PATH", "REVIEW_PATH", "load_bank", "split_bank",
           "TopicSplit", "overlap_report", "hygiene_report", "assert_clean",
           "HISTORICAL_SOURCES", "SEQUESTERED_SOURCES", "WORDSET_SCREEN",
           "CONTENT_SCREEN", "RARE_STEM_DF", "RARE_STEM_MIN_SHARED",
           "RARE_STEM_MIN_LETTERS", "SEMANTIC_REVIEW_PATH", "SPLIT_SEED",
           "content_words", "load_semantic_review"]

_HERE = Path(__file__).resolve().parent
SOURCE_PATH = _HERE / "data" / "topics_source.json"
#: Topic bank v2 (revision 2026-10, R6): 144 fresh questions, 12 per area,
#: split into T1 (48, screening) and T2 (96, membership); no reserved part,
#: and screened against bank v1 (every one of its 576 questions) as well as
#: the historical banks. The reserved 480 of bank v1 are never read here.
SOURCE_PATH_V2 = _HERE / "data" / "topics_source_v2.json"
REVIEW_PATH_V2 = _HERE / "data" / "topics_review_v2.json"
SEMANTIC_REVIEW_PATH_V2 = _HERE / "data" / "topics_semantic_review_v2.json"
_REPO = _HERE.parents[2]

REVIEW_PATH = _HERE / "data" / "topics_review.json"

#: Every historical question bank in the repository: name -> (path, format).
#: ``records``: a JSON list of {topic_id, question}; ``by_area``: a JSON
#: object of area -> [question]; ``python_lists``: module-level lists named
#: ``*_TOPICS`` of string literals, read from the syntax tree (never run).
HISTORICAL_SOURCES = {
    "dci1/v2": (_REPO / "dci1/src/dci1/topics/data/topics.json", "records"),
    "dci1v3": (_REPO / "dci1/src/dci1v3/topics/data/topics_v3.json", "records"),
    "dci1v3/candidates": (_REPO / "dci1/tools/new_topics_v3.json", "by_area"),
    "dci1v4": (_REPO / "dci1/src/dci1v4/topics/data/topics_v4.json", "records"),
    "dci1v5/calibration_b": (
        _REPO / "dci1/src/dci1v5/topics/data/calibration_b_v5.json", "records"),
    "dci1v7/calibration_b_v6": (
        _REPO / "dci1/src/dci1v7/topics/data/calibration_b_v6.json", "records"),
    "dci/v19/task_bank": (
        _REPO / "src/dci/pipeline/stages/c142_constraints_and_tasks.py",
        "python_lists"),
}
#: Bank v2 is screened against every historical bank and against all 576
#: questions of bank v1 (the 96 pilot topics and the reserved 480 alike).
HISTORICAL_SOURCES_V2 = {**HISTORICAL_SOURCES,
                         "dci/batch1/bank_v1": (SOURCE_PATH, "batch1_bank")}
SEQUESTERED_SOURCES = {
    "dci1v3/sequestered": _REPO / "dci1/src/dci1v3/topics/data/sequestered_v3.json",
    "dci1v4/sequestered": _REPO / "dci1/src/dci1v4/topics/data/sequestered_v4.json",
}

WORDSET_SCREEN = 0.5
CONTENT_SCREEN = 0.3
RARE_STEM_DF = 6
RARE_STEM_MIN_SHARED = 2
RARE_STEM_MIN_LETTERS = 4
SEMANTIC_REVIEW_PATH = Path(__file__).resolve().parent / "data" / \
    "topics_semantic_review.json"
SPLIT_SEED = "dci.batch1:topic-split:v1:202610180"

_STOP = frozenset("""a an the of in on at to for from by with and or but is are
was were be been being do does did how why what which who whom whose when where
can could would should will shall may might must it its this that these those
as than then so such some any each every more most less few many much very not
no into out up down over under about between through during before after above
below there their they them your you we our i me my he she his her him us if
explain describe""".split())


def _stem(word: str) -> str:
    for suffix in ("ing", "ers", "er", "es", "ed", "ly", "s"):
        if len(word) > 4 and word.endswith(suffix):
            return word[:-len(suffix)]
    return word


def content_words(question: str) -> frozenset[str]:
    """Stemmed words outside a fixed stop list (the screen's second metric)."""
    return frozenset(_stem(w) for w in T.folded_words(question)
                     if w not in _STOP)


@dataclass(frozen=True)
class Topic:
    topic_id: str
    area: str
    question: str


def load_bank(path: Path = SOURCE_PATH) -> tuple[Topic, ...]:
    doc = json.loads(Path(path).read_text())
    topics = tuple(Topic(t["topic_id"], t["area"], t["question"])
                   for t in doc["topics"])
    ids = [t.topic_id for t in topics]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate topic ids in the bank")
    for t in topics:
        if not t.question.strip().endswith("?"):
            raise ValueError(f"{t.topic_id}: not a question")
    return topics


def _order(topic_id: str) -> str:
    return sha(["batch1/topic-order", SPLIT_SEED, topic_id])


@dataclass(frozen=True)
class TopicSplit:
    stage1: tuple[Topic, ...]
    stage2: tuple[Topic, ...]
    confirmatory: tuple[Topic, ...]
    bank_hash: str

    def manifest(self) -> dict[str, Any]:
        return {"schema": "dci.batch1/topic-split/v1", "seed": SPLIT_SEED,
                "bank_hash": self.bank_hash,
                "stage1": [t.topic_id for t in self.stage1],
                "stage2": [t.topic_id for t in self.stage2],
                "confirmatory_reserved": [t.topic_id for t in self.confirmatory],
                "counts": {"stage1": len(self.stage1),
                           "stage2": len(self.stage2),
                           "confirmatory_reserved": len(self.confirmatory)}}

    @property
    def split_hash(self) -> str:
        return sha(["batch1/topic-split", self.manifest()])

    def split_of(self, topic_id: str) -> str:
        for name, group in (("stage1", self.stage1), ("stage2", self.stage2),
                            ("confirmatory", self.confirmatory)):
            if any(t.topic_id == topic_id for t in group):
                return name
        raise KeyError(topic_id)


def split_for(cfg: Any) -> "TopicSplit":
    """The split a configuration names: bank v1 (stage 1, stage 2, the
    reserved confirmatory bank) or bank v2 (T1, T2, nothing reserved)."""
    if cfg.topic_bank == "v2":
        return split_bank(load_bank(SOURCE_PATH_V2),
                          pilot_topics=cfg.pilot_topics,
                          stage1_topics=cfg.stage1_topics, reserve=False)
    return split_bank(load_bank(), pilot_topics=cfg.pilot_topics,
                      stage1_topics=cfg.stage1_topics)


def split_bank(topics: Iterable[Topic], *, pilot_topics: int,
               stage1_topics: int, reserve: bool = True) -> TopicSplit:
    topics = tuple(topics)
    areas = sorted({t.area for t in topics})
    if pilot_topics % len(areas):
        raise ValueError(f"{pilot_topics} pilot topics do not divide over "
                         f"{len(areas)} areas")
    per_area = pilot_topics // len(areas)
    pilot_by_area: dict[str, list[Topic]] = {}
    confirmatory: list[Topic] = []
    for area in areas:
        ordered = sorted((t for t in topics if t.area == area),
                         key=lambda t: _order(t.topic_id))
        if reserve and len(ordered) <= per_area:
            raise ValueError(f"area {area!r} has no topics left to reserve")
        if len(ordered) < per_area:
            raise ValueError(f"area {area!r} has {len(ordered)} topics, fewer "
                             f"than {per_area}")
        pilot_by_area[area] = ordered[:per_area]
        confirmatory += ordered[per_area:]
    dealt: list[Topic] = []
    for i in range(per_area):
        dealt += [pilot_by_area[a][i] for a in areas]
    if stage1_topics > len(dealt):
        raise ValueError("more stage-1 topics than pilot topics")
    bank_hash = sha(["batch1/topic-bank",
                     sorted((t.topic_id, t.area, t.question) for t in topics)])
    split = TopicSplit(tuple(dealt[:stage1_topics]),
                       tuple(dealt[stage1_topics:]), tuple(confirmatory),
                       bank_hash)
    _assert_disjoint(split)
    return split


def _assert_disjoint(split: TopicSplit) -> None:
    groups = {"stage1": split.stage1, "stage2": split.stage2,
              "confirmatory": split.confirmatory}
    seen: dict[str, str] = {}
    for name, group in groups.items():
        for t in group:
            key = _normal(t.question)
            for probe in (t.topic_id, key):
                if probe in seen and seen[probe] != name:
                    raise ValueError(f"topic {t.topic_id} appears in both "
                                     f"{seen[probe]} and {name}")
                seen[probe] = name


def _normal(question: str) -> str:
    return " ".join(question.lower().split())


def _wordset(question: str) -> frozenset[str]:
    return frozenset(T.folded_words(question))


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def _read_source(name: str, path: Path, kind: str) -> list[dict[str, Any]]:
    if kind == "batch1_bank":
        return [{"source": name, "id": r["topic_id"], "question": r["question"]}
                for r in json.loads(path.read_text())["topics"]]
    if kind == "records":
        return [{"source": name, "id": r["topic_id"], "question": r["question"]}
                for r in json.loads(path.read_text())]
    if kind == "by_area":
        return [{"source": name, "id": f"{area}#{i}", "question": q}
                for area, qs in json.loads(path.read_text()).items()
                for i, q in enumerate(qs)]
    if kind == "python_lists":
        out = []
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
                    isinstance(node.targets[0], ast.Name) and \
                    node.targets[0].id.endswith("_TOPICS") and \
                    isinstance(node.value, ast.List):
                out += [{"source": name, "id": f"{node.targets[0].id}#{i}",
                         "question": e.value}
                        for i, e in enumerate(node.value.elts)
                        if isinstance(e, ast.Constant) and
                        isinstance(e.value, str)]
        return out
    raise ValueError(f"source format {kind!r}")


def _source_key(sources: Mapping[str, tuple[Path, str]] | None = None
                ) -> tuple:
    sources = HISTORICAL_SOURCES if sources is None else sources

    def stamp(path: Path):
        return (str(path), path.stat().st_mtime_ns if path.exists() else None)
    return (tuple((n, stamp(p), k) for n, (p, k) in sources.items()),
            tuple((n, stamp(p)) for n, p in SEQUESTERED_SOURCES.items()))


@lru_cache(maxsize=8)
def _historical_cached(key: tuple) -> tuple[tuple, frozenset, tuple]:
    released: list[dict[str, Any]] = []
    missing: list[str] = []
    for name, (path, _), kind in key[0]:
        if Path(path).exists():
            released += _read_source(name, Path(path), kind)
        else:
            missing.append(name)
    hashes: set[str] = set()
    for name, (path, _) in key[1]:
        if Path(path).exists():
            hashes |= {e["sha256"] for e in json.loads(Path(path).read_text())}
        else:
            missing.append(name)
    return tuple(released), frozenset(hashes), tuple(missing)


def _historical(sources: Mapping[str, tuple[Path, str]] | None = None
                ) -> tuple[list[dict[str, Any]], set[str], list[str]]:
    released, hashes, missing = _historical_cached(_source_key(sources))
    return [dict(r) for r in released], set(hashes), list(missing)


def _bank_paths(bank: str) -> tuple[Mapping[str, tuple[Path, str]], Path,
                                     Path, Path]:
    """bank -> (historical sources, review, semantic review, source file),
    read from the module's current paths (tests may substitute them)."""
    if bank == "v2":
        return (HISTORICAL_SOURCES_V2, REVIEW_PATH_V2, SEMANTIC_REVIEW_PATH_V2,
                SOURCE_PATH_V2)
    if bank == "v1":
        return HISTORICAL_SOURCES, REVIEW_PATH, SEMANTIC_REVIEW_PATH, SOURCE_PATH
    raise ValueError(f"topic bank {bank!r}")


def _question_hash(question: str) -> str:
    return hashlib.sha256(question.encode("utf-8")).hexdigest()


def load_review(path: Path | None = None) -> dict[tuple[str, str, str], dict]:
    """(topic_id, neighbour source, neighbour id) -> the review decision."""
    path = REVIEW_PATH if path is None else path
    if not path.exists():
        return {}
    doc = json.loads(path.read_text())
    return {(d["topic_id"], d["neighbour_source"], d["neighbour_id"]): d
            for d in doc["kept_distinct"]}


def _screen(a: str, b: str) -> tuple[float, float]:
    return (_jaccard(_wordset(a), _wordset(b)),
            _jaccard(content_words(a), content_words(b)))


def _flagged(wordset: float, content: float, rare: Iterable[str] = ()) -> bool:
    return (wordset >= WORDSET_SCREEN or content >= CONTENT_SCREEN
            or len(tuple(rare)) >= RARE_STEM_MIN_SHARED)


def _document_frequency(questions: Iterable[str]) -> dict[str, int]:
    """Per stem, the number of distinct questions (normalised) using it."""
    df: dict[str, int] = {}
    for q in {_normal(q): q for q in questions}.values():
        for w in content_words(q):
            df[w] = df.get(w, 0) + 1
    return df


def load_semantic_review(path: Path | None = None) -> dict[str, Any]:
    path = SEMANTIC_REVIEW_PATH if path is None else path
    if not path.exists():
        return {"findings": []}
    return json.loads(path.read_text())


def _stamp(path: Path) -> tuple:
    return (str(path), path.stat().st_mtime_ns if path.exists() else None)


def overlap_report(topics: Iterable[Topic], *, bank: str = "v1"
                   ) -> dict[str, Any]:
    sources, review, semantic, _ = _bank_paths(bank)
    return json.loads(_overlap_cached(tuple(topics), _source_key(sources),
                                      (_stamp(review), _stamp(semantic)),
                                      bank))


@lru_cache(maxsize=8)
def _overlap_cached(topics: tuple[Topic, ...], source_key: tuple,
                    review_key: tuple, bank: str = "v1") -> str:
    sources, review_path, semantic_path, source_path = _bank_paths(bank)
    released, hashes, missing = _historical(sources)
    review = load_review(review_path)
    hist_text = {_normal(r["question"]): r for r in released}
    df = _document_frequency([t.question for t in topics]
                             + [r["question"] for r in released])

    def rare(stems: frozenset[str]) -> frozenset[str]:
        return frozenset(w for w in stems if len(w) >= RARE_STEM_MIN_LETTERS
                         and df.get(w, 0) <= RARE_STEM_DF)

    hist_sets = [(_wordset(r["question"]), content_words(r["question"]),
                  rare(content_words(r["question"])), r) for r in released]
    exact, sequestered, flagged = [], [], []
    max_hist = (0.0, None, None)
    for t in topics:
        if _normal(t.question) in hist_text:
            exact.append(t.topic_id)
        if _question_hash(t.question) in hashes:
            sequestered.append(t.topic_id)
        ws, cs = _wordset(t.question), content_words(t.question)
        rs = rare(cs)
        for hws, hcs, hrs, r in hist_sets:
            wj, cj = _jaccard(ws, hws), _jaccard(cs, hcs)
            shared = sorted(rs & hrs)
            score = max(wj, cj)
            if score > max_hist[0]:
                max_hist = (score, t.topic_id, f"{r['source']}:{r['id']}")
            if _flagged(wj, cj, shared):
                flagged.append(_pair(t, r["source"], r["id"], r["question"],
                                     wj, cj, review, shared))
    internal = []
    max_new = (0.0, None, None)
    sets = [(_wordset(t.question), content_words(t.question),
             rare(content_words(t.question)), t) for t in topics]
    for i, (wa, ca, ra, ta) in enumerate(sets):
        for wb, cb, rb, tb in sets[i + 1:]:
            wj, cj = _jaccard(wa, wb), _jaccard(ca, cb)
            shared = sorted(ra & rb)
            score = max(wj, cj)
            if score > max_new[0]:
                max_new = (score, ta.topic_id, tb.topic_id)
            if _flagged(wj, cj, shared):
                internal.append(_pair(ta, "batch1", tb.topic_id, tb.question,
                                      wj, cj, review, shared))
    unreviewed = [p for p in flagged + internal if not p["reviewed"]]
    semantic = load_semantic_review(semantic_path)
    current = {t.topic_id: _question_hash(t.question) for t in topics}
    open_semantic = sorted(
        f["topic_id"] for f in semantic.get("findings", [])
        if f.get("verdict") == "RESTATEMENT"
        and current.get(f["topic_id"]) == f.get("question_sha256"))
    clean = not (exact or sequestered or unreviewed or missing
                 or open_semantic)
    return json.dumps({
        "schema": "dci.batch1/topic-overlap/v3", "clean": clean,
        "n_topics": len(topics), "historical_released": len(released),
        "historical_sources": sorted(sources),
        "historical_sequestered_hashes": len(hashes),
        "historical_sources_missing": missing,
        "screen": {"wordset_jaccard": WORDSET_SCREEN,
                   "content_jaccard": CONTENT_SCREEN,
                   "rare_stems": {"max_document_frequency": RARE_STEM_DF,
                                  "min_shared": RARE_STEM_MIN_SHARED,
                                  "min_letters": RARE_STEM_MIN_LETTERS}},
        "semantic_review": {
            "file_hash": sha_file(semantic_path)
            if semantic_path.exists() else None,
            "findings": len(semantic.get("findings", [])),
            "restatements_still_in_bank": open_semantic},
        "exact_matches": exact, "sequestered_matches": sequestered,
        "flagged_historical": flagged, "flagged_internal": internal,
        "unreviewed": [f"{p['topic_id']}~{p['neighbour_source']}:"
                       f"{p['neighbour_id']}" for p in unreviewed],
        "max_jaccard_historical": {"value": round(max_hist[0], 4),
                                   "topic": max_hist[1],
                                   "historical": max_hist[2]},
        "max_jaccard_internal": {"value": round(max_new[0], 4),
                                 "a": max_new[1], "b": max_new[2]},
        "review_file_hash": sha_file(review_path)
        if review_path.exists() else None,
        "source_file_hash": sha_file(source_path)
        if source_path.exists() else None}, sort_keys=True)


def _pair(t: Topic, source: str, nid: str, question: str, wj: float,
          cj: float, review: Mapping, rare: Iterable[str] = ()
          ) -> dict[str, Any]:
    decision = review.get((t.topic_id, source, nid))
    reviewed = bool(decision) and \
        decision.get("question_sha256") == _question_hash(t.question) and \
        decision.get("neighbour_sha256") == _question_hash(question) and \
        bool(decision.get("rationale"))
    return {"topic_id": t.topic_id, "question": t.question,
            "neighbour_source": source, "neighbour_id": nid,
            "neighbour": question, "wordset_jaccard": round(wj, 4),
            "content_jaccard": round(cj, 4), "rare_shared": list(rare),
            "reviewed": reviewed,
            "decision": decision.get("rationale") if reviewed else None}


# ----------------------------------------------------------------- hygiene

_INTERROGATIVE = ("why", "how", "what", "when", "where", "which", "who", "is",
                  "are", "do", "does", "can", "could", "should", "would", "in")
_IMPERATIVE = re.compile(r"^\s*(explain|describe|list|write|answer|give|name|"
                         r"tell|summari[sz]e|discuss|compare|outline|use)\b",
                         re.IGNORECASE)
_DIRECTIVE = re.compile(
    r"(\bin \d+\b|\b\d+ (words|sentences|paragraphs|lines)\b|"
    r"\banswer in\b|\brespond (in|with)\b|\bin one sentence\b|\bbullet|\bexactly\b|"
    r"\bat most\b|\bat least\b|\bdo not use\b|\bonly words\b|\n|\d\.)",
    re.IGNORECASE)


def _library_words() -> set[str]:
    from dci.batch1 import library as L
    words = {L.FOCAL_WORD}
    for c in L.reference_library():
        words |= set(c.required_words()) | set(c.p.get("words", ()))
        if "word" in c.p:
            words.add(c.p["word"])
    return words - {"the"}


def _profile(group: Iterable[Topic]) -> dict[str, Any]:
    group = tuple(group)
    if not group:
        return {"n": 0}
    longest = [T.max_word_letters(t.question) for t in group]
    lengths = [T.word_count(t.question) for t in group]
    areas: dict[str, int] = {}
    for t in group:
        areas[t.area] = areas.get(t.area, 0) + 1
    def share(pred):
        return round(sum(1 for t in group if pred(t)) / len(group), 4)
    return {"n": len(group), "areas": dict(sorted(areas.items())),
            "mean_words": round(statistics.mean(lengths), 3),
            "mean_longest_word": round(statistics.mean(longest), 3),
            "share_longest_ge_9": share(lambda t: T.max_word_letters(t.question) >= 9),
            "share_longest_ge_11": share(lambda t: T.max_word_letters(t.question) >= 11),
            "share_longest_ge_13": share(lambda t: T.max_word_letters(t.question) >= 13),
            "share_with_letter_b": share(lambda t: "b" in t.question.lower()),
            "share_with_letter_z": share(lambda t: "z" in t.question.lower()),
            "share_why": share(lambda t: t.question.lower().startswith("why")),
            "share_how": share(lambda t: t.question.lower().startswith("how"))}


def hygiene_report(topics: Iterable[Topic], split: "TopicSplit") -> dict[str, Any]:
    topics = tuple(topics)
    words = _library_words()
    form, commands, leaks = [], [], []
    for t in topics:
        q = t.question
        first = (T.folded_words(q) or [""])[0]
        if "\n" in q or not q.strip().endswith("?") or \
                first not in _INTERROGATIVE:
            form.append(t.topic_id)
        if _IMPERATIVE.match(q) or _DIRECTIVE.search(q):
            commands.append(t.topic_id)
        found = sorted(set(T.folded_words(q)) & words)
        if found:
            leaks.append({"topic_id": t.topic_id, "words": found})
    clean = not (form or commands or leaks)
    return {"schema": "dci.batch1/topic-hygiene/v1", "clean": clean,
            "not_a_single_interrogative_line": form,
            "instruction_like": commands, "library_word_leaks": leaks,
            "library_words_checked": sorted(words),
            "profiles": {"stage1": _profile(split.stage1),
                         "stage2": _profile(split.stage2),
                         "confirmatory_reserved": _profile(split.confirmatory)}}


def assert_clean(report: dict[str, Any]) -> None:
    if not report["clean"]:
        raise ValueError("the topic bank overlaps a historical bank or "
                         "itself without a review decision, or a historical "
                         "source is missing: "
                         f"{ {k: report[k] for k in ('exact_matches', 'sequestered_matches', 'unreviewed', 'historical_sources_missing')} } "
                         f"semantic: {report['semantic_review']['restatements_still_in_bank']}")
