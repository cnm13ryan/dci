# Human validation of the deterministic verifier

- criterion: human-vs-verifier disagreement rate, conditional on the deterministic verifier's class
- interval: one-sided 95% Wilson upper bound; registered target 10%, strengthened target 5%
- the bound is claimed on the **representative** component only

- items presented: 120; human records: 120 (response rate 100.0%)
- labelled: 120; abstentions (UNSURE): 0; coverage 100.0%
- overall accuracy (human == verifier, over labelled): 96.7%

## Human x verifier

| human | verifier | count |
|---|---|---|
| SATISFIES | fail | 4 |
| SATISFIES | pass | 60 |
| VIOLATES | fail | 56 |

## Per-class bounds

| component | verifier class | cases | disagreements | error rate | 95% Wilson upper | <=10% | <=5% | more for 10% | more for 5% |
|---|---|---|---|---|---|---|---|---|---|
| representative | pass | 52 | 0 | 0.0% | 4.9% | yes | yes | 0 | 0 |
| representative | fail | 52 | 4 | 7.7% | 16.1% | no | no | 34 | 123 |
| boundary | pass | 8 | 0 | 0.0% | 25.3% | -- | -- | -- | -- |
| boundary | fail | 8 | 0 | 0.0% | 25.3% | -- | -- | -- | -- |
| pooled | pass | 60 | 0 | 0.0% | 4.3% | -- | -- | -- | -- |
| pooled | fail | 60 | 4 | 6.7% | 14.0% | -- | -- | -- | -- |

## Discordant items

| id | human | verifier | n | s0 | component | boundary category |
|---|---|---|---|---|---|---|
| gemma-3n-e2b-it::gate1_validation:history-47:solo:A:4:0 | SATISFIES | fail | 4 | 5 | representative | None |
| gemma-3n-e4b-it::gate1_validation:history-47:solo:A:7:0 | SATISFIES | fail | 7 | 8 | representative | None |
| gemma-3n-e4b-it::gate1_validation:technology-06:solo:A:8:0 | SATISFIES | fail | 8 | 9 | representative | None |
| qwen3-4b::gate1_validation:language-and-writing-00:solo:A:1:0 | SATISFIES | fail | 1 | 2 | representative | None |

## Operational channel (never merged into a label)

- reported for the instrument, never merged into a human label: an operational failure is not a judgment
- human abstentions: 0
- pool finish_reason over reviewed items: {'stop': 115, 'length': 5}
- registered judge statuses over reviewed items: {'valid': 343, 'invalid_output': 17}

## Sequential stopping decision

- **ESCALATE** — the observed disagreement rate cannot meet the target at any sample size; this is a finding about the verifier, not a sampling shortfall
- verifier-pass: 52 cases, 0 disagreements; 10% MET (+0), 5% MET (+0)
- verifier-fail: 52 cases, 4 disagreements; 10% CONTINUE (+34), 5% UNREACHABLE_AT_OBSERVED_RATE (+123)
- next batch representative targets: {'pass': 0, 'fail': 123}
- projected total labels 243 vs budget 150 (OVER)

## Integrity

- record dir: pins {'pins': 3, 'files': 2}, chains [{'file': 'calibration_Bryan.jsonl', 'records': 56, 'chained': 0, 'unchained_legacy': 56}, {'file': 'extension1_Bryan.jsonl', 'records': 64, 'chained': 64, 'unchained_legacy': 0}]
- sealed reserved set sha256: f8831598e275487037e6e51cd85e1df2b33c8e359d13836e500e9ab7b881d7a3 (untouched; 0 sealed ids labelled)

