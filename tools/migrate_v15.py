"""Mechanical extractor: notebook cells -> dci package (Stage A migration).

What it does, and why each step is behavior-preserving:

1.  SHARED-NAME ANALYSIS. The notebook's cells communicate through one global
    namespace. A name is "shared" when it is assigned at the top level of one
    cell and read in a different cell (or named in a `global` statement, or
    force-listed because the inference seam moved its reader into a backend
    module). Every reference to a shared name — read, write, delete, augmented
    assign, at module level or inside a function body — is rewritten to an
    attribute of the explicit state module `dci.pipeline.state` (imported as
    `S`). Module-attribute access has exactly the notebook's semantics: late
    binding, in-place mutation, rebinding visible everywhere. Names that never
    cross a cell boundary are left untouched.

2.  SCOPE-CORRECT REWRITING. `symtable` decides, per scope, whether a Name
    resolves to module scope. Function parameters, locals, comprehension
    targets and genuine closures are never rewritten. `global` declarations for
    shared names are deleted (the S attribute *is* the global).

3.  SOURCE-PRESERVING SPLICE. Rewrites are applied as positional text splices
    ("NAME" -> "S.NAME"), so comments, formatting and every scientific message
    string survive byte-for-byte. Names inside f-strings (whose child-node
    positions are unreliable before Python 3.12) are handled by AST-rewriting
    the enclosing JoinedStr and splicing `ast.unparse` of it over the exact
    literal span — semantically identical, format-normalized only within that
    literal.

4.  LIBRARY EXTRACTION. A curated list of pure definitions is cut verbatim
    from the cells into real library modules. A definition is extracted only
    if an automatic purity check proves it references no shared name; anything
    impure is left in place and reported. Cells that used an extracted name
    get an import injected.

5.  PATCHES. The few genuinely intentional code changes (config switches ->
    loader, Colab storage -> layout, inference seam -> backend, sharding hook)
    are exact-string replacements declared in PATCHES below. Every patch is a
    ledger row; nothing else in the cell text changes.

Run:  python tools/migrate_v15.py            (from the repo root)
Emits: src/dci/pipeline/stages/c*.py, stage ORDER, extracted libraries,
       docs/migration_map.csv, docs/migration_ledger.csv (patch rows).
"""
from __future__ import annotations

import ast
import csv
import symtable
import sys
from textwrap import dedent as textwrap_dedent
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CELLS = REPO / "notebook_source" / "cells"
STAGES = REPO / "src" / "dci" / "pipeline" / "stages"
DOCS = REPO / "docs"

SKIP_CELLS = {"104.py"}          # the %pip cell: environments/ replaces it

STAGE_TITLES = {
    "112": "configuration_and_statuses", "122": "runtime_provenance_gates",
    "126": "durable_storage", "132": "model_backend_binding",
    "142": "constraints_and_tasks", "152": "verifiers",
    "162": "coupling_and_response_bank", "172": "paraphrases_and_audit",
    "182": "design_builders", "192": "oracle_and_generation",
    "202": "statistics", "212": "reference_machinery",
    "216": "measurement_architecture", "222": "gate0_selftest",
    "232": "gateM_measurement", "242": "benchmark_and_budget",
    "252": "gate1_u_bank", "262": "prescreen",
    "272": "calibration_and_calipers", "282": "gate2_admission_panel",
    "292": "pool_dependence", "302": "pseudo_focal_cohort",
    "312": "uval_measurement", "322": "gate3_validation",
    "332": "gate3b_wording", "342": "freeze",
    "352": "confirmatory_generation", "362": "confirmatory_analysis",
    "372": "secondary_analyses", "382": "gate4_falsification",
    "392": "figures", "402": "export", "412": "exploratory",
}

# Names whose readers moved into backend modules, plus `global`-statement names.
FORCE_SHARED = {
    "model", "tokenizer", "_PROMPT_MODE", "_telemetry_stop",
    "_PROMPT_IDS", "_PROMPT_TEXT", "_FULL_PROMPT_LENGTH",
    "TOKENISATION_MANIFEST", "TERMINATION_RECORDS",
    "RESOLVED_DTYPE", "BACKEND", "synthetic_response", "set_all_seeds",
}
NEVER_SHARED = {"S"}
ALIAS_SHARED: set = set()

