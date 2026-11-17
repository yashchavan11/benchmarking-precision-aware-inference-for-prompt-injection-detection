# Correctness and validity evidence

This log records the evidence supporting implementation correctness and research validity.
Development evaluator checks are recorded below. Planned checks and their expected outputs
do not count as performed validation.

Required properties come from the [research protocol](RESEARCH_PROTOCOL.md), the
[learned-gate checks](EXTENSION.md), the [artifact contracts](ARCHITECTURE.md), and each
[roadmap phase](ROADMAP.md). This log stores what was actually checked and what the evidence
establishes; it does not maintain a second copy of those requirements.

## Validation index

| Validation ID | Phase / target version | Property checked | Method / conditions | Outcome | Evidence / affected records | Reviewer |
|---|---|---|---|---|---|---|
| V-003 | Incoming `1d9f9ca` | Windows reproduction and calibration edges | Synthetic checks | Failed; preserved | outputs/review-20261117/; record below | Automated independent review; human signoff pending |
| V-004 | Local repaired incoming candidate | Portability and calibration repair | Fresh Git fixture checkout; independent arithmetic | Passed within scope | outputs/review-20261117/; record below | Automated independent review |
| V-005 | Main workspace at `1d9f9ca` plus local changes | Integration and combined suite | Python 3.11.9 / Windows | Passed: 26 tests | outputs/integration-20261117/ | Coordinating automated review |
| V-006 | Dataset audit-v2 | Counts, identities, groups and exclusion arithmetic | Direct-string independent recomputation | Passed within scope | dataset/independent-review-results.json under asset-audit output | Independent automated reviewer |
| V-007 | Initial dataset acquisition code | Reject altered unverified cache | Synthetic reproduction | Failed; preserved | dataset/independent-review-cache-probe.json | Independent automated reviewer |
| V-008 | Dataset audit-v3 and corrected acquisition | Administrative audit and cache integrity | Full identity/hash checks; 4,096 precedence cases; nine cache/parser checks | Passed within scope | docs/evidence/p1a-data-*.json; record below | Independent automated reviewer plus coordinating review |
| V-009 | Public pinned Sentinel metadata audit | Source identity/access and label-evidence sufficiency | HTTP outcomes, retained bytes/hashes, conservative parser tests | Inconclusive for full asset/label validity; access blocker verified | docs/evidence/p1a-model-metadata-20261117.json | Coordinating automated review |
| V-010 | Access recheck after user-reported acceptance | Availability to local Python process | Credential-presence check and pinned config HTTP request | Inconclusive for account access; local unauthenticated request returned 401 | docs/evidence/p1a-access-recheck-20261117.json | Local handoff verification |
| V-001 | P1-B/P1-C component preparation; source hashes in generated results.json | Metrics, pairing, artifact integrity and report generation | Python 3.13.3; synthetic fixtures; standard-library unittest | Passed: 18 tests | tests/; outputs/synthetic-demo/ (regenerable, ignored); S-20261111-01 | Second-contributor review pending |

### V-003 — Independent incoming-commit review, failures preserved

