# Asset, split and exposure registry

This register contains the verified identities, memberships and exposure history of the
assets actually used. The [research protocol](RESEARCH_PROTOCOL.md) defines data roles,
duplicate isolation and permitted access; this file records their implementation and evidence.
Pinned sources and the approved D-008 population construction are recorded below.
Review-ready eligibility/A/B memberships now exist. D-009 authorizes independent development
continuation without teammate attestations; performance releases still follow the protocol. Authenticated pinned tokenizer files and the classifier tensor header are verified;
native tokenization/configuration and all-source lengths now pass V-034 through V-038.
Full checkpoint identity and same-GPU FP32/FP16/LLM.int8 execution are verified for the bounded batch-one P1-B pilot (V-041); the main study and padded-equivalence policy remain unfrozen.

## Selected sources and verification state

| Asset | Selected source | Immutable revision / verified identity | Verified scope / remaining work |
|---|---|---|---|
| Classifier | `rogue-security/prompt-injection-jailbreak-sentinel-v2` | Audited/executed revision `05ff9bfd1f28c5228e53121d5ee4427bb5205212`; ASSET-002 | Full payload/hash, actual loading/head orientation and three effective precision treatments verified in batch-one pilot (V-039/V-041); source score.weight F16 [2,1024], no bias |
| Tokenizer | Tokenizer accompanying the selected Sentinel v2 checkpoint | Same audited repository revision; ASSET-002 | Native wrapper/configuration/all-source lengths verified (V-034 through V-038); actual final-token/EOS pooling verified (V-041). Padded equivalence is unsupported, not assumed |
| Dataset | `hendzh/PromptShield` | `a5234cb1f5cdb256600cab64b8c961195b5e8404`; ASSET-001 | D-008 construction and all-source lengths checked; P1-A complete, unknown-history/near-duplicate limitations retained |

The recorded revisions identify audited sources, not a complete experimental freeze. Provider descriptions are
catalogued in [SOURCES.md](SOURCES.md); audit entries below must distinguish provider claims
from properties observed in the pinned assets. Safe artifact references and hashes belong
here; raw prompt collections and credentials do not.

## Partition index

| Partition | Membership record / artifact | Parent revision | Effective row / class / group counts | Freeze and verification | Exposure state |
|---|---|---|---|---|---|
| Eligible training | SPLIT-001; `eligible-training.jsonl` in current partition directory | ASSET-001 | 18,909 rows/groups; 9,457 benign / 9,452 injection | D-008/V-021; D-009 development-access amendment | Native tokenization EXP-005/006; selected 128-row model pilot and score/error inspection EXP-008; earlier training snippets EXP-002 |
| Eligible validation | SPLIT-002; `eligible-validation.jsonl` | ASSET-001 | 1,000 rows/groups; 497 benign / 503 injection | D-008/V-021; D-009 development-access amendment | Native development tokenization, EXP-005/006; no model outcome |
| Test-A | SPLIT-003; `test-a.jsonl` | ASSET-001 official test | 11,758 rows; 8,515 benign / 3,243 injection; 11,657 groups | D-008; performance release pending P1-C | No project model performance; prior team history incompletely declared |
| Test-B | SPLIT-004; `test-b.jsonl` | ASSET-001 official test | 11,758 rows; 8,515 benign / 3,243 injection; 11,702 groups | D-008; performance release pending P2-D/P2-E | Administrative only; no claim of cryptographic or universal historical sealing |

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

### ASSET-002 follow-up — Authenticated browser configuration, S-20261117-04

V-012 verifies account-granted access and retains the pinned classifier config at
`outputs/resume-20261117/model-browser/config.json`; its source URL, byte hash and complete
configuration are in [the safe receipt](evidence/p1a-browser-config-20261117.json).
Configured labels are 0=`benign` and 1=`jailbreak`, with a single-label classification
task. The config omits `num_labels`, `label2id` and `pad_token_id`; do not fabricate these
fields or treat omitted padding as an established batching policy. Tensor head dimensions,
runtime output shape/softmax, tokenizer IDs/defaults, pooling and effective precision still
require verification. No weights were downloaded. Earlier failures remain historical evidence.

The browser account path works; local Python still has no configured Hub credential.
V-013/V-014 add and revalidate an optional secure credential-reading path but does not establish a successful
authenticated CLI request. Browser automation was stopped by its URL-confidence policy;
tokenizer retrieval remains incomplete. Original model license/access limitations persist.