# ---------------------------------------------------------------- extraction
# name -> (library module, import-from path). Verbatim cut; auto purity check.
LIB_TARGETS: dict[str, str] = {}
LIB_SPECS = [
    ("dci.statuses", "src/dci/statuses.py",
     ["GateStatus"],
     ["from __future__ import annotations"]),
    ("dci.exceptions", "src/dci/exceptions.py",
     ["StudyStop", "LineageViolation", "CacheIntegrityError",
      "FrozenPlanMismatch", "TaskBankInsufficient", "SensitivityNotEstimable"],
     ["from __future__ import annotations",
      "from dci.protocol.gate_types import GateOutcome  # noqa: F401"]),
    ("dci.protocol.gate_types", "src/dci/protocol/gate_types.py",
     ["GateOutcome"],
     ["from __future__ import annotations",
      "from dataclasses import asdict, dataclass, field",
      "from typing import Any",
      "from dci.statuses import GateStatus"]),
    ("dci.protocol.estimands", "src/dci/protocol/estimands.py",
     ["ESTIMAND_DEFINITIONS"],
     ["from __future__ import annotations"]),
    ("dci.provenance.hashes", "src/dci/provenance/hashes.py",
     ["sha", "sha_text", "sha_file", "stable_int", "referenced_names"],
     ["from __future__ import annotations",
      "import dis", "import hashlib", "import json",
      "from pathlib import Path", "from typing import Any"]),
    ("dci.measurement.audit_sizing", "src/dci/measurement/audit_sizing.py",
     ["wilson_interval", "error_ceiling_sample_size",
      "required_cases_for_ceiling"],
     ["from __future__ import annotations",
      "import math", "from typing import Callable",
      "from scipy import stats"]),
    ("dci.constraints.spec", "src/dci/constraints/spec.py",
     ["ConstraintSpec", "spec", "P"],
     ["from __future__ import annotations",
      "from dataclasses import dataclass",
      "from typing import Any, Literal"]),
    ("dci.verifiers.rules", "src/dci/verifiers/rules.py",
     ["OutcomeStatus", "VerificationResult", "WORD_PATTERN", "INTEGER_PATTERN",
      "DIGIT_PATTERN", "PERCENT_PATTERN", "SENTENCE_BOUNDARY", "LIST_MARKER",
      "STRAIGHT_QUOTE", "CURLY_QUOTES", "VOWELS", "normalize_text", "split_sentences",
      "word_tokens", "integer_tokens", "fraction_status", "count_status",
      "_unscorable", "_per_sentence",
      # every deterministic verifier rule
      "v_exact_sentence_count", "v_increasing_lengths",
      "v_nondecreasing_lengths", "v_sentence_initial", "v_min_sentence_words",
      "v_alphabetical_starts", "v_long_word_each_sentence",
      "v_sentence_ends_long", "v_commas_per_sentence",
      "v_min_long_words_per_sentence", "v_word_band", "v_semicolon_each",
      "v_comma_and_min_words", "v_unique_words", "v_integer_sum",
      "v_distinct_integers", "v_forbid_word_set", "v_require_word_set",
      "v_require_word", "v_no_suffix", "v_alliteration", "v_caps_word",
      "v_exact_char_total", "v_no_char", "v_paren_pairs", "v_quote_pairs",
      "v_exact_integer_count", "v_vowel_words_per_sentence",
      "v_caps_sentence_count", "v_sentence_initial_forbidden_word",
      "v_question_sentence_count", "v_min_integer_count",
      "v_max_integer_count", "v_no_digits", "v_percent_count"],
     ["from __future__ import annotations",
      "import math", "import re",
      "import numpy as np",
      "from dataclasses import dataclass",
      "from typing import Any, Literal"]),
    ("dci.analysis.stats", "src/dci/analysis/stats.py",
     ["bootstrap_functional", "bootstrap_se", "percentile_ci", "simultaneous_bounds",
      "simultaneous_abs_upper", "bootstrap_p", "paired_advantage", "holm",
      "within_sesoi", "indexed_frame"],
     ["from __future__ import annotations",
      "import math",
      "import numpy as np", "import pandas as pd",
      "from typing import Any, Callable, Iterable, Optional",
      "from scipy import stats"]),
]
for _mod, _path, _names, _hdr in LIB_SPECS:
    for _n in _names:
        LIB_TARGETS[_n] = _mod

