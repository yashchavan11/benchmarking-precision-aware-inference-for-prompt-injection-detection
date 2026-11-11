# Correctness and validity evidence

This log records the evidence supporting implementation correctness and research validity.
Development evaluator checks are recorded below. Planned checks and their expected outputs
do not count as performed validation.

Required properties come from the [research protocol](RESEARCH_PROTOCOL.md), the
[learned-gate checks](EXTENSION.md), the [artifact contracts](ARCHITECTURE.md), and each
[roadmap phase](ROADMAP.md). This log stores what was actually checked and what the evidence
establishes; it does not maintain a second copy of those requirements.

## Validation index

| Validation ID | Phase / target version | Property checked | Method / conditions | Outcome | Evidence / affected records | Reviewer |
|---|---|---|---|---|---|---|
| V-001 | P1-B/P1-C component preparation; source hashes in generated results.json | Metrics, pairing, artifact integrity and report generation | Python 3.13.3; synthetic fixtures; standard-library unittest | Passed: 18 tests | tests/; outputs/synthetic-demo/ (regenerable, ignored); S-20261111-01 | Second-contributor review pending |

### V-001 — Development evaluator verification

- **Performed by/date:** Codex, at Shreyas's request; 2026-11-11, America/New_York.
- **Target:** `precision_benchmark/`, interface v1 (D-007); exact source hashes are retained in the generated `results.json`.
- **Executed:** `python3 -m unittest discover -s tests -v` — 18 tests passed on Python 3.13.3. `python3 -m precision_benchmark --manifest tests/fixtures/synthetic/comparison.json --output outputs/synthetic-demo` — exit 0; five output files generated. `git diff --check` — passed.
- **Independent arithmetic:** Six-example hand-calculated confusion matrix TN=2, FP=1, FN=1, TP=2 gives accuracy/macro-F1/AUC=2/3, FPR/FNR=1/3. Rank-based AUC agrees exactly with a pairwise reference over all 81 score assignments from {0, 0.5, 1} to two positives/two negatives. Floating-point hand calculations use unittest's default seven-decimal-place tolerance.
- **Edge checks:** Threshold equality; tied scores; endpoints/empty calibration bins; undefined metrics; single-class labels; empty/mismatched vectors; invalid labels and nonfinite/out-of-range/oversized scores. All four paired correctness outcomes are checked, including positive accuracy delta when the candidate corrects an FP32 error.
- **Integrity checks:** Missing/duplicate IDs, wrong reference labels/run IDs, incomplete runs, mismatched configuration and hashes, duplicate JSON keys, partial/inconsistent length metadata and held-out roles are rejected. Test-B rejection occurs before opening the examples file.
- **Integration checks:** Reordered prediction rows join correctly; two CLI runs yield byte-identical outputs under the same environment and invocation paths; report values match fixtures; existing output directories are preserved; CSV formula-like identifiers are escaped. The generated Markdown was inspected for labels, metric direction and unavailable-resource disclosure.
- **Evidence:** `tests/test_evaluation.py`, `tests/test_artifacts.py`, `tests/test_report.py`, `tests/fixtures/synthetic/`; README contains regeneration commands. Source and input SHA-256 values are emitted with each report.
- **Limits:** No real dataset or checkpoint, GPU execution, threshold selection, confidence intervals, or profiling was checked. Python versions other than 3.13.3 were not executed. Consistent metadata is not independent verification of the declarations. This is software evidence, not a completed P1-A/B/C phase or empirical finding.
- **Review:** A second contributor still needs to review scientific formulas, conventions, eligibility and real-run evidence under AGENTS.md. No human review is claimed.

IDs have the form `V-[unique number]`. Outcomes are `passed`, `failed` or `inconclusive`.
A pass applies to the stated property and conditions, not automatically to other data,
backends, scales or measurement claims.

## Validation record template

### V-[number] — [check]

- **Performed by / date / phase:** [actual values]
- **Target and version:** [data manifest, metric implementation, model path, gate, run or report]
- **Property and source requirement:** [precise expected behavior and protocol/roadmap reference]
- **Method:** [independent reference, known-answer fixture, invariance check, audit,
  integration comparison or repeatability test]
- **Inputs and permitted split:** [fixture or audited input identity, exposure state and relevant grouping]
- **Conditions:** [implementation/backend, configuration and scale actually exercised]
- **Expected outcome and tolerance:** [chosen before comparing outputs, with rationale]
- **Observed outcome:** [actual values and passed / failed / inconclusive status]
- **Evidence location and integrity:** [artifact/hash or exact reproducible procedure]
- **What this establishes:** [scope of the evidence]
- **What it does not establish:** [unverified backend/scale, statistical assumption or missing system cost]
- **Affected runs/results:** [IDs, invalidation implications or none]
- **Failure/inconclusive diagnosis:** [smallest reproduction, confirmed cause versus hypothesis,
  correction attempted and unresolved concern; not applicable if passed]
- **Revalidation relationship:** [earlier failed check, corrected target version and new check ID]
- **Follow-up and owner:** [fix, investigation, repeat, review or complete]
- **Review evidence:** [actual reviewer and assessment, or pending]

A corrected implementation receives new validation evidence; the earlier failed record
remains available so its effect on dependent results can be traced.
