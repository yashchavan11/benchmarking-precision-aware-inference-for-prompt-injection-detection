# Phase completion records

This file is the evidence ledger for the phases defined in [ROADMAP.md](ROADMAP.md).
The linked roadmap section owns each phase's tasks, dependencies and completion criteria;
this record stores what actually happened and what the next phase can reuse. Current
session state and the next task are summarized in [STATUS.md](STATUS.md).

## Completion ledger

P1-A and the bounded batch-one P1-B pilot are complete as recorded below. A blank closeout reference for later phases means
no completion evidence is recorded, not that their requirements have passed.

| Phase and authoritative plan | Status | Closeout / evidence reference |
|---|---|---|
| [P1-A - Asset and data audit](ROADMAP.md#p1-a--asset-data-and-evaluation-design-audit) | Complete, 2026-11-17 | P1-A closeout below; V-008 through V-038 establish asset/data/input scope |
| [P1-B - Components and pilot](ROADMAP.md#p1-b--reusable-components-and-a-small-real-pilot) | Complete for unpadded batch-one pilot, 2026-11-17 | P1-B closeout below; D-012, V-039 through V-042, RES-004 and complete three-treatment bundle |
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

## P1-A closeout - Asset, data and evaluation-design audit

- **Date/owner/review:** November 17, 2026, America/New_York; coordinating agent at Yash's request, with separate automated source, data, code, native-output and phase-evidence reviews. No unperformed human implementation/review is claimed. D-009 permits continuation without teammate attestations.
- **Status/decision:** Complete. The coordinating review accepts the independently supported [completion facts](evidence/p1a-closeout-20261117.json) and final checklist in `outputs/runtime-20261117/phase-review/p1a-final-assessment.md`. Earlier conditional assessments remain preserved; actual D-011 evidence resolved their remaining all-split token-length item.
- **Inputs:** README scope and D-001 through D-011; RESEARCH_PROTOCOL; ASSET-001/002; fixed source/data identities and exposures. No model performance influenced source eligibility or A/B construction.

| ROADMAP requirement | Evidence establishing completion |
|---|---|
| Resolve selected identities, access, schema, head labels and preprocessing requirements | ASSET-001/002, V-022, V-034/V-035: immutable data/model/tokenizer revisions, authenticated seven-file/header verification, actual native configuration and tokenizer behavior. Injection index 1 and two-row F16 head descriptor [2,1024] are established; full weight loading remains P1-B. |
| Audit all source rows, labels, groups, conflicts and lengths; implement eligibility | V-008/V-011, V-019/V-021, V-026/V-027, V-034 through V-038: all 43,425 original IDs/rows; exact-group isolation and no exclusions; all-split character/byte and token-length accounting. Raw sources/labels unchanged. |
| Construct Test-A/Test-B before model performance | D-008 and SPLIT-001 through SPLIT-004, independently checked: 11,758 rows per test subset, 8,515 benign/3,243 injection each, whole-group integrity and zero cross-population exact-group intersections. No outcome-driven allocation. |
| Specify administrative access, exposure and reserved evaluation protection | D-006/D-009/D-011; EXP-001 through EXP-007; fixed role/access manifests and early guarded development input loading. Official-test token processing was separately approved and aggregate-only. No classifier or test performance was accessed/released. |
| Define usable component/artifact contracts and next task | ARCHITECTURE v1, checked evaluator, hash-bound input loader and native audits. Exact expected IDs, label/score semantics, source hashes, role boundaries and failure/complete states support the P1-B proposal below. |

### Established facts and reuse inventory

- **Sources:** PromptShield `a5234cb1f5cdb256600cab64b8c961195b5e8404`; Sentinel/tokenizer `05ff9bfd1f28c5228e53121d5ee4427bb5205212`. Audited original files/header and source hashes are ASSET-001/002; full checkpoint payload/checksum/loading is still a P1-B prerequisite.
- **Populations:** `outputs/contract-20261117/partitions-v2/`, with compact summary/access/identity hashes in DATA_REGISTRY. Eligible training 18,909 and validation 1,000; Test-A/Test-B 11,758 each. D-009 development access SHA `83dde0502e9aca5cfd000c5f6ec9631602db9f03a334a2f1a42d9ac3adc3e79b`. Original v1, authority-guard failure and corrected v2 are retained; population bytes remain identical.
- **Native development:** R-P1-A-20261117-07 successful job 11955247, retrieved under `outputs/runtime-20261117/attempt-04/`. V-035 independently checks all 19,909 rows, synthetic behavior and summary arithmetic. RES-003 owns length/truncation observations and the prior development-only pilot proposal.
- **Native official-test administration:** R-P1-A-20261117-08 job 11956265, retrieved under `outputs/holdout-prep-20261117/attempt-01/`. V-038 checks complete 23,516-row total-only histogram/statistics, source/runtime/package identity and85-test evidence. This is administrative access, not an untouched-file or performance claim.
- **Environment:** Approved Explorer CPU route, Python 3.13.5, Transformers 4.57.1/tokenizers 0.22.2. Exact package lock and setup/reuse hashes retained. Native source hashes match the audited official library. Windows native policy remains unchanged; GPU/PyTorch/bitsandbytes operation is not established by CPU success.
- **Software:** Reusable evaluator, source/contract audits, development input loader, tokenizer audits and role checks.85 tests pass locally and on the final Explorer job within recorded conditions. Input/string preservation, explicit wrapper settings and complete coverage are checked; predictions are not yet produced.
- **Retention:** Source/row/job artifacts remain local and in private scratch with hashes/receipts. Compact safe evidence and reproducible code are in Git. Scratch is not the durable sole copy; another teammate's access to ignored files is not assumed. Preserve failed attempts and unchanged source snapshots rather than recreating evidence silently.

### Limits and unrun work transferred to P1-B

No classifier weights were fully downloaded or loaded, no logits/scores/predictions exist,
and no precision treatment or model resource measurement has executed. Header/configuration
and tokenizer evidence do not establish model pooling/position equivalence or finite
inference. Unknown prior external exposure, annotation truth, near-duplicate/template
dependence and pretrained contamination remain disclosed limits, not invented clean history.
Support counts are not a power guarantee. Main threshold/endpoint/uncertainty/profile choices
and the P1-C freeze remain later work. Test-A/Test-B releases and the sequential full learned-gate
study are unchanged. Complete Part 1 before substantive Part 2 work.

### Next bounded task

Prepare the proposed 128-example eligible-training pilot in all three treatments, using
the exact checkpoint, a common verified GPU/runtime, explicit shared tokenization and
original unpadded batch one. Candidate cap 1024 comes from RES-003 development evidence
recorded before official-test token statistics. Make the full-weight download/integrity,
GPU compatibility, precision/head policy, matched schedule, provisional scoring threshold,
budget, failure handling and output manifests concrete before model execution. Obtain the
required approval for this model/GPU task; the proposal is not a main-study freeze. The
pilot must verify actual model loading, finite complete outputs and effective precision,
not assume quality or speed benefits. Read this closeout, RES-003, ARCHITECTURE, Q-004/Q-014
and the common protocol before P1-B. No prerequisite to wait for a teammate is introduced.

## P1-B closeout - Reproducible three-precision development pilot

**Disposition:** Complete for the original unpadded batch-one feasibility configuration,
November 17,2026. D-012 authorized the bounded work; V-039 through V-042 and RES-004 provide
actual checks/results. Independent automated reviews are labeled as such, not human review.
No main-protocol freeze or final quality/cost claim follows from this closeout.

| ROADMAP completion requirement | Observed evidence |
|---|---|
| Same semantic classifier task in all three intended treatments | Full pinned checkpoint checksum; same 128 training IDs and actual token/mask schedule; complete finite FP32/FP16/LLM.int8 runs on one L40S allocation. |
| Effective precision, labels, head and device verified | Actual311-tensor inventory; two-logit benign/jailbreak orientation;196 executed INT8 projections with floating head/residuals; strict FP32 flags, eval/frozen state, common eager attention and device. |
| Relevant input/pooling/correctness checks | Exact capped-prefix/length checks; final-token hooks including EOS cases; empty/mask rejection; original padded-batch rejection; checked scoring and stable ID alignment. Padded equivalence remains unsupported, not silently assumed. |
| Deterministic pilot and initial feasibility observations | PILOT-001 membership precedes outputs;128/128 predictions in each mode; raw synchronized forward/loading/memory records. Resource limitations and unfavorable observations retained in RES-004. |
| Reproducible, independently checked outputs | Portable text-free bundle with exact executed source archive, run/artifact hashes, package lock/provenance, usage commands, offline assembly/reanalysis and independent arithmetic/native reviews.107 GPU-job tests; 111 final local tests including four new offline-only checks. |

**Retained inputs/outputs:** ASSET-001/002 and all P1-A populations remain unchanged.
The [portable bundle](evidence/p1b-pilot-20261117/comparison.json) supplies predictions and
analysis without requiring raw assets or GPU access. Registered ignored raw sources, model
weights, setup logs and prior failed/superseded audit evidence remain preserved. GPU job
11959388 and CPU setup 11959175 are complete; no pilot job remains active.

**Findings/limits transferred:** RES-004 records identical FP32/FP16 classifications,
one INT8 correction, shared false negatives, lower observed INT8 memory and slower pilot
median forward latency. No statistical superiority, end-to-end speedup or escalation
benefit is established. Cap1024/threshold 0.5/INT8 threshold 6/head policy are pilot settings;
main choices are not automatically frozen. Larger batches need a checked pooling policy
if selected. Near-duplicates, annotation truth, pretrained contamination, unknown external
exposure and small enriched-sample limits remain disclosed.

**Next bounded phase:** P1-C. Prepare a concrete decision packet for the main endpoint,
FP32-validation threshold objective/search/tie rule, common preprocessing/batch/quantization
policy, paired uncertainty and repeated profiling plan/budget. Ask Yash before these major
choices and further substantive experiments. After approval, perform the eligible validation
selection and required analysis/measurement checks, then freeze the complete Part 1 plan
before Test-A. Test-B remains reserved for the later frozen learned-gate study. The current
progress-report inference deliverable is complete; report assembly/presentation can proceed
without waiting for an unprovided teammate artifact.