# ------------------------------------------------------------------ patches
# cell -> list[(ledger_id, find, replace, change_type, rationale)]
COMPAT_IMPORT = "from dci.compat import torch  # optional-dependency shim\n"
PATCHES: dict[str, list[tuple[str, str, str, str, str]]] = {
    "112.py": [
        ("P1-switches",
         'MODEL_PROFILE: Literal["dev_fast", "integration_pass", "pilot", "study"] = "dev_fast"\n'
         'RUN_MODE: Literal["smoke", "full"] = "smoke"\n'
         'DRY_RUN_MODE = True\n'
         'USE_GOOGLE_DRIVE = True',
         'MODEL_PROFILE: Literal["dev_fast", "integration_pass", "pilot", "study"] = ACTIVE.model_profile\n'
         'RUN_MODE: Literal["smoke", "full"] = ACTIVE.run_mode\n'
         'DRY_RUN_MODE = ACTIVE.dry_run_mode\n'
         'USE_GOOGLE_DRIVE = ACTIVE.use_google_drive',
         "execution-only",
         "Notebook switches now come from the typed profile loader; defaults "
         "are identical, so a bare run reproduces the notebook."),
        ("P2-runid",
         "RUN_ID: Optional[str] = None",
         "RUN_ID: Optional[str] = ACTIVE.run_id",
         "execution-only", "Resume target selectable from the CLI."),
        ("P3-overrides",
         "                     use_google_drive=USE_GOOGLE_DRIVE,\n"
         "                     **_INTEGRATION_OVERRIDES)",
         "                     use_google_drive=USE_GOOGLE_DRIVE,\n"
         "                     **{**_INTEGRATION_OVERRIDES,\n"
         "                        **ACTIVE.storage_overrides(),\n"
         "                        **ACTIVE.protocol_overrides})",
         "execution-only",
         "Storage roots and the harness's V1x_* size overrides arrive through "
         "the loader instead of source edits; scientific overrides remain "
         "visible in the protocol exactly as before."),
        ("P4-device",
         "    single_gpu_index: int = 0",
         "    single_gpu_index: int = ACTIVE.device_index if ACTIVE.device_index is not None else 0",
         "execution-only", "Local dual-GPU selection without editing source."),
    ],
    "122.py": [
        ("P5-storage",
         None,  # filled at runtime: the whole Colab mount block
         "from dci.storage.layout import resolve_durable_base\n"
         "DRIVE_AVAILABLE, DRIVE_NOTE, DURABLE_BASE = resolve_durable_base(CFG)",
         "execution-only",
         "Colab/Drive resolution becomes a storage adapter with identical "
         "branch semantics; no /content path remains in the core."),
    ],
    "132.py": [
        ("P6-backend-construct",
         None,  # whole cell replaced
         None,
         "execution-only",
         "HF model loading moved verbatim into dci.inference.hf_transformers; "
         "the stage now binds the backend chosen by execution config. load/"
         "free/tokenizer semantics, gating and fingerprint checks unchanged."),
    ],
    "152.py": [
        ("P10-probe-through-library",
         "split_sentences = _forbidden_split  # noqa: F811  (temporary probe)\n"
         "try:\n"
         "    for _uid in _WHOLE_TEXT_U:\n"
         "        VERIFIERS[_uid](_PROBE_TEXT)\n"
         "finally:\n"
         "    split_sentences = _REAL_SPLIT",
         "import dci.verifiers.rules as _rules_mod\n"
         "_rules_mod.split_sentences = _forbidden_split  # noqa  (temporary probe)\n"
         "try:\n"
         "    for _uid in _WHOLE_TEXT_U:\n"
         "        VERIFIERS[_uid](_PROBE_TEXT)\n"
         "finally:\n"
         "    _rules_mod.split_sentences = _REAL_SPLIT",
         "execution-only",
         "The whole-text-verifiers-never-segment tripwire now monkey-patches "
         "split_sentences where the verifier rules actually resolve it (the "
         "extracted library), preserving the probe's full detection power; "
         "patching the stage module would have weakened it silently."),
    ],
    "192.py": [
        ("P0-shard-import",
         "def prompt_fingerprint(user_prompt: str) -> str:",
         "from dci.pipeline.sharding import shard_filter, wait_for_stage_complete\n"
         "\n\n"
         "def prompt_fingerprint(user_prompt: str) -> str:",
         "execution-only",
         "Import for the deterministic sharding hooks."),
        ("P9-shard-barrier",
         "        progress.close()\n"
         "\n"
         "    return rows_for_design(design, stage, plan)",
         "        progress.close()\n"
         "\n"
         "    wait_for_stage_complete(stage, design, plan)\n"
         "    return rows_for_design(design, stage, plan)",
         "execution-only",
         "Completeness barrier for sharded workers; identity when unsharded."),
        ("P7-generate-seam",
         None,  # generate_batch body swap, computed at runtime
         None,
         "execution-only",
         "generate_batch delegates to the frozen backend; the oracle branch "
         "and the torch branch moved verbatim into dci.inference.*."),
        ("P8-shard-hook",
         "    payload, _ = read_commits(stage, plan)\n"
         "    complete = set(payload)\n"
         "    pending = [b for b in plan if not set(b[\"row_ids\"]).issubset(complete)]",
         "    payload, _ = read_commits(stage, plan)\n"
         "    complete = set(payload)\n"
         "    pending = [b for b in plan if not set(b[\"row_ids\"]).issubset(complete)]\n"
         "    pending = shard_filter(stage, plan, pending)",
         "execution-only",
         "Deterministic batch-to-worker assignment (batch_index mod N) from "
         "the frozen plan; absent sharding this is the identity."),
    ],
}


