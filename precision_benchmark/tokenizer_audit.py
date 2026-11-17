"""Offline CPU tokenizer/config audit; execute only in an approved native runtime.

Both D-009 development roles are required. No model/weights or protected source is
loaded. Development exports contain IDs, hashes, lengths and index diagnostics,
never prompt text or token vectors. Native imports are lazy; tests use mocks.
"""

import argparse
from collections.abc import Mapping
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import unicodedata

from . import contract_audit, input_data

MODEL_ID = contract_audit.MODEL_ID
REVISION = contract_audit.REVISION
ASSET_MANIFEST_SHA256 = "fe4ef4fe0609b4465b1e7b8f2550c9c511fa9d1dc48c1fa34af7cb37cbdd1c23"
SOURCE_METADATA_SHA256 = "ebaedfbfb451d7daaabda87d25e51366126e8b980af458bb25b8248e3587da07"
ROLES = ("eligible_training", "eligible_validation")
CAPS = (512, 1024, 2048)
VERSIONS = {"transformers": "4.57.1", "tokenizers": "0.22.2"}
EOS = 151645
VOCAB_LIMIT = 151936


class TokenizerAuditError(ValueError):
    """Safe fixed messages; never include provider messages or development text."""


def require(condition, message):
    if not condition:
        raise TokenizerAuditError(message)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def verify_assets(directory):
    directory = Path(directory)
    manifest = input_data.parsed(input_data.checked_bytes(directory / "manifest.json", ASSET_MANIFEST_SHA256))
    sources = input_data.parsed(input_data.checked_bytes(directory / "source-metadata.json", SOURCE_METADATA_SHA256))
    for value in (manifest, sources):
        require(value.get("model_id") == MODEL_ID and value.get("revision") == REVISION,
                "Pinned model/tokenizer source identity mismatch")
    require(manifest.get("status") == "complete", "Retained asset retrieval is incomplete")
    entries = manifest.get("files", [])
    require(len(entries) == len(contract_audit.FILES)
            and {entry["filename"] for entry in entries} == set(contract_audit.FILES), "Asset file allowlist mismatch")
    require(sum(entry["bytes"] for entry in entries) <= contract_audit.MAX_FILES_BYTES, "Asset size budget exceeded")
    docs, hashes = {}, {}
    for entry in entries:
        name = entry["filename"]
        raw = input_data.checked_bytes(input_data.fixed_path(directory, name), entry["sha256"])
        require(entry["http_status"] == 200 and len(raw) == entry["bytes"], "Asset receipt size/status mismatch")
        source = sources["files"][name]
        require(source["filename"] == name, "Asset source filename mismatch")
        contract_audit.verify_file(raw, source)
        hashes[name] = contract_audit.sha256(raw)
        if name.endswith(".json"):
            docs[name] = input_data.parsed(raw)
    return docs, hashes


def library_sources():
    names = ("transformers.configuration_utils", "transformers.models.qwen3.configuration_qwen3",
             "transformers.models.qwen2.tokenization_qwen2_fast", "transformers.tokenization_utils_fast",
             "transformers.tokenization_utils_base")
    hashes = {}
    for name in names:
        filename = getattr(sys.modules.get(name), "__file__", None)
        require(isinstance(filename, str), "Loaded library source identity is unavailable")
        hashes[name] = contract_audit.sha256(Path(filename).read_bytes())
    return hashes


