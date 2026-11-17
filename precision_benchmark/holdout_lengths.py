"""Separately authorized, aggregate-only official-test token-length administration.

Prepare/review this command before requesting its additional data-scope approval.
It does not release a test population to inference or modify development guards.
Native loading is lazy. No model, per-row exports, cap comparisons or A/B breakdown.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import sys

from . import contract_audit, input_data, tokenizer_audit

ADMIN_ROLE = "administrative_official_test_lengths"
DATASET = "hendzh/PromptShield"
DATASET_REVISION = "a5234cb1f5cdb256600cab64b8c961195b5e8404"
SOURCE_FILENAME = "test.json"
SOURCE_SHA256 = "526207c2485829d9961407011d7f4cd929569e7f285dc8396b3f385e0608bc70"
EXPECTED_ROWS = 23516
EXPECTED_CLASSES = {0: 17030, 1: 6486}


class HoldoutLengthError(ValueError):
    """Fixed messages; never include source contents or native exception messages."""


def require(condition, message):
    if not condition:
        raise HoldoutLengthError(message)


def validate_source(raw):
    source = input_data.parsed(raw, object_required=False)
    require(isinstance(source, list) and len(source) == EXPECTED_ROWS, "Official-test source row count mismatch")
    counts = Counter()
    for row in source:
        require(isinstance(row, dict) and set(row) == {"prompt", "label"}
                and isinstance(row["prompt"], str) and type(row["label"]) is int
                and row["label"] in (0, 1), "Official-test source schema invalid; contents suppressed")
        counts[row["label"]] += 1
    require(dict(counts) == EXPECTED_CLASSES, "Official-test source class support mismatch")
    return source, {str(label): counts[label] for label in (0, 1)}


def length_evidence(lengths):
    """Total row-weighted sufficient statistics, without row linkage or subgroups."""
    return {"original_token_lengths": tokenizer_audit.length_summary(lengths),
            "original_token_length_histogram": {str(length): count for length, count in sorted(Counter(lengths).items())}}


def audit(role, output, asset_dir, raw_dir, source_sha256,
          asset_manifest_sha256=tokenizer_audit.ASSET_MANIFEST_SHA256, batch_size=64):
    # The separate administrative role is checked before any file read or native load.
    require(role == ADMIN_ROLE and isinstance(role, str), "Only the fixed administrative official-test-length role is accepted")
    require(source_sha256 == SOURCE_SHA256, "Source expectation differs from the approved pinned official test")
    require(asset_manifest_sha256 == tokenizer_audit.ASSET_MANIFEST_SHA256,
            "Asset expectation differs from the verified pinned tokenizer receipt")
    require(type(batch_size) is int and 1 <= batch_size <= 128, "Administrative batch size must be between 1 and 128")
    output = Path(output)
    require(not output.exists(), "Output directory must be new; preserve earlier evidence")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "incomplete", "stage": "asset_validation", "data_role": ADMIN_ROLE,
                "expected_rows": EXPECTED_ROWS, "processed_rows": 0,
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "Aggregate-only original official-test token lengths; no model, caps, A/B groups, row IDs or token vectors",
                "completion_requires": "summary.json present with matching manifest hash"}
    tokenizer_audit.write_json(output / "manifest.json", manifest)
    try:
        docs, asset_hashes = tokenizer_audit.verify_assets(asset_dir)
        manifest["stage"] = "pinned_official_test_validation"
        source_path = input_data.fixed_path(raw_dir, SOURCE_FILENAME)
        original_bytes = input_data.checked_bytes(source_path, SOURCE_SHA256)
        source, class_counts = validate_source(original_bytes)
        manifest["stage"] = "native_wrapper_load"
        tokenizer_audit.write_json(output / "manifest.json", manifest)
        tokenizer, runtime = tokenizer_audit.load_native(asset_dir, docs["config.json"])
        manifest["stage"] = "untruncated_token_lengths"
        tokenizer_audit.write_json(output / "manifest.json", manifest)
        lengths = []
        for start in range(0, EXPECTED_ROWS, batch_size):
            texts = [row["prompt"] for row in source[start:start + batch_size]]
            unchanged = tuple(texts)
            ids, masks = tokenizer_audit.encode(tokenizer, texts, cap=None, padding=False, specials=True)
            require(tuple(texts) == unchanged, "Native call changed the supplied source strings")
            for tokens, mask in zip(ids, masks):
                require(bool(tokens) and all(value == 1 for value in mask),
                        "Zero-token or masked official-test input; no row may be dropped")
                lengths.append(len(tokens))
                manifest["processed_rows"] = len(lengths)
            tokenizer_audit.write_json(output / "manifest.json", manifest)
        require(len(lengths) == EXPECTED_ROWS, "Administrative coverage differs from the full intended source")
        require(input_data.checked_bytes(source_path, SOURCE_SHA256) == original_bytes,
                "Original source bytes changed during administration")
        require(tokenizer_audit.verify_assets(asset_dir)[1] == asset_hashes, "Tokenizer asset bytes changed during administration")
        manifest.update({"status": "complete", "stage": "complete",
                         "completed_at_utc": datetime.now(timezone.utc).isoformat()})
        tokenizer_audit.write_json(output / "manifest.json", manifest)
        summary = {"status": "complete", "data_role": ADMIN_ROLE, "dataset": DATASET,
                   "dataset_revision": DATASET_REVISION, "source_filename": SOURCE_FILENAME,
                   "source_sha256": SOURCE_SHA256, "source_bytes": len(original_bytes),
                   "expected_rows": EXPECTED_ROWS, "processed_rows": len(lengths), "source_class_counts": class_counts,
                   **length_evidence(lengths),
                   "quantiles": "p90/p95/p99 nearest rank ceil(p*n)-1; median conventional; mean arithmetic",
                   "tokenizer_model_revision": tokenizer_audit.REVISION,
                   "asset_manifest_sha256": tokenizer_audit.ASSET_MANIFEST_SHA256,
                   "source_metadata_sha256": tokenizer_audit.SOURCE_METADATA_SHA256, "asset_hashes": asset_hashes,
                   "runtime": runtime, "python": sys.version,
                   "hardware": {"platform": platform.platform(), "machine": platform.machine(),
                                "processor_reported": platform.processor(), "host": platform.node(),
                                "host_logical_cpus": os.cpu_count(),
                                "scheduler_allocation": {key: os.environ.get(key) for key in
                                    ("SLURM_JOB_ID", "SLURM_CPUS_PER_TASK", "SLURM_MEM_PER_NODE", "SLURM_JOB_NODELIST")}},
                   "batch_size": batch_size,
                   "call": {"add_special_tokens": True, "padding": False, "truncation": False,
                            "split_special_tokens": False, "return_tensors": None},
                   "source_bytes_and_strings_preserved": True,
                   "exports_row_ids_hashes_prompts_or_token_vectors": False,
                   "cap_or_truncation_comparison_performed": False, "a_b_subgroups_computed": False,
                   "model_loaded_or_inference_performed": False, "test_performance_released": False,
                   "may_inform_development_choices": False, "phase_closed": False,
                   "manifest_sha256": contract_audit.sha256((output / "manifest.json").read_bytes()),
                   "code_sha256": {f"precision_benchmark/{name}": contract_audit.sha256(Path(__file__).with_name(name).read_bytes()) for name in
                                   ("holdout_lengths.py", "tokenizer_audit.py", "input_data.py", "artifacts.py", "contract_audit.py")}}
        tokenizer_audit.write_json(output / "summary.json", summary)
        return summary
    except Exception as error:
        manifest.update({"status": "incomplete", "error_type": type(error).__name__, "error_details_suppressed": True})
        tokenizer_audit.write_json(output / "manifest.json", manifest)
        raise HoldoutLengthError("Administrative length audit incomplete; sanitized coverage manifest retained") from None


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, "Invalid administrative-length arguments; use --help.\n")
    parser = SafeParser(description=__doc__)
    for name in ("output", "assets", "raw-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("role", "source-sha256", "asset-manifest-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    try:
        result = audit(args.role, args.output, args.assets, args.raw_dir, args.source_sha256,
                       args.asset_manifest_sha256, args.batch_size)
    except Exception:
        print("Administrative length audit did not complete; no source/provider details printed.", file=sys.stderr)
        return 2
    print(f'{{"status":"complete","processed_rows":{result["processed_rows"]},"aggregate_only":true}}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
