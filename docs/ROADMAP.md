# Project roadmap

This is the single execution plan for **Part 1: precision benchmarking → Part 2: learned
precision escalation → final delivery**. Both research parts are committed work. The
phase identifiers below are used by the project records; they do not imply that any phase
has already been completed.

[README.md](../README.md) defines the project, scope and acceptance criteria. The
[research protocol](RESEARCH_PROTOCOL.md) owns shared scientific controls, and
[EXTENSION.md](EXTENSION.md) owns the learned-gate method. This roadmap assigns that work
to phases, identifies its dependencies, and lists the evidence needed to advance.
[STATUS.md](STATUS.md) identifies current work; [PHASE_RECORDS.md](PHASE_RECORDS.md)
retains reviewed closeouts and the knowledge passed between phases. Session and team
procedures are in [AGENTS.md](../AGENTS.md).

Numerical options below are **candidate settings**, not measured optima, course requirements,
or fixed user choices. Select and justify settings using permitted development evidence;
record them in [DECISIONS.md](DECISIONS.md) before the relevant evaluation freeze.
Additional checks, ablations or diagnostic experiments are appropriate when they resolve a
specific uncertainty. A completion gate means that its evidence is established; it does
not require a new user-permission request for every routine action.

## Part 1 — Precision benchmark

### P1-A — Asset, data and evaluation design audit

**Goal:** establish the exact research inputs and protect both later evaluations.

**Dependencies:** approved scope, [SOURCES.md](SOURCES.md), the research protocol and the
initial questions in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). No test-model performance is
needed for this audit.

**Work:**

1. Resolve model, tokenizer and dataset revisions, access conditions, actual schema and
   classification-head label meanings. Identify preprocessing requirements and provenance
   limitations rather than assuming the source cards fully describe the pinned artifacts.
2. Audit official split sizes, class support, exact duplicate/conflicting-label groups,
   available grouping information and text lengths. Create stable example identities and
   hashes. Apply the protocol's eligibility and duplicate-isolation rules through manifests
   while preserving the original source snapshots.
3. Establish Test-A and sealed Test-B before test-performance inspection. Candidate
   allocations are 50/50 or 60/40, selected after aggregate support and group audits. Record
   the deterministic grouping/stratification rule, membership, exclusions and rationale.
   Describe both populations as project-defined subsets of the official test split.
4. Establish permitted administrative access, Test-B exposure controls and the exposure
   record. Resolve inadequate Test-B support before P1-D rather than after gate development.
5. Specify the artifact contracts in [ARCHITECTURE.md](ARCHITECTURE.md) sufficiently to
   detect missing IDs, invalid labels, duplicate prediction records and incompatible runs.

**Outputs:** populated [DATA_REGISTRY.md](DATA_REGISTRY.md), source and split audit evidence,
eligibility/A/B manifests, class/group counts, access and exposure decisions, and a concrete
component-development task list.

**Completion gate:** inputs can be located by stable identity; label semantics, development
eligibility and held-out boundaries are unambiguous; both evaluation populations have
sufficient documented support. No final model-performance result influenced the partition.
A verified access blocker is recorded precisely, while independent audit/design work can
continue under the session procedure.

### P1-B — Reusable components and a small real pilot

**Goal:** verify a comparable end-to-end precision experiment before substantial execution.

**Dependencies:** P1-A's data contract, pinned source revisions and eligible training
examples. Test-A and Test-B performance remain uninspected.

**Work:**

1. Build the minimum data-preparation, inference, scoring and recording components for the
   same frozen checkpoint in FP32, FP16 and LLM.int8(). Select the environment/backend from
   actual compatibility. Verify score transformation, label orientation, effective dtypes,
   quantized modules, retained classifier-head policy and device placement.
2. Check tokenization, padding and pooling with single-item and padded-batch cases; check
   finite outputs, stable ID alignment, matched batch composition and explicit failures.
   Include known-answer scoring/metric checks as the relevant components are introduced.
3. Run a deterministic training-data pilot in all three treatments. Candidate sizes are
   128 or 256 examples, with class and length coverage documented. Enlarge the pilot when
   an identified failure mode needs additional coverage.
4. Investigate a small common configuration: candidate length caps are 512, 1,024 or 2,048
   tokens, initially at batch size 1, followed by a common larger batch if useful and
   feasible. Estimate truncation and resource effects using development evidence.
