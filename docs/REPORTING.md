# Research outputs and course deliverables

## Progress update — November 17, later verified milestone

The earlier update below is historical. D-008 now selects the 50/50 whole-group design.
SPLIT-001–004 retain all 18,909 training and 1,000 validation rows and construct two
11,758-row test subsets, each with 8,515 benign/3,243 injection examples. Independent
administrative checks cover every source ID, all 71 duplicate groups, ordered membership,
provenance and zero cross-population exact-group intersections. Human scientific review
and performance releases remain pending. A review found and repaired an unapproved-revision
reuse path without changing any actual membership (V-018–V-021).

Authenticated retrieval now verifies all seven pinned tokenizer/configuration files and the
actual classifier tensor header: F16 score.weight [2,1024], no bias, configured injection
index 1. No tensor payload or model inference was needed. Source review identified
different serialized/wrapper PAD settings and EOS-sensitive pooling that must be controlled
before the pilot. Native tokenization is currently blocked by Windows Application Control
at regex import (V-017), despite successful Hub access. No token lengths, model quality,
precision effects or resource benefits are yet measured.

The reproducible metadata/header and partition commands are integrated, with 56 passing
combined tests and independent automated review (V-022/V-023). This is substantial audited
preparation, not P1-A completion. Yash authorized committing/pushing properly completed
milestones; final publication status is recorded in STATUS/SESSION_LOG. The November 18
progress-report format remains unspecified; nothing has been submitted.

## Progress update — November 17, 2026

The November 11/16 text below is historical. The current evidence includes authorized local
integration of both reviewed commits, fixes for Windows fixture integrity and calibration
bin boundaries, and a combined suite of **26 passing tests** (V-005). S-20261117-03 packages
the work in commit `1259a61`; Yash subsequently authorized its push to the existing private
GitHub repository. This does not establish final public-repository delivery or phase completion.

**Substantive data preparation.** A reproducible administrative audit now covers every row
of the pinned PromptShield revision: 18,909 training, 1,000 validation and 23,516 test rows
(43,425 total). It validates actual schema/label encoding, stable IDs, source and text hashes,
class counts, exact duplicates/conflicts, cross-split overlap and character/byte lengths.
There are no exact cross-split overlaps or conflicting-label groups. Official test contains
71 duplicate groups that must remain intact during the later A/B allocation. See ASSET-001,
RES-001 and V-008 for counts, evidence and limitations. This administrative inspection is
not model-performance evaluation; character lengths are not token lengths.

**Verification.** Independent checks compared all 43,425 identities and aggregates with
direct-string calculations and exercised 4,096 synthetic exclusion-precedence cases. Review
also found and fixed a source-cache reuse weakness; altered cached files now fail against
retained provenance. The original failures and corrected evidence are preserved. Human/team
scientific signoff remains pending; do not attribute automated execution to a teammate.

**Inference readiness and remaining work.** The pinned Sentinel v2 config was retrieved
through the approved browser and preserved with a hash (V-012). It declares output 0 as
benign and output 1 as jailbreak, with single-label classification. Actual tensor head
shape, tokenizer and pooling behavior remain unverified; the config omits `pad_token_id`.
Local credentials remain absent. Browser automation stopped during tokenizer retrieval
because the tool could not confidently determine the current URL; no completed tokenizer
file was found. Earlier unauthenticated 401 responses remain preserved. Optional secure
local-authentication support now passes the combined 35-test suite after independent review
found and corrected a redirect-error disclosure path (V-013/V-014), using mocked
transport; real authenticated CLI retrieval has not been tested. Local
inventory detects an RTX 5070 Ti Laptop GPU with 12,227 MiB VRAM and driver 577.13; no
PyTorch/Transformers/bitsandbytes runtime was installed or validated in the checked interpreter.
Hardware presence alone does not establish backend compatibility or a measured benefit.

