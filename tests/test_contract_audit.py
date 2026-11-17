"""Synthetic, network-free checks. No existing Hub credentials are read."""
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from precision_benchmark import contract_audit as target

TOKEN = "hf_SYNTHETIC_ONLY_NO_SECRET"


class Raw:
    def __init__(self, body=b"", forbid=False):
        self.body, self.forbid, self.reads = body, forbid, []

    def read(self, count, decode_content):
        if self.forbid:
            raise AssertionError("Body must not be read")
        self.reads.append((count, decode_content))
        return self.body[:count]


class Response:
    def __init__(self, status=200, body=b"{}", headers=None, forbid=False):
        self.status_code = status
        self.headers = headers or {}
        self.raw = Raw(body, forbid)
        self.closed = False

    @property
    def content(self):
        raise AssertionError("Unbounded content access forbidden")

    def close(self):
        self.closed = True


class Adapter:
    def __init__(self, responses):
        self.responses = list(responses)
        self.sent = []

    def send(self, request, **kwargs):
        self.sent.append((request, kwargs))
        return self.responses.pop(0)

    def close(self):
        pass


def request(method, url, headers):
    value = SimpleNamespace(method=method, url=url, headers=dict(headers))
    value.prepare = lambda: value
    return value


def settings(url):
    return {"verify": "configured-ca.pem", "cert": None,
            "proxies": {"https": "http://configured-proxy.invalid:8888"}}


def transport(*responses):
    adapter = Adapter(responses)
    return target.BoundedTransport(TOKEN, adapter, request, settings), adapter


def header_fixture():
    value = {"score.weight": {"dtype": "F16", "shape": [2, 3], "data_offsets": [0, 12]},
             "score.bias": {"dtype": "F32", "shape": [2], "data_offsets": [12, 20]}}
    raw = json.dumps(value, separators=(",", ":")).encode()
    return struct.pack("<Q", len(raw)), raw, 8 + len(raw) + 20


def source_info(body=b"{}"):
    _, _, total = header_fixture()
    blob = hashlib.sha1(f"blob {len(body)}\0".encode() + body).hexdigest()
    siblings = [SimpleNamespace(rfilename=name, size=len(body), blob_id=blob, lfs=None)
                for name in target.FILES]
    siblings.append(SimpleNamespace(rfilename="model.safetensors", size=total,
                                   blob_id="b"*40, lfs=SimpleNamespace(size=total, sha256="c"*64)))
    return SimpleNamespace(id=target.MODEL_ID, sha=target.REVISION, siblings=siblings)


class TransportTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("requests"), "optional requests dependency is not installed")
    def test_real_requests_preparation_preserves_environment_without_netrc(self):
        import requests
        upper = "http://configured-proxy.invalid:8888"
        lower = "http://configured-lowercase-proxy.invalid:8889"
        cases = [("uppercase", {"HTTPS_PROXY": upper}, upper),
                 ("lowercase", {"https_proxy": lower}, lower),
                 ("both_case_precedence", {"HTTPS_PROXY": upper, "https_proxy": lower}, lower)]
        for case, proxy_settings, expected_proxy in cases:
            response = Response(headers={"Content-Length": "2"})
            environment = {"REQUESTS_CA_BUNDLE": "configured-ca.pem", "NO_PROXY": "", **proxy_settings}
            # Isolate this mock's expectations from a host/cluster's lowercase proxy,
            # no_proxy, ALL_PROXY or CA settings. Production environment handling stays intact.
            with self.subTest(case=case), patch.dict(os.environ, environment, clear=True), \
                    patch("requests.sessions.get_netrc_auth", side_effect=AssertionError("netrc forbidden")), \
                    patch.object(requests.adapters.HTTPAdapter, "send", return_value=response) as send:
                reader = target.BoundedTransport(TOKEN)
                try:
                    reader.read("config.json", 2)
                finally:
                    reader.close()
                prepared = send.call_args.args[0]
                self.assertNotIn("Cookie", prepared.headers)
                self.assertEqual(prepared.headers["Authorization"], "Bearer " + TOKEN)
                self.assertEqual(send.call_args.kwargs["verify"], "configured-ca.pem")
                self.assertEqual(send.call_args.kwargs["proxies"]["https"], expected_proxy)
                self.assertTrue(response.closed)

    def test_exact_read_preserves_proxy_ca_and_limits_body(self):
        response = Response(headers={"Content-Length": "2"})
        reader, adapter = transport(response)
        raw, receipt = reader.read("config.json", 2)
        self.assertEqual(raw, b"{}")
        self.assertEqual(response.raw.reads, [(3, False)])
        self.assertTrue(response.closed)
        self.assertTrue(adapter.sent[0][1]["stream"])
        self.assertEqual(adapter.sent[0][1]["verify"], "configured-ca.pem")
        self.assertEqual(adapter.sent[0][1]["proxies"], settings("")["proxies"])
        self.assertNotIn(TOKEN, json.dumps(receipt))

    def test_manual_redirect_reads_no_intermediate_body_or_cross_origin_auth(self):
        first = Response(302, headers={"Location": "https://cdn-lfs.hf.co/blob?signature=example"}, forbid=True)
        second = Response(307, headers={"Location": target.BASE + "config.json"}, forbid=True)
        third = Response()
        reader, adapter = transport(first, second, third)
        _, receipt = reader.read("config.json", 2)
        self.assertIn("Authorization", adapter.sent[0][0].headers)
        self.assertNotIn("Authorization", adapter.sent[1][0].headers)
        self.assertNotIn("Authorization", adapter.sent[2][0].headers)
        self.assertEqual(receipt["redirect_count"], 2)
        self.assertNotIn("signature", json.dumps(receipt))
        self.assertTrue(first.closed and second.closed and third.closed)

    def test_bad_redirect_destinations_stop_before_second_send(self):
        for url in ("http://huggingface.co/x", "https://other.invalid/x",
                    "https://user:password@huggingface.co/x", "https://huggingface.co:44/x",
                    f"https://[{TOKEN}]/", f"https://cdn-lfs.hf.co/?q={TOKEN}"):
            with self.subTest(url=url):
                response = Response(302, headers={"Location": url}, forbid=True)
                reader, adapter = transport(response)
                with self.assertRaises(target.AuditError) as ctx:
                    reader.read("config.json", 2)
                self.assertNotIn(TOKEN, str(ctx.exception))
                self.assertEqual(len(adapter.sent), 1)
                self.assertTrue(response.closed)

    def test_ignored_range_and_wrong_content_range_never_read_body(self):
        for response in (Response(200, forbid=True),
                         Response(206, headers={"Content-Range": "bytes 1-8/100"}, forbid=True),
                         Response(206, headers={"Content-Range": "bytes 0-7/101"}, forbid=True)):
            reader, _ = transport(response)
            with self.assertRaises(target.AuditError):
                reader.read("model.safetensors", 8, (0, 7), 100)
            self.assertTrue(response.closed)

    def test_exact_range_with_no_full_weight_path(self):
        response = Response(206, b"12345678", {"Content-Range": "bytes 0-7/100", "Content-Length": "8"})
        reader, adapter = transport(response)
        raw, receipt = reader.read("model.safetensors", 8, (0, 7), 100)
        self.assertEqual(raw, b"12345678")
        self.assertEqual(adapter.sent[0][0].headers["Range"], "bytes=0-7")
        self.assertEqual(receipt["content_range"], "bytes 0-7/100")
        with self.assertRaises(target.AuditError):
            reader.read("model.safetensors", 100)

    def test_reflection_overrun_encoding_and_revision_rejected(self):
        cases = [(TOKEN.encode(), len(TOKEN), {}),
                 (b"abc", 2, {}), (b"{}", 2, {"Content-Encoding": "gzip"}),
                 (b"{}", 2, {"X-Repo-Commit": "d"*40})]
        for body, size, headers in cases:
            reader, _ = transport(Response(body=body, headers=headers))
            with self.assertRaises(target.AuditError):
                reader.read("config.json", size)


