import json
from pathlib import Path
import shutil
import tempfile
import unittest

from precision_benchmark.artifacts import load_comparison, read_json, sha256

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic"


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "input"
        shutil.copytree(FIXTURE, self.root)
        self.path = self.root / "comparison.json"

    def update_json(self, name, change):
        path = self.root / name
        value = read_json(path)
        change(value)
        path.write_text(json.dumps(value))

    def rehash(self):
        for precision in ("fp32", "fp16", "int8"):
            self.update_json(precision + ".run.json", lambda run: run["predictions"].update(
                sha256=sha256(self.root / run["predictions"]["path"])))
        def update(manifest):
            for entry in [manifest["examples"], *manifest["runs"]]:
                entry["sha256"] = sha256(self.root / entry["path"])
        self.update_json("comparison.json", update)

    def update_row(self, name, change):
        path = self.root / name
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        change(rows)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.rehash()

    def test_complete_fixture(self):
        _, examples, runs, scores, provenance = load_comparison(self.path)
        self.assertEqual(len(examples), 8)
        self.assertEqual(set(runs), {"fp32", "fp16", "int8"})
        self.assertEqual(scores["fp32"]["synthetic-0"], .1)
        self.assertEqual(len(provenance), 8)

    def test_changed_file_hash(self):
        (self.root / "fp32.jsonl").write_text("changed")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            load_comparison(self.path)

    def test_missing_and_duplicate_predictions(self):
        self.update_row("fp32.jsonl", lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, "coverage"):
            load_comparison(self.path)
        shutil.copy(FIXTURE / "fp32.jsonl", self.root / "fp32.jsonl")
        self.update_row("fp32.jsonl", lambda rows: rows.append(rows[0]))
        with self.assertRaisesRegex(ValueError, "duplicate example_id"):
            load_comparison(self.path)

    def test_wrong_prediction_label_or_run_id(self):
        for update, message in [({"prediction": 1}, "prediction does not match"),
                                ({"label": 0}, "reference-label mismatch"),
                                ({"run_id": "wrong"}, "different run_id"),
                                ({"score": float("nan")}, "finite number")]:
            with self.subTest(update=update):
                shutil.copy(FIXTURE / "fp32.jsonl", self.root / "fp32.jsonl")
                self.update_row("fp32.jsonl", lambda rows: rows[0].update(update))
                with self.assertRaisesRegex(ValueError, message):
                    load_comparison(self.path)

    def test_incompatible_runs(self):
        for field, value, message in [("threshold", .6, "threshold differs"),
                                      ("threshold_source", "other", "threshold source"),
                                      ("model_revision", "other", "incompatible model_revision"),
                                      ("preprocessing_id", "other", "incompatible preprocessing_id"),
                                      ("environment_id", "other", "incompatible environment_id"),
                                      ("code_revision", "other", "incompatible code_revision"),
                                      ("population_id", "other", "incompatible population"),
                                      ("status", "incomplete", "not complete"),
                                      ("precision", "fp32", "exactly once"),
                                      ("score_semantics", "confidence", "scores must describe injection")]:
            with self.subTest(field=field):
                shutil.copy(FIXTURE / "fp16.run.json", self.root / "fp16.run.json")
                self.update_json("fp16.run.json", lambda run: run.update({field: value}))
                self.rehash()
                with self.assertRaisesRegex(ValueError, message):
                    load_comparison(self.path)

    def test_bad_lengths_and_labels(self):
        self.update_row("examples.jsonl", lambda rows: rows[0].update(truncated=True))
        with self.assertRaisesRegex(ValueError, "truncated must agree"):
            load_comparison(self.path)
        shutil.copy(FIXTURE / "examples.jsonl", self.root / "examples.jsonl")
        self.update_row("examples.jsonl", lambda rows: rows[0].update(label=True))
        with self.assertRaisesRegex(ValueError, "integer 0 or 1"):
            load_comparison(self.path)

    def test_holdout_rejected_before_reading_examples(self):
        self.update_json("comparison.json", lambda m: m.update(data_role="Test-B"))
        (self.root / "examples.jsonl").unlink()
        with self.assertRaisesRegex(ValueError, "held-out evaluation is not enabled"):
            load_comparison(self.path)

    def test_partial_length_metadata_rejected(self):
        def remove_lengths(rows):
            for key in ("original_tokens", "effective_tokens", "truncated"):
                del rows[0][key]
        self.update_row("examples.jsonl", remove_lengths)
        with self.assertRaisesRegex(ValueError, "every example"):
            load_comparison(self.path)

    def test_duplicate_json_keys(self):
        self.path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            load_comparison(self.path)


if __name__ == "__main__":
    unittest.main()
