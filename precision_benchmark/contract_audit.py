"""Fetch only pinned tokenizer assets and the checkpoint header, never tensor payloads.

Run with the project's audit Python and --output NEW_DIRECTORY after private Hub login.
No token argument or prompt is supported. No Transformers/native backend is imported.
"""
import argparse
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import logging
import math
from pathlib import Path
import re
import struct
import sys
from urllib.parse import unquote, urljoin, urlsplit

MODEL_ID = "rogue-security/prompt-injection-jailbreak-sentinel-v2"
REVISION = "05ff9bfd1f28c5228e53121d5ee4427bb5205212"
BASE = f"https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/"
FILES = ("config.json", "tokenizer_config.json", "special_tokens_map.json",
         "added_tokens.json", "tokenizer.json", "vocab.json", "merges.txt")
MAX_FILES_BYTES = 32 * 1024 * 1024
MAX_HEADER_BYTES = 2 * 1024 * 1024
SHA1 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
RANGE = re.compile(r"bytes ([0-9]+)-([0-9]+)/([0-9]+)")
DTYPE_BYTES = {"BOOL": 1, "I8": 1, "U8": 1, "I16": 2, "U16": 2,
               "F16": 2, "BF16": 2, "I32": 4, "U32": 4, "F32": 4,
               "I64": 8, "U64": 8, "F64": 8, "F8_E4M3": 1, "F8_E5M2": 1}


class AuditError(ValueError):
    """Messages are fixed strings, never provider content or credentials."""


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def no_reflection(value, token):
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    if token.encode("ascii") in raw:
        raise AuditError("Credential reflection rejected before retention")


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AuditError("Duplicate JSON key")
            result[key] = value
        return result
    def invalid_constant(_):
        raise AuditError("Nonfinite JSON value")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)


def origin(url):
    try:
        p = urlsplit(url)
        port = p.port
        host = p.hostname
    except ValueError:
        raise AuditError("Invalid redirect URL") from None
    if (p.scheme != "https" or port not in (None, 443) or p.username or p.password
            or not host or not (host == "huggingface.co" or host.endswith(".huggingface.co")
                                or host.endswith(".hf.co"))):
        raise AuditError("Unapproved or insecure download origin")
    return p.scheme, host, port or 443


class BoundedTransport:
    """Manual redirects; no netrc/cookies; configured proxy/CA controls preserved."""
    def __init__(self, token, adapter=None, request_factory=None, settings_factory=None):
        self.environment_session = None
        if adapter is None or request_factory is None or settings_factory is None:
            import requests
            adapter = adapter or requests.adapters.HTTPAdapter(max_retries=0)
            request_factory = request_factory or requests.Request
            if settings_factory is None:
                # Use Session only for proxy/CA settings, never for request preparation or sending.
                # Request.prepare below cannot load .netrc or merge a session cookie jar.
                self.environment_session = requests.Session()
                settings_factory = lambda url: self.environment_session.merge_environment_settings(
                    url, {}, True, True, None)
        self.adapter = adapter
        self.request_factory = request_factory
        self.settings_factory = settings_factory
        self.token = token

    def close(self):
        self.adapter.close()
        if self.environment_session is not None:
            self.environment_session.close()

    def read(self, filename, expected, byte_range=None, total_size=None):
        if filename not in FILES + ("model.safetensors",):
            raise AuditError("File outside fixed audit scope")
        if not integer(expected, 1) or expected > MAX_FILES_BYTES:
            raise AuditError("Invalid bounded request size")
        if filename == "model.safetensors" and byte_range is None:
            raise AuditError("Tensor payload download forbidden")
        url = BASE + filename
        headers = {"Authorization": "Bearer " + self.token, "Accept-Encoding": "identity",
                   "User-Agent": "precision-benchmark-contract-audit/1"}
        if byte_range is not None:
            start, end = byte_range
            if not integer(start) or not integer(end) or end - start + 1 != expected:
                raise AuditError("Invalid exact range")
            headers["Range"] = f"bytes={start}-{end}"
        for redirect_number in range(6):
            old_origin = origin(url)
            request = self.request_factory("GET", url, headers=headers).prepare()
            settings = self.settings_factory(url)
            if settings["verify"] is False or settings["verify"] is None:
                raise AuditError("TLS verification must remain enabled")
            response = self.adapter.send(request, stream=True, timeout=(10, 30),
                                         verify=settings["verify"], cert=settings["cert"],
                                         proxies=settings["proxies"])
            try:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not isinstance(location, str):
                        raise AuditError("Redirect missing location")
                    no_reflection(unquote(location), self.token)
                    next_url = urljoin(url, location)
                    if origin(next_url) != old_origin:
                        headers.pop("Authorization", None)
                    url = next_url
                    continue
                if response.status_code != (206 if byte_range is not None else 200):
                    raise AuditError("Unexpected HTTP status; no response body retained")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise AuditError("Encoded response rejected for exact byte audit")
                length = response.headers.get("Content-Length")
                if length is not None and (not length.isascii() or not length.isdecimal()
                                           or int(length) != expected):
                    raise AuditError("Unexpected response length")
                if byte_range is not None:
                    content_range = response.headers.get("Content-Range", "")
                    match = RANGE.fullmatch(content_range)
                    if (not match or tuple(map(int, match.groups()[:2])) != byte_range
                            or int(match.group(3)) != total_size):
                        raise AuditError("Content-Range does not match exact request/source size")
                commit = response.headers.get("X-Repo-Commit")
                if commit is not None and commit != REVISION:
                    raise AuditError("Response repository revision mismatch")
                raw = response.raw.read(expected + 1, decode_content=False)
                if len(raw) != expected:
                    raise AuditError("Response exceeds or does not fill declared byte range")
                no_reflection(raw, self.token)
                safe = {"source_url": BASE + filename, "http_status": response.status_code,
                        "bytes": len(raw), "sha256": sha256(raw),
                        "redirect_count": redirect_number, "repo_commit_header": commit}
                if byte_range is not None:
                    safe["content_range"] = f"bytes {byte_range[0]}-{byte_range[1]}/{total_size}"
                # Do not retain response.url, Location, cookies, request headers, or arbitrary ETags.
                return raw, safe
            finally:
                response.close()
        raise AuditError("Redirect limit exceeded")