### EXP-003 — Resume audit and model-source access

2026-11-17; coordinating agent and independent automated reviewer at Yash's request.
Retained source bytes were hashed, and text-free identities/reference labels were used for
integrity and unselected allocation-support calculations (V-011). No PromptShield prompt,
model prediction or performance was displayed. The browser showed the model card, its
publisher example/results, the access-granted notice and pinned model configuration
(V-012); publisher results are not project findings. No official-test performance or
new dataset-example exposure occurred. Team external-history uncertainty remains Q-013.

### ASSET-002 follow-up — Authenticated complete tokenizer assets and tensor header

- **Identity/retrieval:** Same selected immutable model/tokenizer revision. V-022 and [authenticated receipt](evidence/p1a-authenticated-contract-20261117.json) retain seven files (15,884,361 bytes) under `outputs/contract-20261117/model-auth/`. Six Git blob identities and the tokenizer JSON LFS SHA-256 match the pinned [file metadata](evidence/p1a-model-file-identities-20261117.json). All four previously browser-saved configs match byte-for-byte. Original failures remain retained.
- **Header evidence:** Two exact HTTP 206 ranges retrieved only the eight-byte prefix and 35,024-byte header of the 1,192,138,968-byte checkpoint. The header describes 311 F16 tensor extents totaling 596,051,968 elements, including `score.weight` shape `[2,1024]`, no `score.bias`. Header SHA-256 is `38c56eac7bc3c2fb0c1c3a212f6e13b7c0453c7d246041562f078fb8ef7f1458`. Full tensor payload/LFS checksum, weight values and actual loading remain unverified; F16 storage does not establish effective inference precision.
- **Configured score contract:** Actual two-row head descriptor plus `id2label`/single-label config support the protocol's two-logit softmax with injection index 1. Retain both logits and compute injection score explicitly; default pipeline top-label confidence is not that score. Actual finite logits/shape and consistent conversion across treatments still require runtime checks.
- **Tokenizer evidence:** BPE backend has 151,643 vocabulary entries, 151,387 merges and 26 added-token entries, independently matched to external vocab/merges and configuration. Backend and inspected slow-tokenizer source specify NFC normalization. Preserve original dataset text/hashes; do not manually normalize or rewrite source prompts.
- **Defaults requiring explicit control:** Wrapper config declares PAD/EOS `<|im_end|>` ID 151645, left padding, right truncation and model_max_length 131072. Serialized backend instead stores PAD `<|endoftext|>` ID 151643 and truncation cap 5000. Model positional maximum is 40960 and model PAD remains unset. Pinned wrapper source resolves these defaults per call, but no actual encoding has yet run. A direct backend call cannot silently substitute for the selected wrapper. Q-014 tracks pooling semantics and V-016/V-022 retain source interpretation.
- **Access/runtime:** Yash configured a read token privately using the explicitly authorized Python login path; successful authenticated file access resolves Q-012. Credential values remain outside project files/Git. Windows Application Control blocks the installed regex native library, so tokenizer lengths and inference remain paused (Q-015/V-017).
- **Review/terms:** Independent automated asset review is [V-022 evidence](evidence/p1a-asset-contract-review-20261117.json), not human signoff. Original source terms were inspected; the unmodified upstream license accompanies reproduced configuration metadata in `docs/third_party/`. No tokenizer vocabulary, weight payload or dataset prompts are included in the publication candidate. This does not claim review of unknown agreements or approve later larger-asset redistribution.

### SPLIT-001 through SPLIT-004 — D-008 review-ready populations

