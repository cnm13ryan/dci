# DCI-1 v8 — confirmatory membership (locked before any composed row)

Produced by `tools/v8_membership_lock.py` from the signed `MEMBERSHIP` records under `/home/cnm13ryan/git/dci-v8-canonical/dci1/evidence/dci1v8-confirm-r2`.

| model | LOCAL eligible | LOCAL frames | SPECTRUM frames | topped up | P(n* reproduced) by frame |
|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | yes | [0, 1, 3] | [0, 1, 3] | no | f0: 0.50, f1: 0.91, f2: 0.95, f3: 0.51 |
| `gemma-3n-e4b-it` | yes | [0, 1, 3] | [0, 1, 2, 3] | no | f0: 0.43, f1: 0.41, f2: 0.86, f3: 0.79 |
| `qwen3-4b` | yes | [0, 3] | [0, 1, 2, 3] | yes | f0: 0.53, f1: 0.58, f2: 0.57, f3: 0.40 |
| `qwen3-4b-instruct-2507` | no | [] | [1, 3] | no | f0: —, f1: 0.64, f2: —, f3: 0.94 |

**Allocation:** 384 blocks per frame (rules.CONFIRMATORY_BLOCKS_PER_FRAME; projected at 3 LOCAL frames, joint family size 18; adverse-scenario precondition met: True).

**Precision rule.** one allocation, rules.CONFIRMATORY_BLOCKS_PER_FRAME = 384 blocks per entering frame (the ceiling), for every model; §16.1's variance form is projected at it under the registered planning constants and the adverse scenarios at the joint Šidák constant (k = 6 x LOCAL frames entering) and the projection is recorded; §16.2's precondition and §17.3's realised evaluation decide, and no allocation is chosen from a menu

**Multiplicity rule.** per (model, frame, configuration): F1 as registered (six members), bootstrap studentised maximum-modulus; per (model, configuration): the JOINT family of every F1 member of every entering frame, critical value from a topic-level block bootstrap with one draw shared across frames; the decision interval of every primary claim is the joint one; a model-level LOCAL claim is the conjunction over its entering frames (intersection-union; no further adjustment); no at-least-one-frame claim exists