def validate_info(info):
    if info.id != MODEL_ID or info.sha != REVISION:
        raise AuditError("Hub source identity mismatch")
    siblings = {}
    for item in info.siblings or []:
        if item.rfilename in FILES + ("model.safetensors",):
            if item.rfilename in siblings:
                raise AuditError("Duplicate source file identity")
            if not integer(item.size, 1) or not isinstance(item.blob_id, str) or not SHA1.fullmatch(item.blob_id):
                raise AuditError("Missing or invalid source size/blob identity")
            record = {"filename": item.rfilename, "size": item.size, "git_blob_sha1": item.blob_id}
            if item.lfs is not None:
                if (not isinstance(item.lfs.sha256, str) or not SHA256.fullmatch(item.lfs.sha256)
                        or item.lfs.size != item.size):
                    raise AuditError("Invalid LFS identity")
                record["lfs_sha256"] = item.lfs.sha256
            siblings[item.rfilename] = record
    if set(siblings) != set(FILES + ("model.safetensors",)):
        raise AuditError("Selected source files missing")
    if sum(siblings[name]["size"] for name in FILES) > MAX_FILES_BYTES:
        raise AuditError("Selected metadata/tokenizer assets exceed total size budget")
    return siblings


def verify_file(raw, record):
    if len(raw) != record["size"]:
        raise AuditError("File size mismatch")
    if "lfs_sha256" in record:
        if sha256(raw) != record["lfs_sha256"]:
            raise AuditError("LFS content hash mismatch")
    else:
        prefix = f"blob {len(raw)}\0".encode("ascii")
        if hashlib.sha1(prefix + raw).hexdigest() != record["git_blob_sha1"]:
            raise AuditError("Git blob content hash mismatch")
    if record["filename"].endswith(".json"):
        if not isinstance(strict_json(raw), dict):
            raise AuditError("Selected JSON asset must be an object")


def inspect_header(prefix, raw, total_size):
    if len(prefix) != 8:
        raise AuditError("Invalid safetensors prefix")
    header_size = struct.unpack("<Q", prefix)[0]
    if not 1 <= header_size <= MAX_HEADER_BYTES or len(raw) != header_size or not raw.startswith(b"{"):
        raise AuditError("Invalid safetensors header length or encoding")
    header = strict_json(raw)
    if not isinstance(header, dict):
        raise AuditError("Safetensors header must be an object")
    metadata = header.get("__metadata__", {})
    if not isinstance(metadata, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in metadata.items()):
        raise AuditError("Invalid safetensors metadata")
    payload_size = total_size - 8 - header_size
    spans = []
    count = 0
    dtypes = {}
    for name, tensor in header.items():
        if name == "__metadata__":
            continue
        if not isinstance(tensor, dict) or set(tensor) != {"dtype", "shape", "data_offsets"}:
            raise AuditError("Invalid tensor entry")
        dtype, shape, offsets = tensor["dtype"], tensor["shape"], tensor["data_offsets"]
        if (not isinstance(dtype, str) or dtype not in DTYPE_BYTES or not isinstance(shape, list)
                or any(not integer(dim) for dim in shape) or not isinstance(offsets, list)
                or len(offsets) != 2 or any(not integer(v) for v in offsets)):
            raise AuditError("Invalid tensor shape/dtype/offsets")
        start, end = offsets
        elements = math.prod(shape)
        if start > end or end > payload_size or end - start != elements * DTYPE_BYTES[dtype]:
            raise AuditError("Tensor byte extent inconsistent with shape/dtype")
        spans.append((start, end))
        count += elements
        dtypes[dtype] = dtypes.get(dtype, 0) + elements
    cursor = 0
    for start, end in sorted(spans):
        if start != cursor:
            raise AuditError("Tensor payload offsets overlap or have gaps")
        cursor = end
    if cursor != payload_size:
        raise AuditError("Header does not account for exact tensor payload extent")
    head = header.get("score.weight")
    if not isinstance(head, dict):
        raise AuditError("Expected classifier head tensor absent")
    return {"header_bytes": header_size, "header_sha256": sha256(raw),
            "source_file_bytes": total_size, "tensor_count": len(spans),
            "parameter_elements": count, "dtype_elements": dtypes,
            "score_weight": head, "score_bias_present": "score.bias" in header,
            "tensor_payload_downloaded": False, "full_weight_sha256_independently_verified": False,
            "runtime_loading_or_inference_verified": False}


