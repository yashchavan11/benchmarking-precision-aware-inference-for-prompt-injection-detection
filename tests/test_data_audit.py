import json
from pathlib import Path
import tempfile
import unittest

from precision_benchmark.data_audit import DATASET, acquire, audit_splits, digest, ordered_id_hash

REVISION = "a" * 40


class DataAuditTests(unittest.TestCase):
    def test_cache_requires_provenance_and_rejects_later_changed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contents = {"README.md": b"synthetic card", "repository-metadata.json": json.dumps({"id": DATASET, "sha": REVISION}).encode(),
                        **{f"{split}.json": b'[{"prompt":"synthetic","label":0}]' for split in ("train", "validation", "test")}}
            for name, raw in contents.items():
                (root / name).write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "no integrity receipt"):
                acquire(REVISION, root, False)
            previous = root / "previous-provenance.json"
            previous.write_text(json.dumps({"source_api": {"id": DATASET, "sha": REVISION},
                                            "files": {name: {"sha256": digest(raw)} for name, raw in contents.items()}}))
            source, _ = acquire(REVISION, root, False, previous)
            self.assertEqual(source["train"][0]["label"], 0)
            self.assertTrue((root / "source-integrity.json").exists())
            (root / "train.json").write_bytes(b'[{"prompt":"changed","label":1}]')
            with self.assertRaisesRegex(ValueError, "cached source SHA-256 mismatch"):
                acquire(REVISION, root, False)

    def test_overlap_precedence_conflicts_and_original_ids(self):
        source = {
            "train": [{"prompt": "test shared", "label": 1}, {"prompt": "validation shared", "label": 0},
                      {"prompt": "keep", "label": 0}, {"prompt": "keep", "label": 1}],
            "validation": [{"prompt": "test shared", "label": 0}, {"prompt": "validation shared", "label": 0}],
            "test": [{"prompt": "test shared", "label": 1}, {"prompt": "test shared", "label": 1}]}
        summary, identities, excluded, kept = audit_splits(source, REVISION, 1)
        self.assertEqual(summary["all_splits"]["conflicting_label_groups"], 2)
        self.assertEqual(summary["all_splits"]["rows_in_conflicting_label_groups"], 6)
        self.assertEqual(summary["all_splits"]["excess_duplicate_rows"], 5)
        self.assertEqual(summary["splits"]["test"]["exact_text_groups_by_label"], {"0": 0, "1": 1})
        self.assertEqual(summary["splits"]["test"]["duplicate_group_size_histogram"], {"2": 1})
        self.assertEqual([r["source_row"] for r in kept["train"]], [2, 3])
        self.assertEqual([r["source_row"] for r in kept["validation"]], [1])
        self.assertEqual([r["exclusion_reason"] for r in excluded],
                         ["exact_text_in_official_test", "exact_text_in_retained_validation", "exact_text_in_official_test"])
        self.assertEqual(summary["development_overlap_projection"]["train"]["remaining_rows_in_conflicting_label_groups"], 2)
        self.assertEqual(summary["incidental_viewer_prefix_proxy"]["test_rows_in_those_groups"], 2)
        self.assertEqual(identities[2]["example_id"], f"{REVISION}:train:2")
        self.assertTrue(all("prompt" not in row for row in identities))
        self.assertFalse(any(summary["projection_isolation_checks"].values()))

    def test_exact_hashing_preserves_whitespace_unicode_and_row_order(self):
        source = {"train": [{"prompt": "café", "label": 0}, {"prompt": "cafe\u0301", "label": 0},
                            {"prompt": " café", "label": 0}],
                  "validation": [{"prompt": "v", "label": 1}],
                  "test": [{"prompt": "t", "label": 1}]}
        summary, rows, _, _ = audit_splits(source, REVISION)
        self.assertEqual(summary["splits"]["train"]["exact_text_groups"], 3)
        self.assertEqual(rows[0]["raw_text_sha256"], digest("café".encode("utf-8")))
        self.assertEqual(rows[0]["unicode_characters"], 4)
        self.assertEqual(rows[0]["utf8_bytes"], 5)
        self.assertNotEqual(ordered_id_hash(["x", "y"]), ordered_id_hash(["y", "x"]))

    def test_invalid_schema_labels_and_revision_rejected_without_prompt_echo(self):
        normal = {s: [{"prompt": "sensitive synthetic text", "label": 0}] for s in ("train", "validation", "test")}
        for bad in ({"prompt": "sensitive synthetic text", "label": True},
                    {"prompt": "sensitive synthetic text", "label": 2},
                    {"prompt": 123, "label": 0}, {"flag": 0, "prompt": "sensitive synthetic text"}):
            with self.subTest(bad=bad):
                source = {**normal, "train": [bad]}
                with self.assertRaises(ValueError) as caught:
                    audit_splits(source, REVISION)
                self.assertNotIn("sensitive synthetic text", str(caught.exception))
        with self.assertRaises(ValueError):
            audit_splits(normal, "main")


if __name__ == "__main__":
    unittest.main()
