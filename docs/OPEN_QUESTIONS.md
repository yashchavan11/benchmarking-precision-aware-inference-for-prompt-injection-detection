# Open questions and blockers

Register of unresolved choices and uncertainties affecting concrete project work. An open
question is not a demonstrated failure. Resolved entries retain links to the decision or
evidence that answered them.

## Initial questions

| ID | Question | Resolution boundary | Current state |
|---|---|---|---|
| Q-001 | What exact model, tokenizer and dataset revisions are available, and what are their actual schemas and label mappings? | P1-A, before relying on predictions. | Resolved for P1-A input scope: ASSET-001/002 and V-034 through V-038 verify exact sources, native tokenizer/configuration, label orientation/head descriptor and all-source lengths. Full model loading, original batch-one pooling and three precision treatments are additionally verified by V-041; main-study choices remain P1-C. |
| Q-002 | What Test-A/Test-B allocation supplies adequate class support and duplicate isolation while preserving a useful untouched extension holdout? | Before any Part 1 official-test model-performance inspection; see D-006. | D-008 approved 50/50; review-ready memberships verified V-018–V-021. Independent construction review passed; D-009 removes teammate waits. Performance release remains subject to the protocol freeze. |
| Q-003 | What duplicate/conflicting-label issues exist, and which development eligibility manifests remove held-out overlaps and separate gate fitting from validation selection? | Audit in P1-A; resolve exclusions and relevant sensitivity analyses before affected fitting/evaluation. | Exact audit completed (V-008): no cross-split overlaps/conflicts; 71 duplicate groups within test. Projection removes no development rows. D-008 construction now applies exact grouping/eligibility (V-021); unperformed human review and residual near-duplicate limits remain documented; D-009 permits independent continuation. |
| Q-004 | Which preprocessing and common execution conditions produce a valid, feasible three-precision comparison? | Development investigation in P1-B; P1-C freeze. | Resolved for the bounded P1-B batch-one pilot by D-012/V-041; main-study preprocessing, batching and precision settings still require P1-C selection. |
| Q-005 | Which quality metric is primary, and which shared-threshold selection rule reflects the intended comparison? | Selection from documented candidates before P1-C freeze. | Open. |
| Q-006 | What profiling and uncertainty budget is adequate for stable, interpretable results? | Pilot in P1-B; main-plan freeze in P1-C. | Open; additional checks may be justified by pilot evidence. |
| Q-007 | Which low/high precision pair offers useful recoverable-error headroom and measured cost differences? | P2-A, using development evidence. | Open. |
| Q-008 | Which permitted features and learned-gate family predict net benefit beyond simple confidence routing? | P2-C development and diagnostic iterations. | Open. |
| Q-009 | What accuracy tolerance, cost budget or tradeoff objective selects the gate's operating point? | Before final policy selection and Test-B exposure. | Open. |
| Q-010 | Which residency/loading scenario is practical, and does measured complete cascade cost support the desired claim? | P2-D, before the final evaluation freeze. | Open. |
| Q-011 | What protected validation-selection arrangement is needed after repeated exploration? | Before extensive Part 2 tuning; candidate arrangements include training-only cross-validation or a fixed validation partition. | Open. |

The candidate settings and permitted data roles are defined in [ROADMAP.md](ROADMAP.md),
[RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md) and [EXTENSION.md](EXTENSION.md). This register
tracks whether questions have been resolved; it does not establish a competing method.

## Access and exposure follow-up

### Q-012 — Authorized access to the selected gated checkpoint

- **Raised/date/phase:** 2026-11-17, P1-A; local access audit requested by Yash.
- **Type/evidence:** Verified access blocker: public pinned model API/card/license return 200; configuration/tokenizer files return HTTP 401 without authentication (V-009).
- **Historical local state (S-20261117-03):** Yash now reports accepting model access. A new local check still found no configured Hub credential; the unauthenticated pinned config request returned 401 (V-010). Account acceptance and authenticated local retrieval are separate conditions. No token was displayed or saved to project artifacts.
- **Current state (S-20261117-05):** Resolved for authenticated asset access. Yash privately configured a read token using an explicitly authorized Python login alternative after Windows blocked the hf.exe launcher. All seven selected files and bounded header ranges were retrieved and verified (V-022), with no token in chat/project/Git. Full weight download remains unperformed by design.
- **Next action:** Reuse retained pinned assets and the fully verified checkpoint. Native Explorer tokenizer and three-treatment GPU execution are now verified (V-034/V-041); Windows policy remains unchanged. Do not repeat access acceptance or confuse historical unauthenticated 401s with authenticated access.
- **Independent work:** Administrative data audit and evaluator integration completed; environment inventory is retained. No substitution of a different classifier or silent relaxation of the access requirement.

### Q-013 — Prior external test exposure and final partition design

- **Raised/date/phase:** 2026-11-17, P1-A.
- **Known at the P1-A administrative checkpoint:** That work processed all splits administratively and viewed aggregate statistics; an incidental source-page view showed training snippets (EXP-002). No model performance or test prompts were displayed. Exact training/test overlap is zero; near-duplicate relationships and prior team access remain unknown.
- **Next action under D-009:** Continue from verified D-008 memberships and inspect incoming work/artifacts when pushed. Do not wait for or routinely solicit separate exposure attestations. Preserve unknown history; assess actual leakage if discovered and bound affected claims. No invented sealed-history claim or silent allocation change.
- **Earlier candidate evidence (now followed by approved D-008):** V-011 and `docs/evidence/p1a-partition-candidates-20261117.json` provide reproducible group-preserving 50/50 and 60/40 support proposals. Automated recommendation is 50/50 for equal support across both committed studies; no selection/freeze or power claim. Final eligibility, ratio/algorithm/seed and exposure controls require the requested team/user decision.
- **Status:** Yash reports no prior test inspection to his knowledge; this is not an independently verified history for every teammate. Authenticated asset access now succeeds (V-022/Q-012 resolved); runtime execution is the separate Q-015 blocker. D-008 now selects the design and V-021 constructs review-ready memberships; human review remains unperformed but is not a continuation gate under D-009; test releases and empirical phase prerequisites remain unchanged.

