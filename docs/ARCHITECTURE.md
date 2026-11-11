# Architecture and artifact contracts

This document specifies logical components and the information they exchange. The
quality-analysis and reporting components now have a development implementation described
below; other components remain planned. Backend choices remain implementation decisions. Scientific rules belong in
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

## Implemented development evaluation interface v1

`precision_benchmark/evaluation.py` implements pure metrics and paired comparisons;
`artifacts.py` validates saved data; `report.py` generates analysis artifacts;
`__main__.py` exposes the CLI. No inference dependency is required. The executable example
is [tests/fixtures/synthetic/comparison.json](../tests/fixtures/synthetic/comparison.json).
Its deliberately invented scores are fixtures, not experimental results.

### Data owner handoff

Supply UTF-8 JSONL with one object per nonblank line and unique stable `example_id` values.
This file is the expected complete population, not a list inferred from successful predictions.
Reference `label` is integer 0 (benign) or 1 (injection); booleans and strings are rejected.

```json
{"example_id":"revision:train:42","label":1,"original_tokens":700,"effective_tokens":512,"truncated":true}
```

The three token/truncation fields may all be omitted for all examples; otherwise supply
all three for every example. Counts are nonnegative integers under the same token-counting
definition, with effective <= original and `truncated == (effective < original)`.
The preprocessing record must define counting before padding, including special-token policy.
Do not include raw prompt text in evaluation exports. Dataset audit, eligibility, label
orientation and duplicate isolation remain upstream responsibilities requiring review.

### Inference owner handoff

Export one JSONL file per treatment with all expected IDs exactly once. Row order does not
matter; analysis joins by ID. Each row must include:

```json
{"example_id":"revision:train:42","run_id":"R-example-fp32","score":0.73,"prediction":1}
```

`score` is the finite injection-class score in [0,1], not the top-label confidence.
`prediction` must equal `int(score >= threshold)`. An optional `label` is checked against
the separate expected-label file. Other row fields (such as logits) are permitted but not
used by this evaluator. Failed predictions must not be removed to create a smaller success
population: retain upstream failure records and leave the run incomplete.

Each run has a JSON manifest; see [fp32.run.json](../tests/fixtures/synthetic/fp32.run.json).

| Field | Required meaning |
|---|---|
| `run_id`, `precision`, `status` | Unique ID; exactly one of `fp32`, `fp16`, `int8`; `complete` only after upstream checks. |
| `data_role`, `population_id` | Same as comparison manifest. Real roles supported now: `eligible_training`, `eligible_validation`; fixtures use `synthetic`. |
| `threshold`, `threshold_source` | Same numeric threshold and nonempty provenance reference across runs. A provisional pilot threshold must be identified as such; validation-selected thresholds link FP32 validation evidence. |
| `model_revision`, `tokenizer_revision`, `dataset_revision` | Immutable source identities, equal across all treatments. |
| `preprocessing_id` | Immutable shared record defining tokenizer configuration, padding, truncation, length and label/score mapping. |
| `input_schedule_id` | Immutable shared record of input IDs/order and batch composition, regardless of saved row order. |
| `environment_id` | Shared comparable hardware/software/attention-backend record; different job IDs may be recorded separately. |
| `score_semantics` | Literal `p_injection`. |
| `code_revision` | Same inference code revision or source-tree hash across treatments. |
| `precision_evidence` | Treatment-specific evidence reference covering actual dtype/module conversion, device placement and flags. |
| `predictions` | Object with `path` and lowercase `sha256` of the exact prediction file bytes. Path is relative to this run manifest. |

Metadata equality prevents accidental incompatible comparisons; it cannot prove that
someone used the declared configuration or that the source records are correct. A second
contributor must review the scientific evidence before relying on real results.

### Integration owner handoff

The comparison JSON contains `schema_version: 1`, `data_role`, `population_id`, `threshold`,
`threshold_source`, an `examples` file reference and a `runs` list of three file references.
Each file reference is `{ "path": "relative/file", "sha256": "actual-sha256" }`;
paths are relative to the containing manifest. Compute hashes after writing final bytes:

```sh
python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' path/to/file
```

Hash predictions first, then write/hash run manifests, then write the comparison manifest.
Do not use synthetic metadata or hashes for real runs. Preserve source manifests and
predictions together; report hashes identify bytes, not a durable storage location.

```sh
python3 -m precision_benchmark --manifest path/to/comparison.json --output outputs/pilot-comparison-001
```

The command rejects hash mismatches, incomplete runs, missing/extra/duplicate IDs,
conflicting supplied labels, nonfinite/out-of-range scores, inconsistent predicted labels,
incompatible metadata and protected test roles before creating an output directory.
An existing output directory is never overwritten. Exit status is 0 on success and 2 on
input/output failure. Interrupted writes may leave a partial new directory; `report.md`
is written last, and a retry must use a fresh directory or remove only that failed export.

| Output | Contents |
|---|---|
| `report.md` | Readable development comparison, provenance and limitations; synthetic data prominently labeled. |
| `quality.csv` | Supports, confusion counts, accuracy, both classes' precision/recall/F1, macro-F1, FPR/FNR, ROC-AUC, Brier and ECE. |
| `paired.csv` | Candidate-versus-FP32 correctness combinations, disagreement, score shifts and accuracy difference in percentage points. |
| `error_analysis.csv` | ID-level introduced/corrected/shared errors with both scores, threshold distances and optional token metadata. |
| `results.json` | Full-precision results, reliability-bin counts, optional truncation subgroups, run metadata, input and analysis-source hashes. |

CSV string identifiers starting with spreadsheet formula characters are prefixed with an
apostrophe; exact identifiers remain in JSON. Rates are fractions, not percentages; only
`accuracy_delta_pp` uses percentage points. No raw prompts are copied to the error report.
Uncertainty, threshold optimization and measured profiling are not implemented in this
development command. Resource sections explicitly remain unavailable until the profiler
handoff. Held-out analysis requires subsequent implementation and the P1-C freeze.
