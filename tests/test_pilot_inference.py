"""Pilot contract/scoring/orchestration checks; no native inference or network."""
from contextlib import ExitStack, nullcontext, redirect_stderr, redirect_stdout
import copy
import io
import json
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from precision_benchmark import input_data
from precision_benchmark import pilot_inference as target


def fixture(directory):
    rows, records = [], []
    for label in (0, 1):
        for original in [3] * 48 + [600] * 8 + [1030] * 8:
            index = len(rows)
            example_id = f"{input_data.REVISION}:train:{index}"
            text = ("a" if label == 0 else "b") * original
            raw_hash = target.digest(text.encode())
            rows.append({"example_id": example_id, "label": label, "raw_text_sha256": raw_hash,
                         "source_split": "train", "source_row": index, "original_tokens": original,
                         "effective_tokens": min(original, target.CAP), "truncated": original > target.CAP,
                         "data_role": target.ROLE})
            records.append(input_data.InputRecord(example_id, "train", index, raw_hash, text))
    examples = directory / "examples.jsonl"
    examples.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    ids = [row["example_id"] for row in rows]
    manifest = {"schema_version": 1, "data_role": target.ROLE, "purpose": "development_precision_pilot",
                "decision_id": "D-012", "model_revision": target.tokenizer_audit.REVISION,
                "tokenizer_revision": target.tokenizer_audit.REVISION, "dataset_revision": input_data.REVISION,
                "cap": target.CAP, "batch_size": 1, "threshold": 0.5, "threshold_source": target.THRESHOLD_SOURCE,
                "preprocessing_options": copy.deepcopy(target.PREPROCESSING), "population_id": "synthetic-pilot",
                "preprocessing_id": "synthetic-options", "input_schedule_id": "synthetic-planned-schedule",
                "selected_ids": ids, "ordered_id_sha256": input_data.id_hash(ids),
                "membership_sha256": input_data.id_hash(sorted(ids)),
                "examples": {"path": "examples.jsonl", "sha256": target.file_hash(examples)}}
    path = directory / "manifest.json"
    target.write_json(path, manifest)
    population = input_data.LoadedDevelopment(tuple(records), tuple(rows), {"expected_rows": 128})
    return path, manifest, rows, population


class FakeTokenizer:
    """Invented character encoder used only to check control flow and lengths."""
    def __call__(self, texts, **kwargs):
        ids = [[ord(character) + 1 for character in text] for text in texts]
        if kwargs["truncation"]:
            ids = [values[:kwargs["max_length"]] for values in ids]
        return {"input_ids": ids, "attention_mask": [[1] * len(values) for values in ids]}


class FakeRunner:
    fail_on = None
    loading_seconds = 0.01
    def __init__(self, precision, directory, device):
        self.precision, self.calls = precision, 0
    def environment(self):
        return {"scope": "mock-only", "allocation": "synthetic"}, "synthetic-environment"
    def synthetic_checks(self, tokenizer):
        return {"status": "passed", "scope": "mock orchestration only"}
    def precision_evidence(self):
        return {"precision": self.precision, "scope": "mock-only"}
    def forward(self, ids, mask):
        self.calls += 1
        if self.calls == self.fail_on:
            raise RuntimeError("PRIVATE_SOURCE_MUST_NOT_BE_LOGGED")
        # Equality case deliberately exercises score >= threshold.
        return {"score": 0.5, "logits": [0.0, 0.0], "forward_seconds": 0.01}
    def start_measurement(self):
        return {"allocated_bytes": 12, "reserved_bytes": 24}
    def memory(self):
        return {"peak_allocated_bytes": 15, "peak_reserved_bytes": 30}


class Scalar:
    def __init__(self, value):
        self.value = value
    def item(self):
        return self.value
    def all(self):
        return self


class Logits:
    def __init__(self, values, dtype="float16", shape=(1, 2)):
        self.values, self.dtype, self.shape = values, dtype, shape
    def to(self, dtype):
        return Logits(self.values, dtype, self.shape)
    def detach(self):
        return self
    def cpu(self):
        return self
    def tolist(self):
        return self.values
    def __getitem__(self, index):
        return Scalar(self.values[index[1]]) if isinstance(index, tuple) else self


