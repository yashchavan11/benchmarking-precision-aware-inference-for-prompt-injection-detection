"""Load verified development text under D-009; never open an official-test source.

The CLI writes text-free preflight evidence only. Raw prompts stay unchanged in
internal InputRecord.prompt values, which are excluded from repr. No tokenization,
model execution, normalization, or new evaluation release is performed.
"""

import argparse
from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import sys

from .artifacts import parse_json

DATASET = "hendzh/PromptShield"
REVISION = "a5234cb1f5cdb256600cab64b8c961195b5e8404"
ROLES = {"eligible_training": ("train", "eligible-training.jsonl", "train.json"),
         "eligible_validation": ("validation", "eligible-validation.jsonl", "validation.json")}
IDENTITY_FIELDS = {"example_id", "source_split", "source_row", "label", "raw_text_sha256",
                   "unicode_characters", "utf8_bytes", "data_role"}
AUTHORIZED_STATUS = "authorized_for_input_preflight_and_permitted_development"


class InputError(ValueError):
    """Fixed diagnostic messages never include source text or malformed input values."""


@dataclass(frozen=True)
class InputRecord:
    example_id: str
    source_split: str
    source_row: int
    raw_text_sha256: str
    prompt: str = field(repr=False)


@dataclass(frozen=True)
class LoadedDevelopment:
    records: tuple = field(repr=False)
    references: tuple = field(repr=False)
    evidence: dict


def require(condition, message):
    if not condition:
        raise InputError(message)


def require_role(role):
    require(isinstance(role, str) and role in ROLES,
            "Only eligible_training and eligible_validation are authorized; no source was opened")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def checked_bytes(path, expected):
    require(valid_sha(expected), "Expected SHA-256 is invalid")
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise InputError("Required artifact could not be read") from None
    require(digest(raw) == expected, "Artifact SHA-256 mismatch; preserve changed input")
    return raw


