"""Prepare the authorized P1-B pilot from verified text-free training evidence.

Fixed 128 rows: per reference class, 48 original lengths <=512, eight 513–1024,
and eight >1024. No raw prompt, protected population or model output is read.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

from . import input_data, tokenizer_audit

ROLE = "eligible_training"
DECISION = "D-012"
NAMESPACE = "precision-aware-inference:p1b-pilot:v1:20261117"
QUOTAS = {"le512": 48, "513to1024": 8, "gt1024": 8}
CAP = 1024
THRESHOLD_SOURCE = "provisional-p1b-fixed-0.5-not-validation-selected"
LENGTH_FIELDS = {"caps", "data_role", "example_id", "original_source_pooling", "original_tokens",
                 "python_nfc_changes_raw_string", "raw_text_sha256"}
PREPROCESSING_OPTIONS = {
    "tokenizer_class": "Qwen2TokenizerFast", "use_fast": True,
    "add_special_tokens": True, "split_special_tokens": False,
    "padding": False, "truncation": True, "max_length": CAP,
    "truncation_side": "right", "padding_side": "left",
    "chat_template": False, "manual_eos": False,
    "model_pad_token_id": None, "model_pooling": "original_unpadded_batch_one",
}


class PilotDataError(ValueError):
    """Fixed diagnostics never echo source contents."""


def require(condition, message):
    if not condition:
        raise PilotDataError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def length_bin(length):
    require(type(length) is int and length > 0, "Original token length must be a positive integer")
    return "le512" if length <= 512 else "513to1024" if length <= 1024 else "gt1024"


def read_sources(population_dir, population_summary_sha256, native_dir, native_summary_sha256):
    summary = input_data.parsed(input_data.checked_bytes(input_data.fixed_path(population_dir, "summary.json"), population_summary_sha256))
    native = input_data.parsed(input_data.checked_bytes(input_data.fixed_path(native_dir, "summary.json"), native_summary_sha256))
    require(summary.get("dataset") == input_data.DATASET and summary.get("revision") == input_data.REVISION
            and summary.get("construction_decision") == "D-008", "Population source differs from the approved dataset construction")
    require(native.get("status") == "complete" and native.get("model_id") == tokenizer_audit.MODEL_ID
            and native.get("model_revision") == tokenizer_audit.REVISION
            and native.get("asset_manifest_sha256") == tokenizer_audit.ASSET_MANIFEST_SHA256
            and native.get("source_metadata_sha256") == tokenizer_audit.SOURCE_METADATA_SHA256,
            "Native length audit source/identity is incompatible")
    require(isinstance(native.get("asset_hashes"), dict)
            and set(native["asset_hashes"]) == set(tokenizer_audit.contract_audit.FILES)
            and all(input_data.valid_sha(value) for value in native["asset_hashes"].values()),
            "Native tokenizer asset hash inventory is incomplete")
    require(native.get("baseline_call") == {"add_special_tokens": True, "padding": False, "truncation": False, "split_special_tokens": False}
            and native.get("chat_template_applied") is False, "Native original-length definition is incompatible")
    require(native["runtime"]["tokenizer_class"] == "Qwen2TokenizerFast"
            and native["runtime"]["versions"] == tokenizer_audit.VERSIONS, "Native tokenizer runtime is incompatible")
    population = summary["populations"][ROLE]
    require(population["file"] == "eligible-training.jsonl", "Unexpected training population filename")
    population_sha = summary["output_files"]["eligible-training.jsonl"]
    preflight = native["populations"][ROLE]["input_evidence"]
    require(preflight["data_role"] == ROLE and preflight["dataset"] == input_data.DATASET
            and preflight["revision"] == input_data.REVISION
            and preflight["construction_decision"] == "D-008" and preflight["continuation_decision"] == "D-009",
            "Native input evidence does not identify approved training")
    require(preflight["inputs"]["parent_population_summary"] == {"filename": "summary.json", "sha256": population_summary_sha256}
            and preflight["inputs"]["population"] == {"filename": "eligible-training.jsonl", "sha256": population_sha}
            and preflight["inputs"]["original_source"] == {"filename": "train.json", "sha256": summary["original_source_sha256"]["train.json"]},
            "Native length audit is not bound to the expected training source/population")
    rows = input_data.membership_rows(input_data.checked_bytes(input_data.fixed_path(population_dir, "eligible-training.jsonl"), population_sha), ROLE, population)
    n = len(rows)
    require(preflight["expected_rows"] == preflight["validated_rows"] == n
            and preflight["ordered_id_sha256"] == population["ordered_id_sha256"]
            and preflight["class_counts"] == population["class_counts"], "Native preflight coverage differs from training membership")
    require(len({row["raw_text_sha256"] for row in rows}) == n,
            "Pilot selection requires the audited unique training groups; duplicate-group design needs explicit review")
    manifest_sha = native["manifest_sha256"]
    manifest = input_data.parsed(input_data.checked_bytes(input_data.fixed_path(native_dir, "manifest.json"), manifest_sha))
    require(manifest.get("status") == "complete" and manifest.get("model_revision") == tokenizer_audit.REVISION
            and manifest["expected_rows"][ROLE] == manifest["processed_rows"][ROLE] == n,
            "Native run manifest does not establish complete training coverage")
    length_sha = manifest["output_hashes"]["eligible_training-lengths.jsonl"]
    raw = input_data.checked_bytes(input_data.fixed_path(native_dir, "eligible_training-lengths.jsonl"), length_sha)
    native_rows = [input_data.parsed(line.encode("utf-8")) for line in raw.decode("utf-8").splitlines()]
    require(len(native_rows) == n, "Native length rows do not cover the full expected training population")
    require([row.get("example_id") for row in native_rows] == [row["example_id"] for row in rows],
            "Native length IDs are missing, duplicated, unexpected or reordered")
    lengths = {}
    for expected, row in zip(rows, native_rows):
        require(set(row) == LENGTH_FIELDS and row["data_role"] == ROLE
                and row["raw_text_sha256"] == expected["raw_text_sha256"], "Native length identity/schema differs from original training")
        length_bin(row["original_tokens"])
        require(set(row["caps"]) == {"512", "1024", "2048"}, "Unexpected native cap evidence")
        for cap, observed in row["caps"].items():
            require(type(observed["effective_tokens"]) is int and observed["effective_tokens"] == min(row["original_tokens"], int(cap))
                    and type(observed["truncated"]) is bool and observed["truncated"] == (row["original_tokens"] > int(cap)),
                    "Native capped length/truncation is inconsistent")
        lengths[row["example_id"]] = row
    total = native["populations"][ROLE]["total"]
    require(total["rows"] == total["original_lengths"]["n"] == n
            and total["caps"]["1024"]["denominator_rows"] == n
            and total["caps"]["1024"]["truncated_rows"] == sum(row["original_tokens"] > CAP for row in native_rows),
            "Native aggregate coverage/truncation disagrees with retained rows")
    evidence = {"population_summary": {"path": (Path(population_dir) / "summary.json").as_posix(), "sha256": population_summary_sha256},
                "training_population": {"path": (Path(population_dir) / "eligible-training.jsonl").as_posix(), "sha256": population_sha},
                "native_summary": {"path": (Path(native_dir) / "summary.json").as_posix(), "sha256": native_summary_sha256},
                "native_manifest": {"path": (Path(native_dir) / "manifest.json").as_posix(), "sha256": manifest_sha},
                "native_training_lengths": {"path": (Path(native_dir) / "eligible_training-lengths.jsonl").as_posix(), "sha256": length_sha},
                "original_training_source_sha256": summary["original_source_sha256"]["train.json"],
                "full_training_rows_verified": n, "full_training_class_counts": population["class_counts"],
                "tokenizer_asset_manifest_sha256": native["asset_manifest_sha256"]}
    return rows, lengths, evidence, native["asset_hashes"]


def select(rows, lengths):
    buckets = {(label, bin_name): [] for label in (0, 1) for bin_name in QUOTAS}
    for row in rows:
        buckets[(row["label"], length_bin(lengths[row["example_id"]]["original_tokens"]))].append(row)
    selected = set()
    support = {}
    for (label, bin_name), candidates in buckets.items():
        quota = QUOTAS[bin_name]
        require(len(candidates) >= quota, "A required class/length stratum has insufficient support; do not backfill silently")
        ranked = sorted(candidates, key=lambda row: (digest(f'{NAMESPACE}:{label}:{bin_name}:{row["example_id"]}'.encode("utf-8")), row["example_id"]))
        selected.update(row["example_id"] for row in ranked[:quota])
        support[f"{label}:{bin_name}"] = {"available": len(candidates), "selected": quota}
    chosen = sorted((row for row in rows if row["example_id"] in selected), key=lambda row: row["source_row"])
    require(len(chosen) == 2 * sum(QUOTAS.values()) == 128 and len(selected) == len(chosen), "Pilot selection coverage is not exactly 128 unique rows")
    return chosen, support


def build(population_dir, population_summary_sha256, native_dir, native_summary_sha256, output):
    output = Path(output)
    require(not output.exists(), "Output directory must be new; preserve earlier pilot artifacts")
    try:
        rows, lengths, sources, assets = read_sources(population_dir, population_summary_sha256, native_dir, native_summary_sha256)
        selected, support = select(rows, lengths)
        examples = []
        for row in selected:
            observed = lengths[row["example_id"]]
            examples.append({key: row[key] for key in ("example_id", "label", "data_role", "source_split", "source_row", "raw_text_sha256")}
                            | {"original_tokens": observed["original_tokens"], "effective_tokens": observed["caps"]["1024"]["effective_tokens"],
                               "truncated": observed["caps"]["1024"]["truncated"]})
        ids = [row["example_id"] for row in examples]
        ordered_hash, membership_hash = input_data.id_hash(ids), input_data.id_hash(sorted(ids))
        preprocessing = {"options": PREPROCESSING_OPTIONS, "model_revision": tokenizer_audit.REVISION,
                         "tokenizer_revision": tokenizer_audit.REVISION, "score_semantics": "p_injection", "injection_index": 1}
        schedule = {"ordered_example_ids": ids, "batch_size": 1, "cap": CAP, "padding": False}
        raw = b"".join(canonical(row) + b"\n" for row in examples)
        manifest = {"schema_version": 1, "status": "prepared", "decision_id": DECISION,
                    "purpose": "development_precision_pilot", "data_role": ROLE,
                    "dataset": input_data.DATASET, "dataset_revision": input_data.REVISION,
                    "model_id": tokenizer_audit.MODEL_ID, "model_revision": tokenizer_audit.REVISION,
                    "tokenizer_revision": tokenizer_audit.REVISION, "tokenizer_asset_hashes": assets,
                    "population_id": "pilot-128:sha256:" + membership_hash,
                    "ordered_id_sha256": ordered_hash, "membership_sha256": membership_hash,
                    "selected_ids": ids, "examples": {"path": "examples.jsonl", "sha256": digest(raw)},
                    "input_schedule": schedule, "input_schedule_id": "sha256:" + digest(canonical(schedule)),
                    "preprocessing_options": PREPROCESSING_OPTIONS,
                    "preprocessing_contract": preprocessing, "preprocessing_id": "sha256:" + digest(canonical(preprocessing)),
                    "cap": CAP, "batch_size": 1, "score_semantics": "p_injection", "injection_index": 1,
                    "threshold": 0.5, "threshold_source": THRESHOLD_SOURCE,
                    "selection": {"namespace": NAMESPACE, "quotas_per_class": QUOTAS, "support": support,
                                  "algorithm": "Within each reference class/original-token-length stratum, sort SHA256(namespace:label:stratum:example_id) ascending, then example_id; take fixed quota; emit original source-row order.",
                                  "length_basis": "Actual native original tokens before padding/truncation", "selection_used_model_outputs": False},
                    "rows": len(examples), "class_counts": {str(label): sum(row["label"] == label for row in examples) for label in (0, 1)},
                    "source_evidence": sources, "model_inference_performed": False, "main_study_freeze": False,
                    "limitations": ["Class/length-stratified training feasibility pilot, not a representative population or confirmatory quality estimate.",
                                    "Threshold 0.5 is provisional and not selected from FP32 validation predictions.",
                                    "Input schedule fixes IDs/order/batch composition; actual token-vector schedule must be checked by inference.",
                                    "Full checkpoint loading, effective precision, GPU feasibility and complete outputs require separate execution checks."],
                    "code_sha256": {f"precision_benchmark/{name}": digest(Path(__file__).with_name(name).read_bytes()) for name in
                                    ("pilot_data.py", "input_data.py", "artifacts.py", "tokenizer_audit.py")}}
        output.mkdir(parents=True, exist_ok=False)
        (output / "examples.jsonl").write_bytes(raw)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        return manifest
    except PilotDataError:
        raise
    except (OSError, ValueError, UnicodeError, KeyError, TypeError, AttributeError):
        raise PilotDataError("Pilot preparation failed source/contract checks; source contents suppressed") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("populations", "native-audit", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--population-summary-sha256", required=True)
    parser.add_argument("--native-summary-sha256", required=True)
    args = parser.parse_args()
    try:
        result = build(args.populations, args.population_summary_sha256, args.native_audit, args.native_summary_sha256, args.output)
    except PilotDataError as error:
        print(f"Pilot preparation failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "rows": result["rows"], "class_counts": result["class_counts"],
                      "population_id": result["population_id"], "model_inference": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
