# Correctness and validity evidence

This log records the evidence supporting implementation correctness and research validity.
No checks are recorded yet. Planned checks and their expected outputs do not count as
performed validation.

Required properties come from the [research protocol](RESEARCH_PROTOCOL.md), the
[learned-gate checks](EXTENSION.md), the [artifact contracts](ARCHITECTURE.md), and each
[roadmap phase](ROADMAP.md). This log stores what was actually checked and what the evidence
establishes; it does not maintain a second copy of those requirements.

## Validation index

| Validation ID | Phase / target version | Property checked | Method / conditions | Outcome | Evidence / affected records | Reviewer |
|---|---|---|---|---|---|---|

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
