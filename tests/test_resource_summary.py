"""Offline resource-summary checks using invented timings plus the retained pilot bundle."""
import json
import math
from pathlib import Path
import statistics
import shutil
import tempfile
import unittest
from unittest.mock import patch

from precision_benchmark import pilot_compare, pilot_inference
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
        # Invented values exercise arithmetic directly; they are not an accepted native pilot.
        with tempfile.TemporaryDirectory() as temp:
            build(temp)
            treatments = {}
            for p in target.PRECISIONS:
                directory = Path(temp) / "runs" / p
                treatments[p] = target.summarize_treatment({
                    "feasibility": json.loads((directory / "feasibility.json").read_bytes()),
                    "precision_evidence": json.loads((directory / "precision-evidence.json").read_bytes())})
        fp32, fp16, int8 = (treatments[p] for p in target.PRECISIONS)
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
        self.assertEqual(fp32["n"], 10)

    def test_tampered_feasibility_fails_hash_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = copied_bundle(Path(temp) / "bundle", lambda run, files: None)
            path = manifest.parent / "runs/int8/feasibility.json"
            data = json.loads(path.read_text())
            data["memory"]["peak_allocated_bytes"] = 1
            pilot_inference.write_json(path, data)
            with self.assertRaisesRegex(ValueError, "hash"):
                target.summarize(manifest)

    def test_unmatched_workload_is_rejected(self):
        def shorten(run, files):
            if run["precision"] == "fp16":
                files["feasibility.json"]["samples"][4]["effective_tokens"] = 199
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "Timing coverage"):
                target.summarize(copied_bundle(Path(temp) / "bundle", shorten))

    def test_recorded_median_must_match_raw_samples(self):
        def alter(run, files):
            if run["precision"] == "fp32":
                files["feasibility.json"]["median_forward_seconds"] = 0.001
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "median"):
                target.summarize(copied_bundle(Path(temp) / "bundle", alter))

    def test_different_devices_are_rejected(self):
        def move(run, files):
            if run["precision"] == "int8":
                files["environment.json"]["gpu_uuid"] = "gpu-2"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "Environment digest"):
                target.summarize(copied_bundle(Path(temp) / "bundle", move))

    def test_cli_writes_tables_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = copied_bundle(Path(temp) / "bundle", lambda run, files: None)
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
        self.assertAlmostEqual(summary["ratios_vs_fp32"]["int8"]["peak_allocated_vs_fp32"], 932.5576171875 / 2482.7822265625)
        self.assertEqual(summary["ratios_vs_fp32"]["fp32"]["median_latency_vs_fp32"], 1)

    def test_all_published_numerical_tables_are_unchanged(self):
        summary = target.summarize(BUNDLE)
        published = ROOT / "docs/evidence/p1b-resource-20261118"
        old = json.loads((published / "resource_summary.json").read_bytes())
        for field in ("treatments", "ratios_vs_fp32", "samples", "hardware", "boundaries"):
            self.assertEqual(summary[field], old[field], field)
        self.assertEqual(target._csv(target.resource_rows(summary)), (published / "resource.csv").read_text())
        self.assertEqual(target._csv(target.band_rows(summary)), (published / "resource_by_length.csv").read_text())

    def test_real_assembler_sibling_references_work_with_resource_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            assembly = Path(temp) / "comparison"
            pilot = BUNDLE.parent / "pilot/manifest.json"
            pilot_compare.compare_pilot(pilot, pilot_inference.file_hash(pilot), BUNDLE.parent / "runs", assembly)
            manifest = assembly / "comparison.json"
            self.assertIn("..", json.loads(manifest.read_bytes())["examples"]["path"])
            self.assertEqual(target.main(["--manifest", str(manifest), "--output", str(Path(temp) / "resources"),
                                          "--no-figure"]), 0)


