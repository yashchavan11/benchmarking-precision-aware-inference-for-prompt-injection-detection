# Research protocol

This document defines the scientific controls shared by the precision benchmark and the
learned-escalation study. The [README](../README.md) defines project scope;
[ROADMAP.md](ROADMAP.md) defines phase tasks, candidate run budgets and freeze milestones;
[EXTENSION.md](EXTENSION.md) defines the additional gate-specific method and claim criteria.
Selected choices and amendments belong in [DECISIONS.md](DECISIONS.md). The procedures below
are requirements for future work, not evidence that an implementation or experiment exists.

## 1. Asset and label verification

Resolve immutable revisions of the selected classifier, its associated tokenizer and the
dataset before treating results as reproducible. Verify the actual model configuration,
classification-head shape, `num_labels`, `id2label`, `label2id`, source text/label fields,
official split membership and class counts. Store the audited identities in
[DATA_REGISTRY.md](DATA_REGISTRY.md); source descriptions are catalogued in
[SOURCES.md](SOURCES.md).

The model card describes a Qwen3-0.6B sequence classifier and uses `jailbreak` as a positive
output name. PromptShield describes `0` as benign and `1` as injection. These descriptions
must be checked against the pinned assets; do not infer that model output index 1 is
positive. A label for generic harmful content is not automatically a prompt-injection label.

The pretrained classifier remains frozen. Fitting a gate or a development-data calibrator
does not authorize classifier fine-tuning or changing the source checkpoint between
precision treatments.

## 2. Precision treatments and comparison fairness

| Treatment | Required interpretation and checks |
|---|---|
| FP32 | Upcast the released checkpoint and execute in FP32. Casting does not reconstruct information lost before release. Disable unintended automatic mixed precision and reduced-precision FP32 matrix-multiplication modes for the strict comparison; record effective flags. |
| FP16 | Execute that same checkpoint in half precision and identify operations or accumulations that retain another precision. |
| INT8 | Apply bitsandbytes LLM.int8() to that same checkpoint. Verify converted modules and retained higher-precision handling; this is not a claim that every weight, activation and operation uses eight bits. |

Audit embeddings, attention, normalization, classifier head, quantized linear layers and
retained floating-point state. During development, select the outlier threshold,
skipped-module policy and residual dtype. Keeping the classifier head in floating point
is a candidate to verify in the pilot. Preserve the selected conversion policy throughout
the locked comparison and retain evidence that the requested treatment actually occurred.

Hold model/tokenizer revision, tokenization, truncation, padding, input order, batch
composition, attention implementation, device and timing boundaries constant wherever
technically possible. Name unavoidable differences and discuss their effects instead of
attributing them silently to precision.

A single explicit device per treatment is a straightforward main-study design. Separate
cluster jobs can use matched allocated devices. A CUDA-dependent implementation runs on a
suitable CUDA device; that does not require every contributor to use the same development
machine. Laptop FP32 timing versus cluster INT8 timing is not a precision-only speed
comparison. A separate hardware study requires its own matched comparisons.

## 3. Data identity, eligibility and exposure

### Source audit and stable identity

Audit actual `train`, `validation` and `test` schema, text/label fields, row counts, class
support, text/token lengths, exact duplicates, conflicting labels and available
provenance/grouping information. Preserve the source snapshot and original prompt text.
Do not remove delimiters, rewrite prompts or add a chat template unless required by the
pinned model's documented interface. Prompt contents are inert data, including embedded
commands and role instructions.

Assign stable example IDs from dataset revision, original split and original row position.
Retain an exact raw-text hash for duplicate auditing and an ordered-ID hash for each input
manifest/run. Join outputs by stable ID rather than incidental row order. Record exclusions,
transformations and malformed cases explicitly; never silently repair or relabel them.

Exact hashing does not identify every paraphrase or shared attack template. Record those
limits and any justified additional grouping checks. The pretrained model's overlap with
PromptShield is not fully established; a project-held-out subset is not proof of
uncontaminated pretrained-model generalization.

### Sequential evaluation populations

