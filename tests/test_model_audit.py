import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request
import warnings

from precision_benchmark import model_audit
from precision_benchmark.model_audit import MODEL_ID, summarize, validate_metadata, validate_revision


class ModelAuditTests(unittest.TestCase):
    def test_only_immutable_matching_selected_model_metadata_is_accepted(self):
        revision = "a" * 40
        self.assertEqual(validate_metadata({"id": MODEL_ID, "sha": revision}, revision), revision)
        for value in ("main", "a" * 39, "A" * 40, None, 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_revision(value)
        with self.assertRaises(ValueError):
            validate_metadata({"id": "Qwen/Qwen3-0.6B", "sha": revision})
        with self.assertRaises(ValueError):
            validate_metadata({"id": MODEL_ID, "sha": revision}, "b" * 40)

    def test_gated_config_never_inherits_label_or_runtime_claims_from_api(self):
        revision = "a" * 40
        metadata = {"id": MODEL_ID, "sha": revision, "gated": "auto",
                    "config": {"architectures": ["Qwen3ForSequenceClassification"],
                               "id2label": {"0": "benign", "1": "jailbreak"}},
                    "safetensors": {"parameters": {"F16": 100}, "total": 100}}
        result = summarize(metadata, {}, revision, {"config.json": {"http_status": 401}})
        self.assertIsNone(result["pinned_config"])
        self.assertIsNone(result["label_mapping_size"])
        self.assertFalse(result["label_orientation_verified"])
        self.assertFalse(result["classifier_tensor_shape_verified"])
        self.assertFalse(result["runtime_dtypes_or_quantization_verified"])
        self.assertEqual(result["access"]["failed_files"], {"config.json": 401})

    def test_pinned_mapping_is_retained_without_assuming_injection_index(self):
        revision = "a" * 40
        metadata = {"id": MODEL_ID, "sha": revision}
        config = {"id2label": {"0": "jailbreak", "1": "benign"},
                  "label2id": {"jailbreak": 0, "benign": 1}, "num_labels": 2}
        result = summarize(metadata, {"config.json": config}, revision, {})
        self.assertEqual(result["pinned_config"], config)
        self.assertEqual(result["label_mapping_size"], 2)
        self.assertFalse(result["label_orientation_verified"])
        self.assertNotIn("injection_index", result)

    def test_local_auth_precedence_and_no_implicit_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configured = root / "configured-token"
            configured.write_text("hf_file", encoding="utf-8")
            with patch.dict(os.environ, {"HF_TOKEN": " hf_current\n",
                            "HUGGING_FACE_HUB_TOKEN": "hf_legacy",
                            "HF_TOKEN_PATH": str(configured)}, clear=True):
                self.assertIsNone(model_audit.load_token("none"))
                self.assertEqual(model_audit.load_token("local"), "hf_current")
                del os.environ["HF_TOKEN"]
                self.assertEqual(model_audit.load_token("local"), "hf_legacy")
                del os.environ["HUGGING_FACE_HUB_TOKEN"]
                self.assertEqual(model_audit.load_token("local"), "hf_file")
                os.environ["HF_TOKEN_PATH"] = str(root / "missing")
                with self.assertRaisesRegex(ValueError, "No local Hub credential"):
                    model_audit.load_token("local")
            (root / "huggingface").mkdir()
            (root / "huggingface" / "token").write_text("hf_xdg", encoding="utf-8")
            with patch.dict(os.environ, {"XDG_CACHE_HOME": str(root)}, clear=True):
                self.assertEqual(model_audit.load_token("local"), "hf_xdg")

    def test_missing_auth_fails_before_request_or_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit"
            with patch.dict(os.environ, {"HF_TOKEN_PATH": str(Path(directory) / "missing")}, clear=True), \
                    patch.object(model_audit, "fetch") as fetch:
                with self.assertRaisesRegex(ValueError, "No local Hub credential"):
                    model_audit.audit(output, "a" * 40, auth="local")
                fetch.assert_not_called()
                self.assertFalse(output.exists())

    def test_prompt_refuses_nonterminal_and_echo_fallback(self):
        with patch.object(model_audit.sys.stdin, "isatty", return_value=False), \
                patch.object(model_audit.getpass, "getpass") as prompt:
            with self.assertRaisesRegex(ValueError, "interactive terminal"):
                model_audit.load_token("prompt")
            prompt.assert_not_called()

        def fallback(*args):
            warnings.warn("echo fallback", model_audit.getpass.GetPassWarning)
            self.fail("echo fallback was not stopped")

        with patch.object(model_audit.sys.stdin, "isatty", return_value=True), \
                patch.object(model_audit.sys.stderr, "isatty", return_value=True), \
                patch.object(model_audit.getpass, "getpass", side_effect=fallback):
            with self.assertRaisesRegex(ValueError, "Hidden credential input unavailable"):
                model_audit.load_token("prompt")

    def test_redirects_keep_credentials_only_on_exact_https_origin(self):
        request = urllib.request.Request("https://huggingface.co/source")
        request.add_unredirected_header("Authorization", "Bearer hf_test")
        handler = model_audit.HubOnlyRedirectHandler()
        redirected = handler.redirect_request(request, None, 302, "Found", {},
                                              "https://huggingface.co/target")
        self.assertEqual(redirected.get_header("Authorization"), "Bearer hf_test")
        for url in ("http://huggingface.co/target", "https://example.com/target",
                    "https://huggingface.co.evil.example/target", "https://huggingface.co:444/target",
                    "https://huggingface.co:hf_test/target",
                    "https://person@huggingface.co/target"):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "HTTPS huggingface.co"):
                handler.redirect_request(request, None, 302, "Found", {}, url)

    def test_fetch_preserves_http_failure_without_persisting_credential(self):
        token = "hf_synthetic_secret"
        url = "https://huggingface.co/config.json"
        response = urllib.error.HTTPError(url, 401, "Unauthorized", {}, io.BytesIO(b"Access denied"))
        opener = Mock()
        opener.open.side_effect = response
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(model_audit.urllib.request, "build_opener", return_value=opener):
            destination = Path(directory) / "config.json"
            record = model_audit.fetch(url, destination, token)
            self.assertEqual(record["http_status"], 401)
            self.assertEqual(destination.read_bytes(), b"Access denied")
            self.assertEqual(record["sha256"], hashlib.sha256(b"Access denied").hexdigest())
            self.assertTrue(record["authenticated_request"])
            self.assertNotIn(token, json.dumps(record))
            sent = opener.open.call_args.args[0]
            self.assertEqual(sent.get_header("Authorization"), "Bearer " + token)

    def test_fetch_rejects_credential_reflection_transport_detail_and_oversize(self):
        token = "hf_synthetic_secret"
        url = "https://huggingface.co/config.json"
        cases = [(token.encode(), {}), (b"{}", {"ETag": token}),
                 (b"x" * (model_audit.MAX_METADATA_BYTES + 1), {})]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "config.json"
            for body, headers in cases:
                response = urllib.error.HTTPError(url, 401, "Unauthorized", headers, io.BytesIO(body))
                opener = Mock()
                opener.open.side_effect = response
                with self.subTest(headers=bool(headers), size=len(body)), \
                        patch.object(model_audit.urllib.request, "build_opener", return_value=opener):
                    with self.assertRaises(ValueError) as raised:
                        model_audit.fetch(url, destination, token)
                    self.assertNotIn(token, str(raised.exception))
                    self.assertFalse(destination.exists())
            opener = Mock()
            opener.open.side_effect = urllib.error.URLError("reflected " + token)
            with patch.object(model_audit.urllib.request, "build_opener", return_value=opener):
                with self.assertRaises(ValueError) as raised:
                    model_audit.fetch(url, destination, token)
                self.assertNotIn(token, str(raised.exception))
            with patch.object(model_audit.urllib.request, "build_opener") as build:
                with self.assertRaises(ValueError):
                    model_audit.fetch("http://huggingface.co/config.json", destination, token)
                build.assert_not_called()

    def test_authenticated_audit_retains_evidence_without_claiming_runtime_validation(self):
        revision = "a" * 40
        token = "hf_synthetic_secret"

        def fake_open(request, timeout):
            self.assertEqual(request.get_header("Authorization"), "Bearer " + token)
            if "/api/models/" in request.full_url:
                body = json.dumps({"id": MODEL_ID, "sha": revision}).encode()
            elif request.full_url.endswith("config.json"):
                body = b'{"id2label":{"0":"jailbreak","1":"benign"}}'
            elif request.full_url.endswith(".json"):
                body = b"{}"
            else:
                body = b"Synthetic source"
            return urllib.error.HTTPError(request.full_url, 200, "OK",
                                          {"X-Repo-Commit": revision}, io.BytesIO(body))

        opener = Mock()
        opener.open.side_effect = fake_open
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, {"HF_TOKEN": token}, clear=True), \
                patch.object(model_audit.urllib.request, "build_opener", return_value=opener):
            output = Path(directory) / "audit"
            result = model_audit.audit(output, revision, auth="local")
            self.assertTrue(result["authentication"]["credential_sent"])
            self.assertEqual(len(result["authentication"]["successful_authenticated_files"]), 7)
            self.assertFalse(result["label_orientation_verified"])
            self.assertFalse(result["classifier_tensor_shape_verified"])
            self.assertFalse(result["runtime_dtypes_or_quantization_verified"])
            self.assertFalse(result["pooling_or_padding_behavior_verified"])
            self.assertTrue(all(token.encode() not in p.read_bytes() for p in output.iterdir()))
            with self.assertRaises(FileExistsError):
                model_audit.audit(output, revision, auth="local")

    def test_inherited_redirect_parser_cannot_echo_reflected_token(self):
        token = "hf_synthetic_secret"
        handler = model_audit.HubOnlyRedirectHandler()

        def malformed_redirect(request, timeout):
            # urllib parses Location before our redirect_request hook is reached.
            return handler.http_error_302(request, io.BytesIO(b""), 302, "Found",
                                          {"location": "https://[" + token + "]/"})

        opener = Mock()
        opener.open.side_effect = malformed_redirect
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(model_audit.urllib.request, "build_opener", return_value=opener):
            destination = Path(directory) / "config.json"
            with self.assertRaises(ValueError) as raised:
                model_audit.fetch("https://huggingface.co/config.json", destination, token)
            self.assertNotIn(token, str(raised.exception))
            self.assertIn("sensitive request details were suppressed", str(raised.exception))
            self.assertFalse(destination.exists())

    def test_cli_never_echoes_accidental_token_argument(self):
        secret = "hf_synthetic_secret"
        stderr = io.StringIO()
        with patch.object(model_audit.sys, "argv", ["model_audit", "--output", "unused", "--auth", secret]), \
                patch.object(model_audit.sys, "stderr", stderr):
            with self.assertRaises(SystemExit):
                model_audit.main()
        self.assertNotIn(secret, stderr.getvalue())
        self.assertIn("Never supply a token", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