## Question record schema

### Q-[next unique number] — [question]

- **Raised by / date / phase:** [actual values]
- **Type:** [design choice / scientific uncertainty / verified technical blocker]
- **Why it matters:** [dependent goal, claim or task]
- **Known evidence:** [source/evidence IDs]
- **Missing information:** [specific unknown]
- **Candidate answers:** [bounded alternatives and their tradeoffs]
- **Smallest useful investigation:** [permitted data, expected observation and cost]
- **Owner / resolution boundary:** [actual assignment or unassigned; relevant deadline or phase]
- **Status:** [open / investigating / resolved / deferred with reason]
- **Resolution:** [answer with decision, validation, run or result references]
- **Effect on existing work:** [what remains valid and what changes]
- **Blocker evidence, if applicable:** [attempted operation, conditions, observed failure and smallest reproduction]
- **Independent work, if blocked:** [useful actions that remain possible without the missing dependency]

### Q-014 — Explicit tokenizer and pooling semantics

V-016/V-022/RES-002 establish the source-level PAD mismatch and EOS-sensitive pooling
choice. Verify actual wrapper behavior, NFC/special-token handling, explicit cap and
single-versus-padded agreement in an approved runtime. Proposed first reference is original
unpadded batch one; standard PAD=EOS or a mask-based adapter are unselected alternatives.
Do not silently change head pooling, strip delimiters, resize embeddings or substitute a
base tokenizer. No real outputs exist to invalidate; the pilot proposal must state these checks.

### Q-015 - Windows native block; approved Explorer CPU/GPU routes verified

Current disposition: the approved Explorer CPU tokenizer/configuration and GPU inference routes
are verified by V-034 through V-041. Windows itself remains blocked; its policy was not changed.
The following paragraph preserves the earlier local failure and conditions preceding authorization.

V-017 records `regex._regex` DLL import blocked while importing Transformers. The user
authorized the Python login alternative for the separate blocked hf.exe launcher; that
authorization does not remove the native-runtime block. No security policy was weakened or
blocked module retried through a substitute execution path. An approved executable runtime
(for example, provisioned university-cluster access) or user/administrator resolution is
needed before token-length and inference checks. Preserve the installed environment/logs;
do not reinstall blindly. Standard-library administrative construction and authenticated
HTTP/header retrieval have completed independently. CUDA/PyTorch/bitsandbytes feasibility
is still untested and no expensive experiment is authorized by an environment proposal.

### S-20261117-06 disposition of coordination and runtime dependencies

D-009 supersedes separate teammate review/exposure declarations as automatic wait
conditions. Q-013 remains an uncertainty to report and assess if new evidence arrives,
not a request to stop until each teammate answers. Communicate completed overlapping
work and shared settings to affected teammates; inspect their actual pushed contributions.
V-025 confirms Q-015 is a real enforced native-library block. It does not prevent the
standard-library input preflight now completed in V-026. No Viraj-specific missing code
or artifact is demonstrated to block the current work.

### Q-016 - Official-test length administration (resolved by D-011 / V-037 / V-038)

The initial native development run deliberately excluded official test, leaving its token
lengths as an explicit remaining P1-A requirement. Yash separately approved the total-only
administrative route in D-011. R-P1-A-20261117-08 completed all 23,516 source rows, and V-038
independently verified source/support, total histogram/statistics and runtime identity.
The all-split length requirement is complete; no inference guard or test-performance freeze
changed. The cap 1024 pilot proposal in RES-003 preceded any test-token statistics and remains
development-derived and unfrozen. No model result or cap choice follows from this audit.

Q-014 now includes verified original batch-one model/EOS pooling (V-041), while padded
equivalence remains unsupported. Q-015 includes verified approved Explorer CPU and GPU
routes; Windows itself remains blocked and its policy is unchanged. The P1-A closeout
below preserves the earlier state before that P1-B execution.

### P1-A closeout disposition - November 17

Q-001/Q-003 source/schema/label/group/eligibility/input-contract requirements are completed
within recorded audit limits. Q-002's construction is selected and verified by D-008;
performance release still awaits the proper freezes. Q-012 access and the approved CPU
portion of Q-015 are resolved; Windows itself is unchanged. D-011 and V-037/V-038 resolve
Q-016's all-split length requirement. Q-013 remains a disclosed unknown-history limitation
under D-009, not an attestation wait. Q-004/Q-014 now concern actual model/GPU/precision
and pooling checks in P1-B. No model-weight load, pilot configuration approval or final
threshold selection is inferred from P1-A completion.

### P1-B closeout disposition - November 17

Q-004 now has actual same-GPU FP32/FP16/LLM.int8 feasibility evidence and complete compatible
pilot predictions (V-041/V-042). Q-014 is resolved for original unpadded batch-one/EOS
pooling and explicit rejection of padded batches; a different batching/pooling policy
still needs validation if proposed. Q-015's approved Explorer GPU route now works with
recorded native versions and actual hardware; Windows policy remains unchanged.
Q-005/Q-006 remain open for the primary endpoint, final validation threshold rule,
uncertainty and repeated profiling decisions in P1-C. Pilot 0.5/cap 1024 and observed resource
samples do not close those choices. No Viraj-specific missing deliverable blocks the
completed inference/report contribution. Report assembly can use the portable bundle;
test releases and full learned-gate requirements remain unchanged.
