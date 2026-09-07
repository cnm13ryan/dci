# DCI-1 v8.1 — revalidation of the frame-aware pre-screen on fresh successor pilots

**Status.** Deliverable 5 of the redesign (2026-09-03). Section 1 (the
invalidation boundary) is proved from code and contracts and is final.
Sections 2–5 are filled from the successor pilot roots (2026-09-07
00:00Z). Every model has a first successor run and a replicate at
`PILOT_REPORT` (gemma-3n-e4b-it's first two roots were lost to incidents,
§2; its valid runs are `r23`/`r24` at commit `7d8e1d9`). A third run of
qwen3-4b-instruct-2507 (`r25`) is complete; a re-execution of the v8
pooled design (`r26`, the control of §2) is in progress and is appended
when it lands.

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
| gemma-3n-e4b-it | `dci1v8-pilot-r13` | `dci1v8-pilot-r23` | 1, then 0 | `7d8e1d9` | `PILOT_REPORT` 2026-09-06 23:55Z (the only difference from `025e138` is the backend wall-clock cap) |
| gemma-3n-e2b-it, replicate | `dci1v8-pilot-r16` (first successor run) | `dci1v8-pilot-r19` | 1 | `025e138` | **pending** (registered 2026-09-04 21:27Z) |
| qwen3-4b-instruct-2507, replicate | `dci1v8-pilot-r15` (first successor run) | `dci1v8-pilot-r20` | 1 | `025e138` | **pending** (launched after r19 reported, 2026-09-05) |
| qwen3-4b, replicate | `dci1v8-pilot-r14` (first successor run) | `dci1v8-pilot-r21` | 0 | `025e138` | **pending** (chained after r18, 2026-09-05) |
| gemma-3n-e4b-it, replicate | — | `dci1v8-pilot-r22` | 1 | `025e138` | **cancelled** before registration (it would have hit the same cap) |
| gemma-3n-e4b-it, replicate | `dci1v8-pilot-r23` | `dci1v8-pilot-r24` | 0 | `7d8e1d9` | `PILOT_REPORT` 2026-09-06 23:04Z |
| qwen3-4b-instruct-2507, third run | `dci1v8-pilot-r15` | `dci1v8-pilot-r25` | 1 | `025e138` | `PILOT_REPORT` 2026-09-07 05:33Z |
| qwen3-4b-instruct-2507, **v8-design re-execution** | `dci1v8-pilot-r10` (v8) | `dci1v8-pilot-r26` | 0 | `f7af7f2` (the frozen v8 commit) | **pending** (chained after r25, 2026-09-06 23:59Z) |

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
A third run of qwen3-4b-instruct-2507 (`dci1v8-pilot-r25`, at `025e138`
like r15 and r20) was started on card 1 while the e4b tails, which are
CPU-bound and cannot share the host, left it idle: it takes the frame-3
result that the causal claim rests on from two runs to three.
`dci1v8-pilot-r26` is the control from the other side: a re-execution of
the *v8 pooled design itself* at the frozen commit `f7af7f2` (a new pilot
root; the frozen confirm root is not touched), chained on card 0 after r25.
It asks whether the pooled design's own verdict on 2507 frame 3 (3/0 in
r10) survives decoding noise: if a pooled re-run reached 5/2 there, the
"rule alone" attribution would rest on r10's decoding luck rather than on
the design. Its block compares r26 with r10.

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

Fourth incident (r23 and r24, 2026-09-06 02:51Z): the root filesystem
filled up (the test suites of §4 had left about 190 GB of pytest temporary
fixture directories under `/tmp`, one module fixture set per worker per
run) and both lanes' backends failed with `OSError` while writing rows —
r23 in its Gate-2 grid-B run, r24 in second-pass batch 2. The temporary
directories were deleted (189 GB free again), every rows file the crash
touched was checked to end on a complete JSON line (the backend writes
whole lines), and the drivers' automatic retries resumed both stages:
complete backend runs (r23's grid-A, r24's batches 0 and 1) are reused by
identity, the interrupted ones regenerate. No evidence was edited; the
roots' driver logs show the retry.

