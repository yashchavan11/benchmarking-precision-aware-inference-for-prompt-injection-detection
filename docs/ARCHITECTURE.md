# Planned architecture and artifact contracts

This document specifies logical components and the information they exchange. The
components are planned, not implemented. Concrete module names, serialization formats and
backend choices remain implementation decisions. Scientific rules belong in
[RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md) and [EXTENSION.md](EXTENSION.md); phase ordering
belongs in [ROADMAP.md](ROADMAP.md).

## Component responsibilities

| Component | Responsibility | Input → output |
|---|---|---|
| Asset/data preparation | Resolve source identities and construct audited eligibility manifests. | Source snapshots and audit decisions → assets, membership, exclusions and exposure metadata. |
| Input preparation | Apply the selected tokenizer and preprocessing configuration. | Eligible text → tokens, masks, lengths and truncation metadata. |
| Precision execution | Load the frozen classifier with the selected treatment and expose its verified output. | Pinned assets, inputs and precision configuration → logits/scores, treatment evidence and failures. |
| Classification decision | Apply the common injection-score definition and classification threshold. | Verified score and threshold artifact → label. |
| Quality analysis | Calculate reproducible metrics and paired analyses from saved predictions. | Complete compatible prediction rows and reference labels → metrics, differences, uncertainty and subgroup summaries. |
| Resource profiler | Measure defined execution scopes and preserve raw samples. | Workload and measurement plan → timing, throughput, memory and loading observations. |
| Gate feature extraction | Construct the gate's input without needing a high-precision pass. | Input metadata and low-run output → feature vector and acquisition-cost information. |
| Learned gate | Apply training-fitted transforms and a selected benefit/cost decision rule. | Feature vector and fitted gate artifact → escalation decision and optional benefit estimate. |
| Escalation executor | Execute selected high passes and assemble correctly matched final results. | Low results and route decisions → final predictions, execution traces and costs. |
| Reporting analysis | Produce figures, tables and claim references from retained evidence. | Registered compatible outputs → reproducible reporting artifacts. |

These responsibilities do not require one module per row or a large framework. Keeping
deterministic analysis independent of expensive inference permits regenerated results and
isolated numerical checks without rerunning the classifier.

## Inference and training boundaries

At inference, input preparation feeds low-precision execution; low output and permitted
input metadata feed the feature extractor and fitted gate. The executor sends only selected
IDs to high precision and merges selected results back into original request order. The
classification threshold and escalation cutoff are distinct artifacts.

Gate fitting is a separate development path: paired low/high predictions join reference
labels to construct targets; permitted features join those targets by ID. Reference labels,
correctness and high predictions must not enter the deployed feature input. The target and
feature definitions are specified in EXTENSION rather than inferred from available columns.

## Artifact contracts

The tables below define information that must be recoverable from machine artifacts or
linked immutable manifests. Shared metadata can live once at run level rather than being
copied into every prediction row. Human records link these artifacts; they are not a
substitute for retaining the actual inputs and outputs.

### Asset and input manifests

| Information | Required content |
|---|---|
| Source identity | Immutable model/tokenizer/dataset revisions; original dataset split and row identity. |
| Example identity | Stable example ID, raw-text hash and duplicate/group identity where used. |
| Membership | Ordered eligible IDs, membership hash, data role and allowed phase. |
| Reference labels | Verified label semantics and an ID-keyed label artifact; labels may be separate from inference inputs. |
| Eligibility lineage | Parent snapshot, excluded IDs/reasons, transformations and resulting counts. |
| Preprocessing | Versioned tokenization, special-token, padding, truncation and length configuration. |
| Integrity and access | Artifact hash, durable location and exposure/access references. |

A path alone is not an identity: its contents can change. Source snapshots remain unchanged;
eligibility and transformations are represented through manifests under the protocol.
Actual asset/split records are maintained in [DATA_REGISTRY.md](DATA_REGISTRY.md).

### Prediction artifacts

Each row identifies the example and run, injection score and derived label. Retain logits
when diagnostics or selected gate features require them. Original/effective lengths and
truncation metadata must be recoverable when used in analysis. Run metadata supplies the
model/tokenizer, precision, preprocessing and threshold identities.

Define expected row coverage, shape and score semantics explicitly. A failed prediction
has an ID-keyed failure record instead of disappearing from the table. Reference labels can
be joined separately so inference does not require label access. Shared numerical and
coverage checks are specified in RESEARCH_PROTOCOL.

### Run manifest

A machine run manifest connects phase/purpose, source assets, input membership,
configuration, code identity, execution environment, threshold artifacts, raw outputs and
completion state. Effective dtype/module evidence, device placement and relevant precision
flags must be linked. Retain output hashes and coverage evidence.

The human [EXPERIMENT_REGISTER.md](EXPERIMENT_REGISTER.md) links the manifest, execution and
resume information, outputs and actual state. Planned, running, failed, incomplete,
complete and invalidated runs must remain distinguishable. Versioned artifact identity
allows a reported result to remain traceable after a later repeat or amendment.

### Measurement artifacts

Each raw timing sample needs a request/batch identity, repetition ID and value, linked to
workload lengths, batch size, timing boundary, warm-up policy, synchronization and
cache/loading state. Name its unit and statistic type: request latency, batch latency,
amortized time per item or throughput.

Memory artifacts identify measurement method and scope, baseline/reset state, model
footprint, peak allocated/reserved device memory where available, and host-memory sampling.
Storage measurements identify the saved representation. Unavailable values remain
explicitly unavailable. The definitions and fair-comparison requirements are owned by
RESEARCH_PROTOCOL; cascade component boundaries are owned by EXTENSION.

### Fitted gate and feature artifacts

Every fitted gate links a versioned feature definition, fitted transform, training
membership, target-construction rule, fitting configuration, validation-selection procedure,
parameters and escalation cutoff. The associated classification threshold remains separately
identifiable. Training and calibration/selection membership must be recoverable for leakage
checks.

Each feature definition specifies its source and availability before high execution, any
extra tokenization or retained activations, and acquisition/runtime-memory measurements.
The deployed feature schema excludes target-only columns. This separation must apply to
preprocessing and feature construction as well as to the estimator itself.

### Escalation traces

A trace records request ID, low result, permitted feature/gate output, route decision,
whether high precision actually executed, final selected score/label, failure state and
linked cost measurements. IDs must survive routed-sub-batch rearrangement so a result cannot
be returned to the wrong request.

The executor returns the original low result when not routed and the corresponding high
result when routed. Averaging or choosing between scores would be a different research
policy, not an implicit implementation detail. Gate-specific endpoint, batching and replay
checks are defined in [EXTENSION.md](EXTENSION.md#6-gate-correctness-checks).

A cost trace identifies which components are independently timed and which are already
included in an end-to-end timer. The reference to the selected residency/loading scenario
prevents interpreting a low-model footprint as the complete cascade's peak memory.

## Reuse and implementation boundaries

Artifacts can be reused when source versions, memberships, labels, preprocessing, score
semantics, precision configuration and coverage remain compatible under RESEARCH_PROTOCOL.
Changed contracts require revalidation and identification of invalidated results. Stable
run IDs and hashes permit this decision without trusting file names or old chat context.

The Part 1 closeout in [PHASE_RECORDS.md](PHASE_RECORDS.md) records reusable interfaces,
checked assumptions, defects and conditions of validity. Large artifacts need durable
team-accessible locations and hashes referenced by their data/run records. Environment and
scheduler configuration should be selected for the actual implementation; they do not
alter these data and component contracts.
