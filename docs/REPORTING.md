# Research outputs and course deliverables

## November 18 progress report - runtime/resource section (Hareeshwar)

Completed resource section for Shreyas to place in the assembled progress report. The values are
regenerated from the retained raw samples by `precision_benchmark.resource_summary` (V-044, RES-006),
not typed by hand. Evidence: [resource table](evidence/p1b-resource-20261118/resource.csv),
[length breakdown](evidence/p1b-resource-20261118/resource_by_length.csv),
[figure](evidence/p1b-resource-20261118/latency_vs_tokens.png) and the
[full summary](evidence/p1b-resource-20261118/resource_summary.json). Text between the rules is
ready to paste; trim the figure or the length sentence first if space is short.

---

**Runtime and resource measurements (preliminary).** All three treatments ran the same 128
pretokenized training examples on one NVIDIA L40S (48 GB, CUDA 12.6, PyTorch 2.9.1, Transformers
4.57.1, bitsandbytes 0.48.2), in fresh processes within one Slurm allocation, in the fixed order
FP32, FP16, INT8. Inputs were unpadded, batch size 1, capped at 1,024 tokens (9-1,024, median 83).
The timer wraps one synchronized forward pass from device-resident token tensors to raw logits;
it excludes tokenization, host-device transfer, score conversion and file output. Peak memory is
PyTorch's maximum allocated GPU memory after a reset that follows warm-up.

| Treatment | Median forward (ms) | p95 forward (ms) | Peak allocated GPU memory (MiB) | Parameter storage (MiB) | Derived forward-only rate (ex/s)* |
|---|---:|---:|---:|---:|---:|
| FP32 | 25.51 | 59.68 | 2,482.78 | 2,273.76 | 31.62 |
| FP16 | 26.27 | 27.00 | 1,321.42 | 1,136.88 | 31.20 |
| INT8 (LLM.int8) | 87.49 | 93.48 | 932.56 | 716.88 | 11.18 |

\*128 examples divided by the sum of their 128 forward durations. This is a derived forward-only
service rate, not a measured wall-clock, sustained or end-to-end throughput, and not 1 / median latency.
p95 uses the nearest-rank rule.

**Memory versus latency trade-off.** Lower precision reduced memory: peak allocated memory was 53%
(FP16) and 38% (INT8) of FP32. Almost all of the saving is weight storage; the post-warm-up workload
on top of the resident model was similar in every mode (about 150-180 MiB). INT8 did not reach a
quarter of FP32 because LLM.int8 quantizes only the 196 transformer linear projections. The
151,936 x 1,024 token-embedding table (296.75 MiB) and the classifier head stay in FP16. INT8 was
**slower**, not faster: its median forward time was 3.4x FP32's and its derived rate about one third.
FP16 matched FP32's median on short inputs. Above 512 tokens FP32's median rose to 56.0 ms while
FP16 stayed at 26.2 ms (n=32). INT8 was about 87-92 ms in every length band. The flat FP16/INT8
curves suggest that per-call fixed costs dominate at batch size 1 for this 0.6B model. LLM.int8's
extra per-projection quantization and outlier handling are a plausible source of INT8's constant
overhead, and FP32 with TF32 disabled is a plausible reason for its long-input growth. These are
hypotheses; we did not profile kernels to confirm them. Lower bit width therefore reduced memory
but did not reduce latency on this GPU. On this evidence, INT8 is better suited to memory-limited
deployment than to latency-critical deployment. FP16 showed the most favorable latency/memory
combination observed in this pilot, with one unexplained 493 ms spike.