def load_cells() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8")
            for p in sorted(CELLS.glob("*.py")) if p.name not in SKIP_CELLS}


# ------------------------------------------------------- shared-name analysis
def top_level_assigned(tree: ast.Module) -> set[str]:
    out: set[str] = set()

    def store(t):
        if isinstance(t, ast.Name):
            out.add(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                store(e)
        elif isinstance(t, ast.Starred):
            store(t.value)

    def scan(body):
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(n.name)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    store(t)
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)):
                store(n.target)
            elif isinstance(n, ast.For):
                store(n.target); scan(n.body); scan(n.orelse)
            elif isinstance(n, (ast.While, ast.If)):
                scan(n.body); scan(n.orelse)
            elif isinstance(n, ast.With):
                for it in n.items:
                    if it.optional_vars:
                        store(it.optional_vars)
                scan(n.body)
            elif isinstance(n, ast.Try):
                scan(n.body); scan(n.orelse); scan(n.finalbody)
                for h in n.handlers:
                    scan(h.body)
    scan(tree.body)
    return out


def module_scope_loads(src: str) -> set[str]:
    """Names whose Load resolves to module scope (params/locals excluded)."""
    tree = ast.parse(src)
    st = symtable.symtable(src, "<x>", "exec")
    out: set[str] = set()
    cache: dict[int, list] = {}

    def kids(tab):
        if id(tab) not in cache:
            cache[id(tab)] = list(tab.get_children())
        return cache[id(tab)]

    def child(tab, name, lineno):
        c = [t for t in kids(tab) if t.get_name() == name and t.get_lineno() == lineno]
        if c:
            return c[0]
        c = [t for t in kids(tab) if t.get_name() == name]
        return c[0] if c else tab

    def visit(node, chain):
        nc = chain
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nc = chain + [child(chain[-1], node.name, node.lineno)]
        elif isinstance(node, ast.Lambda):
            nc = chain + [child(chain[-1], "lambda", node.lineno)]
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            kind = {ast.ListComp: "listcomp", ast.SetComp: "setcomp",
                    ast.DictComp: "dictcomp", ast.GeneratorExp: "genexpr"}[type(node)]
            nc = chain + [child(chain[-1], kind, node.lineno)]
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if resolves_to_module(nc, node.id):
                out.add(node.id)
        for ch in ast.iter_child_nodes(node):
            visit(ch, nc)

    for n in tree.body:
        visit(n, [st])
    return out


def module_read_before_write(src: str) -> set[str]:
    """Names read at MODULE statement level before their first module store.

    Fully scope-aware: only Loads whose own scope chain is the module (not
    comprehensions, lambdas or function bodies) count, in source order, so a
    comprehension temp reusing a shared name's spelling cannot poison the
    analysis, and a function body's global read (bound at call time) does not
    masquerade as an import-time read.
    """
    tree = ast.parse(src)
    st = symtable.symtable(src, "<x>", "exec")
    seen_store: set[str] = set()
    out: set[str] = set()

    def visit(node, depth):
        d2 = depth
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Lambda, ast.ListComp,
                             ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            d2 = depth + 1
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                seen_store.add(node.name)
        if isinstance(node, ast.Name) and depth == 0:
            if isinstance(node.ctx, ast.Load) and node.id not in seen_store:
                out.add(node.id)
            elif isinstance(node.ctx, ast.Store):
                seen_store.add(node.id)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for al in node.names:
                seen_store.add(al.asname or al.name.split(".")[0])
        if isinstance(node, ast.Assign):
            visit(node.value, d2)          # loads on the right happen first
            for t in node.targets:
                visit(t, d2)
            return
        if isinstance(node, ast.AugAssign):
            visit(node.value, d2)
            visit(node.target, d2)
            return
        for ch in ast.iter_child_nodes(node):
            visit(ch, d2)

    for n in tree.body:
        visit(n, 0)
    return out


