# Benchmarking Precision Aware Inference for Prompt Injection Detection

**Course:** CS5130  
**Team:** Shreyas Shukla, Viraj Paradkar, Yash Chavan, and Hareeshwar Muthu Kumaran

## Current milestone

**November 17, 2026: P1-A is complete.** Pinned assets, native tokenizer/config behavior,
all 43,425 source-row lengths and the approved group-preserving development/Test-A/Test-B
manifests are verified. See [the closeout](docs/PHASE_RECORDS.md#p1-a-closeout---asset-data-and-evaluation-design-audit)
and [STATUS](docs/STATUS.md) for exact evidence and continuation. The final CPU job passed
85 tests. Classifier weights have not been fully downloaded/loaded, and no model-quality,
precision or GPU-resource experiment has run. P1-B is the next phase.

## Project overview

This project investigates the relationship between numerical precision, classification
quality, and inference cost in a pretrained prompt-injection detector. It has two
sequential research parts. The first establishes a controlled comparison of FP32, FP16,
and INT8 inference using the same frozen classifier. The second develops a learned gate
that decides whether a prediction made at lower precision warrants an additional
higher-precision pass.

The precision benchmark is a complete empirical study in its own right. The learned-gate
investigation is also a committed part of the project, with model fitting, diagnostic
iterations, baseline comparisons, and evaluation of an actual inference system. Its aim
is to recover useful higher-precision quality while reducing the cost of running higher
precision on every input. The extent to which those objectives can be achieved is an
empirical research question.

## Problem and motivation

A prompt-injection detector classifies text as benign or an injection attempt. A false
negative misses an attack; a false positive flags benign text. Changes in either kind of
error matter, even when overall accuracy changes little. The classifier's scores also
matter: numerical differences can change a thresholded decision or the usefulness of a
confidence estimate without changing every predicted label.

Lower-precision inference can reduce the resources used to represent or process model
weights, but nominal precision alone does not establish a practical speedup, a lower
peak-memory requirement, or a loss of accuracy. Backend behavior, retained floating-point
operations, input lengths, batching, and loading conditions affect the observed tradeoff.
This project measures those effects under comparable conditions.

The research extension asks a more specific question than whether a prediction is
uncertain: **can information from the low-precision run predict when a high-precision
rerun will improve the outcome enough to justify its additional cost?** Higher precision
can correct an error, preserve the same outcome, or introduce an error. Reference labels,
not precision level, determine correctness.

## Selected model, dataset, and precision treatments

| Element | Project choice and interpretation |
|---|---|
| Classifier | [`rogue-security/prompt-injection-jailbreak-sentinel-v2`](https://huggingface.co/rogue-security/prompt-injection-jailbreak-sentinel-v2), a Qwen3-0.6B-based sequence classifier. Its pretrained classification weights remain frozen throughout the precision comparison and gate study. |
| Dataset | [`hendzh/PromptShield`](https://huggingface.co/datasets/hendzh/PromptShield), containing benign and prompt-injection text with reference labels and official train, validation, and test splits. |
| FP32 treatment | Execute an FP32 version derived from the released checkpoint. Casting released weights to FP32 does not recover precision lost before their release. |
| FP16 treatment | Execute the same checkpoint using the declared FP16 configuration. |
| INT8 treatment | Use the selected bitsandbytes LLM.int8() approach. It includes mixed-precision behavior; the study will inspect effective module and computation precision rather than assume every operation is integer arithmetic. |
| Adaptation | Train the escalation gate while keeping the underlying detector frozen. No additional detector or base-model fine-tuning is part of the initial scope. |

The asset audit will establish exact model, tokenizer, and dataset revisions; actual
schema and class counts; positive-label mapping; preprocessing; duplicate relationships;
and access and usage conditions. Publisher-reported performance is background information,
not a reproduced project result. The source register distinguishes verified source
statements from checkpoint-specific facts that still require investigation.

## Part 1: controlled precision evaluation

The first study addresses four groups of questions:

1. **Classification quality:** how do precision variants differ in accuracy, macro-F1,
   class-specific precision and recall, false-positive and false-negative rates, and
   ranking quality?
2. **Prediction changes:** which reference-labeled examples are corrected or newly
   misclassified, which errors remain shared, and how do scores and decision disagreements
   relate to the classification threshold?
3. **Confidence and input effects:** how does calibration change, and what relationships
   appear with input length, truncation, and proximity to the decision boundary?
4. **Resource use:** what differences occur in latency, throughput, initialization/loading,
   stored model footprint, and peak memory under matched workloads and execution conditions?

The output will include audited assets and evaluation populations, reproducible prediction
records, paired comparisons, uncertainty estimates, resource measurements, and an error
analysis. Differences will be interpreted in the context of the actual precision treatments
and workload. The full controls, definitions, and statistical procedures are specified in
[RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md).

## Part 2: learned selective precision escalation

The initial inference design performs a low-precision forward pass, derives permissible
features, and evaluates a learned gate. The system either returns the low-precision
prediction or runs the higher-precision variant and returns that prediction. This is a
classification system; generated chains of thought are not part of the initial design.
Intermediate-layer stopping may be investigated later as a justified refinement.

The development study will quantify recoverable errors and harmful reruns, define the
gate's learning target, train candidate policies, and examine their quality-versus-cost
operating points. Permissible gate features must be available before the higher-precision
pass. The comparison includes always-low and always-high inference, transparent confidence
routing, matched random routing, and an explicitly nondeployable oracle for headroom analysis.
A confidence heuristic alone does not complete the learned-gate investigation.

Both precision variants must be accessible in the chosen execution scenario. Keeping both
resident can increase memory use; loading one on demand can introduce additional latency.
The actual cascade also pays for the initial low-precision pass on every request, including
requests that are escalated. Consequently, the following claims have different baselines:

| Research claim | Required comparison |
|---|---|
| Improved classification quality | Learned routing versus low precision alone. |
| Reduced inference cost | Complete cascade execution versus high precision alone. |
| Quality close to higher precision | Routed quality versus always-high, using a tolerance and assessment specified before final evaluation. |
| Useful learned selection | Learned routing versus simple routing policies under fair coverage or cost conditions. |
| Memory advantage | Measured combined peak memory under the declared residency/loading scenario. |

A result in one row does not establish the others. In particular, a smaller low-precision
model does not prove that a two-model system uses less memory, and an estimated cost curve
does not establish a measured runtime saving. The extension requires implemented routing,
full cost accounting, and reasoned investigation of weak or unexpected results. Its precise
targets, candidate features and gate families, correctness checks, numerical illustrations,
and claim criteria are defined in [EXTENSION.md](docs/EXTENSION.md).

## Sequential study and independent evaluation

The order is **complete Part 1, then investigate Part 2, then integrate the findings**.
This preserves the benchmark as a standalone contribution and allows the extension to
reuse verified preprocessing, inference functions, analysis components, and eligible
prediction records.

The working evaluation design reserves two project-defined subsets of PromptShield's
official test split before any test-model performance is inspected: Test-A for the precision
benchmark and sealed Test-B for final evaluation of the learned gate and its baselines.
The allocation remains a choice to resolve from the data audit. These subsets will be
reported as such, rather than as evaluations of the entire official test split.

Training and validation data support development and selection. After Part 1, Test-A is
seen evidence and cannot provide fresh confirmation for Part 2. The frozen routing policy
and all fixed-model comparisons are evaluated on the same Test-B examples. Duplicate
isolation, eligibility exclusions, permitted administrative inspection, accidental exposure,
and conditions for a defensible confirmation are defined in the research protocol.

## Scope, choices, and completion criteria

The selected classifier, dataset, three precision treatments, frozen detector, sequential
research structure, and substantive learned-gate investigation define the agreed scope.
New detectors, additional datasets, base-model fine-tuning, leaderboard comparisons, or
extra quantization families require an explicit scope decision. Meaningful additional
correctness checks and diagnostics within the research questions are welcome.

Several methodological and implementation details remain open: exact asset revisions,
sequence lengths and batches, the primary endpoint, threshold selection, uncertainty
settings, holdout allocation, gate features and family, operating objective, residency
scenario, environment, and job execution. The [roadmap](docs/ROADMAP.md) provides candidate
choices and the phase in which each must be resolved. These candidates are neither measured
optima nor fixed user requirements; the selected settings need a rationale and a recorded
freeze before their relevant confirmatory evaluation.

Completion requires:

- A controlled Part 1 comparison with verified treatments, matched inputs and conditions,
  complete coverage, paired error analysis, uncertainty, and measured resources.
- A trained gate with meaningful development iterations, appropriate baselines, a frozen
  selection procedure, held-out quality evaluation, and complete system-cost measurement.
- Traceable claims that distinguish measured outcomes, estimates, hypotheses, and limitations;
  failed experiments and unfavorable effects remain part of the evidence.
- A reproducible, understandable implementation with appropriate checks of the functions
  and analysis actually used, and reusable outputs whose validity conditions are recorded.
- Project records sufficient for a new contributor to recover the goals, decisions,
  completed phases, evidence, and next task without the original conversation.
- The repository, report, presentation, references, and actual contribution statement
  described in [REPORTING.md](docs/REPORTING.md).

Windows, macOS, remote development, and the university cluster are valid working
environments. CUDA-dependent experiments can run on suitable cluster resources. Backend
compatibility is an implementation decision; scientific comparisons require matched
conditions within each reported comparison, regardless of where development occurs.

## Project documentation and research records

The development evaluator is implemented and checked against synthetic fixtures. A pinned
PromptShield administrative audit, authenticated model/header audit and native tokenizer
audits complete P1-A. Their source/label/population evidence and reuse limits are in
[DATA_REGISTRY.md](docs/DATA_REGISTRY.md). Model inference and empirical precision experiments
remain pending. This README makes no claim of measured model-performance results.
The evolving state and next task are recorded in [STATUS.md](docs/STATUS.md).

### Run the development evaluator

Python 3.10+ is required; the evaluator uses only the standard library. From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -m precision_benchmark --manifest tests/fixtures/synthetic/comparison.json --output outputs/synthetic-demo
```

The output directory must be new; existing reports are never overwritten. The demo uses
eight invented examples, not Sentinel or PromptShield predictions. It writes `report.md`,
`quality.csv`, `paired.csv`, `error_analysis.csv`, and `results.json`. The last file preserves
input/source hashes, run metadata, calibration bins and optional truncation subgroups.

For real development runs, use the exact JSON/JSONL interface in
[ARCHITECTURE.md](docs/ARCHITECTURE.md#implemented-development-evaluation-interface-v1).
Replace the demo manifest path with your audited comparison manifest. No model downloads,
GPU, inference packages or network access are needed to regenerate analyses. Test-A/Test-B
analysis is intentionally disabled until the later protocol freeze and uncertainty work;
see [D-007](docs/DECISIONS.md#d-007--development-evaluator-interface-and-metric-conventions).

### Reproduce the administrative asset audits

These standard-library commands inspect metadata and aggregate dataset properties; they
do not run a model or choose Test-A/Test-B. Use a new output directory for each run. On
Windows, use `python` if `python3` is unavailable.

```sh
python -m precision_benchmark.model_audit --revision 05ff9bfd1f28c5228e53121d5ee4427bb5205212 --output outputs/model-audit-repeat
python -m precision_benchmark.data_audit --revision a5234cb1f5cdb256600cab64b8c961195b5e8404 --raw-dir data/raw/promptshield/a5234cb1f5cdb256600cab64b8c961195b5e8404 --download --output outputs/data-audit-repeat
```

The model command is unauthenticated by default. To use an existing locally configured
Hub credential, add `--auth local`; it is read from the standard environment/cache and is
never printed or copied into audit artifacts. `--auth prompt` instead accepts hidden input
in a real local terminal without saving it. Never put a token in a command argument or chat.
Use a fresh output directory. These modes have synthetic software checks and independent regression repair (V-013/V-014); these original small-file authentication modes have only synthetic checks. The full
authenticated contract retrieval is now V-022 via the integrated `contract_audit` helper.
All selected tokenizer files are retained; actual tokenization/model runtime remains unverified.

The model command records HTTP outcomes; a successful audit command does not mean gated
configuration files were accessible. Check `summary.json` before using any retained file.
The dataset command downloads about 31 MB on first use and checks retained source hashes
on reuse. Do not display raw official-test prompts or treat projected development identities
as a frozen eligibility decision. Preserve `data/raw/` and `outputs/` locally; compact audit
evidence is retained in `docs/evidence/`. No model weights or inference dependencies are
installed by either command. See V-005–V-009 in [VALIDATION_LOG](docs/VALIDATION_LOG.md).

| Document or record | Contents |
|---|---|
| [ROADMAP.md](docs/ROADMAP.md) | Detailed phases, dependencies, candidate settings, planned outputs, and completion conditions. |
| [RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md) | Shared scientific procedures for precision, data boundaries, quality analysis, uncertainty, and measurement. |
| [EXTENSION.md](docs/EXTENSION.md) | Learned escalation formulation, development strategy, routing comparisons, and cost/quality verification. |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Planned components, data flow, and interfaces connecting the two studies. |
| [SOURCES.md](docs/SOURCES.md) | Model, dataset, and method references; unresolved source-specific facts; prior-art register. |
| [REPORTING.md](docs/REPORTING.md) | Research presentation, evidence products, and course submission requirements. |
| [DECISIONS.md](docs/DECISIONS.md) and [OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | Chosen methods with rationale, and unresolved questions affecting the work. |
| [DATA_REGISTRY.md](docs/DATA_REGISTRY.md) and [EXPERIMENT_REGISTER.md](docs/EXPERIMENT_REGISTER.md) | Asset and population identities, exposure history, planned/executed runs, and artifact references. |
| [VALIDATION_LOG.md](docs/VALIDATION_LOG.md) and [RESULTS.md](docs/RESULTS.md) | Correctness evidence and supported findings with their limitations. |
| [SESSION_LOG.md](docs/SESSION_LOG.md) and [PHASE_RECORDS.md](docs/PHASE_RECORDS.md) | Chronological research history and phase closeouts, including reusable outputs. |
| [CONTRIBUTIONS.md](docs/CONTRIBUTIONS.md) | Actual team contributions and reviews for the final contribution statement. |

### Reproduce approved population construction and the model contract audit

D-008 now selects a 50/50 whole-group design. The constructed populations are review-ready;
human scientific review and performance-release conditions remain pending. Reuse the
verified local audit inputs, or regenerate them from the earlier pinned data-audit command.

```sh
python -m precision_benchmark.partition_data --revision a5234cb1f5cdb256600cab64b8c961195b5e8404 --identities outputs/asset-audit-20261117/dataset/audit-v3/row-identities.jsonl --identities-sha256 f1a9450854c2e618da2a72ff1c6dc0f12c816cfe3d1b1afcc5cfc3b1283a2be6 --provenance outputs/asset-audit-20261117/dataset/audit-v3/provenance.json --provenance-sha256 029122b812b22e76b620111f71541e85661a91f8f629982bc3e59fb17ef15af9 --receipt data/raw/promptshield/a5234cb1f5cdb256600cab64b8c961195b5e8404/source-integrity.json --receipt-sha256 6e571116cb02f85d477d45f4ed296231a76570103bc6acea0aa72e16232dd12a --output outputs/partitions-repeat
```

The full pinned tokenizer/configuration and header-only audit is available separately:

```sh
python -m precision_benchmark.contract_audit --output outputs/contract-audit-repeat
```

Use an approved Python environment with `huggingface-hub` and `requests` from
`requirements-audit.txt`, and an existing securely configured Hub credential. No token
argument is accepted. This downloads about 16 MB of tokenizer/configuration plus a bounded
header, never the full weights. Retained results establish source/head metadata, not model
execution. The tokenizer dependencies are verified on Explorer; Windows still blocks `regex` locally
(Q-015). The dependency-free evaluator and partition builder remain usable. One optional
requests-specific mock test skips when requests is absent. The final combined suite passed
85 tests locally and on the final Explorer job. DATA_REGISTRY and PHASE_RECORDS link the
completed P1-A scope; no empirical model-precision result is claimed.

### Check development inputs before tokenization

The standard-library input loader now verifies original text/label/ID alignment for the
approved development populations. D-009 permits independent continuation without teammate
attestations. The CLI exports no prompt text and rejects protected roles before reading
files. Use a new output directory:

```sh
python -m precision_benchmark.input_data --role eligible_training --access docs/evidence/p1a-development-access-20261117.json --access-sha256 83dde0502e9aca5cfd000c5f6ec9631602db9f03a334a2f1a42d9ac3adc3e79b --partitions outputs/contract-20261117/partitions-v2 --raw-dir data/raw/promptshield/a5234cb1f5cdb256600cab64b8c961195b5e8404 --output outputs/training-input-preflight-repeat
```

For validation, select `eligible_validation` and a different fresh output directory.
Actual preflights verified 18,909 training and 1,000 validation rows; 66 combined tests
passed (V-026). This prepares input handling without executing tokenization or a model.
The Windows native-library policy block remains Q-015; no teammate reply is needed for
independent work. Shared choices and overlapping work should be communicated per D-009.

### Native tokenizer audit commands

`precision_benchmark.tokenizer_audit` validates both D-009 development roles with explicit
untruncated/unpadded local-only wrapper calls and the three candidate cap diagnostics.
`precision_benchmark.holdout_lengths` is a separate administrative command with a fixed
source/role and total-only outputs; it is not a test-inference entry point. Use their
`--help` and the reviewed Slurm scripts for exact arguments. Scripts require an approved
runtime, new output/run directories and preserved asset/input hashes. The original
development guard still rejects protected roles before reading files.

The recorded commands use exact retained audit receipts/parent artifacts. Reacquisition
provenance can differ in timestamps/paths; do not silently replace expected hashes. Reuse
the registered compatible artifacts or explicitly verify/document equivalent source bytes
and reconstructed populations. Raw data, vocabularies, weights, environments and large
row outputs remain excluded from Git; coordinate access/regeneration using the registry.
