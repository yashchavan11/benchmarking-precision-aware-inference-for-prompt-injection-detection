# Open questions and blockers

Register of unresolved choices and uncertainties affecting concrete project work. An open
question is not a demonstrated failure. Resolved entries retain links to the decision or
evidence that answered them.

## Initial questions

| ID | Question | Resolution boundary | Current state |
|---|---|---|---|
| Q-001 | What exact model, tokenizer and dataset revisions are available, and what are their actual schemas and label mappings? | P1-A, before relying on predictions. | Partly resolved: dataset revision/schema/counts and public model revision verified in ASSET-001/002; pinned model/tokenizer configs returned 401, so head/output mapping remains unknown (V-009). |
| Q-002 | What Test-A/Test-B allocation supplies adequate class support and duplicate isolation while preserving a useful untouched extension holdout? | Before any Part 1 official-test model-performance inspection; see D-006. | Open; no completed partition. |
| Q-003 | What duplicate/conflicting-label issues exist, and which development eligibility manifests remove held-out overlaps and separate gate fitting from validation selection? | Audit in P1-A; resolve exclusions and relevant sensitivity analyses before affected fitting/evaluation. | Exact audit completed (V-008): no cross-split overlaps/conflicts; 71 duplicate groups within test. Projection removes no development rows. A/B grouping, final eligibility and residual near-duplicate limitations still need review. |
| Q-004 | Which preprocessing and common execution conditions produce a valid, feasible three-precision comparison? | Development investigation in P1-B; P1-C freeze. | Open. |
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
- **Current local state (S-20261117-03):** Yash now reports accepting model access. A new local check still found no configured Hub credential; the unauthenticated pinned config request returned 401 (V-010). Account acceptance and authenticated local retrieval are separate conditions. No token was displayed or saved to project artifacts.
- **Next action:** Establish authenticated local read access using Yash's already-approved account, or use an authorized authenticated browser flow. Do not ask him to accept the terms again unless evidence shows a remaining provider requirement. Do not paste credentials into chat or Git. Retrieve pinned configs into a new artifact directory and verify labels/head/tokenizer before inference.
- **Independent work:** Administrative data audit and evaluator integration completed; environment inventory is retained. No substitution of a different classifier or silent relaxation of the access requirement.

### Q-013 — Prior external test exposure and final partition design

- **Raised/date/phase:** 2026-11-17, P1-A.
- **Known:** This session processed all splits administratively and viewed aggregate statistics; an incidental source-page view showed training snippets (EXP-002). No model performance or test prompts were displayed. Exact training/test overlap is zero; near-duplicate relationships and prior team access remain unknown.
- **Next action:** Confirm whether team members previously inspected official-test examples or outputs. Then review group-preserving 50/50 or 60/40 allocation candidates using ASSET-001's support; choose and record the design before any test-model performance. Do not invent a sealed-history claim or choose an allocation implicitly.
- **Status:** Yash reports no prior test inspection to his knowledge; this is not an independently verified history for every teammate. He subsequently reports accepting model access; local authentication remains Q-012. No partition freeze, model-test run or empirical phase advance.

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