5. Repeat the bounded pilot where needed to investigate unexplained numerical changes or
   timing variability. Repeated executions of a fixed model are not independently trained
   models. Record backend constraints and unresolved treatment differences.

**Outputs:** implemented reusable components, pilot predictions and manifests, verified
precision-treatment descriptions, initial feasibility/length/resource observations, failed
attempts and evidence in [VALIDATION_LOG.md](VALIDATION_LOG.md).

**Completion gate:** all intended treatments execute the same semantic task with comparable
inputs and documented effective precision; relevant correctness checks pass; the pilot is
reproducible. Pilot observations establish feasibility, not final accuracy or speed claims.

### P1-C — Analysis implementation and main-protocol freeze

**Goal:** establish the analysis and fix choices before the primary Test-A comparison.

**Dependencies:** P1-A/B evidence and eligible validation data.

**Work:**

1. Implement and independently check saved-result analysis: ID joins, metric formulas,
   calibration summaries, paired uncertainty, configuration compatibility and resource
   measurement. A small development run must produce auditable known-correct outputs.
2. Select the primary quality endpoint and complementary metrics, classification-threshold
   search/tie rule, uncertainty design, common input-length/batch policy, and profiling
   matrix. Use the protocol for definitions and record the reasons for the selected choices.
3. Select the shared classification threshold using FP32 validation predictions only;
   retain the candidate comparison and chosen threshold artifact.
4. Verify timing scopes, accelerator synchronization, warm-up, loading separation, partial
   batches, memory definitions and comparable input schedules. Choose resource repetitions
   and budgets using pilot evidence and the intended statistical interpretation.
5. Define the required tables, figures, manifests and reproducible analysis outputs. Resolve
   outstanding issues that could change the primary comparison, including how configuration
   changes would invalidate earlier runs or require repetition.
6. Record the Part 1 freeze: exact assets, data/configuration identities, threshold, chosen
   analysis and profiling settings, execution/dependency information, resource budget and
   Test-A membership. Reconfirm sealed Test-B status.

**Outputs:** validated evaluation/profile methods, selected threshold, analysis plan, required
output definitions and a traceable main-protocol freeze.

**Completion gate:** every choice affecting the primary Test-A comparison is fixed before
P1-D. The supporting development run can regenerate correct analyses from retained inputs.

### P1-D — Main benchmark and analysis

**Goal:** establish the controlled empirical precision comparison.

**Dependencies:** the P1-C freeze and its registered input/configuration identities.

| Work item | Population | Treatments and purpose |
|---|---|---|
| Final quality comparison | Frozen Test-A | All three precisions on matched examples: quality, decision stability, score/calibration and truncation effects. |
| Dedicated resource profiling | Fixed representative validation subset | All three precisions with common length/batch schedules: repeated latency, throughput, memory and loading measurements. |
| Reproducibility confirmation | Declared development samples or repeated fixed measurements | Unchanged settings: verify execution and aggregation without selecting new settings from Test-A outcomes. |

A starting profiling budget may use 128–256 validation examples, 5–10 warm-up batches per
relevant shape and 10 measured passes. These are options to settle in P1-C. Sample support
must suit the stated median/p95 interpretation. Retain raw measurements and document any
justified expansion consistently across treatments; do not multiply the full quality
matrix by every possible configuration without a concrete research need.

Validate complete intended-ID coverage, labels, effective precision, matched conditions,
output integrity and run compatibility. Analyze quality differences, introduced/corrected
errors, score movement, calibration, paired uncertainty and length/truncation effects under
the frozen protocol. Preserve failed attempts and limitations alongside completed runs.

**Outputs:** registered complete predictions/profiles, checked analyses, paired effect
estimates, main tables/figures, raw repeated measurements and linked interpretation.

**Completion gate:** each reported comparison regenerates from traceable evidence for the
intended population. Test-A is recorded as seen; Test-B remains sealed. Reporting identifies
Test-A as a subset of PromptShield's official test split.

### P1-E — Part 1 closeout and knowledge transfer

**Goal:** preserve a complete, independently interpretable result and the foundation for Part 2.

**Dependencies:** P1-D's validated runs and analyses.

Create the Part 1 evidence snapshot and closeout with:

- Findings about changed predictions, introduced/corrected errors, and quality/resource
  tradeoffs with uncertainty and exact measurement scopes.
- Limitations concerning truncation, calibration, treatment compatibility, duplicate
  dependence and unknown pretrained-model contamination; unresolved bugs and failed approaches.
