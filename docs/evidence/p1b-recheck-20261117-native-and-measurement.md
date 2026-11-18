# Fresh native-result and measurement recheck

November 17, 2026, America/New_York. Read-only skeptical review by
`/root/secure_model_access`, requested after the pilot milestone. This review
reopened the actual source, executed ZIP, bundled native artifacts, preparation
bindings, report tables and measurement protocol; it did not merely repeat the
earlier review's conclusion. No native/GPU run, raw/test prompt inspection, network
operation or source edit was performed.

**Conclusion:** no defect was found that invalidates the existing numerical quality
values for the declared 128-example training pilot. The published resource values
also remain valid as the recorded observations. There are substantive unimplemented
profiling capabilities and controls; they cannot be completed by relabeling or
formatting the existing table.

## Fresh evidence checks

- Verified the executed archive SHA-256
  `eda1261b459b25390bbe562e7e9155aebc8946cc038460f8246386f8e6c778b4`
  and all 50 listed source-file byte hashes. The five inference/helper files named
  in the native run manifests match the ZIP exactly and also match the current
  working files. This addresses source drift and line-ending ambiguity directly.
- Rechecked all five preparation-source references, the complete 18,909-row
  training identity/native-length join, and independently reconstructed the
  namespace/class/length hash selection. All 128 IDs, 64-per-class quotas, original
  order and source/raw-hash bindings match. No raw training file was reopened.
- Rechecked all three native prediction/artifact hashes and matching actual
  token-schedule, environment, code, preprocessing, checkpoint/revision and threshold
  identities. Saved logits are finite and scores agree with an independently
  calculated index-1 two-logit softmax within the established `2e-7` FP32-rounding
  allowance (largest fresh double-reference discrepancy approximately `5.84e-8`).
  Every prediction equals `int(score >= 0.5)`.
- Independently recalculated every numerical quality column: confusion counts,
  accuracy, both class metrics, macro-F1, FPR/FNR, direct pairwise tied-score AUC,
  Brier and explicitly bounded ten-bin ECE. All match `analysis/quality.csv` within
  `1e-12`. Counts remain FP32/FP16 TN=63, FP=1, FN=30, TP=34; INT8 TN=63, FP=1,
  FN=29, TP=35. No lower-precision run used a separately tuned threshold.
- Reopened the actual parameter/module evidence: 311 FP32 tensors in FP32; 311
  FP16 tensors in FP16; INT8 has 196 INT8 projection tensors and 115 FP16 residual
  tensors. All 596,051,968 elements are accounted for, frozen and on CUDA; module
  evaluation flags and clean loading information agree. The INT8 projection policy,
  floating head and mixed internal precision are declared rather than hidden.

The executed code hashes the full selected checkpoint before directory loading,
checks its config against the pinned assets, rejects missing/mismatched model keys,
and freezes the loaded classifier. Runtime labels and final-token synthetic head
checks support the chosen score/pooling interpretation. The full payload was not
rehydrated or rehashed by this reviewer; the verified retrieval receipt and executed
checksum checks were reused. Similarly, equal actual token hashes support cross-mode
input equality; real token vectors were deliberately not exported for independent
retokenization. These are explicit evidence limits, not discovered contradictions.

## What the measurements actually cover

The forward timer creates/transfers GPU input tensors **before** its synchronized
start. It stops after synchronized raw logits and **before** finite/dtype checking,
FP32 softmax, host transfer and artifact writing. That is a defensible forward-only
wall-time boundary. It is not request-level/end-to-end latency or GPU-kernel-only time.

The memory reset occurs once after warm-up. Its subsequent peak covers the inference
loop's input allocations, forward activations, score conversion and checks, not only
the forward-timer interval. It excludes the loading peak and CPU tokenization memory.
Reserved-memory baselines retain the allocator's previous cache; reset_peak_memory_stats
does not empty it. The records contain both baseline and peak allocated/reserved
values, so this scope can be reported accurately. Root's revised reporting text now
separates timer and memory boundaries; no numerical correction is required.

