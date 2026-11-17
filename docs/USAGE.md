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

## Software checks

```sh
python -m unittest discover -s tests -v
```

Tests use synthetic inputs and mocked transport/native calls. One requests-specific test
skips if that optional dependency is absent. Passing the suite does not establish real model,
GPU or tokenizer execution; actual run evidence and its limits are in the validation log.
