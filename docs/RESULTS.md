# Findings and claim register

No measured findings are recorded yet. This register stores conclusions and their evidence;
[REPORTING.md](REPORTING.md) defines how they become tables, figures and final deliverables.
Statistical and measurement definitions belong to [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md),
and the gate's separate quality/cost claims belong to [EXTENSION.md](EXTENSION.md).

## Result index

| Result ID | Part / phase | Question or claim | Evidence type / population | Supporting runs / validation | Status / reviewer |
|---|---|---|---|---|---|

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
