"""Audit public Sentinel metadata without credentials, weights, or inference.

This deliberately records gated-file failures instead of substituting a base model's
configuration. Run with ``python -m precision_benchmark.model_audit --output NEW_DIR``.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


MODEL_ID = "rogue-security/prompt-injection-jailbreak-sentinel-v2"
REVISION_RE = re.compile(r"[0-9a-f]{40}")
MAX_METADATA_BYTES = 2_000_000
FILES = ("config.json", "tokenizer_config.json", "special_tokens_map.json",
         "added_tokens.json", "README.md", "LICENSE.md")


def validate_revision(value):
    if not isinstance(value, str) or REVISION_RE.fullmatch(value) is None:
        raise ValueError("model revision must be an immutable 40-character lowercase commit SHA")
    return value


def validate_metadata(value, revision=None):
    if not isinstance(value, dict) or value.get("id") != MODEL_ID:
        raise ValueError("Hub metadata does not identify the selected Sentinel v2 repository")
    observed = validate_revision(value.get("sha"))
    if revision is not None and observed != validate_revision(revision):
        raise ValueError("pinned Hub response revision differs from the requested revision")
    return observed


def fetch(url, destination):
    """Retain public response bytes, HTTP outcome, and a hash; never send credentials."""
    request = urllib.request.Request(url, headers={"User-Agent": "precision-benchmark-metadata-audit/1"})
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read(MAX_METADATA_BYTES + 1)
        if len(raw) > MAX_METADATA_BYTES:
            raise ValueError("metadata response exceeds the audit's byte limit")
        record = {"url": url, "http_status": response.code,
                  "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                  "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                  "path": destination.name,
                  "repo_commit_header": response.headers.get("X-Repo-Commit"),
                  "etag": response.headers.get("ETag")}
    destination.write_bytes(raw)
    return record


def summarize(metadata, documents, revision, records):
    """Keep API declarations separate from configuration bytes and runtime facts."""
    validate_metadata(metadata, revision)
    api_config = metadata.get("config", {})
    api_tokenizer = api_config.get("tokenizer_config", {})
    config = documents.get("config.json")
    tokenizer = documents.get("tokenizer_config.json")
    mapping = config.get("id2label") if isinstance(config, dict) else None
    config_fields = ("architectures", "model_type", "num_labels", "id2label", "label2id",
                     "torch_dtype", "dtype", "hidden_size", "vocab_size", "max_position_embeddings",
                     "pad_token_id", "bos_token_id", "eos_token_id", "transformers_version")
    tokenizer_fields = ("tokenizer_class", "model_max_length", "padding_side", "truncation_side",
                        "add_bos_token", "add_eos_token", "bos_token", "eos_token", "pad_token", "unk_token")
    return {
        "schema_version": 1, "model_id": MODEL_ID, "revision": revision,
        "audit_scope": "public metadata and lightweight files only; no authentication, weights, or inference",
        "access": {"private": metadata.get("private"), "gated": metadata.get("gated"),
                   "failed_files": {name: record["http_status"] for name, record in records.items()
                                    if record["http_status"] != 200}},
        "hub_declared": {
            "architectures": api_config.get("architectures"),
            "model_type": api_config.get("model_type"),
            "base_model": metadata.get("cardData", {}).get("base_model"),
            "license_metadata": metadata.get("cardData", {}).get("license"),
            "safetensors_summary": metadata.get("safetensors"),
            "tokenizer_special_tokens": {key: api_tokenizer.get(key)
                                         for key in ("bos_token", "eos_token", "pad_token", "unk_token")},
            "chat_template_present": bool(api_tokenizer.get("chat_template")),
        },
        "pinned_config": ({key: config[key] for key in config_fields if key in config}
                          if isinstance(config, dict) else None),
        "pinned_tokenizer_config": ({key: tokenizer[key] for key in tokenizer_fields if key in tokenizer}
                                    if isinstance(tokenizer, dict) else None),
        "pinned_special_tokens_map": documents.get("special_tokens_map.json"),
        "label_mapping_size": len(mapping) if isinstance(mapping, dict) else None,
        "label_orientation_verified": False,
        "classifier_tensor_shape_verified": False,
        "runtime_dtypes_or_quantization_verified": False,
        "pooling_or_padding_behavior_verified": False,
        "source_records": records,
        "limitations": [
            "Hub safetensors counts/dtypes are provider metadata, not independently read weight tensors.",
            "A repository or tokenizer chat template does not establish that classification should apply it.",
            "The injection output index must be verified from accessible checkpoint evidence; index 1 is not assumed.",
            "Actual head shape, score conversion, last-token pooling, padding and all three treatments still need runtime checks.",
            "Source license metadata and retained license text are evidence, not a redistribution approval.",
            "This audit revision is an observed source identity, not a final experimental freeze.",
        ],
    }


def audit(output, revision=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = {}
    api = "https://huggingface.co/api/models/" + MODEL_ID
    if revision is None:
        records["resolver"] = fetch(api, output / "resolver.json")
        if records["resolver"]["http_status"] != 200:
            raise ValueError("public model revision lookup failed; see resolver.json")
        revision = validate_metadata(json.loads((output / "resolver.json").read_bytes()))
    else:
        validate_revision(revision)
    records["pinned_model_info"] = fetch(api + "/revision/" + revision, output / "model-info.json")
    if records["pinned_model_info"]["http_status"] != 200:
        raise ValueError("pinned model metadata retrieval failed; see model-info.json")
    metadata = json.loads((output / "model-info.json").read_bytes())
    validate_metadata(metadata, revision)
    documents = {}
    for name in FILES:
        record = fetch(f"https://huggingface.co/{MODEL_ID}/resolve/{revision}/{name}", output / name)
        records[name] = record
        if record["repo_commit_header"] not in (None, revision):
            raise ValueError(f"{name}: response commit differs from requested revision")
        if record["http_status"] == 200 and name.endswith(".json"):
            value = json.loads((output / name).read_bytes())
            if not isinstance(value, dict):
                raise ValueError(f"{name}: expected a JSON object")
            documents[name] = value
    result = summarize(metadata, documents, revision, records)
    result["audit_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New local directory for retained metadata evidence")
    parser.add_argument("--revision", help="Immutable previously resolved model revision; omit to resolve main once")
    args = parser.parse_args()
    try:
        result = audit(args.output, args.revision)
    except (OSError, ValueError) as error:
        print(f"Model metadata audit failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"revision": result["revision"], "gated": result["access"]["gated"],
                      "failed_files": result["access"]["failed_files"],
                      "summary": str(Path(args.output) / "summary.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
