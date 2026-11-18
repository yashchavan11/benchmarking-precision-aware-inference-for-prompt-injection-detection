"""Local-only P1-B pilot: matched unpadded training inputs in one precision per process.

The command never downloads assets or opens official-test data. It preserves failed
runs as incomplete. Timing observations are bounded feasibility evidence, not the
final profiling study. Native inference imports occur only after input validation.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import sys
import time

from . import input_data, tokenizer_audit
from .preprocessing import CAP, PREPROCESSING_OPTIONS as PREPROCESSING
from .preprocessing import PreprocessingError, encode_prompt
from .preprocessing import validate_vectors as validate_preprocessed_vectors

PRECISIONS = ("fp32", "fp16", "int8")
ROLE = "eligible_training"
SIZE = 128
WEIGHT_BYTES = 1192138968
WEIGHT_SHA256 = "19701022d11e38d39bd77aed7263d2e9ce3a45ae29305248ef3de585f947511c"
THRESHOLD_SOURCE = "provisional-p1b-fixed-0.5-not-validation-selected"
EXAMPLE_FIELDS = {"example_id", "label", "raw_text_sha256", "source_split", "source_row",
                  "original_tokens", "effective_tokens", "truncated", "data_role"}


class PilotError(ValueError):
    """Safe fixed messages; no raw source or provider error is included."""


def require(condition, message):
    if not condition:
        raise PilotError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def load_pilot(path, expected_sha256):
    path = Path(path)
    manifest = input_data.parsed(input_data.checked_bytes(path, expected_sha256))
    require(manifest.get("data_role") == ROLE, "Pilot permits only eligible training; no source was opened")
    require(manifest.get("schema_version") == 1 and type(manifest.get("schema_version")) is int
            and manifest.get("purpose") == "development_precision_pilot"
            and manifest.get("decision_id") == "D-012", "Pilot purpose/version/decision mismatch")
    require(manifest.get("model_revision") == tokenizer_audit.REVISION
            and manifest.get("tokenizer_revision") == tokenizer_audit.REVISION
            and manifest.get("dataset_revision") == input_data.REVISION, "Pilot asset revisions differ")
    require(type(manifest.get("cap")) is int and manifest["cap"] == CAP
            and type(manifest.get("batch_size")) is int and manifest["batch_size"] == 1,
            "Pilot requires cap 1024 and unpadded batch one")
    require(type(manifest.get("threshold")) in (int, float) and manifest["threshold"] == 0.5
            and manifest.get("threshold_source") == THRESHOLD_SOURCE, "Provisional threshold contract differs")
    require(canonical(manifest.get("preprocessing_options")) == canonical(PREPROCESSING),
            "Pilot preprocessing differs from approved options")
    for name in ("population_id", "preprocessing_id", "input_schedule_id"):
        require(isinstance(manifest.get(name), str) and bool(manifest[name]), "Pilot identity missing")
    ids = manifest.get("selected_ids")
    require(isinstance(ids, list) and len(ids) == SIZE and all(isinstance(value, str) for value in ids)
            and len(set(ids)) == SIZE, "Pilot must identify exactly 128 unique examples")
    require(input_data.id_hash(ids) == manifest.get("ordered_id_sha256")
            and input_data.id_hash(sorted(ids)) == manifest.get("membership_sha256"), "Pilot membership hashes disagree")
    ref = manifest.get("examples")
    require(isinstance(ref, dict) and ref.get("path") == "examples.jsonl", "Pilot examples must use the fixed local filename")
    raw = input_data.checked_bytes(input_data.fixed_path(path.parent, "examples.jsonl"), ref.get("sha256"))
    rows = [input_data.parsed(line.encode("utf-8")) for line in raw.decode("utf-8").splitlines()]
    require(len(rows) == SIZE and [row.get("example_id") for row in rows] == ids, "Pilot examples/order differ from manifest")
    previous = -1
    for row in rows:
        require(set(row) == EXAMPLE_FIELDS and row["data_role"] == ROLE and row["source_split"] == "train",
                "Pilot example schema/role is invalid")
        require(type(row["source_row"]) is int and row["source_row"] > previous
                and row["example_id"] == f"{input_data.REVISION}:train:{row['source_row']}",
                "Pilot source lineage/order is invalid")
        require(type(row["label"]) is int and row["label"] in (0, 1)
                and input_data.valid_sha(row["raw_text_sha256"]), "Pilot label/hash invalid")
        original, effective = row["original_tokens"], row["effective_tokens"]
        require(type(original) is int and original > 0 and type(effective) is int
                and effective == min(original, CAP) and type(row["truncated"]) is bool
                and row["truncated"] == (original > CAP), "Pilot length metadata inconsistent")
        previous = row["source_row"]
    require(Counter(row["label"] for row in rows) == {0: 64, 1: 64}, "Pilot class support differs from selected design")
    for label in (0, 1):
        lengths = [row["original_tokens"] for row in rows if row["label"] == label]
        require((sum(n <= 512 for n in lengths), sum(512 < n <= CAP for n in lengths), sum(n > CAP for n in lengths))
                == (48, 8, 8), "Pilot length-stratum support differs from selected design")
    return manifest, rows


def select_records(population, examples):
    by_id = {row.example_id: row for row in population.records}
    references = {row["example_id"]: row for row in population.references}
    selected = []
    for example in examples:
        key = example["example_id"]
        require(key in by_id and key in references, "Pilot ID not in authorized training population")
        record, reference = by_id[key], references[key]
        require(record.source_split == "train" and record.source_row == example["source_row"]
                and record.raw_text_sha256 == example["raw_text_sha256"]
                and reference["label"] == example["label"], "Pilot example differs from authorized source")
        selected.append(record)
    return selected


def validate_vectors(ids, mask):
    try:
        validate_preprocessed_vectors(ids, mask)
    except PreprocessingError as exc:
        raise PilotError(str(exc)) from None


def prepare_inputs(tokenizer, records, examples):
    require(len(records) == len(examples) == SIZE, "Pilot tokenization coverage differs")
    prepared, schedule = [], hashlib.sha256()
    for record, expected in zip(records, examples):
        try:
            ids, mask, original_length = encode_prompt(tokenizer, record.prompt, record.raw_text_sha256)
        except PreprocessingError as exc:
            raise PilotError(str(exc)) from None
        require(original_length == expected["original_tokens"]
                and len(ids) == expected["effective_tokens"], "Tokenization disagrees with reviewed pilot length/prefix evidence")
        schedule.update(canonical({"example_id": record.example_id, "input_ids": ids, "attention_mask": mask}) + b"\n")
        prepared.append((record.example_id, ids, mask))
    return prepared, schedule.hexdigest()


def verify_checkpoint(path, assets):
    path = Path(path)
    require(path.name == "model.safetensors" and path.is_file() and path.stat().st_size == WEIGHT_BYTES,
            "Full pinned checkpoint file/size is unavailable")
    require(file_hash(path) == WEIGHT_SHA256, "Full checkpoint SHA-256 mismatch")
    require((path.parent / "config.json").read_bytes() == (Path(assets) / "config.json").read_bytes(),
            "Checkpoint directory config differs from pinned audited config")
    return {"filename": "model.safetensors", "bytes": WEIGHT_BYTES, "sha256": WEIGHT_SHA256,
            "full_payload_hash_verified": True}


def source_identity():
    names = ("pilot_inference.py", "preprocessing.py", "input_data.py", "tokenizer_audit.py", "contract_audit.py", "artifacts.py")
    sources = {"precision_benchmark/" + name: file_hash(Path(__file__).with_name(name)) for name in names}
    return sources, "sha256:" + digest(canonical(sources))


class TorchRunner:
    def __init__(self, precision, checkpoint_dir, device):
        require(precision in PRECISIONS and re.fullmatch(r"cuda:[0-9]+", device) is not None,
                "Pilot requires one declared CUDA device and supported precision")
        import torch
        from transformers import AutoModelForSequenceClassification, BitsAndBytesConfig
        self.torch, self.precision, self.device = torch, precision, torch.device(device)
        require(torch.cuda.is_available() and self.device.index < torch.cuda.device_count(), "Requested CUDA device is unavailable")
        require(importlib.metadata.version("torch").split("+")[0] == "2.9.1"
                and torch.version.cuda == "12.6" and importlib.metadata.version("bitsandbytes") == "0.48.2"
                and importlib.metadata.version("accelerate") == "1.11.0", "GPU runtime differs from pinned pilot environment")
        props = torch.cuda.get_device_properties(self.device)
        require((props.major, props.minor) >= (7, 5), "GPU capability is below the selected three-treatment minimum")
        torch.cuda.set_device(self.device)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.set_float32_matmul_precision("highest")
        torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction = False
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
        torch.backends.cudnn.benchmark = False
        torch.manual_seed(0)
        torch.cuda.manual_seed_all(0)
        dtype = torch.float32 if precision == "fp32" else torch.float16
        kwargs = {"local_files_only": True, "trust_remote_code": False, "use_safetensors": True,
                  "torch_dtype": dtype, "attn_implementation": "eager", "device_map": {"": device},
                  "low_cpu_mem_usage": True, "output_loading_info": True}
        if precision == "int8":
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True, llm_int8_threshold=6.0,
                    llm_int8_skip_modules=["score"], llm_int8_has_fp16_weight=False,
                    llm_int8_enable_fp32_cpu_offload=False)
        torch.cuda.synchronize(self.device)
        start = time.perf_counter()
        with tokenizer_audit.contract_audit.quiet_provider():
            self.model, loading = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_dir), **kwargs)
        torch.cuda.synchronize(self.device)
        self.loading_seconds = time.perf_counter() - start
        require(all(not loading.get(key) for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")),
                "Checkpoint loading reported missing/unexpected/mismatched tensors")
        self.loading_info = {key: loading.get(key, []) for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")}
        self.model.eval()
        for parameter in self.model.parameters():
            parameter.requires_grad_(False)
        config = self.model.config
        require(config.num_labels == 2 and config.id2label == {0: "benign", 1: "jailbreak"}
                and config.pad_token_id is None and config._attn_implementation == "eager",
                "Loaded classifier labels/PAD/attention contract differs")
        require(list(self.model.score.weight.shape) == [2, 1024] and self.model.score.bias is None
                and type(self.model.score).__name__ == "Linear", "Loaded classifier head differs or was quantized")

    def flags(self):
        torch = self.torch
        return {"tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
                "tf32_cudnn": torch.backends.cudnn.allow_tf32,
                "float32_matmul_precision": torch.get_float32_matmul_precision(),
                "fp16_reduced_precision_reduction": torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction,
                "bf16_reduced_precision_reduction": torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction,
                "cudnn_benchmark": torch.backends.cudnn.benchmark,
                "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                "autocast_enabled_outside_forward": torch.is_autocast_enabled(), "attention": "eager"}

    def environment(self):
        torch = self.torch
        versions = {}
        for name in ("torch", "transformers", "tokenizers", "accelerate", "bitsandbytes", "safetensors"):
            try:
                versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                versions[name] = None
        props = torch.cuda.get_device_properties(self.device)
        evidence = {"python": sys.version, "platform": platform.platform(), "versions": versions,
                    "gpu_name": props.name, "gpu_total_memory": props.total_memory,
                    "gpu_compute_capability": [props.major, props.minor], "device": str(self.device),
                    "gpu_uuid": str(getattr(props, "uuid", "unavailable")), "cuda_runtime": torch.version.cuda,
                    "cudnn_version": torch.backends.cudnn.version(), "flags": self.flags(),
                    "allocation_id": os.environ.get("SLURM_JOB_ID", "local"),
                    "scope": "Matched pilot execution environment; timings are feasibility observations only"}
        return evidence, "sha256:" + digest(canonical(evidence))

    def forward(self, ids, mask):
        validate_vectors(ids, mask)
        torch = self.torch
        inputs = {"input_ids": torch.tensor([ids], dtype=torch.long, device=self.device),
                  "attention_mask": torch.tensor([mask], dtype=torch.long, device=self.device)}
        torch.cuda.synchronize(self.device)
        start = time.perf_counter()
        with torch.inference_mode(), torch.autocast(device_type="cuda", enabled=False):
            output = self.model(**inputs, use_cache=False, return_dict=True)
        torch.cuda.synchronize(self.device)
        elapsed = time.perf_counter() - start
        require(tuple(output.logits.shape) == (1, 2) and bool(torch.isfinite(output.logits).all().item()),
                "Model returned nonfinite logits or the wrong output shape")
        require(output.logits.dtype == (torch.float32 if self.precision == "fp32" else torch.float16),
                "Executed output-logit dtype differs from retained-head policy")
        self.observed_logits_dtype = str(output.logits.dtype)
        probabilities = torch.softmax(output.logits.to(torch.float32), dim=-1)
        require(bool(torch.isfinite(probabilities).all().item()), "Score conversion returned nonfinite probabilities")
        score = float(probabilities[0, 1].item())
        require(math.isfinite(score) and 0 <= score <= 1 and elapsed > 0, "Invalid injection score or timing sample")
        return {"score": score, "logits": output.logits[0].to(torch.float32).detach().cpu().tolist(),
                "forward_seconds": elapsed, "raw_logits": output.logits}

    def synthetic_checks(self, tokenizer):
        torch = self.torch
        texts = ["Plain diagnostic text.", "before<|im_end|>after", "before<|im_end|>", "<|im_end|>"]
        cases, captured, module_io = [], [], {}
        hooks = []
        def observe(name, module, args, result):
            require(bool(args) and torch.is_tensor(args[0]) and torch.is_tensor(result),
                    "Observed projection/normalization module did not return expected tensors")
            item = module_io.setdefault(name, {"class": type(module).__name__, "input_dtypes": set(), "output_dtypes": set(), "calls": 0})
            item["input_dtypes"].add(str(args[0].dtype))
            item["output_dtypes"].add(str(result.dtype))
            item["calls"] += 1
        for name, module in self.model.named_modules():
            if type(module).__name__ in ("Embedding", "Linear", "Linear8bitLt", "Qwen3RMSNorm"):
                hooks.append(module.register_forward_hook(lambda module, args, result, name=name: observe(name, module, args, result)))
        hook = self.model.score.register_forward_hook(lambda module, args, result: captured.append(result.detach()))
        try:
            for text in texts:
                vectors, masks = tokenizer_audit.encode(tokenizer, [text], cap=CAP)
                captured.clear()
                result = self.forward(vectors[0], masks[0])
                require(len(captured) == 1 and tuple(captured[0].shape) == (1, len(vectors[0]), 2)
                        and torch.equal(result["raw_logits"], captured[0][:, -1, :]),
                        "Actual returned classifier logits do not equal the original final-token head output")
                cases.append({"text": text, "input_ids": vectors[0], "attention_mask": masks[0],
                              "selected_pool_index": len(vectors[0]) - 1, "last_token_is_eos": vectors[0][-1] == tokenizer_audit.EOS,
                              "final_token_head_exactly_matches_returned_logits": True, "logits": result["logits"]})
        finally:
            hook.remove()
            for handle in hooks:
                handle.remove()
        self.synthetic_module_io = {name: {**value, "input_dtypes": sorted(value["input_dtypes"]),
                                          "output_dtypes": sorted(value["output_dtypes"])} for name, value in module_io.items()}
        require(cases[2]["last_token_is_eos"] and cases[3]["input_ids"] == [tokenizer_audit.EOS],
                "Synthetic strings did not exercise terminal/EOS-only pooling")
        empty, _ = tokenizer_audit.encode(tokenizer, [""])
        require(empty == [[]], "Expected empty synthetic tokenization changed")
        for ids, mask in (([], []), ([tokenizer_audit.EOS], [0]), ([10], []), ([10], [True])):
            try:
                validate_vectors(ids, mask)
            except PilotError:
                pass
            else:
                raise PilotError("Empty/invalid-mask inference guard failed")
        # This is an intentionally invalid synthetic diagnostic, not a batched study treatment.
        padded, padded_masks = tokenizer_audit.encode(tokenizer, ["x", "A longer diagnostic input."], cap=CAP, padding=True)
        require(len(padded) == 2 and len(padded[0]) == len(padded[1]) and any(0 in mask for mask in padded_masks),
                "Synthetic padded-batch diagnostic did not exercise padding")
        try:
            with torch.inference_mode(), torch.autocast(device_type="cuda", enabled=False):
                self.model(input_ids=torch.tensor(padded, dtype=torch.long, device=self.device),
                           attention_mask=torch.tensor(padded_masks, dtype=torch.long, device=self.device),
                           use_cache=False, return_dict=True)
        except ValueError as error:
            require(str(error) == "Cannot handle batch sizes > 1 if no padding token is defined.",
                    "Padded diagnostic failed for an unexpected reason")
        else:
            raise PilotError("Original no-PAD model unexpectedly accepted a padded batch of two")
        torch.cuda.synchronize(self.device)
        return {"status": "passed", "scope": "Actual model forward/head-hook on synthetic inputs; no padding-policy modification",
                "cases": cases, "invalid_input_guards_passed": 4, "empty_model_call_performed": False,
                "model_pad_token_id": self.model.config.pad_token_id, "padded_batch_two_rejected_as_expected": True,
                "padded_batch_equivalence_tested": False}

    def precision_evidence(self):
        torch = self.torch
        expected_dtype = torch.float32 if self.precision == "fp32" else torch.float16
        def describe(name, tensor):
            return {"name": name, "class": type(tensor).__module__ + "." + type(tensor).__name__,
                    "shape": list(tensor.shape), "dtype": str(tensor.dtype), "device": str(tensor.device),
                    "elements": tensor.numel(), "storage_bytes": tensor.numel() * tensor.element_size(),
                    "requires_grad": bool(getattr(tensor, "requires_grad", False))}
        parameters = [describe(name, tensor) for name, tensor in self.model.named_parameters()]
        buffers = [describe(name, tensor) for name, tensor in self.model.named_buffers()]
        modules, quantized = [], []
        for name, module in self.model.named_modules():
            modules.append({"name": name, "class": type(module).__module__ + "." + type(module).__name__,
                            "training": module.training})
            if type(module).__name__ == "Linear8bitLt":
                state = getattr(module, "state", None)
                require(state is not None and state.threshold == 6.0 and not state.has_fp16_weights,
                        "INT8 outlier/retained-weight policy differs")
                state_tensors = []
                for owner_name, owner in (("weight", module.weight), ("state", state)):
                    for key in ("CB", "SCB"):
                        value = getattr(owner, key, None)
                        if torch.is_tensor(value):
                            state_tensors.append(describe(owner_name + "." + key, value))
                quantized.append({"name": name, "weight_dtype": str(module.weight.dtype),
                                  "threshold": state.threshold, "has_fp16_weights": state.has_fp16_weights,
                                  "state_tensors": state_tensors})
        require(parameters and all(not p["requires_grad"] and p["device"] == str(self.device) for p in parameters)
                and all(not item["training"] for item in modules), "Model is not fully frozen/eval/on the declared GPU")
        require(len(parameters) == 311 and sum(p["elements"] for p in parameters) == 596051968,
                "Loaded parameter tensor/element counts differ from the pinned checkpoint")
        require(all(item["device"] == str(self.device) for item in buffers), "Model buffer is outside the declared device")
        if self.precision == "int8":
            expected = {f"model.layers.{layer}.{group}.{projection}" for layer in range(28)
                        for group, names in (("self_attn", ("q_proj", "k_proj", "v_proj", "o_proj")),
                                             ("mlp", ("gate_proj", "up_proj", "down_proj"))) for projection in names}
            require({item["name"] for item in quantized} == expected
                    and all(item["weight_dtype"] == "torch.int8" for item in quantized),
                    "INT8 conversion does not cover exactly the intended 196 transformer projections")
            require({name for name, item in self.synthetic_module_io.items() if item["class"] == "Linear8bitLt"} == expected,
                    "Synthetic execution did not call every converted INT8 projection")
            quant_weights = {name + ".weight" for name in expected}
            require(all(p["dtype"] == ("torch.int8" if p["name"] in quant_weights else str(expected_dtype)) for p in parameters),
                    "INT8 residual parameter precision differs")
        else:
            require(not quantized and all(p["dtype"] == str(expected_dtype) for p in parameters),
                    "Floating-point parameter precision differs or quantized modules remain")
        require(self.model.score.weight.dtype == expected_dtype and self.model.score.bias is None,
                "Classifier head precision/policy differs")
        return {"precision": self.precision, "parameters": parameters, "buffers": buffers, "modules": modules,
                "quantized_linear_modules": quantized, "loading_info": self.loading_info,
                "head_shape": list(self.model.score.weight.shape), "head_dtype": str(self.model.score.weight.dtype),
                "head_quantized": False, "all_parameters_frozen": True, "all_modules_eval": True,
                "observed_logits_dtype": self.observed_logits_dtype, "synthetic_module_io": self.synthetic_module_io,
                "flags": self.flags(), "score_conversion": "torch.softmax(logits.float(), dim=-1)[0,1]",
                "computation_limits": "Tensor/module storage and executed output evidence; not a claim that every internal operation uses the named dtype"}

    def start_measurement(self):
        self.torch.cuda.synchronize(self.device)
        self.torch.cuda.reset_peak_memory_stats(self.device)
        return {"allocated_bytes": self.torch.cuda.memory_allocated(self.device),
                "reserved_bytes": self.torch.cuda.memory_reserved(self.device)}

    def memory(self):
        return {"peak_allocated_bytes": self.torch.cuda.max_memory_allocated(self.device),
                "peak_reserved_bytes": self.torch.cuda.max_memory_reserved(self.device)}


def run(output, pilot_path, pilot_sha256, assets, checkpoint, access, access_sha256,
        partitions, raw_dir, precision, run_id, device="cuda:0", runner_factory=TorchRunner):
    require(precision in PRECISIONS, "Unsupported precision")
    require(isinstance(run_id, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", run_id), "Invalid run ID")
    output = Path(output)
    require(not output.exists(), "Output directory already exists; preserve prior evidence")
    pilot, examples = load_pilot(pilot_path, pilot_sha256)
    docs, asset_hashes = tokenizer_audit.verify_assets(assets)
    population = input_data.load_development(ROLE, access, access_sha256, partitions, raw_dir)
    records = select_records(population, examples)
    checkpoint_evidence = verify_checkpoint(checkpoint, assets)
    checkpoint_stat = (Path(checkpoint).stat().st_size, Path(checkpoint).stat().st_mtime_ns)
    sources, code_revision = source_identity()
    output.mkdir(parents=True, exist_ok=False)
    job = {"status": "incomplete", "run_id": run_id, "precision": precision, "expected_rows": SIZE,
           "completed_rows": 0, "stage": "tokenization", "started_at_utc": datetime.now(timezone.utc).isoformat(),
           "pilot_manifest_sha256": pilot_sha256, "data_role": ROLE, "test_performance_released": False}
    write_json(output / "execution.json", job)
    try:
        tokenizer, tokenizer_runtime = tokenizer_audit.load_native(assets, docs["config.json"])
        prepared, token_hash = prepare_inputs(tokenizer, records, examples)
        effective_schedule = "sha256:" + digest(canonical({"planned_schedule": pilot["input_schedule_id"], "token_schedule_sha256": token_hash}))
        job["stage"] = "model_loading"
        write_json(output / "execution.json", job)
        runner = runner_factory(precision, Path(checkpoint).parent, device)
        environment, environment_id = runner.environment()
        write_json(output / "environment.json", environment)
        job["stage"] = "synthetic_checks"
        write_json(output / "execution.json", job)
        synthetic = runner.synthetic_checks(tokenizer)
        write_json(output / "synthetic-checks.json", synthetic)
        precision_evidence = runner.precision_evidence()
        write_json(output / "precision-evidence.json", precision_evidence)
        # Same first three pilot inputs and order for every treatment; warm-up is excluded from samples.
        job["stage"] = "warmup"
        write_json(output / "execution.json", job)
        for _, ids, mask in prepared[:3]:
            runner.forward(ids, mask)
        baseline = runner.start_measurement()
        job["stage"] = "pilot_inference"
        write_json(output / "execution.json", job)
        timings = []
        with (output / "predictions.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
            for index, ((example_id, ids, mask), example) in enumerate(zip(prepared, examples)):
                job["current_example_id"] = example_id
                result = runner.forward(ids, mask)
                score, logits, elapsed = result["score"], result["logits"], result["forward_seconds"]
                require(type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 1
                        and isinstance(logits, list) and len(logits) == 2
                        and all(type(v) in (int, float) and math.isfinite(v) for v in logits)
                        and type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed > 0,
                        "Invalid native inference output")
                row = {"example_id": example_id, "run_id": run_id, "score": score,
                       "prediction": int(score >= pilot["threshold"]), "logits": logits}
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                timings.append({"example_id": example_id, "effective_tokens": len(ids), "batch_size": 1,
                                "repetition": 0, "forward_seconds": elapsed})
                job["completed_rows"] = index + 1
                write_json(output / "execution.json", job)
        require(job["completed_rows"] == SIZE and tokenizer_audit.verify_assets(assets)[1] == asset_hashes,
                "Coverage incomplete or tokenizer assets changed during execution")
        require(runner.environment()[1] == environment_id, "Execution environment/flags changed during pilot")
        final_precision = runner.precision_evidence()
        write_json(output / "precision-evidence.json", final_precision)
        resource = {"scope": "Pilot feasibility only; one forward sample per selected training example; no final speedup/throughput claim",
                    "forward_boundary": "Pretokenized device-resident tensors to raw logits, synchronized before/after; excludes transfers/tokenization/score conversion",
                    "warmup": {"batches": 3, "schedule": "first three planned IDs in order"},
                    "loading_seconds": runner.loading_seconds, "loading_scope": "Populated local checkpoint to device; no download/hash verification",
                    "memory_baseline_after_warmup": baseline, "memory": runner.memory(), "samples": timings,
                    "median_forward_seconds": statistics.median(row["forward_seconds"] for row in timings),
                    "p95_forward_seconds": sorted(row["forward_seconds"] for row in timings)[math.ceil(0.95 * SIZE) - 1]}
        write_json(output / "feasibility.json", resource)
        require(source_identity() == (sources, code_revision), "Inference source files changed during execution")
        require((Path(checkpoint).stat().st_size, Path(checkpoint).stat().st_mtime_ns) == checkpoint_stat,
                "Checkpoint file changed after hash verification")
        manifest = {"run_id": run_id, "precision": precision, "status": "complete", "data_role": ROLE,
                    "population_id": pilot["population_id"], "threshold": pilot["threshold"], "threshold_source": pilot["threshold_source"],
                    "model_revision": tokenizer_audit.REVISION, "tokenizer_revision": tokenizer_audit.REVISION,
                    "dataset_revision": input_data.REVISION, "preprocessing_id": pilot["preprocessing_id"],
                    "input_schedule_id": effective_schedule, "planned_input_schedule_id": pilot["input_schedule_id"],
                    "token_schedule_sha256": token_hash, "environment_id": environment_id,
                    "score_semantics": "p_injection", "code_revision": code_revision,
                    "precision_evidence": "precision-evidence.json#sha256=" + file_hash(output / "precision-evidence.json"),
                    "predictions": {"path": "predictions.jsonl", "sha256": file_hash(output / "predictions.jsonl")},
                    "checkpoint": checkpoint_evidence, "tokenizer_runtime": tokenizer_runtime,
                    "pilot_manifest_sha256": pilot_sha256, "expected_rows": SIZE, "observed_rows": SIZE,
                    "source_sha256": sources, "test_performance_released": False,
                    "limitations": ["Deliberately balanced/tail-enriched training pilot, not representative or held-out quality.",
                                    "Threshold 0.5 is provisional, not selected on validation.",
                                    "Original unpadded batch-one pooling only; padded equivalence untested.",
                                    "Resource samples establish feasibility, not final controlled profiling or statistical benefit."],
                    "artifact_sha256": {name: file_hash(output / name) for name in
                                        ("environment.json", "synthetic-checks.json", "precision-evidence.json", "feasibility.json")}}
        job.update({"status": "complete", "stage": "complete", "completed_at_utc": datetime.now(timezone.utc).isoformat()})
        job.pop("current_example_id", None)
        write_json(output / "execution.json", job)
        write_json(output / "run.json", manifest)  # Completion marker last.
        return manifest
    except Exception as error:
        job.update({"status": "incomplete", "error_type": type(error).__name__, "error_details_suppressed": True})
        # Only this exact internal class is created from fixed diagnostics above.
        # Native/provider exception messages remain suppressed, including subclasses.
        if type(error) is PilotError:
            job["failure_reason"] = str(error)
        write_json(output / "execution.json", job)
        raise PilotError("Pilot incomplete; sanitized stage/coverage evidence retained") from None


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, "Invalid pilot arguments; use --help.\n")
    parser = SafeParser(description=__doc__)
    for name in ("output", "pilot", "assets", "checkpoint", "access", "partitions", "raw-dir"):
        parser.add_argument("--" + name, required=True, type=Path)
    for name in ("pilot-sha256", "access-sha256", "run-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--precision", required=True, choices=PRECISIONS)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    try:
        result = run(args.output, args.pilot, args.pilot_sha256, args.assets, args.checkpoint,
                     args.access, args.access_sha256, args.partitions, args.raw_dir,
                     args.precision, args.run_id, args.device)
    except Exception:
        print("Pilot did not complete; raw source/provider errors suppressed. Inspect sanitized execution evidence if present.", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "precision": result["precision"], "rows": result["observed_rows"],
                      "data_role": result["data_role"], "test_performance_released": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
