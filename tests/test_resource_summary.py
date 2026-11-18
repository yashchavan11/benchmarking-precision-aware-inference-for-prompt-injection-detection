"""Offline resource-summary checks using invented timings plus the retained pilot bundle."""
import json
import math
from pathlib import Path
import statistics
import tempfile
import unittest

from precision_benchmark import pilot_inference
from precision_benchmark import resource_summary as target

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "docs/evidence/p1b-pilot-20261117/comparison.json"
MIB = 2 ** 20

# Ten invented examples: lengths cover all three bands; three warm-ups are the first three.
TOKENS = [12, 63, 92, 10, 200, 300, 600, 1024, 40, 128]
BASE_MS = {"fp32": [20, 21, 22, 23, 24, 25, 40, 60, 26, 27],
           "fp16": [21, 21, 21, 21, 21, 21, 21, 400, 21, 21],
           "int8": [80, 81, 82, 83, 84, 85, 86, 250, 87, 88]}
PEAK = {"fp32": 2400 * MIB, "fp16": 1300 * MIB, "int8": 900 * MIB}


def build(root, mutate=None):
    """Write a three-run bundle with a valid hash chain; mutate(precision, files) may alter content."""
    root = Path(root)
    runs = []
    for precision in target.PRECISIONS:
        directory = root / "runs" / precision
        directory.mkdir(parents=True)
        durations = [ms / 1000 for ms in BASE_MS[precision]]
        samples = [{"example_id": f"synthetic:{i}", "effective_tokens": tokens, "batch_size": 1,
                    "repetition": 0, "forward_seconds": seconds}
                   for i, (tokens, seconds) in enumerate(zip(TOKENS, durations))]
        files = {
            "feasibility.json": {
                "forward_boundary": "synthetic boundary", "loading_scope": "synthetic", "loading_seconds": 1.5,
                "warmup": {"batches": 3, "schedule": "first three"},
                "memory": {"peak_allocated_bytes": PEAK[precision], "peak_reserved_bytes": PEAK[precision] + MIB},
                "memory_baseline_after_warmup": {"allocated_bytes": PEAK[precision] - 100 * MIB,
                                                 "reserved_bytes": PEAK[precision]},
                "samples": samples, "median_forward_seconds": statistics.median(durations),
                "p95_forward_seconds": sorted(durations)[math.ceil(0.95 * len(durations)) - 1]},
            "environment.json": {"gpu_name": "Synthetic GPU", "gpu_uuid": "gpu-1", "allocation_id": "1",
                                 "cuda_runtime": "0.0", "versions": {}, "flags": {}},
            "precision-evidence.json": {
                "parameters": [{"storage_bytes": {"fp32": 400, "fp16": 200, "int8": 120}[precision]}],
                "quantized_linear_modules": ([{"state_tensors": [{"name": "state.CB", "storage_bytes": 64},
                                                                 {"name": "state.SCB", "storage_bytes": 8}]}]
                                             if precision == "int8" else [])},
        }
        if mutate:
            mutate(precision, files)
        for name, value in files.items():
            pilot_inference.write_json(directory / name, value)
        run = {"precision": precision, "status": "complete",
               "artifact_sha256": {name: pilot_inference.file_hash(directory / name) for name in files}}
        pilot_inference.write_json(directory / "run.json", run)
        runs.append({"path": f"runs/{precision}/run.json", "sha256": pilot_inference.file_hash(directory / "run.json")})
    manifest = root / "comparison.json"
    pilot_inference.write_json(manifest, {"schema_version": 1, "runs": runs})
    return manifest


