# DCI-1 v8.1 — revalidation of the frame-aware pre-screen on fresh successor pilots

**Status.** Deliverable 5 of the redesign (2026-09-03). Section 1 (the
invalidation boundary) is proved from code and contracts and is final.
Sections 2–5 are filled from the successor pilot roots (2026-09-05 22:00Z).
Three of the four models have a first successor run and a replicate at
`PILOT_REPORT`; gemma-3n-e4b-it's first two roots were lost to incidents
(§2) and its valid runs `r23`/`r24` are in progress at commit `7d8e1d9`,
so every e4b row says *pending*. The verdict in §5 is given now with e4b
pending and is re-read when r23 lands.

## 1. The invalidation boundary, from the code

A changed retention rule changes which rungs a frame's calibration table
holds, and every later stage is a function of that table. Reading the
producer/consumer contract (`run/contracts.py`) and the stage code:

| artifact | reusable from a v8 root? | why |
|---|---|---|
| `PILOT_REGISTERED`, `QUALIFIED`, `GATE_0_APPARATUS` | no — a root registers under one commit and one manifest (`manifest.ensure_registration` refuses a different commit or binding) | the successor's manifest binds new rule constants, a new document and protocol version `8.1-pilot` |
| `REGIME_SCREEN` | no | the screen is laid out over four passes (`regime.screen_blocks`), the per-frame counts and screens are new record fields, the cap selection is rerun |
| `SECOND_PASS_SCREEN` | no | the batches are planned per frame and rendered under every frame; the record's `final_table_by_frame`, `provisional_plan` and `comparator_plan` are what Gate 2 reads |
| `GATE_1_INSTRUMENT` | no (reads the new screen rows) | descriptive, but formed on the new rows |
| forwarded candidate calibration (`GATE_2_CALIBRATION` candidate run) | **no** | the candidate population is decided per frame at Gate 2 (`FORWARDING_RULE`) and generated per frame; the v8 rows were one set on every frame |
| operating points n\*(f), m\*(f) | recomputed (same rule, fresh grid rows) | the grids are regenerated in the fresh root; the rule is unchanged, so agreement with v8 is expected up to sampling and is reported |
| chance coordinates κ(X, f), ι_A(f) | recomputed | read on the fresh root's own unconstrained cells |
| LOCAL validity, SPECTRUM validity / selection, core references, backups | recomputed | functions of the frame's new table |
| operating-point stability, reference sensitivity | recomputed at `MEMBERSHIP` of a successor confirm root | read the fresh Gate-2 grid rows and Gate-3 records |
| model eligibility, membership, confirmatory manifest | recomputed / new root | `confirm/pilot_import` binds the pilot records by hash; a v8 pilot is refused by readiness item 11 |

So the boundary is `REGIME_SCREEN`: nothing after `GATE_0_APPARATUS` of a
v8 root can be reused, and the successor pilots are fresh roots run from
registration. The v8 roots and the frozen root `dci1v8-confirm-r2` are not
overwritten, not resumed and not read by any successor stage.

## 2. Successor pilot roots

All four roots were registered at the successor commit `025e138` (protocol
version `8.1-pilot`), launched 2026-09-03 16:46Z from a clean worktree at
that commit (`/home/cnm13ryan/git/dci-v8-frameaware`; the lifecycle gate
refuses a dirty tree or a different commit), two independent TP=1 lanes,
roots under `dci1/evidence/` of the canonical worktree. The old roots are
the v8 pilots the frozen root was built from.