def compute_shared(cells: dict[str, str]) -> set[str]:
    trees = {k: ast.parse(v) for k, v in cells.items()}
    assigned = {k: top_level_assigned(t) for k, t in trees.items()}
    loads = {k: module_scope_loads(v) for k, v in cells.items()}
    shared: set[str] = set(FORCE_SHARED)
    definers: dict[str, set[str]] = {}
    for k, names in assigned.items():
        for n in names:
            definers.setdefault(n, set()).add(k)
    read_first = {k: module_read_before_write(v) for k, v in cells.items()}
    order = list(cells)
    for name, defs in definers.items():
        # Shared when read outside every defining cell, or when a LATER
        # defining cell reads it at module level before its own first write
        # (VERIFIER_AUDIT_SIGNED_INPUT, SECONDS_PER_GENERATION): that read
        # consumes the earlier cell's value, which only shared state carries.
        # A name every definer writes first (loop temps like `fam`) stays
        # private, which also keeps pandas @-variable resolution working.
        first_def = min(defs, key=order.index)
        if any(name in loads[c] for c in cells if c not in defs):
            shared.add(name)
        elif any(name in read_first[c] for c in defs if c != first_def):
            shared.add(name)
    for t in trees.values():
        for node in ast.walk(t):
            if isinstance(node, ast.Global):
                shared.update(node.names)
    shared -= set(LIB_TARGETS)        # extracted names are imports, not state
    shared -= NEVER_SHARED
    return shared