@contextmanager
def quiet_provider():
    old_level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            yield
    finally:
        logging.disable(old_level)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def audit(output):
    output = Path(output)
    if output.exists():
        raise AuditError("Output directory must be new")
    from huggingface_hub import HfApi, get_token
    token = get_token()
    if not isinstance(token, str) or not re.fullmatch(r"hf_[A-Za-z0-9_-]+", token):
        raise AuditError("Existing local read credential required")
    output.mkdir(parents=True, exist_ok=False)
    stage = "source_metadata"
    manifest = {"model_id": MODEL_ID, "revision": REVISION, "status": "incomplete",
                "started_at_utc": datetime.now(timezone.utc).isoformat(), "files": [],
                "scope": "Tokenizer/config bytes and safetensors header only; no tensor payload or inference",
                "helper_sha256": sha256(Path(__file__).read_bytes())}
    transport = None
    try:
        with quiet_provider():
            info = HfApi(endpoint="https://huggingface.co").model_info(
                MODEL_ID, revision=REVISION, files_metadata=True, token=True)
        sources = validate_info(info)
        write_json(output / "source-metadata.json", {"model_id": MODEL_ID, "revision": REVISION,
                   "source_url": f"https://huggingface.co/api/models/{MODEL_ID}/revision/{REVISION}",
                   "files": sources})
        transport = BoundedTransport(token)
        for name in FILES:
            stage = name
            with quiet_provider():
                raw, receipt = transport.read(name, sources[name]["size"])
            verify_file(raw, sources[name])
            if name.endswith(".json"):
                no_reflection(json.dumps(strict_json(raw), ensure_ascii=False), token)
            (output / name).write_bytes(raw)
            receipt.update({"filename": name, "source_content_hash_verified": True})
            manifest["files"].append(receipt)
            write_json(output / "manifest.json", manifest)
        stage = "safetensors_header"
        total_size = sources["model.safetensors"]["size"]
        with quiet_provider():
            prefix, prefix_receipt = transport.read("model.safetensors", 8, (0, 7), total_size)
            header_size = struct.unpack("<Q", prefix)[0]
            if not 1 <= header_size <= MAX_HEADER_BYTES or header_size + 8 >= total_size:
                raise AuditError("Safetensors header exceeds bounded budget/source size")
            raw, header_receipt = transport.read("model.safetensors", header_size,
                                                  (8, header_size + 7), total_size)
        summary = inspect_header(prefix, raw, total_size)
        no_reflection(json.dumps(strict_json(raw), ensure_ascii=False), token)
        (output / "safetensors-prefix.bin").write_bytes(prefix)
        (output / "safetensors-header.json").write_bytes(raw)
        write_json(output / "safetensors-summary.json", summary)
        manifest.update({"status": "complete", "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                         "header_requests": [prefix_receipt, header_receipt], "head_summary": summary})
        write_json(output / "manifest.json", manifest)
        return manifest
    except Exception as error:
        # Provider errors can contain tokens or signed URLs. Retain no exception message/traceback.
        manifest.update({"failed_stage": stage, "error_type": type(error).__name__,
                         "error_details_suppressed": True})
        write_json(output / "manifest.json", manifest)
        raise AuditError("Contract retrieval incomplete; sanitized manifest retained") from None
    finally:
        if transport is not None:
            transport.close()


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, "Invalid arguments; only --output NEW_DIRECTORY is accepted.\n")
    parser = SafeParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = audit(args.output)
    except Exception:
        print("Contract audit did not complete; no credential/provider error details printed.", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "files_verified": len(result["files"]),
                      "header_verified": True, "inference_performed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
