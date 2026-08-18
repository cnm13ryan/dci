# autorater_forensics — sample-level diagnosis of the Gate 1 autorater

Standalone diagnostic workspace (UK AISI **Inspect AI** + **Inspect
View** + **Inspect Scout**) for understanding how
`openai/gpt-oss-20b`'s reasoning effort changes its binary judgments of
frozen DCI-1 v3 responses. The registered Gate 1 implementation and
evidence tree are **authoritative and read-only** here: nothing in this
directory imports `dci1v3`, mutates `dci1/evidence/`, or feeds back
into registered records. Judgments produced here are diagnostic
observables of a proxy instrument — never human validation, ground
truth, verifier accuracy against humans, or semantic correctness.
Reasoning traces are observables, not guaranteed faithful explanations.

## Layout

    autorater_forensics/
    ├── README.md               this file
    ├── requirements.txt        diagnostic-only deps (own .venv)
    ├── server/launch_server.sh one fixed TP=1 vLLM OpenAI server
    ├── src/forensics/          paths, dataset builder, parser, verifier
    ├── task.py                 the Inspect task (effort is the only knob)
    ├── smoke.py                end-to-end data-path smoke test
    ├── dataset/                built diagnostic dataset   (gitignored)
    ├── logs/{low,medium,high}/ immutable Inspect eval logs (gitignored)
    ├── analysis/merge_runs.py  cross-reasoning merge + pattern tables
    ├── analysis/out/           merged.jsonl / merged.csv / report.md
    ├── scans/scanners.py       Scout scanners (add new ones here)
    ├── scans/run_scan.py       run scanners over the eval logs
    ├── scans/results/          Scout findings (separate from raw logs)
    └── tests/                  smoke checks (pytest)

## The diagnostic unit and dataset

One fixed `(constraint, frozen model response)` judged under exactly
three matched conditions — `reasoning_effort` ∈ {low, medium, high} —
with judge model+revision (`6cee5e81…`), prompt (gate1-judge/2.0.0
verbatim), greedy decoding (T=0, top_p=1, seed fixed), max_tokens 2048,
parsing vocabulary, dataset order (sorted stable IDs), and serving
(one TP=1 server, prefix caching disabled for greedy repeatability)
all held fixed.

`src/forensics/dataset.py` builds `dataset/diagnostic.jsonl` READ-ONLY
from the frozen response pools and the three registered development
rounds (low/medium/high labels already exist per item, so contested
cases are identified without any new inference). Development-half items
only — held-out calibration items are never included. Components:
**contested** (labels differ across efforts, any label disagrees with
the deterministic verifier, or any round had a non-valid status —
invalids preserved, never dropped) and **representative controls**
(all-agree, stratified per (source model, n, verifier class)). Stable
sample ID = `<model_key>::<item_id>`, identical across all three runs.

## Operator guide (exact commands, in order)

From `autorater_forensics/` (`source .venv/bin/activate` optional; the
explicit interpreter paths below work without it):

    # 0. one-time environment
    uv venv .venv --python 3.12
    uv pip install --python .venv/bin/python -r requirements.txt

    # 1. start one identical TP=1 server per GPU (~1.5 min to load).
    #    Do not run registered backend ops on these GPUs meanwhile.
    bash server/launch_server.sh 0 8555 &
    bash server/launch_server.sh 1 8556 &
    for p in 8555 8556; do
      until curl -s -o /dev/null http://127.0.0.1:$p/v1/models; do sleep 3; done
    done

    # 2. build the dataset (read-only over evidence) + smoke test
    .venv/bin/python -m src.forensics.dataset
    .venv/bin/python smoke.py          # must end with SMOKE PASS

    # 3. the three matched runs (370 samples each), both GPUs busy:
    #    each effort's run stays WHOLLY on one server (never split a
    #    run across servers); high is the longest, so it gets its own
    #    card while low+medium share the other.
    OPENAI_API_KEY=forensics .venv/bin/inspect eval task.py@forensics \
      -T effort=high --model openai/gpt-oss-20b \
      --model-base-url http://127.0.0.1:8555/v1 \
      --log-dir logs/high --max-connections 4 --display plain &
    for e in low medium; do
      OPENAI_API_KEY=forensics .venv/bin/inspect eval task.py@forensics \
        -T effort=$e --model openai/gpt-oss-20b \
        --model-base-url http://127.0.0.1:8556/v1 \
        --log-dir logs/$e --max-connections 4 --display plain
    done
    wait

    # 4. browse samples in Inspect View
    .venv/bin/inspect view --log-dir logs --port 7575
    #    open http://127.0.0.1:7575

    # 5. cross-reasoning comparison tables
    .venv/bin/python analysis/merge_runs.py
    #    -> analysis/out/{merged.jsonl, merged.csv, report.md}

    # 6. Scout scanners over the eval logs
    .venv/bin/python scans/run_scan.py
    #    findings -> scans/results/ ; browse with:
    .venv/bin/scout view scans/results

    # 7. smoke checks
    .venv/bin/python -m pytest tests -q

