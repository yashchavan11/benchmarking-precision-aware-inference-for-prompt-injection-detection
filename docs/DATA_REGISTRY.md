# Asset, split and exposure registry

This register contains the verified identities, memberships and exposure history of the
assets actually used. The [research protocol](RESEARCH_PROTOCOL.md) defines data roles,
duplicate isolation and permitted access; this file records their implementation and evidence.
No pinned snapshot, partition membership or data audit has yet been recorded.

## Selected sources and verification state

| Asset | Selected source | Immutable revision / verified identity | Audit outstanding |
|---|---|---|---|
| Classifier | `rogue-security/prompt-injection-jailbreak-sentinel-v2` | Not recorded | Checkpoint configuration, head shape and positive-class mapping |
| Tokenizer | Tokenizer accompanying the selected Sentinel v2 checkpoint | Not recorded | Revision, special tokens, padding/truncation and classification pooling |
| Dataset | `hendzh/PromptShield` | Not recorded | Actual schema, official splits, row/class counts and duplicate structure |

These source selections are not verified snapshot identities. Provider descriptions are
catalogued in [SOURCES.md](SOURCES.md); audit entries below must distinguish provider claims
from properties observed in the pinned assets. Safe artifact references and hashes belong
here; raw prompt collections and credentials do not.

## Partition index

| Partition | Membership record / artifact | Parent revision | Effective row / class / group counts | Freeze and verification | Exposure state |
|---|---|---|---|---|---|
| Eligible training | Not constructed | Not pinned | Not audited | Pending P1-A | No audit recorded |
| Eligible validation | Not constructed | Not pinned | Not audited | Pending P1-A | No audit recorded |
| Test-A | Not constructed | Not pinned | Not audited | Pending P1-A | No exposure recorded |
| Test-B | Not constructed | Not pinned | Not audited | Pending P1-A | No exposure recorded |

The index describes recorded state, not proof that an asset has never been inspected.
Any verified prior access must appear in the exposure log. Pilot, profiling,
cross-validation and validation-subdivision manifests receive their own records when
created; each points to its eligible parent rather than silently redefining that parent.

## Asset record template

### ASSET-[unique ID] — [model / tokenizer / dataset]

- **Recorded by / date / source URL:** [actual values]
- **Immutable revision and retrieval identity:** [commit or source snapshot; never a guessed hash]
- **Team-accessible artifact reference and integrity hash:** [safe location and actual hash]
- **Verified configuration/schema:** [relevant fields, head shape and label mapping]
- **Tokenizer/preprocessing identity:** [associated revision and relevant configuration, where applicable]
- **License/access evidence:** [source, verified status and applicable conditions; no credentials]
- **Audit and verification evidence:** [run or validation IDs]
- **Used by:** [split, configuration or run IDs]
- **Known limitations:** [training provenance, contamination uncertainty, schema defects, etc.]

## Split and partition record template

### SPLIT-[unique ID] — [train / validation / Test-A / Test-B / pilot / profiling / fold]

- **Parent asset / immutable revision / parent split:** [source and eligible-parent references]
- **Purpose and allowed phase:** [role selected under the research protocol]
- **Construction method:** [algorithm/version, seed, source ordering, exact-text hash rule,
  duplicate-group handling and stratification procedure]
- **Membership artifact and integrity:** [stable original IDs, location, membership hash and ordered-ID hash where relevant]
- **Source and effective counts:** [total, per-class and per-group counts before and after exclusions]
- **Duplicate/conflict audit:** [within/across-partition findings, group references, conflicts and treatment]
- **Eligibility accounting:** [excluded source IDs, reason codes, precedence decision and retained counts]
- **Isolation verification:** [intersection-check evidence for the relevant held-out, fitting,
  selection and cross-validation boundaries]
- **Text/token-length summary:** [method, tokenizer identity, aggregate statistics and truncation support]
- **Related decisions:** [allocation, grouping, preprocessing, exclusions and approved amendments]
- **Freeze date / author / reviewer:** [actual values and linked evidence]
- **Exposure state:** [unopened / administrative audit only / development-visible / final-results-released;
  exposure-log references and any access limitations]
- **Known support or dependence limitations:** [class/group feasibility, residual near-duplicates or provenance uncertainty]
- **Linked runs and results:** [downstream IDs; any affected evidence after a membership change]

## Exposure log

No exposure entries have been recorded. This absence is not a verified history of non-access.

| Exposure ID | Date / actor or process | Split / artifact / record IDs | Information revealed | Purpose and protocol boundary | Consequence / decision / affected evidence |
|---|---|---|---|---|---|

The **information revealed** field distinguishes schema/count inspection, reference-label
use for administrative stratification, raw-example inspection, model scores, aggregate
metrics and individual errors. Record the audience and access channel when exposure occurs
through a shared chat, notebook, report or artifact; identify accidental exposure explicitly.
The consequence field records whether a planned evaluation remains eligible and links any
required redesign or limitation. Permitted exposure and holdout-release rules are defined
once in [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md).
