# Experiment register

This register is the index of planned and executed experiments. No runs are recorded yet.
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