class SyntheticResourceTests(unittest.TestCase):
    def test_regenerates_quantiles_rate_bands_memory_and_ratios(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = target.summarize(build(temp))
        fp32, fp16, int8 = (summary["treatments"][p] for p in target.PRECISIONS)
        self.assertAlmostEqual(fp32["median_ms"], 24.5)
        self.assertAlmostEqual(fp32["p95_ms"], 60.0)  # nearest rank: ceil(9.5)-1 = index 9 of 10
        self.assertAlmostEqual(fp16["max_ms"], 400.0)
        self.assertEqual(fp16["max_sample"]["effective_tokens"], 1024)
        # Rate is n / sum(durations), deliberately different from 1 / median.
        self.assertAlmostEqual(fp16["derived_forward_only_rate_per_s"], 10 / ((9 * 21 + 400) / 1000))
        self.assertNotAlmostEqual(fp16["derived_forward_only_rate_per_s"], 1000 / fp16["median_ms"], places=1)
        self.assertEqual([b["n"] for b in fp32["length_bands"]], [6, 2, 2])
        self.assertAlmostEqual(fp32["length_bands"][2]["median_ms"], 50.0)
        self.assertEqual(fp32["warmup_tokens"], [12, 63, 92])
        self.assertEqual(fp32["samples_longer_than_any_warmup"], 5)
        self.assertAlmostEqual(int8["peak_allocated_mib"], 900)
        self.assertAlmostEqual(int8["workload_increment_allocated_mib"], 100)
        self.assertEqual(int8["quantization_scale_state_mib"], 8 / MIB)  # SCB only; CB aliases the weight
        self.assertAlmostEqual(summary["ratios_vs_fp32"]["int8"]["peak_allocated_vs_fp32"], 900 / 2400)
        self.assertAlmostEqual(summary["ratios_vs_fp32"]["fp32"]["median_latency_vs_fp32"], 1.0)
        self.assertEqual(summary["workload"]["examples"], 10)

    def test_tampered_feasibility_fails_hash_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = build(temp)
            path = Path(temp) / "runs/int8/feasibility.json"
            data = json.loads(path.read_text())
            data["memory"]["peak_allocated_bytes"] = 1
            pilot_inference.write_json(path, data)
            with self.assertRaisesRegex(ValueError, "hash"):
                target.summarize(manifest)

    def test_unmatched_workload_is_rejected(self):
        def shorten(precision, files):
            if precision == "fp16":
                files["feasibility.json"]["samples"][4]["effective_tokens"] = 199
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "same examples"):
                target.summarize(build(temp, shorten))

    def test_recorded_median_must_match_raw_samples(self):
        def alter(precision, files):
            if precision == "fp32":
                files["feasibility.json"]["median_forward_seconds"] = 0.001
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "median"):
                target.summarize(build(temp, alter))

    def test_different_devices_are_rejected(self):
        def move(precision, files):
            if precision == "int8":
                files["environment.json"]["gpu_uuid"] = "gpu-2"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "devices"):
                target.summarize(build(temp, move))

    def test_cli_writes_tables_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = build(Path(temp) / "bundle")
            output = Path(temp) / "out"
            self.assertEqual(target.main(["--manifest", str(manifest), "--output", str(output), "--no-figure"]), 0)
            for name in ("resource_summary.json", "resource.csv", "resource_by_length.csv", "resource.md"):
                self.assertTrue((output / name).is_file(), name)
            self.assertIn("not 1 / median latency", (output / "resource.md").read_text(encoding="utf-8"))
            before = (output / "resource.csv").read_bytes()
            self.assertEqual(target.main(["--manifest", str(manifest), "--output", str(output), "--no-figure"]), 2)
            self.assertEqual((output / "resource.csv").read_bytes(), before)


@unittest.skipUnless(BUNDLE.is_file(), "Retained pilot bundle not present")
class RetainedPilotTests(unittest.TestCase):
    """Regression against RES-004 / V-043 values recorded from the native L40S run."""

    def test_retained_bundle_reproduces_recorded_resource_table(self):
        summary = target.summarize(BUNDLE)
        expected = {"fp32": (25.51, 59.68, 2482.78, 31.6177), "fp16": (26.27, 27.00, 1321.42, 31.1950),
                    "int8": (87.49, 93.48, 932.56, 11.1842)}
        for precision, (median, p95, peak, rate) in expected.items():
            t = summary["treatments"][precision]
            self.assertEqual(t["n"], 128)
            self.assertEqual(round(t["median_ms"], 2), median)
            self.assertEqual(round(t["p95_ms"], 2), p95)
            self.assertEqual(round(t["peak_allocated_mib"], 2), peak)
            self.assertEqual(round(t["derived_forward_only_rate_per_s"], 4), rate)
            self.assertEqual(t["warmup_tokens"], [63, 92, 12])
        self.assertEqual(summary["hardware"]["gpu"], "NVIDIA L40S")
        self.assertEqual(round(summary["treatments"]["fp16"]["max_ms"], 4), 493.0451)
        self.assertEqual(round(summary["treatments"]["int8"]["max_ms"], 4), 264.0951)


if __name__ == "__main__":
    unittest.main()
