# DCI-1 v8 — confirmatory membership (locked before any composed row)

Produced by `tools/v8_membership_lock.py` from the signed `MEMBERSHIP` records under `/home/cnm13ryan/git/dci-v8-canonical/dci1/evidence/dci1v8-confirm`.

| model | LOCAL eligible | LOCAL frames | SPECTRUM frames | topped up | P(n* reproduced) by frame |
|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | yes | [1, 3] | [0, 1, 2, 3] | yes | f0: 0.85, f1: 0.88, f2: 0.99, f3: 0.47 |
| `gemma-3n-e4b-it` | no | [] | [0, 1, 2, 3] | yes | f0: 0.68, f1: 0.39, f2: 0.65, f3: 0.55 |
| `qwen3-4b` | yes | [0, 3] | [0, 1, 2, 3] | yes | f0: 0.56, f1: 0.57, f2: 0.56, f3: 0.40 |
| `qwen3-4b-instruct-2507` | no | [] | [1, 3] | no | f0: —, f1: 0.64, f2: —, f3: 0.94 |

**Allocation:** 384 blocks per frame (decided at 2 LOCAL frames, joint family size 12; rule met: True).

**Precision rule.** the smallest allocation in {288, 384} blocks per frame whose projected simultaneous half-width for Delta_R at the joint Šidák constant (k = 6 x LOCAL frames entering) is <= 0.05 under BOTH REGISTERED_ALTERNATE and COMPOSED_AT_HALF; §16.1's variance form, §16.2's precondition and §17.3's realised evaluation unchanged

**Multiplicity rule.** per (model, frame, configuration): F1 as registered (six members), bootstrap studentised maximum-modulus; per (model, configuration): the JOINT family of every F1 member of every entering frame, critical value from a topic-level block bootstrap with one draw shared across frames; the decision interval of every primary claim is the joint one; a model-level LOCAL claim is the conjunction over its entering frames (intersection-union; no further adjustment); no at-least-one-frame claim exists
