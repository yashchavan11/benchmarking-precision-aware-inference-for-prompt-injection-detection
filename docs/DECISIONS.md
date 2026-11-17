# Project decision register

This register records the authority, rationale and lifecycle of project choices. It
separates approved scope from candidate methods and frozen experimental settings. The
current entries describe commitments and a working evaluation design; none establishes
experimental validation.

## Current decisions

| ID | Status / authority | Recorded decision | Governing detail |
|---|---|---|---|
| D-001 | User-approved project direction | Binary prompt-injection classification using Sentinel v2 and PromptShield. | Selected assets and scope in [README.md](../README.md). |
| D-002 | User-approved core study | Compare FP32 execution, FP16 execution and INT8 quantization of the same frozen checkpoint. | Treatment semantics and controlled comparisons in [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md). |
| D-003 | User-approved research priority | A learned selective higher-precision gate is a crucial, committed second research part requiring serious development, diagnosis and refinement. | Required research and evidence in [EXTENSION.md](EXTENSION.md). |
| D-004 | User-approved sequence | Complete Part 1, then develop Part 2, reusing valid functions and permitted results. | Phase dependencies and knowledge transfer in [ROADMAP.md](ROADMAP.md). |
| D-005 | User-approved working constraints | Preserve durable project context; support Windows, macOS and university-cluster work, with CUDA-dependent experiments on suitable cluster resources. Local setup/publication is not a prerequisite for independent useful work. | Session continuity and coordination in [AGENTS.md](../AGENTS.md); experimental comparability in RESEARCH_PROTOCOL. |
| D-006 | Sequential holdout design retained; concrete eligibility/allocation selected in D-008 | Designate disjoint Test-A for Part 1 and sealed Test-B for Part 2 before any Part 1 official-test model-performance inspection. | Group isolation, development-overlap exclusions and exposure rules in RESEARCH_PROTOCOL; identities and memberships in [DATA_REGISTRY.md](DATA_REGISTRY.md); construction in D-008/SPLIT-001?004; human review/exposure conditions remain Q-002/Q-013. |
| D-007 | Development conventions; not a confirmatory freeze | Shared evaluator interface and metric definitions. | Detailed record below; scientific review and real-run validity remain required. |
| D-008 | User-approved construction; human review/release pending | Exact 50/50 whole-group split and development eligibility. | Detailed record below; SPLIT-001?004 / V-021. |

At adoption, D-006 proposed the sequential holdout design without a selected allocation.
D-008 now records Yash's concrete choice and SPLIT-001?004 retain checked review-ready
memberships. Human review/exposure conditions must still be resolved before Test-A performance
is inspected. Any necessary alternative requires a recorded rationale and the same honest
account of data exposure; an already exposed population cannot be made unseen by renaming
or repartitioning it.

### D-008 — Approved P1-A eligibility and 50/50 whole-group construction

- **Date/authority/status:** 2026-11-17, America/New_York; Yash explicitly approved the 50/50 proposal and requested review-ready manifests during S-20261117-05. Construction design selected; human scientific review and P1-A closeout remain pending. This is not the P1-C benchmark freeze or a release of test performance.
- **Inputs/evidence:** ASSET-001 pinned source and V-008/V-011; exact proposal in `docs/evidence/p1a-partition-candidates-20261117.json`. No model output influenced the choice. Prior team exposure remains incompletely declared (Q-013).
- **Eligibility:** Apply the existing protocol's test-overlap-first, then validation-precedence exclusions. Verified current data exclude no rows: retain all 18,909 train and 1,000 validation rows, preserving original IDs/text/labels. No extra normalization, relabeling or deduplication.
- **Allocation:** Within each reference class, order whole exact-text SHA-256 groups by `SHA256(namespace + ':' + label + ':' + raw_text_sha256)` (ascending hex), then raw-text hash as collision tie-break. Literal namespace is `precision-aware-inference:p1a-ab-candidate:v1:20261117`. Select the prefix minimizing `abs(2 * prefix_rows - class_rows)`; ties prefer fewer A rows. B is the complement. Preserve original test source order in outputs. Do not change the namespace because it contains the word `candidate`.
- **Support/construction:** Each side 11,758 rows, 8,515 benign and 3,243 injection; A/B groups 11,657/11,702. V-019/V-021 independently verify these counts, complete coverage, group integrity and development isolation in SPLIT-001?004. All 71 duplicate groups stay intact. Human scientific review remains pending.
- **Rationale/options:** 50/50 preserves equal class support for both committed research parts and 649 more positive examples in B than the reviewed 60/40 candidate. This is not a power guarantee; endpoints/effect sizes remain unspecified. 60/40 support remains historical candidate evidence, not selected membership.
- **Exposure controls:** Administrative ID/label/group use only. Development uses training/validation role manifests. Test-A performance awaits P1-C; default no Test-B predictions before P2-E after P2-D freeze. Record exposure and enforce roles in future loaders; public source files are not cryptographically sealed. Unknown prior exposure cannot be relabeled none.
- **Review/reconsideration:** Review actual output evidence and each teammate's exposure declaration before scientific reliance/closeout. Conflicting new provenance or exposure requires impact assessment before evaluation. Near-duplicate/template and pretrained-contamination limitations remain. No previous empirical results exist to invalidate; D-006's working design is made concrete without changing the sequential scope.

