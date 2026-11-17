"""Synthetic D-009 contracts only; fixture identifiers do not attest real provenance."""

from contextlib import contextmanager
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from precision_benchmark import input_data as target


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ids_sha(ids):
    return sha("".join(value + "\n" for value in ids).encode())


class InputDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.partitions, self.raw = self.root / "partitions", self.root / "raw"
        self.partitions.mkdir()
        self.raw.mkdir()
        self.access_path = self.root / "development-access.json"
        self.source = {"train": [{"prompt": "  SYNTHETIC café\u0301\t\n<|im_end|>  ", "label": 1},
                                 {"prompt": "unselected synthetic source row", "label": 0},
                                 {"prompt": "\nKeep\u00a0this whitespace\r\n", "label": 0}],
                       "validation": [{"prompt": "validation café", "label": 1}]}
        self.rows, self.summary = {}, {
            "schema_version": 1, "dataset": target.DATASET, "revision": target.REVISION,
            "construction_decision": "D-008", "all_source_ids_accounted_exactly_once": True,
            "populations": {}, "original_splits": {}, "original_source_sha256": {}, "output_files": {}}
        self.old_access = {"schema_version": 1, "construction_decision": "D-008", "roles": {}}
        self.access = {"schema_version": 1, "dataset": target.DATASET, "revision": target.REVISION,
                       "construction_decision": "D-008", "continuation_decision": "D-009",
                       "human_review_performed": False, "protected_roles": ["test_a", "test_b"], "roles": {}}
        for role, (split, filename, source_file) in target.ROLES.items():
            positions = [0, 2] if split == "train" else [0]
            rows = []
            for pos in positions:
                item = self.source[split][pos]
                raw = item["prompt"].encode()
                rows.append({"example_id": f"{target.REVISION}:{split}:{pos}", "source_split": split,
                             "source_row": pos, "data_role": role, "label": item["label"],
                             "raw_text_sha256": sha(raw), "unicode_characters": len(item["prompt"]), "utf8_bytes": len(raw)})
            self.rows[role] = rows
            ids = [r["example_id"] for r in rows]
            self.summary["populations"][role] = {
                "file": filename, "rows": len(rows), "ordered_id_sha256": ids_sha(ids),
                "membership_sha256": ids_sha(sorted(ids)), "exact_text_groups": len(rows),
                "class_counts": {str(c): sum(r["label"] == c for r in rows) for c in (0, 1)}}
            self.summary["original_splits"][split] = {"rows": len(self.source[split])}
            self.old_access["roles"][role] = {"file": filename, "release_status": "pending",
                                               "release_condition": "P1-A closeout and human scientific review"}
            self.access["roles"][role] = {"population_file": filename, "source_split": split,
                "source_file": source_file, "row_count": len(rows), "ordered_id_sha256": ids_sha(ids),
                "status": target.AUTHORIZED_STATUS, "teammate_attestation_required": False}
        self.persist()

    def persist(self):
        """Reissue fixture hashes without silently recomputing expected membership/counts."""
        for role, (split, filename, source_file) in target.ROLES.items():
            raw_source = json.dumps(self.source[split], ensure_ascii=False).encode()
            (self.raw / source_file).write_bytes(raw_source)
            self.access["roles"][role]["source_sha256"] = sha(raw_source)
            self.summary["original_source_sha256"][source_file] = sha(raw_source)
            raw = "".join(json.dumps(row, sort_keys=True) + "\n" for row in self.rows[role]).encode()
            (self.partitions / filename).write_bytes(raw)
            self.access["roles"][role]["population_sha256"] = sha(raw)
            self.old_access["roles"][role]["sha256"] = sha(raw)
            self.summary["output_files"][filename] = sha(raw)
        old_raw = json.dumps(self.old_access).encode()
        (self.partitions / "access-manifest.json").write_bytes(old_raw)
        self.summary["output_files"]["access-manifest.json"] = sha(old_raw)
        self.access["parent_access_manifest"] = {"filename": "access-manifest.json", "sha256": sha(old_raw)}
        summary_raw = json.dumps(self.summary).encode()
        (self.partitions / "summary.json").write_bytes(summary_raw)
        self.access["parent_population_summary"] = {"filename": "summary.json", "sha256": sha(summary_raw)}
        self.access_path.write_text(json.dumps(self.access))
        self.expected = sha(self.access_path.read_bytes())

    def load(self, role="eligible_training"):
        return target.load_development(role, self.access_path, self.expected, self.partitions, self.raw)

    @contextmanager
    def forbid_raw_reads(self):
        original = Path.read_bytes
        def read(path):
            if path.parent == self.raw:
                self.fail("Raw source opened before invalid metadata/membership was rejected")
            return original(path)
        with patch.object(Path, "read_bytes", read):
            yield

    def test_forbidden_roles_fail_before_any_file_read(self):
        for role in ("test_a", "test_b", "test", "eligible_test", None, ["eligible_training"]):
            with self.subTest(role=role), patch.object(Path, "read_bytes", side_effect=AssertionError("No file may be read")) as read:
                with self.assertRaisesRegex(target.InputError, "Only eligible_training"):
                    self.load(role)
                with self.assertRaisesRegex(target.InputError, "Only eligible_training"):
                    target.preflight(role, self.access_path, self.expected, self.partitions, self.raw, self.root / "out")
                read.assert_not_called()

    def test_amendment_identity_and_fixed_role_filenames_precede_source_reads(self):
        original = copy.deepcopy(self.access)
        mutations = [lambda a: a.update(revision="b" * 40), lambda a: a.update(dataset="other/source"),
                     lambda a: a.update(continuation_decision="D-010"),
                     lambda a: a["roles"]["eligible_training"].update(source_file="test.json"),
                     lambda a: a["roles"]["eligible_training"].update(population_file="../test-a.jsonl"),
                     lambda a: a["roles"]["eligible_training"].update(source_split="test"),
                     lambda a: a["roles"].update(test_a=a["roles"]["eligible_training"]),
                     lambda a: a["roles"]["eligible_training"].update(status="pending")]
        for mutation in mutations:
            self.access = copy.deepcopy(original)
            mutation(self.access)
            self.access_path.write_text(json.dumps(self.access))
            self.expected = sha(self.access_path.read_bytes())
            with self.subTest(mutation=mutation), self.forbid_raw_reads(), self.assertRaises(target.InputError):
                self.load()

    def test_relabelled_test_population_rejected_before_raw_source(self):
        self.rows["eligible_training"][0].update(source_split="test", example_id=f"{target.REVISION}:test:0")
        self.persist()  # Even internally consistent, freshly hashed parents cannot relabel test lineage.
        with self.forbid_raw_reads(), self.assertRaisesRegex(target.InputError, "source split"):
            self.load()

    def test_all_hash_chain_tampering_is_rejected(self):
        paths = [self.access_path, self.partitions / "summary.json", self.partitions / "access-manifest.json",
                 self.partitions / "eligible-training.jsonl", self.raw / "train.json"]
        for path in paths:
            before = path.read_bytes()
            path.write_bytes(before + b" ")
            with self.subTest(path=path.name), self.assertRaisesRegex(target.InputError, "SHA-256 mismatch"):
                self.load()
            path.write_bytes(before)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("Invalid expected digest must not read")):
            with self.assertRaisesRegex(target.InputError, "Expected SHA-256"):
                target.load_development("eligible_training", self.access_path, "invalid", self.partitions, self.raw)

    def test_missing_duplicate_reordered_and_bad_lineage_membership_rejected(self):
        original = copy.deepcopy(self.rows["eligible_training"])
        variants = [original[:1], [original[0], original[0]], list(reversed(original)),
                    [dict(original[0], source_row=5, example_id=f"{target.REVISION}:train:5"), original[1]],
                    [dict(original[0], example_id=f'{"b" * 40}:train:0'), original[1]]]
        for rows in variants:
            self.rows["eligible_training"] = copy.deepcopy(rows)
            self.persist()
            with self.subTest(rows=len(rows)), self.forbid_raw_reads(), self.assertRaises(target.InputError):
                self.load()

    def test_parent_consistency_and_reference_label_or_text_mismatch(self):
        self.summary["output_files"]["eligible-training.jsonl"] = "0" * 64
        # Write only the parent chain so the deliberate population inconsistency remains.
        raw = json.dumps(self.summary).encode()
        (self.partitions / "summary.json").write_bytes(raw)
        self.access["parent_population_summary"]["sha256"] = sha(raw)
        self.access_path.write_text(json.dumps(self.access))
        self.expected = sha(self.access_path.read_bytes())
        with self.forbid_raw_reads(), self.assertRaisesRegex(target.InputError, "hash chain"):
            self.load()
        self.persist()
        self.source["train"][0]["label"] = 0
        self.persist()
        with self.assertRaisesRegex(target.InputError, "reference label"):
            self.load()
        self.source["train"][0]["label"] = 1
        self.source["train"][0]["prompt"] = "CHANGED SYNTHETIC CONTENT NEVER ECHO"
        self.persist()
        with self.assertRaisesRegex(target.InputError, "text hash") as raised:
            self.load()
        self.assertNotIn("CHANGED SYNTHETIC CONTENT", str(raised.exception))

    def test_original_lengths_and_source_counts_checked(self):
        self.rows["eligible_training"][0]["unicode_characters"] -= 1
        self.persist()
        with self.assertRaisesRegex(target.InputError, "lengths disagree"):
            self.load()
        self.source["train"].append({"prompt": "extra", "label": 0})
        self.persist()
        with self.assertRaisesRegex(target.InputError, "array count"):
            self.load()

    def test_verbatim_internal_records_safe_repr_and_text_free_reproducible_output(self):
        loaded = self.load()
        self.assertEqual([record.source_row for record in loaded.records], [0, 2])
        self.assertEqual([record.prompt for record in loaded.records],
                         [self.source["train"][i]["prompt"] for i in (0, 2)])
        self.assertFalse(hasattr(loaded.records[0], "label"))
        self.assertEqual([r["label"] for r in loaded.references], [1, 0])
        for prompt in (self.source["train"][i]["prompt"] for i in (0, 2)):
            self.assertNotIn(prompt, repr(loaded))
            self.assertNotIn(prompt, repr(loaded.records))
        first, second = self.root / "first", self.root / "second"
        evidence = target.preflight("eligible_training", self.access_path, self.expected, self.partitions, self.raw, first)
        target.preflight("eligible_training", self.access_path, self.expected, self.partitions, self.raw, second)
        self.assertEqual({p.name: p.read_bytes() for p in first.iterdir()}, {p.name: p.read_bytes() for p in second.iterdir()})
        self.assertEqual(evidence["expected_rows"], 2)
        self.assertEqual(evidence["validated_rows"], 2)
        self.assertFalse(evidence["human_review_performed"])
        self.assertFalse(evidence["teammate_attestation_required"])
        self.assertFalse(evidence["tokenization_performed"])
        self.assertFalse(evidence["test_performance_released"])
        rows = [json.loads(line) for line in (first / "examples.jsonl").read_bytes().splitlines()]
        self.assertEqual(rows, self.rows["eligible_training"])
        self.assertTrue(all("prompt" not in row for row in rows))
        self.assertEqual(self.load("eligible_validation").records[0].prompt, "validation café")

    def test_existing_output_refused_before_input_reads_and_preserved(self):
        out = self.root / "existing"
        out.mkdir()
        (out / "keep.txt").write_bytes(b"preserve")
        with patch.object(Path, "read_bytes", side_effect=AssertionError("No input read needed")):
            with self.assertRaisesRegex(target.InputError, "already exists"):
                target.preflight("eligible_training", self.access_path, self.expected, self.partitions, self.raw, out)
        self.assertEqual((out / "keep.txt").read_bytes(), b"preserve")

    def test_cli_rejection_does_not_echo_malformed_source(self):
        self.source["train"][0] = {"prompt": "DO NOT ECHO THIS SOURCE", "label": True}
        self.persist()
        stderr = io.StringIO()
        argv = ["input_data", "--role", "eligible_training", "--access", str(self.access_path),
                "--access-sha256", self.expected, "--partitions", str(self.partitions),
                "--raw-dir", str(self.raw), "--output", str(self.root / "out")]
        with patch.object(target.sys, "argv", argv), patch.object(target.sys, "stderr", stderr):
            self.assertEqual(target.main(), 2)
        self.assertNotIn("DO NOT ECHO", stderr.getvalue())
        self.assertFalse((self.root / "out").exists())


if __name__ == "__main__":
    unittest.main()
