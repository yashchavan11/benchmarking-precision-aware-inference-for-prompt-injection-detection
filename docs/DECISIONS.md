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
| D-006 | Working methodological design; details unresolved before held-out use | Designate disjoint Test-A for Part 1 and sealed Test-B for Part 2 before any Part 1 official-test model-performance inspection. | Group isolation, development-overlap exclusions and exposure rules in RESEARCH_PROTOCOL; identities and memberships in [DATA_REGISTRY.md](DATA_REGISTRY.md); unresolved feasibility in Q-002. |

D-006 is a methodological proposal supporting the approved sequence, not a user-selected
allocation or an audited partition. Its adequacy must be resolved before Test-A performance
is inspected. Any necessary alternative requires a recorded rationale and the same honest
account of data exposure; an already exposed population cannot be made unseen by renaming
or repartitioning it.

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