def load_native(directory, config):
    versions = {name: importlib.metadata.version(name) for name in VERSIONS}
    require(versions == VERSIONS, "Runtime library versions differ from the audited candidate")
    # This is the only native import path. Callers validate roles/assets/data first.
    with contract_audit.quiet_provider():
        from transformers import AutoConfig, AutoTokenizer
        resolved = AutoConfig.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False)
        tokenizer = AutoTokenizer.from_pretrained(str(directory), use_fast=True,
                                                  local_files_only=True, trust_remote_code=False)
    fields = ("num_labels", "id2label", "label2id", "pad_token_id", "eos_token_id",
              "vocab_size", "max_position_embeddings", "hidden_size", "model_type")
    observed = {name: getattr(resolved, name, None) for name in fields}
    require(observed["num_labels"] == 2 and observed["id2label"] == {0: "benign", 1: "jailbreak"}
            and observed["label2id"] is None and observed["pad_token_id"] is None,
            "Resolved classifier configuration differs from audited label/PAD defaults")
    require(all(observed[name] == config[name] for name in fields[4:]), "Resolved model dimensions/IDs differ from pinned config")
    require(type(tokenizer).__name__ == "Qwen2TokenizerFast" and tokenizer.is_fast is True,
            "Exact fast tokenizer wrapper was not loaded")
    require(tokenizer.pad_token_id == EOS and tokenizer.eos_token_id == EOS
            and tokenizer.bos_token_id is None and tokenizer.unk_token_id is None
            and tokenizer.padding_side == "left" and tokenizer.truncation_side == "right"
            and tokenizer.model_max_length == 131072, "Loaded wrapper token/default contract mismatch")
    return tokenizer, {"versions": versions, "tokenizer_class": type(tokenizer).__name__,
                       "tokenizer_module": type(tokenizer).__module__, "resolved_config": observed,
                       "library_source_sha256": library_sources(), "model_loaded": False}


def backend_state(tokenizer):
    return {"padding": tokenizer.backend_tokenizer.padding, "truncation": tokenizer.backend_tokenizer.truncation}


def encode(tokenizer, texts, cap=None, padding=False, specials=True):
    kwargs = {"add_special_tokens": specials, "padding": padding, "truncation": cap is not None,
              "return_attention_mask": True, "return_token_type_ids": False, "return_tensors": None,
              "split_special_tokens": False}
    if cap is not None:
        kwargs["max_length"] = cap
    if padding:
        kwargs["padding_side"] = "left"
    with contract_audit.quiet_provider():
        encoded = tokenizer(texts, **kwargs)
    require(isinstance(encoded, Mapping), "Tokenizer output must be a mapping")
    ids, masks = encoded["input_ids"], encoded["attention_mask"]
    require(isinstance(ids, list) and isinstance(masks, list) and len(ids) == len(masks) == len(texts),
            "Tokenizer output does not cover the intended batch")
    for tokens, mask in zip(ids, masks):
        require(isinstance(tokens, list) and isinstance(mask, list) and len(tokens) == len(mask)
                and all(type(value) is int and 0 <= value < VOCAB_LIMIT for value in tokens)
                and all(type(value) is int and value in (0, 1) for value in mask), "Invalid token/mask vectors")
        if not padding:
            require(all(value == 1 for value in mask), "Unpadded call returned masked positions")
        if cap is not None:
            require(sum(mask) <= cap, "Capped output exceeds explicit maximum")
    return ids, masks


def pool_diagnostic(tokens, mask):
    require(bool(tokens) and len(tokens) == len(mask) and any(mask), "Empty/all-masked inputs are invalid for future inference")
    stock = max(range(len(tokens)), key=lambda i: i * int(tokens[i] != EOS))
    visible = max(i for i, value in enumerate(mask) if value)
    return {"eos_tokens": sum(token == EOS for token, keep in zip(tokens, mask) if keep),
            "ends_in_eos": tokens[visible] == EOS, "pad_eos_source_pool_index": stock,
            "last_visible_index": visible, "source_pool_index_disagreement": stock != visible}


