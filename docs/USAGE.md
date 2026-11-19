# Tool usage

This guide describes the executable tools and their input contracts. Research methods
belong in [RESEARCH_PROTOCOL](RESEARCH_PROTOCOL.md) and [EXTENSION](EXTENSION.md);
registered asset/population identities belong in [DATA_REGISTRY](DATA_REGISTRY.md).
Execution history, measured checks and current work are recorded separately in
[EXPERIMENT_REGISTER](EXPERIMENT_REGISTER.md), [VALIDATION_LOG](VALIDATION_LOG.md) and
[STATUS](STATUS.md).

## Requirements

Use Python 3.10 or newer from the repository root; substitute `python3` for `python` where
appropriate. The evaluator, data audit, population builder and development input loader
use the standard library. Authenticated contract retrieval additionally uses
`huggingface-hub` and `requests`; native tokenizer commands use Transformers and tokenizers.
Pinned audit dependencies are in [requirements-audit.txt](../requirements-audit.txt).
The separate CUDA pilot dependencies are in
[requirements-inference.txt](../requirements-inference.txt); its PyTorch wheel source and
execution requirements are described below.

Use an isolated environment appropriate to the execution system. Installing packages or
passing dependency resolution does not establish that native libraries execute correctly
or that a GPU backend is compatible. The audit requirements are not a complete inference
environment. Recorded environments and any demonstrated runtime constraints are in STATUS
and the validation log.

Use a **new output directory** for each command. Preserve incomplete/failed outputs and
inspect completion metadata before reuse. Downloaded data, tokenizer assets, model weights,
environments and generated outputs are excluded from Git; their existence on another
contributor's machine is not implied by a project-relative path.

## Offline evaluation

```sh
python -m precision_benchmark --manifest tests/fixtures/synthetic/comparison.json --output outputs/synthetic-demo
```

The fixture contains eight invented examples, not model predictions. The command writes:

| File | Contents |
|---|---|
| `report.md` | Readable comparison with scope and provenance. |
| `quality.csv` | Classification, ranking and calibration metrics. |
| `paired.csv` | Disagreements and corrected/introduced/shared errors relative to FP32. |
| `error_analysis.csv` | ID-level paired outcomes and available length context. |
| `results.json` | Full-precision results, reliability bins, input/source hashes and metadata. |

