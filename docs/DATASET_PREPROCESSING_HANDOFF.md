# Dataset and preprocessing handoff

The dataset audit, protected partition design, and shared preprocessing for the
development pilot are complete. This handoff maps the dataset and preprocessing
owner's deliverables to the existing evidence.

## Dataset summary

PromptShield is pinned at `a5234cb1f5cdb256600cab64b8c961195b5e8404`. Each source
row has a nonblank string `prompt` and an integer `label` (0 benign, 1 injection).
The audit found no invalid labels or blank prompts. Stable example IDs use the
dataset revision, original split, and zero-based row position. Exact-text groups
use SHA-256 of the original decoded prompt re-encoded as UTF-8, with no trimming or
Unicode normalization. [Audit summary](evidence/p1a-data-summary-20261117.json) ·
[Source provenance](evidence/p1a-data-provenance-20261117.json)

| Official split | Rows | Benign | Injection | Exact-text groups |
|---|---:|---:|---:|---:|
| Train | 18,909 | 9,457 | 9,452 | 18,909 |
| Validation | 1,000 | 497 | 503 | 1,000 |
| Test | 23,516 | 17,030 | 6,486 | 23,359 |
| Total | 43,425 | 26,984 | 16,441 | 43,268 |

No exact-text group crosses official splits, so all training and validation rows
remain eligible. The official test contains 71 duplicate groups with 228 rows
(157 rows beyond the first occurrence in each group). All 71 groups are benign,
the largest has 58 rows, and no group has conflicting labels. Exact matching
cannot detect all paraphrases or shared templates. The label audit checks valid
encoding and group consistency. Individual annotation truth and prior external
exposure remain uncertain. [Data registry](DATA_REGISTRY.md)

| Protected population | Rows | Benign | Injection | Exact-text groups | Release condition |
|---|---:|---:|---:|---:|---|
| Test-A | 11,758 | 8,515 | 3,243 | 11,657 | Part 1 after the benchmark protocol freeze |
| Test-B | 11,758 | 8,515 | 3,243 | 11,702 | Part 2 after the final policy freeze |

The D-008 partition keeps whole duplicate groups together and has zero exact-group
intersections across the four eligible/protected populations. The registered
development loader accepts eligible training and validation only. The separately
authorized official-test tokenizer audit retained aggregate total lengths only.
Neither holdout has recorded model predictions. [Population manifests and hashes](evidence/p1a-partitions-20261117.json) ·
[Independent membership verification](evidence/p1a-partition-guard-revalidation-20261117.json)

## Lengths and shared preprocessing

The source audit retains character and UTF-8 byte summaries. Native tokenization
accounted for all 43,425 source rows using the pinned Sentinel v2 tokenizer
(`05ff9bfd1f28c5228e53121d5ee4427bb5205212`). The official-test summary covers
the entire official split in aggregate. Cap selection uses development data.
[Character and byte statistics](evidence/p1a-data-summary-20261117.json) ·
[Development token statistics](evidence/p1a-native-tokenizer-summary-20261117.json) ·
[Official-test token statistics](evidence/p1a-official-test-token-lengths-20261117.json)

| Development split | Median tokens | p95 | p99 | Max | Over 512 | Over 1,024 | Over 2,048 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Eligible train | 70 | 523 | 916 | 6,412 | 965 (5.10%) | 124 (0.66%) | 11 (0.06%) |
| Eligible validation | 68.5 | 519 | 894 | 2,580 | 52 (5.20%) | 8 (0.80%) | 2 (0.20%) |

Across the full official test split, the median is 100 tokens, p95 is 581, p99 is
1,126, and the maximum is 8,317. These figures are aggregate administrative evidence.

The pilot uses the pinned fast tokenizer wrapper on the original prompt string
with `add_special_tokens=True`, `split_special_tokens=False`, right truncation at
1,024 tokens, no padding, and batch size one across all precision modes. No chat
template or manual EOS is added. The model's PAD setting stays unset so the original
final-token pooling behavior is preserved, including for genuine terminal EOS.
Native checks verified capped sequences against their uncapped prefixes. The 1,024
cap follows the development retention figures above. Main-study settings remain
open for P1-C, and padded batching requires a pooling and logit equivalence check.
[Tokenizer controls](RESULTS.md#res-003---native-development-lengths-and-explicit-tokenizer-controls) ·
[Shared preprocessing code](../precision_benchmark/preprocessing.py)

## Reproduction and checks

| Deliverable | Repository entry point |
|---|---|
| Source audit | [Audit code](../precision_benchmark/data_audit.py) and [audit command](USAGE.md#administrative-source-audits) |
| Split recreation and guarded input loading | [Partition builder](../precision_benchmark/partition_data.py), [input loader](../precision_benchmark/input_data.py), and [registered inputs](USAGE.md#population-construction-and-development-inputs) |
| Tokenization diagnostics | [Development tokenizer code](../precision_benchmark/tokenizer_audit.py) and [native diagnostic commands](USAGE.md#native-tokenizer-diagnostics) |
| Reproducible training pilot | [Selection code](../precision_benchmark/pilot_data.py), [manifest](evidence/p1b-pilot-20261117/pilot/manifest.json), [ordered IDs, labels and lengths](evidence/p1b-pilot-20261117/pilot/examples.jsonl), and [rerun instructions](USAGE.md#preparing-and-running-the-development-precision-pilot) |
| Split-overlap and label checks | [Source tests](../tests/test_data_audit.py), [partition tests](../tests/test_partition_data.py), [loader tests](../tests/test_input_data.py), and [validation evidence](VALIDATION_LOG.md) |

The deterministic pilot selects 128 eligible training examples: 64 per class,
with 48 short, eight medium, and eight long per class. Sixteen inputs truncate.
The portable bundle includes all 384 predictions so teammates can rerun the
offline comparison from a clean checkout. Native reruns require verified source and
tokenizer assets plus the checkpoint and GPU environment. Full population
manifests are generated artifacts with registered hashes. The pilot manifest and
ordered examples are checked into Git.

```sh
python -m unittest tests.test_data_audit tests.test_partition_data tests.test_input_data tests.test_tokenizer_audit tests.test_holdout_lengths tests.test_pilot_data tests.test_pilot_inference -q
python -m precision_benchmark --manifest docs/evidence/p1b-pilot-20261117/comparison.json --output outputs/pilot-reanalysis-new
```

Use a fresh output directory. To own the next decision, bring the development-only
cap comparison and the verified unpadded reference policy to P1-C. Record the
agreed setting and rationale before Test-A release. Keep source labels and
memberships tied to the registered revision and document any preprocessing change
that makes earlier predictions incompatible.