- **Parent/decision:** ASSET-001 official sources, unchanged; D-008 owns the approved exact allocation method, namespace, eligibility precedence and exposure controls. No model output was available when Yash selected 50/50.
- **Current artifact directory:** `outputs/contract-20261117/partitions-v2/`. [Summary/provenance](evidence/p1a-partitions-20261117.json) records exact input, source, membership, ordered-ID and output-file hashes, class/group counts and source-code identity. [Access manifest](evidence/p1a-partition-access-20261117.json) binds roles to file hashes and leaves review/release pending.
- **Coverage:** All 43,425 source IDs are accounted for exactly once. All 18,909 train and 1,000 validation rows remain eligible under approved exact-overlap rules; exclusions are empty. Test-A and Test-B each contain 11,758 rows (8,515 benign/3,243 injection). A/B groups total 11,657/11,702; 35/36 duplicate groups respectively. All 71 test duplicate groups remain intact. Six cross-population exact-group intersections are zero.
- **Compatibility/review:** V-018/V-019 verified original construction; V-020 found a reusable decision/revision guard defect. V-021 rejects unapproved revisions and reconstructs v2 with every population/exclusion/access file byte-identical to v1. The original memberships remain valid administrative evidence; preserve both versions. Human scientific review, prior exposure declarations and test-performance releases remain pending. No P1-A or main-protocol freeze is implied.
- **Retention/limits:** Large text-free manifests remain ignored locally, with reproducible code/commands and compact hashes retained. Team access to ignored files is not assumed. Exact grouping and the V-024 NFC probe do not exclude paraphrases, attack-template dependence or pretrained contamination. Counts do not establish power.

### EXP-004 — Authenticated asset and approved partition work

2026-11-17; automated tools/reviewers at Yash's request. Authenticated model-source files
and header metadata were inspected without weights or model execution. All dataset IDs,
reference labels and group hashes were used administratively for D-008 construction and
independent checks. A targeted Python NFC probe read pinned raw splits solely to compute
aggregate collision counts; development-only literal EOS incidence was counted without
displaying prompts or IDs. No official-test prompts, scores, errors or performance were
displayed. Membership was not changed by the probe. Human external exposure remains Q-013.

### D-009 development-access amendment and input preflight

The [development-access amendment](evidence/p1a-development-access-20261117.json), SHA-256
`83dde0502e9aca5cfd000c5f6ec9631602db9f03a334a2f1a42d9ac3adc3e79b`, explicitly authorizes
the unchanged SPLIT-001/002 memberships for input preflight and permitted development
without a separate teammate attestation. It binds the original D-008 summary/access and
population/source hashes. Old v2 access metadata is preserved as history; Test-A/Test-B
release remains pending under the original freezes. Human review is not falsely claimed.

R-P1-A-20261117-06 validates all 18,909 training and 1,000 validation rows against the
original text, source position, label, character/UTF-8 length and raw-text hash. See
[training evidence](evidence/p1a-training-input-preflight-20261117.json) and
[validation evidence](evidence/p1a-validation-input-preflight-20261117.json).
Text-free exports remain byte-identical to the approved corresponding population files;
raw text is retained verbatim only in memory for future inference calls. No tokenizer,
normalization, model or official-test source was used by these preflights.

### EXP-005 - Development input validation

November 17, 2026; automated implementation and independent review. The loader read
hash-verified official training/validation source files to verify every approved input;
prompt text was not displayed/exported or interpreted as instructions. Reference labels
were kept separate from internal inference inputs. Boundary tests used invented fixtures.
No official-test raw source or model outcomes were read. Prior external history remains
unknown beyond existing statements; D-009 removes attestation waits, not that limitation.

### ASSET-002 / SPLIT-001/002 native tokenizer follow-up

V-034/V-035 and R-P1-A-20261117-07 complete actual tokenizer/config execution for both
development populations. The verified wrapper is Qwen2TokenizerFast (Transformers 4.57.1,
tokenizers 0.22.2); Python 3.13.5 on Explorer, Unicode database 15.1.0. It applies intrinsic
NFC while the input loader preserves original text/hashes. Explicit call settings control
padding/truncation and add no automatic BOS/EOS or chat template. ASSET-002's seven source
hashes remain unchanged. Actual model-config defaults and source hashes are in the
[native summary](evidence/p1a-native-tokenizer-summary-20261117.json).

All 18,909 training and 1,000 validation rows have complete original token lengths and
candidate-cap diagnostics. Raw per-ID counts/hashes (without text/tokens) remain at
`outputs/runtime-20261117/attempt-04/tokenizer-audit-native/`; summary/manifest/output hashes
and retrieval receipt bind them. RESULTS RES-003 owns the aggregate observations/proposal.
This establishes neither held-out token lengths nor model output/precision behavior.

### EXP-006 - Approved native development tokenization

