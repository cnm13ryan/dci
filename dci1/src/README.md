# dci1/src — one package per protocol revision

Each DCI-1 revision is its own package with its own study id and evidence tree,
kept unmodified after it closed. Closed does not mean unused: later revisions
import earlier ones, so `dci1v4` and `dci1v7` are dependencies of the current
line. Status is as `RESEARCH_STATE.md` §4b records it. A package's own docstring
describes it as it stood when written, so for example `dci1v5`'s still says "not
frozen".

| package | revision | status | imports | tests | in CI |
|---|---|---|---|---|---|
| `dci1` | v2 | closed | — | `tests/` | yes |
| `dci1v3` | v3 | closed: Gemmas reached unmasked analysis, Qwens stopped at Gate 2A | — | `tests_v3/` | yes |
| `dci1v4` | v4r2 | implemented, never frozen, no confirmatory data; **shared base of every later revision** | — | `tests_v4/` | yes |
| `bgrid_screen_v4`, `cal_screen_v4`, `fs_screen_v4`, `matrix_screen_v4` | v4 design screens | non-confirmatory design evidence | `dci1v4`, each other | `tests_v4/` | yes |
| `dci1v4r3` | v4r3 | closed 2026-08-21 at `GATE_1_MEASUREMENT` | `dci1v4` | `tests_v4r3/` | yes |
| `dci1v4r4` | v4r4 | two replications frozen 2026-08-22; superseded by v5 | `dci1v4`, `dci1v4r3` | `tests_v4r4/` | yes |
| `dci1v5` | v5 | run and closed 2026-08-24 | `dci1v4`, `dci1v4r4` | `tests_v5/` | yes |
| `dci1v6` | v6 | closed 2026-08-27, zero survivors | `dci1v4`, `dci1v4r4` | `tests_v6/` | yes |
| `dci1v7` | v7 | closed 2026-08-28, zero survivors; **base of v8** | `dci1v4`, `dci1v4r4` | `tests_v7/` | yes |
| `dci1v8dev` | v8 and v8.1 | **current**: v8.1 frozen 2026-09-08, analysed 2026-09-10 | `dci1v7`, `dci1v4`, `dci1v5` | `tests_v8dev/` | yes |

"Imports" lists the other packages a package's source imports. `dci1/tools/`
imports most of them, too.

Two consequences:

- **A change to `dci1v4` or `dci1v7` is a change to v8.1.** Those packages hold
  the verifiers, wordings and backend seam that v8.1 runs, and v8.1's frozen
  verifier hash covers `dci1v4` and `dci1v7` modules
  (`dci1v8dev/verifiers/__init__.py`).
- **The closed packages are records, not candidates for repair.** Known defects
  in them are recorded rather than fixed: see `RESEARCH_STATE.md` §5, for
  example the foreign-root refusal (PR #31) and four pinned decision-packet
  paths in v6 and v7.
