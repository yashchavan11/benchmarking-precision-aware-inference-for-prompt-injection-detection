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
| R-P1-A-20261117-03 | P1-A / authenticated pinned configuration contract | ASSET-002 | Approved browser retrieval; no weights | RESEARCH_PROTOCOL section 1 | incomplete; config retained, tokenizer pending | model-browser/retrieval.json; V-012 | Automated execution/artifact review; runtime checks pending |
| R-P1-A-20261117-04 | P1-A / authenticated contract | ASSET-002 | Pinned files/header only | RESEARCH_PROTOCOL section 1 | complete within source/header scope | V-022; model-auth/manifest.json | Independent automated review; runtime pending |
| R-P1-A-20261117-05 | P1-A / D-008 construction | ASSET-001 text-free IDs | Eligibility/A-B administrative | D-008 | complete review-ready construction | V-018?V-021; partitions-v2/summary.json | Independent automated review; human release pending |
| R-P1-A-20261117-06 | P1-A / development input contract | SPLIT-001/002 under D-009 | Raw-to-identity preflight only | D-008/D-009 | complete bounded preflight | V-026/V-027; input-preflight/execution.json | Independent automated review |
| R-P1-A-20261117-07 | P1-A / native development tokenizer | SPLIT-001/002 | CPU configuration/length audit | D-009/D-010 | complete; failures preserved | V-031 through V-035 | Independent native-output review |
| R-P1-A-20261117-08 | P1-A / official-test length administration | ASSET-001 official test | Aggregate original lengths only | D-011 | complete | V-036 through V-038 | Independent aggregate review |

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

### R-P1-A-20261117-07 - Original native tokenizer/configuration plan (completed below)

- **Phase/purpose:** P1-A; verify actual local-file tokenizer/config behavior and development token lengths before choosing pilot preprocessing. No classifier, weights, GPU or test performance.
- **Inputs:** D-009/SPLIT-001/002 training and validation only; pinned ASSET-002 seven-file tokenizer/config bundle. Stage manifest binds 50 files (34,894,817 uncompressed bytes); packaged archive 8,415,316 bytes, SHA-256 `75a505f56cda4381c346e6cf97291a3604b67d258b4486e085ecab9585da71c8`. Credentials, weight payloads and official-test source/membership files are excluded.
- **Candidate environment/budget:** Existing Explorer SSH/transfer profiles verified read-only; account `cs5130.202710`, courses partition, one task/two CPUs, 8 GiB, 20-minute maximum, zero GPUs. Python module 3.13.5 is available; isolated environment will use pinned audit dependencies. Scheduler test-only validation succeeded and created no job; no native execution has occurred.
- **Prepared implementation/checks:** Final local stage-03 supersedes two retained packaging attempts; V-029/V-030 record an optimization-sensitive verifier and its repair. `precision_benchmark.tokenizer_audit`, `scripts/tokenizer_audit.sbatch`, and staging verifier. 76 combined local tests passed; native calls were mocked. Independent source/arithmetic/boundary review passed. Local preparation/evidence is under `outputs/runtime-20261117/`.
- **Expected output/completion:** Complete expected-ID coverage for both development roles, synthetic padding/special-token/truncation checks, explicit untruncated lengths and 512/1024/2048 candidate-cap diagnostics, resolved configuration/library/source identities, retained logs/hashes and independent result review. Real prompts/tokens are not exported; exact synthetic vectors are labeled invented. A successful submission or process exit alone is not completion.
- **State when planned (superseded by completion follow-up):** Explicit alternate-execution-route approval requested after Windows denied the local native library. No remote files staged and no actual job ID. Candidate run root is `/scratch/chavan.yas/precision-aware-inference/tokenizer-audit-20261117-01`; create it only after approval and preserve any existing directory instead of overwriting it.
- **Scientific limits:** No study cap, model-pooling adapter, threshold, inference precision treatment or phase closeout is selected here. Model batching equivalence and GPU compatibility remain later checks. Windows protections remain unchanged.

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

