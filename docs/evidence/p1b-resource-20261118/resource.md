# Pilot resource summary (regenerated offline)

Scope: Offline regeneration of single-pass pilot resource observations; no model run. Development feasibility only, not a final or controlled speed/memory benchmark.

Workload: 128 matched training examples, batch size 1, effective tokens 9-1024 (median 83.0); order fp32, fp16, int8 (fixed, separate fresh processes, same allocation). Hardware: NVIDIA L40S, CUDA 12.6.

| Treatment | Median forward (ms) | p95 forward (ms) | Max forward (ms) | Peak allocated (MiB) | Parameter storage (MiB) | Derived forward-only rate (ex/s) |
|---|---:|---:|---:|---:|---:|---:|
| FP32 | 25.51 | 59.68 | 60.14 | 2482.78 | 2273.76 | 31.62 |
| FP16 | 26.27 | 27.00 | 493.05 | 1321.42 | 1136.88 | 31.20 |
| INT8 | 87.49 | 93.48 | 264.10 | 932.56 | 716.88 | 11.18 |

Median forward time by effective-token band:

| Treatment | 1-128 tokens | 129-512 tokens | 513-1024 tokens |
|---|---:|---:|---:|
| FP32 | 25.45 (n=80) | 25.26 (n=16) | 56.01 (n=32) |
| FP16 | 26.26 (n=80) | 26.42 (n=16) | 26.16 (n=32) |
| INT8 | 86.68 (n=80) | 88.67 (n=16) | 91.92 (n=32) |

Boundaries:

- **forward**: Pretokenized device-resident tensors to raw logits, synchronized before/after; excludes transfers/tokenization/score conversion
- **memory**: PyTorch max_memory_allocated/reserved after reset following warm-up; covers resident weights plus the post-warm-up input, forward and score-conversion allocations. Not total device, driver/context or host memory.
- **loading**: Populated local checkpoint to device; no download/hash verification
- **warmup**: {"batches": 3, "schedule": "first three planned IDs in order"}
- **p95**: Nearest rank: sorted[ceil(0.95 * n) - 1]; median is the conventional median.
- **rate**: Derived forward-only rate = number of samples / sum of their synchronized forward durations. Not a measured wall-clock, sustained or end-to-end throughput; not 1 / median latency.

Warm-up inputs had 63, 92, 12 tokens; 59 of 128 timed samples are longer than any warm-up input.
INT8 parameter storage excludes its 1.31 MiB of float32 LLM.int8 scale state (SCB).
