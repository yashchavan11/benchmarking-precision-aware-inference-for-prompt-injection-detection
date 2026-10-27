# Research outputs and course deliverables

This document defines the evidence packages, presentation artifacts and submission requirements.
The project title, team and scope are defined in the [README](../README.md). Scientific
procedures are in [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md); the criteria for learned-gate
claims are in [EXTENSION.md](EXTENSION.md). Reported findings come from
[RESULTS.md](RESULTS.md), with links to their actual runs and validation.

## Part 1 evidence package

The benchmark must be understandable as a complete study before the learned-gate work is
presented. The following artifacts supply its evidence; related items can share a figure
or table when that improves readability.

| Artifact | Content needed by a reader | Primary evidence source |
|---|---|---|
| Asset and population table | Pinned model/tokenizer/data identities; official and effective split sizes; eligibility, exclusions and duplicate handling; the Test-A/Test-B allocation | DATA_REGISTRY and audit validation |
| Input coverage summary | Original/effective lengths, truncation policy and support, retained versus excluded cases | Membership/input manifests and checked analysis |
| Quality table | Selected primary endpoint and complementary classification/ranking metrics, common threshold, class support and valid denominators | Complete matched Test-A prediction runs |
| Paired stability analysis | Corrected, introduced and shared errors; prediction disagreements and score shifts, including threshold/length context | Paired analysis linked to the same runs |
| Uncertainty summary | Effect estimates, declared interval method, sampling unit, confidence level, resampling budget/seed, valid replicates and dependence limits | Analysis artifacts and protocol freeze |
| Calibration figure/table | Brier score, reliability bins/counts and the declared ECE definition; binning sensitivity when investigated | Calibration analysis with raw-score provenance |
| Resource table/figures | Matched workload/backend, measurement scopes, latency distribution, throughput, loading, storage and memory | Actual profiling runs and raw measurements |
| Error analysis | Bounded examples or categories from permitted data; observed patterns distinguished from explanations | Linked results and exposure-eligible example references |

Captions identify Test-A as a **designated subset of PromptShield's official test split**
and give its actual support. Source-overlap uncertainty remains visible in the study's
limitations; the data audit cannot establish what the pretrained classifier previously saw.

## Part 2 evidence package

The research account includes the learned method and its development, not only a final
performance number. Both development and confirmatory artifacts are useful, provided their
roles are labeled.

| Artifact | Content needed by a reader | Primary evidence source |
|---|---|---|
| Headroom analysis | All four low/high correctness combinations, recoverable/harmful prevalence and nondeployable oracle reference | Eligible development paired predictions |
| Method description | Benefit target, permitted features, fitting/selection design, gate family, objective and feature-acquisition cost | Frozen policy artifacts and methodological decisions |
| Iteration/ablation account | Tested hypotheses, meaningful refinements, simple controls, failures and why the final candidate was selected | Experiment/result records, including unsuccessful attempts |
| Quality–coverage–cost figure | Development frontier and declared final operating point; any estimated cost clearly distinguished from measured execution | Development baseline/gate runs and selection decision |
| Confirmatory policy table | Always-low, always-high, confidence/random routing and learned routing on the same Test-B population; quality changes versus both fixed models with uncertainty | Frozen P2-E comparison runs |
| Routing behavior table | Route rate, helpful/harmful reruns, missed recoverable errors and shared errors | Checked selection traces and paired correctness analysis |
| System resource table | Complete measured cost versus each fixed baseline, median/p95 latency, throughput, initialization/loading assumptions and combined peak memory | Integrated-system profiles under the declared deployment scenario |
| Claims and limitations statement | Which predeclared criteria are supported, which remain uncertain, resource regressions and the scope of each conclusion | Reviewed RESULTS entries and EXTENSION claim criteria |

The comparison caption identifies **Test-B**, the final freeze, its sample/class support,
and the selected policy. A development frontier is labeled separately from confirmatory
results. Any policy chosen after seeing Test-B outcomes is labeled exploratory and cannot
replace the originally frozen result in the main comparison.

A negative or uncertain finding still belongs in the research account. Explain the
hypotheses investigated, what the evidence rules out, the remaining limitations and
justified next research directions. The actual learned-gate investigation remains part of
the deliverable regardless of the sign of the final effect.

## Figure, table and claim traceability

Each reported artifact has an identifiable source record containing:

- Result and run IDs, eligible input membership and the analysis/code version.
- Named comparison reference, policy/operating point and evaluation role.
- Units, metric direction, denominators, uncertainty and effective support.
- Workload/device, batch or concurrency, sequence-length and loading context where relevant.
- Artifact location/hash and the check showing regeneration from retained evidence.

Tables and figures are regenerated from stored outputs rather than manually entered
numbers. Caption terminology follows the metric and cost definitions in RESEARCH_PROTOCOL
and EXTENSION. In particular, the displayed evidence must make measured system results,
offline replay and illustrative calculations distinguishable. Extended evidence stays in
the repository when page or slide limits require a shorter presentation.

## Course submission requirements

| Deliverable | Required contents or constraint |
|---|---|
| Proposal | At most one page, following the course proposal requirements. |
| Final repository | Public and owned by a team member; README with purpose, organization and usage; implemented Python package with initialization, functional modules and tests. |
| Final report | At most two pages; exact project title and full author list, actual public repository URL, purpose, data and achieved results, implemented architecture/method, actual contribution statement and references. |
| Presentation | 5–10 slides covering the problem, precision comparison, architecture/method, findings, learned gate, measured quality/cost tradeoffs and limitations. |

The final report can use a compact sequence: research question and method, core benchmark
results, learned-gate formulation and principal tradeoff, limitations, contributions and
references. Separate evaluation populations must remain clear even within the page limit.
The report and slides describe achieved work; planned experiments are identified as plans.

The contribution statement is derived from [CONTRIBUTIONS.md](CONTRIBUTIONS.md), supported
by actual work and review evidence rather than inferred from membership or commit totals.
References come from [SOURCES.md](SOURCES.md). Applicable course requirements for citations
and disclosure of tools or assistance govern the final submission; no additional policy
is assumed here.

## Final delivery evidence

Phase F closes when its [phase record](PHASE_RECORDS.md) links the final repository,
report, slides and evidence snapshot, with checks establishing:

- Reproducible reported analysis and meaningful validation of implemented functions.
- Accurate usage documentation and accessible supporting artifact references.
- Agreement between reviewed findings and all report, slide and repository claims.
- Complete authorship/contribution, citation and course-format requirements.

The [roadmap](ROADMAP.md) owns the phase sequence; this section defines the submission
artifacts and verification evidence for that final phase.
