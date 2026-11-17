"""Small invented fixtures only; never read official-test bytes or import native code."""

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from precision_benchmark import holdout_lengths as target


class MockTokenizer:
    """Deterministic fixture lengths; not a tokenizer/BPE implementation."""
    def __init__(self, fault=None):
        self.calls = []
        self.fault = fault

    def __call__(self, texts, **kwargs):
        self.calls.append((list(texts), copy.deepcopy(kwargs)))
        if self.fault == "reflection":
            print("PRIVATE_SOURCE_TEXT", file=target.sys.stderr)
            raise ValueError("PRIVATE_SOURCE_TEXT provider failure")
        lengths = {"PRIVATE_SOURCE_TEXT": 3, " cafe\u0301 \t": 5, "<|im_end|>": 2, "": 0}
        ids = [[100 + i for i in range(lengths[text])] for text in texts]
        masks = [[1] * len(values) for values in ids]
        if self.fault == "coverage":
            ids, masks = ids[:-1], masks[:-1]
        if self.fault == "mutate":
            texts[0] = "changed source argument"
        return {"input_ids": ids, "attention_mask": masks}


class HoldoutLengthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw_dir = self.root / "raw"
        self.raw_dir.mkdir()
        self.rows = [{"prompt": "PRIVATE_SOURCE_TEXT", "label": 0},
                     {"prompt": " cafe\u0301 \t", "label": 1},
                     {"prompt": "<|im_end|>", "label": 0}]
        self.source_path = self.raw_dir / "test.json"
        self.write_source()

    def write_source(self):
        self.source_path.write_text(json.dumps(self.rows, ensure_ascii=False), encoding="utf-8")
        self.source_sha = hashlib.sha256(self.source_path.read_bytes()).hexdigest()

    def patched(self, fault=None):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(target, "SOURCE_SHA256", self.source_sha))
        stack.enter_context(patch.object(target, "EXPECTED_ROWS", 3))
        stack.enter_context(patch.object(target, "EXPECTED_CLASSES", {0: 2, 1: 1}))
        self.tokenizer = MockTokenizer(fault)
        self.native = stack.enter_context(patch.object(target.tokenizer_audit, "load_native",
                    return_value=(self.tokenizer, {"model_loaded": False, "fixture_only": True})))
        self.assets = stack.enter_context(patch.object(target.tokenizer_audit, "verify_assets",
                    return_value=({"config.json": {}}, {"fixture.json": "0" * 64})))

    def run_audit(self, name="output", role=target.ADMIN_ROLE, **kwargs):
        return target.audit(role, self.root / name, self.root / "assets", self.raw_dir,
                            self.source_sha, batch_size=2, **kwargs)

    def test_only_fixed_role_and_source_authority_before_any_read_or_native(self):
        for role in ("eligible_training", "eligible_validation", "test", "test_a", "test_b", "other", None, []):
            with self.subTest(role=role), patch.object(Path, "read_bytes", side_effect=AssertionError("No reads")), \
                    patch.object(target.tokenizer_audit, "load_native") as native:
                with self.assertRaises(target.HoldoutLengthError):
                    self.run_audit(role=role)
                native.assert_not_called()
        with patch.object(Path, "read_bytes", side_effect=AssertionError("No reads")), \
                patch.object(target.tokenizer_audit, "verify_assets") as assets:
            with self.assertRaisesRegex(target.HoldoutLengthError, "Source expectation"):
                self.run_audit()
            assets.assert_not_called()
        self.assertFalse((self.root / "output").exists())

    def test_wrong_asset_authority_and_existing_output_refused_without_reads(self):
        self.patched()
        with patch.object(Path, "read_bytes", side_effect=AssertionError("No reads")):
            with self.assertRaisesRegex(target.HoldoutLengthError, "Asset expectation"):
                self.run_audit(asset_manifest_sha256="0" * 64)
        out = self.root / "existing"
        out.mkdir()
        (out / "preserve.txt").write_bytes(b"unchanged")
        with patch.object(Path, "read_bytes", side_effect=AssertionError("No reads")):
            with self.assertRaisesRegex(target.HoldoutLengthError, "must be new"):
                self.run_audit(name="existing")
        self.assertEqual((out / "preserve.txt").read_bytes(), b"unchanged")
        self.native.assert_not_called()

    def test_source_hash_schema_count_and_labels_fail_before_native(self):
        self.patched()
        self.source_path.write_bytes(self.source_path.read_bytes() + b" ")
        with self.assertRaises(target.HoldoutLengthError):
            self.run_audit(name="tampered")
        self.native.assert_not_called()
        variants = [self.rows[:2], [dict(row, label=0) for row in self.rows],
                    [dict(self.rows[0], label=True), *self.rows[1:]],
                    [dict(self.rows[0], extra="PRIVATE_SCHEMA_VALUE"), *self.rows[1:]]]
        for index, rows in enumerate(variants):
            raw = json.dumps(rows).encode()
            self.source_path.write_bytes(raw)
            expected = hashlib.sha256(raw).hexdigest()
            with patch.object(target, "SOURCE_SHA256", expected), self.assertRaises(target.HoldoutLengthError):
                target.audit(target.ADMIN_ROLE, self.root / f"invalid-{index}", "assets", self.raw_dir, expected)
            self.native.assert_not_called()
            for path in (self.root / f"invalid-{index}").iterdir():
                self.assertNotIn(b"PRIVATE_SCHEMA_VALUE", path.read_bytes())

    def test_fixed_source_filename_has_no_fallback(self):
        self.patched()
        self.source_path.rename(self.raw_dir / "validation.json")
        with self.assertRaises(target.HoldoutLengthError):
            self.run_audit()
        self.native.assert_not_called()

    def test_complete_mock_exports_only_total_aggregates_and_preserves_strings(self):
        self.patched()
        before = self.source_path.read_bytes()
        result = self.run_audit()
        self.assertEqual(result["original_token_lengths"],
                         {"n": 3, "min": 2, "max": 5, "mean": 10 / 3, "median": 3, "p90": 5, "p95": 5, "p99": 5})
        self.assertEqual(result["original_token_length_histogram"], {"2": 1, "3": 1, "5": 1})
        self.assertEqual(result["source_class_counts"], {"0": 2, "1": 1})
        self.assertEqual(result["processed_rows"], 3)
        self.assertEqual([text for texts, _ in self.tokenizer.calls for text in texts], [row["prompt"] for row in self.rows])
        for _, kwargs in self.tokenizer.calls:
            self.assertIs(kwargs["padding"], False)
            self.assertIs(kwargs["truncation"], False)
            self.assertIs(kwargs["add_special_tokens"], True)
            self.assertNotIn("max_length", kwargs)
        self.assertEqual(self.source_path.read_bytes(), before)
        out = self.root / "output"
        self.assertEqual({p.name for p in out.iterdir()}, {"manifest.json", "summary.json"})
        encoded = (out / "summary.json").read_text()
        for forbidden in ("PRIVATE_SOURCE_TEXT", " cafe", "<|im_end|>", '"example_id"', '"input_ids"', '"attention_mask"', '"by_class"', '"caps"'):
            self.assertNotIn(forbidden, encoded)
        self.assertFalse(result["a_b_subgroups_computed"])
        self.assertFalse(result["cap_or_truncation_comparison_performed"])
        self.assertFalse(result["may_inform_development_choices"])
        self.assertFalse(result["model_loaded_or_inference_performed"])
        self.assertEqual(result["manifest_sha256"], hashlib.sha256((out / "manifest.json").read_bytes()).hexdigest())

    def test_zero_tokens_coverage_and_mutation_fail_without_summary(self):
        self.rows[1]["prompt"] = ""
        self.write_source()
        self.patched()
        with self.assertRaises(target.HoldoutLengthError):
            self.run_audit(name="zero")
        failed = json.loads((self.root / "zero" / "manifest.json").read_text())
        self.assertEqual(failed["processed_rows"], 1)
        self.assertEqual(failed["status"], "incomplete")
        self.assertFalse((self.root / "zero" / "summary.json").exists())
        # Restore valid source before the independent coverage/mutation probes.
        # Otherwise the earlier zero-token failure could mask a missing mutation guard.
        self.rows[1]["prompt"] = " cafe\u0301 \t"
        self.write_source()
        with patch.object(target, "SOURCE_SHA256", self.source_sha):
            for fault in ("coverage", "mutate"):
                self.tokenizer.fault = fault
                with self.subTest(fault=fault), self.assertRaises(target.HoldoutLengthError):
                    self.run_audit(name=fault)
                self.assertFalse((self.root / fault / "summary.json").exists())

    def test_duplicate_weighted_histogram_preserves_count_and_sum(self):
        result = target.length_evidence([1, 1, 3, 5])
        histogram = result["original_token_length_histogram"]
        self.assertEqual(histogram, {"1": 2, "3": 1, "5": 1})
        self.assertEqual(sum(histogram.values()), 4)
        self.assertEqual(sum(int(length) * count for length, count in histogram.items()), 10)
        self.assertEqual(result["original_token_lengths"],
                         {"n": 4, "min": 1, "max": 5, "mean": 2.5, "median": 2.0,
                          "p90": 5, "p95": 5, "p99": 5})

    def test_provider_failure_sanitizes_logs_manifest_and_exception(self):
        self.patched("reflection")
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr), self.assertRaises(target.HoldoutLengthError) as error:
            self.run_audit()
        self.assertNotIn("PRIVATE_SOURCE_TEXT", stdout.getvalue() + stderr.getvalue() + str(error.exception))
        out = self.root / "output"
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["error_type"], "ValueError")
        self.assertTrue(manifest["error_details_suppressed"])
        self.assertFalse((out / "summary.json").exists())
        self.assertNotIn("PRIVATE_SOURCE_TEXT", (out / "manifest.json").read_text())

    def test_no_cli_caps_or_alternative_revision_authority(self):
        argv = ["holdout_lengths", "--role", target.ADMIN_ROLE, "--assets", "assets", "--raw-dir", "raw", "--output", "out",
                "--source-sha256", target.SOURCE_SHA256, "--asset-manifest-sha256", target.tokenizer_audit.ASSET_MANIFEST_SHA256]
        for extra in (["--cap", "512"], ["--revision", "b" * 40], ["--source-file", "validation.json"]):
            stderr = io.StringIO()
            with self.subTest(option=extra[0]), patch.object(target.sys, "argv", argv + extra), \
                    patch.object(target.sys, "stderr", stderr), patch.object(target, "audit") as audit:
                with self.assertRaises(SystemExit):
                    target.main()
                audit.assert_not_called()
            self.assertIn("Invalid administrative-length arguments", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