## How Inspect reaches the server

Model `openai/gpt-oss-20b` with `--model-base-url
http://127.0.0.1:8555/v1` (any `OPENAI_API_KEY` value; the local server
ignores auth). `reasoning_effort` travels as a **top-level
chat-completions parameter** via `GenerateConfig.extra_body`; the
pinned vLLM (0.15.1) maps it into the harmony chat template
(`chat_completion/serving.py:299`) and returns the analysis channel
separately as `reasoning`/`reasoning_content`, which Inspect stores as
`ContentReasoning` — so reasoning is never concatenated with the final
answer. Verified three ways by `smoke.py`: `/tokenize` + `/detokenize`
show `Reasoning: <effort>` in the rendered prompt; low vs high produce
different reasoning lengths; an invalid effort value is rejected by the
server schema (HTTP 400), proving the field is parsed.

## Using Inspect View

`inspect view --log-dir logs --port 7575`, then pick the run
(low/medium/high) in the top-left log selector. Click any sample row to
open it: the **Messages** tab shows the exact prompt, the model's
reasoning block (collapsible, rendered separately), and the final
answer; **Scoring** shows the parsed label, agreement flag, status,
truncation, and reasoning/final sizes (our scorer's metadata);
**Metadata** shows the frozen provenance (source model, pool, n,
s0 count, prior round labels, contested reasons); **Usage** shows token
counts; errors appear on the sample header. To align one sample across
conditions, note its stable ID and open the same ID in each run's log
(the three runs share identical IDs); `analysis/out/merged.jsonl` holds
the same alignment programmatically.

## Adding Scout scanners

Write a new `@scanner(...)` factory in `scans/scanners.py` (see
`reasoning_final_contradiction` — deterministic: flags transcripts
whose reasoning concludes one verdict while the final answer emits the
other), add it to the list in `scans/run_scan.py`, and re-run. Findings
go to `scans/results/` (`scout view scans/results` to browse); raw eval
logs are never modified. Add scanners only after manual inspection
reveals a recurring phenomenon — the taxonomy is discovered, not
pre-committed. `grep_scanner` and `llm_scanner` from `inspect_scout`
are available for quick variants.

## Stability experiments (experiments/)

`experiments/PREREGISTERED.md` fixes the designs, thresholds, and
rejection rules for the judge-stability program BEFORE any run;
`experiments/FINDINGS.md` holds the consolidated results. Layout:

    experiments/
    ├── PREREGISTERED.md        fixed designs/thresholds (committed first)
    ├── FINDINGS.md             consolidated results + decision
    ├── build_sets.py           E1/E2 datasets, calibration sample,
    │                           sealed reserved final-check IDs
    ├── exp1_cap/               output-cap search (run.sh, analyze.py)
    ├── exp2_repeat/            3x identical repeat triples per effort
    ├── exp3_path/              path-divergence factor tests: prompt
    │                           token identity, conc=1 vs 4, registered
    │                           offline seam at chunk 32/1
    ├── escalation.py           pre-specified human-escalation triggers
    └── human_review/           blind review CLI + fixed definitions +
                                paired agreement report + sampled sets

Human-review flow (when an annotator is available): blind `review_app.py
review --set calibration --annotator NAME` (shows ONLY instruction,
response, definitions, edge rules; refuses piped input), then
`reveal` per item AFTER commit, then `agreement_report.py` for the
paired per-configuration comparison. `records/` is append-only; the
self-test marks its records synthetic and `agreement_report.py`
refuses them. The reserved final-check IDs
(`reserved_final_check_ids.json`) stay sealed until the full
configuration is frozen.

Analysis outputs land in `analysis/out/`: `exp1_report.md`,
`exp2_report.md`, `exp3_report.md`, `exp1_records.jsonl`,
`escalation.json`.

## Extension points (deliberately not built yet)

Oracle labels / human calibration (e.g. CJE) can be added later without
restructuring: raw per-sample records in `merged.jsonl` carry stable
IDs, full responses, and all three judgments, so an oracle-label column
or judge-calibration layer attaches by ID. No human annotator is
currently available, so nothing here claims human validation.
