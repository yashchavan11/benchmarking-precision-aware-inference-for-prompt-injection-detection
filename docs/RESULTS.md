# Findings and claim register

Administrative findings and the completed training-only P1-B precision/resource pilot
are recorded below. Confirmatory quality, repeated profiling and gate findings remain
pending. This register stores conclusions and their evidence;
[REPORTING.md](REPORTING.md) defines how they become tables, figures and final deliverables.
Statistical and measurement definitions belong to [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md),
and the gate's separate quality/cost claims belong to [EXTENSION.md](EXTENSION.md).

## Result index

| Result ID | Part / phase | Question or claim | Evidence type / population | Supporting runs / validation | Status / reviewer |
|---|---|---|---|---|---|
| RES-001 | Part 1 / P1-A | Pinned source supports an exact-duplicate-aware evaluation design | Development observation: administrative source audit, no classifier | R-P1-A-20261117-01; V-006/V-008; ASSET-001 | Observed and independently checked by automated review; human signoff pending |
| RES-002 | Part 1 / P1-A | Padding/pooling policies require explicit checks | Static source and synthetic index cases | R-P1-A-20261117-04; V-016/V-022 | Source-level observation; original batch-one runtime checks later verified by V-041; padded equivalence unsupported |
| RES-003 | P1-A | Native development lengths and tokenizer controls | Complete administrative development observation | R-P1-A-20261117-07; V-034/V-035 | Independently checked; no model/cap freeze |
| RES-004 | Part 1 / P1-B | Three precision treatments execute with mixed quality/resource observations | Class/length-enriched 128-row training pilot, provisional threshold | R-P1-B-20261117-01; V-041/V-042 | Native and arithmetic evidence independently checked; no final ranking or gate benefit |

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

### RES-003 - Native development lengths and explicit tokenizer controls

- **Evidence/status:** Administrative development observation from complete R-P1-A-20261117-07, independently checked by V-034/V-035; not a classifier quality/resource result. Exact versions, input/asset/output hashes are in the native summary and registry.
- **Original lengths:** Training n=18,909, median 70, p95=523, p99=916, maximum 6412. Validation n=1000, median 68.5, p95=519, p99=894, maximum 2580. p95/p99 use nearest rank; median is conventional. All rows are below the model's declared 40960-position value; this is not a measured runtime capacity limit.

| Candidate cap | Training truncated / 18,909 | Validation truncated / 1,000 |
|---|---:|---:|
| 512 | 965 (5.10%) | 52 (5.20%) |
| 1024 | 124 (0.66%) | 8 (0.80%) |
| 2048 | 11 (0.06%) | 2 (0.20%) |

- **Tokenizer controls observed:** Initial backend PAD ID 151643 and cap 5000 are overridden/disabled by explicit wrapper calls; wrapper padding uses PAD/EOS ID 151645. All tested added-token flags agree with source; no automatic boundary tokens are appended. Unequal padded synthetic content matches the unpadded token sequences after masking. Every development capped sequence matches its original right prefix.
- **Pooling limit:** The integer stock PAD=EOS rule disagrees with last-visible-token selection on relevant synthetic EOS cases, but there were zero such index disagreements in these development sequences at the measured caps. This is not model-logit batching equivalence and does not rule out other inputs.
- **Proposal made before any official-test token-length audit:** Start the later 128-example pilot at cap 1024, original unpadded batch one, based on development retention above. This preserves more development text than512 while leaving2048 as a justified sensitivity/feasibility option. No model quality, speed or memory advantage is inferred, and no cap/pooling/threshold freeze is made by this proposal.
- **Later completion:** Official-test token lengths were deliberately outside D-010's package, then separately authorized in D-011 and completed in R-P1-A-20261117-08. No held-out cap comparisons or development selection occurred. P1-A is now closed; model loading, logits, effective precision and the pilot belong to P1-B. The development-derived proposal above remains unchanged.

### RES-004 - Three-treatment development feasibility, not a held-out ranking

**Evidence:** D-012 / PILOT-001, R-P1-B-20261117-01 and V-040 through V-042.
The [portable evidence bundle](evidence/p1b-pilot-20261117/comparison.json) retains all
384 predictions, two-logit scores, actual precision/environment checks and a regenerated
[quality table](evidence/p1b-pilot-20261117/analysis/quality.csv),
[paired table](evidence/p1b-pilot-20261117/analysis/paired.csv) and
[error analysis](evidence/p1b-pilot-20261117/analysis/error_analysis.csv).

All three treatments completed the same 128 training examples on one NVIDIA L40S:
64 benign/64 injection, deliberately enriched for longer inputs, with 16 truncated at
1,024 tokens. Batch size is one without padding, and the predeclared pilot threshold is
0.5. These choices and membership preceded model outputs. FP32 upcasts the released F16
checkpoint; it does not reconstruct a more precise original checkpoint. The observed
parameter/module treatment matches the requested modes: FP32, FP16, and 196 actual
LLM.int8 transformer projections with a floating FP16 classifier head/residual parameters.