- **Performed by/date/phase:** Local automated metric and protocol reviewers at Yash's request; 2026-11-17, America/New_York. Independent software preparation/review; P1-A remains incomplete.
- **Target:** `df61690bbe90519599353add417ba746182fe5e3` and documentation follow-up `1d9f9ca4ef3752d56b04c662f4cac6b042feca4a`, compared with `ebc1f3f`. No production or held-out data.
- **Expected:** Existing 18 tests and documented demo succeed from a supported Windows checkout; calibration bins follow D-007 exactly.
- **Observed portability failure:** Python 3.11.9, Git 2.53.0.windows.2, existing system `core.autocrlf=true`. Fifteen tests passed; two errored and one failed on fixture SHA-256 mismatch. CLI returned 2. All eight committed JSON/JSONL fixtures had LF in Git and CRLF in the checkout; no attributes pinned bytes. The committed examples hash is `20e7be5333e2618c819a61fb6593cebbc55cb73d641cad837793196184a2e2aa`; checkout hash was `1022a165fb2cdb63a9904958f387bac84849bc35684e9886d8944c93ad320873`. Exact Git-blob LF snapshot passed all original tests and the demo on the same Python, isolating newline conversion as the cause.
- **Observed metric failure:** `int(score * 10)` placed `0.8999999999999999` in the bin starting at 0.9. With labels `[0,1]` and scores `[0.8999999999999999,0.9]`, observed ECE was approximately 0.4 instead of 0.5; bin-8/bin-9 counts were `[0,2]` instead of `[1,1]`. One of 29 exact/adjacent-edge probes failed. The new regression also failed before the correction; expected answers were not changed.
- **Other evidence:** Independent small-case checks passed for 18,720 metric cases and 4,680 paired comparisons. Documentation accurately distinguishes software evidence from real model findings. Phase-ledger wording is a minor coordination issue, not a completed-phase claim.
- **Retention/reproduction:** `outputs/review-20261117/capture_baseline.py`, `baseline-*.txt`, `baseline-results.json`, `upstream-lf/` (exact committed files), `metric-review-check.py`, `metric-review-boundaries-baseline.json`, and `boundary-regression-before-fix.txt`. Scripts use only local Git/files and synthetic fixtures; no dependency installation.
- **Impact:** V-001/V-002 remain historical evidence under their stated environments; they did not establish Windows portability or adjacent-float calibration behavior. The synthetic fixture's reported quality values are unaffected. No empirical run/result exists to invalidate. Future calibration outputs containing affected scores require regeneration with the correction.
- **Disposition:** The original review did not integrate or publish changes. Local correction and revalidation are V-004; subsequent authorized integration is V-005.

### V-004 — Local repair and independent revalidation

- **Target:** Local candidate modifies only `.gitattributes`, `precision_benchmark/evaluation.py`, and `tests/test_evaluation.py` for the implementation patch. Exact source/output hashes are in `outputs/review-20261117/candidate-results.json`.
- **Correction:** Pin LF for committed synthetic JSON/JSONL fixtures, retaining exact-byte hash checks and original hashes. Use explicit bin edges with `bisect_right`, preserving D-007's existing lower-inclusive convention. Add one regression test covering all nine boundaries, both adjacent floats, and the failing two-example ECE case. No scientific method or project setting was changed.
- **Procedure/outcome:** `python outputs/review-20261117/verify_candidate.py` freshly materialized all eight fixtures with Git and `core.autocrlf=true`; all bytes matched the original Git blobs. The existing 18 tests plus the new regression passed. Two CLI runs produced all five files byte-identically. `python outputs/review-20261117/metric-review-check.py outputs/review-20261117/metric-review-candidate-results.json` independently passed 18,720 metric cases, 4,680 paired comparisons and 29/29 edge probes; failing ECE became approximately 0.5.
- **Recovery note:** `git checkout-index --force` against already-materialized unchanged files did not rewrite their CRLF bytes. A fresh destination, then copying its verified bytes into this isolated checkout, completed revalidation. Adding attributes alone is not proof an old checkout's bytes were refreshed. Do not bypass checks or recalculate manifests to accept incidental newline conversion.
- **Evidence/review:** `outputs/review-20261117/candidate-results.json`, `candidate-tests.txt`, `candidate-demo-*.txt`, `metric-review-candidate-results.json`, `metric-review-candidate.md`, and `protocol-review.md`. Readable output: `outputs/review-candidate-demo-a/report.md`. Independent automated review is AI code review; human/team scientific signoff remains pending.
- **Limits:** Windows/Python 3.11.9 and synthetic data only in this session. No GPU/model execution, real eligibility/label audit, profiling, threshold selection, uncertainty implementation, or phase completion. No claims of error-free behavior outside the exercised scope.
- **Next:** Yash subsequently authorized local integration; see V-005. Reuse the evaluator for real development only after P1-A input/label/eligibility and treatment evidence are reviewed.

### V-001 — Development evaluator verification

