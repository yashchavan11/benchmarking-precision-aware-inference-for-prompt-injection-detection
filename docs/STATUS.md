# Current project state and handoff

This is the replaceable snapshot of active work and its exact continuation. Chronological
history remains in [SESSION_LOG.md](SESSION_LOG.md); phase completion is established by
[PHASE_RECORDS.md](PHASE_RECORDS.md). The session procedure is defined in
[AGENTS.md](../AGENTS.md).

## Current snapshot — evaluation component ready for development integration

| Field | Current value |
|---|---|
| Overall state | Offline development evaluation implemented and tested with synthetic fixtures; empirical work pending |
| Active phase | P1-A — asset, data and evaluation design audit; not started |
| Latest completed research phase | None |
| Snapshot provenance | Codex, 2026-11-16, America/New_York; S-20261116-01 |
| Active owner and reserved work | Shreyas's evaluation/integration workstream implemented by Codex; no active edits/jobs. Real-data/inference/profiling owners must confirm their assignments. |
| Latest session / changes since previous handoff | S-20261116-01: demo rerun and 18 tests passed (V-002); metric walkthrough, checkpoint methods/limitations and repository-only team handoff/review request prepared |
| Current source revisions | Unresolved; asset entries in [DATA_REGISTRY.md](DATA_REGISTRY.md) |
| Experimental configurations | Not frozen |
| Experimental findings | None recorded in [RESULTS.md](RESULTS.md) |
| Evaluation exposure | No model-performance inspection recorded; actual exposure history requires verification at project start |
| Reusable work | precision_benchmark/ and tests/; ARCHITECTURE v1; V-001; outputs/synthetic-demo/ is illustrative and regenerable, not experimental evidence |
| Partial changes / running or interrupted jobs | No active or interrupted jobs from this session. Repository inventory contains no real inference/data artifacts. Use Git status/history for the current commit and publication state. |
| Verified blockers | Real evaluation integration awaits audited labels and model predictions, which are absent locally. GPU/access/backend compatibility has not been tested. |
| Subsequent phase | P1-B after the P1-A completion gate is satisfied |

## Immediate continuation

**Evaluation handoff:** Read D-007, V-001 and ARCHITECTURE's implemented development interface.
The November 16 handoff/review request is in ARCHITECTURE; no messages were sent and no
reviewer is assigned. REPORTING now includes a metric guide and speaking notes. Latest
demo: `outputs/synthetic-demo-20261116/report.md`, with verification in V-002.
Run `python3 -m unittest discover -s tests -v` to verify the evaluator. The existing demo is
`outputs/synthetic-demo/report.md`; use a fresh output directory to regenerate it. It is
synthetic software evidence only. REPORTING contains accurate progress-report working text.
The evaluator's next steps are (1) second-contributor review of metric/contract choices,
(2) receive audited development labels and compatible FP32/FP16/INT8 outputs, and
(3) generate and review real development tables. No real report result exists yet.
The following P1-A work remains prerequisite to empirical execution.

**Bounded goal:** establish a verified, versioned asset/data contract and a defensible
sequential evaluation design before any final-test model performance is inspected.

**Task-specific context:** the scope in [README.md](../README.md); P1-A in
[ROADMAP.md](ROADMAP.md); D-001–D-006 in [DECISIONS.md](DECISIONS.md); Q-001–Q-004 in
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md); the data and exposure controls in
[RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md); existing entries in
[DATA_REGISTRY.md](DATA_REGISTRY.md); asset evidence in [SOURCES.md](SOURCES.md); and
Part 2's evaluation requirements in [EXTENSION.md](EXTENSION.md).

| Order | Next action | Evidence or output |
|---|---|---|
| 1 | Reconcile the actual workspace, prior data exposure and any active work with this planning snapshot; establish the owner and bounded P1-A task. | Corrected current state, explicit ownership and any verified blocker or missing context. |
| 2 | Verify exact model/tokenizer/dataset revisions, source fields and split counts, reference/model label meanings, duplicates, conflicting labels and relevant input lengths. | Audited asset and data entries with evidence; unresolved issues linked by question ID. |
| 3 | Resolve the Test-A/Test-B design and development eligibility using the audited counts and group constraints; document reproducible memberships, exclusions, exposure controls, rationale and limitations. | Recorded methodological decision, asset/split manifests and the evidence needed for the P1-A review. |

**Current review boundary:** no final held-out evaluation, router fitting or measured-gain
claim is appropriate at this planning state. Permitted development diagnostics and later
work follow the phase dependencies in ROADMAP and the data-role rules in RESEARCH_PROTOCOL.

**Completion condition:** the P1-A gate in ROADMAP is met and its review/evidence is linked
from PHASE_RECORDS. Missing access or an inadequate partition remains an explicit unresolved
condition, not an assumed success.

**Records affected by this task:** DATA_REGISTRY for audited assets, memberships and
exposure; DECISIONS for selected methods; OPEN_QUESTIONS for unresolved issues; applicable
VALIDATION_LOG evidence; and the session, phase and current-state records required by AGENTS.

## Continuation fields for subsequent snapshots

The current snapshot and immediate continuation above are replaced as work advances.
These field definitions supply the additional detail needed when actual artifacts and
execution exist; they are not completed work records.

| Field | Information needed for a reliable continuation |
|---|---|
| Snapshot provenance | Preparer, actual date/timezone, phase and session ID. |
| Changes since prior snapshot | Brief changes with links to the chronological session entry and affected decisions/evidence. |
| Reusable artifacts | Durable location, version/hash where relevant, compatible configuration, data membership and exposure status. |
| Ownership and reserved work | Owner, bounded task, affected files/interfaces and other contributors' work to preserve. |
| Partial edits and jobs | Actual system and process/job IDs; queued/running/interrupted state; saved checkpoint; output/log references; safe verification or resume action. |
| Uncertainty | Verified blockers separately from open hypotheses, with question IDs and the next useful investigation. |
| Next actions | Ordered bounded tasks, normally up to three, with the specific records/artifacts they depend on. |
| Required checks and review boundary | What must be verified, which downstream action depends on it, and what evidence establishes completion. |
| Next-phase transfer | The preceding phase closeout and its reusable outputs, limitations, invalidated evidence and required follow-up. |
