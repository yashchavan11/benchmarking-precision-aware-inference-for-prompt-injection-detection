# Current project state and handoff

PR #1 follow-up (November 18): preparation source inventory now includes the shared
preprocessing module, with a fail-before/pass-after regression check. See VALIDATION_LOG's
PR-1 entry and Git history for publication state. Scientific pilot status below is unchanged.

## Current snapshot - P1-B complete; progress-report inference deliverable ready

| Field | Current value |
|---|---|
| Provenance/phase | November 17, 2026, America/New_York; S-20261117-10 recheck. P1-A and bounded batch-one P1-B remain closed; next P1-C. |
| Completion evidence | PHASE_RECORDS P1-B closeout; D-012; PILOT-001; V-039 through V-042; RES-004. Complete finite FP32/FP16/INT8 predictions for the same 128 training IDs. |
| Ownership/jobs | S-20261117-10 complete. Fresh arithmetic, source/code/measurement and report-gap assessments are incorporated in V-043. No active reservations, new GPU job, data selection, threshold change or teammate dependency. |
| Repository | Reviewed P1-B milestone `3f20b824aec92d60cf43a28aa9446a9830f48872` was pushed to origin/main and its remote SHA verified, using configured Yash author/committer identity. See Git history for the latest handoff tip and `outputs/pilot-20261117/publication.json` for the final local receipt. No comments, PRs, issues, teammate messages, submissions or visibility changes were made. |
| Inputs | Pinned dataset/model revisions and D-008 populations unchanged. Full checkpoint now retrieved and hashed. D-012 uses original unpadded batch 1, cap 1024, provisional threshold 0.5; these are not a main-study freeze. |
| Native evidence | CPU setup 11959175 completed 0:0 in 10m24s. GPU 11959388 completed 0:0 in 11m59s on one L40S/d4046. 107 software tests passed on the GPU node before execution; 111 final local tests include four later offline-only assembly checks. |
| Observed findings | FP32/FP16 each 97/128 correct; INT8 98/128 with one corrected error and none introduced. Shared false negatives remain; INT8 AUC is lower despite its one-example accuracy gain. INT8 used less measured allocated memory and had a slower pilot median forward time. V-043 confirms the values and identifies short-only warmups/spikes; see RES-004 for scope. |
| Scientific boundaries | Training-only enriched pilot, provisional operating point and single-pass resource observations. No representative/generalization, statistical superiority, final speedup or learned-gate benefit claim. No Test-A/Test-B predictions or performance release. |
| Runtime | Verified Explorer CUDA environment and full checkpoint are reusable; preserve the separate audit environment and Windows security policy. Exact package lock, source archive and hardware evidence are retained. |
| Reporting | Actual guideline screenshot recorded in REPORTING: November 18 progress report <=4 pages; implementation, pipeline/baseline, preliminary evaluation, lessons/risks. Ready-to-use inference prose/tables and remaining team actions are linked there. No submission made. |

## Required continuation and reusable artifacts

**November 18 report follow-up (S-20261118-01):** Shreyas's fillable PDF sections are prepared
at `../output/pdf/CS5130_Progress_Report_Shreyas_Filled.pdf`. Three source-checked qualitative
development cases are now recorded in RES-005/EXP-009; human review remains pending.
This completes a bounded investigation, not all possible failure analysis. The prior
November 17 handoff below is historical where it says no prompt-level investigation exists.
Team sections and final report assembly remain unfinished. No inference setting changed.

Read the P1-B closeout, D-012, PILOT-001, RES-004 including its recheck follow-up, V-039 through V-043 and REPORTING before
continuing. The [portable team bundle](evidence/p1b-pilot-20261117/comparison.json) includes
all 384 predictions, reference IDs/labels/lengths, native precision/pooling evidence, package
provenance, raw feasibility samples, complete analysis and the exact executed code package.
It supports offline reanalysis without weights, raw data, credentials or GPU access. USAGE
contains reproducible inference and analysis commands. Bundle integrity must survive Git
checkout; its exact bytes are protected by .gitattributes and the bundle inventory.