| Treatment | Correct / 128 | Accuracy | Macro-F1 | Injection recall / 64 | False positives / 64 | False negatives / 64 |
|---|---:|---:|---:|---:|---:|---:|
| FP32 | 97 | 75.78% | 0.7447 | 53.13% | 1 | 30 |
| FP16 | 97 | 75.78% | 0.7447 | 53.13% | 1 | 30 |
| INT8 | 98 | 76.56% | 0.7538 | 54.69% | 1 | 29 |

FP16 made identical classifications to FP32, although scores and AUC were not identical.
INT8 differed on one example, correcting an FP32 false negative without introducing another
error in this sample. The changed example is original training row 3949, 288 tokens with no
truncation: its injection score moved from 0.49147448 to 0.51865286 across the fixed 0.5 threshold.
This is a concrete threshold-boundary observation; one example does not establish INT8
superiority. Higher precision is not ground truth, and these pilot outcomes provide no
observed example of a lower-precision error that FP32 would correct. They do not establish
learned-gate headroom or justify dropping the committed gate investigation.

Most errors were shared missed injections. FP32's 30 false negatives include 27 untruncated
and three truncated examples; therefore truncation is not a complete explanation for the
observed misses. This is descriptive error accounting, not causal evidence about the cap.
The preliminary operating point needs the planned validation-only threshold procedure;
we did not tune the threshold on this pilot to improve its reported result. Source-text
interpretation, annotation ambiguities and broader failure-case analysis remain later work.

#### Pilot resource observations

| Treatment | Median forward time (ms) | p95 forward time (ms) | Peak PyTorch allocated memory (MiB) |
|---|---:|---:|---:|
| FP32 | 25.51 | 59.68 | 2482.78 |
| FP16 | 26.27 | 27.00 | 1321.42 |
| INT8 | 87.49 | 93.48 | 932.56 |

These are raw descriptive observations from one forward sample per selected example,
three warm-up inputs, fresh processes and fixed FP32/FP16/INT8 order in the same allocation.
Timing covers pretokenized device-resident input through synchronized raw logits; it
excludes tokenization, transfers, score conversion, file writes and process imports.
PyTorch memory peaks were reset after warmup; they are not total device/host/residency
costs. [Per-treatment feasibility files](evidence/p1b-pilot-20261117/runs/int8/feasibility.json)
retain every raw sample, loading scope, memory baseline and limits.

INT8 showed lower measured allocated memory and a slower median forward time in this
pilot. No latency improvement is observed here; this is not a final speed ranking or a
reasoned diagnosis of the slowdown. Repeated, shape-aware, order-controlled profiling and
end-to-end boundaries remain required before broader cost claims. Shared-cluster conditions
and the deliberately unusual length mix further limit interpretation.

**Limits/next evidence:** Training-only, small class/length-stratified sample; no uncertainty
claim or representative prevalence; provisional threshold and cap; unknown pretrained
contamination and near-duplicate dependence. No official-test predictions were produced.
The main comparison requires P1-C decisions and FP32 validation threshold selection before
Test-A. Complete Part 1 before substantive learned-gate development and eventual frozen
Test-B comparison. Existing P1-A inputs/partitions remain unchanged and valid within their
recorded limits.


### RES-004 follow-up - Fresh recheck and narrower resource interpretation

S-20261117-10 / V-043 independently rechecks the unchanged retained pilot. The accuracy
advantage is exactly one reference-labelled injection: training row 3949 has scores
FP32=0.4914744794, FP16=0.4914864302, INT8=0.5186528563 at threshold 0.5. The corresponding
logit margins are -0.0341053754, -0.0340576172, +0.0746459961. Numerical changes can move a
borderline prediction in either direction; greater arithmetic precision does not guarantee
agreement with the reference label. No mechanism such as beneficial regularization has
been established. INT8's AUC is 0.926025390625 versus FP32's 0.932373046875, so the small
thresholded-accuracy gain is not an across-metric improvement.

A timing recheck identifies the exact three warmup lengths: 63, 92, 12 tokens in every mode.
The longer shapes were not explicitly warmed. All raw samples are retained, including an
FP16 maximum of 493.0451 ms at 712 tokens and an INT8 maximum of 264.0951 ms at 1024 tokens.
Their causes and repeatability are unknown. The existing medians/p95 remain correct
single-pass descriptions; they do not establish a fully warmed stable benchmark. Memory
peaks span the post-warm-up GPU workload including input/score allocations, while the
forward timer excludes transfers and score conversion. These are different boundaries.

For completeness, a derived forward-only service rate can be calculated as 128 divided
by the sum of the 128 recorded forward durations: 31.6177 FP32, 31.1950 FP16 and 11.1842 INT8
examples per forward-second. This is not a measured continuous wall-window or end-to-end
pipeline throughput. The calculation uses the sum of durations, not the median; it adds
no new native execution or proof of a sustained rate. The compact recheck evidence retains
source hashes and the formula. Qualitative prompt-level failure investigation and fuller
profiling remain unfinished; final threshold and protected evaluations remain unchanged.
