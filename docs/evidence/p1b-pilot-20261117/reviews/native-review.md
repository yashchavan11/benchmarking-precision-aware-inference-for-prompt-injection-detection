# Independent native three-precision pilot review

November 17, 2026, America/New_York; automated reviewer
`/root/secure_model_access`. Reviewed actual retained FP32, FP16 and INT8 runs under
`outputs/pilot-20261117/attempt-01/runs/` for allocation 11959388. FP32/FP16 were
available first; the final checks below include the subsequently completed INT8
run. No raw prompts, official-test source/performance, native inference rerun or
network operation was used by this reviewer. No production code was modified.

**Disposition:** all three complete runs passed the independent retained-evidence
checks described below. No blocking validity defect was found. The evidence
supports the bounded D-012 training pilot; it does not establish a final benchmark,
representative performance estimate, deployment speedup or completed learned gate.

## Identity, coverage and independent scoring

All run completion markers, execution states, referenced artifact/prediction hashes
and current executed-source hashes match. Each run covers exactly the same 128
selected IDs once, in the reviewed original source order. Separate example labels
were joined by ID. The approved pilot manifest remains
`405f6ccac8c923abf33d951e2ac4e31c7d2bae6e87fc5441912b8e0cd3c906e4`.
All three share the checkpoint identity, tokenizer/data revisions, provisional 0.5
threshold, preprocessing, population, actual schedule, code and environment IDs.

The recorded full checkpoint verification matches the earlier complete retrieval
receipt: 1,192,138,968 bytes, SHA-256
`19701022d11e38d39bd77aed7263d2e9ce3a45ae29305248ef3de585f947511c`.
The reviewer reused this receipt and inspected the executed streaming-hash/load
checks; it did not reread the entire checkpoint payload. Loaded parameter names and
shapes were independently compared with the retained checkpoint header.

The common actual token-schedule SHA-256 is
`6801a8fc3226b9fc632b1e93a50be9cab327623230b130a9dc6ed861c0d2ba57`.
The effective schedule ID independently recomputes from this hash and the planned
schedule. Real token vectors were intentionally not exported; equality of actual
token hashes and the executed token/length/prefix checks support matched inputs,
not an independent second tokenization by the reviewer.

All 384 saved logits/scores are finite. Logits lie on the declared FP32 or FP16
representation grid, and all scores are representable in FP32 within [0,1]. A
separate standard-library reference rounds the stable two-logit softmax steps to
FP32 and selects output index 1. An absolute tolerance of `2e-7` was specified
before checking, allowing CUDA exp/reduction rounding rather than requiring a
bit-identical scalar implementation. Maximum discrepancies were `2.9802322387695312e-8`
for FP32 and `5.960464477539063e-8` for FP16/INT8. Every prediction equals
`int(score >= 0.5)`. This checks injection-score orientation, not top-label confidence.

| Run | Run-manifest SHA-256 |
|---|---|
| FP32 | `74d887efe9950333bdbee0997c7dec55440379c00df53f6b4a9b6cc9b0cf21a9` |
| FP16 | `8ab299832a3e826414c2a7de94bdb51f79f1c495ce930b04619b1d6d833af00e` |
| INT8 | `04faf391c05ffcbe1dc915c844d3b190b72bb34ac579078b900404872a75cd5a` |

## Actual treatment and pooling evidence

Every run reports and independently accounts for all 311 parameter tensors and
596,051,968 parameter elements, with header-matching shapes, frozen gradients and
CUDA placement. All 427 recorded modules are in evaluation mode; loading reports
no missing, unexpected, mismatched or failed keys. Each run retains a standard
unquantized bias-free `[2,1024]` classifier head.

- **FP32:** all parameters, observed projection/norm outputs, head and output logits
  are FP32; no converted modules are present.
- **FP16:** all parameters, observed projection/norm outputs, head and output logits
  are FP16; no converted modules are present.
- **INT8:** exactly the intended 196 attention/MLP projections across 28 layers are
  `Linear8bitLt`, with INT8 weight tensors, threshold 6 and no retained FP16 weight
  state. Every recorded CB matrix/SCB scale shape/dtype/device matches its projection.
  Residual parameters, embeddings, norms and the excluded head are FP16; projection
  input/output hooks and output logits are FP16. SCB scales are FP32.

