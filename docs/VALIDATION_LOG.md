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
| V-011 | Preserved handoff artifacts | 77 local integrity checks and unselected allocation support | No model execution | Passed within scope | p1a-retained-verification / partition-candidates evidence | Independent automated reviewer |
| V-012 | Pinned model config via browser | Granted access, retained bytes and configured label orientation | Authenticated Chrome; local hashing | Partial contract verified; tokenizer incomplete | p1a-browser-config evidence | Coordinating plus independent artifact review |
| V-013 | Initial auth implementation | Mock security/compatibility checks | 34 tests | Tests passed; later redirect-parser defect found | Initial manifest and V-014 failure | Independent automated review |
| V-014 | Corrected auth implementation | Redirect exception redaction and integration | Failing regression then 35 passing tests | Passed within exercised scope | p1a-auth-revalidation evidence | Focused independent recheck passed |
| V-015 | Browser tokenizer configs | File hashes and JSON mapping consistency | Passed for retained files | Tokenizer runtime unverified | p1a-tokenizer-configs/consistency evidence | Coordinating review |
| V-016 | Pinned Transformers source | Head/pooling/default semantics | Static review + seven integer cases | Passed within source scope | p1a-library-contract/sources/pooling-cases | Independent automated reviewer |
| V-017 | Audit environment | Installation/import readiness | pip check; actual import | Native runtime blocked by Application Control | p1a-runtime-blockers/environment | Coordinating observation |
| V-018 | Initial D-008 builder | Actual construction and synthetic cases | 41 tests; administrative outputs | Actual memberships complete; later reuse flaw | p1a-partitions-v1 | Automated implementation |
| V-019 | Initial actual memberships | Full IDs, method, isolation, hashes | Independent checker | Passed for approved source | p1a-partition-review-v1 | Independent automated reviewer |
| V-020 | Original builder reuse | D-008 revision authority | Synthetic alternate revision | Failed; preserved | p1a-partition-guard-failure | Independent reproduction |
| V-021 | Corrected builder | Revision rejection and membership compatibility | Failing regression repaired; 42 tests | Passed; population bytes unchanged | p1a-partition-guard-review/revalidation | Independent automated recheck |
| V-022 | Authenticated selected assets | Seven files and actual header | Bounded retrieval + independent parsing/hashes | Complete source/header audit; no model execution | p1a-authenticated-contract/asset-contract-review | Independent automated reviewer |
| V-023 | Integrated commands | Synthetic/mock suite and source identity | 56 tests + focused independent review | Passed within exercised scope | p1a-integrated-software | Independent automated code review |
| V-024 | NFC/delimiter probe | Administrative normalization collision support | Python UCD14 on pinned sources | No new collisions; not tokenization | p1a-normalization-probe | Coordinating automated probe |
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

### V-011 — Resumed evidence integrity and allocation-support review

- **Date/scope:** 2026-11-17, America/New_York; independent automated review during S-20261117-04, not human scientific signoff.
- **Observed:** 77 retained-evidence checks passed. Original seven package/five test hashes matched V-005 before this session's authentication edits; all five dataset source hashes, five audit-output hashes, receipt, 43,425 text-free identities/aggregates, eight original model responses, and V-010 response matched preserved evidence. No full dataset download or expensive experiment was repeated.
- **Evidence:** [retained verification](evidence/p1a-retained-verification-20261117.json); reproducible `outputs/resume-20261117/review/verify_retained.py` and `review.md`. Historical 26 tests were reused, not rerun at this point; new auth code is covered separately by V-013.
- **Candidate support:** [unselected allocation candidates](evidence/p1a-partition-candidates-20261117.json) evaluates one declared hash ordering at 50/50 and 60/40 using reference labels/groups only. Both keep duplicate groups intact; neither is a selected method, final membership artifact, power calculation or freeze. Script retained as `outputs/resume-20261117/review/partition_support.py`.
- **Limits:** Local consistency against retained provenance, not fresh remote attestation, annotation truth, near-duplicate independence or human review. No raw prompt/model-output display. Existing empirical evidence is unaffected; no empirical runs exist.

### V-012 — Approved browser access and retained pinned classifier configuration