### R-P1-A-20261117-03 — Resumed authenticated configuration audit

- **Purpose/phase:** P1-A, verify selected pinned configuration/tokenizer access and declared contract without weights, inference or data-performance inspection. Completion requires retained configurations/tokenizer evidence with validated identities and explicit remaining runtime checks.
- **Conditions/input:** Windows/Python 3.11.9 for local file checks; authorized signed-in Chrome for the exact ASSET-002 revision. No training/validation/test inputs used in retrieval.
- **State/output:** Incomplete. Model config retained and hashed in `outputs/resume-20261117/model-browser/`; receipt in V-012. Tokenizer retrieval attempted but no completed file located. No process to monitor or weight checkpoint to resume.
- **Failure/recovery:** Initial requested save destination was empty; actual download recovered from default Downloads and copied byte-for-byte. Browser automation subsequently stopped on current-URL confidence; no attempt was made to bypass the stop. Local credentials remain absent.
- **Checks/exposure:** V-012 / EXP-003. Config's label orientation is established as a declaration; actual head/pooling/score and treatment execution remain unverified. V-013 is software preparation only and was not used for real authenticated retrieval.
- **Next:** Retain pinned tokenizer assets through authorized browser or local credential path, compare source identity/hashes, then complete the configuration contract. Keep R-P1-A-20261117-02 and its unauthenticated failures intact.

### R-P1-A-20261117-04 — Pinned model/tokenizer contract audit

- **Purpose/data role:** P1-A administrative asset verification only; establish declared labels, actual tensor header and full tokenizer source identity without prompts, tensor payloads or performance.
- **Conditions/execution:** Windows/Python 3.11.9; source audit Transformers 4.57.1; Hub 0.36.2/requests 2.34.2 for authenticated retrieval. Exact invocation/source hash is `outputs/contract-20261117/retrieval-execution.json`; installed package inventory and policy failures are V-017. Browser attempts and failed responses remain preserved.
- **State:** Complete for the bounded source/header audit, V-015/V-016/V-022. All seven intended files verified, header ranges complete, independent review passed. No running process/checkpoint. No tokenizer encoding or classifier execution is claimed; that dependent task remains blocked by Q-015 and pending design/review checks.
- **Artifacts/exposure:** `outputs/contract-20261117/model-auth/`, library evidence and safe compact records linked in ASSET-002; EXP-004. Credentials remain outside the repository. The full checkpoint checksum has not been independently computed.
- **Next:** Use an approved executable runtime for token lengths, explicit wrapper/input behavior and pooling checks before the proposed pilot.

### R-P1-A-20261117-05 — Approved eligibility and A/B construction

- **Purpose/data role:** Implement D-008 from the retained identity/provenance/receipt hashes; administrative IDs/reference labels only, no model outputs or raw prompt display.
- **State:** Complete for review-ready construction and automated isolation checks. Initial `partitions/` retained; corrected current `partitions-v2/` has identical population/exclusion/access bytes. V-018–V-021 distinguish initial checks, independent actual-membership review, alternate-revision failure and correction. Human scientific review/release remain pending.
- **Conditions/output:** Python 3.11.9 / Windows, standard library; exact commands/environment/source hashes in each directory's `execution.json`. SPLIT-001–004 and compact summary retain all population/file/ordered hashes. All intended source IDs are accounted for; no active job or checkpoint.
- **Exposure/limits:** EXP-004. Exact isolation and class support do not establish unseen external history, near-duplicate independence, statistical power or P1-A completion. No test-performance allocation choice was made after observing results.

### R-P1-A-20261117-06 - Approved development input preflight