- **Performed by/date:** Codex, at Shreyas's request; 2026-11-11, America/New_York.
- **Target:** `precision_benchmark/`, interface v1 (D-007); exact source hashes are retained in the generated `results.json`.
- **Executed:** `python3 -m unittest discover -s tests -v` — 18 tests passed on Python 3.13.3. `python3 -m precision_benchmark --manifest tests/fixtures/synthetic/comparison.json --output outputs/synthetic-demo` — exit 0; five output files generated. `git diff --check` — passed.
- **Independent arithmetic:** Six-example hand-calculated confusion matrix TN=2, FP=1, FN=1, TP=2 gives accuracy/macro-F1/AUC=2/3, FPR/FNR=1/3. Rank-based AUC agrees exactly with a pairwise reference over all 81 score assignments from {0, 0.5, 1} to two positives/two negatives. Floating-point hand calculations use unittest's default seven-decimal-place tolerance.
- **Edge checks:** Threshold equality; tied scores; endpoints/empty calibration bins; undefined metrics; single-class labels; empty/mismatched vectors; invalid labels and nonfinite/out-of-range/oversized scores. All four paired correctness outcomes are checked, including positive accuracy delta when the candidate corrects an FP32 error.
- **Integrity checks:** Missing/duplicate IDs, wrong reference labels/run IDs, incomplete runs, mismatched configuration and hashes, duplicate JSON keys, partial/inconsistent length metadata and held-out roles are rejected. Test-B rejection occurs before opening the examples file.
- **Integration checks:** Reordered prediction rows join correctly; two CLI runs yield byte-identical outputs under the same environment and invocation paths; report values match fixtures; existing output directories are preserved; CSV formula-like identifiers are escaped. The generated Markdown was inspected for labels, metric direction and unavailable-resource disclosure.
- **Evidence:** `tests/test_evaluation.py`, `tests/test_artifacts.py`, `tests/test_report.py`, `tests/fixtures/synthetic/`; README contains regeneration commands. Source and input SHA-256 values are emitted with each report.
- **Limits:** No real dataset or checkpoint, GPU execution, threshold selection, confidence intervals, or profiling was checked. Python versions other than 3.13.3 were not executed. Consistent metadata is not independent verification of the declarations. This is software evidence, not a completed P1-A/B/C phase or empirical finding.
- **Review:** A second contributor still needs to review scientific formulas, conventions, eligibility and real-run evidence under AGENTS.md. No human review is claimed.

### V-002 — November 16 demonstration and documentation verification

- **Performed by/date:** Codex at Shreyas's request; 2026-11-16, America/New_York.
- **Target:** Unchanged evaluator and fixtures from commit `df61690`; documentation preparation for the November 18 checkpoint.
- **Executed:** `python3 -m unittest discover -s tests -v` — all 18 tests passed. `python3 -m precision_benchmark --manifest tests/fixtures/synthetic/comparison.json --output outputs/synthetic-demo-20261116` — exit 0.
- **Observed:** Quality CSV reports 4/8 correct for FP32/FP16 fixtures and 6/8 for INT8. FP16 paired counts are two in each correctness category, with four disagreements and zero net accuracy change. INT8 has four corrected and two introduced errors, or +25 percentage points. Error rows confirm the example explanations in REPORTING.
- **Artifacts:** The five generated outputs are in `outputs/synthetic-demo-20261116/` (ignored, regenerable). `results.json` retains input/source hashes; fixtures remain tracked. These values are synthetic software demonstrations, not empirical model findings.
- **Scope:** Reconfirmed existing software behavior and prepared explanations. No real data, model execution, human review or hardware measurements. No implementation change or research-phase completion.

IDs have the form `V-[unique number]`. Outcomes are `passed`, `failed` or `inconclusive`.

### V-005 — Authorized local integration and combined checks

