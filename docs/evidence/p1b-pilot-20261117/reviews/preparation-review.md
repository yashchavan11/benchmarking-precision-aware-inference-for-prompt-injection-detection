# Independent D-012 pilot preparation review

November 17, 2026, America/New_York; automated reviewer
`/root/secure_model_access`. Read-only review of `pilot_data.py`, its six synthetic
tests, the actual preparation artifacts, source evidence and the inference ingestion
interface. No source edits, raw prompt/test-source reads, model outputs, native
imports, network requests or tokenization/model reruns occurred in this review.

**Disposition:** passed for this prepared population and ingestion contract. No
blocking population defect was found. This does not establish inference correctness,
effective precision, successful GPU execution or a completed P1-B phase.

## Actual identities and independent reconstruction

Reviewed artifacts:

- Manifest: `outputs/pilot-20261117/preparation-01/manifest.json`, SHA-256
  `405f6ccac8c923abf33d951e2ac4e31c7d2bae6e87fc5441912b8e0cd3c906e4`.
- Examples: `outputs/pilot-20261117/preparation-01/examples.jsonl`, SHA-256
  `828cf651e2ccbeace777eb8936ab91fcbb888f7e903f22825b6c87163c222089`.
- Preparation source: `1eaded1eb6dceba61af662eeb133166be3bb481bb86890ea6cefae5419a7a1b3`;
  test source: `cfc9d8d5deee89655c9247ca465468f11c22fcf712a51fd6f60c9243befe2502`.

An independent inline standard-library checker verified all five referenced
population/native-audit file hashes against the retained files and their previously
reviewed identities. It checked the D-008/D-009 chain, original training source hash,
complete 18,909-ID native coverage, original source positions, labels, unique exact
groups, and every retained original/capped length flag. Only text-free metadata and
length records were used; the raw training file was not reopened.

Selection was reconstructed without importing the preparation selector: assign each
original length to the exact D-012 stratum, calculate binary SHA-256 priority for
`namespace:label:stratum:example_id`, sort by priority then ID, take the fixed quota,
and filter the original source order. The namespace is exactly
`precision-aware-inference:p1b-pilot:v1:20261117`.

| Reference class | Original length stratum | Available | Selected |
|---|---|---:|---:|
| 0 | <=512 | 9,003 | 48 |
| 0 | 513–1024 | 382 | 8 |
| 0 | >1024 | 72 | 8 |
| 1 | <=512 | 8,941 | 48 |
| 1 | 513–1024 | 459 | 8 |
| 1 | >1024 | 52 | 8 |

All 128 independently selected IDs exactly match the manifest/examples and original
source order. There are 64 examples per class and 16 truncated at cap 1024. Every
example preserves its source identity, reference label and raw-text hash, and its
effective length equals `min(original_tokens, 1024)`. No backfill, duplicated group,
test membership or model-output-dependent selection was found.

The checker independently reproduced these identities:

- Ordered IDs: `a151a17e213649abd260545ec998ca364bdb8205d52f41cb66ac9eb93062b07c`.
- Sorted membership: `29c3acc60ec3ab635668ba80b1607e77c31ad1d20e3ae04068f13b044d9d4bfe`.
- Preprocessing contract: `sha256:a9826109d5475df7011cbe6e91b27e8d4b1da0cf3621d5fa83f997112ee4026e`.
- Input schedule: `sha256:2958a7a37e949b14f10cd6522fcdd4da66cc656013cf350c03c923780db30802`.

## Method and interface review

The source requires full training membership/native-length coverage and hash
consistency before selection. It rejects malformed labels, nonpositive/noninteger
lengths, cap inconsistencies, missing/duplicated/reordered length rows, duplicate
training groups and insufficient strata. It refuses existing output directories.
The six inspected tests cover fixed known-answer selection, stratum edges,
reproducibility/identities, integrity failures, bad source contracts and refusal to
backfill. The retained verification records six passing tests bound to the inspected
source/test hashes; this review did not repeat that suite.

Metadata matches D-012: eligible training only, pinned model/tokenizer/data revisions,
cap 1024, original unpadded batch one, right truncation, no chat template/manual EOS,
unset model PAD, injection index 1 and `p_injection`. Threshold 0.5 is explicitly
provisional and not validation-selected. The main-study-freeze and model-execution
flags remain false. Asset hashes match the independently verified native audit.

The actual manifest was passed to `pilot_inference.load_pilot` with its exact expected
SHA. It returned the same 128 rows and accepted all required declarations. The
preprocessing options also exactly match that consumer's current contract. No torch,
Transformers, tokenizers or regex module was imported by this interface check.
The inference source at that check had SHA-256
`2b82e32e4ccaae83e5079523bf076873ec38ceb723070072e74b8145165b179d`;
this check covers ingestion only, not the native inference implementation.

## Limits

The fixed class/length quotas deliberately enrich tails. Pilot quality is a
feasibility/diagnostic observation, not a representative training-population or
held-out performance estimate. No threshold was selected on validation and no
held-out statistic or classifier outcome entered selection. Input identity hashes
do not themselves verify the eventual token vectors, numerical treatment, score
conversion, device allocation or complete predictions; those remain execution and
inference-review requirements. The prepared artifacts are valid for the reviewed
scope and version, not automatically for later changed settings.