- **Purpose/phase:** P1-A input-contract verification and inference component preparation; bind actual development text to the selected identities without model execution.
- **Inputs/authority:** SPLIT-001/002, pinned ASSET-001 source bytes, D-008 construction and explicit D-009 development-access amendment. Only training/validation; no held-out source or outputs.
- **Conditions/execution:** System Python 3.11.9 on Windows, standard library. Exact two CLI commands, source hashes and 66-test run are in `outputs/continuation-20261117/input-preflight/execution.json`.
- **State/output:** Complete bounded input preflight for 18,909 training and 1,000 validation rows. Text-free exports/preflight JSON retained in `training/` and `validation/`; raw text kept verbatim in internal records only. No active job/checkpoint.
- **Checks/limits:** V-026/V-027, EXP-005. Teammate attestations are not a prerequisite under D-009. Token lengths, tokenizer/pooling execution, precision treatment and model quality/resource outcomes remain unverified; Test-A/Test-B freezes unchanged.

### R-P1-A-20261117-07 execution and completion follow-up

D-010 approved the reviewed CPU route. Private scratch roots `tokenizer-audit-20261117-01`
through `-04` preserve all attempts. Jobs11954782/11954830 failed during initialization,
before setup; job 11954889 installed the environment then failed a proxy mock-test gate.
V-031 through V-033 record causes, repairs and compatibility. Fresh job 11955247 reused the
complete environment, requested two CPUs/8 GiB with an 11-minute limit, and completed with exit 0:0
in 45 seconds on c0584. All 76 tests and native synthetic/development checks passed. Combined
allocated elapsed across attempts was 523 seconds; no GPU was requested.

**Current state: complete for native development tokenization.** Local retained outputs,
logs, package locks and environment-reuse receipt are under
`outputs/runtime-20261117/attempt-04/`; prior setup is in `attempt-03/`. Execution-01 through
-04, stage receipts and `retrieval-receipt.json` retain identities and histories. V-035
independently verified full intended coverage and aggregates before RES-003. No active job
remains. Model inference, selected preprocessing cap and official-test token lengths are
not completed by this run.

### R-P1-A-20261117-08 - Prepared aggregate official-test token-length audit

- **Purpose:** Complete the remaining all-source length administration required by the protocol. Fixed pinned official test only, untruncated/unpadded tokenizer call; no classifier, cap comparison, A/B breakdown or development selection.
- **Prepared output:** Total length summary plus sparse total length histogram for independent reconstruction, source/support/runtime hashes and a completion manifest. No row IDs/hashes, prompts or token vectors exported. Existing inference/development test-role guards are unchanged.
- **Candidate execution:** Two CPUs, 8 GiB, five-minute maximum on Explorer courses allocation; reuse the verified environment and existing tokenizer assets without installation. Local code/mock checks pass; separate reviewed package in `outputs/holdout-prep-20261117/` contains the pinned test source and no weights/credentials.
- **State when planned (superseded by completion follow-up):** Additional data-scope approval requested because D-010 explicitly excluded official test. No remote transfer, actual native test processing or submitted job. Completion requires complete 23,516-row support, source/runtime identity checks, internally consistent aggregate histogram/statistics and independent review. Do not claim phase completion from preparation.

### R-P1-A-20261117-08 execution and completion follow-up

D-011 separately authorized the reviewed administrative scope. The 6.4 MB package was
transferred and all member/hash checks passed before actual job 11956265 submission.
Private run root: `/scratch/chavan.yas/precision-aware-inference/holdout-length-audit-20261117-01`.
The job reused the existing environment and tokenizer assets, requested two CPUs/8 GiB/
five minutes, and completed with exit 0:0 in 25 seconds on c0617. The remote suite passed 85 tests.

**Current state: complete within aggregate-only administrative scope.** All 23,516 expected
rows and source class support are accounted for. V-038 independently reconstructs total
statistics from the histogram and verifies all identity/runtime/scope bindings. Local
outputs/logs are `outputs/holdout-prep-20261117/attempt-01/`; execution/retrieval receipts
and reviews are retained beside them. No active job remains. No model performance was
released, no cap selected, and no Test-A/Test-B membership or inference guard changed.