- **Date/conditions:** 2026-11-17, America/New_York; Yash restored the Chrome window and reported readiness. Native browser UI showed the selected model's granted-access state. No agreement was accepted, credential extracted or new key created.
- **Observed:** The exact pinned `config.json` resolve URL rendered valid JSON. Browser Save As produced `Downloads/config.json`; an initial check of the intended audit destination failed because it had not been saved there. The actual 1,488-byte download was subsequently located and copied unchanged to `outputs/resume-20261117/model-browser/config.json`; SHA-256 `d54521222f0389dbc309f0dd1dc7392ded2e432c9bb9ec48133e2af1ed256728`.
- **Configuration evidence:** `Qwen3ForSequenceClassification`, `id2label` 0=`benign`, 1=`jailbreak`, `problem_type=single_label_classification`, declared `dtype=float16`, hidden size 1024, vocab size 151936, BOS 151643, EOS 151645 and maximum positions 40960. `num_labels`, `label2id` and `pad_token_id` are absent. This establishes configured orientation, not inspected head tensor shape or a validated runtime score transformation.
- **Evidence/provenance limits:** [browser/config receipt](evidence/p1a-browser-config-20261117.json) records the pinned URL, bytes/hash, observations and absent fields. Browser HTTP status, ETag and commit response headers were not captured; no status code is invented. No tokenizer or model weights are validated by this check.
- **Interruption:** Browser connector unavailable; native UI was used. After a tokenizer download attempt, Computer Use stopped because it could not determine the current browser URL on Windows with enough confidence to enforce policy. Browser interaction ceased. No completed tokenizer download was located. Earlier 401 responses remain unchanged.
- **Follow-up:** Retrieve/verify tokenizer files; inspect actual head metadata and selected library semantics; resolve padding explicitly and check single/padded execution during the pilot. Local Hub authentication remains absent; approved browser access is now independently observed. No inference or held-out performance was accessed.

### V-013 — Optional credential-safe metadata audit software

- **Date/target:** 2026-11-17; `precision_benchmark/model_audit.py` and `tests/test_model_audit.py`; exact tested hashes and Python version in [software verification](evidence/p1a-auth-software-20261117.json).
- **Change:** Explicit `--auth local` reads an existing configured Hub credential; `--auth prompt` requires hidden interactive input and does not save it. Default remains unauthenticated. Missing credentials fail before output creation/network requests. The implementation intends to confine requests/redirects to HTTPS `huggingface.co`, suppress credential-bearing error details and reject exact reflected credentials before persistence. Independent review found an exception-path gap despite these initial tests; see the failure below and V-014.
- **Observed:** All 34 tests passed (26 previous plus eight authentication checks). Initial targeted checks exposed two failures from eager home-directory evaluation with an explicit token path in a stripped Windows environment; the implementation was corrected and revalidated, with prior failure summary retained. Full log is `outputs/resume-20261117/auth-review/all-tests.txt`.
- **Limits/review:** Mocked transport and synthetic credentials only; no real authenticated CLI retrieval, token installation, tokenizer execution or scientific validity claim. Independent automated review demonstrated a malformed redirect-parser error containing a synthetic credential; this version is not accepted for real credential use. Correction/revalidation is V-014. No human scientific signoff or phase completion is implied. Historical V-005 remains evidence for its old source hashes, not the changed authentication module.

### V-014 — Redirect-parser disclosure regression and corrected authentication checks

- **Failure/affected version:** V-013's original 34-test evidence did not cover inherited urllib redirect parsing. Independent review found that a malformed bracketed-host Location could raise `ValueError` containing an echoed synthetic token before the custom URL validator ran. An invalid-port path had already been corrected concurrently; the inherited-parser path remained. No real secret was used or disclosed.
- **Preserved evidence:** [synthetic failure](evidence/p1a-auth-review-failure-20261117.json), `outputs/resume-20261117/review/auth-review-note.md`, and `outputs/resume-20261117/auth-review/redirect-regression-before-fix.txt`. The added regression failed before correction; expected redaction was not weakened.
- **Correction/check:** Sanitize both `OSError` and `ValueError` escaping `opener.open`. The regression invokes the inherited redirect handler through a fake opener and verifies generic failure without retaining a response. All 35 combined tests passed after correction; log `outputs/resume-20261117/auth-review/final-v2-all-tests.txt`, exact final hashes in [revalidation manifest](evidence/p1a-auth-revalidation-20261117.json).
- **Impact/limits:** V-013 remains historical initial-test evidence; current source is identified by V-014. This corrects credential-output handling, not a scientific metric/result. No real authenticated CLI request, credential installation, network-backed security attestation or model inference has run. Independent focused recheck passed: final source/test hashes match, the synthetic malformed redirect produces a generic error with no marker in message or rendered traceback, and no response file is written. [Independent evidence](evidence/p1a-auth-independent-review-20261117.json). Human scientific review remains pending.

