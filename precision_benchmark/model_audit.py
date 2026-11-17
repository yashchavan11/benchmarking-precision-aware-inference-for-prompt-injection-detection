"""Audit pinned Sentinel metadata without weights or inference.

This deliberately records gated-file failures instead of substituting a base model's
configuration. Run with ``python -m precision_benchmark.model_audit --output NEW_DIR``.
Authentication is opt-in: --auth local uses an existing Hub credential; --auth prompt
reads one without echo in an interactive terminal. Credentials are never saved.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import getpass
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import warnings


MODEL_ID = "rogue-security/prompt-injection-jailbreak-sentinel-v2"
REVISION_RE = re.compile(r"[0-9a-f]{40}")
MAX_METADATA_BYTES = 2_000_000
FILES = ("config.json", "tokenizer_config.json", "special_tokens_map.json",
         "added_tokens.json", "README.md", "LICENSE.md")


def _validate_token(value):
    token = value.strip()
    if len(token) > 4096 or not re.fullmatch(r"hf_[A-Za-z0-9_-]+", token):
        raise ValueError("Hub credential has an invalid format; its value was not retained")
    return token


def load_token(auth):
    """Read only the explicitly requested credential source; never log or persist it."""
    if auth == "none":
        return None
    if auth == "prompt":
        if not sys.stdin.isatty() or not sys.stderr.isatty():
            raise ValueError("--auth prompt requires an interactive terminal with hidden input")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                value = getpass.getpass("Hugging Face read token (hidden; not saved): ")
        except (getpass.GetPassWarning, EOFError, OSError):
            raise ValueError("Hidden credential input unavailable; no credential was retained") from None
        return _validate_token(value)
    if auth != "local":
        raise ValueError("authentication mode must be none, local or prompt")
    for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return _validate_token(value)
    if os.environ.get("HF_TOKEN_PATH"):
        token_path = Path(os.environ["HF_TOKEN_PATH"])
    elif os.environ.get("HF_HOME"):
        token_path = Path(os.environ["HF_HOME"]) / "token"
    else:
        cache_root = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
        token_path = cache_root / "huggingface" / "token"
    # An explicit path/home is authoritative; do not silently substitute another account.
    paths = [token_path]
    if not any(os.environ.get(name) for name in ("HF_TOKEN_PATH", "HF_HOME", "XDG_CACHE_HOME")):
        paths.append(Path.home() / ".huggingface" / "token")
    for path in paths:
        try:
            if path.is_file():
                with path.open("r", encoding="utf-8") as stream:
                    value = stream.read(4097)
                if len(value) > 4096:
                    raise ValueError("Hub credential file exceeds the expected size")
                return _validate_token(value)
        except (OSError, UnicodeError):
            raise ValueError("Unable to read configured Hub credential; no value was retained") from None
    raise ValueError("No local Hub credential found; configure one securely or use --auth prompt in your terminal")


def _validate_hub_url(url):
    try:
        parsed = urllib.parse.urlsplit(url)
        valid = (parsed.scheme == "https" and parsed.hostname == "huggingface.co"
                 and parsed.port in (None, 443) and not parsed.username and not parsed.password)
    except ValueError:
        valid = False  # A malformed redirect may contain secrets; do not echo it.
    if not valid:
        raise ValueError("Metadata requests and redirects must stay on HTTPS huggingface.co")


class HubOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward a credential to another origin or an HTTP endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_hub_url(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and req.get_header("Authorization"):
            redirected.add_unredirected_header("Authorization", req.get_header("Authorization"))
        return redirected


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


def fetch(url, destination, token=None):
    """Retain bounded source responses, refusing credential reflection or unsafe redirects."""
    _validate_hub_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": "precision-benchmark-metadata-audit/1"})
    if token is not None:
        token = _validate_token(token)
        request.add_unredirected_header("Authorization", "Bearer " + token)
    opener = urllib.request.build_opener(HubOnlyRedirectHandler())
    try:
        response = opener.open(request, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    except (OSError, ValueError):
        # urllib may parse redirects before our handler; even ValueError can echo
        # a reflected credential. Never expose transport/parser exception details.
        raise ValueError("Metadata transport failed; sensitive request details were suppressed") from None
    with response:
        try:
            raw = response.read(MAX_METADATA_BYTES + 1)
        except OSError:
            raise ValueError("Metadata response read failed; sensitive transport details were suppressed") from None
        if len(raw) > MAX_METADATA_BYTES:
            raise ValueError("metadata response exceeds the audit's byte limit")
        retained_headers = {"repo_commit_header": response.headers.get("X-Repo-Commit"),
                            "etag": response.headers.get("ETag")}
        if token is not None and (token.encode("utf-8") in raw or any(
                token in value for value in retained_headers.values() if value is not None)):
            raise ValueError("Response reflected a credential; response bytes and headers were not retained")
        record = {"url": url, "http_status": response.code,
                  "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                  "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                  "path": destination.name,
                  "authenticated_request": token is not None,
                  **retained_headers}
    destination.write_bytes(raw)
    return record


def summarize(metadata, documents, revision, records, auth="none"):
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
        "audit_scope": "metadata and lightweight files only; no weights or inference",
        "authentication": {"mode": auth,
                           "credential_sent": any(r.get("authenticated_request", False) for r in records.values()),
                           "successful_authenticated_files": [name for name, r in records.items()
                               if r.get("authenticated_request", False) and r["http_status"] == 200],
                           "credential_persisted": False},
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


def audit(output, revision=None, auth="none"):
    if revision is not None:
        validate_revision(revision)
    token = load_token(auth)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = {}
    api = "https://huggingface.co/api/models/" + MODEL_ID
    if revision is None:
        records["resolver"] = fetch(api, output / "resolver.json", token)
        if records["resolver"]["http_status"] != 200:
            raise ValueError("public model revision lookup failed; see resolver.json")
        revision = validate_metadata(json.loads((output / "resolver.json").read_bytes()))
    else:
        validate_revision(revision)
    records["pinned_model_info"] = fetch(api + "/revision/" + revision, output / "model-info.json", token)
    if records["pinned_model_info"]["http_status"] != 200:
        raise ValueError("pinned model metadata retrieval failed; see model-info.json")
    metadata = json.loads((output / "model-info.json").read_bytes())
    validate_metadata(metadata, revision)
    documents = {}
    for name in FILES:
        record = fetch(f"https://huggingface.co/{MODEL_ID}/resolve/{revision}/{name}", output / name, token)
        records[name] = record
        if record["repo_commit_header"] not in (None, revision):
            raise ValueError(f"{name}: response commit differs from requested revision")
        if record["http_status"] == 200 and name.endswith(".json"):
            value = json.loads((output / name).read_bytes())
            if not isinstance(value, dict):
                raise ValueError(f"{name}: expected a JSON object")
            documents[name] = value
    result = summarize(metadata, documents, revision, records, auth)
    result["audit_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main():
    class SafeArgumentParser(argparse.ArgumentParser):
        def error(self, message):
            # Do not echo a credential accidentally supplied as an argument.
            self.print_usage(sys.stderr)
            self.exit(2, "Invalid arguments; use --help. Never supply a token on the command line.\n")

    parser = SafeArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New local directory for retained metadata evidence")
    parser.add_argument("--revision", help="Immutable previously resolved model revision; omit to resolve main once")
    parser.add_argument("--auth", choices=("none", "local", "prompt"), default="none",
                        help="none (default), existing local Hub credential, or hidden terminal prompt; never a token value")
    args = parser.parse_args()
    try:
        result = audit(args.output, args.revision, args.auth)
    except (OSError, ValueError) as error:
        print(f"Model metadata audit failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"revision": result["revision"], "gated": result["access"]["gated"],
                      "failed_files": result["access"]["failed_files"],
                      "summary": str(Path(args.output) / "summary.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
