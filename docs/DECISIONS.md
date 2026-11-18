# Project decision register

This register records the authority, rationale and lifecycle of project choices. It
separates approved scope from candidate methods and frozen experimental settings. The
current entries describe commitments and a working evaluation design; none establishes
experimental validation.

## Current decisions

| ID | Status / authority | Recorded decision | Governing detail |
|---|---|---|---|
| D-001 | User-approved project direction | Binary prompt-injection classification using Sentinel v2 and PromptShield. | Selected assets and scope in [README.md](../README.md). |
| D-002 | User-approved core study | Compare FP32 execution, FP16 execution and INT8 quantization of the same frozen checkpoint. | Treatment semantics and controlled comparisons in [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md). |
| D-003 | User-approved research priority | A learned selective higher-precision gate is a crucial, committed second research part requiring serious development, diagnosis and refinement. | Required research and evidence in [EXTENSION.md](EXTENSION.md). |
| D-004 | User-approved sequence | Complete Part 1, then develop Part 2, reusing valid functions and permitted results. | Phase dependencies and knowledge transfer in [ROADMAP.md](ROADMAP.md). |
| D-005 | User-approved working constraints | Preserve durable project context; support Windows, macOS and university-cluster work, with CUDA-dependent experiments on suitable cluster resources. Local setup/publication is not a prerequisite for independent useful work. | Session continuity and coordination in [AGENTS.md](../AGENTS.md); experimental comparability in RESEARCH_PROTOCOL. |
| D-006 | Sequential holdout design retained; concrete eligibility/allocation selected in D-008 | Designate disjoint Test-A for Part 1 and sealed Test-B for Part 2 before any Part 1 official-test model-performance inspection. | Group isolation, development-overlap exclusions and exposure rules in RESEARCH_PROTOCOL; identities and memberships in [DATA_REGISTRY.md](DATA_REGISTRY.md); construction in D-008/SPLIT-001 through SPLIT-004; test-release conditions remain; D-009 removes teammate-attestation waits and Q-013 retains exposure limits. |
| D-007 | Development conventions; not a confirmatory freeze | Shared evaluator interface and metric definitions. | Detailed record below; scientific review and real-run validity remain required. |
| D-008 | User-approved construction; test release pending | Exact 50/50 whole-group split and development eligibility. | Detailed record below; SPLIT-001 through SPLIT-004 / V-021; continuation amended by D-009. |
| D-009 | User-directed coordination amendment | Continue from verified artifacts without teammate-attestation waits; communicate overlap. | Detailed record below; no test-performance release or fabricated exposure history. |
| D-010 | User-approved CPU development route; completed | Bounded Explorer tokenizer/config audit with no test source/model/GPU. | R-P1-A-20261117-07 and V-034/V-035. |
| D-011 | User-approved aggregate official-test administration; completed | Total original token-length statistics/histogram only, no selection or performance release. | R-P1-A-20261117-08 and V-037/V-038. |
| D-012 | User-authorized progress-report pilot | Fixed 128 training examples and bounded same-GPU FP32/FP16/LLM.int8 feasibility execution. | Detailed conditions below; PILOT-001 and R-P1-B-20261117-01. No main-study freeze or test release. |

At adoption, D-006 proposed the sequential holdout design without a selected allocation.
D-008 now records Yash's concrete choice and SPLIT-001 through SPLIT-004 retain checked review-ready
memberships. D-009 now removes teammate-attestation waits; the required P1-C freeze still
precedes Test-A performance, and unknown exposure is reported as a limitation. Any necessary alternative requires a recorded rationale and the same honest
account of data exposure; an already exposed population cannot be made unseen by renaming
or repartitioning it.

### D-008 — Approved P1-A eligibility and 50/50 whole-group construction

