# Precision comparison: PRELIMINARY DEVELOPMENT

These are development observations, not held-out benchmark results.

Population: pilot-128:sha256:29c3acc60ec3ab635668ba80b1607e77c31ad1d20e3ae04068f13b044d9d4bfe; role: eligible_training.
Shared threshold: 0.5; positive when score >= threshold.
Threshold source: provisional-p1b-fixed-0.5-not-validation-selected.

## Detection quality

All rates are fractions in [0, 1]. Injection is the positive class.

| precision | n | accuracy | macro_f1 | injection_precision | injection_recall | fpr | fnr | roc_auc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fp32 | 128 | 0.757812 | 0.744708 | 0.971429 | 0.531250 | 0.015625 | 0.468750 | 0.932373 |
| fp16 | 128 | 0.757812 | 0.744708 | 0.971429 | 0.531250 | 0.015625 | 0.468750 | 0.932129 |
| int8 | 128 | 0.765625 | 0.753846 | 0.972222 | 0.546875 | 0.015625 | 0.453125 | 0.926025 |

Full class support, confusion counts, class-specific metrics and calibration summaries are in quality.csv and results.json.

## Paired changes versus FP32

Corrected means FP32 was wrong and the candidate is right; introduced means the reverse.
Accuracy delta is candidate minus FP32 in percentage points. FP32 is not ground truth.

| precision | both_correct | introduced_errors | corrected_errors | both_wrong | disagreement_rate | accuracy_delta_pp |
| --- | --- | --- | --- | --- | --- | --- |
| fp16 | 97 | 0 | 0 | 31 | 0.000000 | 0.000000 |
| int8 | 97 | 0 | 1 | 30 | 0.007812 | 0.781250 |

error_analysis.csv contains every example wrong in either member of each pair, including shared errors.
It includes score shifts, threshold distances and token lengths when supplied; it contains no prompt text.

## Resource measurements

Not available. Offline score analysis does not measure latency, throughput, memory or model size.
Integrate the profiler's matched measurements after its timing and memory boundaries are reviewed.

## Provenance

| precision | run_id | code_revision | environment_id |
| --- | --- | --- | --- |
| fp32 | p1b-20261117-fp32-11959388 | sha256:cf30977d3e3698c73f133088195c14235a839c193d0eae93865cf72b6538c8de | sha256:a89ef2e9bdc5c92487a885febaadfdf7a2f902bdf514ce360d3d2d3efa1dbd6c |
| fp16 | p1b-20261117-fp16-11959388 | sha256:cf30977d3e3698c73f133088195c14235a839c193d0eae93865cf72b6538c8de | sha256:a89ef2e9bdc5c92487a885febaadfdf7a2f902bdf514ce360d3d2d3efa1dbd6c |
| int8 | p1b-20261117-int8-11959388 | sha256:cf30977d3e3698c73f133088195c14235a839c193d0eae93865cf72b6538c8de | sha256:a89ef2e9bdc5c92487a885febaadfdf7a2f902bdf514ce360d3d2d3efa1dbd6c |

results.json records complete run metadata and SHA-256 hashes of inputs and analysis source.

## Limitations

- Descriptive development analysis; no confidence intervals or significance claims.
- Runtime and memory are unmeasured by this offline evaluator.
- Metadata consistency does not independently verify assets, labels, eligibility, or effective precision.
- Undefined metrics are null (JSON), empty (CSV), or N/A (Markdown).
