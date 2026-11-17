import unittest

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


if __name__ == "__main__":
    unittest.main()
