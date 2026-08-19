You are taking over an active research codebase implementing the DCI study.

You have NO prior conversational context. Treat the repository, its committed documentation, run manifests, generated artifacts, logs, tests, preregistrations, amendments, and provenance records as the source of truth for what has actually been completed.

Your job is to:

1. reconstruct the current state of the project;
2. determine which steps below have already been completed correctly;
3. execute every remaining step in dependency order;
4. repair implementation or provenance defects where specified;
5. run all required validation;
6. leave the repository in a reproducible, scientifically auditable state;
7. produce a final completion report distinguishing:
   - completed before this session,
   - completed by you,
   - blocked by a genuine external dependency,
   - scientifically unresolved.

Do not rerun expensive experiments merely because they appear in this prompt. First establish whether valid outputs already exist.

Do not infer completion from filenames alone. Verify completion from manifests, hashes, configurations, logs, row counts, provenance, tests, and analysis outputs.

Do not ask the user questions if the repository contains enough information to resolve them. Inspect the codebase and make the best evidence-based decision.

Do not fabricate human judgments, researcher attestations, external annotations, experimental results, approval records, or missing data.

Do not weaken preregistered criteria merely to make a gate pass.


============================================================
A. SCIENTIFIC CONTEXT
============================================================

The historical DCI design studies interactions among constraints.

Important notation:

- A = designated target constraint.
- B = focal constraint whose effect/interference is of interest.
- R = matched reference constraint replacing B.
- S = one or more background constraints.
- X_c = whether constraint c is satisfied.
- F_A = failure on A, historically derived from deterministic verifier S0.
- Historical primary contrast:
      A + B + S
  versus
      A + R + S.

A positive historical effect typically meant that introducing B rather than R increased failure on A.

However, subsequent construct auditing identified serious reasons not to assume this historical target-specific contrast is the right primary scientific quantity.

The emerging primitive outcome is the full joint compliance/delivery vector:

    X = (X_1, ..., X_n)

with each constraint scored separately.

A more informative candidate phenomenon is:

    compositional delivery loss

meaning that a constraint becomes less likely to be delivered when other constraints are simultaneously imposed.

A useful directional quantity is reciprocal delivery loss:

    D(c <- G)

where c is a constraint and G is the additional constraint or set of constraints placed alongside it.

Operationally, use the repository's canonical definition if one already exists. If it does not, the natural starting quantity is:

    D(c <- G)
      = P(c satisfied | c alone)
        - P(c satisfied | c composed with G)

with appropriate cell matching and uncertainty estimation.

Do not silently introduce this exact formula if project documentation has since adopted a more precise definition. Locate and use the latest valid definition.

Important existing evidence motivating the redesign:

- In at least one clean load-2 comparison:
    B alone satisfaction was about 0.667;
    B with A fell to about 0.150;
    A alone was 1.000;
    A with B remained 1.000.

  Thus there can be a large asymmetric delivery loss that the historical
  A-targeted tau cannot detect because A is at ceiling.

- Across a broader census, B has often been intrinsically harder than R.

- Pooled compositional degradation has occurred for both focal and reference
  constraints, so generic compositional load remains a leading alternative
  explanation.

- Historical target-effect estimates have shown sign reversals under changes
  in instruction order, checkpoint, and segmentation convention.

- Some apparent effects are sensitive to punctuation/segmentation conventions,
  especially semicolon-related cases.

Therefore:

DO NOT assume "directional constraint interference" is already established as a
stable pairwise causal property.

The most important unresolved discriminating question is:

    Does B specifically deteriorate much more when combined with A
    than when B is combined with other constraints such as R or S?

The identified missing experiment is approximately 800 generations covering:

    B + R
    B + S

without sentence-count target A.

If B deteriorates similarly under R/S and under A, the evidence favors generic
compositional delivery degradation.

If deterioration of B is materially and reproducibly larger specifically when
paired with A than with comparable R/S partners, that supports a more
constraint-identity-specific interaction.

This experiment is scientifically prior to launching another large legacy
A+B+S versus A+R+S confirmatory study.


============================================================
B. CURRENT MEASUREMENT ARCHITECTURE TO VERIFY
============================================================

The repository was previously reported to implement the following architecture.
DO NOT assume it remains true. Verify every item.

1. Primary behavioral scores are deterministic Python functions of generated
   response text and fixed severity/configuration.

2. Deterministic verdicts are computed during generation and stored together
   with a verifier source hash.

3. Historical F_A comes only from S0.