| model | old root | successor root | card | commit | successor status |
|---|---|---|---|---|---|
| qwen3-4b | `dci1v8-pilot-r9` | `dci1v8-pilot-r14` | 0 | `025e138` | `PILOT_REPORT` |
| qwen3-4b-instruct-2507 | `dci1v8-pilot-r10` | `dci1v8-pilot-r15` | 1 | `025e138` | `PILOT_REPORT` |
| gemma-3n-e2b-it | `dci1v8-pilot-r12` | `dci1v8-pilot-r16` | 1 | `025e138` | `PILOT_REPORT` |
| gemma-3n-e4b-it | `dci1v8-pilot-r13` | `dci1v8-pilot-r17` | 0 | `025e138` | **INVALIDATED** (reached `PILOT_REPORT` 16:39Z on unanswered candidate rows, below) |
| gemma-3n-e4b-it | `dci1v8-pilot-r13` | `dci1v8-pilot-r18` | 0 | `025e138` | **ABANDONED** at `GATE_2_CALIBRATION` (12 h backend cap, below) |
| gemma-3n-e4b-it | `dci1v8-pilot-r13` | `dci1v8-pilot-r23` | 1 | `7d8e1d9` | **pending** (chained after r20, 2026-09-05 14:15Z; the only difference from `025e138` is the backend wall-clock cap) |
| gemma-3n-e2b-it, replicate | `dci1v8-pilot-r16` (first successor run) | `dci1v8-pilot-r19` | 1 | `025e138` | **pending** (registered 2026-09-04 21:27Z) |
| qwen3-4b-instruct-2507, replicate | `dci1v8-pilot-r15` (first successor run) | `dci1v8-pilot-r20` | 1 | `025e138` | **pending** (launched after r19 reported, 2026-09-05) |
| qwen3-4b, replicate | `dci1v8-pilot-r14` (first successor run) | `dci1v8-pilot-r21` | 0 | `025e138` | **pending** (chained after r18, 2026-09-05) |
| gemma-3n-e4b-it, replicate | — | `dci1v8-pilot-r22` | 1 | `025e138` | **cancelled** before registration (it would have hit the same cap) |
| gemma-3n-e4b-it, replicate | `dci1v8-pilot-r23` | `dci1v8-pilot-r24` | 0 | `7d8e1d9` | **pending** (registered 2026-09-05 22:00Z on the card r21 freed) |

Incident on `dci1v8-pilot-r17`: the first `GATE_2_CALIBRATION` attempt
(started 06:33Z) was killed by the kernel's out-of-memory handler at
13:08:36Z (exit 137; the kernel log names the stage's python, 16.8 GB
anonymous RSS at the kill) because the slow test suite of §4 had been
started on the same host during the stage's candidate run. The suite was
stopped. The driver's automatic retry (13:10:37Z) failed in ten minutes
with `IntegrityError: backend blocked the run`: the vLLM engine core of
the killed attempt had survived as an orphan (reparented to the user's
`systemd --user`, 22 GB of card 0 still allocated) because the adapter's
reaper is a `finally` block that a SIGKILL bypasses, so the retry's
engine could not initialise. The orphan was terminated by hand after
checking its parentage and start time, and the driver was relaunched at
13:23:57Z from the same clean worktree at `025e138`. The third attempt reached `PILOT_REPORT` at 16:39Z and its records are
**invalid evidence**: the grids' backend runs of the first attempt were
reused (complete and answered), but so was the candidate run's rows file
that the failed second attempt had left behind — 274,176 rows, every
`final_answer` empty, the run's provenance sidecar marked `blocked`. The
reuse rule (`dci1v7.run.execute._reusable_rows`, unchanged since the base
commit `ab1b6be`) reuses a stored run when the design's generation
identity matches and checks neither that the rows were answered nor the
sidecar's `blocked` flag, so the stage scored 274,176 empty answers, every
family came out with zero LOCAL-valid rungs on every frame under every
policy (own, legacy, proxy alike), and the Gate-2 and Gate-3 records were
signed on that. The root is left as it is (nothing is edited in place) and
is excluded from §3; it documents the defect. The replacement root
`dci1v8-pilot-r18` was registered at 16:42Z from the same clean worktree at
`025e138` and runs every stage from registration with nothing to reuse.
This is the "pre-existing unrelated failure" of the task brief: it is not
touched by the redesign (the reuse code has no diff against the base
commit), it was reached only because of the out-of-memory kill, it is
reported here and in §4, and it is not fixed on this branch. The slow suite
is rerun after the pilots finish (§4).