class HeaderTests(unittest.TestCase):
    def test_valid_header_reports_shape_and_payload_scope(self):
        result = target.inspect_header(*header_fixture())
        self.assertEqual(result["score_weight"]["shape"], [2, 3])
        self.assertEqual(result["dtype_elements"], {"F16": 6, "F32": 2})
        self.assertEqual(result["parameter_elements"], 8)
        self.assertTrue(result["score_bias_present"])
        self.assertFalse(result["tensor_payload_downloaded"])

    def test_duplicate_json_and_invalid_tensor_structure_rejected(self):
        duplicate = b'{"score.weight":{},"score.weight":{}}'
        with self.assertRaises(target.AuditError):
            target.inspect_header(struct.pack("<Q", len(duplicate)), duplicate, len(duplicate)+8)
        _, raw, total = header_fixture()
        original = json.loads(raw)
        for field, value in (("shape", [True, 3]), ("shape", [-1, 3]),
                             ("dtype", "UNKNOWN"), ("data_offsets", [0, 13]),
                             ("data_offsets", [1, 13])):
            case = json.loads(raw)
            case["score.weight"][field] = value
            changed = json.dumps(case).encode()
            with self.subTest(field=field, value=value), self.assertRaises(target.AuditError):
                target.inspect_header(struct.pack("<Q", len(changed)), changed, len(changed)+28)

    def test_overlapping_gapped_and_unaccounted_payload_rejected(self):
        _, raw, _ = header_fixture()
        for offsets in ([10, 18], [14, 22]):
            case = json.loads(raw)
            case["score.bias"]["data_offsets"] = offsets
            changed = json.dumps(case).encode()
            with self.assertRaises(target.AuditError):
                target.inspect_header(struct.pack("<Q", len(changed)), changed, len(changed)+30)
        prefix, raw, total = header_fixture()
        with self.assertRaises(target.AuditError):
            target.inspect_header(prefix, raw, total + 1)


class ArtifactTests(unittest.TestCase):
    def test_source_identity_budget_and_hashes(self):
        info = source_info()
        sources = target.validate_info(info)
        target.verify_file(b"{}", sources["config.json"])
        with self.assertRaises(target.AuditError):
            target.verify_file(b"[]", sources["config.json"])
        info.sha = "d"*40
        with self.assertRaises(target.AuditError):
            target.validate_info(info)
        info = source_info()
        info.siblings[0].size = target.MAX_FILES_BYTES
        with self.assertRaises(target.AuditError):
            target.validate_info(info)

    def test_complete_audit_is_limited_and_no_credential_retained(self):
        calls = []
        class FakeTransport:
            def __init__(self, token):
                self.assert_token = token
            def read(self, name, expected, byte_range=None, total_size=None):
                calls.append((name, expected, byte_range))
                prefix, header, _ = header_fixture()
                raw = b"{}" if name in target.FILES else (prefix if byte_range == (0,7) else header)
                return raw, {"sha256": target.sha256(raw), "bytes": len(raw)}
            def close(self):
                pass
        fake_hub = SimpleNamespace(get_token=lambda: TOKEN,
                     HfApi=lambda **kw: SimpleNamespace(model_info=lambda *a, **k: source_info()))
        with tempfile.TemporaryDirectory() as temp, patch.dict(sys.modules, {"huggingface_hub": fake_hub}), \
                patch.object(target, "BoundedTransport", FakeTransport):
            out = Path(temp)/"new"
            result = target.audit(out)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(len(calls), len(target.FILES)+2)
            self.assertEqual(calls[-2][2], (0,7))
            self.assertFalse((out/"model.safetensors").exists())
            for file in out.iterdir():
                self.assertNotIn(TOKEN.encode(), file.read_bytes())
            with self.assertRaises(target.AuditError):
                target.audit(out)

    def test_provider_failure_output_and_manifest_are_sanitized(self):
        def failing(*a, **k):
            print(TOKEN)
            print("https://cdn-lfs.hf.co/file?secret="+TOKEN, file=sys.stderr)
            raise ValueError("provider reflected "+TOKEN)
        fake_hub = SimpleNamespace(get_token=lambda: TOKEN,
                     HfApi=lambda **kw: SimpleNamespace(model_info=failing))
        stdout, stderr = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as temp, patch.dict(sys.modules, {"huggingface_hub": fake_hub}), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            out = Path(temp)/"new"
            with self.assertRaises(target.AuditError) as ctx:
                target.audit(out)
            self.assertNotIn(TOKEN, str(ctx.exception))
            self.assertNotIn(TOKEN, (out/"manifest.json").read_text())
        self.assertNotIn(TOKEN, stdout.getvalue()+stderr.getvalue())

    def test_missing_credential_fails_before_output_creation(self):
        fake_hub = SimpleNamespace(get_token=lambda: None, HfApi=lambda **kw: self.fail("No network"))
        with tempfile.TemporaryDirectory() as temp, patch.dict(sys.modules, {"huggingface_hub": fake_hub}):
            out = Path(temp)/"new"
            with self.assertRaises(target.AuditError):
                target.audit(out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
