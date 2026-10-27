# Part 2: learned selective precision escalation

This document defines the learned gate: its decision rule, targets, admissible features,
training and diagnostic strategy, correctness checks, full system costs and standards for
quality–cost claims. The [README](../README.md) establishes Part 2 as committed project work;
[ROADMAP.md](ROADMAP.md) defines P2-A through P2-E and their completion conditions. Shared
data eligibility, Test-A/Test-B exposure, score semantics, metric definitions and resource
measurement controls are authoritative in [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md).

The desired result is useful accuracy recovery over always-low with a measured cost
reduction relative to always-high. The following method distinguishes those claims and
requires evidence for each, including any cost or quality regressions.

## 1. What the system decides

For each input x:

1. Run the selected low-precision classifier and obtain its score/logits and permissible features.
2. Apply the learned gate using only information available at this point.
3. If the gate chooses escalation, run the higher-precision classifier and return its prediction.
4. Otherwise return the original low-precision prediction.

Use the same shared classification threshold for the returned low/high scores. The gate's escalation cutoff is a separate parameter, selected on development data. Save both values and their roles.

The current scientific task is sequence classification, so there is no generated reasoning trace to inspect. The initial gate acts after the low-precision forward pass. An intermediate-layer or early-exit gate would require new signals, auxiliary computation and validation; it can be a later documented research direction, but it must not quietly replace the selected output-based learned-gate study.

Start by assessing INT8 as the low-precision candidate and FP32 as the higher-precision reference. Use Part 1 development profiles to verify which candidate is actually cheaper. FP16 may be the low-precision choice if evidence supports it. Record the pair before final gate evaluation. “Low” describes representation precision; “cheap” must be established by measurement. FP32 is not guaranteed to be correct whenever another treatment is wrong.

## 2. Separate the research claims

| Question | Correct reference | Required evidence |
|---|---|---|
| Does escalation recover useful accuracy? | Always-low on the same held-out inputs | Paired accuracy/quality changes, helpful and harmful reruns, uncertainty. |
| Does the system preserve or improve high-precision quality? | Always-high on those same inputs | Difference and interval; any accepted quality-loss tolerance declared before policy selection. |
| Does it save latency/computation? | Always-high **without first running low** | Measured full cascade cost with matched workload and timing boundaries. |
| What extra cost is paid for the quality gain? | Always-low alone | Gate and rerun overhead, route rate, memory and latency change. |
| Is learning useful beyond a simple heuristic? | Confidence and random routing at matched coverage or cost | Controlled comparison, including equivalent feature-acquisition costs. |
| Is deployment feasible under the stated assumptions? | Stated memory/loading and concurrency constraints | Combined resident/peak memory, loading/transfer costs and actual batching behavior. |

A gain over always-low does not prove savings over always-high. A lower latency does not imply a lower peak memory. Accuracy matching high precision does not establish identical FPR/FNR. Keep these as separate measurements before discussing the overall tradeoff.

### Predeclare what will count as support for a claim

Let Q be a selected quality metric for which larger is better, and C a selected measured cost for which smaller is better. For reference policy R, define **ΔQ(R) = Q(gate) − Q(R)** and **ΔC(R) = C(gate) − C(R)**. Thus positive ΔQ is a quality gain and negative ΔC is a cost saving. A relative saving may also be reported as **[C(R) − C(gate)] / C(R)** when C(R) is positive. Name the metric, unit, reference and evaluation population whenever reporting an effect; reverse the direction explicitly for error-rate metrics.

Choose the primary metrics, claim family, confidence level, one-sided or two-sided interval procedure, operating-point selection rule and any tolerances before final policy selection/confirmation. The following are candidate acceptance rules to select and record, not fixed numerical mandates:

| Intended claim | Example predeclared support rule |
|---|---|
| Accuracy gain over always-low | A positive paired accuracy estimate and a lower confidence bound above zero for ΔQ(low), using the declared procedure. Report effect size and practical relevance as well as statistical support. |
| Retained or near-high quality | Choose an acceptable loss tolerance δ before policy selection. A declared noninferiority procedure supports retention when the lower confidence bound for ΔQ(high) is at least −δ. State whether the bound comes from a chosen one-sided interval or the lower endpoint of a chosen two-sided interval. |
| Cost saving over always-high | A negative estimate for full measured ΔC(high), supported by the declared repeated-measurement uncertainty procedure; for example, an upper confidence bound below zero. Match workloads and include all stated system costs. Dtype, nominal operation counts or model storage are not substitutes for measured latency. |
| Joint quality–cost benefit | Meet the declared quality-gain criterion against low and cost-saving criterion against high for the same frozen policy under the stated statistical procedure. If the claim also promises retained high-precision quality, meet that noninferiority criterion too. Report memory and other resource regressions separately. |

δ should reflect a scientifically or practically acceptable loss, with units stated, rather than the loss that happened to appear in the test result. A failure to find a significant difference from always-high does **not** establish equivalence or noninferiority. Equivalence would require its own predeclared two-sided acceptable region and procedure; do not use the terms interchangeably.

Use paired uncertainty for quality comparisons on matched examples and a repeated-trial design appropriate to the cost statistic. Distinguish request variability from run-to-run measurement variability. If several policies, operating points or metrics are used to make confirmatory claims, predeclare how the claim family is handled; do not select a favorable test-set comparison or interval after observing the outcomes. Validation-selected primary policies and clearly labeled secondary analyses keep this manageable.

Every measured result can still be reported descriptively with its estimate, interval and limitations. An interval that overlaps zero is not a reason to hide the finding, and statistical significance is not required merely to report an observation. Use language such as “estimated gain with uncertainty spanning zero” when the predeclared rule does not support a stronger improvement claim.

## 3. Recoverable benefit and oracle headroom

For each labeled development example, join low/high predictions by stable ID. Define the per-example correctness benefit as:

**b(x) = correctness(high, x) − correctness(low, x)**.

The target takes three values:

| Target | Meaning | Consequence of escalation |
|---|---|---|
| +1 | Low is wrong; high is correct | Corrects an error. |
| −1 | Low is correct; high is wrong | Introduces an error. |
| 0 | Both are correct or both are wrong | No accuracy change, but still incurs the rerun cost. |

Count all four correctness combinations, class support and the distribution of b. Inspect recoverable-error prevalence and where it occurs in development data. A low-confidence example may be difficult for both models; a confident low-precision error may still be recoverable. Therefore uncertainty is a useful baseline feature, not proof of benefit.

The oracle that escalates exactly the b=+1 cases gives an accuracy upper bound for the fixed low/high pair and decision threshold. It uses ground-truth information unavailable at deployment. It is neither a feasible gate nor automatically optimal for macro-F1. Use it to assess headroom and diagnose what the learned policy misses, not as a claimed achieved system. The permitted evidence for this analysis is defined by the data-role and reuse rules in RESEARCH_PROTOCOL.

If observed headroom is very small, verify label mapping, shared preprocessing, numerical treatment and paired joins before interpreting it. Examine whether the precision pair, threshold neighborhood or truncation behavior explains the scarcity. The conclusion may be meaningful, but it must follow investigation rather than a single low aggregate difference.

## 4. Routing baselines and operating-point selection

Evaluate the following on common development inputs and matched workload assumptions:

- **Always-low:** return the low-precision result and pay only its cost.
- **Always-high:** run high precision directly, without a preliminary low pass.
- **Random reruns:** rerun a fixed random fraction, matched to the evaluated policy's route rate or measured cost. Record seeds and uncertainty.
- **Confidence routing:** use distance to the common classification threshold, such as the absolute difference between the low score and t. Smaller distance is a candidate sign of uncertainty.
- **Learned routing:** predict expected benefit using development-fitted features and parameters.
- **Oracle reference:** theoretical recoverable-error selection, clearly nondeployable.

Binary entropy centered at 0.5 is a possible secondary uncertainty baseline. It differs from distance to a threshold t when t is not 0.5. Select a small, documented set of alternatives; avoid adding baselines solely because one happens to make the learned gate look better.

Evaluate coverage/quality/cost curves across a declared set of gate thresholds. Choose one or a few final operating points using validation, not Test-B. Possible selection criteria include minimum cost within a predeclared quality tolerance of always-high, maximum quality under a cost budget, or a Pareto-efficient point with a clearly stated preference. The tolerance or budget is a choice to record before selecting a winning point.