Yash approved the Explorer CPU-only route in D-010. The reviewed package copied only
development sources, tokenizer/configuration assets, code and provenance to his private
scratch run directories; no credentials, classifier weights or official-test source/membership
files were included. The actual successful job tokenized both development populations;
the reviewer saw text-free IDs/counts and invented synthetic vectors, not real prompts or
tokens. Four job attempts and their failures are preserved. No test or classifier performance
was accessed. Unknown external history remains a limitation rather than an attestation wait.

### ASSET-001 official-test token-length completion

D-011 authorized only aggregate original official-test token-length administration after
the development-only run. V-037/V-038 and R-P1-A-20261117-08 cover all 23,516 rows of source
SHA-256 `526207c2485829d9961407011d7f4cd929569e7f285dc8396b3f385e0608bc70`. The total histogram
and summary are [retained evidence](evidence/p1a-official-test-token-lengths-20261117.json);
independent arithmetic/identity review is linked in V-038. No A/B or class-length breakdown,
cap comparison, row linkage or model output was produced. These statistics are not a
development-selection population and did not select the previously proposed pilot cap.

Together with the verified native development run, all 43,425 source rows now have token
length accounting under the same pinned wrapper/assets and explicit uncapped settings.
Source bytes, labels and SPLIT-001 through SPLIT-004 memberships are unchanged. P1-A's
closeout is in PHASE_RECORDS; performance-release freezes remain in force.

### EXP-007 - Separately approved official-test length administration

November 17, 2026; D-011 approval preceded transfer to a fresh private Explorer scratch
directory. The pinned test source was processed by the fixed administrative tokenizer
command only. The coordinator/reviewer received total length statistics, a total frequency
histogram, class-support validation and provenance. No prompts, row identities/hashes,
real token vectors, cap/A-B comparisons, scores or model performance were displayed/exported.
The existing inference input guards remain unchanged. The aggregate information must not
guide development choices; RES-003's pilot proposal preceded this access. Unknown external
history is still not a claim of universal non-exposure.

### ASSET-002 full checkpoint payload - P1-B verification

D-012 authorized full payload retrieval after the earlier header-only audit. The pinned
`model.safetensors` is now retained under `outputs/pilot-20261117/checkpoint-01/` with
`receipt.json`: 1,192,138,968 bytes and SHA256
`19701022d11e38d39bd77aed7263d2e9ce3a45ae29305248ef3de585f947511c`, exactly matching
ASSET-002's previously retained LFS metadata. The copied config is byte-identical to the
seven-file audit. The same full hash and config hash were independently recomputed after
transfer to private Explorer storage `pilot-checkpoint-20261117-01`. No credential was
transferred; weights are ignored, not published. This establishes payload identity, not
successful loading or effective precision, which remain the actual pilot's checks.

### PILOT-001 - D-012 training diagnostic membership

Prepared before any classifier outputs: `outputs/pilot-20261117/preparation-01/manifest.json`
SHA256 `405f6ccac8c923abf33d951e2ac4e31c7d2bae6e87fc5441912b8e0cd3c906e4`, with
`examples.jsonl` SHA256 `828cf651e2ccbeace777eb8936ab91fcbb888f7e903f22825b6c87163c222089`.
All 128 IDs come from the verified18,909-row eligible training population and prior native
length evidence. D-012 specifies deterministic quotas/order:64/class,48 short/eight mid/eight
long per class;16 selected rows truncate at1024. Labels remain separate from model inputs.
The manifest records source hashes, full coverage checks, membership/order/schedule hashes,
selection namespace and provisional preprocessing/threshold. It contains no prompts/tokens.
This deliberate class/tail enrichment is not representative sampling or a test result.
No earlier population is changed; all protected memberships/release conditions remain intact.

### EXP-008 - Authorized training pilot and result inspection

November 17, P1-B, D-012. The input loader revalidated the complete eligible training source
without displaying raw prompts. Only the preselected 128 training examples were passed to
the frozen detector in FP32/FP16/INT8; reference labels remained outside model calls. Agents
inspected saved logits/scores, reference labels, IDs, lengths and aggregate/paired errors
for that development sample. Synthetic pooling diagnostics used invented strings only.
No actual dataset prompt was displayed in this task's result review, and no official-test
source or model output was opened by the pilot. The earlier EXP-002 exposure and unknown
external/team history remain unchanged; no universal no-exposure claim is made.
