import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from precision_benchmark import partition_data as partition

# Invented rows under the approved identifier exercise the build contract only;
# these temporary fixtures do not claim to be actual PromptShield source data.
REVISION = partition.APPROVED_REVISION


def identity(split, position, group, label=0):
    return {"example_id": f"{REVISION}:{split}:{position}", "source_split": split,
            "source_row": position, "label": label, "raw_text_sha256": group,
            "unicode_characters": 8, "utf8_bytes": 8}


def encoded(rows):
    return "".join(json.dumps(row) + "\n" for row in rows).encode()


def basic_rows():
    return [identity("train", 0, "e" * 64), identity("validation", 0, "f" * 64),
            identity("test", 0, "1" * 64), identity("test", 1, "2" * 64),
            identity("test", 2, "3" * 64, 1), identity("test", 3, "4" * 64, 1)]


class PartitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def inputs(self, rows=None):
        identities = self.root / "identities.jsonl"
        identities.write_bytes(encoded(basic_rows() if rows is None else rows))
        identity_sha = hashlib.sha256(identities.read_bytes()).hexdigest()
        hashes = {name: hashlib.sha256(name.encode()).hexdigest() for name in partition.SOURCE_FILES}
        provenance = {"source_api": {"id": partition.DATASET, "sha": REVISION},
                      "output_files": {"row-identities.jsonl": identity_sha},
                      "files": {name: {"sha256": value} for name, value in hashes.items()}}
        receipt = {"dataset": partition.DATASET, "revision": REVISION, "files": hashes}
        provenance_path, receipt_path = self.root / "provenance.json", self.root / "receipt.json"
        provenance_path.write_text(json.dumps(provenance))
        receipt_path.write_text(json.dumps(receipt))
        return [identities, identity_sha, provenance_path, hashlib.sha256(provenance_path.read_bytes()).hexdigest(),
                receipt_path, hashlib.sha256(receipt_path.read_bytes()).hexdigest(), REVISION]

    def test_whole_group_prefix_boundary_tie_and_absent_class(self):
        # Explicit group order 1,2,3 with sizes 1,4,1: target 3; prefixes 1 and 5
        # are equally close, so A must take the one-row prefix, not split size 4.
        # A single class-1 group cannot be split: empty A wins its 0/2 tie.
        test = [identity("test", i, key * 64, label) for i, (key, label) in enumerate(
            [("2", 0), ("1", 0), ("2", 0), ("3", 0), ("2", 0), ("2", 0), ("4", 1), ("4", 1)])]
        observed_keys = []

        def ordered_digest(value):
            observed_keys.append(value.decode())
            return value.decode().split(":")[-1]

        with patch.object(partition, "digest", side_effect=ordered_digest):
            selected = partition.half_groups(test)
            no_class_one = partition.half_groups(test[:6])
        self.assertEqual(selected, {"1" * 64})
        self.assertEqual(no_class_one, selected)
        self.assertTrue(all(value.startswith("precision-aware-inference:p1a-ab-candidate:v1:20261117:") for value in observed_keys))
        self.assertIn(partition.NAMESPACE + ":1:" + "4" * 64, observed_keys)

    def test_protocol_overlap_precedence_and_source_order(self):
        rows = [identity("train", 0, "1" * 64), identity("train", 1, "2" * 64), identity("train", 2, "3" * 64),
                identity("validation", 0, "1" * 64), identity("validation", 1, "2" * 64), identity("validation", 2, "4" * 64),
                identity("test", 0, "1" * 64), identity("test", 1, "5" * 64)]
        # A shuffled file must still emit original source order, not incidental read order.
        source = partition.read_identities(encoded(list(reversed(rows))), REVISION)
        populations, exclusions, intersections = partition.construct(source)
        self.assertEqual([r["source_row"] for r in populations["eligible_training"]], [2])
        self.assertEqual([r["source_row"] for r in populations["eligible_validation"]], [1, 2])
        self.assertEqual([(r["source_split"], r["source_row"], r["exclusion_reason"]) for r in exclusions],
                         [("train", 0, "exact_text_in_official_test"),
                          ("train", 1, "exact_text_in_retained_validation"),
                          ("validation", 0, "exact_text_in_official_test")])
        self.assertEqual({r["example_id"] for role in ("test_a", "test_b") for r in populations[role]},
                         {f"{REVISION}:test:0", f"{REVISION}:test:1"})
        self.assertTrue(all(value == 0 for value in intersections.values()))
        for role, values in populations.items():
            self.assertTrue(all(r["data_role"] == role for r in values))
            self.assertEqual([r["source_row"] for r in values], sorted(r["source_row"] for r in values))

    def test_invalid_identity_label_hash_schema_and_lineage_rejected(self):
        mutations = [{"label": True}, {"label": 2}, {"raw_text_sha256": "A" * 64},
                     {"source_row": -1}, {"source_row": True}, {"source_split": "test_a"},
                     {"example_id": f'{"b" * 40}:train:0'}, {"unicode_characters": 9},
                     {"prompt": "must not be displayed"}]
        for mutation in mutations:
            rows = basic_rows()
            rows[0].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError) as error:
                partition.read_identities(encoded(rows), REVISION)
            self.assertNotIn("must not be displayed", str(error.exception))
        for raw in (b"", b"\n", b'{"example_id":1,"example_id":2}\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                partition.read_identities(raw, REVISION)
        with self.assertRaisesRegex(ValueError, "immutable"):
            partition.read_identities(encoded(basic_rows()), "main")

    def test_duplicates_missing_positions_and_conflicting_groups_rejected(self):
        rows = basic_rows()
        with self.assertRaisesRegex(ValueError, "duplicate identity"):
            partition.read_identities(encoded(rows + [rows[0]]), REVISION)
        rows[-1] = identity("test", 4, "4" * 64, 1)
        with self.assertRaisesRegex(ValueError, "contiguous"):
            partition.read_identities(encoded(rows), REVISION)
        rows = basic_rows()
        rows[0]["raw_text_sha256"] = rows[-1]["raw_text_sha256"]
        with self.assertRaisesRegex(ValueError, "conflicting labels"):
            partition.read_identities(encoded(rows), REVISION)
        with self.assertRaisesRegex(ValueError, "every original split"):
            partition.read_identities(encoded(basic_rows()[1:]), REVISION)

    def test_input_tampering_and_provenance_binding_fail_before_output(self):
        args = self.inputs()
        for index in (0, 2, 4):
            path = args[index]
            before = path.read_bytes()
            path.write_bytes(before + b" ")
            output = self.root / "rejected"
            with self.subTest(input=index), self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                partition.build(*args, output)
            self.assertFalse(output.exists())
            path.write_bytes(before)
        provenance = json.loads(args[2].read_text())
        receipt = json.loads(args[4].read_text())
        for change in (lambda p: p["source_api"].update(sha="b" * 40),
                       lambda p: p["source_api"].update(id="other/dataset"),
                       lambda p: p["output_files"].update({"row-identities.jsonl": "b" * 64})):
            invalid = copy.deepcopy(provenance)
            change(invalid)
            with self.assertRaises(ValueError):
                partition.verify_source_records(invalid, receipt, REVISION, args[1])
        receipt["files"]["test.json"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "receipt and provenance"):
            partition.verify_source_records(provenance, receipt, REVISION, args[1])

    def test_d008_build_rejects_consistent_unapproved_revision_before_reading(self):
        args = self.inputs()
        other_revision = "b" * 40
        # Every supplied source record consistently describes a different revision.
        # Generic parsing can accept it, but it cannot claim the D-008 decision.
        args[0].write_bytes(args[0].read_bytes().replace(REVISION.encode(), other_revision.encode()))
        args[1] = hashlib.sha256(args[0].read_bytes()).hexdigest()
        provenance = json.loads(args[2].read_text())
        provenance["source_api"]["sha"] = other_revision
        provenance["output_files"]["row-identities.jsonl"] = args[1]
        args[2].write_text(json.dumps(provenance))
        args[3] = hashlib.sha256(args[2].read_bytes()).hexdigest()
        receipt = json.loads(args[4].read_text())
        receipt["revision"] = other_revision
        args[4].write_text(json.dumps(receipt))
        args[5] = hashlib.sha256(args[4].read_bytes()).hexdigest()
        args[6] = other_revision
        output = self.root / "unapproved"
        with self.assertRaisesRegex(ValueError, "D-008.*approved revision"):
            partition.build(*args, output)
        self.assertFalse(output.exists())
        with patch.object(partition, "checked_bytes") as read:
            with self.assertRaisesRegex(ValueError, "D-008.*approved revision"):
                partition.build(*args, output)
            read.assert_not_called()

    def test_artifacts_are_reproducible_role_bound_and_never_overwritten(self):
        args = self.inputs(list(reversed(basic_rows())))
        first, second = self.root / "first", self.root / "second"
        summary = partition.build(*args, first)
        partition.build(*args, second)
        # Source files referenced by the receipt do not exist in this synthetic setup;
        # construction succeeds using only administrative identities and source records.
        self.assertEqual({p.name: p.read_bytes() for p in first.iterdir()},
                         {p.name: p.read_bytes() for p in second.iterdir()})
        self.assertEqual(summary["review_status"], "human_review_pending")
        self.assertFalse(summary["phase_closeout"])
        self.assertEqual(summary["exclusions"]["rows"], 0)
        access = json.loads((first / "access-manifest.json").read_text())
        for role, details in access["roles"].items():
            self.assertEqual(details["review_status"], "human_review_pending")
            self.assertEqual(details["release_status"], "pending")
            raw = (first / details["file"]).read_bytes()
            self.assertNotIn(b"\r", raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), details["sha256"])
            rows = [json.loads(line) for line in raw.splitlines()]
            self.assertTrue(all(r["data_role"] == role and "prompt" not in r for r in rows))
            ids = [r["example_id"] for r in rows]
            self.assertEqual(summary["populations"][role]["ordered_id_sha256"],
                             hashlib.sha256("".join(i + "\n" for i in ids).encode()).hexdigest())
            self.assertEqual(summary["populations"][role]["membership_sha256"],
                             hashlib.sha256("".join(i + "\n" for i in sorted(ids)).encode()).hexdigest())
        self.assertIn("P1-C", access["roles"]["test_a"]["release_condition"])
        self.assertIn("P2-D", access["roles"]["test_b"]["release_condition"])
        before = {p.name: p.read_bytes() for p in first.iterdir()}
        with self.assertRaisesRegex(ValueError, "already exists"):
            partition.build(*args, first)
        self.assertEqual(before, {p.name: p.read_bytes() for p in first.iterdir()})


if __name__ == "__main__":
    unittest.main()
