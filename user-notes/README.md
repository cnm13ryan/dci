# user-notes — what is here

The researcher's DCI-1 planning record from v2 to v7: preregistrations,
changelogs, decision records, audits, and the prompts that commissioned each
implementation. v8 and v8.1 live in `dci1/docs/` instead.

**Pinned** means `dci1` code names the file by its `user-notes/...` path. A
registration or freeze record keeps that path, so do not move or rename a pinned
file. `dci1/tests_v8dev/test_pinned_document_paths.py` fails if one goes missing.

## Preregistrations

| file | revision | |
|---|---|---|
| `DCI-1_preregistration_v2.md` | v2 | pinned |
| `DCI-1_preregistration_v3.md` | v3 | pinned |
| `DCI1_preregistration_v4r1.md` | v4 revision 1 | pinned |
| `DCI1_preregistration_v4r2.md` | v4 revision 2 | pinned |
| `DCI1_preregistration_v4r3.md` | v4 revision 3 | pinned |
| `DCI1_preregistration_v4r4.md` | v4 revision 4 | pinned |
| `DCI1_preregistration_v5.md` | v5 | pinned |
| `DCI1_preregistration_v6.md` | v6 | pinned |
| `DCI1_preregistration_v7.md` | v7; also the base v8 builds on | pinned |

## Changelogs between revisions

| file | |
|---|---|
| `DCI-1_v2-to-v3_changelog.md` | |
| `DCI1_v3_to_v4r1_change_summary.md` | |
| `DCI1_v4r2_changelog.md` | |
| `DCI1_v4r2_scientific_change_summary.md` | |
| `DCI1_v4r2_to_v4r3_changelog.md` | pinned |
| `DCI1_v4r3_to_v4r4_changelog.md` | pinned |
| `DCI1_v4r4_to_v5_changelog.md` | pinned |

## Open decisions, pre-freeze checks, and proposals never adopted

| file | |
|---|---|
| `DCI1_v4r1_unresolved_decisions.md` | |
| `DCI1_v4r2_unresolved_decisions.md` | pinned |
| `DCI1_v4r2_prefreeze_checks.md` | pinned |
| `DCI1_v4_amendment_A_prompt_stem.md` | draft, not adopted |
| `DCI1_v4_amendment_B_reference_pool.md` | draft, not adopted; pinned |
| `DCI1_v4_amendment_C_focal_grid.md` | draft, not adopted |
| `DCI1_v6_proposal.md` | not adopted, not registered |

## Construct, audits and review

| file | |
|---|---|
| `dci-construct-pass1.md` | what DCI should measure: construct diagnosis (2026-08-14) |
| `dci-construct-pass2.md` | the construct decision memo (2026-08-14); pinned |
| `benchmark-1.txt` | DCI as a benchmark construct: operational definition and decomposition |
| `AUDIT_2026-08-23_v4r4_evidence.md` | what v4r4's confirmatory study establishes |
| `AUDIT_2026-08-23_v5_design_execution.md` | can v5 resolve the companion-identity question |
| `AUDIT_2026-08-23_v5_readiness.md` | v5 readiness |
| `DCI_paper_review_packet_2026-08-20.md` | evidence and narrative review before any manuscript prose |

## Implementation and agent prompts

| file | |
|---|---|
| `v2_implementation_prompt.md` | commissioned the v2 implementation |
| `DCI-1 v3 Implementation Prompt.md` | commissioned v3 |
| `Implement_DCI1_v4_as_a_Fresh_Fully_Isolated_Study.md` | commissioned v4 as an isolated study |
| `prompt-to-red-team.md` | red-team handover for an agent with no prior context; pinned |
| `short-cuts-1.txt` | a short red-team prompt |

## Folders

- `consolidated/` — a five-part synthesis: scientific story, question and
  design, lifecycle and results, failure modes and integrity, context and paper
  state.
- `paper-dci1v4r4-i1/` — the paper plan for v4r4 (narrative, outlines, evidence
  map, figure plan, gaps, titles).
- `paper-dci1v4r4-i1-plain-language/` — a plain-language rewrite of eight of
  those files. It is a separate text, not a copy.
- `paper-guides/` — section-by-section writing guidelines and the NeurIPS 2026
  template.