class NativeForwardTests(unittest.TestCase):
    def make_runner(self, values, dtype="float16", shape=(1, 2)):
        events = []
        torch = SimpleNamespace(float32="float32", float16="float16", long="int64")
        torch.tensor = lambda value, **kwargs: events.append("transfer") or value
        torch.cuda = SimpleNamespace(synchronize=lambda device: events.append("synchronize"))
        torch.inference_mode = lambda: nullcontext()
        torch.autocast = lambda **kwargs: (self.assertEqual(kwargs, {"device_type": "cuda", "enabled": False}) or nullcontext())
        torch.isfinite = lambda value: Scalar(all(math.isfinite(x) for x in value.values))
        def softmax(value, dim):
            events.append("softmax")
            self.assertEqual(value.dtype, "float32")
            exponents = [math.exp(x - max(value.values)) for x in value.values]
            return Logits([x / sum(exponents) for x in exponents], "float32")
        torch.softmax = softmax
        runner = target.TorchRunner.__new__(target.TorchRunner)
        runner.torch, runner.device, runner.precision = torch, "cuda:0", "fp16"
        def model(**kwargs):
            events.append("model")
            self.assertNotIn("labels", kwargs)
            self.assertFalse(kwargs["use_cache"])
            self.assertTrue(kwargs["return_dict"])
            return SimpleNamespace(logits=Logits(values, dtype, shape))
        runner.model = model
        return runner, events

    def test_score_selects_injection_index_not_top_confidence_and_timing_scope(self):
        runner, events = self.make_runner([math.log(3), 0.0])
        with patch.object(target.time, "perf_counter", side_effect=[1.0, 1.02]):
            result = runner.forward([12, 13], [1, 1])
        self.assertAlmostEqual(result["score"], 0.25)
        self.assertAlmostEqual(result["forward_seconds"], 0.02)
        self.assertEqual(events, ["transfer", "transfer", "synchronize", "model", "synchronize", "softmax"])

    def test_bad_vectors_never_call_native_forward(self):
        runner, events = self.make_runner([0.0, 0.0])
        for ids, mask in (([], []), ([1], [0]), ([1], [True]), ([1.0], [1]),
                          ([target.tokenizer_audit.VOCAB_LIMIT], [1]), ([1] * 1025, [1] * 1025)):
            with self.assertRaises(target.PilotError):
                runner.forward(ids, mask)
        self.assertEqual(events, [])

    def test_nonfinite_wrong_shape_and_wrong_dtype_are_not_silently_repaired(self):
        for values, dtype, shape in (([float("nan"), 0], "float16", (1,2)),
                                      ([0,0], "float32", (1,2)), ([0,0], "float16", (2,1))):
            runner, _ = self.make_runner(values, dtype, shape)
            with self.assertRaises(target.PilotError):
                runner.forward([1], [1])


