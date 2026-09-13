# Backend determinism measurement (2026-09-02T21:53:25+00:00)

Run directory: `/home/cnm13ryan/git/dci-v8-canonical/dci1/evidence/dci1v8-pilot-r12/evidence/dci1v8/gemma-3n-e2b-it/REGIME_SCREEN/backend_runs/ladder`; 96 design rows re-generated twice on card 1 under the stored plan (digest 71699a2eed9ff390) and the stored scientific seeds.

| comparison | rows | identical | share | mean common-prefix share |
|---|---:|---:|---:|---:|
| fresh_vs_fresh | 96 | 94 | 0.979 | 0.983 |
| fresh1_vs_stored | 96 | 66 | 0.688 | 0.767 |
| fresh2_vs_stored | 96 | 66 | 0.688 | 0.766 |

**Reading.** NOT bit-for-bit deterministic: 0.979 of rows identical across two fresh runs under identical plan and seeds; the design, seeds and verdicts are reproducible as data, the sampled text is not promised

What is promised (preregistration §8): every prompt, seed, verdict and analysis is reproducible as data from the stored rows and the frozen design; the sampled text is reproducible only to the extent measured here.