Fifth incident (r23, 2026-09-06 20:08Z): with both e4b Gate-2 stages on
the host, r23's post-generation tail (every candidate row scored and held
in memory, 63.9 GB resident) was killed by the kernel's out-of-memory
handler while r24's stage was paused by the guard at 24 GB and r24's
backend kept generating; r23's tail had been made the preferred victim on
purpose, because its candidate rows were complete and scored and are
reused by identity on a retry, whereas r24's loss would have orphaned a
15-hour generation. The driver counted the disk-full failure as the first
attempt and stalled after this second one, so r23's driver was relaunched
chained behind r24's (on card 0, which r24 frees; placement is a runtime
argument, not bound by the root), and its Gate 2 resumes alone on the host
once r24 reports: two e4b tails do not fit in 91 GB, which is the same Gate-2
memory follow-up as before (score grid rows in two passes; do not hold
every scored candidate row at once).

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
and the calibration topics and seeds are the same in every root of a model
(§3.5), so n\*(f), m\*(f) and ι_A(f) should agree with the old roots up to
decoding nondeterminism. They do on 13 of the 14 supported frames:
identical n\*/m\* and ι_A(f) within 0.03 (about one topic-level SE):

| model | f | old n\*/m\*, ι_A(f) | new n\*/m\*, ι_A(f) |
|---|---:|---|---|
| qwen3-4b | 0 / 1 / 2 / 3 | 6/12 0.671 · 7/12 0.608 · 3/12 0.672 · 5/13 0.697 | 6/12 0.674 · 7/12 0.608 · 3/12 0.673 · 5/13 0.702 |
| qwen3-4b-instruct-2507 | 1 / 3 | 6/10 0.642 · 6/12 0.681 | 6/10 0.652 · 6/12 0.673 |
| qwen3-4b-instruct-2507 | 0, 2 | UNSUPPORTED (`GRID_RESOLUTION_INSUFFICIENT`: A's curve falls from 0.86 at severity 4 to 0.20 at 5, no whole band bracketed) | same, both frames |
| gemma-3n-e2b-it | 1 / 2 / 3 | 3/10 0.612 · 2/10 0.819 · 7/11 0.663 | 3/10 0.635 · 2/10 0.797 · 7/11 0.686 |
| gemma-3n-e2b-it | 0 | **1/8 0.754** | **8/8 0.642** |
| gemma-3n-e4b-it | 0–3 | 6/9 0.745 · 6/9 0.711 · 7/9 0.676 · 8/10 0.686 | 6/9 0.745 · 6/9 0.711 · 7/9 0.676 · 8/10 0.688 (identical in r23, r24 and the abandoned r18: e4b decodes deterministically here) |

The one exception is gemma-3n-e2b-it frame 0. Its A curve is nearly the
same in both roots and non-monotone (old 0.77 0.80 0.60 0.38 0.48 0.57 0.59
0.62 over severities 1–8; new 0.77 0.77 0.60 0.36 0.46 0.58 0.61 0.64), the
eligible severities are the same set {1, 2, 3, 6, 7, 8}, and the rule
selected the floor (1) in r12 and the top (8) in r16. That is the
operating-point rule on re-decoded grid rows (same topics and seeds; about
half the rows decode differently), not the pre-screen (no forwarding
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
| qwen3-4b-instruct-2507 | 3 | 3/0 l | 5/2 **L** | 4/1 l | 5/2 **L** | 3/36 → 6/35 | **gained by the forwarding rule**: on identical rows the legacy set is unsupported and both frame-specific sets are supported (r20 the same; in the third run r25 the legacy set also reaches 5/2, §3.5) |
| gemma-3n-e2b-it | 0 | 6/2 **L** | 5/2 **L** | 5/2 **L** | 5/2 **L** | 9/34 → 11/34 | unchanged status (operating point moved, §3.1) |
| gemma-3n-e2b-it | 1 | 6/2 **L** | 5/2 **L** | 5/2 **L** | 5/2 **L** | 11/31 → 12/37 | unchanged |
| gemma-3n-e2b-it | 2 | 3/0 l, coverage not identified | 3/0 l, coverage identified | 2/0 l | 3/0 l | 3/38 → 4/28 | unsupported under every policy (ι_A(f) ≈ 0.80 is the hardest frame); the spectrum arm is newly identified, which the comparator arms cannot attribute (coverage is not re-verdicted for them) |
| gemma-3n-e2b-it | 3 | 7/2 **L** | 7/2 **L** | 6/2 **L** | 7/2 **L** | 13/35 → 14/39 | unchanged; the frame's set carries one family more than the legacy set |
| gemma-3n-e4b-it | 0 | 5/2 **L** | 7/2 **L** | 4/1 l | 7/2 **L** | 8/40 → 9/39 | **kept by the forwarding rule**: on identical rows the legacy set is unsupported and both frame-specific sets are supported (replicated in r24) |
| gemma-3n-e4b-it | 1 | 6/2 **L** | 6/2 **L** | 5/2 **L** | 6/2 **L** | 8/38 → 9/41 | unchanged; the frame's set carries one family more than the legacy set |
| gemma-3n-e4b-it | 2 | 4/1 l | 4/1 l | 4/1 l | 4/1 l | 8/36 → 6/35 | unsupported under every policy in both designs |
| gemma-3n-e4b-it | 3 | 7/2 **L** | 8/2 **L** | 7/2 **L** | 8/2 **L** | 13/37 → 17/38 | unchanged; the frame's set carries one family more than the legacy set |

On every measured frame the frame's own set finds at least as many
LOCAL-valid rungs as the legacy set on the same rows except qwen3-4b frame
3 (one family fewer, still supported).

### 3.3 Per model: LOCAL eligibility, SPECTRUM coverage, compute

| model | LOCAL frames old → new | eligible (≥ 2 LOCAL frames) old → new | legacy set on new rows | proxy set on new rows | SPECTRUM frames old → new | generations old → new |
|---|---|---|---|---|---|---|
| qwen3-4b | {0, 3} → {0, 1, 2, 3} | yes → yes | {0, 1, 2, 3}, yes | {0, 1, 2, 3}, yes | {0, 1, 2, 3} → {0, 1, 2, 3} | 266,424 → 401,640 (+51 %) |
| qwen3-4b-instruct-2507 | {1} → {1, 3} | **no → yes** | {1}, **no** | {1, 3}, yes | {1, 3} → {1, 3} | 282,000 → 290,184 (+3 %) |
| gemma-3n-e2b-it | {0, 1, 3} → {0, 1, 3} | yes → yes | {0, 1, 3}, yes | {0, 1, 3}, yes | {0, 1, 3} → {0, 1, 2, 3} | 269,352 → 403,848 (+50 %) |
| gemma-3n-e4b-it | {0, 1, 3} → {0, 1, 3} | yes → yes | {1, 3}, yes | {0, 1, 3}, yes | {0, 1, 2, 3} → {0, 1, 2, 3} | 291,672 → 442,536 (+52 %) |

The eligibility change for qwen3-4b-instruct-2507 and the retention of
gemma-3n-e4b-it's frame 0 are the two outcomes that the comparator arm
attributes to the forwarding rule alone (2 of 14 supported frames; on the
other 12 the pooled set would have reached the same verdict on the same
rows). The generation
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
| gemma-3n-e4b-it | 0.86 · 0.94 · 0.94 · 0.76 | identical on 4/4 | identical on 4/4 |

So the two bases measure different rungs (up to 37 % of a frame's set) and
reach the same §13.15 verdict with the same family and backup counts on
all 14 measured frames. The evidence does not discriminate between them; the
registered choice rests on the precision argument in the design note (the
grid ι_A(f) has SE ≈ 0.02, the screen proxy drifts by up to 0.17), and it
is the choice the pilots ran.

### 3.5 Test-retest under the successor design (replicate roots)

A replicate is a second successor run of the same model at the same
commit. **It is a re-execution, not a resample**: the pilot's seeds are
derived from the study seed, the model and the stage, so a replicate root
screens, re-screens and calibrates the *same topics with the same seeds*
(the 192 calibration topic ids are identical between every pair of roots
of a model, v8 roots included). What differs between two runs is the
decoding: on the same prompts and seeds the vLLM stack on this hardware
does not reproduce the text row for row (first 3,000 grid-A rows, identical
answers: gemma-3n-e4b-it 3,000/3,000 and 2,999/3,000; qwen3-4b-instruct-2507
2,320 and 2,068; qwen3-4b 1,960 and 2,356; gemma-3n-e2b-it 2,032 and 1,533,
each pair being replicate-vs-first and first-vs-v8). So the replicates
answer a narrower question than topic resampling would: whether a frame's
status and forwarded set survive run-to-run decoding nondeterminism on
fixed topics. A topic-resampled replicate needs a distinct replicate seed
under the seed regime, which is a scientific choice and is left to the
researcher (§5). The counterfactual replay's 0.63–0.72 prediction was for
topic resampling and is not the quantity measured here.

| model | pair | n\*(f) first → replicate | LOCAL-supported frames | fam/bk first → replicate | forwarded-set Jaccard by frame |
|---|---|---|---|---|---|
| gemma-3n-e2b-it | r16 → r19 | 8, 3, 2, 7 → 8, 3, 2, 7 | {0, 1, 3} → {0, 1, 3} | 5/2, 5/2, 3/0, 7/2 → 6/2, 5/2, 3/0, 8/2 | 0.76 · 0.72 · 0.61 · 0.66 |
| qwen3-4b-instruct-2507 | r15 → r20 | f1 6, f3 6 → f1 6, f3 6 (f0: unsupported → supported at n\* = 4, ι_A = 0.85) | {1, 3} → {1, 3} | f1 6/2, f3 5/2 → f1 7/2, f3 5/2 (f0 3/0) | f1 0.69 · f3 0.76 |
| qwen3-4b-instruct-2507 | r15 → r25 (third run) | f1 6, f3 6 → f1 6, f3 6 (f0 unsupported again) | {1, 3} → {1, 3} | f1 6/2, f3 5/2 → f1 7/2, f3 5/2; **legacy set on r25's rows: f3 5/2** | f1 0.65 · f3 0.72 |
| qwen3-4b | r14 → r21 | 6, 7, 3, 5 → 6, 7, 3, 4 | {0, 1, 2, 3} → {0, 1, 2, 3} | 5/2, 5/2, 6/2, 6/2 → 6/2, 5/2, 6/2, 5/2 | 0.78 · 0.67 · 0.59 · 0.65 |
| gemma-3n-e4b-it | r23 → r24 | 6, 6, 7, 8 → 6, 6, 7, 8 | {0, 1, 3} → {0, 1, 3} | 7/2, 6/2, 4/1, 8/2 → 7/2, 6/2, 4/1, 8/2 | 0.88 · 1.00 · 0.97 · 0.97 |

gemma-3n-e2b-it replicates exactly at the status level: the same
operating point on every frame (frame 0 chose n\* = 8 in both successor
runs, against n\* = 1 in the v8 root, on the same topics and seeds — the
flip is decoding nondeterminism on a knife-edge curve, half of the grid
rows being re-decoded differently), the same three LOCAL-supported
frames, coverage identified on all four in both, ι_A(f) within 0.02, and
the legacy comparator unsupported on frame 2 in both (2/0 and 1/0). The
forwarded sets overlap at only 0.61–0.76 although the topics are the same:
roughly a third of a frame's set turns over from decoding noise alone,
while the families that survive to references do not.

qwen3-4b-instruct-2507 was run three times. Frame 3, the load-bearing
frame, is LOCAL-supported with 5 families and 2 backups under the frame's
set in all three runs. The legacy pooled set re-verdicted on the same rows
is 4/1 and unsupported in r15 and r20 but 5/2 in r25: under decoding
noise the pooled rule sits at the §13.15 margin on this frame (one family
or one backup either side of the threshold) while the frame-aware rule is
stably above it. So the honest statement of §3.2's attribution is not
"the pooled set fails here" but "the pooled set is marginal here and the
frame's set is not" — the eligibility that v8 denied this model follows
from the frame-aware rule in two of three re-executions and from either
rule in the third. Frame 1 stays supported (6/2 → 7/2 → 7/2, legacy the
same). At Gate 2, before any forwarding, frame 0 is unsupported for grid
resolution in r10, r15 and r25 (A's curve 0.855 at severity 4 against a
band edge) and supported in r20 at n\* = 4 with ι_A(f) = 0.85, the
hardest operating point of any frame, where it gives 3/0 (legacy 2/0); the
model's LOCAL frames are {1, 3} in every run. That frame-0 verdict is the operating-point rule on re-decoded grid
rows (same topics, same seeds, 23 % of the text different), the same
knife-edge as e2b frame 0 (§3.1), and belongs with decision 2 of §5.

qwen3-4b replicates in full: LOCAL-supported on all four frames in both
successor runs (5/2, 5/2, 6/2, 6/2 → 6/2, 5/2, 6/2, 5/2; coverage
identified on all four in both), the legacy set re-verdicted on the same
rows also supported on all four in both, the same n\* on frames 0–2 and
n\* 5 → 4 on frame 3 with ι_A(f) unchanged (0.702 → 0.701), and
forwarded-set overlap 0.59–0.78. So the v8-to-successor gain on frames 1
and 2 (§3.2), which the comparator could not attribute to the rule, is at
least stable under re-execution of the successor design.

Across the four models, every LOCAL verdict on every measured frame
agrees between the successor runs (14 supported frames, 0 disagreements,
2507 three times), and the sets overlap at 0.59–0.78 on identical topics.
The comparator verdicts are less stable than the frame's own: on 2507
frame 3 the pooled set crosses the threshold in one run of three. The
instability lives one stage earlier, in the operating-point rule on the
grids (§3.1 and the 2507 frame-0 flip above), which the pre-screen does
not touch and which decoding noise alone can move. gemma-3n-e4b-it's
decoding is effectively deterministic on this stack (3,000 of 3,000 grid
rows identical between its v8 root and r24), so its successor operating
points equal v8's exactly and its replicate pair (r23 → r24) tests the
pipeline's determinism rather than its noise: identical operating points,
identical family and backup counts on every frame, forwarded sets at
0.88–1.00, and on frame 0 the legacy set is 4/1 and unsupported in both
runs while the frame's set is 7/2 — the second rule-attributed retention
(§3.2), reproduced.

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
- The suites write large per-worker fixture trees under `/tmp` and do not
  clean them; two full runs filled the root filesystem (§2, fourth
  incident). Delete `/tmp/pytest-of-*` after a run on this host.
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

*All four models have a first successor run and a replicate, 2507 a third run; the v8-design control r26 (§2) is appended when it lands.*

**RESEARCHER_DECISION_REQUIRED.** Nothing technical blocks a freeze under
the registered rule: every stage from `REGIME_SCREEN` regenerates in fresh
roots, the contracts and readiness item 11 refuse a v8 pilot, the frozen
root `dci1v8-confirm-r2` is superseded for this successor design and not
altered, and the pilots give the intended effect (frame-specific sets that
are at least as supported as the pooled set on the same rows, and two
frames — 2507 f3 and e4b f0 — where the frame's set is supported and the
pooled set is not on identical rows, the pooled set being marginal there:
on 2507 f3 it crosses the threshold in one of three re-executions) and
the effect replicates (§3.5: 14 of 14 LOCAL verdicts agree between the
successor runs of every model, under decoding noise on fixed topics). Three decisions remain the researcher's
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
   unchanged rule and on the *same* topics and seeds: decoding
   nondeterminism alone moves these frames. A successor confirm root
   carries whichever the pilot it binds read; whether that is acceptable,
   or the rule's behaviour at band edges and on non-monotone curves should
   be resolved first, is a question about the operating-point rule, not
   this redesign.
4. **What a replicate should vary.** Every root of a model shares its
   topics and seeds, so the replicates of §3.5 measure decoding noise, not
   topic sampling. If topic-resampled stability is wanted before a freeze,
   a replicate needs a distinct replicate seed under the seed regime, which
   is a governed choice and is not made here.
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
