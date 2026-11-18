# Retained P1-B development pilot

This is the complete text-free evidence for D-012 / RES-004 / V-039 through V-042,
not official-test performance or the final benchmark. All three treatments ran the same
128 class/length-stratified training examples on one L40S allocation. The provisional
threshold is 0.5, token cap 1024 and unpadded batch size 1. See ../../RESULTS.md for interpretation.

- `pilot/`: fixed reference IDs/labels/lengths and pre-output selection provenance.
- `runs/`: all 384 predictions, run manifests and native precision/pooling/environment/raw
  feasibility evidence. Predictions contain no real prompt text or token vectors.
- `comparison.json` and `analysis/`: reproducible offline descriptive comparison.
- `runtime/`: executed 107-test log, package lock/wheel provenance, source hashes and hardware.
- `reviews/`: independent automated preparation/native/arithmetic reviews; not human signoff.
- `executed-source-stage.zip`: the exact 50-file reviewed code/synthetic-fixture/pilot package
  used on the GPU, with its manifest/receipt. It contains no raw dataset, checkpoint or token.
  This preserves byte identity across platforms, including original source line endings.
  The final repository also adds the offline comparison assembler; it did not change the
  executed model or metric calculations.
- `inventory.json`: SHA256/size for every retained member except the inventory itself.

From the repository root, regenerate descriptive results without GPU, credentials or weights:

```sh
python -m precision_benchmark --manifest docs/evidence/p1b-pilot-20261117/comparison.json --output outputs/pilot-reanalysis-new
```

Use a new output directory. USAGE provides all-three inference and rerun assembly commands.
Raw source data and weights require the registered access/source terms and separate acquisition
or verified transfer. Do not infer access to ignored local/cluster files from this bundle.

FP32/FP16 each classify 97/128 correctly; INT8 classifies 98/128, with one corrected error.
Most errors are shared false negatives. INT8 has lower observed PyTorch allocated memory
but slower pilot median forward time. The sample is small and deliberately tail-enriched;
timing is one fixed-order pass after three warm-ups, not repeated/end-to-end profiling.
No statistical superiority, generalization, final speedup or gate benefit is established.
The main threshold/configuration freeze, Test-A study and full learned-gate/Test-B work remain.