**Measurement limits.** (1) Batch size 1 only; no batching or concurrency. (2) Warm-up used only the
first three inputs (63, 92 and 12 tokens), so 59 of the 128 timed inputs were longer than any
warm-up shape. (3) One measured pass per example, with a fixed treatment order and no repetitions,
so we report no variance or confidence intervals. Isolated spikes are kept in the data (FP16:
493 ms at 712 tokens; INT8: 264 ms at 1,024 tokens), and their causes are unknown. (4) The timer
excludes tokenization, transfers and score conversion, so these are not end-to-end request latencies.
(5) Peak memory covers PyTorch allocations only, not the CUDA context, the allocator's
reserved-but-unused memory or host memory. (6) The recorded loading times (6.7/0.9/32.3 s) depend
on run order and file-cache state, and INT8's includes on-load quantization, so we do not compare
them. (7) The 128 examples are a length-enriched development sample on a shared cluster node, so
the results are feasibility observations, not a final speed ranking.

**Reproduction.** Native run: `scripts/run_precision_pilot.sbatch` on Explorer (job 11959388,
commands in `docs/USAGE.md`). Offline regeneration of this table and figure, without a GPU:
`python -m precision_benchmark.resource_summary --manifest docs/evidence/p1b-pilot-20261117/comparison.json --output outputs/resource-new`.
The command checks the hash chain from the comparison manifest to each run's measurement files.
It also confirms that all three treatments timed identical examples and token lengths on one
device, and that the recomputed median and p95 equal the values recorded during the run.

**Next profiling work (final report).** Warm up every measured shape. Repeat measurements under a
rotated treatment order. Run batch-size and length sweeps. Measure sustained wall-clock and
end-to-end throughput, including tokenization and transfer. Report model size on disk, loading
time under a cold cache, and kernel-level profiles to test the INT8 overhead hypothesis.

*Figure (optional):* `docs/evidence/p1b-resource-20261118/latency_vs_tokens.png`. Caption: Per-example
synchronized forward time against input length (log-log), 128 matched development inputs, batch 1,
one L40S; dashed lines show medians, and the shaded band marks lengths up to the longest warm-up input.

**Contribution (Hareeshwar Muthu Kumaran).** Verified the retained runtime evidence against the raw
per-example samples. Implemented and tested the offline resource-summary module
(`precision_benchmark/resource_summary.py`, 7 tests). Produced the resource table, the length
breakdown and the figure. Wrote the resource analysis, measurement limits and reproduction
instructions. The Explorer GPU environment, the timing/memory instrumentation and the native
pilot run were prepared earlier in the shared pilot (P1-B) and are not claimed here. Claude Code
(an AI assistant) helped with implementation and drafting.

---

## November 18 progress report - completed inference contribution

Yash supplied the actual course guidelines: the progress report is **at most four pages**,
due November 18, covering implementation status, the data pipeline and baseline results,
preliminary evaluation, and lessons learned/remaining risks. Verified requirement/source
identity is below. This record supplies evidence and reusable prose; no report was submitted.