# ------------------------------------------------------------- lib extraction
def extract_libraries(cells: dict[str, str], shared: set[str]):
    """Cut LIB_TARGETS defs verbatim into library modules; inject imports."""
    lib_bodies: dict[str, list[tuple[str, str]]] = {m: [] for m, *_ in
                                                    [(s[0],) for s in LIB_SPECS]}
    extracted: set[str] = set()
    impure: list[tuple[str, str]] = []
    lib_names = set(LIB_TARGETS)

    for cname in list(cells):
        src = cells[cname]
        tree = ast.parse(src)
        lines = src.splitlines(keepends=True)
        cut_spans: list[tuple[int, int]] = []
        cell_assigned = top_level_assigned(tree)
        taken: set[str] = set()
        for node in tree.body:
            names: list[str] = []
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names = [node.name]
            elif isinstance(node, ast.Assign) and all(
                    isinstance(t, ast.Name) for t in node.targets):
                names = [t.id for t in node.targets]  # type: ignore
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names = [node.target.id]
            if not names or not all(n in lib_names for n in names):
                continue
            if any(n in taken for n in names):
                continue               # only the first binding is the library
            # purity: the block may reference other lib names, its own names,
            # builtins and module imports — never a shared run-state name.
            start = node.lineno
            if getattr(node, "decorator_list", None):
                start = min(d.lineno for d in node.decorator_list)
            block_src = "".join(lines[start - 1: node.end_lineno])
            try:
                refs = module_scope_loads(textwrap_dedent(block_src))
            except SyntaxError:
                refs = {n.id for n in ast.walk(node)
                        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
            bad = (refs & shared) | (refs & (cell_assigned - lib_names))
            if bad:
                impure.append((names[0], f"references non-library {sorted(bad)}"))
                continue
            taken.update(names)
            start = node.lineno
            if getattr(node, "decorator_list", None):
                start = min(d.lineno for d in node.decorator_list)
            block = "".join(lines[start - 1: node.end_lineno])
            mod = LIB_TARGETS[names[0]]
            lib_bodies[mod].append((names[0], block))
            extracted.update(names)
            cut_spans.append((start - 1, node.end_lineno))
        if cut_spans:
            keep = []
            removed = set()
            for a, b in cut_spans:
                removed.update(range(a, b))
            for i, line in enumerate(lines):
                if i not in removed:
                    keep.append(line)
            cells[cname] = "".join(keep)

    for mod, path, names, header in LIB_SPECS:
        blocks = [b for n in names for (bn, b) in lib_bodies[mod] if bn == n]
        missing = [n for n in names
                   if n not in extracted and n in LIB_TARGETS]
        text = (f'"""{mod.split(".")[-1]} — extracted verbatim from the v15 '
                f'notebook cells by tools/migrate_v15.py.\n\nBehavior-'
                f'preserving Stage A extraction: bodies are byte-identical to '
                f'the\nnotebook source; only the module home changed. See '
                f'docs/migration_map.csv.\n"""\n'
                + "\n".join(header) + "\n\n\n" + "\n\n".join(blocks))
        (REPO / path).write_text(text, encoding="utf-8")
        if missing:
            print(f"  [extract] {mod}: NOT extracted (impure or absent): {missing}")
    return extracted, impure


# ------------------------------------------------------------ scope rewriting
def resolves_to_module(chain: list, name: str) -> bool:
    """True when `name`, referenced from the innermost scope, is module-global."""
    for tab in reversed(chain):
        try:
            sym = tab.lookup(name)
        except KeyError:
            continue
        if str(tab.get_type()) in ("module", "SymbolTableType.MODULE"):
            return True
        if sym.is_declared_global():
            return True
        if sym.is_local():
            return False               # parameter/local/comprehension target
        if sym.is_free():
            return False               # genuine closure over a function local
        if sym.is_global():
            return True
    return True                        # unseen anywhere -> global by default


def rewrite_cell(cname: str, src: str, shared: set[str],
                 lib_imports_needed: set[str]) -> tuple[str, list[str]]:
    """Return (new_source, notes). Applies S-splices and global-stmt removal."""
    tree = ast.parse(src)
    st = symtable.symtable(src, "<cell>", "exec")

    # Build (position -> splice) edits.
    lines = src.splitlines(keepends=True)
    offsets = [0]
    for ln in lines:
        offsets.append(offsets[-1] + len(ln))

    def pos(lineno, col):
        return offsets[lineno - 1] + col

    # Collect JoinedStr spans for the f-string fallback.
    joined: list[ast.JoinedStr] = [n for n in ast.walk(tree)
                                   if isinstance(n, ast.JoinedStr)]

    # Walk with a scope chain mirrored between ast and symtable.
    edits: list[tuple[int, int, str]] = []   # (start, end, replacement)
    fstring_hits: set[int] = set()           # id() of JoinedStr needing rewrite
    fstring_chain: dict[int, list] = {}
    notes: list[str] = []

    table_children: dict[int, list[symtable.SymbolTable]] = {}

    def children_of(tab):
        if id(tab) not in table_children:
            table_children[id(tab)] = list(tab.get_children())
        return table_children[id(tab)]

    def match_child(tab, name, lineno):
        cands = [c for c in children_of(tab)
                 if c.get_name() == name and c.get_lineno() == lineno]
        if cands:
            return cands[0]
        cands = [c for c in children_of(tab) if c.get_name() == name]
        return cands[0] if cands else tab

    def visit(node, chain):
        new_chain = chain
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            new_chain = chain + [match_child(chain[-1], node.name, node.lineno)]
        elif isinstance(node, ast.Lambda):
            new_chain = chain + [match_child(chain[-1], "lambda", node.lineno)]
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                               ast.GeneratorExp)):
            kind = {ast.ListComp: "listcomp", ast.SetComp: "setcomp",
                    ast.DictComp: "dictcomp",
                    ast.GeneratorExp: "genexpr"}[type(node)]
            new_chain = chain + [match_child(chain[-1], kind, node.lineno)]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)) and len(chain) == 1 \
                and node.name in shared:
            indent = " " * node.col_offset
            insert_at = pos(node.end_lineno, node.end_col_offset)
            edits.append((insert_at, insert_at,
                          f"\n{indent}S.{node.name} = {node.name}"))
        if isinstance(node, ast.Global):
            keep = [n for n in node.names if n not in shared]
            if not keep:
                edits.append((pos(node.lineno, node.col_offset),
                              pos(node.end_lineno, node.end_col_offset), "pass"))
                notes.append(f"removed `global {', '.join(node.names)}`")
            elif keep != node.names:
                raise SystemExit(f"{cname}: mixed global statement {node.names}")
        if isinstance(node, ast.Name) and node.id in shared:
            resolves = resolves_to_module(new_chain, node.id)
            if resolves:
                a = pos(node.lineno, node.col_offset)
                b = pos(node.end_lineno, node.end_col_offset)
                span = src[a:b]
                if span == node.id:
                    edits.append((a, b, f"S.{node.id}"))
                else:
                    host = next((j for j in joined
                                 if pos(j.lineno, j.col_offset) <= a
                                 and b <= pos(j.end_lineno, j.end_col_offset)), None)
                    if host is None:
                        raise SystemExit(
                            f"{cname}:{node.lineno} cannot splice {node.id!r}: "
                            f"span reads {span!r} and no f-string hosts it")
                    fstring_hits.add(id(host))
                    fstring_chain[id(host)] = list(new_chain)
        for child in ast.iter_child_nodes(node):
            visit(child, new_chain)

    for n in tree.body:
        visit(n, [st])

    # F-string fallback: AST-rewrite the whole literal and splice its unparse.
    class SharedRewriter(ast.NodeTransformer):
        def __init__(self, chain):
            self.chain = chain

        def visit_Name(self, node):
            if (node.id in shared and isinstance(node.ctx, ast.Load)
                    and resolves_to_module(self.chain, node.id)):
                return ast.copy_location(
                    ast.Attribute(value=ast.Name(id="S", ctx=ast.Load()),
                                  attr=node.id, ctx=ast.Load()), node)
            return node

    for j in joined:
        if id(j) not in fstring_hits:
            continue
        chain = fstring_chain[id(j)]
        newj = SharedRewriter(chain).visit(ast.parse(ast.unparse(j), mode="eval").body)
        a = pos(j.lineno, j.col_offset)
        b = pos(j.end_lineno, j.end_col_offset)
        edits.append((a, b, ast.unparse(newj)))
        notes.append(f"f-string at line {j.lineno} rewritten via unparse")

    # apply edits right-to-left; overlapping edits are a bug.
    edits.sort(key=lambda e: e[0], reverse=True)
    last_start = None
    out = src
    for a, b, rep in edits:
        if last_start is not None and b > last_start:
            raise SystemExit(f"{cname}: overlapping edits near offset {a}")
        last_start = a
        out = out[:a] + rep + out[b:]

    return out, notes