4. S0 counts occurrences using the project's exact lexical semantics.
   Historically, this involved lowercase alphabetic runs, which means unusual
   strings such as concatenated or hyphenated forms may behave differently from
   ordinary natural-language interpretation.

5. S1/S2/S3 are robustness/failure-taxonomy measurements and should not silently
   redefine F_A.

6. Added-constraint compliance/uptake is separately stored, historically as
   something like `added_pass`.

7. "Pass" for some <=-style constraints may literally mean non-violation.
   Empty or degenerate responses can therefore sometimes mechanically pass.
   Preserve non-behavioral/degeneracy diagnostics and do not interpret such
   cases as meaningful engagement without checking them.

8. An autorater using `openai/gpt-oss-20b` exists for Gate 1 measurement
   validation.

9. The autorater is VALIDATION-ONLY.
   It must NEVER overwrite deterministic behavioral outcomes or F_A.

10. Autorater judgments must remain in separate artifacts.

11. Autorater disagreement with deterministic verification is diagnostic.
    It must not create a hidden write path into primary scoring.

12. The registered autorater configuration previously used:
      - pinned model revision;
      - vLLM;
      - harmony formatting;
      - versioned prompt/parser;
      - greedy decoding;
      - reasoning configuration;
    but inspect the actual current freeze/configuration rather than assuming
    these exact values remain canonical.


============================================================
C. KNOWN AUTORATER FORENSICS TO VERIFY
============================================================

A separate diagnostic forensics workflow previously investigated autorater
stability.

The following results were reported. Verify their artifacts rather than
recomputing them unnecessarily.

1. Low output caps caused truncation at high reasoning effort.

2. Approximate zero-cap-stop settings were found around:
      low:    4096
      medium: 8192
      high:   8192

3. Concurrent serving produced unacceptable repeated-run label instability.

4. Serialized serving with concurrency = 1 was reported to produce exact
   repeatability on the tested samples.

5. Prompt rendering mismatch and parser behavior were ruled out as the primary
   sources of disagreement.

6. The remaining source was batch-composition-dependent generation/numerical
   nondeterminism.

7. Therefore autorater measurements should only be treated as reproducible
   under a frozen deterministic execution context, such as serialized serving
   or an equivalently demonstrated fixed-composition offline path.

8. Low reasoning effort was rejected.

9. The remaining comparison was:

      medium reasoning @ 8192
      versus
      high reasoning @ 8192

   under serialized deterministic execution.

10. A blinded human calibration set contained 56 items.

11. The human annotator completed all 56 with no abstentions.

12. Human versus deterministic verifier agreement was reported as:

      56 / 56 = 100%

13. The human labels were performed by a study author.

This is valid blinded human calibration evidence, but it is NOT independent
external human validation.

Never relabel these author judgments as independent human validation.


============================================================
D. FIRST TASK: RECONSTRUCT CURRENT STATE
============================================================

Before modifying anything, perform a repository-wide state audit.

Inspect at minimum:

- git status;
- branch and commit;
- recent commits relevant to DCI v3;
- uncommitted changes;
- preregistration documents;
- amendments;
- implementation prompts;
- experiment manifests;
- freeze files;
- Gate 1 artifacts;
- autorater forensics artifacts;
- human calibration artifacts;
- sealed final-check metadata;
- verifier source hashes;
- generated datasets;
- run logs;
- analysis outputs;
- provenance manifests;
- tests;
- documentation describing deprecated/foreign data;
- any existing construct-audit or redesign notes;
- any B+R / B+S experiment outputs;
- any newer preregistration superseding the state described above.

Search by concept, not only by expected filenames.

Build an internal completion matrix for every phase in this prompt.

For each purportedly completed experiment verify:

- configuration;
- model;
- revision;
- seed;
- serving mode;
- concurrency;
- output cap;
- prompt version;
- parser version;
- verifier hash;
- sample identifiers;
- row count;
- uniqueness;
- expected conditions;
- provenance;
- whether outputs are committed or otherwise durably recorded;
- whether the associated analysis actually corresponds to those rows.

If the repository contains newer scientifically justified work that supersedes an
instruction below, follow the newer frozen/preregistered state, but document the
difference explicitly in the final report.

Do not discard or overwrite existing scientific artifacts.


============================================================
E. REPOSITORY SAFETY AND REPRODUCIBILITY
============================================================

Before substantive modifications:

1. Ensure the working tree state is understood.

2. Preserve all pre-existing uncommitted work.
   Never reset, clean, or overwrite unrelated changes.

3. If appropriate for the repository workflow, create a dedicated branch or
   worktree for these changes.

4. Record:
   - starting commit;
   - environment;
   - package versions;
   - GPU/runtime information;
   - model revisions;
   - relevant configuration hashes.

