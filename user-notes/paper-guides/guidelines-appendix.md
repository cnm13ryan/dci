## **Guidelines for a Good Appendix**
 
Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), the [NeurIPS 2026 Call for Position Papers](https://neurips.cc/Conferences/2026/CallForPositionPapers), and the NeurIPS 2026 submission instructions, a strong appendix supports the main body from behind and never carries it.
 
**Core function.** The appendix is *optional reading*. It holds the detail that lets a skeptical reader verify, reproduce, audit, or extend the work, and it holds nothing the main argument depends on. The NeurIPS template states the constraint directly: the paper must be able to stand alone without the appendix, and moving critical supporting experiments there is inappropriate.
 
## The Stand-Alone Test
 
Delete the appendix. Read the main body. If any claim in the Abstract or Introduction now lacks support, the deleted material was load-bearing and belongs in the main body, compressed if necessary. Run this test once the draft is stable and again before packaging, because material migrates outward under page pressure.
 
The test has one asymmetry worth knowing: proofs, hyperparameters, and protocol detail can move out freely, since the main body carries the statement and the appendix carries the verification. Evidence cannot, since the main body then carries an assertion and the appendix carries the reason to believe it.
 
## What Belongs Where
 
| Material | Placement | Reason |
| --- | --- | --- |
| Headline evidence for any stated claim | Main body | Fails the stand-alone test |
| Alternative Views or Counterarguments | Main body, required for position papers | The track places this section in the main body explicitly |
| Theorem statements and assumptions | Main body | A reader must be able to check what is claimed |
| Full proofs | Appendix, with a main-body proof sketch | Verification is optional reading; the result is not |
| Extended derivations and algebra | Appendix | Supports a main-body expression the reader can use without it |
| Final hyperparameters, search ranges, seed scheme | Appendix | Needed for reproduction, not for judgement |
| Compute, hardware, library versions | Appendix | Same |
| Secondary sweeps, sensitivity analyses, confirmatory near-duplicates | Appendix | The decisive experiment stays in front |
| Qualitative samples | Appendix, with the selection protocol stated in the main body | The protocol determines what the samples prove |
| Full prompts, task lists, rubric definitions, annotation instructions | Appendix | Bulk material with no argumentative role |
| Citation verification register | Appendix | Project convention, see below |
| Result-insertion map | Appendix | Project convention, see below |
| Reproducibility and artifact statement | Appendix | Points to code, weights, data, licences |
| Tacit knowledge, failed approaches, replication traps | Appendix or companion note | Useful to future researchers, irrelevant to the claim |
 
## Canonical Order
 
Order appendices to mirror the main body, so a reader following a forward reference lands near the material they were already reading.
 
- **A. Derivations and proofs**, in the order the results appear in the main body.
- **B. Full experimental or protocol detail**, including settings, seeds, and compute.
- **C. Additional results**, sweeps, and ablations.
- **D. Qualitative samples**, preceded by the selection protocol.
- **E. Citation verification register.**
- **F. Result-insertion map**, for papers whose experiments have not yet run.
- **G. Reproducibility and artifact statement.**
- **H. Tacit knowledge and lessons.**
Omit any appendix with no content. An empty or near-empty section costs more attention than it returns.
 
## Cross-Referencing Discipline
 
* **Reference every appendix from the main body**, at the point where its detail is first wanted, using a specific pointer such as "Appendix B.2" rather than "the appendix."
* **Cut or reference unreferenced sections.** An appendix section no main-body sentence points to is dead weight.
* **Keep references one-directional.** The main body points forward to appendices; appendices point back to main-body sections. Avoid chains of appendix-to-appendix references deeper than one hop.
* **Make each pointer state what the reader gains.** "Full hyperparameters appear in Appendix B" beats "see Appendix B."
## Self-Containment
 
Each appendix opens with one sentence naming what it contains and which main-body claim or section it serves. Recap the notation a reader arriving directly would need, restate the claim under discussion, and write captions that stand alone. A reader entering at Appendix D after a week away should not need to re-read Section 3 to orient.
 
## Project Conventions
 
### Citation verification register
 
Unverified citations remain in the bibliography and are flagged `TODO(CITE)` at the point of use. A dedicated appendix lists every flagged reference with: the claim it supports, whether that claim is load-bearing, what was checked, what remains unverified, and the source consulted. Dropping an unverified citation destroys the trail; flagging it preserves the reference and records its status. Recent work warrants active verification against the source document rather than trust in intermediate summaries, since inherited errors have been substantive.
 
### Result-insertion map
 
For papers whose experiments have not run, a table mapping each needed result to its source artifact, its destination section or figure, and the interpretation that result would change. The map makes the paper's empirical gap auditable and makes the eventual insertion mechanical. It never implies the results exist.
 
### Structural companion note
 
A separate markdown file recording deviations from source material, the guideline rationale behind structural choices, an objection table, and outstanding TODOs. This lives outside the submitted PDF.
 
## Submission Mechanics
 
* **Appendices carry no page limit and do not count as content pages.** Acknowledgments, references, and the checklist are likewise excluded from the nine-page limit.
* **Ship one PDF.** The appendix goes in the same file as the main body. Code and video may be uploaded as a ZIP; a separate appendix PDF may not.
* **Anonymize the appendix.** Double-blind review covers the whole document, including artifact links, filenames, institution-revealing paths, and acknowledgment text.
* **Apply the same font and figure rules.** The document must embed only Type 1 or embedded TrueType fonts throughout. Type 3 fonts from matplotlib output or typewriter faces are as disqualifying in an appendix as in the main body, so validate the packaged PDF rather than the main body alone.
* **Position Paper Track submissions require no checklist**, so no checklist appendix. Papers targeting the Main or Evaluations and Datasets tracks include it after the references.
## Quality Criteria
 
* **Pass the stand-alone test.** No appendix content supports a claim in the Abstract or Introduction.
* **Serve a stated purpose.** Each appendix names the main-body element it supports in its first sentence.
* **Earn the reference.** Every appendix is pointed to from the main body; every pointer says what the reader gains.
* **Preserve auditability.** Verification status, selection protocols, and known gaps are recorded rather than smoothed over.
* **Support random access.** Notation is recapped, claims restated, captions self-contained.
* **Match main-body standards.** Captions lead with takeaways, tables report variation alongside point estimates, and figures explain every visual element.
* **Keep tense honest.** Planned work is described in the future or conditional tense wherever it appears.
* **Validate as packaged.** Page count, undefined references, overfull boxes, and embedded fonts are checked on the compiled document including appendices.
## Common Pitfalls
 
* **Using the appendix as overflow.** Material cut for length under page pressure often turns out to be load-bearing. Compress in place instead, then re-run the stand-alone test.
* **Burying a decisive experiment.** The strongest result belongs in front, however crowded the main body.
* **Filing Alternative Views in the appendix.** The position track requires it in the main body.
* **Writing unreferenced sections.** Appendices accumulate during drafting and are rarely audited afterwards.
* **Dropping detail rather than deferring it.** Protocol detail omitted entirely is unrecoverable; protocol detail in Appendix B costs a reviewer nothing.
* **Assuming the reader arrives from Section 3.** Most appendix readers arrive from a search or a forward reference and need local orientation.
* **Validating the main body only.** Font and layout defects hide in appendix figures and tables.