- **Date/target:** 2026-11-17; original main fast-forwarded from `ebc1f3f` to the already-reviewed `1d9f9ca` after Yash's explicit approval. Applied the reviewed portability/bin-boundary patch; no new commit or remote write.
- **Checks/outcome:** Fresh fixture materialization with `core.autocrlf=true` matched committed Git bytes. Original evaluator plus regression: 19 tests passed; demo generated all five outputs. After adding the administrative audit components, `python -m unittest discover -s tests -v` passed all 26 tests on Python 3.11.9 / Windows. Exact source/test hashes and complete logs are in `outputs/integration-20261117/all-tests-source-manifest.json` and `all-tests-after-audits.txt`; initial integration evidence is `verification.json`, `tests.txt`, and `demo/`.
- **Scope:** Correct local integration, synthetic arithmetic/artifact behavior and administrative audit validation. No actual model treatments, GPU kernels, tokenization, measured resource benefit or completed phase is established. Fixture contents/hashes and expected arithmetic were preserved.
- **Final artifact QA:** An initial documentation check detected CRLF in a copied compact review JSON snapshot. Normalized only the document snapshots to LF, verified unchanged parsed JSON values, and preserved original audit outputs. Final local links, JSON parsing/LF, tested source/test hashes, empty staging area and `git diff --check` passed; evidence is `outputs/integration-20261117/final-checks.json`.

### V-006 — Initial administrative data audit independently checked

- **Target/purpose:** ASSET-001 at pinned dataset revision; audit-v2 computes official-source statistics and protocol overlap projections, not a partition freeze.
- **Method/outcome:** Independent implementation compared original strings directly rather than reusing the audit's group hash calculations; verified every one of 43,425 identities, class/group/duplicate/conflict/length counts, raw/output hashes and projected memberships. Exhaustively checked 4,096 small synthetic exclusion-precedence arrangements. No arithmetic discrepancy found.
- **Evidence:** `outputs/asset-audit-20261117/dataset/independent-review-results.json`, its check script and `independent-review.md`; source snapshots retained. Tokenizer lengths, content-level label truth, near duplicates and prior exposure remain unverified.
- **Qualification:** Review also exposed a reusable cache-integrity weakness (V-007), corrected and revalidated in V-008. Current source downloads were not shown corrupted; earlier evidence is retained rather than silently discarded.

### V-007 — Unverified source cache accepted before repair

- **Expected:** Reusing pinned input files must detect changed bytes or missing provenance rather than assign arbitrary cached content to the requested source revision.
- **Observed:** A synthetic one-row cache with a plausible selected-source metadata ID/revision was accepted by the original acquisition routine without network access or an earlier integrity record. No real source file was modified in the reproduction.
- **Cause/evidence:** The routine skipped retrieval for existing files and generated new hashes without validating their origin. Reproduction and result are preserved as `outputs/asset-audit-20261117/dataset/independent-review-cache-probe.py` and `.json`.
- **Impact:** Future cache reuse could silently misidentify inputs. This finding does not establish that the actual original pinned downloads were wrong. Their retained hashes/counts remain checkable. Corrective action and final reusable code are V-008.

### V-008 — Final dataset audit and cache repair verified

- **Target:** `precision_benchmark/data_audit.py` SHA-256 `78abd494a4e4c913e82c68a4a3a7b58a500c467317e044fbb68369a779d4b5c6`; audit-v3, ASSET-001. `tests/test_data_audit.py` has four passing tests.
- **Correction:** Create a dataset/revision-bound source-integrity receipt after verified acquisition. Reuse checks all five retained source hashes. Existing unverified caches require explicit earlier provenance or a fresh pinned-byte comparison. Altered files are rejected and preserved; source duplicate JSON keys are rejected. Current receipt was bootstrapped from the retained verified prior audit provenance; original raw bytes were not changed.
- **Independent outcome:** Full 43,425-identity/direct-string aggregate and 4,096-case precedence verification passed again. Nine cache/parser checks passed: unverified-cache rejection, tampering of each of five files, wrong receipt revision, duplicate keys, and matching receipt acceptance. No network or real-file edits were used by those mutation checks.
- **Evidence:** Compact [aggregate review](evidence/p1a-data-review-20261117.json), [cache review](evidence/p1a-data-cache-review-20261117.json), [summary](evidence/p1a-data-summary-20261117.json), and [provenance](evidence/p1a-data-provenance-20261117.json). Full sources/check scripts/logs, versions v1/v2/v3, and identity manifests remain under `outputs/asset-audit-20261117/dataset/`; `execution.json` and `AUDIT_NOTES.md` give exact invocations and scope.
- **Limits/follow-up:** Administrative evidence only. EXP-002 documents incidental training-viewer exposure and exact-text propagation checks. Human scientific review, final eligibility/A-B grouping/access controls, token lengths, and model-label mapping remain pending. No holdout assignment or performance-guided choice occurred.