- **Date/authority/status:** 2026-11-17, America/New_York; Yash explicitly approved the 50/50 proposal and requested review-ready manifests during S-20261117-05. Construction design selected; human scientific review and P1-A closeout remain pending. This is not the P1-C benchmark freeze or a release of test performance.
- **Inputs/evidence:** ASSET-001 pinned source and V-008/V-011; exact proposal in `docs/evidence/p1a-partition-candidates-20261117.json`. No model output influenced the choice. Prior team exposure remains incompletely declared (Q-013).
- **Eligibility:** Apply the existing protocol's test-overlap-first, then validation-precedence exclusions. Verified current data exclude no rows: retain all 18,909 train and 1,000 validation rows, preserving original IDs/text/labels. No extra normalization, relabeling or deduplication.
- **Allocation:** Within each reference class, order whole exact-text SHA-256 groups by `SHA256(namespace + ':' + label + ':' + raw_text_sha256)` (ascending hex), then raw-text hash as collision tie-break. Literal namespace is `precision-aware-inference:p1a-ab-candidate:v1:20261117`. Select the prefix minimizing `abs(2 * prefix_rows - class_rows)`; ties prefer fewer A rows. B is the complement. Preserve original test source order in outputs. Do not change the namespace because it contains the word `candidate`.
- **Support/construction:** Each side 11,758 rows, 8,515 benign and 3,243 injection; A/B groups 11,657/11,702. V-019/V-021 independently verify these counts, complete coverage, group integrity and development isolation in SPLIT-001 through SPLIT-004. All 71 duplicate groups stay intact. Human scientific review remains pending.
- **Rationale/options:** 50/50 preserves equal class support for both committed research parts and 649 more positive examples in B than the reviewed 60/40 candidate. This is not a power guarantee; endpoints/effect sizes remain unspecified. 60/40 support remains historical candidate evidence, not selected membership.
- **Exposure controls:** Administrative ID/label/group use only. Development uses training/validation role manifests. Test-A performance awaits P1-C; default no Test-B predictions before P2-E after P2-D freeze. Record exposure and enforce roles in future loaders; public source files are not cryptographically sealed. Unknown prior exposure cannot be relabeled none.
- **Review/reconsideration (continuation amended by D-009):** Inspect actual output evidence before scientific reliance. Separate teammate exposure declarations/human signoff are not routine wait conditions; retain unknown history as a limitation. Conflicting new provenance or exposure requires impact assessment before evaluation. Near-duplicate/template and pretrained-contamination limitations remain. No previous empirical results exist to invalidate; D-006's working design is made concrete without changing the sequential scope.

## Coordination amendment

### D-009 - Coordination without teammate-attestation waits

- **Date/authority:** November 17, 2026, America/New_York; Yash explicitly clarified that teammates perform delegated work and push to GitHub, that overlapping choices/completed work must be conveyed to affected teammates, and that independent work should not wait on their interpretations or exposure statements.
- **Operational choice:** Continue from verified code/artifacts and independent automated evidence review. Human review remains accurately unperformed where applicable, but is not a routine continuation gate. Ask teammates through a draft for Yash only when a concrete deliverable or shared decision requires coordination. Do not assign new commitments or claim their work occurred without evidence.
- **Development authorization:** The approved D-008 training/validation memberships and independent checks may support administrative input preflight and subsequent permitted development work under the roadmap without a separate teammate attestation. A new development-access record identifies this disposition; historical access manifests remain unchanged. This does not authorize an expensive pilot, choose tokenizer/pooling settings, close P1-A, or release Test-A/Test-B performance.
- **Validity boundary:** Unknown external exposure remains an explicit limitation, not a proven absence of exposure. Any discovered leakage, invalid artifact or failed check pauses the affected dependent claim/work until assessed. Existing test-release freezes, selected assets, precision treatments, frozen detector and sequential learned-gate scope are unchanged.
- **Records affected:** AGENTS coordination guidance; current STATUS/Q-013 and prior human-review continuation wording. D-008 membership bytes and prior scientific results are not changed or invalidated. Earlier records retain the then-pending human-review description; D-009 supersedes its use as an automatic wait condition.
- **Review/credit:** Automated review is not relabeled as human scientific signoff. Applicable course disclosure/review requirements are not invented or waived. Commit authorship still does not establish human implementation or review.

## Runtime-route approval

### D-010 - Approved Explorer CPU tokenizer audit route