The rotary frequency buffer is FP32 in all treatments. The 311 per-module synthetic
I/O records each contain four executed calls with the expected input/output dtypes.
These are storage and boundary observations, not proof that every internal operation
uses the treatment's nominal dtype. The pinned Qwen3 source explicitly retains
FP32 normalization/rotary/attention-softmax computations where applicable; hooks
do not measure every internal arithmetic operation. Runtime model/config source
hashes match the retained official 4.57.1 sources. Bitsandbytes integration/quantizer
hashes are additionally retained as runtime identity evidence.

The actual synthetic head-hook tests include ordinary text, interior EOS, terminal
EOS and EOS-only inputs. Returned logits exactly matched the final-token head output
under the original unset model PAD setting. Structural index/mask/EOS evidence was
independently checked. Empty/invalid-mask guards passed, and the intended padded
batch of two raised the exact no-PAD exception. This establishes the original
unpadded batch-one path and rejection boundary; padded-batch equivalence was not
established and no padding policy was silently changed.

## Environment and observed results

All treatments use the identical NVIDIA L40S (compute capability 8.9), UUID
`89c465de-94fe-63ac-d64d-3314c559b8d9`, CUDA device 0 and allocation 11959388.
Versions are torch 2.9.1+cu126, Transformers 4.57.1, tokenizers 0.22.2,
bitsandbytes 0.48.2, accelerate 1.11.0 and safetensors 0.8.0. Eager attention,
disabled TF32/unintended autocast/reduced-precision reduction, and the highest FP32
matmul setting agree across runs. Deterministic algorithms were not enabled.
The retained remote gate contains 107 passing tests and a clean dependency check.

Independent confusion counts against the separate labels:

| Treatment | TN | FP | FN | TP | Correct / 128 |
|---|---:|---:|---:|---:|---:|
| FP32 | 63 | 1 | 30 | 34 | 97 |
| FP16 | 63 | 1 | 30 | 34 | 97 |
| INT8 | 63 | 1 | 29 | 35 | 98 |

FP16 has no label disagreement with FP32. INT8 has one correction and no newly
introduced error: original training row 3949, reference class 1, moves from
FP32 score `0.4914744794368744` to INT8 `0.5186528563499451`. All other labels agree.
The maximum absolute score shifts versus FP32 are approximately 0.006274 for FP16
and 0.092252 for INT8. Higher precision was treated as a baseline, not ground truth.

## Resource arithmetic and limits

All 128 per-treatment timing samples have matching IDs/effective lengths, batch one,
repetition zero and positive finite durations. Median and nearest-rank p95 values
independently recompute. Warm-up is the same first three planned examples. Memory
peaks are consistent with their post-warm-up baselines and allocated/reserved bounds.

| Treatment | Median forward ms | p95 forward ms | Peak allocated MiB | Loading seconds |
|---|---:|---:|---:|---:|
| FP32 | 25.511499 | 59.678756 | 2482.782227 | 6.698511 |
| FP16 | 26.267216 | 27.000487 | 1321.416992 | 0.866793 |
| INT8 | 87.487037 | 93.480418 | 932.557617 | 32.258570 |

The summed reported parameter storage is 2,384,207,872 / 1,192,103,936 /
751,702,016 bytes respectively. Those sums exclude additional state/buffers and
must not be presented as serialized model size or complete GPU/process memory.

Forward timing starts with device-resident tensors and ends after synchronized raw
logits. It excludes tokenization, transfers, score conversion, checksum verification,
library startup and other setup/synthetic work. Loading is a separate local-cache
observation. Allocator peaks are not total device/host-process memory. A single
fixed-order, tail-enriched pilot with three warm-ups is not the later repeated,
rotated profiling study; no final speedup, end-to-end latency, statistical quality
gain or cascade-cost claim follows. The observed INT8 forward medians are slower
in this pilot and are not omitted or described as a speed benefit.

The 128 examples are deliberately class-balanced and tail-enriched training data,
with 16 truncated inputs, not a representative or held-out population. Threshold
0.5 remains provisional. No official-test performance, main-study freeze or learned
gate result is established by this review. Model reruns and a new empirical job
were not needed to verify these retained artifacts.