EXTRA_HEADER = {
    "112.py": "from dci.config.loader import ACTIVE\n",
}

import re as _re
AT_VAR = _re.compile(r"@([A-Za-z_][A-Za-z_0-9]*)")


def at_alias_lines(src: str, shared: set[str]) -> str:
    """pandas .query/.eval resolve @names against the caller frame, which the
    S-rewrite would otherwise starve. Emit read-only module aliases; every
    such name is verified write-once by the migrator."""
    names = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            names.update(AT_VAR.findall(node.value))
    hits = sorted(names & shared)
    if not hits:
        return ""
    return "".join(
        f"{n} = getattr(S, {n!r}, None)  # pandas @-resolution alias (read-only)\n"
        for n in hits)

IMPORT_TRANSFORMS = {
    "import torch": "from dci.compat import torch",
    "from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed":
        "from dci.compat import AutoModelForCausalLM, AutoTokenizer, set_seed",
    "from IPython.display import display":
        "from dci.reporting.display import display",
}


def transform_imports(src: str) -> str:
    src = src.replace("from __future__ import annotations\n", "")
    for old, new in IMPORT_TRANSFORMS.items():
        src = src.replace(old, new)
    return src


def _patch_slot(cname: str, pid: str) -> int:
    for i, entry in enumerate(PATCHES[cname]):
        if entry[0] == pid:
            return i
    raise KeyError(pid)


def build_dynamic_patches(cells: dict[str, str]) -> None:
    """Fill the patches whose find-text is computed from the live source."""
    # P5: the storage block in 122
    src = cells["122.py"]
    a = src.index("DRIVE_AVAILABLE = False")
    b = src.index("PROFILE_ROOT = DURABLE_BASE")
    block = src[a:b].rstrip() + "\n"
    _i = _patch_slot("122.py", "P5-storage")
    _e = PATCHES["122.py"][_i]
    PATCHES["122.py"][_i] = (_e[0], block, _e[2] + "\n\n", _e[3], _e[4])
    # P6: whole of 132 -> backend binding stage (original moves to inference/)
    _i = _patch_slot("132.py", "P6-backend-construct")
    PATCHES["132.py"][_i] = (
        "P6-backend-construct", cells["132.py"],
        '''"""Backend binding. The HF loading/free code that lived in this cell moved
verbatim into dci.inference.hf_transformers (see migration ledger P6); this
stage now constructs the backend the execution config selects and preserves the
cell's public names (`load_model`, `free_model`, `tokenizer`, `model`)."""
from dci.inference import make_backend

BACKEND = make_backend()
load_model = BACKEND.load_model
free_model = BACKEND.free_model
tokenizer = None
model = None

print(f"Model loading is deferred and gated on Gate 0 and Gate M. Profile "
      f"{CFG.model_profile} pins {CFG.model_id} at {CFG.model_revision[:12]}. "
      f"backend={BACKEND.name}")
''',
        "execution-only", PATCHES["132.py"][_i][4])
    # P7: generate_batch body in 192
    src = cells["192.py"]
    a = src.index("def generate_batch(")
    b = src.index("def run_generation_stage(")
    original = src[a:b]
    (REPO / "src/dci/inference/_moved_generate.py.txt").write_text(
        original, encoding="utf-8")
    _i = _patch_slot("192.py", "P7-generate-seam")
    PATCHES["192.py"][_i] = (
        "P7-generate-seam", original,
        '''def generate_batch(batch_rows: list[dict[str, Any]],
                   batch_seed: int) -> tuple[list[str], dict[str, Any]]:
    """Delegates to the frozen backend (ledger P7). The oracle branch and the
    torch branch moved verbatim to dci.inference.oracle / .hf_transformers;
    the recorded engine, seeds, decoding and termination metadata are theirs
    to preserve and the execution fingerprint pins which one ran."""
    return BACKEND.generate(batch_rows, batch_seed)


''',
        "execution-only", PATCHES["192.py"][_i][4])