The replicate root `dci1v8-pilot-r19` is a second successor run of
gemma-3n-e2b-it on the same commit, started on the otherwise idle card
while r18 ran. It is not a replacement: it gives a third grid sample for
frame 0, whose operating point flipped between r12 and r16 (§3.1), and a
test-retest of the frame-aware forwarding on one model (the agreement of
two successor runs' forwarded sets, which the counterfactual replay
predicted at a Jaccard of about 0.6–0.7 for a 24-topic screen). Its block
in the tables compares it with r16, not with the v8 root.
The second replicate `dci1v8-pilot-r20` repeats qwen3-4b-instruct-2507,
the model whose eligibility follows from the forwarding rule alone (frame
3, §3.2), under a fresh sample; it is the cheapest run (two supported
frames) and tests the load-bearing result. Its block compares it with r15.
The third replicate `dci1v8-pilot-r21` repeats qwen3-4b, the model with
the largest status change (LOCAL on two frames under v8, on four under the
successor), chained on card 0 after r18. Its block compares it with r14.
A fourth replicate (`dci1v8-pilot-r22`, gemma-3n-e4b-it) was chained and
then cancelled before registration once the 12 h cap was understood; its
place is taken by `dci1v8-pilot-r24` at `7d8e1d9`, launched on card 0 when
r21 finished, so that e4b too has a test-retest pair (r23 → r24).

Second incident (both lanes): at 22:08Z on 2026-09-04 the host's desktop
session crashed (the journal shows a crash report and the display
connection breaking at 23:08–23:09 local) and every process of the user
session died with it, including both pilot drivers and their backends
(r18 in the second pass, batch 2 at 11,904 of 19,488 rows; r19 in the
screen at 24,000 of 32,928 rows). The crashed backend runs left only
completed, answered rows (no row without a final answer, no `blocked`
sidecar), which the reuse rule reports as `INCOMPLETE_PREVIOUS_RUN` and
regenerates, so the drivers were relaunched at 22:11:52Z on the same roots
from the same clean worktree and resumed at the interrupted stage; the
completed batches are reused by identity. This is unrelated to the
redesign and to the r17 defect; it is recorded because the roots' driver
logs show the restart.

Third incident (r18, the e4b replacement): its Gate-2 candidate run
(276,480 rows, the largest of any model because all four frames are
supported and each carries its comparator extras) was killed by the pilot
layer's 12-hour backend wall-clock cap at 14:10Z on 2026-09-05 with
212,288 rows (77 %) generated, at a steady ~17.5k rows/h on one card. The
backend does not resume a partial rows file (the reuse rule regenerates an
`INCOMPLETE_PREVIOUS_RUN` and the backend restarts at row 0), so the
driver's retry could never finish inside the cap; the driver and the stage
were stopped by hand before the retry launched its backend, no orphan was
left on the card, and the root is left as it is (no Gate-2 record, never
signed). The cap is `dci1v8dev.run.execute` (v8 pilot layer, 2026-08-30,
inherited from v7) and is purely operational; it was raised to 36 h on
commit `7d8e1d9`, which differs from `025e138` in nothing else, and the
e4b rerun `dci1v8-pilot-r23` runs at that commit from a second clean
worktree. r17's first attempt would have hit the same cap. Every other
successor root ran at `025e138`; whether a freeze may bind pilots at two
commits whose only difference is this cap, or every pilot should be rerun
at `7d8e1d9`, is listed in §5.