5. Run the relevant existing test suites before modifications to establish a
   baseline.

6. Do not manually edit generated scientific result files to make tests pass.

7. Prefer deterministic scripts that regenerate derived artifacts.

8. Preserve an auditable command log for every experiment you run.


============================================================
F. PHASE 1: FINISH THE E8 MEDIUM-VS-HIGH COMPARISON
============================================================

Determine first whether this work has already been completed.

The previously unfinished task was to rerun:

    medium @ 8192
    high   @ 8192

on the SAME 56 existing human-labelled calibration items, using the frozen
serialized deterministic serving context.

If complete and valid:
- verify the report;
- verify the sample is exactly the intended 56;
- verify human labels were not altered;
- verify output cap = 8192;
- verify serving execution satisfies the demonstrated deterministic context;
- verify the candidate configurations are otherwise matched;
- reuse the result.

If incomplete:
execute it.

Requirements:

- Do not create new human labels.
- Do not inspect or use the sealed 40-item final-check set.
- Use precisely the existing 56-item human calibration sample.
- Use the repository's frozen prompt and parser.
- Use concurrency = 1 or the exact deterministic execution configuration
  previously validated.
- Preserve candidate outputs separately.
- Do not allow autorater judgments to alter deterministic verifier scores.

For medium and high compute:

- valid-judgment coverage;
- overall agreement with the 56 human labels;
- per-class agreement;
- confusion matrix;
- false-positive/false-negative counts;
- any abstention/parse-failure count;
- exact paired discordant items;
- deterministic reproducibility check;
- truncation/cap-stop incidence;
- response/generation failures;
- if already used by project, Wilson/binomial uncertainty intervals.

Because medium and high are evaluated on the same items, report the comparison
as paired rather than treating observations as independent.

If the repository already specifies a paired test, use it.

Otherwise report at least:
- medium-only errors;
- high-only errors;
- both-wrong;
- both-correct;
- exact discordant-item table.

Do not select a configuration from aggregate accuracy alone if coverage,
truncation, instability, or systematic error makes it invalid.

Selection hierarchy:

1. valid deterministic execution;
2. adequate output cap / absence of problematic truncation;
3. valid parsing and coverage;
4. agreement with human labels;
5. simpler/lower-cost setting if performance is practically indistinguishable.

Document the chosen configuration and rejected alternative.


============================================================
G. PHASE 2: FREEZE GATE 1 VALIDATION CONFIGURATION
============================================================

After E8 is complete, inspect the latest preregistration/amendment for the exact
Gate 1 procedure.

Freeze every parameter needed for reproducibility, including as applicable:

- autorater model identifier;
- exact revision;
- reasoning setting;
- max output tokens;
- temperature / decoding configuration;
- serving implementation;
- concurrency;
- batching/fixed-composition rules;
- prompt version/hash;
- parser version/hash;
- failure handling;
- retry policy;
- escalation policy;
- deterministic verifier hash;
- human-comparison sample identifier;
- software/runtime versions where required.

Write this freeze through the repository's existing mechanism.

Do not invent a parallel mechanism if one already exists.

If Gate 1 requires an explicit researcher approval record:

- determine whether the approval is merely an explicit acknowledgement of
  objective evidence or a human scientific attestation;
- if objective and the repository workflow permits it, generate the required
  evidence-backed record;
- if it requires an actual human attestation that does not already exist, DO
  NOT forge it;
- instead leave the gate blocked with a precise machine-readable and
  human-readable description of the missing attestation.

Check every registered model rather than assuming a single global Gate 1 record
is sufficient.

If some model-specific Gate 1 artifacts are missing, complete them according to
the current registered workflow before continuing.


============================================================
H. PHASE 3: RUN THE SEALED 40-ITEM FINAL CHECK
============================================================

A 40-item reserved final-check set was previously created from items that had
not been used in diagnostics.

The historical seal hash was:

    f8831598e275487037e6e51cd85e1df2b33c8e359d13836e500e9ab7b881d7a3

Do not blindly trust this value. Locate the actual current sealed artifact and
verify the repository's canonical hash.

CRITICAL:

Do not inspect item content, labels, composition, or results until ALL
autorater choices are frozen.

Before unsealing verify that the following can no longer be changed in response
to final-check performance:

- reasoning setting;
- cap;
- serving mode;
- concurrency/batching;
- prompt;
- parser;
- retry/failure handling;
- escalation rules.

If the final check has already been validly executed after such a freeze:
do not rerun it merely to obtain a better result.

If not:
run it exactly once under the frozen selected configuration.