## 5. Learned-gate formulation and investigation

### Target and objective

A useful first formulation estimates the three target probabilities and computes:

**estimated net accuracy benefit = P(b=+1 | available features) − P(b=−1 | available features)**.

This explicitly accounts for harmful reruns. Training only a “low model is wrong” detector is insufficient because the high model may also be wrong. Training only a recoverable-error detector without accounting for regressions can also select an unfavorable policy.

A cost-aware gate can compare predicted net benefit with predicted incremental escalation cost. One candidate objective is expected accuracy benefit minus a chosen cost penalty; another is maximizing expected benefit under a budget. Keep the units clear: a quality fraction and milliseconds are not directly comparable until a documented weight or constraint connects them. Accuracy-derived benefit does not directly optimize macro-F1 or class-specific security costs; report those metrics, and consider a carefully defined class-weighted objective as a separate development hypothesis if needed.

### Permissible features

Candidate features available without running high precision include:

| Feature | Reason to investigate | Cost or validity concern |
|---|---|---|
| Low injection score / distance from t | Captures the decision boundary and score confidence. | Scores may be miscalibrated; probability and confidence are not interchangeable. |
| Low binary entropy or logit margin | Summarizes uncertainty or separation. | These may be redundant for binary classification; test their added value. |
| Effective/original token length | Cost and difficulty may depend on length. | Obtaining the original length can require additional tokenization; count it. |
| Truncation flag | A missing part of the input may affect recoverability. | Use a consistent deployed preprocessing policy. |
| Low-run numerical/representation signal | May capture ambiguity beyond the output score. | Include only if available without high precision and measure acquisition/storage overhead. |

Forbidden gate inputs include the high-precision score or prediction, either model's correctness, reference labels, oracle benefit, test-set identity, and annotations unavailable at deployment. Labels and high predictions can construct **training targets**, but must never become inference features. Inspect the entire feature pipeline, not just the fitted estimator, for leakage.

### Models and fitting discipline

Start with a small interpretable model, such as regularized multinomial logistic regression. A regression model for net benefit is an alternative. A modest tree-based model can test nonlinear interactions if the development evidence justifies it. These are candidate approaches, not mandatory implementations of every family.

Fit on eligible training paired predictions. Fit feature scaling, imputation, selection and class weighting on training data only. Use training-only cross-validation for model/hyperparameter exploration when practical; reserve a clear validation role for operating-point selection. If benefit classes are absent or extremely sparse, record the issue and use an explicit fallback or alternative formulation; do not fabricate examples or present unstable class probabilities as reliable estimates.

Keep validation overuse visible. If repeated research iterations rely heavily on it, use a declared development/selection split or training-only cross-validation for new choices. Do not solve this by opening Test-B. Preserve the relation between gate training data and any feature-calibration data.

### Serious iteration rather than one attempt

For each iteration, write a hypothesis, the data role, the change, expected mechanism, observed result and decision. Investigate at least the relevant failure categories:

1. **Validity:** label orientation, joins, threshold application, actual precision conversion, batching and numerical stability.
2. **Available benefit:** how many errors are recoverable, how often high precision harms, and the maximum attainable quality under the pair.
3. **Signal:** whether uncertainty/length/features discriminate benefit on development data; feature ablations and simple controls.
4. **Learning:** sparse target classes, overfitting, calibration of benefit estimates, regularization and validation stability.
5. **Cost:** gate/feature overhead, routed-example length distribution, batching fragmentation, transfers, loading and combined memory.
6. **Operating point:** whether a useful frontier exists even if one initially chosen threshold is poor.

Use this diagnosis to select meaningful next experiments. Additional tests and analyses are welcome. Avoid both premature abandonment and unbounded blind searching. Closing a direction requires an evidence-backed account of attempted hypotheses, remaining limitations and what would be needed to improve it. Record unresolved work for the next agent rather than silently dropping it.

## 6. Gate correctness checks

In addition to the common validation in RESEARCH_PROTOCOL, verify these gate-specific behaviors with known-answer examples and integration checks:

- Gate features can be produced before the high model is called, and the unselected high path does not execute accidentally.
- Zero routing reproduces always-low labels; routing every input reproduces always-high labels while correctly paying for both passes.
- Escalated requests return the corresponding high result; non-escalated requests retain the corresponding low result, joined by ID.
- Empty routed batches, all-routed batches, partial batches and threshold equality are handled explicitly.
- Helpful reruns minus harmful reruns equals the net accuracy-count change relative to always-low on the same examples.
- The oracle never scores worse than the gate in accuracy under the same fixed pair and threshold; a violation suggests a bug or mismatched definitions.
- Cached replay and actual integrated execution agree on decisions/scores within the stated numerical tolerance when configured equivalently.
- The integrated trace and reported resource totals agree with the component boundaries and residency scenario in Section 7.

Record exact evidence in [VALIDATION_LOG.md](VALIDATION_LOG.md). These requirements describe checks to build and perform; a checklist entry alone is not evidence that it passed.

## 7. Full cascade cost accounting

For one sequential request, the total cost includes:

**C_gate-system(x) = C_low(x) + C_features(x) + C_gate(x) + I(escalate) × [C_high(x) + C_extra-transfer-or-load(x)] + C_other-system(x)**.

Do not double-count a component already inside an end-to-end measurement. Define boundaries explicitly. The always-high baseline is high inference alone under the corresponding loading/workload convention, not low plus high. Always-low likewise excludes the gate and high pass.

If per-input costs vary, estimate the average of the actual selected costs. A simple route-rate average can be misleading when the gate routes longer inputs. Batching and concurrency can change the formula's additive interpretation; measure the integrated system when making a runtime claim.

**Illustrative arithmetic, not a project result:** suppose low inference costs 4 ms, feature/gate processing costs 0.2 ms, and high inference costs 10 ms, with both models already resident and constant per-request costs. Expected cascade time is 4.2 + 10r ms at route rate r. Saving time versus always-high requires r < 0.58. Routing 20% gives 6.2 ms, a 38% reduction relative to 10 ms, while costing 55% more than always-low's 4 ms. Real measurements must test whether these assumptions apply.

For the same illustrative 1,000 inputs, suppose low is correct on 900, high on 930, and the pair has 45 recoverable errors plus 15 harmful reruns. A gate correcting 30 and harming 5 returns 925 correct: +2.5 percentage points versus low, but −0.5 points versus high. That is a quality–cost tradeoff, not an accuracy improvement over high. It might meet a predeclared tolerance, but the tolerance and statistical uncertainty cannot be invented after seeing the result.

### Memory and loading scenarios

| Scenario | What to measure and report |
|---|---|
| Both variants resident | Combined model/gate memory, peak activations, allocator behavior, and any reduced batching capacity. Lower latency does not imply lower memory. |
| Higher precision loaded on demand | Real load/transfer latency, cache state, eviction/reuse policy, request frequency and peak memory. Do not assume free loading. |
| Offline paired-score replay | Policy quality, route selection and estimated costs only. It does not prove end-to-end speed, memory or concurrency feasibility. |

Choose and document the main deployment scenario during development. At least one claimed useful operating point needs measured integrated execution. An on-demand benefit claim additionally requires its loading path to be measured. Reuse tokenization only if the actual implementation does so; include any extra feature-extraction work. Record whether latency includes queueing and how throughput/concurrency are controlled. The end-of-P2-D freeze in ROADMAP binds the measured implementation and selected policy before confirmation.

## 8. Evidence needed to interpret the gate

The confirmatory comparison follows the P2-D freeze and P2-E procedure in ROADMAP, using
RESEARCH_PROTOCOL's shared population and measurement controls. In addition to the common
classification/resource metrics, retain route rate, helpful and harmful reruns, shared
errors and missed recoverable errors. These quantities explain whether a favorable or
unfavorable result comes from the pair's headroom, gate selection or system overhead.

Show the preselected operating point with sufficient development-frontier context and
confidence/random controls to explain the tradeoff. Apply Section 2's predeclared support
rules independently to each claimed outcome. A quality gain, a cost reduction and retained
high-precision quality are distinct conclusions; report memory or other regressions even
when the primary criterion is met.

[REPORTING.md](REPORTING.md) specifies the presentation of this evidence. Retain the fitted
versions, feature/cost definitions, iteration and ablation outcomes, validation evidence
and complete execution artifacts so every conclusion is traceable to the actual policy.
