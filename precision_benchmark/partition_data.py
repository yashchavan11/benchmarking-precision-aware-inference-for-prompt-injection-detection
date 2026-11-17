"""Build D-008 review-ready populations from pinned, text-free audit identities.

No prompts, network requests, model outputs, or evaluation releases are involved.
All expected hashes are required; existing output directories are never overwritten.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys

from .artifacts import parse_json

DATASET = "hendzh/PromptShield"
DECISION = "D-008"
APPROVED_REVISION = "a5234cb1f5cdb256600cab64b8c961195b5e8404"
NAMESPACE = "precision-aware-inference:p1a-ab-candidate:v1:20261117"
SPLITS = ("train", "validation", "test")
SOURCE_FILES = {"README.md", "train.json", "validation.json", "test.json", "repository-metadata.json"}
IDENTITY_FIELDS = {"example_id", "label", "raw_text_sha256", "source_row", "source_split",
                   "unicode_characters", "utf8_bytes"}
ROLE_FILES = {"eligible_training": "eligible-training.jsonl",
              "eligible_validation": "eligible-validation.jsonl",
              "test_a": "test-a.jsonl", "test_b": "test-b.jsonl"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_bytes(path, expected):
    require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
            "expected SHA-256 must be 64 lowercase hexadecimal characters")
    raw = Path(path).read_bytes()
    require(digest(raw) == expected, "input SHA-256 mismatch; preserve and investigate changed input")
    return raw


def object_from_bytes(raw):
    try:
        value = parse_json(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise ValueError("invalid JSON source record") from None
    require(isinstance(value, dict), "expected a JSON source object")
    return value


def read_identities(raw, revision):
    require(isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision) is not None,
            "revision must be an immutable 40-character lowercase SHA")
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeError:
        raise ValueError("identities must be UTF-8") from None
    require(bool(lines), "identity input is empty")
    rows = []
    for number, line in enumerate(lines, 1):
        try:
            row = parse_json(line)
        except ValueError:
            raise ValueError(f"identity line {number}: invalid JSON") from None
        require(isinstance(row, dict) and set(row) == IDENTITY_FIELDS,
                f"identity line {number}: expected text-free audit identity fields only")
        require(isinstance(row["source_split"], str) and row["source_split"] in SPLITS,
                f"identity line {number}: invalid source split")
        require(type(row["source_row"]) is int and row["source_row"] >= 0,
                f"identity line {number}: invalid original row position")
        require(row["example_id"] == f'{revision}:{row["source_split"]}:{row["source_row"]}',
                f"identity line {number}: ID does not match pinned revision and original lineage")
        require(type(row["label"]) is int and row["label"] in (0, 1),
                f"identity line {number}: label must be integer 0 or 1")
        require(isinstance(row["raw_text_sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", row["raw_text_sha256"]) is not None,
                f"identity line {number}: invalid raw-text hash")
        require(type(row["unicode_characters"]) is int and type(row["utf8_bytes"]) is int
                and 0 <= row["unicode_characters"] <= row["utf8_bytes"],
                f"identity line {number}: invalid administrative lengths")
        rows.append(row)
    require(len({r["example_id"] for r in rows}) == len(rows), "duplicate identity ID")
    by_split = {}
    for split in SPLITS:
        ordered = sorted((r for r in rows if r["source_split"] == split), key=lambda r: r["source_row"])
        require(bool(ordered), "every original split must be represented")
        require([r["source_row"] for r in ordered] == list(range(len(ordered))),
                f"{split}: original row positions must cover the complete contiguous source")
        by_split[split] = ordered
    labels = {}
    for row in rows:
        key = row["raw_text_sha256"]
        require(key not in labels or labels[key] == row["label"],
                "conflicting labels within an exact-text group require scientific resolution")
        labels[key] = row["label"]
    return by_split


def verify_source_records(provenance, receipt, revision, identities_sha256):
    api = provenance.get("source_api")
    require(isinstance(api, dict) and api.get("id") == DATASET and api.get("sha") == revision,
            "source provenance does not identify the selected dataset revision")
    outputs = provenance.get("output_files")
    require(isinstance(outputs, dict) and outputs.get("row-identities.jsonl") == identities_sha256,
            "source provenance does not bind the expected identity bytes")
    files = provenance.get("files")
    require(isinstance(files, dict) and set(files) == SOURCE_FILES,
            "source provenance must cover every original source file")
    hashes = {}
    for name, entry in files.items():
        require(isinstance(entry, dict) and isinstance(entry.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is not None,
                "source provenance contains an invalid file hash")
        hashes[name] = entry["sha256"]
    require(receipt.get("dataset") == DATASET and receipt.get("revision") == revision
            and receipt.get("files") == hashes, "source receipt and provenance differ")
    return hashes


def half_groups(test_rows):
    """D-008: nearest half by class in seeded group order; ties prefer fewer A rows."""
    groups = defaultdict(list)
    for row in test_rows:
        groups[row["raw_text_sha256"]].append(row)
    chosen = set()
    for label in (0, 1):
        keys = [key for key, group in groups.items() if group[0]["label"] == label]
        keys.sort(key=lambda key: (digest(f"{NAMESPACE}:{label}:{key}".encode("utf-8")), key))
        total = sum(len(groups[key]) for key in keys)
        prefix = best_rows = best_cut = 0
        best_distance = total
        for cut, key in enumerate(keys, 1):
            prefix += len(groups[key])
            distance = abs(2 * prefix - total)
            if (distance, prefix) < (best_distance, best_rows):
                best_distance, best_rows, best_cut = distance, prefix, cut
        chosen.update(keys[:best_cut])
    return chosen


def construct(by_split):
    test_hashes = {r["raw_text_sha256"] for r in by_split["test"]}
    validation_hashes = {r["raw_text_sha256"] for r in by_split["validation"]
                         if r["raw_text_sha256"] not in test_hashes}
    populations, exclusions = {}, []
    for split, role in (("train", "eligible_training"), ("validation", "eligible_validation")):
        populations[role] = []
        for row in by_split[split]:
            key = row["raw_text_sha256"]
            reason = ("exact_text_in_official_test" if key in test_hashes else
                      "exact_text_in_retained_validation" if split == "train" and key in validation_hashes else None)
            if reason:
                exclusions.append({**row, "data_role": "excluded_development", "exclusion_reason": reason})
            else:
                populations[role].append({**row, "data_role": role})
    selected = half_groups(by_split["test"])
    for role, in_a in (("test_a", True), ("test_b", False)):
        populations[role] = [{**row, "data_role": role} for row in by_split["test"]
                             if (row["raw_text_sha256"] in selected) == in_a]
    group_sets = {role: {r["raw_text_sha256"] for r in rows} for role, rows in populations.items()}
    intersections = {f"{left}__{right}": len(group_sets[left] & group_sets[right])
                     for left, right in itertools.combinations(ROLE_FILES, 2)}
    require(not any(intersections.values()), "constructed populations violate exact-group isolation")
    expected_ids = {r["example_id"] for rows in by_split.values() for r in rows}
    output_ids = [r["example_id"] for rows in populations.values() for r in rows]
    output_ids.extend(r["example_id"] for r in exclusions)
    require(len(output_ids) == len(set(output_ids)) and set(output_ids) == expected_ids,
            "constructed populations/exclusions do not cover every original ID exactly once")
    return populations, exclusions, intersections


def id_hash(ids):
    return digest("".join(value + "\n" for value in ids).encode("utf-8"))


def support(rows):
    class_counts = Counter(r["label"] for r in rows)
    groups = Counter(r["raw_text_sha256"] for r in rows)
    ids = [r["example_id"] for r in rows]
    return {"rows": len(rows), "class_counts": {str(c): class_counts[c] for c in (0, 1)},
            "exact_text_groups": len(groups),
            "class_groups": {str(c): len({r["raw_text_sha256"] for r in rows if r["label"] == c}) for c in (0, 1)},
            "duplicate_groups": sum(n > 1 for n in groups.values()),
            "largest_group": max(groups.values(), default=0),
            "ordered_id_sha256": id_hash(ids), "membership_sha256": id_hash(sorted(ids))}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def build(identities, identities_sha256, provenance_path, provenance_sha256,
          receipt_path, receipt_sha256, revision, output):
    require(revision == APPROVED_REVISION,
            "D-008 construction requires its exact approved revision; another revision needs a new decision")
    output = Path(output)
    require(not output.exists(), "output directory already exists; preserve it and choose a new location")
    identity_bytes = checked_bytes(identities, identities_sha256)
    provenance = object_from_bytes(checked_bytes(provenance_path, provenance_sha256))
    receipt = object_from_bytes(checked_bytes(receipt_path, receipt_sha256))
    by_split = read_identities(identity_bytes, revision)
    source_hashes = verify_source_records(provenance, receipt, revision, identities_sha256)
    populations, exclusions, intersections = construct(by_split)
    output.mkdir(parents=True, exist_ok=False)
    output_hashes = {}
    for filename, rows in [(ROLE_FILES[role], rows) for role, rows in populations.items()] + [("development-exclusions.jsonl", exclusions)]:
        raw = "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows).encode("utf-8")
        (output / filename).write_bytes(raw)
        output_hashes[filename] = digest(raw)
    access = {"schema_version": 1, "construction_decision": DECISION,
              "review_status": "human_review_pending", "phase_closeout": False,
              "prior_team_exposure": "incompletely_declared; see Q-013 and exposure log",
              "enforcement": "Declarative workflow metadata; future loaders must enforce roles. Public files are not cryptographically sealed.",
              "roles": {}}
    for role, filename in ROLE_FILES.items():
        gate = ("P1-A closeout and human scientific review" if role.startswith("eligible_") else
                "P1-C freeze before P1-D Test-A performance" if role == "test_a" else
                "P2-D policy freeze before P2-E; no Test-B predictions earlier by default")
        access["roles"][role] = {"file": filename, "sha256": output_hashes[filename],
                                 "review_status": "human_review_pending", "release_status": "pending",
                                 "release_condition": gate,
                                 "current_access": "administrative identities, reference labels and aggregate support only"}
    write_json(output / "access-manifest.json", access)
    output_hashes["access-manifest.json"] = digest((output / "access-manifest.json").read_bytes())
    summary = {"schema_version": 1, "dataset": DATASET, "revision": revision,
               "construction_decision": DECISION, "construction_status": "review_ready",
               "review_status": "human_review_pending", "phase_closeout": False,
               "namespace": NAMESPACE, "target_A_fraction": "1/2",
               "algorithm": "Within class, seeded SHA256 group order then raw hash tie-break; nearest-half prefix by rows, tie fewer A rows; B complement; outputs in original source order.",
               "eligibility": "test-overlap first, then retained-validation precedence; no text transformation or relabeling",
               "id_hash_method": "SHA256 of UTF-8 IDs each followed by LF; membership uses sorted IDs; ordered uses source order",
               "inputs": {"identities": {"path": Path(identities).as_posix(), "sha256": identities_sha256},
                          "source_provenance": {"path": Path(provenance_path).as_posix(), "sha256": provenance_sha256},
                          "source_receipt": {"path": Path(receipt_path).as_posix(), "sha256": receipt_sha256}},
               "original_source_sha256": source_hashes,
               "original_splits": {split: support(rows) for split, rows in by_split.items()},
               "populations": {role: {"file": ROLE_FILES[role], **support(rows)} for role, rows in populations.items()},
               "exclusions": {"file": "development-exclusions.jsonl", **support(exclusions),
                              "by_reason": dict(sorted(Counter(r["exclusion_reason"] for r in exclusions).items()))},
               "isolation_intersections": intersections, "all_source_ids_accounted_exactly_once": True,
               "output_files": output_hashes,
               "code_sha256": {"precision_benchmark/partition_data.py": digest(Path(__file__).read_bytes()),
                               "precision_benchmark/artifacts.py": digest(Path(__file__).with_name("artifacts.py").read_bytes())},
               "limitations": ["No prompts, model outputs, performance, or new source downloads accessed.",
                               "Local retained provenance is not independent source attestation.",
                               "Human scientific review and prior team exposure declarations remain pending.",
                               "Near-duplicate/template dependence, annotation truth and pretrained contamination remain unresolved.",
                               "Support counts do not establish power; no evaluation release or P1-A closeout."]}
    write_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("identities", "provenance", "receipt", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("identities-sha256", "provenance-sha256", "receipt-sha256", "revision"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        result = build(args.identities, args.identities_sha256, args.provenance, args.provenance_sha256,
                       args.receipt, args.receipt_sha256, args.revision, args.output)
    except (OSError, ValueError) as error:
        print(f"Partition construction failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["construction_status"], "review_status": result["review_status"],
                      "populations": {role: value["rows"] for role, value in result["populations"].items()},
                      "summary": (args.output / "summary.json").as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