Record:

- seal verification before opening;
- timestamp/commit/configuration;
- item IDs;
- prediction outputs;
- coverage;
- agreement;
- per-class diagnostics;
- parsing failures;
- truncation;
- any unexpected runtime issue.

Do not tune anything after observing this set.

If performance exposes a failure severe enough to invalidate the measurement
procedure, mark Gate 1 failed/unestablished. Any subsequent redesign must use a
NEW held-out final-check set. Never reuse this set for iterative tuning.


============================================================
I. PHASE 4: HANDLE HUMAN-VALIDATION STATUS CORRECTLY
============================================================

Inspect the latest amendments.

There have historically been TWO distinct human-evidence pathways:

1. Author-performed blinded calibration:
   the existing 56-item sample.

2. Production independent human audit:
   historically one independent annotator per model under an amendment,
   with class-wise disagreement criteria.

Do not conflate them.

If valid independent human-audit results already exist:
- validate their provenance;
- run the registered analysis;
- report the correct measurement status.

If an external independent annotator is not available and no such labels exist:
- do NOT fabricate them;
- do NOT label the author's 56 judgments "independent";
- preserve the correct status, such as HUMAN_VALIDATION_UNAVAILABLE or the
  repository's current terminology;
- proceed only to stages that the current preregistration permits without
  independent validation.

If a production human-audit UI/workflow already exists, reuse it.
Do not rebuild it unnecessarily.

If the workflow has a registered class-wise Wilson disagreement criterion,
preserve it exactly. Historically this was approximately:

    one-sided 95% Wilson upper bound on disagreement <= 0.10

for an established class, with sample-size handling encoded in the amendment.

Use the actual current amendment as authoritative.


============================================================
J. PHASE 5: FIX THE POST-GATE-1 VERIFIER HASH-BINDING DEFECT
============================================================

A known implementation defect must be fixed unless it already has been fixed.

Historical problem:

- verifier changes before Gate 1 were detected;
- a Gate 1 record stored verifier provenance;
- but after Gate 1 approval, a later committed verifier change could
  potentially allow downstream Gate 2 / freeze / confirmatory / analysis
  commands to run using a verifier different from the Gate-1-validated one.

This must fail closed.

Implement a central invariant:

    current deterministic-verifier identity/hash
        ==
    verifier identity/hash frozen by Gate 1

for every downstream stage whose scientific validity depends on the Gate 1
measurement freeze.

Apply the guard to all relevant entry points, which may include:

- Gate 2A;
- Gate 2B;
- experiment freeze;
- confirmatory generation;
- scoring;
- confirmatory analysis;
- unmasking;
- report generation;
- any resume/restart command capable of introducing newly scored rows.

Inspect the actual architecture and cover all real execution paths.

Requirements:

1. Use a canonical verifier hash implementation.
2. Include every source/configuration component that can change verifier
   semantics.
3. Store the frozen hash in a canonical Gate 1 artifact.
4. Compare before downstream work begins.
5. Produce a clear error on mismatch.
6. Never silently update the frozen hash.
7. Require explicit invalidation/recalibration if verifier semantics change.
8. Preserve the ability to audit old already-scored artifacts using their
   recorded historical hash where appropriate, without falsely treating them as
   newly valid under the current verifier.

Add regression tests:

A. unchanged verifier after Gate 1:
   downstream stage succeeds.

B. committed semantic verifier modification after Gate 1:
   every protected downstream stage fails closed.

C. revert to frozen verifier:
   downstream stage succeeds again.

D. irrelevant source change:
   does not produce a false verifier mismatch if the canonical hashing scheme
   intentionally excludes it.

E. stored generated verdict provenance:
   remains traceable to the verifier that actually generated it.

Run the targeted and full relevant test suites.


============================================================
K. PHASE 6: AUDIT AND CORRECT HISTORICAL PROVENANCE
============================================================

A previous provenance audit reportedly found that at least one committed
`reasoning_rows.csv`-like artifact was derived entirely from files marked
DEPRECATED/FOREIGN and contained a very high duplicate-replicate rate.

Treat this as a serious provenance issue.

First verify whether it remains true.

Trace:

source files
    -> aggregation script
    -> reasoning_rows / equivalent
    -> derived statistics
    -> report/table/figure/claim

Check:

- manifest source classification;
- run IDs;
- duplicate generations;
- duplicate replicate IDs;
- effective sample size;
- whether rows came from foreign/deprecated experiments;
- whether any current report still cites these results as valid evidence.

If the issue has already been corrected:
verify the correction and do nothing destructive.

If not:

