# Experiment register

This register is the index of planned and executed experiments and administrative audit runs.
Administrative runs are recorded below; no model-performance or resource experiment has run.
Each entry links the machine-readable run manifest and raw outputs described in
[ARCHITECTURE.md](ARCHITECTURE.md), rather than copying prediction tables or prompts here.
The [research protocol](RESEARCH_PROTOCOL.md) governs run comparability;
[EXTENSION.md](EXTENSION.md) supplies routing-specific measurement requirements.

## Run identity and states

A run ID has the form `R-[phase]-[date]-[sequence]`. This is a naming pattern, not an
existing experiment. A rerun receives a new ID and a relationship to its predecessor;
completed artifacts are retained instead of overwritten.

| State | Meaning |
|---|---|
| `planned` | Question, inputs and intended procedure are registered; execution has not begun. |
| `running` | Execution has begun and its current job/process can be identified. |
| `failed` | A recorded error prevented the intended experiment from completing. |
| `incomplete` | Some expected outputs or required validation are missing, even if the process exited normally. |
| `complete` | Expected coverage, output integrity and the run's required checks are established. |
| `invalidated` | A later identified defect withdraws the run's previously accepted validity; retain the cause, affected conclusions and recovery or replacement reference. |
| `excluded` | Retained evidence is not eligible for a specified comparison; the reason and impact are explicit. |
| `superseded` | A later identified run replaces this run for a stated use; its history remains available. |

## Run index

| Run ID | Phase / question | Input membership ID | Treatment / policy | Protocol / decision IDs | State | Manifest / output integrity | Owner / reviewer |
|---|---|---|---|---|---|---|---|
| R-P1-A-20261117-01 | P1-A / source schema, duplicate and overlap audit | ASSET-001 official splits | Administrative processing; no classifier | RESEARCH_PROTOCOL section 3 | complete for bounded audit; no phase closeout | audit-v3 provenance; V-008 | Local automated execution/independent review; human signoff pending |
| R-P1-A-20261117-02 | P1-A / selected checkpoint metadata and labels | ASSET-002 | Public source retrieval; no weights | RESEARCH_PROTOCOL section 1 | incomplete for full asset/label audit | model/summary.json; V-009 | Local automated execution/review; authorized access pending |

### R-P1-A-20261117-01 — Administrative PromptShield audit

- **Purpose/input/expected output:** Before final inference, establish pinned official schema, class support, duplicates/conflicts, source identities and development-overlap projections. All official splits are eligible only for administrative computation; no model performance is computed or inspected.
- **Execution:** Windows / Python 3.11.9, standard library, no GPU. `precision_benchmark.data_audit` at source hash in V-008; pinned source and all paths/hashes in ASSET-001 and its retained provenance. Actual invocation/history is `outputs/asset-audit-20261117/dataset/execution.json`.
- **State/output:** Complete administrative audit-v3, no active job. All 43,425 intended rows covered; source bytes and all identity/output hashes verified. Original audit-v1/v2 retained; V-007's reusable-cache defect was repaired and V-008 revalidated the final version without changing input data.
- **Evidence/exposure:** V-006–V-008, EXP-002. Full class/group/length summaries, stable text-free identities, empty exclusion list and projected train/validation outputs retained. RESULTS RES-001 scopes the finding. No A/B assignment, eligibility freeze, token-length study, inference result or P1-A completion is implied.
- **Next:** Resolve model access/labels and prior team exposure; review allocation and final eligibility under Q-001–Q-004/Q-013.

### R-P1-A-20261117-02 — Model metadata and access audit

- **Purpose/input:** Establish exact selected-model/tokenizer identity and configuration evidence without weights or performance inspection. Pinned public metadata acquisition completed; required private configuration remained unavailable.
- **Execution/output:** Windows / Python 3.11.9, `python -m precision_benchmark.model_audit --output outputs/asset-audit-20261117/model`; source hash and eight HTTP response hashes in `summary.json`, mirrored in `docs/evidence/p1a-model-metadata-20261117.json`.
- **Incomplete condition:** Four gated requests returned HTTP 401. Script completion/exit zero means the public access audit ran; it does not establish the requested labels/head/tokenizer contract. No process is still running, and there is no checkpoint to resume.
- **Validation/continuation:** V-009, ASSET-002 and Q-012. Obtain authorized access, retrieve pinned configurations in a new artifact location, then verify full model-label semantics. Keep failed responses; do not overwrite them or infer class orientation.

## Run record template

### R-[phase]-[date]-[sequence] — [question]

- **Owner / date / phase:** [actual values]
- **Purpose and prior hypothesis:** [question and expected mechanism, not a promised result]
- **Experiment type:** [pilot / quality evaluation / measured system profile / offline policy replay / other justified analysis]
- **State and last transition:** [state, time and evidence for the transition]
- **Prerequisites:** [phase gate, protocol freeze and exposure eligibility references]
- **Input identity:** [asset/split records, ordered row-ID hash, labels and exclusions]
- **Model/tokenizer identity:** [asset records and immutable configuration references]
- **Treatment or policy:** [precision/quantization configuration, preprocessing and batch schedule;
  for routing, low/high pair, feature pipeline, fitted gate and operating-point artifacts]
- **Machine-readable manifest:** [location, integrity hash and schema/version]
- **Code/configuration identity when implemented:** [version/commit, uncommitted working-state description and hashes]
- **Execution conditions:** [environment reference, software versions, device/allocation and timing/memory scope]
- **Reproduction and job tracking:** [actual invocation or job-script reference, scheduler/job ID,
  resource allocation, logs, output location and checkpoint/resume procedure]
- **Measurement plan:** [selected metrics, repetitions/resampling, seed, scope and governing decision]
- **Outputs and integrity:** [prediction, timing, manifest and other artifact references/hashes]
- **Coverage and failures:** [expected versus observed IDs, omissions, duplicates, nonfinite values,
  failure reason and diagnostic artifacts]
- **Validation links:** [V-records and any remaining conditions for complete status]
- **Result links:** [RES-records derived from this run]
- **Exposure record:** [revealed information, audience and date; DATA_REGISTRY reference]
- **Relationships:** [matched baselines, candidates, reruns, superseded records and affected conclusions]
- **Exclusion or supersession rationale:** [specified use, reason, uncertainty/claim impact and replacement ID]
- **Next action:** [analysis, diagnosis, justified rerun or closeout]

Interrupted execution is recorded as `incomplete`, with its actual job state and recovery
details. Failed, invalidated and excluded runs remain part of the record. Their status and
diagnostic value are separate from whether their outputs qualify for aggregate conclusions.
