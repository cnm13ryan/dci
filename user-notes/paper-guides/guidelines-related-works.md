## **Guidelines for a Good Related Works Section**

Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), a strong Related Work section clearly positions the paper within the existing literature.

**Core function.** The Related Work section maps the field around the paper's contribution. It explains how the work differs from close, parallel, and corrective prior work, and anchors the novelty claims so readers understand why the paper targets this specific problem.

## Division of Labor

* **The Introduction carries the headline framing of prior work:** the field, the gap, and why the contribution matters.
* **The Related Work section carries precise comparisons:** close prior work, parallel work, borrowed methods, corrected mistakes, and the exact novelty delta.

## Placement

* **After the Introduction:** Use this when the paper is tightly embedded in an existing literature, fills a specific gap, corrects prior work, or depends heavily on surrounding contributions.
* **Near the Discussion or Conclusion:** Use this when the Introduction provides enough context and the body benefits from reaching the methods and results sooner.

## Canonical Structure

1. **Group prior work by theme.** Organize papers by approach, problem setting, technique, or claim.
2. **State the delta for each cluster.** Briefly explain what prior work did, then specify how this work differs: setting, method, result strength, assumption, limitation corrected, or parallel discovery.
3. **Handle close work explicitly.** For the most similar papers, state whether the work extends, corrects, generalizes, narrows, or independently overlaps with them.
4. **Give background pointers.** Cite surveys, tutorials, or books for readers who need broader context.
5. **Attribute precisely.** Cite specific methods, datasets, theorems, sections, or pages where possible. Make clear what is inherited from prior work and what is new.

## Quality Criteria

* **Make novelty explicit.** For every closely related paper, state the concrete difference.
* **Critique methods professionally.** Describe methodological issues and how the work addresses them. Keep critique focused on the work.
* **Name parallel work directly.** Acknowledge contemporaneous or independent results clearly and explain the remaining contribution.
* **Make every citation useful.** Each citation supports a specific claim, comparison, definition, or attribution.
* **Prioritize relevance and clarity.** Favor references that help readers understand the contribution. Include canonical citations the field expects.
* **Attribute generously and precisely.** Credit borrowed ideas, tools, datasets, and results with enough detail for readers to verify them.
* **Keep the section reader-oriented.** Help expert readers locate the paper on the map of existing work.

## Common Pitfalls

* Padding citations to appear comprehensive.
* Listing papers without explaining how they relate to the contribution.
* Repeating context already covered in the Introduction.
* Vague phrases such as "we extend prior work" without specifying how.
* Critiquing authors.
* Treating Related Work as an exhaustive literature survey.

## Practical Workflow

1. **Search broadly for close work.** Use literature search tools to surface relevant papers, then read the important ones directly.
2. **Write the delta sentence.** For each close paper, write one sentence on what it did and one sentence on how this work differs.
3. **Audit each citation.** Before submission, ask: "What does the reader gain from this citation?" Keep citations that clarify the contribution, support attribution, or satisfy field expectations.
