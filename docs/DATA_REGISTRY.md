# Asset, split and exposure registry

This register contains the verified identities, memberships and exposure history of the
assets actually used. The [research protocol](RESEARCH_PROTOCOL.md) defines data roles,
duplicate isolation and permitted access; this file records their implementation and evidence.
Pinned administrative source audits are recorded below. Evaluation partitions and final
development eligibility are not frozen; the selected checkpoint's private configuration
and output-label mapping remain unavailable without authorized access.

## Selected sources and verification state

| Asset | Selected source | Immutable revision / verified identity | Audit outstanding |
|---|---|---|---|
| Classifier | `rogue-security/prompt-injection-jailbreak-sentinel-v2` | Candidate audited revision `05ff9bfd1f28c5228e53121d5ee4427bb5205212`; ASSET-002 | Configuration files gated; head shape, positive-class mapping and runtime precision unverified |
| Tokenizer | Tokenizer accompanying the selected Sentinel v2 checkpoint | Same candidate repository revision; ASSET-002 | Full files gated; numerical token IDs, padding/truncation and classification pooling unverified |
| Dataset | `hendzh/PromptShield` | `a5234cb1f5cdb256600cab64b8c961195b5e8404`; ASSET-001 | Source schema/counts/exact duplicates audited; tokenizer lengths and final eligibility/A-B design pending |

The recorded revisions identify audited sources, not a complete experimental freeze. Provider descriptions are
catalogued in [SOURCES.md](SOURCES.md); audit entries below must distinguish provider claims
from properties observed in the pinned assets. Safe artifact references and hashes belong
here; raw prompt collections and credentials do not.

## Partition index

| Partition | Membership record / artifact | Parent revision | Effective row / class / group counts | Freeze and verification | Exposure state |
|---|---|---|---|---|---|
| Eligible training | Overlap-rule projection in ASSET-001; not frozen | ASSET-001 | Projection: 18,909 rows/groups; 9,457 class 0 / 9,452 class 1 | Audit V-008; final eligibility pending | Administrative audit; incidental training snippets, EXP-002 |
| Eligible validation | Overlap-rule projection in ASSET-001; not frozen | ASSET-001 | Projection: 1,000 rows/groups; 497 class 0 / 503 class 1 | Audit V-008; final eligibility pending | Administrative audit, EXP-002 |
| Test-A | Not constructed | ASSET-001 official test | No allocation selected | Pending P1-A / Q-002, Q-013 | Source aggregate audit only this session; prior external exposure unknown |
| Test-B | Not constructed | ASSET-001 official test | No allocation selected | Pending P1-A / Q-002, Q-013 | Source aggregate audit only this session; no sealed-history claim yet |

The index describes recorded state, not proof that an asset has never been inspected.
Any verified prior access must appear in the exposure log. Pilot, profiling,
cross-validation and validation-subdivision manifests receive their own records when
created; each points to its eligible parent rather than silently redefining that parent.

## Audited assets

### ASSET-001 — PromptShield administrative snapshot

- **Date/phase:** 2026-11-17, America/New_York; P1-A, automated administrative audit requested by Yash.
- **Source identity:** `hendzh/PromptShield` at `a5234cb1f5cdb256600cab64b8c961195b5e8404`; URLs and exact source hashes in [retained provenance](evidence/p1a-data-provenance-20261117.json). Original UTF-8 JSON bytes retained under `data/raw/promptshield/a5234cb1f5cdb256600cab64b8c961195b5e8404/` (ignored; about 31 MB). `source-integrity.json` binds future reuse to the retained bytes.
- **Observed schema:** Nonempty arrays of objects containing exactly `prompt` (string) and `label` (integer 0 or 1). No malformed labels, empty text, or whitespace-only rows observed. Pinned source card describes 0 as benign and 1 as injection; the audit validates encoding, not the semantic truth of each annotation.

| Official split | Rows | Benign (0) | Injection (1) | Exact-text groups |
|---|---:|---:|---:|---:|
| Train | 18,909 | 9,457 | 9,452 | 18,909 |
| Validation | 1,000 | 497 | 503 | 1,000 |
| Test | 23,516 | 17,030 | 6,486 | 23,359 |
| Total | 43,425 | 26,984 | 16,441 | 43,268 |

