# Benchmarking Precision Aware Inference for Prompt Injection Detection

**Course:** CS5130  
**Team:** Shreyas Shukla, Viraj Paradkar, Yash Chavan, and Hareeshwar Muthu Kumaran

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

The project is currently a planned study; this README makes no claim of measured results.
The evolving state and next task are recorded in [STATUS.md](docs/STATUS.md).

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
