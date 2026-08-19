## **Guidelines for a Good Methods Section**

Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), a strong Methods section makes the paper's experimental choices precise, justified, and reproducible.

**Core function.** The Methods section describes what was done and why, in enough detail for a skeptical reader to judge whether the design supports the paper's claims and to reproduce the experiments. It owns experimental design, baselines, metrics, protocols, and reproducibility detail. The Results section reports outcomes.

## Default Order

The default order is **Background → Methods → Results**. Define terminology and standard techniques in Background. Describe what was done and why in Methods. Report outcomes in Results.

When claims require substantially different methods, organize **per claim**: pair each claim with its own methods and results. Adjacent setup and evidence reduce reader load.

## For Each Experiment, Specify

1. **Claim.** Which contribution does this experiment support, and how does it connect to the paper's narrative?
2. **Hypothesis discrimination.** Which competing hypotheses does the experiment distinguish?
3. **Setting.** Datasets, models, what varies, what stays fixed — in enough detail for an expert to reproduce.
4. **Metric.** What is measured and why it tracks the claim.
5. **Baselines.** What the comparison is against and why each comparison is fair and strong.
6. **Uncertainty protocol.** Number of runs, seed scheme, and the variance measure reported.

## Replication Detail

* **Final hyperparameters** for each model and algorithm.
* **Search ranges and selection criteria** used during development.
* **Seed scheme** sufficient to reproduce randomized methods.
* **Compute and infrastructure:** hardware (GPU/CPU model), memory, operating system, library and framework versions.
* **Code and artifacts:** release source code, model weights, datasets, licenses, READMEs, and runnable examples where possible. Otherwise describe them in enough detail for reconstruction.

## Quality Criteria

* **Use strong baselines.** Tune them seriously. Match the effort spent on the proposed method. Document the prompting, scaffolding, and hyperparameter search applied.
* **Justify metrics.** Explain why each metric measures the claim it supports.
* **Design ablations.** Isolate each component of a multi-part method.
* **Choose a variance measure that fits the data.** State the distributional summary reported and why it suits the data distribution.
* **Calibrate statistical thresholds before observing results.** Match thresholds to the design and the number of hypotheses tested.
* **Pre-specify the analysis plan.** Decide which analyses are confirmatory before observing results, so post-hoc patterns can be honestly distinguished later.
* **Specify the qualitative-example selection protocol.** State whether examples will be sampled randomly, curated, or exhaustively.
* **Design diverse evidence.** Use qualitatively different tests of the same claim.
* **Pair pseudocode with prose.** Use a readable outline to clarify nontrivial algorithms.
* **Handle qualitative evidence transparently.** Provide random examples alongside curated ones where possible. Use single examples only for existence-proof claims.
* **Separate setup from results.** Present the experimental design before the outcomes so readers can evaluate the setup independently.
* **Calibrate technical depth.** Give standard methods a brief explanation and citation. Give novel methods full technical detail.

## For Theoretical Contributions

* **State assumptions formally.**
* **Make theorem statements self-contained.** A reader checking the problem setup, notation, and assumptions can verify a statement.
* **Include proofs of nontrivial results.**
* **Attribute proof material precisely.** State which steps are new and which follow prior work.
* **Provide intuition.** Pair formal statements with informal explanation of why they hold.

The guiding principle: a reader can understand exactly what was done, why it was done, and what would be needed to evaluate or reproduce it. The Methods section earns trust by making the design inspectable.