1. Do not delete historical artifacts.
2. Mark contaminated artifacts/report sections as superseded or invalid for
   confirmatory inference.
3. Add a clear provenance/correction notice.
4. Regenerate any derived report from valid data if valid source data exists.
5. If valid replacement data do not exist, remove the quantitative claim rather
   than silently substituting unsupported numbers.
6. Ensure current analysis pipelines cannot accidentally ingest
   DEPRECATED/FOREIGN sources as registered evidence.
7. Add tests or validation guards where practical.

Document the effective sample-size problem explicitly.


============================================================
L. PHASE 7: RUN THE MISSING ~800-GENERATION DISCRIMINATING EXPERIMENT
============================================================

This is the most important new scientific experiment.

First search the repository for evidence that it has already been executed.

Look for conditions equivalent to:

    B + R
    B + S

WITHOUT target A.

Verify that any candidate existing experiment is genuinely comparable to the
relevant A+B condition rather than merely sharing a label.

Required objective:

Determine whether the large observed deterioration in delivery of B is
specific to pairing B with A or is mostly generic degradation caused by adding
another constraint.

Use approximately 800 generations TOTAL unless the current repository contains
a subsequently frozen design specifying a different exact N.

If no exact allocation has already been specified, use a balanced design such
as approximately:

    400 B+R
    400 B+S

while preserving the relevant crossing over tasks, severities, paraphrases,
orders, seeds, and other nuisance dimensions.

Whenever possible, use paired/matched cells and seeds corresponding to the
cleanest existing:

    B alone
    B + A

data.

Do not regenerate valid B-alone or B+A observations merely to inflate the
sample. Reuse them only if:

- provenance is valid;
- verifier hashes are appropriate;
- configuration is comparable;
- no data-contamination issue applies;
- they are not from an explicitly deprecated/foreign source.

If comparability cannot be established, rerun the minimal required companion
cells under one coherent configuration rather than mixing incompatible data.

Design requirements:

1. No target A in the new B+R and B+S conditions.

2. Use deterministic behavioral verification.

3. Record the complete constraint-compliance vector, not only one target.

4. Preserve graded verifier statistics where available.

5. Track:
   - empty/degenerate response;
   - truncation;
   - generation failure;
   - non-behavioral outcome;
   - order;
   - task;
   - severity;
   - paraphrase;
   - checkpoint/model;
   - seed;
   - verifier hash;
   - exact constraint identities.

6. Randomize/counterbalance order according to the valid experimental
   conventions already in the repository.

7. Do not use the autorater as the primary scorer.

8. Keep exploratory companion-condition data clearly distinguished from later
   preregistered confirmatory evidence.

Primary analysis:

Estimate, at minimum:

    D(B <- A)
    D(B <- R)
    D(B <- S)

using the project's canonical solo baseline for B.

Also estimate reciprocal effects where the necessary solo baselines exist:

    D(A <- B)
    D(R <- B)
    D(S <- B)

Report uncertainty.

Use cell-aware bootstrap, paired estimates, mixed/logistic models, or other
methods already established in the codebase where appropriate.

Do NOT blindly pool across order/checkpoint/configuration when existing evidence
shows substantial heterogeneity.

At minimum stratify or diagnose:

- order;
- model/checkpoint;
- severity;
- task/background family;
- segmentation/verifier convention where scientifically relevant.

Report:

- solo compliance;
- composed compliance;
- absolute delivery loss;
- relative delivery loss if useful;
- full joint-state frequencies;
- joint success;
- reciprocal/asymmetric loss;
- confidence intervals;
- cell counts;
- missingness/failures;
- sensitivity to known boundary cases.

Do not convert this exploratory experiment into a binary "success" result using
a threshold invented after seeing the data.


============================================================
M. PHASE 8: MAKE THE CONSTRUCT DECISION
============================================================

After Phase 7, write a machine-readable and human-readable construct decision.

There are three possible high-level outcomes.

CASE 1: Generic compositional delivery loss

If:

    D(B <- R) and/or D(B <- S)

is broadly comparable to:

    D(B <- A)

and there is no robust evidence that A uniquely harms B beyond plausible
generic composition effects, then:

- do not continue presenting the phenomenon primarily as a special A/B
  directional-interference effect;
- adopt "compositional delivery loss" or the repository's latest equivalent
  construct;
- use the complete compliance vector as the primitive measurement;
- make reciprocal delivery loss the primary estimand;
- demote historical target-specific tau to a secondary diagnostic;
- treat identity-specific interference as unestablished.

CASE 2: Constraint-identity-specific interaction

