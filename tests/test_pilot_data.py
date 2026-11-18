"""Invented text-free training/length fixtures; no real prompts or model outputs."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from precision_benchmark import input_data, pilot_data, tokenizer_audit


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def jsonl(rows):
    return b"".join(json.dumps(row, sort_keys=True).encode() + b"\n" for row in rows)


class PilotDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.popdir, self.native_dir = self.root / "populations", self.root / "native"
        self.popdir.mkdir()
        self.native_dir.mkdir()
        self.rows, self.length_rows = [], []
        for label in (0, 1):
            for length in [100] * 49 + [512] + [513] * 9 + [1024] + [1025] * 9 + [1400]:
                position = len(self.rows)
                example_id = f"{input_data.REVISION}:train:{position}"
                group = sha(f"invented-group-{position}".encode())
                self.rows.append({"example_id": example_id, "data_role": "eligible_training", "source_split": "train",
                                  "source_row": position, "label": label, "raw_text_sha256": group,
                                  "unicode_characters": length * 4, "utf8_bytes": length * 4})
                self.length_rows.append({"example_id": example_id, "data_role": "eligible_training", "raw_text_sha256": group,
                    "original_tokens": length, "original_source_pooling": {}, "python_nfc_changes_raw_string": False,
                    "caps": {str(cap): {"effective_tokens": min(length, cap), "truncated": length > cap} for cap in (512, 1024, 2048)}})
        ids = [row["example_id"] for row in self.rows]
        original_source_hash = "a" * 64
        self.population = {"file": "eligible-training.jsonl", "rows": 140, "class_counts": {"0": 70, "1": 70},
                           "exact_text_groups": 140, "ordered_id_sha256": input_data.id_hash(ids),
                           "membership_sha256": input_data.id_hash(sorted(ids))}
        self.population_summary = {"dataset": input_data.DATASET, "revision": input_data.REVISION, "construction_decision": "D-008",
                                   "populations": {"eligible_training": self.population}, "output_files": {},
                                   "original_source_sha256": {"train.json": original_source_hash}}
        self.preflight = {"dataset": input_data.DATASET, "revision": input_data.REVISION, "data_role": "eligible_training",
                          "construction_decision": "D-008", "continuation_decision": "D-009", "expected_rows": 140,
                          "validated_rows": 140, "ordered_id_sha256": self.population["ordered_id_sha256"],
                          "class_counts": {"0": 70, "1": 70},
                          "inputs": {"original_source": {"filename": "train.json", "sha256": original_source_hash}}}
        self.native_manifest = {"status": "complete", "model_revision": tokenizer_audit.REVISION,
                                "expected_rows": {"eligible_training": 140}, "processed_rows": {"eligible_training": 140},
                                "output_hashes": {}}
        self.native_summary = {"status": "complete", "model_id": tokenizer_audit.MODEL_ID, "model_revision": tokenizer_audit.REVISION,
             "asset_manifest_sha256": tokenizer_audit.ASSET_MANIFEST_SHA256,
             "source_metadata_sha256": tokenizer_audit.SOURCE_METADATA_SHA256,
             "asset_hashes": {name: "b" * 64 for name in tokenizer_audit.contract_audit.FILES},
             "baseline_call": {"add_special_tokens": True, "padding": False, "truncation": False, "split_special_tokens": False},
             "chat_template_applied": False, "runtime": {"tokenizer_class": "Qwen2TokenizerFast", "versions": tokenizer_audit.VERSIONS},
             "populations": {"eligible_training": {"input_evidence": self.preflight,
                 "total": {"rows": 140, "original_lengths": {"n": 140}, "caps": {"1024": {"denominator_rows": 140, "truncated_rows": 20}}}}}}
        self.persist()

    def persist(self):
        raw = jsonl(self.rows)
        (self.popdir / "eligible-training.jsonl").write_bytes(raw)
        self.population_summary["output_files"]["eligible-training.jsonl"] = sha(raw)
        parent_raw = json.dumps(self.population_summary).encode()
        (self.popdir / "summary.json").write_bytes(parent_raw)
        self.population_sha = sha(parent_raw)
        self.preflight["inputs"]["parent_population_summary"] = {"filename": "summary.json", "sha256": self.population_sha}
        self.preflight["inputs"]["population"] = {"filename": "eligible-training.jsonl", "sha256": sha(raw)}
        length_raw = jsonl(self.length_rows)
        (self.native_dir / "eligible_training-lengths.jsonl").write_bytes(length_raw)
        self.native_manifest["output_hashes"]["eligible_training-lengths.jsonl"] = sha(length_raw)
        manifest_raw = json.dumps(self.native_manifest).encode()
        (self.native_dir / "manifest.json").write_bytes(manifest_raw)
        self.native_summary["manifest_sha256"] = sha(manifest_raw)
        native_raw = json.dumps(self.native_summary).encode()
        (self.native_dir / "summary.json").write_bytes(native_raw)
        self.native_sha = sha(native_raw)

    def build(self, name="out"):
        return pilot_data.build(self.popdir, self.population_sha, self.native_dir, self.native_sha, self.root / name)

    def test_known_hash_selection_quotas_boundaries_and_source_order(self):
        manifest = self.build()
        rows = [json.loads(line) for line in (self.root / "out" / "examples.jsonl").read_bytes().splitlines()]
        # Fixed known-answer omissions for the declared namespace and 140 invented IDs.
        omitted = {3, 28, 52, 58, 63, 67, 86, 115, 120, 121, 130, 135}
        self.assertEqual([row["source_row"] for row in rows], [i for i in range(140) if i not in omitted])
        self.assertEqual(manifest["class_counts"], {"0": 64, "1": 64})
        for label in (0, 1):
            selected = [row for row in rows if row["label"] == label]
            self.assertEqual(sum(row["original_tokens"] <= 512 for row in selected), 48)
            self.assertEqual(sum(513 <= row["original_tokens"] <= 1024 for row in selected), 8)
            self.assertEqual(sum(row["original_tokens"] > 1024 for row in selected), 8)
        self.assertEqual(sum(row["truncated"] for row in rows), 16)
        self.assertTrue(all(row["effective_tokens"] == min(row["original_tokens"], 1024) for row in rows))
        self.assertTrue(all("prompt" not in row for row in rows))
        for value, expected in ((1, "le512"), (512, "le512"), (513, "513to1024"), (1024, "513to1024"), (1025, "gt1024")):
            self.assertEqual(pilot_data.length_bin(value), expected)
        for value in (0, -1, True, 1.5):
            with self.assertRaises(pilot_data.PilotDataError):
                pilot_data.length_bin(value)

    def test_manifest_interface_identities_and_reproducibility(self):
        manifest = self.build("first")
        self.build("second")
        self.assertEqual({p.name: p.read_bytes() for p in (self.root / "first").iterdir()},
                         {p.name: p.read_bytes() for p in (self.root / "second").iterdir()})
        raw = (self.root / "first" / "examples.jsonl").read_bytes()
        self.assertEqual(manifest["examples"], {"path": "examples.jsonl", "sha256": sha(raw)})
        self.assertEqual(manifest["ordered_id_sha256"], input_data.id_hash(manifest["selected_ids"]))
        self.assertEqual(manifest["membership_sha256"], input_data.id_hash(sorted(manifest["selected_ids"])))
        self.assertEqual(manifest["input_schedule_id"], "sha256:" + sha(pilot_data.canonical(manifest["input_schedule"])))
        self.assertEqual(manifest["preprocessing_id"], "sha256:" + sha(pilot_data.canonical(manifest["preprocessing_contract"])))
        self.assertEqual((manifest["cap"], manifest["batch_size"], manifest["threshold"]), (1024, 1, 0.5))
        self.assertEqual(manifest["threshold_source"], "provisional-p1b-fixed-0.5-not-validation-selected")
        self.assertFalse(manifest["main_study_freeze"])
        self.assertFalse(manifest["model_inference_performed"])
        self.assertEqual(manifest["source_evidence"]["full_training_rows_verified"], 140)

    def test_each_source_artifact_hash_is_checked_and_no_existing_output_overwritten(self):
        files = [self.popdir / "summary.json", self.popdir / "eligible-training.jsonl",
                 self.native_dir / "summary.json", self.native_dir / "manifest.json", self.native_dir / "eligible_training-lengths.jsonl"]
        for path in files:
            original = path.read_bytes()
            path.write_bytes(original + b" ")
            with self.subTest(file=path.name), self.assertRaises(pilot_data.PilotDataError):
                self.build()
            self.assertFalse((self.root / "out").exists())
            path.write_bytes(original)
        self.build()
        before = {p.name: p.read_bytes() for p in (self.root / "out").iterdir()}
        with patch.object(input_data, "checked_bytes", side_effect=AssertionError("No read")):
            with self.assertRaisesRegex(pilot_data.PilotDataError, "must be new"):
                self.build()
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.root / "out").iterdir()})

    def test_missing_duplicate_reordered_length_coverage_rejected(self):
        original = copy.deepcopy(self.length_rows)
        variants = [original[:-1], [original[0], *original[:-1]], list(reversed(original))]
        for rows in variants:
            self.length_rows = copy.deepcopy(rows)
            self.persist()
            with self.subTest(n=len(rows)), self.assertRaises(pilot_data.PilotDataError):
                self.build()
            self.assertFalse((self.root / "out").exists())

    def test_incompatible_label_identity_length_and_native_source_contracts_rejected(self):
        original_rows, original_lengths = copy.deepcopy(self.rows), copy.deepcopy(self.length_rows)
        mutations = [lambda: self.length_rows[0].update(raw_text_sha256="c" * 64),
                     lambda: self.length_rows[0].update(data_role="test_a"),
                     lambda: self.length_rows[0].update(original_tokens=True),
                     lambda: self.length_rows[0]["caps"]["1024"].update(effective_tokens=99),
                     lambda: self.rows[0].update(label=True),
                     lambda: self.rows[0].update(source_split="test")]
        for mutation in mutations:
            self.rows, self.length_rows = copy.deepcopy(original_rows), copy.deepcopy(original_lengths)
            mutation()
            self.persist()
            with self.assertRaises(pilot_data.PilotDataError):
                self.build()
        self.rows, self.length_rows = original_rows, original_lengths
        self.native_summary["model_revision"] = "b" * 40
        self.persist()
        with self.assertRaisesRegex(pilot_data.PilotDataError, "source/identity"):
            self.build()

    def test_insufficient_strata_and_duplicate_training_groups_do_not_backfill(self):
        lengths = {row["example_id"]: row for row in self.length_rows}
        without_three_medium = [row for row in self.rows if row["source_row"] not in (50, 51, 52)]
        with self.assertRaisesRegex(pilot_data.PilotDataError, "insufficient support"):
            pilot_data.select(without_three_medium, lengths)
        self.rows[1]["raw_text_sha256"] = self.rows[0]["raw_text_sha256"]
        self.length_rows[1]["raw_text_sha256"] = self.rows[0]["raw_text_sha256"]
        self.population["exact_text_groups"] = 139
        self.persist()
        with self.assertRaisesRegex(pilot_data.PilotDataError, "unique training groups"):
            self.build()


if __name__ == "__main__":
    unittest.main()