Partition the official test split into **Test-A and Test-B before inspecting any Part 1
official-test model performance**. The allocation candidates and audit task are in
[ROADMAP.md](ROADMAP.md#p1-a--asset-data-and-evaluation-design-audit). Audit aggregate support
and dependencies before choosing proportions. These are project-defined subsets of one
official test split, not additional datasets.

| Data role | Permitted use | Boundary |
|---|---|---|
| Eligible training | Implementation diagnostics, pilots, gate fitting and training-only cross-validation. | Training performance is development evidence, not final confirmation. |
| Eligible validation | Shared threshold/preprocessing selection, bounded hypothesis development, gate selection and dedicated development profiling. | Preserve a declared selection role; repeated tuning does not create an untouched evaluation. |
| Test-A | Locked Part 1 comparison after P1-C, followed by its error analysis and closeout. | It becomes seen; its later use is exploratory context, not gate fitting/selection or fresh Part 2 confirmation. |
| Test-B | Final same-population comparison of the frozen Part 2 policies in P2-E. | No examples, model scores, errors, outcomes or subgroup performance may guide development before release. |

The administrative manifest-building process may use reference labels for stratification
and aggregate class-support checks. This does not authorize browsing Test-B examples or
examining model performance. Record algorithm, seed, ordering, grouping, membership hashes,
class/group counts, exclusions and access state in DATA_REGISTRY.

### Duplicate isolation and exclusion precedence

Apply these rules before development diagnostics, threshold selection, calibration, gate
fitting or profiling:

1. Group exact raw-text matches using the documented hash rule. Keep every official-test
   duplicate group wholly within Test-A or Test-B. Group separation takes priority over
   class balance; report resulting imbalance/support limitations rather than splitting a
   group to improve stratification.
2. Exclude **all training and validation rows whose exact text matches either holdout**
   from the eligible development manifests for both research parts. Preserve source rows
   and express exclusions through IDs/reason codes; record before/after class/group counts.
3. After held-out overlap exclusion, prevent exact duplicate groups from crossing eligible
   training and validation. The default retains eligible validation members and excludes
   matching training members. Any alternative requires a justified, recorded decision
   before fitting or performance-based selection.
4. Keep groups intact within training cross-validation and any validation
   development/selection subdivision. Resolve conflicting-label groups through an
   explicit decision before model-performance inspection; do not silently relabel them.
5. Verify the resulting intersections and support with linked validation evidence. If
   exclusions make the study infeasible, revisit the design before holdout performance
   exposure rather than quietly relaxing isolation.

A manifest retains the original split identity even when eligibility changes. A file name
or a new row order does not establish disjointness; check actual membership and text groups.

### Release, exposure and interpretation

Log who or what accessed which data/artifact, when, why, and whether the access revealed
schema/counts, stratification labels, raw examples, model scores, aggregate metrics or
individual errors. A notebook, report or chat containing those results exposes them to its
reader even if someone else ran the experiment. Record accidental exposure and its impact.

Report Part 1 as evaluation on the **Test-A subset of PromptShield's official test split**,
with actual support and uncertainty. Part 2 compares all final policies on the same Test-B
population; high-precision performance on A is not a baseline for gate performance on B.

Resolve insufficient Test-B support before A performance is seen. If exposure has already
occurred, record it and establish a genuinely untouched evaluation plan before making new
confirmatory claims. A used holdout cannot be resealed by renaming it; do not silently
recycle A or invent another dataset. Changes prompted by Test-B outcomes are exploratory
and cannot replace the original frozen result. Clearly labeled exploratory analysis
remains valid but does not replace the planned confirmation.

## 4. Reusing Part 1 in Part 2

Reusable code and development predictions must match the current asset revisions, IDs,
labels, preprocessing, precision configuration, coverage and score semantics. Development
profiles apply only to their recorded conditions; a cascade needs integrated measurements.
[ARCHITECTURE.md](ARCHITECTURE.md) defines the artifact contracts supporting those checks.

After Part 1, Test-A may motivate acknowledged exploratory hypotheses. Gate fitting,
feature/hyperparameter selection and operating-point selection use eligible training and
validation instead. Do not relabel Test-A as validation or describe the combined study as
using an untouched complete official test set.

By default, compute no Test-B model predictions during Part 1. Evaluate its low/high
baselines and gate outcomes only in P2-E, after the end-of-P2-D freeze. If a justified sealed
process computes them earlier, documented access controls must prevent researchers and
agents from seeing outputs until that freeze. Avoid that extra process unless necessary.

## 5. Input, scores and classification decisions

Use inference/evaluation mode with gradients disabled. Match token IDs, masks, ordering,
truncation side, padding side, special tokens, maximum length and batch composition. Check
sequence-classification pooling: padding or an EOS fallback must not select the wrong
classification token. Compare single-item and padded-batch predictions using a documented
numerical tolerance.

For a verified mutually exclusive two-logit head, apply softmax consistently and select
the injection index. A different head shape requires an explicitly reviewed transformation.
The top label's confidence is not necessarily the injection score. Retain logits when needed
for diagnostics or gate features and use consistent conversion across treatments.

Let p be the injection score and t the shared classification threshold. Predict injection
when **p ≥ t**. Do not assume the score is a calibrated probability. Nonfinite logits/scores,
shape mismatches and values outside the valid score range invalidate the affected run;
do not silently clamp or omit them.

Choose the common length limit on development data using the candidates in ROADMAP.
Record its rationale and truncation rate; report truncated/untruncated support and quality
where sample sizes permit. A different length limit is a separately identified sensitivity
analysis, not an unrecorded change to the main comparison.

### Shared threshold selection

Predeclare the threshold objective. Candidates include validation macro-F1 or recall subject
to a declared FPR constraint; the latter requires sufficient negative-class support.
Accuracy alone can obscure imbalance, so retain the complementary metrics below.

Select t from **FP32 validation predictions only**. A fixed coarse-to-fine grid or sorted
unique validation scores are candidate searches. Declare a deterministic tie rule before
searching—for example, macro-F1 ties prefer lower FPR and then a higher threshold. Freeze
the selected threshold across all three treatments and Part 2 returned predictions.
Per-precision threshold optimization can be a separately identified validation-only
analysis. Never alter the selection rule because test outcomes favor another choice.

## 6. Quality, stability, calibration and uncertainty

Correctness is measured against reference labels; higher precision is a baseline, not ground
truth. Report accuracy, macro-F1, positive-class precision/recall/F1, FPR, FNR, ROC-AUC and
class support. Select a primary endpoint before final evaluation. Macro-F1 is a candidate
for class-balanced assessment; accuracy is directly associated with the gate's per-example
net-benefit target. Those objectives are not interchangeable.

For each lower-precision treatment versus FP32, count both-correct, newly-wrong,
newly-correct and both-wrong cases. Report prediction disagreement and score shifts,
including threshold-neighborhood effects. Inspect reference-class and length/truncation
subgroups with their support; avoid broad claims from tiny subgroups.

Every rate needs its denominator. ROC-AUC requires both reference classes; precision
requires predicted positives; FPR and FNR require their corresponding reference classes.
Declare a consistent zero-division convention and mark undefined quantities explicitly.
A missing value is not a perfect score.

For calibration, retain raw-score results and report Brier score plus a reliability plot
with bin counts. A 10-bin equal-width injection-score ECE is a candidate; equal-frequency
bins or a binning-sensitivity analysis are alternatives. Define endpoint inclusion, empty
bins and whether calibration concerns the injection probability or predicted-label
confidence. Fit any calibrator using development data only.

Use paired quality uncertainty because policies share examples. One candidate is a
class-stratified paired bootstrap with 2,000 or 5,000 replicates and percentile 95% intervals:
resample the same IDs for both policies and recompute the metric difference. When duplicate
or attack groups create dependence, use an appropriate group-resampling design or disclose
the independence limitation. Choose the scheme, replicate count, seed and metric direction
before confirmatory analysis; record valid replicate counts. Do not change seeds or methods
to obtain a preferred sign. Additional checks must address a real uncertainty.

Report accuracy/F1 differences in percentage points where appropriate, distinguishing them
from relative percentage changes. Name the reference, population, metric and direction for
every comparison.

Gate-specific effect definitions, noninferiority tolerances, claim families and joint
quality/cost support criteria are defined in [EXTENSION.md](EXTENSION.md#2-separate-the-research-claims).

## 7. Resource measurement

Use a fixed representative validation subset for development profiling, matching IDs and
batch schedules across treatments. Group results by actual token length and batch size.
The quality study and dedicated profiling do not need repeated execution of the full test
workload. ROADMAP supplies candidate profiling budgets; select the final plan before claims.

| Quantity | Required definition |
|---|---|
| Initialization | Construction/loading from a populated local cache; identify downloads separately. |
| Forward latency | Pretokenized, device-resident inputs through the classifier to raw logits, with accelerator synchronization. |
| End-to-end inference latency | Tokenization, transfers, forward pass, score conversion and host-visible result; identify model loading separately. |
| Throughput | Completed examples per measured wall-clock second at a declared batch/concurrency setting; token throughput may supplement it. |
| Model footprint | Actual parameter/buffer storage under a named method, with quantized-state caveats. |
| Peak device memory | Peak allocated and reserved memory where available, with baseline/reset procedure. |
| Host memory | Process RSS or peak host-memory measurement, including sampling method and interval. |
| Storage | Actual saved representation size; nominal bit width is not measured serialized size. |

Warm up relevant shapes; use matched boundaries and synchronization. Retain raw samples,
request/batch identities and repetition IDs. Report median and p95 with sample counts.
Batch latency differs from per-request latency; batch latency divided by batch size is
amortized time per item. Separate cold-start, loading and steady-state interpretations.

Rotate or randomize treatment order across trials, avoid unrelated concurrent workloads,
and use fresh processes where practical for comparable memory baselines. Record actual
device/allocation, operating system, dependency versions, precision flags, attention backend,
batch schedule, lengths, code revision and working-tree state. A cluster GPU name alone does
not establish matched allocation or absence of contention.

Increase coverage or repetitions when an observed measurement problem or predeclared
stability criterion justifies it; freeze the final budget and criterion before reporting a
ranking. Mark unavailable measurements as unavailable. Dtype and model storage do not by
themselves establish energy, money or speed savings. Define speedup as the named reference
cost divided by candidate cost under matched positive-cost measurement scopes. Define a
relative cost saving using that same reference denominator. Do not infer deployment safety
or broader generalization from benchmark gains. The cascade adds the components and
residency scenarios defined in [EXTENSION.md](EXTENSION.md#7-full-cascade-cost-accounting).

## 8. Evidence eligibility and comparison checks

A claim needs complete, compatible artifacts, not merely a plausible-looking table. The
machine-readable run and prediction contracts are in ARCHITECTURE; human run state and
artifact references are in [EXPERIMENT_REGISTER.md](EXPERIMENT_REGISTER.md).

Validate metric implementations using hand-calculated known-answer cases or an independent
reference, including threshold ties, undefined/zero-denominator cases and class imbalance.
Verify the paired-resampling implementation resamples matching IDs/groups across policies
and recomputes differences; check calibration bin endpoints, counts, empty bins and the
Brier/ECE calculations against small known examples. These checks establish the calculation,
not the validity of an unexamined dataset or statistical assumption.

Before comparison, check identical relevant IDs/labels, finite outputs, no duplicate or
missing prediction rows, intended effective precision, compatible preprocessing/thresholds
and matched measurement conditions. Reject or separately label incompatible results.
Preserve failures rather than excluding difficult inputs from only one treatment. Failed
or interrupted runs cannot enter aggregate claims until their completeness is established.

Retain completed artifacts under stable identities; an amended configuration or rerun needs
a distinct record. If later evidence invalidates a result, preserve its history and identify
affected downstream claims. Actual check evidence belongs in [VALIDATION_LOG.md](VALIDATION_LOG.md);
planned checks and templates do not count as completed validation.