def parsed(raw, object_required=True):
    try:
        value = parse_json(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise InputError("Invalid JSON artifact; source contents suppressed") from None
    if object_required:
        require(isinstance(value, dict), "Expected a JSON metadata object")
    return value


def fixed_path(directory, filename):
    """Only fixed filenames in the supplied root; reject file-link redirection."""
    root = Path(directory).resolve()
    path = root / filename
    require(path.resolve() == path, "Artifact path redirects outside its fixed filename")
    return path


def id_hash(ids):
    return digest("".join(value + "\n" for value in ids).encode("utf-8"))


def validate_access(access):
    require(access.get("schema_version") == 1 and type(access.get("schema_version")) is int
            and access.get("dataset") == DATASET and access.get("revision") == REVISION
            and access.get("construction_decision") == "D-008"
            and access.get("continuation_decision") == "D-009", "Access decision or pinned source identity mismatch")
    require(access.get("human_review_performed") is False,
            "This D-009 contract does not attest human scientific review")
    require(access.get("protected_roles") == ["test_a", "test_b"], "Protected-role declaration mismatch")
    require(isinstance(access.get("roles"), dict) and set(access["roles"]) == set(ROLES),
            "Access amendment must contain only the two development roles")
    for role, (split, population_file, source_file) in ROLES.items():
        entry = access["roles"][role]
        require(isinstance(entry, dict) and entry.get("source_split") == split
                and entry.get("population_file") == population_file and entry.get("source_file") == source_file,
                "Access role uses an unexpected population or source filename/lineage")
        require(entry.get("status") == AUTHORIZED_STATUS and entry.get("teammate_attestation_required") is False,
                "Development role is not authorized by this continuation contract")
        require(integer(entry.get("row_count"), 1)
                and all(valid_sha(entry.get(key)) for key in ("population_sha256", "source_sha256", "ordered_id_sha256")),
                "Access role has invalid expected counts or hashes")
    for key, name in (("parent_population_summary", "summary.json"),
                      ("parent_access_manifest", "access-manifest.json")):
        entry = access.get(key)
        require(isinstance(entry, dict) and entry.get("filename") == name and valid_sha(entry.get("sha256")),
                "Access parent reference must use the fixed filename and a SHA-256")


def validate_parents(summary, historical_access, access, role):
    split, population_file, source_file = ROLES[role]
    entry = access["roles"][role]
    require(summary.get("schema_version") == 1 and type(summary.get("schema_version")) is int
            and summary.get("dataset") == DATASET and summary.get("revision") == REVISION
            and summary.get("construction_decision") == "D-008"
            and summary.get("all_source_ids_accounted_exactly_once") is True,
            "Parent population summary does not match approved construction/source")
    require(historical_access.get("schema_version") == 1
            and type(historical_access.get("schema_version")) is int
            and historical_access.get("construction_decision") == "D-008",
            "Historical access manifest does not identify D-008")
    population = summary["populations"][role]
    old_role = historical_access["roles"][role]
    require(population["file"] == population_file and old_role["file"] == population_file
            and old_role["sha256"] == entry["population_sha256"]
            and summary["output_files"][population_file] == entry["population_sha256"]
            and summary["output_files"]["access-manifest.json"] == access["parent_access_manifest"]["sha256"],
            "Population/access hash chain is inconsistent")
    require(integer(population["rows"], 1) and population["rows"] == entry["row_count"]
            and population["ordered_id_sha256"] == entry["ordered_id_sha256"]
            and valid_sha(population["membership_sha256"]), "Expected population counts or ID hashes disagree")
    require(summary["original_source_sha256"][source_file] == entry["source_sha256"],
            "Original source hash does not match authorized role")
    require(integer(summary["original_splits"][split]["rows"], 1)
            and summary["original_splits"][split]["rows"] >= population["rows"],
            "Original source count is inconsistent with expected membership")
    return population


def membership_rows(raw, role, expected):
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeError:
        raise InputError("Population identities must be UTF-8") from None
    require(len(lines) == expected["rows"], "Population does not contain the full expected row count")
    split = ROLES[role][0]
    rows, ids, previous, groups = [], set(), -1, {}
    for line in lines:
        row = parsed(line.encode("utf-8"))
        require(set(row) == IDENTITY_FIELDS, "Population must contain only the approved text-free identity fields")
        require(row["data_role"] == role and row["source_split"] == split,
                "Population role or original source split is not authorized")
        position = row["source_row"]
        require(integer(position) and position > previous, "Population positions must be unique and in original source order")
        require(row["example_id"] == f"{REVISION}:{split}:{position}", "Population ID disagrees with pinned original lineage")
        require(row["example_id"] not in ids, "Population contains a duplicate ID")
        require(type(row["label"]) is int and row["label"] in (0, 1), "Population label must be integer 0 or 1")
        require(valid_sha(row["raw_text_sha256"]) and integer(row["unicode_characters"])
                and integer(row["utf8_bytes"]) and row["unicode_characters"] <= row["utf8_bytes"],
                "Population hash or administrative lengths are invalid")
        key = row["raw_text_sha256"]
        require(key not in groups or groups[key] == row["label"], "Population has conflicting exact-group labels")
        groups[key] = row["label"]
        ids.add(row["example_id"])
        previous = position
        rows.append(row)
    ordered_ids = [row["example_id"] for row in rows]
    require(id_hash(ordered_ids) == expected["ordered_id_sha256"]
            and id_hash(sorted(ordered_ids)) == expected["membership_sha256"], "Population ID hashes disagree with expected membership")
    class_counts = {str(label): sum(r["label"] == label for r in rows) for label in (0, 1)}
    require(expected["class_counts"] == class_counts
            and all(type(n) is int for n in expected["class_counts"].values())
            and expected["exact_text_groups"] == len(groups)
            and type(expected["exact_text_groups"]) is int, "Population class/group counts disagree with parent summary")
    return rows


def load_development(role, access_path, expected_access_sha256, partition_dir, raw_dir):
    # Must precede every input read, including metadata. Tests spy on read_bytes.
    require_role(role)
    try:
        access = parsed(checked_bytes(access_path, expected_access_sha256))
        validate_access(access)
        summary_ref, old_access_ref = access["parent_population_summary"], access["parent_access_manifest"]
        summary = parsed(checked_bytes(fixed_path(partition_dir, "summary.json"), summary_ref["sha256"]))
        old_access = parsed(checked_bytes(fixed_path(partition_dir, "access-manifest.json"), old_access_ref["sha256"]))
        expected = validate_parents(summary, old_access, access, role)
        split, population_file, source_file = ROLES[role]
        role_entry = access["roles"][role]
        population_raw = checked_bytes(fixed_path(partition_dir, population_file), role_entry["population_sha256"])
        rows = membership_rows(population_raw, role, expected)
        require(rows[-1]["source_row"] < summary["original_splits"][split]["rows"],
                "Population original row is outside the retained source count")
        # Every role, parent, membership and original-lineage check precedes this read.
        source = parsed(checked_bytes(fixed_path(raw_dir, source_file), role_entry["source_sha256"]), False)
        require(isinstance(source, list) and len(source) == summary["original_splits"][split]["rows"],
                "Original source array count differs from the retained audit")
        records = []
        for row in rows:
            position = row["source_row"]
            require(position < len(source), "Population original row is outside the verified source")
            item = source[position]
            require(isinstance(item, dict) and set(item) == {"prompt", "label"}
                    and isinstance(item["prompt"], str) and type(item["label"]) is int
                    and item["label"] in (0, 1), "Original source row schema is invalid; contents suppressed")
            require(item["label"] == row["label"], "Original reference label disagrees with the population")
            text = item["prompt"]
            encoded = text.encode("utf-8")
            require(digest(encoded) == row["raw_text_sha256"], "Original source text hash disagrees with the population")
            require(len(text) == row["unicode_characters"] and len(encoded) == row["utf8_bytes"],
                    "Original character/byte lengths disagree with the population")
            records.append(InputRecord(row["example_id"], split, position, row["raw_text_sha256"], text))
        evidence = {"schema_version": 1, "dataset": DATASET, "revision": REVISION, "data_role": role,
                    "construction_decision": "D-008", "continuation_decision": "D-009",
                    "status": "complete_for_development_input_preflight",
                    "allowed_purpose": "Input preflight and permitted development under the roadmap; no test performance or expensive pilot authorization",
                    "expected_rows": role_entry["row_count"], "validated_rows": len(records),
                    "class_counts": expected["class_counts"], "exact_text_groups": expected["exact_text_groups"],
                    "ordered_id_sha256": expected["ordered_id_sha256"], "membership_sha256": expected["membership_sha256"],
                    "inputs": {"development_access": {"path": Path(access_path).as_posix(), "sha256": expected_access_sha256},
                               "parent_population_summary": summary_ref, "parent_access_manifest": old_access_ref,
                               "population": {"filename": population_file, "sha256": role_entry["population_sha256"]},
                               "original_source": {"filename": source_file, "sha256": role_entry["source_sha256"]}},
                    "historical_access_disposition": "D-009 explicitly authorizes development use; unchanged D-008 access record is retained as history",
                    "human_review_performed": False, "teammate_attestation_required": False,
                    "prior_external_exposure": "unknown beyond recorded statements; not assumed absent",
                    "tokenization_performed": False, "model_inference_performed": False,
                    "phase_closeout": False, "test_performance_released": False,
                    "text_transformation": "none; original string and UTF-8 hash preserved",
                    "preflight_exports_raw_text": False,
                    "code_sha256": {"precision_benchmark/input_data.py": digest(Path(__file__).read_bytes()),
                                    "precision_benchmark/artifacts.py": digest(Path(__file__).with_name("artifacts.py").read_bytes())}}
        return LoadedDevelopment(tuple(records), tuple(rows), evidence)
    except InputError:
        raise
    except (KeyError, TypeError, AttributeError, UnicodeError, OSError, ValueError):
        raise InputError("Malformed input contract or source; contents suppressed") from None


def preflight(role, access_path, expected_access_sha256, partition_dir, raw_dir, output):
    require_role(role)
    output = Path(output)
    require(not output.exists(), "Output directory already exists; preserve it and select a new location")
    loaded = load_development(role, access_path, expected_access_sha256, partition_dir, raw_dir)
    raw = "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in loaded.references).encode("utf-8")
    evidence = {**loaded.evidence, "examples": {"filename": "examples.jsonl", "sha256": digest(raw)}}
    output.mkdir(parents=True, exist_ok=False)
    (output / "examples.jsonl").write_bytes(raw)
    (output / "preflight.json").write_text(json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n",
                                          encoding="utf-8", newline="\n")
    return evidence


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, "Invalid input-preflight arguments; use --help.\n")
    parser = SafeParser(description=__doc__)
    parser.add_argument("--role", required=True)
    parser.add_argument("--access-sha256", required=True)
    for name in ("access", "partitions", "raw-dir", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        result = preflight(args.role, args.access, args.access_sha256, args.partitions, args.raw_dir, args.output)
    except InputError as error:
        print(f"Development input preflight failed: {error}", file=sys.stderr)
        return 2
    except OSError:
        print("Development input preflight failed during output; preserve partial output.", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "data_role": result["data_role"],
                      "validated_rows": result["validated_rows"], "raw_text_exported": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