## Choice status vocabulary

| Status | Meaning |
|---|---|
| User-approved scope | A project goal or boundary; implementation details and empirical outcomes are not predetermined. |
| Candidate | A concrete option available for investigation on permitted development data. |
| Chosen for pilot | An operational choice subject to revision after diagnostic evidence. |
| Frozen for evaluation | The choice and dependencies were recorded before the designated evaluation; later changes require a documented amendment and impact assessment. |
| Superseded | A historical choice retained with its replacement and affected runs/results identified. |

Numerical settings and method candidates are defined in ROADMAP and the applicable protocol.
Their presence there does not make them user-mandated constants or measured optima.

## Decision record schema

### D-[next unique number] — [short decision]

- **Date / author / reviewer:** [actual values]
- **Phase and status:** [phase ID and status from the vocabulary above]
- **Question:** [specific choice being made]
- **Options considered:** [relevant alternatives and their tradeoffs]
- **Selected choice and rationale:** [why it serves the research question]
- **Evidence:** [source, validation, run or result IDs; inference distinguished from observation]
- **Data available when decided:** [splits and exposure-log reference]
- **Fixed parameters/artifacts:** [exact settings, memberships and hashes when available]
- **Consequences and limitations:** [accuracy, cost, comparability and reproducibility effects]
- **Earlier records affected:** [none, or IDs requiring rerun, reanalysis or retraction]
- **Reconsideration condition:** [new evidence or condition that would justify review]
- **Supersedes / superseded by:** [record IDs if applicable]

## Amendment record

### D-007 — Development evaluator interface and metric conventions

- **Date / author / reviewer:** 2026-11-11, America/New_York; Codex implementing Shreyas's authorized evaluation task; second-contributor review pending.
- **Phase/status:** P1-B/P1-C component preparation on synthetic data; chosen for development, not a main-protocol freeze.
- **Choice:** Standard-library offline package and CLI using the JSON/JSONL v1 contract in ARCHITECTURE. Keep expected labels separate from inference rows; join by stable IDs; reject incomplete/incompatible runs. This enables independent work before real inference outputs exist.
- **Metric conventions:** Injection is class 1; score >= shared threshold is positive. Undefined denominators return null, never a fabricated perfect score. F1 is `2TP/(2TP+FP+FN)` (and the corresponding class-0 expression); macro-F1 averages the two only when both are defined. AUC gives ties half credit. Brier is mean squared injection-score error. Development ECE uses ten equal-width bins, lower-inclusive/upper-exclusive except the final bin includes 1; empty bins contribute zero and retain null means/count zero.
- **Paired interpretation:** Corrected/introduced errors refer to candidate versus FP32; correctness comes from reference labels. Accuracy delta is candidate minus FP32 in percentage points.
- **Exposure/threshold:** Only synthetic fixtures were used. The fixture's 0.5 threshold is illustrative, not a selected project threshold. No real inputs, source revisions or data partitions were audited or frozen.
- **Evidence:** V-001 and S-20261111-01. Tests cover hand-computed metrics, all paired outcomes, tied AUC via an independent pairwise calculation, input integrity and CLI integration.
- **Limits/follow-up:** Keep Test-A/Test-B disabled until the required freeze and uncertainty implementation. No resource-cost claims or automatic threshold selection. Primary endpoint and final calibration/uncertainty choices remain Q-005/Q-006. Review formulas, label orientation and source contracts before real use.
- **Prior evidence affected:** None; no empirical results existed.

A replacement decision retains the original rationale and states why it changed, what
final outcomes were already visible, and which downstream evidence remains valid.
Post-evaluation choices have the exploratory/confirmatory status defined by
RESEARCH_PROTOCOL; extra checks do not erase earlier exposure. A superseded decision is
history, not an instruction to repeat the obsolete method.
