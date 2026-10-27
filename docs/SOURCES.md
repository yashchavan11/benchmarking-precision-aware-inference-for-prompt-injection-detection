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