If B degradation when paired with A is materially larger and robustly distinct
from degradation with comparable R/S partners:

- retain a constraint-specific interaction hypothesis;
- explicitly model reciprocal directionality;
- do not infer a universal pairwise property if effects still depend on order,
  model, severity, or background;
- define the estimand conditionally on the relevant experimental context.

CASE 3: Ambiguous

If uncertainty, measurement sensitivity, heterogeneity, or inadequate
comparability prevents either interpretation:

- mark the construct unresolved;
- identify the minimum additional experiment required;
- do not launch a large confirmatory run under an unjustified interpretation.

If the repository already defines an equivalence region or smallest
scientifically meaningful difference, use it.

If it does not, do not manufacture a post-hoc confirmatory threshold from these
exploratory results. Instead use Phase 7 to inform a prospectively frozen margin
for the NEXT preregistered study.


============================================================
N. PHASE 9: REDESIGN THE STUDY AROUND THE RESULT
============================================================

Only after the construct decision, update the next-study design.

Follow this dependency order:

1. Define the phenomenon/construct.

2. Define primitive observations.

3. Define primary and secondary estimands.

4. Find an informative operating regime with adequate headroom.

5. Establish measurement validity in that regime.

6. Select/calibrate reference conditions if references are scientifically
   necessary.

7. Define outcomes, exclusions, missingness rules, and analysis.

8. Establish sample-size/power justification.

9. Run targeted adversarial/pilot checks.

10. Freeze/preregister the confirmatory study.

Do not reverse this order by choosing a convenient reference before deciding
what quantity is being identified.


============================================================
O. OPERATING-REGIME REQUIREMENTS
============================================================

A recurring problem has been target constraints near ceiling, making some
effects unidentified or structurally tiny.

Before confirmatory execution, verify that the selected regime provides
headroom.

For every primary constraint:

- estimate solo performance;
- estimate composition performance in pilot cells;
- identify floor/ceiling behavior;
- inspect variance;
- inspect generation failures;
- inspect whether the model actually attempts the constraint.

Do not proceed with an estimand whose outcome is essentially fixed at 0 or 1
throughout the intended experimental region.

If the existing severity grid does not produce an informative regime, expand or
adjust it prospectively.

Do not call this a failure of the model or hypothesis. Report it as
"regime not found" or the project's current terminology.


============================================================
P. REFERENCE-CONDITION REQUIREMENTS
============================================================

If the chosen scientific question still requires R-like controls:

Do not assume matching on nominal textual difficulty is sufficient.

Assess reference candidates on the nuisance dimensions needed for causal
interpretation, including where measurable:

- solo satisfaction;
- compositional degradation;
- token/length burden;
- lexical versus relational character;
- order sensitivity;
- output-format pressure;
- verifier type;
- response-length effects;
- uptake/attempt rate;
- degeneracy susceptibility.

Do not call a reference matched if B is much harder than R in solo use and that
difference materially affects the interpretation.

If no adequately matched reference exists, allow NOT_IDENTIFIED or the current
project equivalent rather than forcing a comparison.


============================================================
Q. OUTCOME AND ANALYSIS REQUIREMENTS
============================================================

Unless superseded by a scientifically justified current specification, the next
design should preserve:

PRIMARY DATA:
    full per-constraint compliance vector X.

PRIMARY EFFECT:
    reciprocal delivery-loss quantities relevant to the selected construct.

SECONDARY:
    joint success;
    redistribution among joint states;
    historical target-specific tau;
    asymmetry measures;
    graded verifier statistics;
    robustness under alternate segmentation conventions.

Where applicable calculate:

    joint-state redistribution rho

and the project's existing interaction/asymmetry statistic such as Gamma, but
do not promote them to primary status unless prospectively justified.

Explicitly model or stratify known moderators:

- instruction order;
- checkpoint/model;
- composition load;
- background constraints;
- reasoning/execution condition;
- constraint family.

Do not report a single pooled number as a stable intrinsic pairwise parameter
when important sign reversals exist across these dimensions.


============================================================
R. SEGMENTATION AND CONSTRUCT-VALIDITY CHECKS
============================================================

Known boundary sensitivity has involved punctuation/segmentation, including
semicolon cases.

Before the next confirmatory freeze:

1. enumerate verifier boundary cases;
2. create deterministic unit tests;
3. run a targeted adversarial corpus;
4. quantify how often real generated samples hit these cases;
5. compare primary convention with prespecified reasonable alternatives;
6. ensure these alternatives are robustness analyses rather than silently
   switching the scoring rule after results are seen.

For the S0 word-count construct, explicitly test examples such as:

- ordinary punctuation around the target word;
- concatenated copies;
- hyphenation;
- Unicode punctuation;
- Unicode lookalikes if relevant;
- zero-width characters if relevant;
- capitalization;
- sentence-boundary punctuation.

The goal is not to make the verifier mimic arbitrary human intuition.
The goal is to know exactly what scientific construct the deterministic rule
operationalizes and how often edge cases matter empirically.


============================================================
S. POWER AND SAMPLE-SIZE PLANNING
============================================================

Once the construct, operating regime, and primary estimand are frozen:

- estimate variance/effect-size ranges from exploratory data without treating
  exploratory estimates as confirmatory evidence;
- choose the confirmatory N prospectively;
- account for blocking/pairing;
- account for multiple primary contrasts if applicable;
- account for model/checkpoint stratification;
- account for invalid generations/missingness;
- preserve any existing FDR/multiple-comparison policy.

Write the justification into the preregistration before confirmatory data are
generated.


============================================================
T. TARGETED PILOT / ADVERSARIAL CHECKS BEFORE CONFIRMATORY RUN
============================================================

Run the minimum pilot needed to demonstrate that the redesigned study is
operational.

Check:

- solo headroom;
- composed headroom;
- reference comparability;
- order balance;
- verifier determinism;
- boundary-case prevalence;
- non-behavioral/empty-response prevalence;
- duplicate generations;
- manifest provenance;
- cell balance;
- seed uniqueness;
- schema completeness;
- missingness;
- hardware/runtime stability.

Do not expand this pilot into an unregistered confirmatory dataset.


============================================================
U. WRITE/FREEZE THE NEXT PREREGISTRATION
============================================================

Only after the preceding design questions are resolved, produce/update the
canonical preregistration.

It must be self-contained and must not depend on obsolete v2 implementation
documents for required semantics.

Include:

- scientific question;
- construct;
- hypotheses;
- experimental unit;
- models/checkpoints;
- task population;
- constraint population;
- treatments/conditions;
- randomization;
- severity selection;
- operating-regime criteria;
- deterministic verifiers;
- verifier freeze/hash;
- Gate 1 evidence;
- human-validation status;
- primary outcome vector;
- primary estimand;
- secondary estimands;
- reference-calibration procedure;
- exclusions;
- invalid generations;
- missingness;
- duplicate handling;
- sample-size justification;
- uncertainty estimation;
- multiple-comparison policy;
- robustness analyses;
- segmentation sensitivity;
- stopping rules;
- gate criteria;
- masking/unmasking;
- provenance requirements;
- allowed deviations/amendment procedure;
- claims licensed by each possible result.

Generate a changelog from the previous canonical preregistration.

Explicitly state which historical DCI claims or estimands have been demoted,
retained, replaced, or abandoned.


============================================================
V. CONFIRMATORY EXECUTION
============================================================

Only proceed if ALL required gates for the redesigned study are satisfied.

If the construct remains unresolved, measurement is unestablished, operating
regime cannot be found, reference calibration fails, or a mandatory external
human dependency is unavailable:

STOP the confirmatory pipeline cleanly.

Produce the appropriate terminal status rather than bypassing the gate.

If all prerequisites pass:

1. freeze the experiment;
2. record commit/configuration/environment hashes;
3. generate the registered confirmatory sample;
4. preserve deterministic verdicts and verifier provenance at generation;
5. maintain masking where required;
6. validate row counts and cell balance;
7. detect duplicates;
8. detect missing generations;
9. enforce verifier-hash binding;
10. run registered analyses only;
11. run registered robustness analyses;
12. unmask only according to the protocol;
13. produce final tables/figures/report;
14. make no unregistered primary-analysis changes after inspecting outcomes.

Any exploratory analyses after unmasking must be labeled exploratory.


============================================================
W. TESTING REQUIREMENTS
============================================================

Run existing tests before making changes.

After changes run, at minimum:

1. deterministic verifier tests;
2. Gate 1 calibration tests;
3. autorater parser/prompt tests;
4. human-review workflow tests if touched;
5. verifier hash-binding regression tests;
6. manifest/provenance tests;
7. experiment-schema tests;
8. randomization/cell-balance tests;
9. duplicate detection tests;
10. analysis tests;
11. full v3/current-study test suite;
12. any legacy tests expected to remain supported.

Do not declare completion if tests fail.

For any failure:

- determine whether it predates your changes;
- determine whether it reflects an obsolete expectation;
- fix the implementation or update an obsolete test only when scientifically
  justified;
- document the reasoning.


============================================================
X. SCIENTIFIC INTEGRITY INVARIANTS
============================================================