def copied_bundle(root, mutate):
    """Relocate actual text-free evidence, then rehash deliberately changed content."""
    root = Path(root)
    shutil.copytree(BUNDLE.parent / "pilot", root / "pilot")
    comparison = json.loads(BUNDLE.read_bytes())
    for entry in comparison["runs"]:
        source = BUNDLE.parent / entry["path"]
        destination = root / entry["path"]
        destination.parent.mkdir(parents=True)
        run = json.loads(source.read_bytes())
        files = {name: json.loads((source.parent / name).read_bytes()) for name in
                 ("feasibility.json", "environment.json", "precision-evidence.json")}
        mutate(run, files)
        for name, value in files.items():
            pilot_inference.write_json(destination.parent / name, value)
            run["artifact_sha256"][name] = pilot_inference.file_hash(destination.parent / name)
        run["precision_evidence"] = "precision-evidence.json#sha256=" + run["artifact_sha256"]["precision-evidence.json"]
        shutil.copyfile(source.parent / "predictions.jsonl", destination.parent / "predictions.jsonl")
        pilot_inference.write_json(destination, run)
        entry["sha256"] = pilot_inference.file_hash(destination)
    pilot_inference.write_json(root / "comparison.json", comparison)
    return root / "comparison.json"


class GuardRegressionTests(unittest.TestCase):
    def reject(self, mutate, message=None):
        with tempfile.TemporaryDirectory() as temp:
            manifest = copied_bundle(Path(temp) / "bundle", mutate)
            with self.assertRaisesRegex(ValueError, message or "."):
                target.summarize(manifest)

    def test_hash_consistent_timing_boundary_mismatch_rejected(self):
        self.reject(lambda run, files: files["feasibility.json"].__setitem__(
            "forward_boundary", "end-to-end") if run["precision"] == "fp16" else None)

    def test_hash_consistent_missing_all_device_identity_rejected(self):
        self.reject(lambda run, files: (files["environment.json"].pop("gpu_uuid"),
                                       files["environment.json"].pop("allocation_id")))

    def test_hash_consistent_test_role_rejected(self):
        self.reject(lambda run, files: run.__setitem__("data_role", "test_b"))

    def test_hash_consistent_different_token_schedule_rejected(self):
        self.reject(lambda run, files: run.__setitem__("token_schedule_sha256", "0" * 64)
                    if run["precision"] == "fp16" else None)

    def test_common_missing_device_with_recomputed_environment_digest_rejected(self):
        def mutate(run, files):
            for key in ("gpu_uuid", "allocation_id"):
                files["environment.json"].pop(key)
            run["environment_id"] = target._identity(files["environment.json"])
        self.reject(mutate, "Missing execution environment")

    def test_common_shortened_timing_population_rejected(self):
        def mutate(run, files):
            f = files["feasibility.json"]
            f["samples"].pop()
            values = sorted(r["forward_seconds"] for r in f["samples"])
            f["median_forward_seconds"] = statistics.median(values)
            f["p95_forward_seconds"] = values[math.ceil(.95 * len(values)) - 1]
        self.reject(mutate, "Timing coverage")

    def test_common_measurement_contract_mutations_rejected(self):
        for key, value in (("forward_boundary", "end-to-end"), ("loading_scope", "includes download"),
                           ("warmup", {"batches": 3, "schedule": "last three planned IDs"}),
                           ("warmup", {"batches": 3.0, "schedule": "first three planned IDs in order"})):
            with self.subTest(key=key, value=value):
                self.reject(lambda run, files: files["feasibility.json"].__setitem__(key, value), "measurement boundary")

    def test_sample_contract_rejects_repetition_bool_batch_and_length(self):
        for key, value in (("repetition", 1), ("repetition", False), ("batch_size", True),
                           ("effective_tokens", 1025), ("forward_seconds", -1)):
            with self.subTest(key=key, value=value):
                self.reject(lambda run, files: files["feasibility.json"]["samples"][0].__setitem__(key, value))

    def test_run_contract_mutations_rejected(self):
        for field, value in (("model_revision", "b" * 40), ("tokenizer_revision", "b" * 40),
                             ("preprocessing_id", "sha256:" + "0" * 64), ("code_revision", "sha256:" + "0" * 64),
                             ("observed_rows", 127), ("test_performance_released", True),
                             ("checkpoint", {}), ("token_schedule_sha256", "0" * 64)):
            with self.subTest(field=field):
                self.reject(lambda run, files: run.__setitem__(field, value))

    def test_rehashed_changed_execution_flags_rejected(self):
        def mutate(run, files):
            files["environment.json"]["flags"]["tf32_matmul"] = True
            files["precision-evidence.json"]["flags"]["tf32_matmul"] = True
            run["environment_id"] = target._identity(files["environment.json"])
        self.reject(mutate, "execution flags")

    def test_memory_storage_and_loading_numeric_guards(self):
        mutations = [lambda f: f["feasibility.json"]["memory"].__setitem__("peak_allocated_bytes", -1),
                     lambda f: f["feasibility.json"]["memory_baseline_after_warmup"].__setitem__("allocated_bytes", 10**20),
                     lambda f: f["feasibility.json"].__setitem__("loading_seconds", -1),
                     lambda f: f["precision-evidence.json"]["parameters"][0].__setitem__("storage_bytes", -1),
                     lambda f: f["precision-evidence.json"].__setitem__("parameters", [])]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.reject(lambda run, files: mutate(files))

    def test_schema_and_protected_comparison_rejected_before_artifact_reads(self):
        for values in ({"schema_version": 2, "data_role": "eligible_training"},
                       {"schema_version": 1, "data_role": "test_b"},
                       {"schema_version": True, "data_role": "eligible_training"}):
            with self.subTest(values=values), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "comparison.json"
                pilot_inference.write_json(path, values)
                with self.assertRaises(ValueError):
                    target.load_bundle(path)

    def test_rehashed_changed_labels_rejected_before_predictions_are_opened(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = copied_bundle(Path(temp) / "bundle", lambda run, files: None)
            root = manifest.parent
            example_path = root / "pilot/examples.jsonl"
            rows = [json.loads(line) for line in example_path.read_text().splitlines()]
            for row in rows:
                row["label"] = 1 - row["label"]  # Same IDs, balanced classes and length quotas.
            example_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
            example_sha = pilot_inference.file_hash(example_path)
            pilot_path = root / "pilot/manifest.json"
            pilot = json.loads(pilot_path.read_bytes())
            pilot["examples"]["sha256"] = example_sha
            pilot_inference.write_json(pilot_path, pilot)
            comparison = json.loads(manifest.read_bytes())
            comparison["examples"]["sha256"] = example_sha
            for entry in comparison["runs"]:
                path = root / entry["path"]
                run = json.loads(path.read_bytes())
                run["pilot_manifest_sha256"] = pilot_inference.file_hash(pilot_path)
                pilot_inference.write_json(path, run)
                entry["sha256"] = pilot_inference.file_hash(path)
            pilot_inference.write_json(manifest, comparison)
            with patch.object(target.artifacts, "load_comparison", side_effect=AssertionError("Prediction reader reached")):
                with self.assertRaisesRegex(ValueError, "not the approved D-012 population"):
                    target.summarize(manifest)

    def test_json_exponent_overflow_is_rejected_after_valid_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = copied_bundle(Path(temp) / "bundle", lambda run, files: None)
            comparison = json.loads(manifest.read_bytes())
            entry = comparison["runs"][0]
            run_path = manifest.parent / entry["path"]
            resource_path = run_path.parent / "feasibility.json"
            data = json.loads(resource_path.read_bytes())
            data["loading_seconds"] = 1e100
            resource_path.write_bytes(json.dumps(data).encode().replace(b"1e+100", b"1e999"))
            run = json.loads(run_path.read_bytes())
            run["artifact_sha256"]["feasibility.json"] = pilot_inference.file_hash(resource_path)
            pilot_inference.write_json(run_path, run)
            entry["sha256"] = pilot_inference.file_hash(run_path)
            pilot_inference.write_json(manifest, comparison)
            with self.assertRaisesRegex(ValueError, "Invalid loading duration"):
                target.summarize(manifest)


if __name__ == "__main__":
    unittest.main()