For real saved development predictions, supply the exact comparison/run/example JSON and
JSONL contracts in [ARCHITECTURE](ARCHITECTURE.md#implemented-development-evaluation-interface-v1).
The injection score is distinct from top-label confidence. All three treatments must have
the same expected IDs, compatible configurations and a shared threshold; failures cannot
be removed to make a smaller success-only population. The evaluator rejects protected
test roles until the required evaluation functionality and freezes are in place.

## Administrative source audits

These commands inspect source identities and aggregate properties; they do not execute
a classifier or choose evaluation populations. The revisions below identify the registered
sources; changing them requires an explicit compatibility/method review.

```sh
python -m precision_benchmark.model_audit --revision 05ff9bfd1f28c5228e53121d5ee4427bb5205212 --output outputs/model-metadata
python -m precision_benchmark.data_audit --revision a5234cb1f5cdb256600cab64b8c961195b5e8404 --raw-dir data/raw/promptshield/a5234cb1f5cdb256600cab64b8c961195b5e8404 --download --output outputs/data-audit
```

The model audit is unauthenticated by default. Add `--auth local` to read an existing
configured Hub credential, or `--auth prompt` to enter one through a hidden prompt in a
real local terminal without saving it. Never supply tokens as command-line arguments.
Gated retrieval requires an account with access to the selected repository.

The command records HTTP outcomes, including failures. A successful process exit does not
mean every gated file was retrieved: check `summary.json` before parsing retained files.
The dataset audit downloads its pinned source files on first use and validates cached bytes
against retained provenance on reuse. Its development identities are projections until the
population construction and access decisions are applied. Administrative processing does
not authorize browsing protected prompts or model outcomes.

The full tokenizer/configuration and bounded checkpoint-header retrieval uses:

```sh
python -m precision_benchmark.contract_audit --output outputs/model-contract
```

It requires an existing local Hub credential and the optional retrieval dependencies.
It retrieves the fixed tokenizer/configuration allowlist and only checkpoint-header ranges,
not the full tensor payload. Full-weight integrity and inference behavior need separate
checks before model execution.

## Population construction and development inputs

The population builder consumes text-free audit identities, their provenance and the
source-integrity receipt. It implements the selected whole-group construction and rejects
unapproved revisions, altered inputs and existing output directories.

```sh
python -m precision_benchmark.partition_data --help
python -m precision_benchmark.input_data --help
```

| Command | Required inputs |
|---|---|
| `partition_data` | Approved dataset revision; identity, provenance and receipt paths with their expected SHA-256 values; new output directory. |
| `input_data` | `eligible_training` or `eligible_validation`; access-record path and expected hash; partition and original-source directories; new output directory. |

Use the identities and exact hashes registered in DATA_REGISTRY and the linked compact
evidence. Exact historical invocations are retained with their experiment execution records.
Do not substitute hashes calculated from unverified files merely to satisfy a check.
Reacquisition can change receipt timestamps or paths; reuse compatible registered artifacts
or explicitly verify and document equivalent source bytes and reconstructed populations.

The development loader validates original source position, ID, label, raw-text hash and
lengths. It preserves prompt strings internally, keeps reference labels separate from
inference inputs, and exports only text-free preflight records. Protected roles are rejected
before file reads. A preflight is not tokenization or model inference.

## Native tokenizer diagnostics

```sh
python -m precision_benchmark.tokenizer_audit --help
python -m precision_benchmark.holdout_lengths --help
```

`tokenizer_audit` requires the exact retained tokenizer assets/manifest hash, the development
access record/hash, partition/source directories and a new output directory. It checks both
development roles with local-only fast-wrapper calls, an explicit unpadded/untruncated
baseline and the diagnostic 512/1024/2048 caps. It exports development identities, hashes,
lengths and summaries, not real prompts or token vectors. Diagnostic caps do not select
the study's preprocessing configuration, and token/mask agreement does not prove model-logit
equivalence.

`holdout_lengths` is a separate, narrowly authorized administrative command. It requires
the fixed `administrative_official_test_lengths` role, pinned source/hash, exact tokenizer
assets/manifest hash and a new output directory. It exports total original length statistics,
a total histogram and provenance only. It does not export row linkage, cap comparisons,
class-length or Test-A/Test-B breakdowns, or model results. This exception does not release
protected data to inference or development selection.

The [development job](../scripts/tokenizer_audit.sbatch) and
[administrative job](../scripts/holdout_lengths.sbatch) show the reviewed Slurm invocations.
They contain execution-system-specific account, module and path assumptions. Review the
resource request, data role, asset/environment references and approved scope before using
or adapting them; do not submit them as generic templates without those checks. Stage
verifiers bind file identities and exclude content outside each job's stated scope.

## Full checkpoint and inference environment

Reuse the registered checkpoint, tokenizer assets and verified environment when available.
Check their hashes and compatibility before copying or loading them; a fresh conversation
or checkout does not require another download or installation. Asset identities and the
full checkpoint digest are registered in [DATA_REGISTRY](DATA_REGISTRY.md). The seven-file
tokenizer directory must include its original verified `manifest.json` and
`source-metadata.json`; matching filenames alone do not satisfy the runner's checks.

For an authorized first acquisition, use an existing private Hub login outside the repository:

```sh
python scripts/fetch_pilot_checkpoint.py --output outputs/full-checkpoint
```

This command retrieves only the pinned `model.safetensors`, streams it under the expected
size limit, and verifies its full SHA-256 before renaming the partial file. It accepts no
credential argument. Preserve any failed output and use a new directory for a retry;
`receipt.json` with `status: complete` identifies a successful retrieval. The header-only
`contract_audit` command remains a separate, smaller operation.

The checkpoint directory also needs a byte-identical copy of the verified model config.
For example, with the registered tokenizer assets available at `outputs/model-contract`:

```sh
python -c "from pathlib import Path; Path('outputs/full-checkpoint/config.json').open('xb').write(Path('outputs/model-contract/config.json').read_bytes())"
```

The exclusive write preserves an existing destination. Use the actual registered asset
location in place of the example path. Do not edit the copied config, add a model PAD ID,
resize embeddings, or substitute a base-model config. No credential is needed by the later
local-only inference processes, and credentials must not be included in a job package.

The pilot checks these runtime versions before loading a model:

| Component | Pilot requirement |
|---|---|
| PyTorch | 2.9.1, compiled for CUDA 12.6; the official wheel reports `2.9.1+cu126` |
| Transformers / tokenizers | 4.57.1 / 0.22.2 |
| bitsandbytes / accelerate | 0.48.2 / 1.11.0 |
| Device | One compatible CUDA GPU with compute capability at least 7.5 |

For a new compatible Linux environment, the installation order is:

```sh
python3 -m venv outputs/inference-env
outputs/inference-env/bin/python -m pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu126 torch==2.9.1
outputs/inference-env/bin/python -m pip install --only-binary=:all: --index-url https://pypi.org/simple -r requirements-inference.txt
outputs/inference-env/bin/python -m pip check
```

Use a new environment path and preserve existing audit/inference environments. Retain the
resolved package lock and installation provenance with an actual run. Dependency resolution
and CPU import checks do not establish CUDA or LLM.int8 execution; the actual device,
driver, module conversion and numerical checks still govern reuse. Do not bypass an
execution system's security controls to make a native import work. The reviewed
[environment preparation script](../scripts/prepare_inference_env.sbatch) provides the
Explorer-specific setup procedure; inspect its allocation and module assumptions before use.

## Preparing and running the development precision pilot

The bounded pilot uses the D-012 design: 128 eligible training examples, 64 per class,
with 48 short, eight medium and eight long inputs per class. The deliberate length-tail
coverage is diagnostic, not a representative or held-out quality sample. Preparation
reads verified text-free membership and the preserved native training-length audit:

```sh
python -m precision_benchmark.pilot_data --help
python -m precision_benchmark.pilot_inference --help
```

`pilot_data` requires population/native-audit directories and their registered summary
hashes, then writes a new `manifest.json` and `examples.jsonl`. Reuse the reviewed prepared
membership for a repeat instead of resampling it. The inference command accepts only the
hash-bound `eligible_training` pilot and rechecks its IDs, labels, class/length support,
source hashes and observed token lengths against authorized development inputs. Labels
remain separate and are never supplied to the model.

Every treatment uses the same raw strings, fast tokenizer, explicit cap 1024, right
truncation, no padding and batch size one. No chat template or manual EOS is added. The
model PAD setting stays unset, preserving the original final-token pooling behavior,
including genuine terminal EOS tokens. The runner checks actual synthetic EOS/head outputs
and the expected rejection of a padded batch of two; it does not claim padded equivalence.
Softmax runs on FP32-converted logits and selects injection index 1. The common threshold
0.5 is explicitly provisional; final threshold selection remains the later FP32-validation
procedure.

FP32 disables TF32 and automatic mixed precision. FP16 loads the same checkpoint in half
precision. INT8 uses bitsandbytes LLM.int8 with outlier threshold 6, the `score` head skipped,
FP16 residual parameters, and no CPU offload. All treatments use eager attention, frozen
parameters, evaluation/inference mode and disabled cache. Named parameter/buffer/module
records and executed synthetic-module dtype observations establish the effective treatment;
the precision label alone is insufficient.

Run all three treatments sequentially in fresh processes within the same reviewed GPU
allocation. The environment identity includes the allocation ID and GPU identity, so
separate unmatched devices or allocations cannot be combined implicitly. The reviewed
[pilot job](../scripts/run_precision_pilot.sbatch) takes six arguments: existing inference
environment, verified tokenizer assets, original source directory, partition directory,
full checkpoint file and expected pilot-manifest SHA-256. It expects a verified staged
project containing `stage-manifest.json` and `pilot/manifest.json`; it is not a generic
submission command for an unstaged checkout.

Alternatively, after setting the `PAI_*` variables to the verified input locations in the
approved allocation, this Bash job-script loop shows the underlying invocation. Choose a
new output root and a unique run tag for every attempt:

```sh
for precision in fp32 fp16 int8; do
  "$PAI_ENV/bin/python" -m precision_benchmark.pilot_inference \
    --pilot "$PAI_PILOT" --pilot-sha256 "$PAI_PILOT_SHA256" \
    --assets "$PAI_ASSETS" --checkpoint "$PAI_CHECKPOINT" \
    --access "$PAI_ACCESS" --access-sha256 "$PAI_ACCESS_SHA256" \
    --partitions "$PAI_PARTITIONS" --raw-dir "$PAI_RAW" \
    --precision "$precision" --run-id "$PAI_RUN_TAG-$precision" \
    --output "$PAI_OUTPUT/$precision" --device cuda:0 || exit 1
done
```

The model loads only from local files after the full checkpoint checksum and byte-identical
config check. Official-test inputs are not accepted. Keep the same input paths, manifest
hash, code and environment throughout the loop. A failed treatment stops dependent
comparison; preserve its outputs rather than dropping failed examples or continuing with
a different scientific configuration under the same run identity.

| Per-treatment artifact | Meaning |
|---|---|
| `execution.json` | Current stage, intended/completed coverage and sanitized failure information; an incomplete record is not a result. |
| `predictions.jsonl` | Stable ID, run ID, two logits, injection score and thresholded prediction; no reference label or raw prompt. |
| `run.json` | Completion marker written last, compatible evaluator metadata and artifact hashes. |
| `environment.json` | Actual software, device, allocation and precision flags. |
| `precision-evidence.json` | Loaded tensor/module/device/dtype evidence and synthetic execution observations. |
| `synthetic-checks.json` | Actual synthetic pooling/EOS and invalid-input boundary checks. |
| `feasibility.json` | Loading, synchronized forward samples and GPU memory observations, scoped to the bounded pilot. |

Require all three `run.json` records to be complete, with exactly the intended 128 IDs,
finite outputs and compatible metadata before analysis. The effective input-schedule
identity incorporates a hash of the actual ordered token IDs and masks; real token vectors
are not exported. Timing excludes tokenization, transfers and score conversion, uses three
warm-up inputs, and retains one sample per selected input. It is feasibility evidence,
not the later controlled profiling study or proof of deployment speedup.

After three complete runs, construct their hash-bound comparison and analysis without
manually editing JSON. `PAI_RUNS` is the directory containing the `fp32`, `fp16` and `int8`
subdirectories; use the same prepared pilot path and hash as inference:

```sh
python -m precision_benchmark.pilot_compare \
  --pilot "$PAI_PILOT" --pilot-sha256 "$PAI_PILOT_SHA256" \
  --runs "$PAI_RUNS" --output outputs/pilot-comparison-new
```

This offline command writes `comparison.json` with relative file references and actual
hashes, then delegates validation and metrics to the existing evaluator under `analysis/`.
It checks each run against the prepared pilot as well as requiring compatible runs and
complete predictions. `assembly.json` records completion or the failed stage. Preserve an
incomplete output directory and select a new one after correcting the underlying issue;
creating references does not independently attest native execution or scientific validity.

## Reanalysing the retained pilot bundle

The retained, reviewed team bundle is `docs/evidence/p1b-pilot-20261117/`, containing
`pilot/manifest.json`, `pilot/examples.jsonl`, per-treatment artifacts under
`runs/fp32`, `runs/fp16`, `runs/int8`, and a `comparison.json` that binds their hashes.
The prepared pilot manifest has SHA-256
`405f6ccac8c923abf33d951e2ac4e31c7d2bae6e87fc5441912b8e0cd3c906e4`;
its presence alone does not establish completed inference. Check the experiment and
validation records for the bundle's actual completion/review state.

Regenerate the complete verified bundle's analysis without model
weights, CUDA, credentials or inference dependencies:

```sh
python -m precision_benchmark --manifest docs/evidence/p1b-pilot-20261117/comparison.json --output outputs/pilot-reanalysis-new
```

The evaluator verifies its file references, full intended coverage and shared treatment
metadata before generating the five analysis files described above. Keep any pilot quality
values labeled as development diagnostics; these inputs and the provisional threshold do
not supply a Test-A result or the final threshold freeze.

### Regenerating the resource table

```sh
python -m precision_benchmark.resource_summary --manifest docs/evidence/p1b-pilot-20261117/comparison.json --output outputs/resource-new
```

Use the retained D-012 training bundle or a comparison manifest assembled for the same pilot.
Keep the prepared `manifest.json` beside `examples.jsonl`. The command verifies the approved
examples, full measurement coverage, matching token schedules, device, execution flags,
timing boundaries and warm-up policy. It reads the hardware and sample count from the
validated evidence. For chronological treatment order, consult the native execution records.

Outputs include `resource.csv`, `resource_by_length.csv`, `resource.md`, `resource_summary.json`
and an optional figure. Use `--no-figure` for a standard-library-only run. The report figure
used Matplotlib 3.11.2. The forward-only rate divides the example count by the sum of the
synchronized forward durations. End-to-end throughput requires a separate wall-clock measurement.

## Software checks

```sh
python -m unittest discover -s tests -v
```

Tests use synthetic inputs and mocked transport/native calls. One requests-specific test
skips if that optional dependency is absent. Passing the suite does not establish real model,
GPU or tokenizer execution; actual run evidence and its limits are in the validation log.