- **Grouping:** SHA-256 of each decoded original prompt re-encoded as UTF-8, without trimming or Unicode normalization. No exact-text group crosses official splits; no conflicting-label group exists. Test contains 71 duplicate groups comprising 228 rows (157 excess rows), all benign; largest group has 58 rows. Test group support is 16,873 benign groups and 6,486 injection groups. Full size distribution and character/byte summaries are in [summary](evidence/p1a-data-summary-20261117.json).
- **Identity/membership artifacts:** IDs are `revision:original-split:zero-based-row`. `outputs/asset-audit-20261117/dataset/audit-v3/row-identities.jsonl` preserves all 43,425 IDs, labels, raw-text hashes and lengths without prompts. `projected-train-identities.jsonl`, `projected-validation-identities.jsonl`, and `development-exclusions.jsonl` apply the protocol's test-overlap-first then validation-precedence rules. No development row is excluded. These projections are not final eligibility or A/B assignments. Output/ordered-ID hashes are retained in the provenance and summary.
- **Source/access conditions:** Public ungated source; pinned card/API metadata declare `apache-2.0`. No raw source data or derivative prompts were published. No broader redistribution/legal conclusion is asserted here.
- **Review:** V-006–V-008; independent direct-string checks covered all identities and aggregates, 4,096 synthetic precedence cases, and the corrected source-cache checks. Human/team scientific signoff is pending.
- **Exposure/limitations:** EXP-002; character and byte counts are not token counts. Exact hashes cannot establish absence of paraphrases, attack-template dependence or pretrained-model contamination. Prior external team exposure remains unknown. Allocation, access controls, final eligibility and sequence-length decisions remain pending.
- **Retention:** Source bytes and large identity manifests remain local and ignored; their project-relative references/hashes and compact summary/provenance are preserved. No team-wide artifact storage has yet been agreed. Do not imply that another machine already has the ignored files; regenerate from pinned public sources and verify hashes, or explicitly transfer them through agreed storage.

### ASSET-002 — Sentinel v2 public metadata and gated-file evidence

- **Date/source identity:** 2026-11-17, P1-A; `rogue-security/prompt-injection-jailbreak-sentinel-v2` at `05ff9bfd1f28c5228e53121d5ee4427bb5205212`. Exact URLs, status codes, response hashes and safe configuration fields are retained in [metadata summary](evidence/p1a-model-metadata-20261117.json).
- **Accessible evidence:** Public pinned API, model card and license file. API declares `Qwen3ForSequenceClassification`, base `Qwen/Qwen3-0.6B`, 596,051,968 parameters with F16 storage metadata, and EOS/PAD strings `<|im_end|>`. These are provider declarations, not verified model execution or tensor inspection. Card names a `jailbreak` output, but output index is not established.
- **Access failure:** Pinned `config.json`, `tokenizer_config.json`, `special_tokens_map.json`, and `added_tokens.json` returned HTTP 401 unauthenticated. Files retained with those names in `outputs/asset-audit-20261117/model/` contain failure-response text, not usable config. No weights were downloaded. Q-012 tracks approved account access; no credential was found in the checked local locations.
- **License evidence:** Pinned `LICENSE.md` identifies Elastic License 2.0; API license field is `other`. No new agreement was accepted and no redistribution approval is claimed.
- **Still unverified:** Actual head shape/num_labels/index mapping, numerical token IDs, safe score transformation, tokenizer defaults, last-token pooling, single-versus-padded batching, effective dtypes and INT8 module conversion. A base-model config or chat-template presence cannot substitute for these checks.
- **Validation/retention:** V-009; all eight response hashes and audit source identity independently checked. Source responses and detailed notes remain locally in the model output directory; compact safe evidence above is retained with project documents. The revision is an audited candidate identity, not a final experiment freeze.
- **Access follow-up (2026-11-17):** Yash reports accepting model access. V-010 records that local credentials are still absent and a fresh unauthenticated pinned config request still returns 401. Do not treat this as rejection of his account approval; configure authenticated access before repeating the full asset audit. Historical failed responses remain preserved.

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

This log records verified session access; it does not establish that other contributors
have never accessed the data. Prior external exposure is an unresolved question (Q-013).

| Exposure ID | Date / actor or process | Split / artifact / record IDs | Information revealed | Purpose and protocol boundary | Consequence / decision / affected evidence |
|---|---|---|---|---|---|
| EXP-001 | 2026-11-17; local automated review at Yash's request | Synthetic evaluator fixtures at `1d9f9ca` and regression cases | Invented labels/scores/metrics/errors only | Incoming review and local integration, V-003–V-005 | No real model/dataset access in the initial review; no empirical findings |
| EXP-002 | 2026-11-17; data audit process and automated reviewers | ASSET-001, all official splits; source-page training viewer | Scripts read raw text/labels to compute hashes and administrative aggregates; reviewers saw counts, schema, hashes and summaries. Initial web source page displayed 50 default training snippets; exact viewer indices were not verified. No official-test prompt or model output was displayed. | Administrative audit and duplicate/isolation checks; incidental training display recorded | All training/test exact-text intersections are zero, so training snippets cannot expose an exact-text test match. Near-duplicate propagation and prior team exposure remain unknown. A first-50 proxy is explicitly not an exact exposure manifest. No A/B allocation or performance-driven choice made. |

The **information revealed** field distinguishes schema/count inspection, reference-label
use for administrative stratification, raw-example inspection, model scores, aggregate
metrics and individual errors. Record the audience and access channel when exposure occurs
through a shared chat, notebook, report or artifact; identify accidental exposure explicitly.
The consequence field records whether a planned evaluation remains eligible and links any
required redesign or limitation. Permitted exposure and holdout-release rules are defined
once in [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md).