These are hard requirements.

1. Autorater judgments never become primary behavioral scores.

2. Human labels are never fabricated.

3. Author-performed human labels are never described as independent external
   validation.

4. The sealed final-check set is not used for tuning.

5. A final-check set is never rerun after failure to optimize the configuration.

6. Verifier semantics cannot change downstream without invalidating the Gate 1
   freeze.

7. Deprecated/foreign artifacts cannot silently enter registered evidence.

8. Duplicate rows cannot count as independent replicates.

9. Ceiling/floor regimes cannot be presented as informative null effects.

10. "Constraint pass" caused by an empty/degenerate output must not be
    interpreted as genuine successful delivery without the corresponding
    behavioral-validity check.

11. Exploratory evidence is not relabeled confirmatory.

12. No post-hoc threshold is described as preregistered.

13. Do not force a "directional interference" interpretation if the B+R/B+S
    experiment supports generic compositional degradation.

14. Do not average away sign reversals across important moderators and describe
    the result as a stable pairwise property.

15. Do not silently change scoring conventions after seeing results.


============================================================
Y. REQUIRED FINAL DELIVERABLES
============================================================

When finished, produce one concise but complete final report.

It must contain:

1. INITIAL STATE

   - starting branch/commit;
   - dirty files found;
   - relevant existing artifacts;
   - which requested steps were already complete.

2. CHANGES MADE

   List each code/config/test/document change and why it was necessary.

3. EXPERIMENTS EXECUTED

   For each:
   - command;
   - configuration;
   - model/revision;
   - N;
   - seeds;
   - execution context;
   - output artifact;
   - provenance/hash;
   - validation result.

4. GATE 1 STATUS

   For each registered model:
   - deterministic verifier status;
   - E8 status;
   - chosen autorater configuration;
   - final-check status;
   - author-human calibration status;
   - independent-human-validation status;
   - approval/gate status;
   - exact blocker if not established.

5. VERIFIER FREEZE STATUS

   - frozen hash;
   - where it is stored;
   - downstream stages protected;
   - tamper regression-test results.

6. PROVENANCE CORRECTION

   - whether contaminated historical evidence was confirmed;
   - affected artifacts/claims;
   - duplicate/effective-N finding;
   - correction/superseded notice added;
   - replacement analysis if available.

7. B+R / B+S DISCRIMINATING EXPERIMENT

   Report:
   - B-alone compliance;
   - B+A compliance;
   - B+R compliance;
   - B+S compliance;
   - D(B <- A);
   - D(B <- R);
   - D(B <- S);
   - reciprocal losses where available;
   - uncertainty;
   - major order/model/severity heterogeneity;
   - joint-state results;
   - boundary-case sensitivity.

8. CONSTRUCT DECISION

   State exactly one:

   - evidence currently favors generic compositional delivery loss;
   - evidence supports a constraint-identity-specific interaction;
   - evidence remains insufficient to distinguish them.

   Explain the evidence without overclaiming.

9. NEXT-STUDY SPECIFICATION

   - primary construct;
   - primary estimand;
   - secondary estimands;
   - operating regime;
   - reference strategy;
   - measurement strategy;
   - sample-size plan;
   - preregistration path/version.

10. CONFIRMATORY STATUS

    State one:

    - completed;
    - ready but intentionally not run because a manual preregistration/freeze
      requirement remains;
    - blocked by Gate 1;
    - blocked by human validation;
    - blocked by inability to find an informative regime;
    - blocked by reference identification;
    - blocked because the construct remains unresolved.

11. VALIDATION

    Include exact test commands and pass/fail counts.

12. FILES CHANGED

    Give a compact list.

13. REMAINING BLOCKERS

    Only genuine dependencies that cannot be completed from the repository and
    available compute.

Do not finish with vague statements such as "more work is needed."

For every blocker specify:
- what is missing;
- why it cannot be produced autonomously;
- what exact action would resolve it.


============================================================
Z. EXECUTION PRINCIPLE
============================================================

Work autonomously through this dependency graph.

Do not stop merely because one item was historically described as "next."

After completing a phase, immediately inspect whether its outputs unlock the
next phase.

Skip phases already completed and validated.

If an upstream result changes what downstream scientific work should be done,
adapt the downstream design accordingly rather than mechanically reproducing an
obsolete plan.

The primary goal is not to preserve the historical DCI framing.

The primary goal is to leave the project measuring a clearly defined,
identifiable behavioral phenomenon with validated measurement, correct
provenance, explicit uncertainty, and a confirmatory design whose claims follow
from the data.