### V-015 — Browser tokenizer configurations retained and checked

Three additional pinned files were saved through the approved browser: tokenizer config,
special-token map and added-token map. [Receipts](evidence/p1a-tokenizer-configs-20261117.json)
retain their bytes/hashes; [JSON checks](evidence/p1a-tokenizer-consistency-20261117.json)
verified all 26 added-token mappings and PAD/EOS ID151645 consistency among these files.
Browser automation stopped on current-URL confidence while opening the larger backend;
no further UI interaction occurred. Later authenticated retrieval (V-022) completed the
assets and matched these bytes. Browser-only evidence did not establish execution behavior.

### V-016 — Pinned library and pooling contract inspected

Transformers 4.57.1's tag resolved to commit `8cb5963cc22174954e7dca2c0a3320b7dc2f4edc`.
Twelve official files were retained with [source receipts](evidence/p1a-library-sources-20261117.json);
all installed file bytes [match](evidence/p1a-installed-sources-20261117.json). The release
is an audit candidate, distinct from the checkpoint's recorded 4.57.0.dev0.
[Static contract findings](evidence/p1a-library-contract-20261117.json) and seven
[integer pooling cases](evidence/p1a-pooling-cases-20261117.json) show that original
unset-PAD batch-one pooling selects the last array position, whereas stock PAD=EOS
pooling selects the last ID unequal to EOS and can skip genuine terminal EOS. A larger
batch with unset model PAD raises in this source. These are source/arithmetic checks,
not model runs. Mask-based pooling is only a candidate; no adapter/policy is selected.
Full notes/scripts are under `outputs/contract-20261117/library/`.

### V-017 — Audit environment installed; native execution blocked

The isolated `.venv` was created for the current audit, with versions in
[environment evidence](evidence/p1a-audit-environment-20261117.json). Installation logs
report success and `pip check` passed; the first PowerShell wrapper returned 1 after a pip
notice on stderr, so actual installed versions were verified without reinstalling.
`hf.exe auth login --help` was blocked by Windows Application Control. Yash explicitly
authorized the Python hidden-login alternative and completed it; its library imports work.
Importing `transformers.AutoConfig` separately failed at `regex._regex` with an Application
Control DLL block. [Observed failures](evidence/p1a-runtime-blockers-20261117.json) preserve
the exact operations and distinction. No security setting was changed or blocked native
library retried through another path. Dependent tokenizer/model execution remains paused.
Dependency resolution, installed source files and successful Hub access do not validate
CUDA, PyTorch, bitsandbytes, tokenization or inference.

### V-018 — Approved partition construction and initial software checks

`precision_benchmark.partition_data` constructs D-008 memberships from hash-bound,
text-free audit identities/provenance/receipt without reading prompts. Six synthetic tests
checked whole-group nearest-half ties, exclusion precedence, ordering, invalid identities,
source tampering, role boundaries and non-overwrite. The combined suite passed 41 tests.
Actual initial outputs and exact commands/hashes/logs are under
`outputs/contract-20261117/partitions/`; [original summary](evidence/p1a-partitions-v1-20261117.json).
The later decision/revision guard flaw is V-020; corrected source/outputs are V-021.

### V-019 — Independent approved-membership verification

[Independent review](evidence/p1a-partition-review-v1-20261117.json) checked all 43,425 IDs,
original fields/labels/order, complete accounting, zero exclusions, all exact-group
intersections, preservation of 71 test duplicate groups, hashes and precise D-008 ranked
prefix/nearest-half/fewer-A tie objective without importing the builder. Pending human
review/release was verified. This passes for the actual approved source and constructed
membership; it does not attest arbitrary future revisions or human scientific signoff.
Script/notes remain in `outputs/contract-20261117/partition-review/`.

### V-020 — Decision authority not initially bound to the approved revision

