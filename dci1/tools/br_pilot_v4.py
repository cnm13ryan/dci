"""B+R discriminating pilot (non-confirmatory, v4 design work).

Runs the smallest version of the focal-outcome companion-swap experiment
recommended by user-notes/dci-construct-pass2.md §G row 1: does the v3
target A specifically degrade delivery of the focal B, or does any
comparable companion constraint do the same?

    D(B<-A) - D(B<-R) > 0.25  supports a pair-specific interaction (H1)
    D(B<-A) - D(B<-R) < 0.10  supports generic compositional load (H2)

In the v3 architecture every prompt already carries the topic background,
so the source note's B+S cell coincides with the existing Gate 2A B-alone
cell; only B+R requires generation. B-alone, R-alone, and B+A are reused
from registered v3 evidence under the reuse conditions of
user-notes/prompt-to-red-team.md (provenance, frozen verifier hash,
content hashes, comparable configuration), pinned by
tests_v3/test_br_pilot_characterization.py.

This tool NEVER writes inside evidence/dci1-v3. Its cache lives in
evidence/br-pilot-v4/ (machine-local, non-confirmatory); its protocol and
results live in reports/br_pilot_v4/.

Usage (from dci1/, in the scientific venv):
    python tools/br_pilot_v4.py plan
    python tools/br_pilot_v4.py generate --model gemma-3n-e2b-it [--device 0]
    python tools/br_pilot_v4.py analyze
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v3.generation.backend import run_backend            # noqa: E402
from dci1v3.generation.cache import cache_rows, fill_cache   # noqa: E402
from dci1v3.generation.plans import backend_plan             # noqa: E402
from dci1v3.generation.prompts import Cell, prompt_plan      # noqa: E402
from dci1v3.models.registry import MODEL_BY_KEY              # noqa: E402
from dci1v3.protocol import constants as C                   # noqa: E402
from dci1v3.protocol.hashing import sha_text                 # noqa: E402
from dci1v3.protocol.wordings import wording                 # noqa: E402
from dci1v3.topics.split import split_topics                 # noqa: E402
from dci1v3.verifiers import verifier_source_hash            # noqa: E402
from dci1v3.verifiers.families import added_verifier         # noqa: E402

EVIDENCE_V3 = DCI1 / "evidence" / "dci1-v3"
PILOT_EVIDENCE = DCI1 / "evidence" / "br-pilot-v4"
REPORT_DIR = DCI1 / "reports" / "br_pilot_v4"
PROTOCOL_PATH = REPORT_DIR / "protocol.json"

STAGE = "brpilot-v4"          # fresh seed-stream label; disjoint from every
                              # registered stage by domain construction
DRAWS = 2                     # predefined; indices 2,3 reserved for the
                              # one-shot precision extension rule
EXTENSION_DRAWS = 4
BOOTSTRAP_SEED = 20260819
RESAMPLES = 10_000
B_FIRST, R_FIRST = "B_first", "R_first"

GEMMAS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it")

#: Verified verbatim from user-notes/dci-construct-pass2.md:415.
THRESHOLD_PAIR_SPECIFIC = 0.25
THRESHOLD_GENERIC_LOAD = 0.10


def freeze_body(model_key: str) -> dict:
    return json.loads((EVIDENCE_V3 / model_key / "gate3_freeze.json")
                      .read_text())["payload"]["body"]


def build_cells(model_key: str) -> list[Cell]:
    """B+R cells on the 96 solo-calibration topics.

    Position p in the frozen solo order fixes: order p mod 2 (even =
    B first), B wording p mod 4, R wording (p + p//4) mod 4 — the
    registered composed-cell allocation with B in the target slot. The
    allocation is shared across the three reference cells of a topic, so
    within a topic the prompts differ only in the R line (asserted).
    """
    body = freeze_body(model_key)
    m_star = body["m_star"]
    references = [tuple(r) for r in body["final_references"]]
    solo = split_topics()["solo"]
    assert len(solo) == C.N_SOLO
    cells: list[Cell] = []
    for p, topic in enumerate(solo):
        order = B_FIRST if p % 2 == 0 else R_FIRST
        b_windex = p % 4
        r_windex = (p + p // 4) % 4
        b_text = wording("B", b_windex, m=m_star)
        skeletons = []
        for family, q in references:
            r_text = wording(family, r_windex, q=q)
            pair = ([b_text, r_text] if order == B_FIRST
                    else [r_text, b_text])
            prompt = C.PROMPT_TWO.format(question=topic["question"],
                                         c1=pair[0], c2=pair[1])
            skeletons.append(prompt.replace(r_text, "{R}"))
            kind = f"br:{family}:{q}"
            cells.append(Cell(
                cell_id=f"{STAGE}:{topic['topic_id']}:{kind}",
                stage=STAGE, topic_id=topic["topic_id"], block_id=None,
                arm=None, kind=kind, constraint_id=family, severity=q,
                order=order, target_wording=b_windex,
                added_wording=r_windex, n=None, prompt=prompt,
                prompt_hash=sha_text(prompt), draws=DRAWS,
                active_wordings=(b_text, r_text)))
        assert len(set(skeletons)) == 1, \
            f"{topic['topic_id']}: prompts differ outside the R line"
    return cells


def write_protocol() -> dict:
    solo = split_topics()["solo"]
    ordered_ids = [t["topic_id"] for t in solo]
    protocol = {
        "name": "br-pilot-v4",
        "status": "non-confirmatory pilot; not a registered v3 stage; "
                  "not a v4 confirmatory run",
        "question": "Is the deterioration of focal delivery under "
                    "composition specific to the target A, or generic "
                    "to adding any matched companion constraint?",
        "source_authority": {
            "design": "user-notes/dci-construct-pass2.md §G row 1",
            "thresholds_verbatim": (
                "D(B<-A) - D(B<-R) > 0.25 supports H1 and licenses a "
                "pairwise construct. < 0.10 supports H2 and refutes the "
                "pairwise framing entirely"),
            "reuse_rules": "user-notes/prompt-to-red-team.md §L",
            "b_plus_s_mapping": (
                "In v3 every prompt carries the topic background and no "
                "third constraint exists, so B+S coincides with the "
                "existing Gate 2A B-alone cell; it is reused, not "
                "generated."),
        },
        "models": list(GEMMAS),
        "models_excluded": {
            "qwen3-4b": "terminal at Gate 2A; no registered B+A cell, so "
                        "D(B<-A) is undefined",
            "qwen3-4b-instruct-2507": "same",
        },
        "design": {
            "topics": "the 96 solo-calibration topics (non-confirmatory "
                      "pool), frozen split order",
            "topic_order_sha256": hashlib.sha256(
                "\x1f".join(ordered_ids).encode()).hexdigest(),
            "cells_per_model": "3 references x 96 topics",
            "references": {m: freeze_body(m)["final_references"]
                           for m in GEMMAS},
            "m_star": {m: freeze_body(m)["m_star"] for m in GEMMAS},
            "draws_per_cell": DRAWS,
            "rows_per_model": C.N_SOLO * C.N_FINAL_REFERENCES * DRAWS,
            "allocation": "position p: order p mod 2 (even = B first); "
                          "B wording p mod 4; R wording (p + p//4) mod 4; "
                          "shared across the topic's three reference "
                          "cells",
            "extension_rule": (
                "If the 95% bootstrap CI of Delta spans either decision "
                "threshold, extend every cell once to 4 draws (indices "
                "2,3; identical seed derivation) and classify from the "
                "extended data. No other extension is permitted."),
        },
        "generation": {
            "backend": "pinned vLLM backend via "
                       "dci1v3.generation.backend.run_backend",
            "plan": "dci1v3.generation.plans.backend_plan(spec, cap=512, "
                    "decoding='stochastic') — byte-identical builder to "
                    "the registered stages",
            "decoding": C.DECODING,
            "completion_cap": 512,
            "seed_scheme": f"generation_seed(GENERATION_ROOT_SEED, "
                           f"'{STAGE}', model_id, prompt_hash, "
                           f"draw_index); the stage label separates this "
                           f"stream from every registered stage",
            "cache_dir": "evidence/br-pilot-v4/<model_key>/ — never "
                         "inside evidence/dci1-v3",
        },
        "outcomes": {
            "instrument": "frozen deterministic verifier",
            "verifier_source_hash": verifier_source_hash(),
            "focal_pass": "added_verifier('B', m_star)(raw_response)",
            "reference_pass": "added_verifier(family, q)(raw_response) "
                              "(stored as added_pass)",
            "diagnostics": ["s0 accidental-'however' count",
                            "finish_reason == 'length' (truncation)",
                            "responses under 3 words",
                            "joint compliance states",
                            "per-order P(B|R)"],
        },
        "reused_baselines": {
            "B_alone": "gate2a solo:B:7 rows, 96 topics x 1 draw "
                       "(E2B 78/96, E4B 73/96)",
            "R_alone": "gate2a solo:<family>:<q> rows at the frozen "
                       "reference severities, same topics",
            "B_plus_A": "confirmatory AB added_pass, 384 blocks x 16 "
                        "draws (E2B 2115/6144, E4B 2730/6144)",
            "validity": "pinned by tests_v3/"
                        "test_br_pilot_characterization.py: frozen "
                        "verifier hash on every reused row equals the "
                        "current instrument, verdicts recompute exactly, "
                        "content hashes verify, revisions match the "
                        "registry",
            "cross_set_note": (
                "P(B|A) comes from confirmatory topics while the pilot "
                "runs on solo-calibration topics; the seeded "
                "area-stratified random split makes the sets "
                "exchangeable by design, and B-solo cancels from Delta "
                "so only P(B|R) - P(B|A) carries the cross-set "
                "comparison."),
        },
        "estimator": {
            "cell_rates": "equal weight per topic: per-topic draw mean, "
                          "then mean over topics (blocks for P(B|A))",
            "quantities": [
                "P(B solo), P(B|R_j), P(B|Rbar) = mean_j P(B|R_j), "
                "P(B|A)",
                "D(B<-A) = P(B solo) - P(B|A)",
                "D(B<-R_j) = P(B solo) - P(B|R_j)",
                "Delta = D(B<-A) - D(B<-Rbar) = P(B|Rbar) - P(B|A)",
                "Delta_j = P(B|R_j) - P(B|A)",
                "reciprocal D(R_j<-B) = P(R_j solo) - P(R_j|B)"],
            "uncertainty": f"nonparametric bootstrap, {RESAMPLES} "
                           f"resamples, seed {BOOTSTRAP_SEED}, "
                           f"percentile 95% intervals; units: solo "
                           f"topics (stratified by pilot order 48/48, "
                           f"joint per-topic vector preserves pairing) "
                           f"independently of confirmatory blocks "
                           f"(stratified by registered order 192/192)",
        },
        "classification_rule": {
            "H1_pair_specific": f"Delta point estimate > "
                                f"{THRESHOLD_PAIR_SPECIFIC}",
            "H2_generic_load": f"Delta point estimate < "
                               f"{THRESHOLD_GENERIC_LOAD}",
            "otherwise": "INDETERMINATE",
            "robustness": "classification is CI-robust when the 95% CI "
                          "excludes the nearest opposing threshold",
        },
        "prohibitions": [
            "no write inside evidence/dci1-v3",
            "no sequestered topics",
            "no confirmatory claim from this pilot",
            "no threshold or design change after generation begins",
        ],
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PROTOCOL_PATH.write_text(json.dumps(protocol, indent=1) + "\n")
    for model_key in GEMMAS:
        cells = build_cells(model_key)
        plan = prompt_plan(cells)
        (REPORT_DIR / f"prompt_plan_{model_key}.json").write_text(
            json.dumps(plan, indent=1) + "\n")
    return protocol


def generate(model_key: str, device: int) -> None:
    if not PROTOCOL_PATH.exists():
        raise SystemExit("run `plan` first: the protocol must be frozen "
                         "before generation")
    protocol = json.loads(PROTOCOL_PATH.read_text())
    spec = MODEL_BY_KEY[model_key]
    cells = build_cells(model_key)
    plan = prompt_plan(cells)
    frozen = json.loads(
        (REPORT_DIR / f"prompt_plan_{model_key}.json").read_text())
    if plan != frozen:
        raise SystemExit(f"{model_key}: prompt plan drifted from the "
                         f"frozen plan; refusing to generate")
    draws = protocol["design"]["draws_per_cell"]
    cells = [c if c.draws == draws else
             Cell(**{**c.__dict__, "draws": draws}) for c in cells]
    stage_dir = PILOT_EVIDENCE / model_key
    report = fill_cache(
        stage_dir, cells, spec=spec, stage=STAGE,
        generation_root=C.GENERATION_ROOT_SEED,
        plan=backend_plan(spec, cap=512, decoding="stochastic"),
        generate_fn=functools.partial(run_backend, device=device),
        environment={"python_executable": sys.executable,
                     "dependency_digest": "br-pilot-v4 (scientific venv)"})
    print(model_key, report["status"], report["cells"], "cells,",
          report["draws"], "draws")


def _percentile_ci(samples: np.ndarray) -> list[float]:
    return [float(np.quantile(samples, 0.025)),
            float(np.quantile(samples, 0.975))]


def analyze() -> dict:
    protocol = json.loads(PROTOCOL_PATH.read_text())
    draws = protocol["design"]["draws_per_cell"]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    result: dict = {"protocol_sha256": sha_text(PROTOCOL_PATH.read_text()),
                    "draws_per_cell": draws, "models": {}}
    for model_key in GEMMAS:
        body = freeze_body(model_key)
        m_star = body["m_star"]
        references = [tuple(r) for r in body["final_references"]]
        focal = added_verifier("B", m_star)

        # --- pilot rows ------------------------------------------------
        rows = cache_rows(PILOT_EVIDENCE / model_key)
        solo_ids = [t["topic_id"] for t in split_topics()["solo"]]
        t_index = {tid: i for i, tid in enumerate(solo_ids)}
        n_t = len(solo_ids)
        br_focal = {r_: np.full((n_t, draws), np.nan) for r_ in references}
        br_ref = {r_: np.full((n_t, draws), np.nan) for r_ in references}
        order_of = np.empty(n_t, dtype=object)
        diag = {"rows": 0, "truncated": 0, "short": 0, "accidental_s0": 0}
        joint = {r_: [0, 0, 0, 0] for r_ in references}   # BR, B~R, ~BR, ~B~R
        per_order = {r_: {B_FIRST: [], R_FIRST: []} for r_ in references}
        for row in rows:
            key = (row["constraint_id"], row["severity"])
            ti = t_index[row["topic_id"]]
            b_pass = focal(row["raw_response"])
            r_pass = bool(row["verdicts"]["added_pass"])
            br_focal[key][ti, row["draw_index"]] = float(b_pass)
            br_ref[key][ti, row["draw_index"]] = float(r_pass)
            order_of[ti] = row["order"]
            diag["rows"] += 1
            diag["truncated"] += row["finish_reason"] == "length"
            diag["short"] += len(row["raw_response"].split()) < 3
            diag["accidental_s0"] += row["verdicts"]["s0"] > 0
            joint[key][(1 - b_pass) * 2 + (1 - r_pass)] += 1
            per_order[key][row["order"]].append(float(b_pass))
        for key in references:
            assert not np.isnan(br_focal[key]).any(), \
                f"{model_key} {key}: incomplete draw matrix"

        # --- reused baselines -------------------------------------------
        g2a = cache_rows(EVIDENCE_V3 / model_key / "gate2a")
        b_solo = np.full(n_t, np.nan)
        r_solo = {r_: np.full(n_t, np.nan) for r_ in references}
        for row in g2a:
            ti = t_index.get(row["topic_id"])
            if ti is None:
                continue
            if row["kind"] == f"solo:B:{m_star}":
                b_solo[ti] = float(bool(row["verdicts"]["added_pass"]))
            for family, q in references:
                if row["kind"] == f"solo:{family}:{q}":
                    r_solo[(family, q)][ti] = \
                        float(bool(row["verdicts"]["added_pass"]))
        assert not np.isnan(b_solo).any()
        ab_by_block: dict[str, list[float]] = {}
        ab_order: dict[str, str] = {}
        with (EVIDENCE_V3 / model_key / "confirmatory"
              / "cache.jsonl").open() as fh:
            for line in fh:
                if '"arm": "AB"' not in line:
                    continue
                row = json.loads(line)
                ab_by_block.setdefault(row["block_id"], []).append(
                    float(bool(row["verdicts"]["added_pass"])))
                ab_order[row["block_id"]] = row["order"]
        blocks = sorted(ab_by_block)
        ab_means = np.array([np.mean(ab_by_block[b]) for b in blocks])
        ab_orders = np.array([ab_order[b] for b in blocks])

        # --- point estimates and bootstrap -------------------------------
        br_topic = {r_: br_focal[r_].mean(axis=1) for r_ in references}
        rin_topic = {r_: br_ref[r_].mean(axis=1) for r_ in references}

        def stats(t_idx: np.ndarray, b_idx: np.ndarray) -> dict:
            p_solo = float(b_solo[t_idx].mean())
            p_ab = float(ab_means[b_idx].mean())
            p_brj = {r_: float(br_topic[r_][t_idx].mean())
                     for r_ in references}
            p_br = float(np.mean(list(p_brj.values())))
            out = {"P_B_solo": p_solo, "P_B_given_A": p_ab,
                   "P_B_given_Rbar": p_br,
                   "D_B_from_A": p_solo - p_ab,
                   "D_B_from_Rbar": p_solo - p_br,
                   "Delta": p_br - p_ab}
            for r_ in references:
                tag = f"{r_[0]}@{r_[1]}"
                out[f"P_B_given_{tag}"] = p_brj[r_]
                out[f"D_B_from_{tag}"] = p_solo - p_brj[r_]
                out[f"Delta_{tag}"] = p_brj[r_] - p_ab
                out[f"D_{tag}_from_B"] = float(
                    r_solo[r_][t_idx].mean()
                    - rin_topic[r_][t_idx].mean())
            return out

        all_t = np.arange(n_t)
        all_b = np.arange(len(blocks))
        point = stats(all_t, all_b)

        t_strata = [np.flatnonzero(order_of == o)
                    for o in (B_FIRST, R_FIRST)]
        b_strata = [np.flatnonzero(ab_orders == o)
                    for o in (C.TARGET_FIRST, C.ADDED_FIRST)]
        boot: dict[str, list] = {k: [] for k in point}
        for _ in range(RESAMPLES):
            t_idx = np.concatenate([rng.choice(s, size=s.size)
                                    for s in t_strata])
            b_idx = np.concatenate([rng.choice(s, size=s.size)
                                    for s in b_strata])
            for k, v in stats(t_idx, b_idx).items():
                boot[k].append(v)
        cis = {k: _percentile_ci(np.array(v)) for k, v in boot.items()}

        delta, ci = point["Delta"], cis["Delta"]
        if delta > THRESHOLD_PAIR_SPECIFIC:
            label = "H1_PAIR_SPECIFIC"
            robust = ci[0] > THRESHOLD_GENERIC_LOAD
        elif delta < THRESHOLD_GENERIC_LOAD:
            label = "H2_GENERIC_LOAD"
            robust = ci[1] < THRESHOLD_PAIR_SPECIFIC
        else:
            label = "INDETERMINATE"
            robust = False
        spans = (ci[0] < THRESHOLD_GENERIC_LOAD < ci[1]
                 or ci[0] < THRESHOLD_PAIR_SPECIFIC < ci[1])

        result["models"][model_key] = {
            "m_star": m_star,
            "references": [list(r_) for r_ in references],
            "point": point,
            "ci95": cis,
            "classification": label,
            "ci_robust": bool(robust),
            "ci_spans_a_threshold": bool(spans),
            "extension_required": bool(spans and draws < EXTENSION_DRAWS),
            "diagnostics": {
                **diag,
                "joint_states_B_R": {
                    f"{r_[0]}@{r_[1]}": dict(zip(
                        ("both_pass", "B_only", "R_only", "neither"),
                        joint[r_])) for r_ in references},
                "P_B_given_R_by_order": {
                    f"{r_[0]}@{r_[1]}": {
                        o: float(np.mean(v))
                        for o, v in per_order[r_].items()}
                    for r_ in references},
                "P_B_given_A_by_order": {
                    o: float(ab_means[ab_orders == o].mean())
                    for o in (C.TARGET_FIRST, C.ADDED_FIRST)},
            },
        }
    out_path = REPORT_DIR / "result.json"
    out_path.write_text(json.dumps(result, indent=1) + "\n")
    print("written", out_path)
    for model_key, r in result["models"].items():
        p, c = r["point"], r["ci95"]
        print(f"== {model_key}  refs {r['references']}")
        print(f"   D(B<-A) = {p['D_B_from_A']:+.4f} {c['D_B_from_A']}")
        print(f"   D(B<-Rbar) = {p['D_B_from_Rbar']:+.4f} "
              f"{c['D_B_from_Rbar']}")
        print(f"   Delta = {p['Delta']:+.4f} {c['Delta']}  ->  "
              f"{r['classification']} (robust={r['ci_robust']})")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    gen = sub.add_parser("generate")
    gen.add_argument("--model", required=True, choices=GEMMAS)
    gen.add_argument("--device", type=int, default=0)
    sub.add_parser("analyze")
    args = parser.parse_args()
    if args.command == "plan":
        write_protocol()
        print("protocol frozen at", PROTOCOL_PATH)
    elif args.command == "generate":
        generate(args.model, args.device)
    else:
        analyze()


if __name__ == "__main__":
    main()