What each successor root ran that the old one did not: a four-pass screen
(24 topics per frame instead of 6, `SCREEN_FRAME_OFFSETS=(0,1,2,3)`), a
second pass planned per frame and rendered under every frame (24 topics per
frame per batch, declared as topics rather than inferred as repeated
draws), Gate-2 forwarding decided per frame against that frame's ι_A(f)
after the grids (`FORWARDING_RULE`, target basis `calibration_iota_a`),
candidate rows generated only on the frame's own blocks, and two comparator
arms generated on the same frame (the legacy pooled set and the screen-proxy
set, `comparator_rows`) so that a Gate-3 re-verdict separates the forwarding
rule from the sample. Every number below is read from the signed pilot
records by `tools/v8_prescreen_revalidation.py --all` (read-only, opens no
protected stage); the machine-readable extract is
`prescreen_revalidation_tables.md` and `revalidation.json` beside this file.

## 3. Old versus successor: model × frame status

### 3.1 Operating points (Gate 2, before any forwarding)

The grids precede the forwarding and the operating-point rule is unchanged,
so n\*(f), m\*(f) and ι_A(f) should agree with the old roots up to fresh
sampling. They do on 9 of the 10 supported frames measured so far: identical
n\*/m\* and ι_A(f) within 0.03 (about one topic-level SE):

