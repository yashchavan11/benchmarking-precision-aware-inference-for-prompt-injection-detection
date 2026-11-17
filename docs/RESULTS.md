# Findings and claim register

Administrative dataset findings are recorded below; no model-performance or resource
findings are established. This register stores conclusions and their evidence;
[REPORTING.md](REPORTING.md) defines how they become tables, figures and final deliverables.
Statistical and measurement definitions belong to [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md),
and the gate's separate quality/cost claims belong to [EXTENSION.md](EXTENSION.md).

## Result index

| Result ID | Part / phase | Question or claim | Evidence type / population | Supporting runs / validation | Status / reviewer |
|---|---|---|---|---|---|
| RES-001 | Part 1 / P1-A | Pinned source supports an exact-duplicate-aware evaluation design | Development observation: administrative source audit, no classifier | R-P1-A-20261117-01; V-006/V-008; ASSET-001 | Observed and independently checked by automated review; human signoff pending |
| RES-002 | Part 1 / P1-A | Padding/pooling policies require explicit checks | Static source and synthetic index cases | R-P1-A-20261117-04; V-016/V-022 | Source-level observation; human/runtime review pending |

### RES-001 — Source audit establishes exact-group constraints, not model performance

- **Date/scope:** 2026-11-17; all official rows of ASSET-001. Authoritative counts, labels, group support, lengths and hashes are in DATA_REGISTRY ASSET-001 and its linked machine evidence.
- **Observation:** No exact-text group crosses official splits and no exact-text conflicting-label group was found. Duplicate groups occur within official test; they must remain intact in any later A/B allocation. Applying the protocol's exact-overlap exclusions removes no training/validation rows.
- **Interpretation:** The audited exact-group structure permits planning a group-isolated allocation using the recorded class support. This is not proof of sufficient power for an unspecified endpoint, absence of near-duplicates, source annotation truth, or absence of pretrained-model contamination.
- **Boundary:** A/B proportions, algorithm, seed, final membership, exposure controls, model labels/tokenization and experimental freezes are not selected here. No accuracy, precision effect, latency or memory claim follows from an administrative dataset audit.
- **Review/reuse:** V-008 independently checks the observed counts/identities and source-cache integrity. Reuse requires the recorded pinned bytes and role restrictions; prior external test exposure remains Q-013. Suitable for the progress report's data/method preparation section, with unfinished work explicit.

IDs have the form `RES-[unique number]`. Evidence types distinguish `development observation`,
`pilot finding`, `Part 1 Test-A result`, `Part 2 Test-B result`, `measured system profile`,
`simulation` and `illustrative calculation`. An illustration is not an empirical observation;
a development result is not a confirmatory test result.

Claim status is one of `hypothesis`, `observed`, `reviewed`, `provisional`, `invalidated`
or `superseded`. Status describes the current support for a particular claim; it does not
change the underlying run history.

## Result record template

### RES-[number] — [specific finding]

- **Recorded by / date / phase:** [actual values]
- **Question and scope:** [project goal and precise dimension addressed]
- **Claim status:** [status from the definitions above]
- **Evidence type:** [type and development/confirmatory role]
- **Population and conditions:** [partition/membership ID, sample/class/group support,
  treatment configuration and timing/memory scope]
- **Supporting artifacts:** [run IDs, validation IDs, analysis version and table/figure references/hashes]
- **Observed quantities:** [values, units, denominators and uncertainty; empty fields remain unmeasured]
- **Comparison and baseline:** [named reference, policy/operating point, controlled conditions
  and intentionally varied factor]
- **Claim criterion:** [predeclared decision/protocol reference and whether the evidence meets it;
  descriptive findings remain reportable without a stronger supported-improvement claim]
- **Interpretation:** [supported conclusion, competing explanations and remaining hypotheses]
- **Correctness and validity evidence:** [relevant label, preprocessing, numerical, measurement
  and selection checks, including any unresolved concern]
- **Limitations:** [sampling, dependence, exposure, calibration, backend and measurement constraints]
- **Reuse boundary:** [which later uses remain valid and what requires fresh measurement]
- **Next investigation:** [bounded follow-up or linked open question]
- **Report destination:** [section, figure or none yet]
- **Review / supersession:** [actual reviewer or pending; replacement ID and reason when applicable]

## Multi-part finding links

A synthesis can link several result records without repeating their measurements. For Part 1,
link the completed evidence package specified in REPORTING. For Part 2, keep separate
records or explicitly separated components for quality versus each fixed-model baseline,
full measured cost versus each baseline, learned selection versus simple routing, and
memory/loading feasibility. Their common policy and evaluation population must be identifiable.
This permits a useful tradeoff to be described without treating success in one dimension as
proof of success in the others.

## Invalidation record

When a result becomes provisional, invalidated or superseded, retain its original claim and add:

- **Trigger and evidence:** [label, metric, split, configuration or measurement defect; V/decision ID]
- **Affected scope:** [which quantities, populations, interpretations and downstream records change]
- **Publication impact:** [report text, headline, figure, slide or repository summary requiring correction]
- **Replacement or recovery:** [new result/run IDs or the unresolved action and owner]

An obsolete headline is part of the affected evidence chain; correcting a technical note
alone does not update the claim presented to readers.

### RES-002 — Source audit identifies padding and pooling choices that require explicit checks

- **Evidence/status:** P1-A development observation from retained source/configuration and synthetic index arithmetic, not a model-performance result. V-016/V-022, ASSET-002 and R-P1-A-20261117-04. Independent automated review complete within source scope; human review pending.
- **Observation:** The model leaves PAD unset; inspected batch-one source selects the last position. Setting PAD=EOS changes stock pooling to last token unequal to EOS. The retained tokenizer backend and wrapper configuration also disagree on PAD ID. Wrapper code adjusts backend settings per call, so a direct backend invocation cannot silently be assumed equivalent.
- **Implication:** Apply one explicitly verified input/pooling policy to all precision treatments. Use unpadded batch one as the initial proposed reference; a later batching adapter or PAD policy requires a rationale and numerical equivalence checks. No policy is selected by this finding.
- **Limits:** No logits, token lengths, precision effects or resource outcomes were measured. V-024's aggregate literal/NFC probe does not remove the need for truncation and synthetic EOS cases. Do not claim a measured detector error or accuracy change from these source observations.
