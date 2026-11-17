"""Administrative PromptShield audit; never prints prompts or runs a classifier.

This module preserves source JSON, assigns revision/split/row IDs, and computes exact
UTF-8 text hashes. Its development projection applies only the protocol's overlap
precedence; it is NOT an approved eligibility manifest or a Test-A/Test-B partition.
"""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import statistics
import urllib.request

from .artifacts import parse_json

DATASET = "hendzh/PromptShield"
SPLITS = ("train", "validation", "test")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ordered_id_hash(ids):
    """Hash UTF-8 IDs in original source order, each followed by LF."""
    return digest("".join(example_id + "\n" for example_id in ids).encode("utf-8"))


def counts(rows):
    labels = Counter(row["label"] for row in rows)
    return {"rows": len(rows), "class_counts": {str(label): labels[label] for label in (0, 1)},
            "exact_text_groups": len({row["raw_text_sha256"] for row in rows})}


def length_summary(values):
    values = sorted(values)
    if not values:
        return {"n": 0}
    return {"n": len(values), "min": values[0], "median": statistics.median(values),
            "mean": statistics.mean(values),
            **{f"p{percent}": values[math.ceil(percent * len(values) / 100) - 1]
               for percent in (90, 95, 99)}, "max": values[-1]}


def audit_splits(source, revision, viewer_prefix_count=0):
    """Return aggregate audit, text-free row identities, and exclusion records."""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("revision must be an immutable 40-character lowercase Git SHA")
    if set(source) != set(SPLITS):
        raise ValueError("provide exactly train, validation, test")
    if type(viewer_prefix_count) is not int or viewer_prefix_count < 0:
        raise ValueError("viewer prefix count must be a nonnegative integer")
    rows, groups, schema = {}, defaultdict(list), {}
    for split in SPLITS:
        values = source[split]
        if not isinstance(values, list) or not values:
            raise ValueError(f"{split}: expected nonempty JSON array")
        rows[split] = []
        empty = whitespace = 0
        for position, value in enumerate(values):
            if not isinstance(value, dict) or set(value) != {"prompt", "label"}:
                raise ValueError(f"{split} row {position}: expected exactly prompt and label fields")
            prompt, label = value["prompt"], value["label"]
            if not isinstance(prompt, str):
                raise ValueError(f"{split} row {position}: prompt must be string")
            if type(label) is not int or label not in (0, 1):
                raise ValueError(f"{split} row {position}: label must be integer 0 or 1")
            encoded = prompt.encode("utf-8")
            row = {"example_id": f"{revision}:{split}:{position}", "source_split": split,
                   "source_row": position, "label": label, "raw_text_sha256": digest(encoded),
                   "unicode_characters": len(prompt), "utf8_bytes": len(encoded)}
            rows[split].append(row)
            groups[row["raw_text_sha256"]].append(row)
            empty += not prompt
            whitespace += bool(prompt) and not prompt.strip()
        schema[split] = {"container": "array", "fields": {"prompt": "string", "label": "integer"},
                         "observed_labels": sorted({r["label"] for r in rows[split]}),
                         "empty_text_rows": empty, "whitespace_only_rows": whitespace}
    split_hashes = {split: {r["raw_text_sha256"] for r in rows[split]} for split in SPLITS}
    conflicts = {key for key, group in groups.items() if len({r["label"] for r in group}) > 1}
    duplicate_groups = {key: group for key, group in groups.items() if len(group) > 1}
    overlap = {}
    for left, right in itertools.combinations(SPLITS, 2):
        shared = split_hashes[left] & split_hashes[right]
        overlap[f"{left}__{right}"] = {
            "shared_exact_text_groups": len(shared),
            "left_rows": counts([r for r in rows[left] if r["raw_text_sha256"] in shared]),
            "right_rows": counts([r for r in rows[right] if r["raw_text_sha256"] in shared])}
    split_summaries = {}
    for split in SPLITS:
        group_sizes = Counter(r["raw_text_sha256"] for r in rows[split])
        split_summaries[split] = {
            **counts(rows[split]), "ordered_id_sha256": ordered_id_hash([r["example_id"] for r in rows[split]]),
            "exact_text_groups_by_label": {str(label): len({r["raw_text_sha256"] for r in rows[split] if r["label"] == label}) for label in (0, 1)},
            "largest_exact_text_group_rows": max(group_sizes.values()),
            "duplicate_group_size_histogram": {str(size): n for size, n in sorted(Counter(group_sizes.values()).items()) if size > 1},
            "within_split_duplicate_groups": sum(n > 1 for n in group_sizes.values()),
            "within_split_duplicate_rows": sum(n for n in group_sizes.values() if n > 1),
            "within_split_excess_duplicate_rows": sum(n - 1 for n in group_sizes.values()),
            "rows_in_global_conflicting_label_groups": sum(r["raw_text_sha256"] in conflicts for r in rows[split]),
            "characters": length_summary([r["unicode_characters"] for r in rows[split]]),
            "utf8_bytes": length_summary([r["utf8_bytes"] for r in rows[split]])}
    # Official-test protection precedes validation precedence, regardless of future A/B allocation.
    protected = split_hashes["test"]
    kept_validation = [r for r in rows["validation"] if r["raw_text_sha256"] not in protected]
    validation_hashes = {r["raw_text_sha256"] for r in kept_validation}
    kept, excluded = {"validation": kept_validation}, []
    for split in ("train", "validation"):
        candidates = []
        for row in rows[split]:
            key = row["raw_text_sha256"]
            reason = ("exact_text_in_official_test" if key in protected else
                      "exact_text_in_retained_validation" if split == "train" and key in validation_hashes else None)
            if reason:
                excluded.append({**row, "exclusion_reason": reason})
            else:
                candidates.append(row)
        kept[split] = candidates
    kept_hashes = {split: {r["raw_text_sha256"] for r in kept[split]} for split in kept}
    projection = {}
    for split in ("train", "validation"):
        projection[split] = {
            **counts(kept[split]),
            "ordered_id_sha256": ordered_id_hash([r["example_id"] for r in kept[split]]),
            "excluded_by_reason": {reason: counts([r for r in excluded if r["source_split"] == split and r["exclusion_reason"] == reason])
                                   for reason in ("exact_text_in_official_test", "exact_text_in_retained_validation")},
            "remaining_conflicting_label_groups": len(kept_hashes[split] & conflicts),
            "remaining_rows_in_conflicting_label_groups": sum(r["raw_text_sha256"] in conflicts for r in kept[split])}
    intersection_checks = {
        "projected_train_vs_test": len(kept_hashes["train"] & protected),
        "projected_validation_vs_test": len(kept_hashes["validation"] & protected),
        "projected_train_vs_validation": len(kept_hashes["train"] & kept_hashes["validation"])}
    assert not any(intersection_checks.values())
    prefix_hashes = {r["raw_text_sha256"] for r in rows["train"][:viewer_prefix_count]}
    summary = {
        "dataset": DATASET, "revision": revision, "schema": schema, "splits": split_summaries,
        "all_splits": {**counts([r for split in SPLITS for r in rows[split]]),
                       "duplicate_groups": len(duplicate_groups),
                       "rows_in_duplicate_groups": sum(len(g) for g in duplicate_groups.values()),
                       "excess_duplicate_rows": sum(len(g) - 1 for g in duplicate_groups.values()),
                       "conflicting_label_groups": len(conflicts),
                       "rows_in_conflicting_label_groups": sum(len(groups[key]) for key in conflicts)},
        "split_overlaps": overlap, "development_overlap_projection": projection,
        "projection_isolation_checks": intersection_checks,
        "incidental_viewer_prefix_proxy": {
            "assumed_first_train_rows": min(viewer_prefix_count, len(rows["train"])),
            "assumption_not_verified_viewer_row_identity": True,
            "exact_groups_overlapping_test": len(prefix_hashes & protected),
            "test_rows_in_those_groups": sum(r["raw_text_sha256"] in prefix_hashes for r in rows["test"]),
            "projected_training_rows_in_those_groups": sum(r["raw_text_sha256"] in prefix_hashes for r in kept["train"])},
        "methods": {
            "text_hash": "SHA-256 of original decoded prompt encoded as UTF-8; no whitespace or Unicode normalization",
            "identity": "dataset-revision:original-split:zero-based-source-array-position",
            "ordered_id_hash": "SHA-256 of UTF-8 example IDs in original split order, each followed by LF",
            "lengths": "Unicode code points and UTF-8 bytes, not tokenizer lengths; p90/p95/p99 nearest-rank, median standard median",
            "eligibility_projection": "test-overlap exclusion first, then exclude training matching retained validation; retain all other rows, including unresolved conflicts"},
        "limitations": [
            "Administrative audit only; no model scores, predictions, or performance inspected.",
            "No Test-A/Test-B assignment, conflict-treatment decision, eligibility freeze, or pilot selection performed.",
            "Projection applies overlap precedence only; remaining conflicting labels need explicit review before inference.",
            "Exact-text hashing does not detect paraphrases/shared templates or pretrained-model contamination.",
            "Source has only prompt and label fields; no source-provided attack-family/group annotation.",
            "Tokenizer lengths/truncation and content-level truth of reference labels are not verified."]}
    identities = [r for split in SPLITS for r in rows[split]]
    return summary, identities, excluded, kept


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def acquire(revision, raw_dir, download, expected_provenance=None):
    """Download from a pinned URL only, retaining original bytes and safe provenance."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = raw_dir / "source-integrity.json"
    expected = None
    if receipt_path.exists():
        receipt = parse_json(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("dataset") != DATASET or receipt.get("revision") != revision:
            raise ValueError("cached integrity receipt does not match requested source")
        expected = receipt.get("files")
    elif expected_provenance is not None:
        earlier = parse_json(Path(expected_provenance).read_text(encoding="utf-8"))
        if earlier.get("source_api", {}).get("id") != DATASET or earlier.get("source_api", {}).get("sha") != revision:
            raise ValueError("earlier provenance does not match requested source")
        expected = {name: entry["sha256"] for name, entry in earlier["files"].items()}
    filenames = ("README.md", *(split + ".json" for split in SPLITS), "repository-metadata.json")
    if expected is not None and (not isinstance(expected, dict) or set(expected) != set(filenames)
                                 or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in expected.values())):
        raise ValueError("integrity receipt must cover every pinned source file with a SHA-256")
    files = {}
    for filename in filenames:
        url = (f"https://huggingface.co/api/datasets/{DATASET}/revision/{revision}" if filename == "repository-metadata.json"
               else f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{filename}")
        target = raw_dir / filename
        if target.exists():
            raw = target.read_bytes()
            if expected is not None:
                if digest(raw) != expected[filename]:
                    raise ValueError(f"{filename}: cached source SHA-256 mismatch; preserve and investigate the changed file")
            else:
                if not download:
                    raise ValueError("existing source cache has no integrity receipt; provide --expected-provenance or reverify with --download")
                with urllib.request.urlopen(url, timeout=60) as response:
                    remote = response.read()
                if raw != remote:
                    raise ValueError(f"{filename}: unverified cache differs from pinned retrieval; preserve it and use a fresh raw directory")
        else:
            if not download:
                raise FileNotFoundError(f"missing {filename}; use --download to retrieve the pinned source")
            with urllib.request.urlopen(url, timeout=60) as response:
                raw = response.read()
            if expected is not None and digest(raw) != expected[filename]:
                raise ValueError(f"{filename}: downloaded bytes differ from the retained source SHA-256")
            target.write_bytes(raw)
        files[filename] = {"url": url, "path": target.as_posix(), "bytes": len(raw), "sha256": digest(raw)}
    metadata_path = raw_dir / "repository-metadata.json"
    raw = metadata_path.read_bytes()
    metadata = parse_json(raw.decode("utf-8"))
    if metadata.get("sha") != revision or metadata.get("id") != DATASET:
        raise ValueError("repository metadata identity does not match requested source")
    source = {split: parse_json((raw_dir / f"{split}.json").read_text(encoding="utf-8")) for split in SPLITS}
    if not receipt_path.exists():
        write_json(receipt_path, {"dataset": DATASET, "revision": revision,
                                  "files": {name: entry["sha256"] for name, entry in files.items()}})
    return source, {"files": files, "source_api": {k: metadata.get(k) for k in ("id", "sha", "gated", "private", "lastModified", "cardData")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New directory; existing evidence is never overwritten")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--expected-provenance", type=Path, help="Earlier verified provenance to bootstrap an existing cache receipt")
    parser.add_argument("--viewer-prefix-count", type=int, default=0, help="Optional conservative proxy for incidental training-viewer exposure")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("revision must be a lowercase 40-character immutable Git SHA")
    if args.output.exists():
        parser.error("output must be a new directory")
    source, provenance = acquire(args.revision, args.raw_dir, args.download, args.expected_provenance)
    summary, identities, excluded, kept = audit_splits(source, args.revision, args.viewer_prefix_count)
    args.output.mkdir(parents=True, exist_ok=False)
    artifacts = {"row-identities.jsonl": identities, "development-exclusions.jsonl": excluded,
                 **{f"projected-{split}-identities.jsonl": kept[split] for split in ("train", "validation")}}
    for filename, values in artifacts.items():
        (args.output / filename).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in values), encoding="utf-8", newline="\n")
    write_json(args.output / "summary.json", summary)
    provenance.update({"retrieved_or_audited_at_utc": datetime.now(timezone.utc).isoformat(),
                       "audit_source_sha256": digest(Path(__file__).read_bytes()),
                       "output_files": {name: digest((args.output / name).read_bytes()) for name in [*artifacts, "summary.json"]}})
    write_json(args.output / "provenance.json", provenance)
    print(json.dumps({"revision": args.revision, "split_counts": {s: summary["splits"][s]["rows"] for s in SPLITS},
                      "summary": (args.output / "summary.json").as_posix(), "status": "administrative audit complete; eligibility/partition decisions pending"}))


if __name__ == "__main__":
    main()