def synthetic_checks(tokenizer, docs):
    backend = docs["tokenizer.json"]
    expected = {entry["content"]: entry["id"] for entry in backend["added_tokens"]}
    require(tokenizer.get_added_vocab() == expected, "Loaded added-token identities differ from serialized assets")
    flags = ("content", "single_word", "lstrip", "rstrip", "normalized", "special")
    for entry in backend["added_tokens"]:
        observed = tokenizer.added_tokens_decoder[entry["id"]]
        require(all(getattr(observed, key) == entry[key] for key in flags), "Added-token flags differ from retained assets")
    state_initial = backend_state(tokenizer)
    known, _ = encode(tokenizer, list(expected), specials=False)
    require(known == [[expected[text]] for text in expected], "Literal added-token recognition mismatch")
    cases = ["Plain text.", "", "café", "cafe\u0301", "  spaces\t\n", "before<|im_end|>after",
             "before<|im_end|>", "<|im_end|>", "<|endoftext|>"]
    with_specials, masks = encode(tokenizer, cases)
    without_specials, _ = encode(tokenizer, cases, specials=False)
    require(with_specials == without_specials and with_specials[1] == []
            and tokenizer.num_special_tokens_to_add(pair=False) == 0, "Unexpected automatic boundary-token insertion")
    require(with_specials[2] == with_specials[3], "Loaded NFC normalizer did not preserve canonical equivalence")
    require(with_specials[7] == [EOS] and with_specials[8] == [151643]
            and with_specials[6][-1] == EOS and with_specials[5].count(EOS) == 1,
            "Literal EOS token behavior differs from retained contract")
    padded_texts = ["x", "A longer invented diagnostic string.", "before<|im_end|>", "<|im_end|>"]
    plain, _ = encode(tokenizer, padded_texts)
    padded, padded_masks = encode(tokenizer, padded_texts, padding=True)
    require(len({len(tokens) for tokens in padded}) == 1 and any(0 in mask for mask in padded_masks),
            "Unequal synthetic batch did not exercise padding")
    for original, tokens, mask in zip(plain, padded, padded_masks):
        require([value for value, keep in zip(tokens, mask) if keep] == original
                and mask == sorted(mask) and all(value == EOS for value, keep in zip(tokens, mask) if not keep),
                "Left-padding IDs/masks differ from unpadded content")
    padded_state = backend_state(tokenizer)
    require(padded_state["padding"]["pad_id"] == EOS and padded_state["padding"]["direction"].lower() == "left",
            "Wrapper padding did not override serialized PAD")
    cap_checks = {}
    for cap in CAPS:
        # Distinct first token distinguishes right-prefix from erroneous suffix truncation.
        texts = ["<|endoftext|>" + "<|im_end|>" * (n - 1) for n in (cap - 1, cap, cap + 1)]
        full, _ = encode(tokenizer, texts)
        short, _ = encode(tokenizer, texts, cap=cap)
        require(full == [[151643] + [EOS] * (n - 1) for n in (cap - 1, cap, cap + 1)]
                and short == [ids[:cap] for ids in full], "Synthetic cap boundary or right-prefix mismatch")
        cap_checks[str(cap)] = {"original_lengths": [len(ids) for ids in full], "effective_lengths": [len(ids) for ids in short]}
    long_text = "<|im_end|>" * 5001
    capped_5000, _ = encode(tokenizer, [long_text], cap=5000)
    full_long, _ = encode(tokenizer, [long_text])
    require(len(capped_5000[0]) == 5000 and len(full_long[0]) == 5001
            and backend_state(tokenizer) == {"padding": None, "truncation": None},
            "Explicit baseline did not disable serialized or previous-call limits")
    return {"status": "passed", "scope": "Invented diagnostic strings; exact vectors are synthetic only",
            "cases": [{"text": text, "input_ids": ids, "attention_mask": mask,
                       "source_pooling": pool_diagnostic(ids, mask) if ids else "empty observed; not eligible for model execution"}
                      for text, ids, mask in zip(cases, with_specials, masks)],
            "padded_cases": [{"text": text, "input_ids": ids, "attention_mask": mask,
                              "source_pooling": pool_diagnostic(ids, mask)} for text, ids, mask in zip(padded_texts, padded, padded_masks)],
            "initial_backend_state": state_initial, "padded_backend_state": padded_state,
            "final_backend_state": backend_state(tokenizer), "cap_checks": cap_checks,
            "serialized_5000_diagnostic": {"explicit_5000": 5000, "explicit_untruncated": 5001, "study_cap_selected": False},
            "loaded_added_token_count": len(expected), "added_flags_match": True}


def length_summary(values):
    if not values:
        return {"n": 0}
    values = sorted(values)
    return {"n": len(values), "min": values[0], "max": values[-1], "mean": statistics.mean(values),
            "median": statistics.median(values),
            **{f"p{q}": values[math.ceil(q * len(values) / 100) - 1] for q in (90, 95, 99)}}