- **Authority/date:** November 17, 2026, America/New_York; Yash explicitly approved copying the reviewed 8.4 MB package to his existing Explorer account and running the CPU-only audit after the Windows native-library block.
- **Approved scope:** R-P1-A-20261117-07; CS5130 allocation, courses partition, one task/two CPUs, 8 GiB memory and a 20-minute maximum. Verified tokenizer/configuration files, training/validation data, code and provenance only. No GPU, model tensor payload, official-test source/membership data or credentials in the package.
- **Execution conditions:** Fresh private scratch run directory, reviewed stage-03 content/hashes, isolated environment on a compute node using the available Python 3.13.5 module and pinned audit dependencies. Local-only/offline tokenizer calls; no Windows policy change. Preserve failed attempts and monitor actual submitted jobs to verified completion.
- **Limits:** This approves the alternate runtime and bounded audit, not a model pilot, final study cap/pooling rule, threshold, Test-A/Test-B release or a scientific phase closeout. Existing evidence/claim boundaries and D-009 coordination remain unchanged.

## Administrative scope approval

### D-011 - Approved aggregate official-test token-length administration

- **Authority/date:** November 17, 2026, America/New_York; Yash explicitly approved the prepared 6.4 MB official-test source/code package and aggregate-only Explorer audit to finish the all-split source-length requirement.
- **Scope:** R-P1-A-20261117-08; fixed pinned PromptShield official test, exact verified tokenizer/assets/environment, two CPUs/8 GiB/five-minute maximum, no installation or GPU. Compute only total original token-length statistics and a sparse total histogram, plus source/support/provenance checks. No prompts, row identities/hashes, real token vectors, cap comparisons, A/B breakdowns or classifier results are exported.
- **Boundary:** This administrative exception does not release Test-A/Test-B to inference or gate development. Existing development/inference test-role guards are unchanged. Test statistics must not select development settings; RES-003's cap 1024 pilot proposal was made from development evidence before any official-test token statistics.
- **Completion:** Full 23,516-row source/support coverage and independent aggregate/hash/runtime review are required before relying on the result or closing the remaining P1-A audit gate. Model loading/precision/pooling logits and the pilot remain separate P1-B work.

## Choice status vocabulary

| Status | Meaning |
|---|---|
| User-approved scope | A project goal or boundary; implementation details and empirical outcomes are not predetermined. |
| Candidate | A concrete option available for investigation on permitted development data. |
| Chosen for pilot | An operational choice subject to revision after diagnostic evidence. |
| Frozen for evaluation | The choice and dependencies were recorded before the designated evaluation; later changes require a documented amendment and impact assessment. |
| Superseded | A historical choice retained with its replacement and affected runs/results identified. |

Numerical settings and method candidates are defined in ROADMAP and the applicable protocol.
Their presence there does not make them user-mandated constants or measured optima.

## Decision record schema

### D-[next unique number] — [short decision]

- **Date / author / reviewer:** [actual values]
- **Phase and status:** [phase ID and status from the vocabulary above]
- **Question:** [specific choice being made]
- **Options considered:** [relevant alternatives and their tradeoffs]
- **Selected choice and rationale:** [why it serves the research question]
- **Evidence:** [source, validation, run or result IDs; inference distinguished from observation]
- **Data available when decided:** [splits and exposure-log reference]
- **Fixed parameters/artifacts:** [exact settings, memberships and hashes when available]
- **Consequences and limitations:** [accuracy, cost, comparability and reproducibility effects]
- **Earlier records affected:** [none, or IDs requiring rerun, reanalysis or retraction]
- **Reconsideration condition:** [new evidence or condition that would justify review]
- **Supersedes / superseded by:** [record IDs if applicable]

## Amendment record

### D-007 — Development evaluator interface and metric conventions

- **Date / author / reviewer:** 2026-11-11, America/New_York; Codex implementing Shreyas's authorized evaluation task; second-contributor review pending.
- **Phase/status:** P1-B/P1-C component preparation on synthetic data; chosen for development, not a main-protocol freeze.
- **Choice:** Standard-library offline package and CLI using the JSON/JSONL v1 contract in ARCHITECTURE. Keep expected labels separate from inference rows; join by stable IDs; reject incomplete/incompatible runs. This enables independent work before real inference outputs exist.
- **Metric conventions:** Injection is class 1; score >= shared threshold is positive. Undefined denominators return null, never a fabricated perfect score. F1 is `2TP/(2TP+FP+FN)` (and the corresponding class-0 expression); macro-F1 averages the two only when both are defined. AUC gives ties half credit. Brier is mean squared injection-score error. Development ECE uses ten equal-width bins, lower-inclusive/upper-exclusive except the final bin includes 1; empty bins contribute zero and retain null means/count zero.
- **Paired interpretation:** Corrected/introduced errors refer to candidate versus FP32; correctness comes from reference labels. Accuracy delta is candidate minus FP32 in percentage points.
- **Exposure/threshold:** Only synthetic fixtures were used. The fixture's 0.5 threshold is illustrative, not a selected project threshold. No real inputs, source revisions or data partitions were audited or frozen.
- **Evidence:** V-001 and S-20261111-01. Tests cover hand-computed metrics, all paired outcomes, tied AUC via an independent pairwise calculation, input integrity and CLI integration.
- **Limits/follow-up:** Keep Test-A/Test-B disabled until the required freeze and uncertainty implementation. No resource-cost claims or automatic threshold selection. Primary endpoint and final calibration/uncertainty choices remain Q-005/Q-006. Review formulas, label orientation and source contracts before real use.
- **Prior evidence affected:** None; no empirical results existed.