**Remaining work.** Complete authorized tokenizer retrieval and prior team test-exposure review; finish
the model/tokenizer and token-length audit; review and freeze group-preserving evaluation
partitions and development eligibility. Then run the small matched three-precision pilot
under the roadmap. No real detection quality, speedup, memory saving, final threshold,
Test-A/Test-B allocation, learned gate, or completed P1-A phase is claimed. The progress-report
format is still pending from Yash.

## Progress report working text — November 18 checkpoint

The following reflects implementation completed on November 11 and rechecked on November 16,
2026, not a claim that the later checkpoint or any model experiment has occurred. Replace pending sections with
verified team outputs before submission; the progress-report rubric has not been supplied.

**Evaluation and integration progress.** We have implemented an offline Python evaluation
package for saved FP32, FP16 and INT8 predictions. It validates complete example coverage,
artifact hashes, shared configurations, score ranges and thresholded labels before calculating
classification metrics. The output includes accuracy, macro-F1, class-specific precision and
recall, false-positive/false-negative rates, ROC-AUC, confusion counts and calibration summaries.
Paired comparisons identify errors introduced, corrected or shared relative to FP32, with
reference labels determining correctness. A single command generates reproducible CSV tables,
an ID-level error-analysis export and a readable report with provenance.

**Methods.** The evaluator consumes saved predictions for the same expected examples under
FP32, FP16 and INT8. Each example has a stable ID and a reference label, with 0 representing
benign text and 1 representing injection. We join runs by ID and require matching model,
tokenizer, dataset, preprocessing, input schedule, environment, code revision and threshold
metadata. A score at or above the shared threshold produces an injection prediction.
Detection quality is calculated against reference labels; FP32 serves as a comparison
baseline, not ground truth. We compare outcomes per example to distinguish corrected errors
from introduced errors, and retain score shifts and threshold distances for follow-up analysis.
The current implementation is descriptive; it does not run models or measure hardware costs.

**Validation completed.** Automated checks use hand-authored synthetic examples and an
independent pairwise AUC reference. They exercise metric edge cases, threshold ties,
all four paired correctness outcomes, integrity/coverage failures and CLI reproducibility.
All 18 tests passed again on November 16, and the CLI regenerated all five report artifacts;
see V-001 and V-002 for the executed checks. Synthetic values demonstrate software behavior and do
not estimate Sentinel v2 performance.

**Pending experimental evidence.** Actual dataset counts and eligible partitions, verified
model/tokenizer revisions, precision-treatment checks, real pilot predictions and measured
runtime/memory outputs remain pending. Accordingly, no detection-quality improvement,
speedup or memory reduction is claimed. The evaluator currently rejects held-out data roles;
Test-A/Test-B remain subject to the project audit and freeze process.

**Limitations.** The eight-example fixture is hand-authored and provides no evidence about
Sentinel v2's real accuracy, quantization behavior or generalization. Artifact consistency
checks cannot independently establish correct labels, duplicate isolation, asset provenance
or actual precision execution. The illustrative threshold of 0.5 has not been selected on
FP32 validation outputs. Confidence intervals, final threshold selection and integrated
resource analysis remain unfinished. Human scientific review is pending. These limitations
prevent claims about accuracy retention, statistical significance, speedup or memory savings.

**Next integration step.** The data owner supplies the audited expected-label manifest;
the inference owner supplies complete predictions and run metadata using ARCHITECTURE's
v1 interface. Shreyas's workstream then regenerates the same tables on eligible development
data and reviews the resulting errors. The profiling owner supplies separately reviewed,
matched resource measurements. A second contributor reviews scientific validity before
the report presents real findings. Full benchmark and learned-gate experiments remain later
milestones, as defined in ROADMAP.

**Contribution disclosure.** This evaluation implementation and its tests/documentation
were produced by Codex at Shreyas's request; human review and experimental execution remain
pending. Use actual subsequent work for the final individual contribution statement and
follow the course's assistance-disclosure policy.

The demonstration can be regenerated using README's command. Never paste its invented
numbers into the report's empirical-results section. An honest current evidence table is:

| Item | Current evidence |
|---|---|
| Evaluation pipeline | Implemented; synthetic validation recorded in V-001. |
| Real detection quality and prediction changes | Not measured. |
| Latency, throughput and memory | Not measured. |
| Dataset audit and model precision verification | Pending upstream work and review. |
| Main-protocol freeze and learned gate | Pending later roadmap phases. |

## Demo walkthrough and speaking notes

On November 16 the demo was run with:

```sh
python3 -m precision_benchmark --manifest tests/fixtures/synthetic/comparison.json --output outputs/synthetic-demo-20261116
```

Open `outputs/synthetic-demo-20261116/report.md`. Generated outputs are ignored by Git;
teammates can regenerate them from the tracked fixture. Use a fresh output directory if
that name already exists. Every number below is synthetic, not a model-performance result.

| Treatment label | Correct / total | TP / TN / FP / FN | Accuracy | Injection precision / recall | Macro-F1 |
|---|---|---|---|---|---|
| FP32 fixture | 4 / 8 | 2 / 2 / 2 / 2 | 50% | 50% / 50% | 0.50 |
| FP16 fixture | 4 / 8 | 2 / 2 / 2 / 2 | 50% | 50% / 50% | 0.50 |
| INT8 fixture | 6 / 8 | 3 / 3 / 1 / 1 | 75% | 75% / 75% | 0.75 |

TP means correctly flagged injection; TN means correctly accepted benign input. FP is a
benign input wrongly flagged; FN is an injection missed by the detector.

| Metric | How to explain it |
|---|---|
| Accuracy | Fraction of all examples classified correctly: `(TP + TN) / N`. It can conceal class imbalance or changes in which examples are wrong. |
| Injection precision | Of the examples flagged as injection, how many really are injections: `TP / (TP + FP)`. |
| Injection recall | Of all actual injections, how many are caught: `TP / (TP + FN)`. |
| FPR / FNR | False alarms among benign inputs / missed attacks among injections. Their denominators differ. |
| Macro-F1 | Compute F1 for each class and average them equally. Each F1 balances precision and recall; this is not the F1 of averaged precision/recall. |
| ROC-AUC | How well scores rank injections above benign examples across thresholds. Ties get half credit; it does not measure accuracy at the chosen threshold. |
| Brier score | Mean squared difference between injection scores and 0/1 reference labels; lower is better. |
| ECE | Count-weighted gap between mean score and observed injection frequency in ten score bins. Lower is better under this binning, but tiny samples are unreliable. |

Undefined metrics are N/A, not zero or perfect performance. The machine-readable rates
are fractions; 0.50 means 50%. An accuracy change from 50% to 75% is **25 percentage points**.

The important paired example is FP16 versus FP32: two examples stay correct, two errors are
corrected, two new errors appear, and two stay wrong. Accuracy remains 50%, but four of
eight decisions change. In `error_analysis.csv`, `synthetic-1` is benign: its score changes
from 0.6 to 0.4 across the 0.5 threshold, correcting a false alarm. `synthetic-2` is also
benign, but its score changes from 0.2 to 0.6, introducing a false alarm.

The INT8 fixture corrects four FP32 errors and introduces two. Its net gain is
`(4 - 2) / 8 = 0.25`, or 25 percentage points. These values were deliberately authored to
exercise the evaluator; they do not imply that INT8 will outperform FP32 on real data.

**Suggested 45-second explanation:** "Our evaluation component takes saved predictions
from three precision modes and compares them against the same labels. It checks that the
runs are compatible and complete before calculating metrics. We report both overall quality
and which individual errors change. For example, our synthetic FP32 and FP16 fixtures have
the same accuracy, although half their decisions differ. That demonstrates why we need
paired error analysis. The software passes 18 tests and produces reproducible reports.
Actual model predictions and hardware measurements are still needed before we can draw
conclusions about precision tradeoffs."

## Reporting requirements

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
