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

## Administrative audit components added November 17

`precision_benchmark/data_audit.py` processes pinned PromptShield JSON without displaying
prompt contents. It preserves source bytes, checks cached-file integrity against a retained
receipt, rejects duplicate JSON keys, and emits aggregate counts plus text-free IDs, exact
UTF-8 text hashes, exclusions, and overlap-rule projections. IDs retain the original split
and zero-based source row. Projection files are explicitly not frozen eligibility or A/B
manifests. Character and byte counts are not tokenizer lengths.

`precision_benchmark/model_audit.py` resolves or accepts an immutable selected-model
revision, rechecks the pinned API identity, and records bounded public metadata retrievals.
HTTP failures remain explicit. In the November 17 evidence, retained configuration filenames
contain 401 response text, not valid configuration JSON; consumers must check the manifest's
HTTP outcome. Provider dtype/count declarations are separated from verified tensor/runtime
facts. Neither component executes prompts, downloads weights, or authorizes a phase advance.

The local cache receipt protects against accidental source changes; it is not a signed
attestation of publisher truth. Preserve the first verified download/provenance and review
source changes instead of silently regenerating hashes. DATA_REGISTRY and V-006–V-009 link
the current evidence and limits.

## Team handoff and metric-review request — November 16

Repository-only request prepared at Shreyas's direction; no email, chat message or GitHub
issue was sent. Assignments below follow the proposed split and need team confirmation.

**Handoff request:** The development evaluator is ready. Please use the v1 interface above
so the same command can compare all three treatments. For the November 18 checkpoint,
please aim to hand off complete development artifacts by November 17, noon Eastern, or
record the specific blocker and expected availability. This is a proposed integration
cutoff, not a confirmed teammate commitment.

| Proposed owner | Requested handoff | Acceptance check |
|---|---|---|
| Viraj — data | Audited eligible development examples JSONL, population identity, labels and optional token lengths; data/eligibility evidence in DATA_REGISTRY. | Unique IDs; verified 0/1 semantics; duplicate and held-out isolation reviewed; expected population includes every intended example. |
| Yash — inference | FP32/FP16/INT8 prediction JSONL files and complete run manifests with hashes and actual treatment evidence. | Exactly the expected IDs in each run; finite injection scores; shared threshold and compatible metadata. Keep failed/incomplete runs identified. |
| Hareeshwar — profiling | Raw timing/memory artifacts and a summary identifying hardware, length/batch schedule, repetitions, warm-up, synchronization, loading boundaries and units. | Matched workloads; distinguish per-request from batch latency; include sample counts. Use RESEARCH_PROTOCOL; the evaluator does not yet import profiling files. |
| Shreyas — integration | Assemble the comparison manifest, run the evaluator, review changed errors and add reviewed resource measurements to the report. | Traceable tables and clearly separated development observations, limitations and next steps. |

**Review request:** One teammate other than Shreyas should review
`precision_benchmark/evaluation.py`, `tests/test_evaluation.py`, and D-007 in DECISIONS.
Reviewer is unassigned; review has not occurred. Please check:

- Positive class is injection; threshold equality predicts injection; FPR/FNR use the correct denominators.
- Per-class and macro-F1, undefined values, tied-score AUC and calibration bins agree with the documented definitions.
- Paired comparisons join IDs and count corrected/introduced errors relative to reference labels, not presumed FP32 correctness.
- The hand-calculated tests support the formulas; run `python3 -m unittest discover -s tests -v` and inspect the fixture, rather than relying only on a green test result.
- No synthetic number is described as empirical performance; real eligibility, label mapping and precision evidence still require upstream review.

Record the reviewer's name, date, reviewed commit, findings and disposition in VALIDATION_LOG
and the actual review contribution in CONTRIBUTIONS. If changes are required, identify
affected outputs and rerun the relevant checks before treating the review as complete.

## Optional metadata authentication — November 17 follow-up

The model audit now accepts explicit `--auth local` or `--auth prompt`, preserving its
unauthenticated default and lightweight-file scope. Authentication mode/request status and
successful authenticated file responses are separate from configured label and runtime
verification. Missing credentials fail before output creation/network access. Credentials
are never persisted by this command; redirects are restricted to HTTPS `huggingface.co`.
See V-013/V-014 for synthetic security/compatibility checks and the reviewed redirect-error repair and their limits. This adds no model
execution or permission to access held-out performance, and changes no prediction contract.

## P1-A implementation and review handoff — November 17 follow-up

`partition_data.py` implements the exact D-008 construction from three expected-hash inputs:
text-free identities, retained provenance and the source receipt. It rejects unapproved
source revisions, malformed/conflicting identities, changed inputs and existing output
directories. Four role-specific JSONL populations, exclusions, access conditions and summary
retain original lineage and hashes. Current artifacts are SPLIT-001–004; declarative pending
release conditions are not yet inference-loader enforcement. Human review remains pending.

`contract_audit.py` uses optional Hub/requests dependencies to retrieve only the fixed pinned
configuration/tokenizer allowlist and two bounded safetensors-header ranges. It validates
source sizes and Git/LFS content hashes before retention, preserves configured proxy/CA
settings, strips authorization on origin changes and suppresses sensitive error details.
It never requests tensor payloads. Complete retrieval is not successful model execution;
V-022/V-023 give actual checks and limits. Native tokenizer dependencies remain blocked locally.

