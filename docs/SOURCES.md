# Sources and verification register

Use primary sources to ground asset identities and methodological choices. These source descriptions were checked on **2026-10-27**. Moving documentation does not replace immutable model/data revisions or a recorded execution environment. Recheck the relevant source when implementation depends on an API or compatibility claim.

## Selected assets and methods

| Source | What it supports | What the project must still establish |
|---|---|---|
| [Sentinel v2 model card](https://huggingface.co/rogue-security/prompt-injection-jailbreak-sentinel-v2) | Selected classifier identity, Qwen3-0.6B basis, sequence-classification interface, `jailbreak` output example, gated access and publisher's Elastic-license statement. | Exact pinned labels/head, tokenizer behavior, released/effective dtypes, applicable access terms, treatment compatibility and measured performance. |
| [Sentinel paper](https://arxiv.org/abs/2506.05446) | Context for the original ModernBERT-based Sentinel approach. | This paper is not an exact architecture specification for Qwen3-based Sentinel v2. The v2 checkpoint's full training provenance and overlap with PromptShield remain uncertain. |
| [PromptShield dataset card](https://huggingface.co/datasets/hendzh/PromptShield) | Prompt/label task, benign/injection encoding, official splits and Apache-2.0 listing. The displayed dataset size is approximately 43,000 examples. | Actual pinned counts/schema, label support, duplicates, lengths, eligibility rules and A/B manifests. One illustrative JSON row uses an inconsistent `flag` key; inspect actual data rather than copying that example. |
| [PromptShield paper, arXiv:2501.15145v2](https://arxiv.org/abs/2501.15145v2) | Benchmark motivation and the importance of false-positive behavior in prompt-injection detection. | The project's sequential A/B evaluation and validation discipline must be described explicitly; they are project design choices, not automatically the paper's protocol. |
| [Transformers bitsandbytes documentation](https://huggingface.co/docs/transformers/quantization/bitsandbytes) | LLM.int8() loading, retained floating-point operations, configuration and offload/backend guidance. | Actual installed backend behavior, converted layers, retained head precision, speed and memory for this classifier. |
| [LLM.int8() paper, arXiv:2208.07339v2](https://arxiv.org/abs/2208.07339v2) | Mixed-precision handling of outlier features and quantization-method background. | Findings for other models do not establish benefits for Sentinel v2 or for the learned gate. |
| [Hugging Face Hub download guide](https://huggingface.co/docs/huggingface_hub/guides/download) | Revision-specific asset identification and cache behavior. | Exact model/tokenizer/dataset versions and hashes retained by the project. |

## Pinned administrative evidence checked November 17, 2026

The initial source table above is historical background. The following source retrievals
support ASSET-001/002 and V-008/V-009; exact URLs/bytes/hashes are retained in their evidence.

- **PromptShield:** [pinned source card](https://huggingface.co/datasets/hendzh/PromptShield/blob/a5234cb1f5cdb256600cab64b8c961195b5e8404/README.md) and revision-specific `train.json`, `validation.json`, `test.json` plus Hub metadata. Card declares benign/injection 0/1 semantics and Apache-2.0 metadata. Actual counts/schema/duplicate facts come from the project's full-file audit, not the page's approximate size or illustrative row. Access was public and ungated.
- **Sentinel v2:** [pinned model card](https://huggingface.co/rogue-security/prompt-injection-jailbreak-sentinel-v2/blob/05ff9bfd1f28c5228e53121d5ee4427bb5205212/README.md), [pinned license](https://huggingface.co/rogue-security/prompt-injection-jailbreak-sentinel-v2/blob/05ff9bfd1f28c5228e53121d5ee4427bb5205212/LICENSE.md), and pinned Hub model API metadata. Provider metadata declares Qwen3 sequence classification and F16 parameter storage; retained source license is Elastic License 2.0. Gated configuration/tokenizer retrievals returned 401, leaving actual output index/head semantics unverified.
- The HTML dataset page incidentally returned training-viewer snippets; EXP-002 records exposure and its exact-overlap check. Future administrative inspection should use pinned API/raw files through aggregate-only scripts. Neither source card establishes the project's test allocation, scientific phase completion or actual precision/runtime behavior.

## Citation records

Cite the exact model and dataset cards as well as relevant papers. Add versions of software actually used when preparing the final report; do not cite a dependency merely because it was considered.

- Dror Ivry and Oran Nahum. *Sentinel: SOTA model to protect against prompt injections*. 2025. arXiv:2506.05446. [Paper](https://arxiv.org/abs/2506.05446).
- Dennis Jacob, Hend Alzahrani, Zhanhao Hu, Basel Alomair, and David Wagner. *PromptShield: Deployable Detection for Prompt Injection Attacks*. 2025. arXiv:2501.15145v2; ACM CODASPY 2025. [Paper](https://arxiv.org/abs/2501.15145v2).
- Tim Dettmers, Mike Lewis, Younes Belkada, and Luke Zettlemoyer. *LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale*. NeurIPS 2022. arXiv:2208.07339v2. [Paper](https://arxiv.org/abs/2208.07339v2).

The quantization method's publication date is separate from the recency of the classifier and benchmark. Changes to the selected method or assets follow the scope rules in the [README](../README.md).

## Literature work during Part 2

Before finalizing the learned-gate formulation, conduct a bounded literature review of selective prediction, classifier cascades, budgeted inference, confidence calibration and cost-sensitive routing. Look for closely related mixed-precision routing studies as well. Use primary papers and official implementations where available. The goal is to understand prior art, identify meaningful baselines and state the project's actual contribution—not to claim novelty from an incomplete search.

For each relevant source, add an entry with title/authors/year, stable link, problem setting, routing signal/target, cost definition, evaluation design, relationship to this project and any adaptation proposed. Separate directly reproduced methods from inspiration. Record unresolved novelty questions in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) and resulting design decisions in [DECISIONS.md](DECISIONS.md).

Do not delay all development for an unlimited survey. Revisit the literature when evidence changes the formulation or when a new claim of novelty is proposed. A useful empirical result can be valuable without inventing a claim that the general concept of learned routing is new.

## Evidence and attribution rules

1. Distinguish source facts, project design choices, measured results and interpretations. An asserted fact needs an appropriate source or direct project evidence.
2. Publisher benchmark values are not this project's reproduced results or acceptance targets.
3. A model family's paper does not establish an exact checkpoint's labels, precision, preprocessing or training contamination status. Source findings motivate hypotheses; the project's own evidence supports its empirical claims.
4. Track the source/version used when a relevant method or API decision changes. Link the decision to the affected phase and experiments.
5. Attribute the Test-A/Test-B design to this project's [research protocol](RESEARCH_PROTOCOL.md), not to PromptShield's original benchmark.
6. Citation does not grant redistribution rights. Access, credentials and publication follow [AGENTS.md](../AGENTS.md); asset-specific terms and their verification belong in [DATA_REGISTRY.md](DATA_REGISTRY.md).

## Authenticated pinned configuration follow-up — November 17

V-012 retains [the pinned model config](https://huggingface.co/rogue-security/prompt-injection-jailbreak-sentinel-v2/blob/05ff9bfd1f28c5228e53121d5ee4427bb5205212/config.json)
retrieved through the approved browser. Its declarations establish configured label names
and task type; they do not establish actual tensor shape or runtime precision/pooling.
ASSET-002 owns the source identity and limitations. For V-013's optional local credential
lookup, the official [Hub environment-variable guide](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables)
and [token guide](https://huggingface.co/docs/hub/security-tokens) were checked on November 17.
The implementation uses existing credentials only; it creates no account, token or grant.

## Pinned implementation and authenticated artifact follow-up — November 17

Transformers 4.57.1 resolves to commit `8cb5963cc22174954e7dca2c0a3320b7dc2f4edc`;
[source receipts](evidence/p1a-library-sources-20261117.json) identify all 12 inspected files.
The [shared classifier implementation](https://github.com/huggingface/transformers/blob/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/modeling_layers.py)
establishes the inspected pooling/head behavior, and the pinned tokenizer/pipeline files
establish wrapper handling and score selection. V-016 distinguishes source interpretation
from execution and from the checkpoint's recorded development-version provenance.

V-022 retrieved the exact selected repository's full tokenizer files and actual checkpoint
header through authenticated access. The provider content identities and project-computed
hashes are retained separately; no full weight checksum or runtime outcome is inferred.
ASSET-002 owns the values. Original Elastic License 2.0 terms are copied unchanged in
`third_party/SENTINEL_LICENSE.md` alongside reproduced configuration metadata; source
assets and tensor payloads remain excluded from the repository publication candidate.
