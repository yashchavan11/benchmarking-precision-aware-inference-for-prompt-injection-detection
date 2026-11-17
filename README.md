# Benchmarking Precision Aware Inference for Prompt Injection Detection

**Course:** CS5130  
**Team:** Shreyas Shukla, Viraj Paradkar, Yash Chavan, and Hareeshwar Muthu Kumaran

## Overview

This project studies how numerical precision affects the quality and cost of a pretrained
prompt-injection detector. It has two sequential research parts:

1. Compare **FP32, FP16 and INT8** execution of the same frozen classifier on matched inputs.
2. Develop a **learned escalation gate** that decides when a lower-precision prediction
   warrants an additional higher-precision pass.

The central question is whether selective escalation can recover useful classification
quality while costing less than running higher precision on every input. Higher precision
is a comparison baseline, not ground truth: a rerun can correct an error, leave the outcome
unchanged, or introduce an error. Reference labels determine correctness.

## Model, data and precision treatments

| Component | Study choice |
|---|---|
| Classifier | [`rogue-security/prompt-injection-jailbreak-sentinel-v2`](https://huggingface.co/rogue-security/prompt-injection-jailbreak-sentinel-v2), a Qwen3-0.6B-based sequence classifier. Its classification weights remain frozen throughout both studies. |
| Dataset | [`hendzh/PromptShield`](https://huggingface.co/datasets/hendzh/PromptShield), with benign/injection labels and official training, validation and test splits. |
| FP32 | Execute an FP32 representation derived from the released checkpoint. Upcasting cannot recover precision lost before release. |
| FP16 | Execute the same checkpoint in half precision, recording operations that retain another precision. |
| INT8 | Apply bitsandbytes **LLM.int8()** to that checkpoint. This is a mixed-precision treatment; it does not make every operation integer arithmetic. |
| Learning | Train the escalation gate while keeping the detector frozen; no detector or base-model fine-tuning. |

Exact revisions, label mappings, source hashes and access conditions are recorded in the
[data registry](docs/DATA_REGISTRY.md). Model and dataset references are collected in
[SOURCES](docs/SOURCES.md). Publisher-reported performance is background information,
not a reproduced result of this project.

## Part 1: controlled precision benchmark

The benchmark examines four aspects of the precision tradeoff:

- **Classification quality:** accuracy, macro-F1, class-specific precision and recall,
  false-positive/false-negative rates, and ranking quality.
- **Prediction stability:** disagreements, corrected and introduced errors, and score
  changes relative to a shared classification threshold.
- **Confidence and input effects:** calibration, input length, truncation and proximity
  to the decision boundary.
- **Resources:** latency, throughput, loading, model storage and peak memory under
  matched workloads and execution conditions.

Comparisons use stable example identities, the same checkpoint and tokenizer, common
preprocessing and a shared threshold selected from FP32 validation predictions. Paired
analysis and uncertainty estimates account for comparisons on the same examples. Nominal
bit width alone does not establish a speedup, memory saving or accuracy loss.

The [research protocol](docs/RESEARCH_PROTOCOL.md) defines the controls, metrics,
uncertainty procedures and measurement boundaries.

## Part 2: learned selective escalation

The escalation design first runs the lower-precision detector and computes permitted signals, such as
its score, logit margin or input-length information. A trained gate then either returns
that prediction or requests a higher-precision pass and returns the resulting prediction.
Gate inputs must be available before the higher-precision pass; reference labels and
higher-precision outputs can form training targets but cannot become deployed gate inputs.

The study includes benefit characterization, gate fitting, diagnostic iterations and
baseline comparisons. Baselines include always-low, always-high, confidence routing and
random routing at comparable coverage or cost. An oracle is used only as a nondeployable
headroom reference. The learned gate is evaluated as an implemented system, including its
feature and routing overhead, both applicable model passes, loading/transfers and combined
memory requirements.

| Claim | Required comparison |
|---|---|
| Better classification quality | Learned routing versus lower precision alone on the same inputs. |
| Lower inference cost | The complete cascade versus higher precision alone. |
| Quality close to higher precision | Routed quality versus always-high under a predeclared tolerance and assessment. |
| Useful learned selection | Learned routing versus simple routing policies at fair coverage or cost. |
| Memory advantage | Measured combined peak memory under the stated residency/loading scenario. |

These are separate empirical questions. A smaller low-precision model does not establish
that a two-model cascade uses less memory, and an estimated cost curve does not establish
a measured runtime saving. The [extension specification](docs/EXTENSION.md) defines the
learning targets, candidate features, investigation strategy and claim criteria.

## Evaluation design

Part 1 is completed before substantive learned-gate development. Training and validation
data support development and selection. PromptShield's official test split is divided
50/50 by whole exact-text groups into two project-defined populations:

- **Test-A:** the locked precision benchmark and its subsequent error analysis.
- **Test-B:** final evaluation of the frozen learned gate and its baselines.

After Part 1, Test-A is seen evidence and cannot supply fresh confirmation or gate-fitting
data for Part 2. All final policies are compared on the same Test-B examples. Duplicate
isolation, exclusions, exposure limits and release conditions follow the research protocol;
exact memberships and provenance are in the data registry. Results are reported as
evaluations of these subsets, not of the entire official test split.

## Scope and research deliverables

The study retains the selected classifier and dataset, three precision treatments, frozen
detector, sequential benchmark and substantive learned-gate investigation. Additional
detectors, datasets, quantization families, base-model fine-tuning or leaderboard comparisons
are outside the initial scope.

The research deliverables are:

- A controlled benchmark with complete prediction coverage, paired quality analysis,
  uncertainty, calibration/error analysis and measured resources.
- A trained and investigated gate with appropriate baselines, a frozen selection procedure,
  held-out evaluation and measured full-system costs.
- Reproducible code, manifests and analyses linking claims to evidence, including failures,
  unfavorable results and limitations.
- A report, presentation, references and accurate contribution statement, as specified in
  [REPORTING](docs/REPORTING.md).

Detailed methods and experimental settings are maintained in the protocol and
[roadmap](docs/ROADMAP.md). Documented findings are collected in [RESULTS](docs/RESULTS.md).

## Quickstart

The runnable package provides asset audits, data/input validation, tokenizer diagnostics
and offline analysis of saved predictions. The example below runs the **offline evaluator**;
it does not execute the detector or estimate Sentinel's performance.

Use Python 3.10 or newer. From the repository root:

```sh
python -m unittest discover -s tests -v
python -m precision_benchmark --manifest tests/fixtures/synthetic/comparison.json --output outputs/synthetic-demo
```

Use `python3` if that is your Python command. The evaluator requires only the standard
library; an optional transport test skips when `requests` is unavailable. The demo uses
eight invented examples and writes `report.md`, `quality.csv`, `paired.csv`,
`error_analysis.csv` and `results.json`. Choose a new output directory for each invocation.

See [USAGE](docs/USAGE.md) for dependencies, authentication, audit commands and input
requirements, and [ARCHITECTURE](docs/ARCHITECTURE.md) for the saved-prediction interface.
Model execution and resource profiling are separate from the offline evaluator.

## Repository guide

| Location | Purpose |
|---|---|
| `precision_benchmark/` | Audit, data preparation and evaluation modules. |
| `tests/` | Synthetic fixtures and correctness checks. |
| `scripts/` | Reviewed batch-job and artifact-verification helpers. |
| `docs/` | Methods, architecture, usage, provenance and research records. |

Contributor procedures and pointers to project-tracking records are in [AGENTS.md](AGENTS.md).