- Reusable functions/interfaces, checked preprocessing and metrics, compatible development
  predictions, profiling records, and the assumptions required for each reuse.
- Exact asset/data/configuration references, data-exposure state and remaining questions.

[RESULTS.md](RESULTS.md) retains the findings; [PHASE_RECORDS.md](PHASE_RECORDS.md) links the
closeout and reusable inventory; [STATUS.md](STATUS.md) identifies the next P2-A task.
Preserve the locked Part 1 results. Seen Test-A may motivate explicitly exploratory
hypotheses under the protocol, but it is not the gate-fitting or validation-selection
population and cannot supply fresh Part 2 confirmation.

**Completion gate:** a fresh contributor can reproduce and interpret Part 1, identify what
Part 2 can reuse or must revalidate, and start P2-A from the records. Unrelated polish must
not delay the committed extension.

## Part 2 — Learned precision escalation

### P2-A — Benefit characterization and research objective

**Goal:** establish the available benefit, the information a gate can use and its objective.

**Dependencies:** the P1-E closeout, eligible paired training/validation predictions and
[EXTENSION.md](EXTENSION.md). Test-B remains protected throughout development.

Apply the extension's headroom analysis: count recoverable errors, harmful reruns, neutral
outcomes and shared errors; inspect the target distribution; quantify nondeployable oracle
headroom and break-even routing rates using measured costs. Investigate where benefit is
concentrated, including uncertainty, threshold proximity, length/truncation and other
permissible features. Distinguish uncertainty from evidence that a rerun can improve a decision.

Choose the low/high pair from development evidence. Define benefit targets, candidate
features and their acquisition costs, operating objectives and the validation-selection
design. Complete the bounded prior-art investigation in [SOURCES.md](SOURCES.md) before
making novelty claims. Record initial hypotheses and a reasoned research iteration plan.

**Outputs:** headroom/target tables, prior-art findings, initial cost model, feature/objective
choices and the declared development plan.

**Completion gate:** benefit semantics, available information, baseline policies, cost
assumptions and selection data are explicit. Small headroom leads to diagnosis and bounded
alternative hypotheses, not automatic cancellation of Part 2.

### P2-B — Transparent routing baselines

**Goal:** establish what simple selection achieves and how learned selection will be compared.

**Dependencies:** P2-A's objective, low/high pair, feature boundary and selection design.

Develop confidence/threshold-distance routing and random routing at matched coverage.
Compare them with always-low and always-high on the same development examples and request
conditions. Retain quality/coverage/cost curves and select a small set of meaningful operating
criteria using validation only, following the fairness rules in the extension.

Check routing decision boundaries, equality cases, returned-model predictions, route-rate
accounting and helpful/harmful outcomes. Verify that labels and high-precision outputs cannot
enter deployed gate inputs. Establish the complete costs of the fixed-model references.

**Outputs:** reproducible baseline policies, development frontiers, routing correctness
evidence and validation operating criteria.

**Completion gate:** the reference comparison is transparent and uses the correct populations
and cost scopes. A confidence rule is a baseline for the learned gate, not completion of Part 2.

### P2-C — Learned gate and diagnostic iterations

**Goal:** learn useful net escalation benefit and investigate why the policy succeeds or fails.

**Dependencies:** P2-A/B evidence and the extension's target, feature and fitting contracts.

Fit a small interpretable gate on eligible training paired predictions. Regularized
multinomial logistic regression is a starting candidate; a modest nonlinear alternative or
cost-aware target requires a development-evidence rationale. Fit transformations on training
only, handle rare/absent target classes, and select regularization, features and escalation
cutoffs through the declared validation or training-only cross-validation procedure.

Compare learned candidates to P2-B at matched coverage or measured-cost conditions. Use the
extension's diagnostic loop to investigate label correctness, effective precision differences,
sparse recoverable errors, imbalance, calibration, feature usefulness, validation overuse
and routing overhead. Include useful feature ablations or controlled comparisons. Each
iteration has a hypothesis, observation and consequent decision recorded with its evidence.

**Outputs:** fitted versions, training/selection provenance, leakage checks, ablations,
diagnostic outcomes and a reproducible candidate choice with limitations.

**Completion gate:** a learned gate has actually been trained and seriously investigated
without Test-B-driven selection. Closing an unproductive direction requires evidence from
the hypotheses investigated; neither one weak attempt nor endless unchanged retries is a
substitute for the research. The candidate is not yet the final frozen policy.