class PilotContractTests(unittest.TestCase):
    def test_manifest_integrity_protected_role_and_exact_options(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, manifest, rows, _ = fixture(root)
            loaded, examples = target.load_pilot(path, target.file_hash(path))
            self.assertEqual(len(examples), 128)
            with self.assertRaises(ValueError):
                target.load_pilot(path, "0" * 64)
            for role in ("test_a", "test_b", "eligible_validation"):
                changed = {**manifest, "data_role": role}
                target.write_json(path, changed)
                with patch.object(target.input_data, "fixed_path", side_effect=AssertionError("Examples must not be opened")):
                    with self.assertRaises(target.PilotError):
                        target.load_pilot(path, target.file_hash(path))
            changed = copy.deepcopy(manifest)
            changed["preprocessing_options"]["use_fast"] = 1
            target.write_json(path, changed)
            with self.assertRaises(target.PilotError):
                target.load_pilot(path, target.file_hash(path))

    def test_authorized_source_join_and_token_length_schedule(self):
        with tempfile.TemporaryDirectory() as temp:
            path, _, examples, population = fixture(Path(temp))
            records = target.select_records(population, examples)
            prepared, token_hash = target.prepare_inputs(FakeTokenizer(), records, examples)
            self.assertEqual(len(prepared), 128)
            self.assertEqual(len(token_hash), 64)
            self.assertEqual(sum(len(ids) == 1024 for _, ids, _ in prepared), 16)
            wrong = copy.deepcopy(examples)
            wrong[0]["label"] = 1
            with self.assertRaises(target.PilotError):
                target.select_records(population, wrong)
            wrong = copy.deepcopy(examples)
            wrong[0]["original_tokens"] += 1
            with self.assertRaises(target.PilotError):
                target.prepare_inputs(FakeTokenizer(), records, wrong)

    def test_checkpoint_hash_and_local_config_checked_before_loading(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            model, assets = root / "model", root / "assets"
            model.mkdir(); assets.mkdir()
            raw = b"synthetic weight payload"
            checkpoint = model / "model.safetensors"
            checkpoint.write_bytes(raw)
            (model / "config.json").write_bytes(b"{}")
            (assets / "config.json").write_bytes(b"{}")
            with patch.object(target, "WEIGHT_BYTES", len(raw)), patch.object(target, "WEIGHT_SHA256", target.digest(raw)):
                self.assertTrue(target.verify_checkpoint(checkpoint, assets)["full_payload_hash_verified"])
                checkpoint.write_bytes(b"X" + raw[1:])
                with self.assertRaises(target.PilotError):
                    target.verify_checkpoint(checkpoint, assets)
                checkpoint.write_bytes(raw)
                (model / "config.json").write_bytes(b"[]")
                with self.assertRaises(target.PilotError):
                    target.verify_checkpoint(checkpoint, assets)

    def run_mock(self, root, runner_factory=FakeRunner):
        path, _, examples, population = fixture(root)
        checkpoint = root / "model.safetensors"
        checkpoint.write_bytes(b"mock")
        with ExitStack() as stack:
            stack.enter_context(patch.object(target.tokenizer_audit, "verify_assets", return_value=({"config.json": {}}, {"config": "hash"})))
            stack.enter_context(patch.object(target.input_data, "load_development", return_value=population))
            stack.enter_context(patch.object(target, "verify_checkpoint", return_value={"scope": "mock-only"}))
            stack.enter_context(patch.object(target.tokenizer_audit, "load_native", return_value=(FakeTokenizer(), {"scope": "mock-only"})))
            result = target.run(root / "output", path, target.file_hash(path), root, checkpoint,
                                root / "access", "a" * 64, root, root, "fp16", "mock-pilot",
                                runner_factory=runner_factory)
        return result, examples

    def test_complete_run_coverage_threshold_and_reusable_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result, examples = self.run_mock(root)
            rows = [json.loads(line) for line in (root / "output/predictions.jsonl").read_text().splitlines()]
            self.assertEqual(result["status"], "complete")
            self.assertEqual([row["example_id"] for row in rows], [row["example_id"] for row in examples])
            self.assertTrue(all(row["prediction"] == 1 and "label" not in row for row in rows))
            self.assertEqual(result["predictions"]["sha256"], target.file_hash(root / "output/predictions.jsonl"))
            self.assertNotEqual(result["input_schedule_id"], result["planned_input_schedule_id"])
            self.assertEqual(json.loads((root / "output/execution.json").read_text())["completed_rows"], 128)
            with self.assertRaises(target.PilotError):
                target.run(root / "output", root / "absent", "0"*64, root, root, root, "0"*64, root, root, "fp16", "again")

    def test_failure_keeps_partial_rows_and_never_marks_run_complete_or_leaks(self):
        class FailingRunner(FakeRunner):
            fail_on = 6  # three warm-ups then two complete data rows
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture = io.StringIO()
            with redirect_stdout(capture), redirect_stderr(capture), self.assertRaises(target.PilotError):
                self.run_mock(root, FailingRunner)
            execution = json.loads((root / "output/execution.json").read_text())
            self.assertEqual(execution["status"], "incomplete")
            self.assertEqual(execution["completed_rows"], 2)
            self.assertEqual(execution["error_type"], "RuntimeError")
            self.assertNotIn("failure_reason", execution)
            self.assertFalse((root / "output/run.json").exists())
            self.assertEqual(len((root / "output/predictions.jsonl").read_text().splitlines()), 2)
            self.assertNotIn("PRIVATE_SOURCE_MUST_NOT_BE_LOGGED", capture.getvalue() + json.dumps(execution))

    def test_fixed_internal_failure_reason_retained_but_subclass_message_suppressed(self):
        class ProviderLikeError(target.PilotError):
            pass
        for error_type in (target.PilotError, ProviderLikeError):
            class GuardFailure(FakeRunner):
                def forward(self, ids, mask):
                    raise error_type("Synthetic fixed guard failure")
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                with self.assertRaises(target.PilotError):
                    self.run_mock(root, GuardFailure)
                execution = json.loads((root / "output/execution.json").read_text())
                if error_type is target.PilotError:
                    self.assertEqual(execution["failure_reason"], "Synthetic fixed guard failure")
                else:
                    self.assertNotIn("failure_reason", execution)


if __name__ == "__main__":
    unittest.main()