Coordinating review identified a reuse risk: the original builder accepted any internally
consistent revision while labeling the result D-008. An independent synthetic
[alternate-revision reproduction](evidence/p1a-partition-guard-failure-20261117.json)
confirmed that unapproved `b` repeated 40 times was accepted. No actual data file was
changed. The original source/tests and newly failing regression are retained under
`outputs/contract-20261117/partition-fix-evidence/`. Actual approved memberships are
unaffected; future authority claims required repair. V-021 supplies the correction.

### V-021 — Approved-revision guard repaired without changing membership

The builder now rejects a revision other than D-008's exact approved source before input
reads or output creation. Seven partition tests plus existing tests passed (42 total).
New construction `outputs/contract-20261117/partitions-v2/` retains exact commands and
source/test hashes in `execution.json`. All four population files, exclusions and access
manifest are byte-identical to v1; only summary code hashes changed. The independent
[post-fix probe](evidence/p1a-partition-guard-revalidation-20261117.json) and
[compatibility review](evidence/p1a-partition-guard-review-20261117.json) passed. Earlier
failure and v1 outputs are preserved. The current final combined integration is V-023.

### V-022 — Authenticated tokenizer assets and actual tensor header verified

After Yash privately configured a read token, a reviewed bounded retrieval helper fetched
seven pinned files and only two exact 206 header ranges. [Receipt](evidence/p1a-authenticated-contract-20261117.json)
and [file identities](evidence/p1a-model-file-identities-20261117.json) bind content to the
pinned revision. The helper's 14 mocked/synthetic checks and source hash are retained in
`outputs/contract-20261117/retrieval-helper/`. It caps selected files at 32 MiB total,
validates blob/LFS hashes, forbids full weight requests, strips cross-origin authorization,
preserves proxy/CA controls, and suppresses credential/provider error details.

Independent [asset review](evidence/p1a-asset-contract-review-20261117.json) recomputed
all file hashes/source identities, four browser-file comparisons, header length/extents,
shape/dtype totals and vocab/merge/added-token agreement. ASSET-002 owns the verified
values. Serialized PAD151643 differs from wrapper PAD/EOS151645; inspected wrapper code
resolves defaults per call, which must be checked in actual execution. A first wrapper
launch failed before network access because Windows could not resolve its relative
executable; an absolute executable path succeeded. No secret, signed URL, tensor payload
or model output was retained. Full weight integrity and native runtime remain unverified.

### V-023 — Integrated audit commands and publication candidate checked

The successful retrieval helper was integrated byte-for-byte as
`precision_benchmark/contract_audit.py`; its tests use the package import and allow the one
requests-specific check to skip when that optional dependency is absent. All 56 combined
tests passed in the audit `.venv`, with [exact source/test hashes](evidence/p1a-integrated-software-20261117.json)
and full log under `outputs/contract-20261117/integration/`. Independent code review
verified all 17 source/test hashes and the retained passing run, then passed 14 focused
contract tests; simulating unavailable requests passed 13 with the intended one skip.
No real credentials/network/native tokenization are used by these tests. Review notes are
`outputs/contract-20261117/final-code-review/review.md`. This is bounded software evidence,
not proof of defect-free behavior, runtime compatibility or human scientific approval.

### V-024 — Targeted NFC and development delimiter probe

The newly verified NFC tokenizer configuration motivated an administrative check using
Python Unicode database 14.0.0 on hash-verified original source bytes.
[Aggregate evidence](evidence/p1a-normalization-probe-20261117.json) found one training and
three test rows changed under Python NFC, with no new group collapse, cross-split NFC
overlap or conflicting-label group. Six training rows contain literal EOS; none of the
training/validation strings end exactly with it. No raw text or IDs were displayed.
This does not execute the Rust tokenizer, establish token lengths, rule out truncation
ending at EOS, or exclude other token-identical/near-duplicate inputs. Membership is
unchanged. Script/source hash: `outputs/contract-20261117/normalization_probe.py`.

Final publication QA for V-023 also checked local Markdown links, JSON parsing/LF, tested
source hashes and staged contents. An initial check found CRLF in five compact S-04 JSON
copies; only their outer line endings were normalized, parsed values verified unchanged,
and original ignored outputs/fixtures preserved. Receipt: `outputs/contract-20261117/compact-json-lf-repair.json`.
Canonical-record review found no scientific overclaim; D-006's current status now links
to D-008. The unsent Viraj draft was confirmed to reference actual constructed manifests.