### P2-D — Integrated system, full-cost measurement and policy freeze

**Goal:** verify the actual escalation system and freeze its final policy before confirmation.

**Dependencies:** the selected P2-C candidate, baseline implementations and comparable
low/high treatments.

Implement low pass → feature extraction/gate → selected high pass using the architecture
contracts. Verify replay-to-execution agreement for returned decisions/scores and route
membership. Measure against always-low and always-high with matched development request
streams using the extension's full-cost accounting, including acquisition overhead, both
applicable model passes, transfers/loading, batch/concurrency effects and combined memory.

Investigate the resident-model scenario; measure loading if claiming on-demand feasibility.
A resident-only result is acceptable with a stated scope and combined memory cost. Diagnose
slowdowns and bottlenecks, refine/revalidate candidates where evidence warrants, and select
the operating point using development measurements. Offline replay or estimated cost terms
cannot substantiate a measured deployment-speed claim.

**Outputs:** validated cascade execution, raw resource profiles, measured development
quality/cost curves, deployment assumptions, selected artifacts and the Part 2 freeze.

**Completion gate:** before leaving this phase, record the selected low/high precision pair,
fitted gate parameters, feature transforms, classification/escalation thresholds,
operating-point selection, baseline policies, hardware conditions, measurement design and
analysis plan as the final policy freeze. Test-B remains sealed. All acquisition and
inference overhead relevant to a claimed cost has been included.

### P2-E — Confirmatory evaluation and tradeoff interpretation

**Goal:** evaluate the frozen policy on the reserved population.

**Dependencies:** a complete P2-D freeze and verified unopened Test-B. A missing or changed
freeze returns work to P2-D before B outcomes are inspected.

Evaluate always-low, always-high, confidence routing, matched random routing and the learned
gate on the same Test-B examples under the frozen conditions. Use paired quality uncertainty
and appropriate repeated resource measurements. An oracle on B is a retrospective,
nondeployable reference only; its output cannot justify a revised policy as confirmatory on B.

Apply the extension's claim criteria to distinguish quality gains over low precision, quality
differences from high precision, savings versus high precision, overhead versus low precision,
and memory/resource effects. Include routing coverage, helpful/harmful reruns, uncertainty
and regressions. Preserve the original frozen result if a post-B hypothesis is explored;
subsequent confirmation requires a justified untouched design, not renamed results.

**Outputs:** registered confirmatory evidence, scoped conclusions, tables/figures and
limitations, with Part 1 evidence preserved separately.

**Completion gate:** a fresh contributor can reproduce the declared result and distinguish
development choices, confirmatory findings and post-hoc interpretation. Every claim meets
its relevant baseline, population, uncertainty and full-cost requirements.

## F — Reproducibility and final delivery

**Goal:** make both research parts understandable, reproducible and ready for course submission.

**Dependencies:** both parts' closeouts and their supporting scientific and validation evidence.

Integrate the findings while keeping Test-A and Test-B populations explicit. A quality
difference between A and B is not an algorithmic gain; policy comparisons use matched
examples within their designated evaluation. Reproduce reported values and figures from
retained records, verify implemented-code checks, and complete repository documentation,
references and the actual contribution statement.

Prepare the course deliverables specified in [REPORTING.md](REPORTING.md), including the
public team-owned repository, report and presentation. Complete the final phase record and
current-state handoff with any residual limitations and reproducibility conditions.

**Completion gate:** reported claims trace to valid evidence; analysis can be reproduced;
the method and limitations are understandable without earlier chats; course requirements
in REPORTING are satisfied.

## Dependencies, failed gates and changes of scope

Independent audit, component-design or evaluation tasks may proceed in parallel when their
inputs are established. Shared labels, data partitions, thresholds and interfaces remain
coordinated under AGENTS. Parallel execution does not remove an exposure boundary or a
required review.

When evidence fails a completion gate, stay in or reopen the affected phase. Record the
reason, impacted outputs and next diagnostic action; preserve superseded evidence and trace
downstream effects. [PHASE_RECORDS.md](PHASE_RECORDS.md) stores the closeout/reopening record.

Keep the chosen classifier, dataset, three principal precisions and focused learned-gate
investigation. Additional checks are welcome within those questions. New model families,
additional datasets, extensive fine-tuning, arbitrary quantization sweeps or early-exit
architectures require the scope decision defined by README; they are not prerequisites
for completing the selected research deeply.
