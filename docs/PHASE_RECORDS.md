# Phase completion records

This file is the evidence ledger for the phases defined in [ROADMAP.md](ROADMAP.md).
The linked roadmap section owns each phase's tasks, dependencies and completion criteria;
this record stores what actually happened and what the next phase can reuse. Current
session state and the next task are summarized in [STATUS.md](STATUS.md).

## Completion ledger

No research phase is currently complete. A blank closeout reference means no completion
evidence is recorded, not that the corresponding work has passed review.

| Phase and authoritative plan | Status | Closeout / evidence reference |
|---|---|---|
| [P1-A — Asset and data audit](ROADMAP.md#p1-a--asset-data-and-evaluation-design-audit) | In progress | V-006–V-009; source counts/provenance audited; model labels/access and evaluation allocation pending; no closeout |
| [P1-B — Components and pilot](ROADMAP.md#p1-b--reusable-components-and-a-small-real-pilot) | Empirical phase not started; independent evaluator preparation | V-001–V-005; no phase closeout |
| [P1-C — Main-protocol freeze](ROADMAP.md#p1-c--analysis-implementation-and-main-protocol-freeze) | Empirical phase/freeze not started; independent evaluator preparation | V-001–V-005; no phase closeout |
| [P1-D — Main benchmark](ROADMAP.md#p1-d--main-benchmark-and-analysis) | Not started | None recorded |
| [P1-E — Part 1 closeout](ROADMAP.md#p1-e--part-1-closeout-and-knowledge-transfer) | Not started | None recorded |
| [P2-A — Benefit and objective](ROADMAP.md#p2-a--benefit-characterization-and-research-objective) | Not started | None recorded |
| [P2-B — Routing baselines](ROADMAP.md#p2-b--transparent-routing-baselines) | Not started | None recorded |
| [P2-C — Learned-gate development](ROADMAP.md#p2-c--learned-gate-and-diagnostic-iterations) | Not started | None recorded |
| [P2-D — System and final freeze](ROADMAP.md#p2-d--integrated-system-full-cost-measurement-and-policy-freeze) | Not started | None recorded |
| [P2-E — Confirmation](ROADMAP.md#p2-e--confirmatory-evaluation-and-tradeoff-interpretation) | Not started | None recorded |
| [F — Final delivery](ROADMAP.md#f--reproducibility-and-final-delivery) | Not started | None recorded |

## Phase closeout template

### [Phase ID] — [title]

- **Owner / reviewer / closeout date:** [actual values]
- **Status:** [not started / in progress / blocked / ready for review / complete / reopened]
- **Inputs read and reused:** [previous closeout, decision, asset, run and result references]
- **Acceptance criteria assessed:** [link to roadmap/protocol criteria and any approved amendment]
- **Outputs produced:** [artifact locations, versions/hashes and related record IDs]
- **Correctness and validity evidence:** [validation IDs; scope of established and unverified behavior]
- **Main findings:** [result IDs with uncertainty, or verified implementation findings]
- **Unresolved limitations:** [claim limitations, known issues and open-question IDs]
- **Data exposure at closeout:** [exposure-log reference and evaluation populations still protected]
- **Protocol or conclusion changes:** [decision IDs, invalidated runs/results and downstream effects]
- **Reusable work:** [functions/interfaces, audited inputs, prediction caches, configurations,
  analysis and profiling outputs; actual artifact references]
- **Reuse conditions:** [compatible settings/populations, assumptions and required revalidation;
  a result on one evaluation set is not automatically a result on another]
- **Required next-phase reads:** [specific record and artifact IDs sufficient to recover the context]
- **Next bounded task and owner:** [explicit task, or unassigned owner]
- **Completion decision:** [reviewer rationale, satisfied criteria and any remaining conditions]

The template describes fields to populate; placeholders are not evidence. The P1-E closeout
must cover the Part 1 transfer inventory specified in ROADMAP. Freeze-phase records must link
the exact frozen artifacts and applicable exposure record, not merely say that a freeze occurred.

## Reopening and supersession

When later evidence invalidates a closeout, change its ledger status to reopened and append
a reopening record containing the triggering finding, affected acceptance criteria,
downstream runs/results, recovery task and replacement evidence required. Preserve the
previous closeout with its superseded status and link the new record from it. An altered
frozen configuration cannot silently inherit the old result tables or completion decision.