A replacement decision retains the original rationale and states why it changed, what
final outcomes were already visible, and which downstream evidence remains valid.
Post-evaluation choices have the exploratory/confirmatory status defined by
RESEARCH_PROTOCOL; extra checks do not erase earlier exposure. A superseded decision is
history, not an instruction to repeat the obsolete method.

## D-012 - Authorized progress-report pilot and execution conditions

- **Date/authority:** November 17, 2026. After the concrete P1-B proposal, Yash supplied the actual course requirements and explicitly requested completion of his inference/quantization deliverable for the November 18 progress report. This authorizes the bounded development pilot and necessary secure full-checkpoint retrieval, CPU environment preparation and Explorer GPU execution; no repeated approval is required for routine implementation/checks within this scope.
- **Population:** 128 eligible training examples, 64 per class; within each class select 48 with original length <=512, eight with 513-1024, and eight above 1024 by deterministic hash order in namespace `precision-aware-inference:p1b-pilot:v1:20261117`, retaining source order for execution. Exact membership and artifact hashes are recorded before model execution. Tail enrichment makes this a feasibility/diagnostic sample, not a representative performance estimate.
- **Common task:** Pinned Sentinel v2 and PromptShield revisions unchanged; cap 1024 from pre-test development evidence, right truncation, original unpadded batch one, no chat template or manual special-token insertion, model PAD remains unset. Eager attention, one matched compatible CUDA device, evaluation/inference mode and frozen classifier. Verify actual finite two-logit outputs and synthetic final-token/EOS pooling. Unsupported padded batching remains rejected, not silently altered.
- **Precision/score:** Strict FP32 with unintended AMP/TF32 disabled; FP16; bitsandbytes LLM.int8 with outlier threshold 6, score head excluded from conversion and FP16 residual parameters. Verify actual module/storage/dtype/device treatment. Compute both-logit softmax in FP32 and select verified injection index 1. Common pilot threshold 0.5 is provisional, never validation-selected or a final freeze.
- **Runtime/budget:** Separate reproducible CUDA environment, preserving the complete audit environment; CPU preparation up to 20 minutes on 2 CPUs/16 GiB, followed by one compatible GPU up to 20 minutes on 4 CPUs/32 GiB. Target A100 on Explorer; verify actual allocation/runtime before reliance. Pinned initial dependency selection: torch 2.9.1 CUDA 12.6, transformers 4.57.1, tokenizers 0.22.2, bitsandbytes 0.48.2, accelerate 1.11.0. Full package lock and executed backend evidence govern reuse. Preserve failures and stop dependent work on failed checks; a scheduler limit does not guarantee completion.
- **Completion:** All 128 intended IDs in each of three complete compatible prediction/run artifacts; checked effective precision/scoring/input identities, regenerated preliminary comparison, reproducible setup/commands and an evidence-based team handoff. Pilot resource observations are feasibility measurements, not the final matched repeated profiling study.
- **Boundaries:** No official-test model use, final cap/threshold/endpoint/uncertainty freeze, gate work, submission or messages. Existing publication authorization covers properly completed reviewed code/record milestones. Main study choices still require their predeclared decisions.

**Runtime selection follow-up:** The planned A100 target had a late scheduler estimate. Before model outcomes, the same bounded task used an available compatible NVIDIA L40S in the sharing partition. All three treatments ran on that one allocated device; job 11959388 completed within the original 20-minute GPU ceiling. This changes the runtime target, not the data, model, treatment or evaluation design.