All warm-ups were the same three inputs of **63, 92 and 12 tokens**. Longer shapes
were not explicitly warmed. There is one measured forward sample per ID, repetition
zero, and fixed FP32→FP16→INT8 order. Large retained samples include FP16 493.045 ms
at 712 tokens, 153.230 ms at 213 tokens and 115.968 ms at 666 tokens; INT8 reaches
264.095 ms at 1024 tokens. Their cause cannot be identified from this one pass.
Shape-specific initialization, scheduling/contention and other effects remain
possibilities, not established explanations. No sample was discarded.

Median and p95 arithmetic are correct, but they must not be described as stable,
fully warmed performance rankings. Matched GPU UUID, inputs and environment are
necessary controls; they do not establish isolated GPU occupancy or remove
treatment-order/run-to-run effects. Seeds are fixed, but deterministic algorithms
were not enabled and bitwise repeatability was not measured.

The forward samples sum to 4.048368 / 4.103220 / 11.444682 seconds. Thus
`128 / sum(forward_seconds)` is 31.617676 / 31.195013 / 11.184234 examples/s. These
are **derived forward-only busy-time rates**, not measured completed-example
throughput. No common wall-window includes all request work. The execution records
span about 253.829 / 126.911 / 256.619 seconds and additionally include setup,
synthetic checks, warm-up, verification and per-row JSON writes/flushes. Dividing
128 by those spans would not repair the missing throughput measurement either.

## Substantive remaining profiling work

| Capability | Current evidence | Work still required |
|---|---|---|
| Forward latency/raw records | 128 synchronized samples per mode, IDs/lengths and median/p95 retained | Warm the actual relevant shapes; repeat matched schedules and rotate/randomize treatment order; retain trial/repetition identities and variability. |
| Completed-example throughput | No measured stream wall-window | Time a defined completed-request window at declared batch/concurrency, excluding or explicitly including instrumentation; count completed examples and optionally tokens. Do not substitute inverse median or the derived busy-time rate. |
| End-to-end latency | Absent | Add a separate tokenization→transfer→forward→score→host-visible-result boundary, keeping model loading separate. Keep evidence/log writing outside that boundary unless it is intentionally part of the measured system. |
| GPU memory | Actual post-warm-up allocator baseline/peaks | Keep this valid scope; separately measure loading/initialization peaks and repeated inference peaks if claiming broader memory behavior. Allocator counters are not total device/process memory. |
| Host memory | Absent | Record process RSS/peak with a declared sampling method and interval. |
| Footprint/storage | Parameter tensor-byte sums and original checkpoint identity | Account for buffers/quantized state without alias double-counting; measure saved representations if making serialized-size claims. No per-treatment quantized file was saved. |
| Final profiling population and design | Tail-enriched training pilot, batch one only | Implement the protocol's fixed representative eligible-validation profiling workload and selected shape/batch matrix. Current pilot runner is hard-coded to 128 training examples and is not that profiler. Larger batching requires the separate pooling/input-policy validation. |
| Statistical performance claim | Descriptive one-pass values only | Choose adequate repetitions/stability criteria and uncertainty before a final ranking; do not choose a favorable seed/order after observing results. |

For Hareeshwar's weekly allocation, GPU/environment reproducibility, scoped forward
latency, GPU allocator memory and raw sample records already have useful evidence.
The throughput item still needs either an explicitly labeled derived-only deliverable
or an actual measured throughput experiment, according to the agreed assignment.
Fully warmed repeated profiling is substantive technical work, not merely review or
presentation. The final protocol additionally requires the other boundaries and
controls above. This review does not assign a new teammate commitment or authorize
a new experiment.

## Claim disposition

Keep the existing confusion/quality values and raw resource observations. Do not
invalidate them because the desired speed benefit was absent, and do not rerun
quality inference merely to fix a report label. Correctly scoped current wording
is supported: INT8 had one more correct prediction and lower post-warm-up allocated
memory, while its observed median forward time was higher in this pilot.

Do not extend those facts to population-level accuracy, statistical superiority,
fully warmed speedup, end-to-end throughput, total deployment memory or learned-gate
benefit. The enriched training sample, provisional threshold, shared false negatives,
unknown upstream contamination/annotation truth and reserved evaluation boundaries
remain substantive limits. No fresh evidence here requires withdrawing the quality
table; the missing profiling work must be completed before stronger resource claims.