### V-010 — Account acceptance reported; local authentication still missing

- **Date/trigger:** 2026-11-17; Yash reports that he has agreed to the selected model's access requirements.
- **Observed:** No credential present in checked environment variables or standard/configured Hub token paths. A fresh request for `config.json` at the existing pinned model revision was therefore unauthenticated and returned HTTP 401. This does not test whether the approved account would succeed when authenticated.
- **Evidence:** [Safe access record](evidence/p1a-access-recheck-20261117.json); failure response retained at `outputs/handoff-20261117/config-access-response.txt` with its hash. No secret was printed or written to project files.
- **Continuation:** Establish authenticated local read access or an approved browser path; preserve Yash's acceptance statement and do not repeat the terms question without contrary evidence. Actual config/head/tokenizer validation remains pending; no weights or model outputs were accessed.

### V-009 — Public model metadata verified; private configuration unavailable

- **Target/method:** ASSET-002; `python -m precision_benchmark.model_audit --output outputs/asset-audit-20261117/model`. Resolved then re-queried the immutable selected-model revision; retained response bytes, statuses, timestamps, headers and SHA-256 values.
- **Observed:** Public API/card/license accessible; four pinned configuration/tokenizer requests returned 401. Eight response hashes and the source-code hash were independently verified in `root-independent-review.json`. Three unit tests validate immutable exact-repository identity and prevent API metadata/gated files from implying verified label orientation or runtime state.
- **Outcome/limits:** Public source identity/access condition established, full model/tokenizer audit inconclusive. Head shape, injection index, pooling, precision behavior and even actual successful checkpoint loading remain unverified. API F16/count metadata is provider declaration, not execution evidence. No credentials, weights or model predictions used; failure-body files are not usable configs.
- **Continuation:** Q-012 requires authorized access before fetching pinned configs. Do not substitute a base-model config, assume class index 1, accept license terms for the user, or call the empirical pipeline complete. Exact sources and outcomes are in [metadata summary](evidence/p1a-model-metadata-20261117.json).

A pass applies to the stated property and conditions, not automatically to other data,
backends, scales or measurement claims.

## Validation record template

### V-[number] — [check]

- **Performed by / date / phase:** [actual values]
- **Target and version:** [data manifest, metric implementation, model path, gate, run or report]
- **Property and source requirement:** [precise expected behavior and protocol/roadmap reference]
- **Method:** [independent reference, known-answer fixture, invariance check, audit,
  integration comparison or repeatability test]
- **Inputs and permitted split:** [fixture or audited input identity, exposure state and relevant grouping]
- **Conditions:** [implementation/backend, configuration and scale actually exercised]
- **Expected outcome and tolerance:** [chosen before comparing outputs, with rationale]
- **Observed outcome:** [actual values and passed / failed / inconclusive status]
- **Evidence location and integrity:** [artifact/hash or exact reproducible procedure]
- **What this establishes:** [scope of the evidence]
- **What it does not establish:** [unverified backend/scale, statistical assumption or missing system cost]
- **Affected runs/results:** [IDs, invalidation implications or none]
- **Failure/inconclusive diagnosis:** [smallest reproduction, confirmed cause versus hypothesis,
  correction attempted and unresolved concern; not applicable if passed]
- **Revalidation relationship:** [earlier failed check, corrected target version and new check ID]
- **Follow-up and owner:** [fix, investigation, repeat, review or complete]
- **Review evidence:** [actual reviewer and assessment, or pending]

A corrected implementation receives new validation evidence; the earlier failed record
remains available so its effect on dependent results can be traced.
