"""Mock-only native boundary checks; no BPE implementation or real tokenizer import."""

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unicodedata
import unittest
from unittest.mock import Mock, patch

from precision_benchmark import input_data
from precision_benchmark import tokenizer_audit as target


SPECIALS = {"<|endoftext|>": 151643, "<|im_start|>": 151644, "<|im_end|>": 151645}


def added_entries():
    return [{"id": value, "content": text, "single_word": False, "lstrip": False,
             "rstrip": False, "normalized": False, "special": True} for text, value in SPECIALS.items()]


class Qwen2TokenizerFast:
    """An explicitly invented character encoder, not a Qwen/BPE reference."""
    is_fast = True
    pad_token_id = eos_token_id = 151645
    bos_token_id = unk_token_id = None
    padding_side, truncation_side = "left", "right"
    model_max_length = 131072

    def __init__(self, fault=None):
        self.fault = fault
        self.calls = []
        self.backend_tokenizer = SimpleNamespace(padding={"pad_id": 151643, "direction": "Left"},
                                                truncation={"max_length": 5000, "direction": "Right"})
        self.added_tokens_decoder = {item["id"]: SimpleNamespace(**{k: v for k, v in item.items() if k != "id"}) for item in added_entries()}

    def get_added_vocab(self):
        return dict(SPECIALS)

    def num_special_tokens_to_add(self, pair=False):
        return 0

    def characters(self, text):
        text = unicodedata.normalize("NFC", text)
        ids = []
        while text:
            match = next((token for token in SPECIALS if text.startswith(token)), None)
            if match:
                ids.append(SPECIALS[match])
                text = text[len(match):]
            else:
                ids.append(ord(text[0]) + 1)
                text = text[1:]
        return ids

    def __call__(self, texts, **kwargs):
        self.calls.append((list(texts), copy.deepcopy(kwargs)))
        if self.fault == "provider_reflection" and any("PRIVATE_DEVELOPMENT" in text for text in texts):
            print("PRIVATE_DEVELOPMENT reflected", file=sys.stderr)
            raise ValueError("PRIVATE_DEVELOPMENT reflected in provider exception")
        ids = [self.characters(text) for text in texts]
        if self.fault == "auto_eos" and kwargs["add_special_tokens"]:
            ids = [values + [151645] for values in ids]
        cap = kwargs.get("max_length") if kwargs["truncation"] else None
        if cap is None and self.fault == "serialized_cap_leak":
            cap = 5000
        if cap is not None:
            ids = [values[-cap:] if self.fault == "suffix" else values[:cap] for values in ids]
        self.backend_tokenizer.truncation = {"max_length": cap, "direction": "Right"} if cap else None
        masks = [[1] * len(values) for values in ids]
        if kwargs["padding"]:
            width = max(map(len, ids), default=0)
            pad_id = 151643 if self.fault == "wrong_pad" else 151645
            masks = [[0] * (width - len(values)) + [1] * len(values) for values in ids]
            ids = [[pad_id] * (width - len(values)) + values for values in ids]
            self.backend_tokenizer.padding = {"pad_id": pad_id, "direction": "left"}
        else:
            self.backend_tokenizer.padding = None
        if self.fault == "literal_eos_masked":
            masks = [[0 if token == 151645 else flag for token, flag in zip(values, mask)] for values, mask in zip(ids, masks)]
        return {"input_ids": ids, "attention_mask": masks}


class TokenizerAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.config = {"num_labels": 2, "id2label": {0: "benign", 1: "jailbreak"}, "label2id": None,
                       "pad_token_id": None, "eos_token_id": 151645, "vocab_size": 151936,
                       "max_position_embeddings": 40960, "hidden_size": 1024, "model_type": "qwen3"}
        docs = {"config.json": self.config, "tokenizer_config.json": {"pad_token": "<|im_end|>"},
                "special_tokens_map.json": {}, "added_tokens.json": SPECIALS, "vocab.json": {},
                "tokenizer.json": {"added_tokens": added_entries(), "normalizer": {"type": "NFC"},
                                   "padding": {"pad_id": 151643, "direction": "Left"},
                                   "truncation": {"max_length": 5000, "direction": "Right"}}}
        entries, sources = [], {}
        for name in target.contract_audit.FILES:
            raw = json.dumps(docs[name]).encode() if name.endswith(".json") else b"synthetic merges\n"
            (self.assets / name).write_bytes(raw)
            entries.append({"filename": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "http_status": 200})
            sources[name] = {"filename": name, "size": len(raw), "git_blob_sha1": hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()}
        manifest = {"model_id": target.MODEL_ID, "revision": target.REVISION, "status": "complete", "files": entries}
        source = {"model_id": target.MODEL_ID, "revision": target.REVISION, "files": sources}
        (self.assets / "manifest.json").write_text(json.dumps(manifest))
        (self.assets / "source-metadata.json").write_text(json.dumps(source))
        self.manifest_sha = hashlib.sha256((self.assets / "manifest.json").read_bytes()).hexdigest()
        self.source_sha = hashlib.sha256((self.assets / "source-metadata.json").read_bytes()).hexdigest()
        self.docs = docs

    def populations(self, private=False):
        texts = ["PRIVATE_DEVELOPMENT e\u0301" if private else "raw e\u0301", "A" * 511 + "<|im_end|>" + "Z" * 20,
                 "terminal<|im_end|>"]
        result = {}
        for role, split in (("eligible_training", "train"), ("eligible_validation", "validation")):
            selected = texts if split == "train" else ["validation sample"]
            records, references = [], []
            for index, text in enumerate(selected):
                example_id = f"{input_data.REVISION}:{split}:{index}"
                records.append(input_data.InputRecord(example_id, split, index, hashlib.sha256(text.encode()).hexdigest(), text))
                references.append({"example_id": example_id, "label": index % 2})
            result[role] = input_data.LoadedDevelopment(tuple(records), tuple(references),
                               {"expected_rows": len(records), "scope": "synthetic fixture only"})
        return result

    def patched(self, tokenizer=None, private=False):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(target, "ASSET_MANIFEST_SHA256", self.manifest_sha))
        stack.enter_context(patch.object(target, "SOURCE_METADATA_SHA256", self.source_sha))
        stack.enter_context(patch.object(target.importlib.metadata, "version", side_effect=lambda name: target.VERSIONS[name]))
        stack.enter_context(patch.object(target, "library_sources", return_value={"synthetic_fixture_only": "0" * 64}))
        tokenizer = tokenizer or Qwen2TokenizerFast()
        tokenizer_factory = Mock(return_value=tokenizer)
        config_factory = Mock(return_value=SimpleNamespace(**self.config))
        fake_module = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=tokenizer_factory),
                                      AutoConfig=SimpleNamespace(from_pretrained=config_factory))
        stack.enter_context(patch.dict(sys.modules, {"transformers": fake_module}))
        data = self.populations(private)
        loader = stack.enter_context(patch.object(target.input_data, "load_development", side_effect=lambda role, *args: data[role]))
        return tokenizer, tokenizer_factory, config_factory, loader, data

    def run_audit(self, name="output", **kwargs):
        return target.audit(self.root / name, self.assets, "synthetic-access.json", "0" * 64,
                            "synthetic-partitions", "synthetic-raw", batch_size=2,
                            asset_manifest_sha256=self.manifest_sha, **kwargs)

    def test_protected_role_and_wrong_asset_expectation_reject_before_reads_or_native(self):
        for roles in (("test_a", "eligible_validation"), ("eligible_training", "test_b"), (), ("eligible_training",)):
            with self.subTest(roles=roles), patch.object(Path, "read_bytes", side_effect=AssertionError("No read")), \
                    patch.object(target, "load_native") as native:
                with self.assertRaises(ValueError):
                    self.run_audit(roles=roles)
                native.assert_not_called()
        with patch.object(Path, "read_bytes", side_effect=AssertionError("No read")), patch.object(target, "load_native") as native:
            with self.assertRaises(target.TokenizerAuditError):
                target.audit(self.root / "out", self.assets, "access", "0" * 64, "partitions", "raw", asset_manifest_sha256="0" * 64)
            native.assert_not_called()
        self.assertFalse((self.root / "out").exists())

    def test_asset_tamper_precedes_native_import(self):
        self.patched()
        (self.assets / "tokenizer_config.json").write_bytes(b"tampered")
        with patch.object(target, "load_native") as native:
            with self.assertRaises(target.TokenizerAuditError):
                self.run_audit()
            native.assert_not_called()
        manifest = json.loads((self.root / "output" / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "incomplete")
        self.assertEqual(manifest["stage"], "asset_validation")
        self.assertNotIn("error_message", manifest)
        self.assertFalse((self.root / "output" / "summary.json").exists())

    def test_unapproved_asset_revision_rejected_even_with_matching_receipt_hashes(self):
        for name in ("manifest.json", "source-metadata.json"):
            value = json.loads((self.assets / name).read_text())
            value["revision"] = "b" * 40
            (self.assets / name).write_text(json.dumps(value))
        manifest_sha = hashlib.sha256((self.assets / "manifest.json").read_bytes()).hexdigest()
        source_sha = hashlib.sha256((self.assets / "source-metadata.json").read_bytes()).hexdigest()
        with patch.object(target, "ASSET_MANIFEST_SHA256", manifest_sha), patch.object(target, "SOURCE_METADATA_SHA256", source_sha):
            with self.assertRaisesRegex(target.TokenizerAuditError, "source identity"):
                target.verify_assets(self.assets)

    def test_explicit_native_factory_flags_and_config_defaults(self):
        _, tokenizer_factory, config_factory, _, _ = self.patched()
        _, record = target.load_native(self.assets, self.config)
        tokenizer_factory.assert_called_once_with(str(self.assets), use_fast=True, local_files_only=True, trust_remote_code=False)
        config_factory.assert_called_once_with(str(self.assets), local_files_only=True, trust_remote_code=False)
        self.assertEqual(record["resolved_config"]["num_labels"], 2)
        self.assertIsNone(record["resolved_config"]["pad_token_id"])
        self.assertFalse(record["model_loaded"])
        config_factory.return_value.pad_token_id = 151645
        with self.assertRaisesRegex(target.TokenizerAuditError, "PAD defaults"):
            target.load_native(self.assets, self.config)
        with patch.object(target.importlib.metadata, "version", return_value="different"):
            with self.assertRaisesRegex(target.TokenizerAuditError, "versions"):
                target.load_native(self.assets, self.config)

    def test_synthetic_checks_detect_semantic_failures_not_ordinary_bpe_lengths(self):
        for fault in ("auto_eos", "serialized_cap_leak", "wrong_pad", "suffix", "literal_eos_masked"):
            with self.subTest(fault=fault), self.assertRaises(target.TokenizerAuditError):
                target.synthetic_checks(Qwen2TokenizerFast(fault), self.docs)
        result = target.synthetic_checks(Qwen2TokenizerFast(), self.docs)
        self.assertEqual(result["serialized_5000_diagnostic"]["explicit_untruncated"], 5001)
        self.assertEqual(result["cases"][1]["input_ids"], [])
        self.assertEqual(result["padded_backend_state"]["padding"]["pad_id"], 151645)
        self.assertEqual(result["final_backend_state"], {"padding": None, "truncation": None})

    def test_source_pooling_integer_boundaries(self):
        self.assertEqual(target.pool_diagnostic([9, 151645], [1, 1])["pad_eos_source_pool_index"], 0)
        self.assertEqual(target.pool_diagnostic([151645, 151645], [1, 1])["pad_eos_source_pool_index"], 0)
        self.assertEqual(target.pool_diagnostic([151645, 9, 151645], [0, 1, 1])["last_visible_index"], 2)
        for ids, mask in (([], []), ([151645], [0])):
            with self.assertRaises(target.TokenizerAuditError):
                target.pool_diagnostic(ids, mask)

    def test_quantiles_denominators_and_empty_class_known_answers(self):
        self.assertEqual(target.length_summary([1, 2, 3, 100]),
                         {"n": 4, "min": 1, "max": 100, "mean": 26.5, "median": 2.5, "p90": 100, "p95": 100, "p99": 100})
        self.assertEqual(target.length_summary(list(range(1, 101)))["p90"], 90)
        empty = target.aggregate([])
        self.assertEqual(empty["original_lengths"], {"n": 0})
        self.assertIsNone(empty["caps"]["512"]["truncated_fraction"])
        self.assertEqual(empty["caps"]["512"]["denominator_rows"], 0)

    def test_mock_complete_audit_coverage_counts_raw_preservation_and_no_real_vectors(self):
        tokenizer, _, _, loader, data = self.patched()
        result = self.run_audit()
        self.assertEqual([call.args[0] for call in loader.call_args_list], list(target.ROLES))
        train = result["populations"]["eligible_training"]
        self.assertEqual(train["total"]["rows"], 3)
        self.assertEqual(train["total"]["caps"]["512"]["truncated_rows"], 1)
        self.assertEqual(train["total"]["caps"]["512"]["truncated_fraction"], 1 / 3)
        self.assertEqual(train["by_class"]["1"]["caps"]["512"]["truncated_fraction"], 1)
        self.assertEqual(train["total"]["python_nfc_changed_rows"], 1)
        original = data["eligible_training"].records[0].prompt
        self.assertTrue(any(original in texts for texts, _ in tokenizer.calls))
        out = self.root / "output"
        rows = [json.loads(line) for line in (out / "eligible_training-lengths.jsonl").read_text().splitlines()]
        self.assertEqual([r["example_id"] for r in rows], [r.example_id for r in data["eligible_training"].records])
        self.assertTrue(rows[1]["caps"]["512"]["ends_in_eos"])
        self.assertTrue(rows[1]["caps"]["512"]["source_pool_index_disagreement"])
        for row in rows:
            self.assertNotIn("input_ids", json.dumps(row))
            self.assertNotIn("prompt", row)
        self.assertEqual(json.loads((out / "manifest.json").read_text())["processed_rows"],
                         {"eligible_training": 3, "eligible_validation": 1})
        self.assertFalse(result["study_cap_selected"])
        self.assertFalse(result["model_loaded_or_inference_performed"])
        self.assertEqual(result["candidate_caps"], [512, 1024, 2048])
        for path in out.iterdir():
            self.assertNotIn(original.encode(), path.read_bytes())
        before = {path.name: path.read_bytes() for path in out.iterdir()}
        with self.assertRaisesRegex(target.TokenizerAuditError, "must be new"):
            self.run_audit()
        self.assertEqual(before, {path.name: path.read_bytes() for path in out.iterdir()})

    def test_provider_failure_sanitized_with_incomplete_summary_absent(self):
        self.patched(Qwen2TokenizerFast("provider_reflection"), private=True)
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr), self.assertRaises(target.TokenizerAuditError) as raised:
            self.run_audit()
        self.assertNotIn("PRIVATE_DEVELOPMENT", str(raised.exception) + stdout.getvalue() + stderr.getvalue())
        out = self.root / "output"
        self.assertFalse((out / "summary.json").exists())
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "incomplete")
        self.assertEqual(manifest["error_type"], "ValueError")
        for path in out.iterdir():
            self.assertNotIn(b"PRIVATE_DEVELOPMENT", path.read_bytes())

    def test_failure_after_first_valid_row_retains_exact_progress(self):
        _, _, _, loader, data = self.patched()
        prior = data["eligible_training"]
        changed = list(prior.records)
        changed[1] = input_data.InputRecord(changed[1].example_id, "train", 1, hashlib.sha256(b"").hexdigest(), "")
        data["eligible_training"] = input_data.LoadedDevelopment(tuple(changed), prior.references, prior.evidence)
        with self.assertRaises(target.TokenizerAuditError):
            self.run_audit()
        out = self.root / "output"
        self.assertEqual(len((out / "eligible_training-lengths.jsonl").read_text().splitlines()), 1)
        self.assertEqual(json.loads((out / "manifest.json").read_text())["processed_rows"]["eligible_training"], 1)


if __name__ == "__main__":
    unittest.main()