Ignored original artifacts remain under `outputs/pilot-20261117/`: preparation-01,
checkpoint-01, environment-01, stages 01/02, attempt-01, analysis-01 and review. Earlier audit
failures, superseded packages and the detached sibling review checkout remain preserved.
No native pilot attempt failed; pre-execution hardening and the unused first stage are
retained without implying they generated model results.

Reusable Explorer references (not the sole durable evidence):
- Inference environment: `/scratch/chavan.yas/precision-aware-inference/pilot-env-20261117-01/inference-env`.
- Full checkpoint/config: `/scratch/chavan.yas/precision-aware-inference/pilot-checkpoint-20261117-01/`.
- Completed run: `/scratch/chavan.yas/precision-aware-inference/pilot-run-20261117-01/project/`.
- Tokenizer and eligible training sources/partitions remain in tokenizer-audit runroot04;
  prior complete CPU audit environment remains in runroot03. Exact identities are registered
  in DATA_REGISTRY and the execution record. Verify access/hash compatibility before reuse;
  do not reinstall/redownload merely because the conversation or checkout changes.

| Order | Next bounded task | Recognizable completion condition |
|---|---|---|
| 1 | Use the corrected report-gap assessment: add bounded qualitative development-error investigation and explicitly scoped resource reporting, then assemble the progress report. | At most four pages covering the rubric and actual contributions. Existing samples permit a narrow derived forward-service rate; sustained/end-to-end throughput and shape-aware repeated profiling require additional approved measurements. No new GPU experiment is mandated merely by the progress-report wording. Submission still needs explicit instruction. |
| 2 | Prepare P1-C main-study decision packet. | Concrete endpoint, validation-threshold objective/search/tie rule, preprocessing/batch/quantization policy, paired uncertainty, profiling matrix/repetitions and budget for Yash's approval before substantive execution. |
| 3 | After those choices, implement/check analysis and perform approved validation selection; freeze the Part 1 plan before Test-A. | Full traceable freeze and compatible development evidence. Complete Part 1 before the committed learned-gate study and final Test-B release. |

The fresh recheck is [V-043 evidence](evidence/p1b-recheck-20261117.json), with an independent
verifier retained beside it. Original bundle bytes and predictions remain unchanged; no
arithmetic/hash mismatch was found. The prior handoff understated throughput scope and
prompt-level qualitative analysis: these are substantive unfinished tasks, not only table
assembly. Forward timer exclusions do not define the wider post-warm-up memory window.
The final threshold, Test-A study and learned gate remain later work, not automatically
required to finish the November 18 preliminary report.

No further scientific experiment is silently authorized by completing the report pilot.
Unknown prior external exposure, annotation truth, near-duplicates and pretrained
contamination remain disclosed limits. Automated reviews are not human signoff. No effective
context-window claim is made.

## Continuation fields for subsequent snapshots

The current snapshot and immediate continuation above are replaced as work advances.
These field definitions supply the additional detail needed when actual artifacts and
execution exist; they are not completed work records.

| Field | Information needed for a reliable continuation |
|---|---|
| Snapshot provenance | Preparer, actual date/timezone, phase and session ID. |
| Changes since prior snapshot | Brief changes with links to the chronological session entry and affected decisions/evidence. |
| Reusable artifacts | Durable location, version/hash where relevant, compatible configuration, data membership and exposure status. |
| Ownership and reserved work | Owner, bounded task, affected files/interfaces and other contributors' work to preserve. |
| Partial edits and jobs | Actual system and process/job IDs; queued/running/interrupted state; saved checkpoint; output/log references; safe verification or resume action. |
| Uncertainty | Verified blockers separately from open hypotheses, with question IDs and the next useful investigation. |
| Next actions | Ordered bounded tasks, normally up to three, with the specific records/artifacts they depend on. |
| Required checks and review boundary | What must be verified, which downstream action depends on it, and what evidence establishes completion. |
| Next-phase transfer | The preceding phase closeout and its reusable outputs, limitations, invalidated evidence and required follow-up. |