| model | f | old n\*/m\*, ι_A(f) | new n\*/m\*, ι_A(f) |
|---|---:|---|---|
| qwen3-4b | 0 / 1 / 2 / 3 | 6/12 0.671 · 7/12 0.608 · 3/12 0.672 · 5/13 0.697 | 6/12 0.674 · 7/12 0.608 · 3/12 0.673 · 5/13 0.702 |
| qwen3-4b-instruct-2507 | 1 / 3 | 6/10 0.642 · 6/12 0.681 | 6/10 0.652 · 6/12 0.673 |
| qwen3-4b-instruct-2507 | 0, 2 | UNSUPPORTED (`GRID_RESOLUTION_INSUFFICIENT`: A's curve falls from 0.86 at severity 4 to 0.20 at 5, no whole band bracketed) | same, both frames |
| gemma-3n-e2b-it | 1 / 2 / 3 | 3/10 0.612 · 2/10 0.819 · 7/11 0.663 | 3/10 0.635 · 2/10 0.797 · 7/11 0.686 |
| gemma-3n-e2b-it | 0 | **1/8 0.754** | **8/8 0.642** |
| gemma-3n-e4b-it | 0–3 | 6/9 0.745 · 6/9 0.711 · 7/9 0.676 · 8/10 0.686 | r18 (abandoned at the candidate run) read 6/9 0.745 · 6/9 0.710 · 7/9 0.676 · 8/10 0.688 on its grids; r23 pending |

The one exception is gemma-3n-e2b-it frame 0. Its A curve is nearly the
same in both roots and non-monotone (old 0.77 0.80 0.60 0.38 0.48 0.57 0.59
0.62 over severities 1–8; new 0.77 0.77 0.60 0.36 0.46 0.58 0.61 0.64), the
eligible severities are the same set {1, 2, 3, 6, 7, 8}, and the rule
selected the floor (1) in r12 and the top (8) in r16. That is the
operating-point rule on fresh grid rows, not the pre-screen (no forwarding
input reaches it); it belongs to the operating-point stability record and
is flagged in §5 because a successor confirm root's `MEMBERSHIP` would carry
the new value.

### 3.2 Per frame: the frame's own set beside every policy on the same rows

fam/bk = LOCAL-valid families / admissible backups; **L** = LOCAL-supported
under §13.15 (≥ 5 families and ≥ 2 backups), l = not. "legacy" and
"proxy" are the Gate-3 re-verdicts of the legacy pooled set and of the
screen-proxy (A-basis) set on the successor run's own calibration rows
(`retention_comparison`), so a difference between "own" and "legacy" on one
row is the forwarding rule and nothing else. "valid rungs" = LOCAL-valid /
SPECTRUM-valid rungs in the frame's table.

| model | f | old (pooled run) | new: own set | new: legacy set, same rows | new: proxy set, same rows | valid rungs old → new | attribution |
|---|---:|---|---|---|---|---|---|
| qwen3-4b | 0 | 5/2 **L** | 5/2 **L** | 5/2 **L** | 5/2 **L** | 8/30 → 11/26 | unchanged |
| qwen3-4b | 1 | 4/1 l | 5/2 **L** | 5/2 **L** | 5/2 **L** | 6/34 → 7/37 | gained; the legacy set is also supported on the new rows, so the gain is the 24-topic screen and/or the fresh calibration sample, not the forwarding rule |
| qwen3-4b | 2 | 4/1 l | 6/2 **L** | 5/2 **L** | 6/2 **L** | 11/35 → 13/33 | gained; as frame 1, and the frame's set carries one family more than the legacy set |
| qwen3-4b | 3 | 7/2 **L** | 6/2 **L** | 7/2 **L** | 6/2 **L** | 10/37 → 9/31 | unchanged status; the frame's set (53 rungs) carries one family fewer than the legacy set on the same rows |
| qwen3-4b-instruct-2507 | 0, 2 | UNSUPPORTED | UNSUPPORTED | — | — | — | unchanged (grid resolution) |
| qwen3-4b-instruct-2507 | 1 | 7/2 **L** | 6/2 **L** | 6/2 **L** | 6/2 **L** | 17/32 → 15/38 | unchanged |
| qwen3-4b-instruct-2507 | 3 | 3/0 l | 5/2 **L** | 4/1 l | 5/2 **L** | 3/36 → 6/35 | **gained by the forwarding rule**: on identical rows the legacy set is unsupported and both frame-specific sets are supported |
| gemma-3n-e2b-it | 0 | 6/2 **L** | 5/2 **L** | 5/2 **L** | 5/2 **L** | 9/34 → 11/34 | unchanged status (operating point moved, §3.1) |
| gemma-3n-e2b-it | 1 | 6/2 **L** | 5/2 **L** | 5/2 **L** | 5/2 **L** | 11/31 → 12/37 | unchanged |
| gemma-3n-e2b-it | 2 | 3/0 l, coverage not identified | 3/0 l, coverage identified | 2/0 l | 3/0 l | 3/38 → 4/28 | unsupported under every policy (ι_A(f) ≈ 0.80 is the hardest frame); the spectrum arm is newly identified, which the comparator arms cannot attribute (coverage is not re-verdicted for them) |
| gemma-3n-e2b-it | 3 | 7/2 **L** | 7/2 **L** | 6/2 **L** | 7/2 **L** | 13/35 → 14/39 | unchanged; the frame's set carries one family more than the legacy set |
| gemma-3n-e4b-it | 0–3 | 5/2 L · 6/2 L · 4/1 l · 7/2 L | pending (r23) | pending | pending | 8/40 · 8/38 · 8/36 · 13/37 → pending | pending |

On every measured frame the frame's own set finds at least as many
LOCAL-valid rungs as the legacy set on the same rows except qwen3-4b frame
3 (one family fewer, still supported).

### 3.3 Per model: LOCAL eligibility, SPECTRUM coverage, compute

| model | LOCAL frames old → new | eligible (≥ 2 LOCAL frames) old → new | legacy set on new rows | proxy set on new rows | SPECTRUM frames old → new | generations old → new |
|---|---|---|---|---|---|---|
| qwen3-4b | {0, 3} → {0, 1, 2, 3} | yes → yes | {0, 1, 2, 3}, yes | {0, 1, 2, 3}, yes | {0, 1, 2, 3} → {0, 1, 2, 3} | 266,424 → 401,640 (+51 %) |
| qwen3-4b-instruct-2507 | {1} → {1, 3} | **no → yes** | {1}, **no** | {1, 3}, yes | {1, 3} → {1, 3} | 282,000 → 290,184 (+3 %) |
| gemma-3n-e2b-it | {0, 1, 3} → {0, 1, 3} | yes → yes | {0, 1, 3}, yes | {0, 1, 3}, yes | {0, 1, 3} → {0, 1, 2, 3} | 269,352 → 403,848 (+50 %) |
| gemma-3n-e4b-it | {0, 1, 3} → pending (r23) | yes → pending | pending | pending | {0, 1, 2, 3} → pending | 291,672 → pending (r18 reached 212,288 candidate rows of 276,480 before the cap) |

The eligibility change for qwen3-4b-instruct-2507 is the one outcome that
the comparator arm attributes to the forwarding rule alone. The generation
increase on the fully supported models decomposes (qwen3-4b) into the
four-pass screen (32,928 rows, four times the old screen), the per-frame
second pass (64,896) and the comparator arms (62,976), the last being a
pilot-only cost that a confirm root does not repeat; the per-frame
candidate population itself costs what the pooled one did. On
qwen3-4b-instruct-2507 the unsupported frames generate nothing, so the
increase is 3 %.

### 3.4 The target basis: C (calibration ι_A(f)) versus A (screen proxy)

The registered basis forwards at Gate 2 against ι_A(f) read from the grid
rows; the screen-proxy plan (`provisional_plan`, basis A) is recorded at the
second pass and generated as a comparator arm. Their agreement on the
forwarded sets (Jaccard) and on the outcome:

| model | Jaccard by frame | fam/bk under A vs C | LOCAL verdict under A vs C |
|---|---|---|---|
| qwen3-4b | 0.97 · 0.83 · 0.80 · 0.96 | identical on 4/4 | identical on 4/4 |
| qwen3-4b-instruct-2507 | — · 0.85 · — · 0.88 | identical on 2/2 | identical on 2/2 |
| gemma-3n-e2b-it | 0.95 · 0.96 · 0.63 · 0.96 | identical on 4/4 | identical on 4/4 |
| gemma-3n-e4b-it | r18's grids gave 0.86 · 0.94 · 0.87 · 0.80 before the run was abandoned; r23 pending | pending | pending |

So the two bases measure different rungs (up to 37 % of a frame's set) and
reach the same §13.15 verdict with the same family and backup counts on
every measured frame. The evidence does not discriminate between them; the
registered choice rests on the precision argument in the design note (the
grid ι_A(f) has SE ≈ 0.02, the screen proxy drifts by up to 0.17), and it
is the choice the pilots ran.

### 3.5 Test-retest under the successor design (replicate roots)

A replicate is a second successor run of the same model at the same
commit with a fresh screen, second pass and grids. It answers two
questions the old-versus-new comparison cannot: whether a frame's status
under the frame-aware rule is stable under resampling, and how much of a
frame's forwarded set is sampling noise (the counterfactual replay
predicted a Jaccard of about 0.63–0.72 between two 24-topic screens).

| model | pair | n\*(f) first → replicate | LOCAL-supported frames | fam/bk first → replicate | forwarded-set Jaccard by frame |
|---|---|---|---|---|---|
| gemma-3n-e2b-it | r16 → r19 | 8, 3, 2, 7 → 8, 3, 2, 7 | {0, 1, 3} → {0, 1, 3} | 5/2, 5/2, 3/0, 7/2 → 6/2, 5/2, 3/0, 8/2 | 0.76 · 0.72 · 0.61 · 0.66 |
| qwen3-4b-instruct-2507 | r15 → r20 | f1 6, f3 6 → f1 6, f3 6 (f0: unsupported → supported at n\* = 4, ι_A = 0.85) | {1, 3} → {1, 3} | f1 6/2, f3 5/2 → f1 7/2, f3 5/2 (f0 3/0) | f1 0.69 · f3 0.76 |
| qwen3-4b | r14 → r21 | 6, 7, 3, 5 → 6, 7, 3, 4 | {0, 1, 2, 3} → {0, 1, 2, 3} | 5/2, 5/2, 6/2, 6/2 → 6/2, 5/2, 6/2, 5/2 | 0.78 · 0.67 · 0.59 · 0.65 |
| gemma-3n-e4b-it | r23 → r24 | pending | pending | pending | pending |

gemma-3n-e2b-it replicates exactly at the status level: the same
operating point on every frame (frame 0 chose n\* = 8 in both successor
runs, against n\* = 1 in the v8 root, on the same eligible set), the same
three LOCAL-supported frames, coverage identified on all four in both,
ι_A(f) within 0.02, and the legacy comparator unsupported on frame 2 in
both (2/0 and 1/0). The forwarded sets overlap at 0.61–0.76, inside the
replay's prediction, so roughly a third of a frame's set turns over
between runs while the families that survive to references do not.

qwen3-4b-instruct-2507 replicates on the load-bearing frame: frame 3 is
LOCAL-supported with 5 families and 2 backups in both successor runs, and
in both the legacy pooled set re-verdicted on the same rows is 4/1 and
unsupported, so the eligibility that follows from the forwarding rule
alone (§3.2) is not a one-sample event. Frame 1 stays supported (6/2 →
7/2, legacy 6/2 → 7/2). The one difference is at Gate 2, before any
forwarding: frame 0, unsupported for grid resolution in r10 and r15 (A's
curve 0.855 at severity 4 against a band edge), is supported in r20 at
n\* = 4 with ι_A(f) = 0.85, the hardest operating point of any frame, and
gives 3/0 (legacy 2/0), so the model's LOCAL frames are {1, 3} in both
runs. That frame-0 verdict is the operating-point rule on fresh grid
rows, the same knife-edge as e2b frame 0 (§3.1), and belongs with
decision 2 of §5.

qwen3-4b replicates in full: LOCAL-supported on all four frames in both
successor runs (5/2, 5/2, 6/2, 6/2 → 6/2, 5/2, 6/2, 5/2; coverage
identified on all four in both), the legacy set re-verdicted on the same
rows also supported on all four in both, the same n\* on frames 0–2 and
n\* 5 → 4 on frame 3 with ι_A(f) unchanged (0.702 → 0.701), and
forwarded-set overlap 0.59–0.78. So the v8-to-successor gain on frames 1
and 2 (§3.2), which the comparator could not attribute to the rule, is at
least stable under resampling of the successor design.

Across the three replicated models, every LOCAL verdict on every measured
frame agrees between the two successor runs (10 supported frames, 0
disagreements), and the sets overlap at 0.59–0.78. The instability lives
one stage earlier, in the operating-point rule on the grids (§3.1 and the
2507 frame-0 flip above), which the pre-screen does not touch.

## 4. Validation

Code at `HEAD` (`e0bbcdf`) is the pilot commit `025e138` plus the read-only
revalidation tool and a regenerated `pipeline_validation` report; the
suites below therefore validate the code the roots were produced by.

- Fast suites, all dci1 testpaths, `-m "not slow"` at `e0bbcdf`: 3,683
  passed, 86 skipped, 13 failed, 9 errors. Every failure and error was
  reproduced at `ab1b6be` (the base commit, without the redesign) with the
  identical set of test ids: the nine errors are `tests/helpers.py`
  importing `dci1.evidence`, which does not exist; five failures in
  `tests/test_freeze_and_config.py` and five in `tests_v4/` (registered
  values, verifier hash against a signed manifest, the autorater split)
  are the same missing module and fixtures; the three isolation tests
  (`tests_v5/v6/v7 test_isolation.py::test_v5_cannot_adopt_a_v4r4_evidence_root`)
  are the disk-dependent failure already reported at `f7af7f2`. None is
  touched by this change; none was fixed here. `tests_v8dev` and
  `tests_v7` (other than that one test) are green.
- Slow suite (`tests_v8dev -m slow`, the synthetic end-to-end walks: pilot
  lifecycle, frame conditioning, frame-aware pre-screen, confirm lifecycle)
  at `e0bbcdf`: 20 passed in 38 min, run on the idle host (the first
  attempt, run beside a Gate 2, caused the r17 out-of-memory kill of §2).
- Commit `7d8e1d9` (the 36 h backend cap, §2) changes one constant in
  `dci1v8dev.run.execute`; `tests_v8dev -m "not slow"` at that commit: 417
  passed, 2 skipped. The e4b roots r23/r24 run at it.
- Pre-existing failure found by the r17 incident (§2), reproduced without
  the redesign by inspection: `dci1v7.run.execute._reusable_rows` (no diff
  against `ab1b6be`) accepts a stored backend run whose rows are unanswered
  and whose sidecar is `blocked`, and the stage's row accounting
  (`every_row_scored`) counts identities, not answers, so a retry after a
  failed backend run signs a record on empty generations. Not fixed here;
  the guard belongs on the reuse path (refuse a `blocked` sidecar and any
  row without a final answer) with a test, and the driver should kill the
  backend's process group and check the card before retrying.
- `reports/dci1v8dev/pipeline_validation.{md,json}` regenerated at the
  successor rule table (world results unchanged).
- Producer/consumer contract: every successor record was written under
  `run/contracts.py` as extended (the walk exercises every stage's producer
  and consumer); `manifest.ensure_registration` bound all four roots to
  `025e138`.
- No protected artifact was opened: the tool reads pilot records only, and
  the working tree under `dci1/evidence/dci1v8-confirm-r2` is unchanged.

## 5. Freeze-readiness verdict

*Given with gemma-3n-e4b-it pending (r23/r24 at `7d8e1d9`); re-read when r23 lands.*

**RESEARCHER_DECISION_REQUIRED.** Nothing technical blocks a freeze under
the registered rule: every stage from `REGIME_SCREEN` regenerates in fresh
roots, the contracts and readiness item 11 refuse a v8 pilot, the frozen
root `dci1v8-confirm-r2` is superseded for this successor design and not
altered, and the pilots give the intended effect (frame-specific sets that
are at least as supported as the pooled set on the same rows, and one
model whose eligibility follows from the rule alone) and the effect
replicates (§3.5: 10 of 10 LOCAL verdicts agree between two successor
runs of each of three models). Three decisions remain the researcher's
and the evidence does not force them:

1. **The target basis.** C (registered, run) and A (comparator) are
   scientifically non-equivalent — they forward different rungs — and
   empirically indistinguishable on outcome (§3.4). Ratifying C freezes
   what was run; choosing A requires re-running Gate 2 onward, because the
   forwarded sets differ.
2. **Knife-edge operating points on fresh grids.** gemma-3n-e2b-it frame
   0 flipped from n\* = 1 (v8) to n\* = 8 (both successor runs) on the
   same eligible set (§3.1), and qwen3-4b-instruct-2507 frame 0 flipped
   from unsupported (grid resolution, v8 and first successor run) to
   supported at n\* = 4, ι_A = 0.85 in the replicate (§3.5), under the
   unchanged rule. A successor confirm root carries whichever the pilot it
   binds read; whether that is acceptable, or the rule's behaviour at band
   edges and on non-monotone curves should be resolved first, is a
   question about the operating-point rule, not this redesign.
3. **The e4b pilot's commit.** `dci1v8-pilot-r23` runs at `7d8e1d9` (the
   backend cap raised to 36 h) while r14, r15, r16 and the replicates ran
   at `025e138`. The confirm layer records each pilot's producing commit
   (`confirm/pilot_import`) and does not itself refuse a mixture, but a
   freeze that binds two commits needs the researcher's sanction or a
   rerun of the other three models at `7d8e1d9` (about 20 card-hours).

Recorded follow-ups, not blocking: an out-of-memory kill of a stage leaves
its engine core alive on the card and the driver's retry then fails on
GPU memory (§2), so the driver should kill the backend's process group
and check the card before retrying; rungs of the class and near-form arms
are forwarded to a design with no such arm (`legacy_prescreen_characterization.md`, the second-pass section); the successor
Gate 2 scores every grid row on every rung any policy could forward
(≈ 24 GB per lane at the grids, ≈ 52 GB at the candidate run), so two
lanes need a memory guard — scoring in two passes would cut it about four
times; and the `V8_CONFIRMATORY` §3a seven-versus-six discrepancy noted
during the characterization.