The inference contribution is complete for the agreed progress-report pilot: a working
FP32/FP16/LLM.int8 command, verified checkpoint/label/pooling/precision treatment, 384 saved
ID-aligned predictions, environment/setup guidance and regenerated preliminary tables.
See [RES-004](RESULTS.md#res-004---three-treatment-development-feasibility-not-a-held-out-ranking),
the [portable bundle](evidence/p1b-pilot-20261117/comparison.json),
[usage instructions](USAGE.md#preparing-and-running-the-development-precision-pilot)
and the P1-B closeout in PHASE_RECORDS. The exact executed source package is retained with
the predictions, so teammates can inspect the code and reanalyse without GPU/model access.

### Suggested inference/results text for the team report

We implemented reproducible inference for the same frozen Sentinel v2 checkpoint in FP32,
FP16 and bitsandbytes LLM.int8. A deterministic development pilot used 128 training examples
(64 per class), with additional long inputs for diagnostic coverage. All modes processed
identical token/mask sequences on one NVIDIA L40S, using unpadded batch size 1, a 1,024-token
cap and a provisional shared 0.5 threshold. Actual model checks verified the two-logit
label mapping, final-token/EOS pooling, frozen parameters and effective precision. INT8
converted 196 transformer projections while retaining the head/residual parameters in FP16;
some internal operations and buffers remain FP32. The released checkpoint itself is F16,
so the FP32 condition is an upcast representation.

FP32 and FP16 each classified 97/128 examples correctly (75.78%, macro-F1=0.7447). INT8
classified 98/128 correctly (76.56%, macro-F1=0.7538), correcting one near-threshold false
negative relative to FP32. FP32/FP16 missed 30/64 injections; INT8 missed 29/64. Most errors
were shared across precisions, and higher precision did not correct a lower-precision
error in this small pilot. The balanced, length-enriched training sample and provisional
threshold do not establish held-out performance, statistical superiority or learned-gate
benefit. No official-test predictions were produced.

Observed median forward times were 25.51/26.27/87.49 ms for FP32/FP16/INT8, with peak
PyTorch allocated memory 2482.78/1321.42/932.56 MiB. INT8 used less measured memory but
was slower by this pilot timing measure. These are single-pass, fixed-order feasibility
observations. The three warm-up inputs had only 63, 92 and 12 tokens, leaving longer
shapes without explicit warmup coverage. The forward timer excludes tokenization, transfers
and score conversion. The post-warm-up PyTorch memory window includes GPU input, forward
and score-conversion allocations; it does not measure total device or host memory. Repeated,
shape-aware profiling and end-to-end costs remain to be established.

For a compact report, use the [quality table](evidence/p1b-pilot-20261117/analysis/quality.csv)
and RES-004's resource table with their denominators and scope. The complete results include
AUC, calibration, score shifts and truncation groups; select only what fits the four-page
progress format without hiding unfavorable outcomes. Software evidence is 107 tests passed
on the actual GPU job and 111 local tests after adding the offline comparison command.

### Lessons, remaining risks and team assembly

- Exact input/pooling controls matter: blindly assigning PAD=EOS can change the selected
  classification token. The pilot preserves original batch-one pooling; larger batching
  needs a separately checked policy if selected.
- Lower bit width did not imply faster inference in the observed pilot. Explain memory
  and latency separately, with the raw measurement boundaries and limitations.
- The provisional operating point missed many injection examples. Select the final common
  threshold from FP32 validation predictions under a predeclared rule; do not tune it on
  held-out data or describe raw scores as calibrated probabilities.
- Keep source contamination/near-duplicate uncertainty, limited pilot support and unknown
  external exposure explicit. Detection is one control, not a guarantee against injection.
- Shreyas's remaining work includes source-based qualitative investigation of permitted
  development failures, in addition to report assembly/integration. Descriptive error counts,
  truncation groups and the single threshold-crossing case already exist; prompt-level
  explanations and annotation interpretation have not been performed.
- Hareeshwar can use the newly recorded, explicitly scoped derived forward-only rate.
  Sustained wall-window/end-to-end throughput is still unmeasured. Fully warmed, repeated and order-controlled profiling remains substantive
  technical work before strong performance claims; it is not merely formatting a table.
- Viraj can reuse the verified data/manifests and coordinate/document preprocessing. No
  missing Viraj implementation blocks the current pilot. Actual contribution/review must
  be credited from evidence, rather than inferred from the responsibility assignment.

The full project still needs the main protocol freeze, validation threshold selection,
Test-A benchmark/error analysis and Part 1 closeout, followed by the substantive learned-gate
investigation, final Test-B comparison and final reporting. The weekly responsibility image
covers the near-term report allocation, not the full remaining research/project deliverable.

## Recheck: report readiness versus unfinished technical work

S-20261117-10 / V-043 rechecked the stored results and the supplied requirements. The core
implementation, data pipeline, baseline predictions and preliminary comparison exist.
The November 18 deliverable does not prescribe a minimum sample size, a final validation
threshold, a held-out benchmark, repeated profiling or a trained gate by that date. An
honest preliminary report can use the current evidence and disclose unfinished work; this
is not a guarantee of a grade or a claim that every weekly item is complete.

The earlier handoff understated the remaining throughput definition/measurement and
qualitative error investigation. These are substantive analysis/measurement tasks. A new
GPU experiment is not automatically required by the progress-report wording: the existing
samples can yield a narrowly labeled forward-service rate. A claim about continuous-window
or end-to-end throughput, stable hardware performance, or warmed long-input latency needs
new instrumentation/controlled measurements and its approved scope. Do not substitute the
inverse median latency for measured throughput.

The recheck also separates accuracy at the provisional threshold from ranking quality.
INT8 classified one additional reference-labelled example correctly, while its ROC-AUC
was lower (0.9260 versus FP32's 0.9324). Keep that distinction and the large shared false-
negative count when describing the result. No model, data, threshold or prediction changed.

## Earlier P1-A report-preparation checklist

The evidence checkpoint below preserves the P1-A closeout, before the completed P1-B pilot above. Its missing-evidence column is historical.
The older progress text and demo farther below preserve earlier checkpoints; they must
not be copied as current state or as empirical model results.

| Required progress-report content | Verified evidence available | Evidence still needed for the report |
|---|---|---|
| Implementation status | Reusable input/audit components, offline evaluator and 85 passing tests at P1-A closeout; actual tokenizer/configuration execution on Explorer. See PHASE_RECORDS and V-034–V-038. | Describe the inference component and effective precision checks only to the extent actually implemented and executed. Distinguish passing software checks from completed experiments. |
| Data pipeline and baseline results | Pinned sources, complete 43,425-row audit, eligible development memberships, protected Test-A/Test-B allocation, raw-input preservation and actual token lengths. See DATA_REGISTRY and RES-001/RES-003. | Real frozen-classifier baseline predictions on a reproducible eligible development pilot; population support, preprocessing, threshold and run provenance. Synthetic fixture values do not fill this requirement. |
| Preliminary evaluation | A checked evaluator can calculate quality, paired disagreements and error changes from complete matched predictions. | Actual FP32/FP16/INT8 outputs and a regenerated comparison table; a bounded qualitative discussion of observed errors or edge cases. Include resources only when matched measurement evidence exists. |
| Lessons learned and remaining risks | Preserved Windows native-library failure and successful CPU-cluster route; explicit tokenizer/PAD/pooling concerns; protected evaluation roles and known provenance limits. | Explain what the pilot verifies or fails to verify, the remaining GPU/precision/pooling issues, and the next controlled benchmark and learned-gate work. Link failures and corrective actions to their records. |

The pilot is preliminary development evidence. A class/length-stratified training sample
does not estimate performance at the source population's prevalence or establish held-out
generalization. Any provisional 0.5 threshold, 1024-token cap or quantization configuration
must be identified as a pilot setting; it does not replace the main-protocol freeze or
FP32-validation threshold selection. The final benchmark and substantive learned-gate
investigation remain agreed project deliverables after this progress milestone.

Within four pages, prioritize a concise task/input/output example, the architecture and
implementation status, one source/population table, one real preliminary comparison table,
and lessons/risks with next actions. This is a suggested organization, not an additional
course template or a guarantee of a grade. If a real result is unavailable, describe its
actual blocker and incomplete requirement rather than substituting synthetic evidence.

The report should identify at least one relevant ethical risk and mitigation. For this
project, missed injections and over-reliance on a detector can expose a downstream system;
mitigations include reporting false negatives and limitations, treating detection as one
control, and keeping dataset instructions inert during experiments. Data leakage risk is
addressed by recorded source identities, protected evaluation roles and explicit exposure
limits. These are engineering safeguards and limitations, not a claim that deployment risk
or all contamination has been eliminated.

Individual contributions must reflect actual technical work and communication. Use
[CONTRIBUTIONS](CONTRIBUTIONS.md) and retained evidence; a planned responsibility does not
establish that its named owner performed completed work. The four-person weekly
responsibilities image is a near-term report work allocation, not the complete allocation
for the benchmark, learned gate and final submission.

## Earlier checkpoint - development input handoff and coordination

D-009 now permits continuation from verified artifacts without separate teammate
attestations; unknown exposure and unperformed human review remain accurately described.
The development input loader verified all 18,909 training and 1,000 validation examples
against original source bytes and approved identities, preserving raw strings and keeping
labels separate from internal inference inputs. It denies test roles before file reads and
exports only text-free records. The combined suite passes 66 tests (V-026), with independent
review in V-027. Native tokenizer/model execution remains blocked by Windows policy (V-025),
so no token-length or empirical precision/resource result is claimed. No teammate-specific
missing implementation is demonstrated to block this completed work.

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
preparation, not P1-A completion. Yash authorized publication of completed milestones; the reviewed implementation/audit
package was committed and pushed to the existing private repository as `e322f3f`.
STATUS/SESSION_LOG record the verified publication and handoff. The November 18
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

**Requirement source, verified November 17, 2026:** Yash supplied a screenshot titled
*CS 5130 Project Guidelines — Fall 2026*, filename
`Screenshot 2026-11-17 194815.png`, SHA-256
`df15c40f042f20f3064a0e4d00aedfb4f487925c05cd2959ac644fb89768c354`.
The image was visually inspected; the table and requirement summary below retain its
substantive requirements without depending on a private absolute file path. No public URL
or separate grading rubric was supplied. These verified limits supersede this document's
earlier unsupported one-page proposal, two-page final report, and 5–10-slide requirement.

| Deliverable | Due date in 2026 | Required contents or constraint |
|---|---|---|
| Team formation and topic selection | October 7 | One page: abstract and team members. |
| Proposal | October 21 | At most two pages: task/problem definition with business value, dataset description, and proposed system architecture and methodology. |
| Progress report | November 18 | At most four pages: implementation status; data pipeline and baseline results; preliminary evaluation; lessons learned and remaining risks. |
| Final submission | December 9 | Presentation of at most ten slides, report of at most five pages, code and references. |

The course emphasizes an engineering-focused AI/ML system: programming quality, data
processing, system design and evaluation. Describe the task's inputs/outputs with concrete
examples and its real-world relevance; dataset size, format and preprocessing; architecture,
data flow, modules and dependencies; representation and algorithm choices; and design
tradeoffs. Clean abstractions, readable modular code and reproducible pipelines support
that account. Evaluate both the baseline and proposed approach quantitatively and
qualitatively, including failure/edge cases, limitations and performance versus complexity.
Identify at least one ethical risk and a mitigation. Teams have two to four members, and
each member contributes both technically and in communication.

The supplied guidelines require code but do **not** state that the repository must be
public or owned by a particular team member. Public hosting must not be attributed to this
course source. Existing project commitments to a usable repository, README, implemented
Python modules, meaningful tests and reproducible evidence remain in force; any separately
agreed publication requirement is distinct from the verified course requirements. Report
the actual repository reference and access state without inventing a public URL.

The project's final report and presentation cover the exact project title and authors,
purpose, data, achieved benchmark and learned-gate results, implemented architecture and
method, measured quality/cost tradeoffs, limitations, actual contributions and references.
These content commitments derive from the agreed project scope and evidence packages
above; the course screenshot supplies the deadlines and maximum page/slide counts.

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

## Native development tokenizer result - November 17

R-P1-A-20261117-07 now executes the actual pinned tokenizer/configuration on an approved
Explorer CPU node. All 18,909 training and 1,000 validation inputs were checked, with no
model inference or official-test source. At cap 1024, 124 training rows (0.66%) and 8 validation
rows (0.80%) truncate; at 512 the corresponding counts are 965 (5.10%) and 52 (5.20%), and at 2048
they are 11 (0.06%) and 2 (0.20%). RES-003/V-034/V-035 retain complete definitions and evidence.
The wrapper's PAD/special-token/truncation behavior is now executed rather than inferred.
All 76 tests passed on Explorer; three earlier failed attempts are retained and explained.
No classifier quality, precision speedup, memory saving or final cap is claimed. The separate
D-011 official-test length administration subsequently completed with independent review
and 85 remote tests (V-037/V-038), supporting the P1-A closeout.