The reviewed source/head contract yields two logits and injection index 1 under the existing
protocol. Explicitly derive the injection score from both logits; no top-label shortcut.
Actual tokenizer wrapper behavior and pooling remain runtime requirements under Q-014.
The serialized backend PAD/truncation settings and wrapper settings differ; pin the actual
wrapper and record explicit arguments. Original raw source text/hashes stay unchanged.

**Proposed next bounded pilot, not yet authorized or executed:** after the remaining P1-A
checks and a working approved runtime, audit development token lengths and
select 128 eligible training examples with class/length coverage. Start with original
unpadded batch one, explicit cap chosen from 512/1024/2048 using that audit, no chat template
or manual EOS. Verify loaded head/frozen weights, finite two-logit scores, actual FP32/FP16/
LLM.int8 module treatment and matching IDs/tokens/masks. Include synthetic literal-EOS,
empty/all-masked rejection and truncation boundaries. Larger batching needs a separately
reviewed pooling/position policy and agreement tolerance. Retain failures and prediction
manifests; no final threshold or hardware benefit claim comes from this pilot proposal.

**Coordination under D-009:** teammates implement their assigned work and push to GitHub.
Inspect actual contributions before integration. Notify affected teammates of overlapping
work and shared choices; do not wait for a separate attestation or human interpretation.
Viraj needs the completed audit/split and preprocessing coordination update, not a request
to redo the audit. Unperformed human review and unknown history remain accurately recorded.
Do not open test prompts/performance to prepare this handoff.

## Development input loader - D-009 continuation

`input_data.py` exposes `load_development` for the future inference wrapper and a CLI
preflight. The caller supplies an expected hash for the D-009 access record plus partition
and original-source directories. The loader checks both parent hashes, original split/ID
lineage and the full population before opening the role's fixed raw source filename.
Only `eligible_training` and `eligible_validation` are accepted; test-role denial precedes
all reads. It never opens `test.json`.

Returned frozen `InputRecord` objects contain IDs, lineage, hash and unchanged prompt text;
prompt text is hidden from repr. Reference labels remain in a separate tuple. The CLI
exports text-free identity JSONL and a preflight receipt, not tokens or predictions. It
validates full expected coverage instead of constructing a success-only population.
D-009 overrides the historical teammate-wait condition for the two development roles;
it neither changes membership nor releases held-out performance. Runtime tokenization
and chosen pooling/caps still require the next approved executable environment.

## Executed tokenizer audit and separate remaining administrative scope

`tokenizer_audit.py` now has a complete native run for both development roles: explicit
local-only fast tokenizer/config loading, uncapped/unpadded baseline, exact synthetic
controls and every-row 512/1024/2048 prefix checks. Development outputs retain IDs/hashes,
lengths and integer diagnostics without real prompts/tokens. Source/model behavior and
limits are V-034/V-035 and RES-003. The model itself was not loaded.

The separately prepared `holdout_lengths.py` accepts only a fixed administrative official-test
length role and source hash/support. It computes only total original lengths and a total
histogram, retaining no row linkage, cap comparison or A/B/class-length breakdown. It reuses
the exact checked tokenizer functions but leaves `input_data` protected-role denial unchanged.
This explicit administrative exception needs its own data-scope authorization; it does not
release test performance or supply gate-fitting data. The prepared five-minute job reuses
the existing environment/assets, with no installation or model/GPU request.

## P1-B next bounded pilot proposal - not executed or frozen

The completed P1-A closeout supplies inputs. Carry forward the development-derived
cap 1024/original unpadded batch-one proposal; do not choose settings from the newly completed
official-test administrative histogram. Proposed size is 128 eligible training examples,
64 per class, with documented short/mid/long coverage. An example defensible construction
is 48 per class at original length <=512, eight at 513-1024, and eight above 1024, selected by
a recorded deterministic ordering before model outputs. This deliberately enriches tails
for diagnostics and is not a representative quality estimate. Membership is not built or
frozen here.

Execute the same fully hashed checkpoint in strict FP32, FP16 and bitsandbytes LLM.int8.
Use one matched compatible GPU/allocation and record exact installed versions, attention
implementation, device mapping, no-grad/eval state and precision flags. Inspect converted
linear layers and retained embeddings/norms/head rather than trusting nominal labels.
Keep model PAD unset for the original unpadded reference. Synthetic EOS/empty/mask cases
must test actual model behavior; tokenizer agreement alone does not prove logit equivalence.
The pilot may use a clearly provisional common 0.5 scoring threshold; final threshold
selection remains FP32 validation-only in P1-C. No classifier fine-tuning is permitted.

Before submission, prepare the checkpoint storage/download (~1.19GB), GPU/dependency
preflight, exact 128-ID manifest and shared input schedule, three run manifests, dtype/module
evidence and failure/coverage checks. A proposed bounded execution ceiling is one compatible
GPU for 20 minutes after environment preparation; actual preparation and job settings must
be reviewed before execution. Require complete finite two-logit/injection-score outputs for
all intended IDs in all treatments, then regenerate the development comparison. Preserve
failures. Resource observations are pilot feasibility evidence, not the final profiling study.
No GPU allocation or model run has been submitted under this proposal.