def aggregate(rows):
    n = len(rows)
    caps = {}
    for cap in CAPS:
        values = [row["caps"][str(cap)] for row in rows]
        truncated = sum(value["truncated"] for value in values)
        caps[str(cap)] = {"effective_lengths": length_summary([value["effective_tokens"] for value in values]),
                          "truncated_rows": truncated, "denominator_rows": n, "truncated_fraction": truncated / n if n else None,
                          "terminal_eos_rows": sum(value["ends_in_eos"] for value in values),
                          "source_pool_index_disagreement_rows": sum(value["source_pool_index_disagreement"] for value in values)}
    return {"rows": n, "original_lengths": length_summary([row["original_tokens"] for row in rows]),
            "python_nfc_changed_rows": sum(row["python_nfc_changes_raw_string"] for row in rows),
            "over_model_declared_max_positions_rows": sum(row["original_tokens"] > 40960 for row in rows),
            "terminal_eos_rows": sum(row["original_source_pooling"]["ends_in_eos"] for row in rows),
            "source_pool_index_disagreement_rows": sum(row["original_source_pooling"]["source_pool_index_disagreement"] for row in rows),
            "caps": caps}


def audit(output, asset_dir, access_path, access_sha256, partition_dir, raw_dir, roles=ROLES, batch_size=64,
          asset_manifest_sha256=ASSET_MANIFEST_SHA256):
    # Reject any protected role before filesystem reads or lazy native imports.
    for role in roles:
        input_data.require_role(role)
    require(tuple(roles) == ROLES, "This audit requires both development roles in the declared order")
    require(type(batch_size) is int and 1 <= batch_size <= 128, "Audit batch size must be between 1 and 128")
    require(asset_manifest_sha256 == ASSET_MANIFEST_SHA256, "Expected asset manifest must match the approved pinned receipt")
    output = Path(output)
    require(not output.exists(), "Output directory must be new; preserve earlier evidence")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "incomplete", "stage": "asset_validation", "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "model_revision": REVISION, "roles": list(ROLES), "processed_rows": {role: 0 for role in ROLES},
                "scope": "CPU tokenizer/config only; no model, weights, protected source, or selected study cap",
                "completion_requires": "summary.json present and valid alongside this manifest"}
    write_json(output / "manifest.json", manifest)
    try:
        docs, asset_hashes = verify_assets(asset_dir)
        manifest["stage"] = "development_input_validation"
        loaded = {role: input_data.load_development(role, access_path, access_sha256, partition_dir, raw_dir) for role in ROLES}
        manifest["expected_rows"] = {role: value.evidence["expected_rows"] for role, value in loaded.items()}
        manifest["stage"] = "native_wrapper_and_config_load"
        write_json(output / "manifest.json", manifest)
        tokenizer, runtime = load_native(asset_dir, docs["config.json"])
        manifest["stage"] = "synthetic_checks"
        write_json(output / "manifest.json", manifest)
        synthetic = synthetic_checks(tokenizer, docs)
        write_json(output / "synthetic-checks.json", synthetic)
        results = {}
        for role, population in loaded.items():
            manifest["stage"] = role
            rows = []
            labels = {row["example_id"]: row["label"] for row in population.references}
            with (output / f"{role}-lengths.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
                for start in range(0, len(population.records), batch_size):
                    batch = population.records[start:start + batch_size]
                    texts = [record.prompt for record in batch]
                    baseline, masks = encode(tokenizer, texts)
                    capped = {cap: encode(tokenizer, texts, cap=cap) for cap in CAPS}
                    for index, record in enumerate(batch):
                        ids = baseline[index]
                        require(bool(ids), "A development input produced zero tokens; no row was dropped")
                        require(contract_audit.sha256(record.prompt.encode("utf-8")) == record.raw_text_sha256,
                                "Original development text changed before tokenization")
                        row = {"example_id": record.example_id, "data_role": role, "raw_text_sha256": record.raw_text_sha256,
                               "original_tokens": len(ids), "original_source_pooling": pool_diagnostic(ids, masks[index]),
                               "python_nfc_changes_raw_string": unicodedata.normalize("NFC", record.prompt) != record.prompt,
                               "caps": {}}
                        for cap in CAPS:
                            short, short_mask = capped[cap][0][index], capped[cap][1][index]
                            require(short == ids[:cap], "Capped development tokens differ from the untruncated right prefix")
                            row["caps"][str(cap)] = {"effective_tokens": len(short), "truncated": len(short) < len(ids),
                                                      **pool_diagnostic(short, short_mask)}
                        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
                        rows.append(row)
                        manifest["processed_rows"][role] = len(rows)
                    stream.flush()
                    manifest["processed_rows"][role] = len(rows)
                    write_json(output / "manifest.json", manifest)
            require([row["example_id"] for row in rows] == [record.example_id for record in population.records]
                    and len(rows) == population.evidence["expected_rows"], "Audit coverage/order differs from intended population")
            results[role] = {"total": aggregate(rows), "by_class": {str(label): aggregate([row for row in rows if labels[row["example_id"]] == label]) for label in (0, 1)},
                             "input_evidence": population.evidence}
        require(verify_assets(asset_dir)[1] == asset_hashes, "Tokenizer assets changed during the audit")
        files = ["synthetic-checks.json", *(f"{role}-lengths.jsonl" for role in ROLES)]
        manifest.update({"status": "complete", "stage": "complete", "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                         "output_hashes": {name: contract_audit.sha256((output / name).read_bytes()) for name in files}})
        write_json(output / "manifest.json", manifest)
        summary = {"status": "complete", "model_id": MODEL_ID, "model_revision": REVISION,
                   "runtime": runtime, "python": sys.version, "platform": platform.platform(),
                   "python_unicode_database": unicodedata.unidata_version, "batch_size": batch_size,
                   "asset_manifest_sha256": ASSET_MANIFEST_SHA256, "source_metadata_sha256": SOURCE_METADATA_SHA256,
                   "asset_hashes": asset_hashes, "serialized_padding": docs["tokenizer.json"]["padding"],
                   "serialized_truncation": docs["tokenizer.json"]["truncation"],
                   "baseline_call": {"add_special_tokens": True, "padding": False, "truncation": False, "split_special_tokens": False},
                   "candidate_caps": list(CAPS), "study_cap_selected": False, "chat_template_applied": False,
                   "quantiles": "p90/p95/p99 nearest rank ceil(p*n)-1; median conventional; mean arithmetic; empty class n=0",
                   "populations": results, "model_loaded_or_inference_performed": False, "phase_closed": False,
                   "pooling_scope": "Conditional integer expression from audited model source; no logits or batching-equivalence claim",
                   "normalization_scope": "Intrinsic tokenizer NFC; raw strings preserved. Per-row NFC-change count uses the recorded Python Unicode database.",
                   "development_tokens_or_prompts_exported": False,
                   "manifest_sha256": contract_audit.sha256((output / "manifest.json").read_bytes()),
                   "code_sha256": {f"precision_benchmark/{name}": contract_audit.sha256(Path(__file__).with_name(name).read_bytes())
                                   for name in ("tokenizer_audit.py", "input_data.py", "artifacts.py", "contract_audit.py")}}
        write_json(output / "summary.json", summary)  # Completion marker is written last.
        return summary
    except Exception as error:
        manifest.update({"status": "incomplete", "error_type": type(error).__name__, "error_details_suppressed": True})
        write_json(output / "manifest.json", manifest)
        raise TokenizerAuditError("Tokenizer audit incomplete; sanitized stage/coverage manifest retained") from None


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, "Invalid tokenizer-audit arguments; use --help.\n")
    parser = SafeParser(description=__doc__)
    for name in ("output", "assets", "access", "partitions", "raw-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--access-sha256", required=True)
    parser.add_argument("--asset-manifest-sha256", required=True)
    parser.add_argument("--roles", nargs="+", default=list(ROLES))
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    try:
        result = audit(args.output, args.assets, args.access, args.access_sha256, args.partitions, args.raw_dir,
                       tuple(args.roles), args.batch_size, args.asset_manifest_sha256)
    except Exception:
        print("Tokenizer audit did not complete; no provider/source details printed.", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "rows": {role: value["total"]["rows"] for role, value in result["populations"].items()},
                      "model_inference": False, "study_cap_selected": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