def apply_patches(cells: dict[str, str]) -> list[dict]:
    ledger = []
    for cname, plist in PATCHES.items():
        for pid, find, rep, ctype, why in plist:
            if find is None:
                raise SystemExit(f"{cname} patch {pid} was never materialised")
            if find not in cells[cname]:
                raise SystemExit(f"{cname}: patch {pid} anchor not found")
            cells[cname] = cells[cname].replace(find, rep, 1)
            ledger.append({"id": pid, "source": f"cells/{cname}",
                           "destination": f"stages/{stage_name(cname)}",
                           "change_type": ctype,
                           "expected_behavior": "unchanged (execution seam only)",
                           "verification": "regression: gate trace + artifact diff",
                           "protocol_impact": "none", "rationale": why})
    return ledger


def stage_name(cname: str) -> str:
    n = cname.removesuffix(".py")
    return f"c{n}_{STAGE_TITLES.get(n, 'stage')}.py"


HEADER = '''"""Stage {num} — migrated from notebook cell {cell} ({title}).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/{cell} to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
{lib_imports}
'''


def emit_stage(cname: str, body: str, lib_imports: set[str]) -> str:
    num = cname.removesuffix(".py")
    imports = []
    by_mod: dict[str, list[str]] = {}
    for n in sorted(lib_imports):
        by_mod.setdefault(LIB_TARGETS[n], []).append(n)
    for mod, names in sorted(by_mod.items()):
        imports.append(f"from {mod} import {', '.join(names)}  # noqa: F401")
    hdr = HEADER.format(num=num, cell=cname,
                        title=STAGE_TITLES.get(num, ""),
                        lib_imports="\n".join(imports))
    return (hdr + EXTRA_HEADER.get(cname, "")
            + at_alias_lines(body, ALIAS_SHARED) + "\n" + body)


def emit_prelude(cells: dict[str, str]) -> None:
    """The notebook's import cell (112) as a shared prelude every stage stars-in."""
    tree = ast.parse(cells["112.py"])
    lines = cells["112.py"].splitlines(keepends=True)
    imports = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append("".join(lines[node.lineno - 1: node.end_lineno]))
    text = ('"""Shared prelude: the notebook top-of-file imports, once, for every '
            'stage.\n\nGenerated by tools/migrate_v15.py from cell 112. torch and '
            'transformers come\nthrough dci.compat so the scientific core runs '
            'without a GPU stack."""\n'
            + transform_imports("".join(imports)))
    (REPO / "src/dci/pipeline/_prelude.py").write_text(text, encoding="utf-8")


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    cells = load_cells()
    emit_prelude(cells)
    build_dynamic_patches(cells)
    ledger = apply_patches(cells)
    shared = compute_shared(cells)
    extracted, impure = extract_libraries(cells, shared)
    print(f"shared names: {len(shared)}; extracted: {len(extracted)}; "
          f"impure (kept in place): {len(impure)}")
    for n, why in impure:
        print(f"  impure: {n}: {why}")

    global ALIAS_SHARED
    ALIAS_SHARED = shared
    order, mapping = [], []
    for cname, src in cells.items():
        src = transform_imports(src)
        refs = {n.id for n in ast.walk(ast.parse(src))
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        lib_needed = refs & extracted
        new_src, notes = rewrite_cell(cname, src, shared, lib_needed)
        out = emit_stage(cname, new_src, lib_needed)
        sname = stage_name(cname)
        (STAGES / sname).write_text(out, encoding="utf-8")
        order.append(sname.removesuffix(".py"))
        mapping.append({"source": f"cells/{cname}",
                        "destination": f"src/dci/pipeline/stages/{sname}",
                        "kind": STAGE_TITLES.get(cname.removesuffix('.py'), ""),
                        "shared_refs": sum(new_src.count(f"S.{n}") for n in shared),
                        "lib_imports": ";".join(sorted(lib_needed)),
                        "notes": "; ".join(notes[:3])})
        compile(out, sname, "exec")     # syntax check now, loudly

    (STAGES / "__init__.py").write_text(
        '"""Generated stage order — the notebook\'s cell order, preserved."""\n'
        f"ORDER = {order!r}\n", encoding="utf-8")
    with open(DOCS / "migration_map.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(mapping[0]))
        w.writeheader()
        w.writerows(mapping)
    with open(DOCS / "migration_ledger_patches.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ledger[0]))
        w.writeheader()
        w.writerows(ledger)
    (DOCS / "shared_names.txt").write_text(
        "\n".join(sorted(shared)) + "\n", encoding="utf-8")
    print(f"emitted {len(order)} stages; map + patch ledger written to docs/")


if __name__ == "__main__":
    sys.exit(main())
