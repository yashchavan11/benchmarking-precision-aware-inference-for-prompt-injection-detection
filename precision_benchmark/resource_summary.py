"""Offline resource summary for retained FP32/FP16/INT8 pilot measurements.

Reads the text-free bundle bound by a comparison manifest, verifies the hash chain
comparison.json -> run.json -> feasibility/environment/precision evidence, checks that
all treatments measured the same workload, and regenerates the resource table from
the raw per-example samples. It runs no model and needs no GPU.

Run with:
    python -m precision_benchmark.resource_summary \
        --manifest docs/evidence/p1b-pilot-20261117/comparison.json --output <new directory>

Measurement boundaries come from the retained evidence; this module does not widen them.
In particular, the "derived forward-only rate" is n / sum(forward seconds). It is not a
measured wall-clock or end-to-end throughput, and it is never 1 / median latency.
"""

import argparse
import csv
import io
import json
import math
from pathlib import Path
import statistics
import sys

from . import artifacts, pilot_compare, pilot_inference

PRECISIONS = ("fp32", "fp16", "int8")
MIB = 2 ** 20
# Effective-token bands used for the shape breakdown (inclusive upper bounds).
LENGTH_BANDS = ((1, 128), (129, 512), (513, 1024))
RATE_DEFINITION = ("Derived forward-only rate = number of samples / sum of their synchronized forward "
                   "durations. Not a measured wall-clock, sustained or end-to-end throughput; "
                   "not 1 / median latency.")
P95_DEFINITION = "Nearest rank: sorted[ceil(0.95 * n) - 1]; median is the conventional median."
FORWARD_BOUNDARY = ("Pretokenized device-resident tensors to raw logits, synchronized before/after; "
                    "excludes transfers/tokenization/score conversion")
LOADING_SCOPE = "Populated local checkpoint to device; no download/hash verification"
WARMUP = {"batches": 3, "schedule": "first three planned IDs in order"}
FLAGS = {"attention": "eager", "autocast_enabled_outside_forward": False,
         "bf16_reduced_precision_reduction": False, "cudnn_benchmark": False,
         "deterministic_algorithms": False, "float32_matmul_precision": "highest",
         "fp16_reduced_precision_reduction": False, "tf32_cudnn": False, "tf32_matmul": False}
# PILOT-001 / D-012: scope authorization is independent of a caller's rehashed manifest.
APPROVED_EXAMPLES = "828cf651e2ccbeace777eb8936ab91fcbb888f7e903f22825b6c87163c222089"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nearest_rank(values, fraction):
    require(values, "Cannot take a quantile of no values")
    ordered = sorted(values)
    return ordered[math.ceil(fraction * len(ordered)) - 1]


def _load_json(path):
    def bad_constant(_):
        raise ValueError("Nonfinite JSON constant")
    value = json.loads(Path(path).read_bytes(), parse_constant=bad_constant,
                       object_pairs_hook=artifacts.unique_object)
    require(isinstance(value, dict), "Expected a JSON object")
    return value


def _verified(path, expected_sha256, label):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"{label} is missing or not a regular file")
    require(pilot_inference.file_hash(path) == expected_sha256, f"{label} hash does not match its manifest")
    return _load_json(path)


def _finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _identity(value):
    return "sha256:" + pilot_inference.digest(pilot_inference.canonical(value))


def _relative(base, entry):
    require(isinstance(entry, dict) and isinstance(entry.get("path"), str), "Missing relative file reference")
    relative = Path(entry["path"])
    # pilot_compare intentionally emits sibling-relative references in a new analysis directory.
    require(not relative.is_absolute(), "File references must be relative")
    return base / relative


def load_bundle(manifest_path):
    """Load only the D-012 training pilot, including its linked population and predictions.

    This is not a generic profiler or a held-out evaluation reader. Hashes establish
    retained evidence consistency, not independent proof of native execution.
    """
    manifest_path = Path(manifest_path)
    manifest = _load_json(manifest_path)
    require(type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1,
            "Unsupported comparison schema")
    require(manifest.get("data_role") == pilot_inference.ROLE,
            "Resource summary supports only the D-012 eligible_training pilot")
    base = manifest_path.parent
    runs = manifest.get("runs")
    require(isinstance(runs, list) and len(runs) == len(PRECISIONS), "Manifest must reference exactly three runs")
    bundle = {}
    for entry in runs:
        run_path = _relative(base, entry)
        run = _verified(run_path, entry.get("sha256"), "run.json")
        precision = run.get("precision")
        require(precision in PRECISIONS and precision not in bundle, "Unexpected or duplicate precision")
        require(run.get("status") == "complete", f"{precision} run is not complete")
        bundle[precision] = {"run": run, "directory": run_path.parent}
    require(set(bundle) == set(PRECISIONS), "Bundle lacks one of fp32/fp16/int8")
    pilot_path = _relative(base, manifest["examples"]).parent / "manifest.json"
    pilot_sha = bundle["fp32"]["run"].get("pilot_manifest_sha256")
    pilot, rows = pilot_inference.load_pilot(pilot_path, pilot_sha)
    require(pilot["examples"]["sha256"] == APPROVED_EXAMPLES,
            "Pilot membership is not the approved D-012 population")
    require(manifest["examples"]["sha256"] == pilot["examples"]["sha256"]
            and manifest.get("population_id") == pilot["population_id"], "Comparison population differs from pilot")
    require(pilot.get("rows") == len(rows)
            and pilot["population_id"] == "pilot-128:sha256:" + pilot["membership_sha256"]
            and _identity(pilot.get("preprocessing_contract")) == pilot["preprocessing_id"]
            and _identity(pilot.get("input_schedule")) == pilot["input_schedule_id"],
            "Pilot population/preprocessing/planned schedule identities disagree")
    for precision, loaded in bundle.items():
        run = loaded["run"]
        pilot_compare.bind_run(run, pilot, pilot_sha, precision)
        require(type(run.get("expected_rows")) is int and run["expected_rows"] == len(rows)
                and type(run.get("observed_rows")) is int and run["observed_rows"] == len(rows)
                and run.get("test_performance_released") is False, "Incomplete or unsupported run coverage/release")
        require(run.get("checkpoint") == {"bytes": pilot_inference.WEIGHT_BYTES, "filename": "model.safetensors",
                "full_payload_hash_verified": True, "sha256": pilot_inference.WEIGHT_SHA256}, "Checkpoint contract differs")
        sources = run.get("source_sha256")
        require(isinstance(sources, dict) and sources
                and all(pilot_inference.input_data.valid_sha(v) for v in sources.values())
                and run["code_revision"] == _identity(sources), "Executed source digest differs")
        loaded["examples"] = rows
    # Only after authorizing the linked training membership do we open predictions.
    # The shared reader validates their hashes, complete IDs, thresholds and common identities.
    _, examples, checked_runs, _, _ = artifacts.load_comparison(manifest_path)
    require(list(examples.values()) == rows, "Comparison examples differ from linked pilot examples")
    for precision, loaded in bundle.items():
        require(loaded["run"] == checked_runs[precision], "Run changed during comparison validation")
        hashes = loaded["run"].get("artifact_sha256", {})
        for name, key in (("feasibility.json", "feasibility"), ("environment.json", "environment"),
                          ("precision-evidence.json", "precision_evidence")):
            loaded[key] = _verified(loaded["directory"] / name, hashes.get(name), f"{precision} {name}")
    return bundle


def _check_matched(bundle):
    """All treatments must time the same examples, token lengths and order on one device."""
    reference = [(row["example_id"], row["effective_tokens"]) for row in bundle["fp32"]["examples"]]
    for precision in PRECISIONS:
        loaded = bundle[precision]
        feasibility, environment, run = loaded["feasibility"], loaded["environment"], loaded["run"]
        samples = feasibility.get("samples")
        require(isinstance(samples, list) and samples, f"{precision} has no raw samples")
        for row in samples:
            require(type(row.get("batch_size")) is int and row["batch_size"] == 1
                    and type(row.get("repetition")) is int and row["repetition"] == 0,
                    "Only the single-pass batch-size-one pilot is supported")
            require(type(row.get("effective_tokens")) is int and 0 < row["effective_tokens"] <= pilot_inference.CAP,
                    "Invalid effective token count")
            require(_finite_positive(row.get("forward_seconds")), "Invalid forward duration")
        schedule = [(row["example_id"], row["effective_tokens"]) for row in samples]
        require(schedule == reference,
                "Timing coverage/order/lengths differ from the expected pilot examples")
        require(feasibility.get("forward_boundary") == FORWARD_BOUNDARY
                and feasibility.get("loading_scope") == LOADING_SCOPE
                and pilot_inference.canonical(feasibility.get("warmup")) == pilot_inference.canonical(WARMUP),
                "Unsupported measurement boundary or warmup schedule")
        require(_finite_positive(feasibility.get("loading_seconds")), "Invalid loading duration")
        memory, baseline = feasibility.get("memory", {}), feasibility.get("memory_baseline_after_warmup", {})
        for values, keys in ((memory, ("peak_allocated_bytes", "peak_reserved_bytes")),
                             (baseline, ("allocated_bytes", "reserved_bytes"))):
            require(all(type(values.get(k)) is int and values[k] > 0 for k in keys), "Invalid memory measurement")
        require(memory["peak_reserved_bytes"] >= memory["peak_allocated_bytes"] >= baseline["allocated_bytes"]
                and memory["peak_reserved_bytes"] >= baseline["reserved_bytes"] >= baseline["allocated_bytes"],
                "Inconsistent memory baseline/peak")
        for field in ("gpu_uuid", "allocation_id", "gpu_name", "device", "python", "platform", "cuda_runtime"):
            value = environment.get(field)
            require(isinstance(value, str) and value.strip() and value not in ("unavailable", "local"),
                    f"Missing execution environment {field}")
        require(pilot_inference.canonical(environment.get("flags")) == pilot_inference.canonical(FLAGS)
                and run["environment_id"] == _identity(environment),
                "Environment digest or supported execution flags differ")
        versions = environment.get("versions", {})
        require(all(isinstance(versions.get(k), str) and versions[k] for k in
                    ("torch", "transformers", "tokenizers", "accelerate", "bitsandbytes", "safetensors")),
                "Missing dependency evidence")
        require(environment == bundle["fp32"]["environment"], "Treatments ran in different environments/devices")
        for key in ("token_schedule_sha256", "checkpoint", "source_sha256", "tokenizer_runtime"):
            require(run.get(key) == bundle["fp32"]["run"].get(key) and run.get(key), f"Incompatible or missing {key}")
        _check_precision(precision, loaded)
    return reference


def _check_precision(precision, loaded):
    """Validate the recorded storage used by the table; this does not rerun the model."""
    evidence, environment = loaded["precision_evidence"], loaded["environment"]
    dtype = "torch.float32" if precision == "fp32" else "torch.float16"
    require(evidence.get("precision") == precision and evidence.get("flags") == environment["flags"]
            and evidence.get("head_shape") == [2, 1024] and evidence.get("head_dtype") == dtype
            and evidence.get("observed_logits_dtype") == dtype and evidence.get("head_quantized") is False
            and evidence.get("all_parameters_frozen") is True and evidence.get("all_modules_eval") is True,
            "Precision/head/execution evidence differs")
    parameters = evidence.get("parameters")
    require(isinstance(parameters, list) and len(parameters) == 311, "Incomplete parameter storage evidence")
    names = {p.get("name") for p in parameters}
    require(len(names) == len(parameters) and all(isinstance(n, str) and n for n in names), "Duplicate/missing parameter names")
    quantized = evidence.get("quantized_linear_modules")
    expected = {f"model.layers.{i}.{layer}" for i in range(28) for layer in
                ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
                 "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")} if precision == "int8" else set()
    require(isinstance(quantized, list) and len(quantized) == len(expected)
            and {q.get("name") for q in quantized} == expected, "Quantized projection evidence differs")
    by_name = {p["name"]: p for p in parameters}
    for parameter in parameters:
        wanted = "torch.int8" if parameter["name"].removesuffix(".weight") in expected else dtype
        _check_tensor(parameter, wanted, environment["device"])
    require(sum(p["elements"] for p in parameters) == 596051968, "Parameter element coverage differs")
    require(by_name.get("score.weight", {}).get("shape") == [2, 1024], "Classifier parameter evidence differs")
    for module in quantized:
        require(module.get("threshold") == 6.0 and module.get("has_fp16_weights") is False
                and module.get("weight_dtype") == "torch.int8", "INT8 treatment settings differ")
        states = module.get("state_tensors", [])
        require(len(states) == 2 and {s.get("name") for s in states} == {"state.CB", "state.SCB"},
                "Missing INT8 state storage evidence")
        weight = by_name.get(module["name"] + ".weight", {})
        for state in states:
            _check_tensor(state, "torch.int8" if state["name"] == "state.CB" else "torch.float32", environment["device"])
            require(state["shape"] == (weight.get("shape") if state["name"] == "state.CB" else weight.get("shape", [])[:1]),
                    "INT8 state shape differs from weight")


def _check_tensor(tensor, dtype, device):
    shape = tensor.get("shape")
    require(isinstance(shape, list) and shape and all(type(n) is int and n > 0 for n in shape), "Invalid tensor shape")
    elements = math.prod(shape)
    require(tensor.get("dtype") == dtype and tensor.get("device") == device and tensor.get("requires_grad") is False
            and type(tensor.get("elements")) is int and tensor["elements"] == elements
            and type(tensor.get("storage_bytes")) is int
            and tensor["storage_bytes"] == elements * {"torch.int8": 1, "torch.float16": 2, "torch.float32": 4}[dtype],
            "Invalid tensor storage/dtype/device evidence")


def _quantization_state_bytes(evidence):
    """Extra float scale tensors (SCB) held by LLM.int8 modules; CB aliases the int8 weight."""
    total = 0
    for module in evidence.get("quantized_linear_modules") or []:
        for state in module.get("state_tensors", []):
            if state.get("name") == "state.SCB":
                total += state["storage_bytes"]
    return total


def summarize_treatment(loaded):
    feasibility, evidence = loaded["feasibility"], loaded["precision_evidence"]
    samples = feasibility["samples"]
    durations = [row["forward_seconds"] for row in samples]
    n = len(durations)
    median, p95 = statistics.median(durations), nearest_rank(durations, 0.95)
    # Regenerated values must agree with what the native run recorded.
    require(median == feasibility.get("median_forward_seconds"), "Recomputed median differs from recorded value")
    require(p95 == feasibility.get("p95_forward_seconds"), "Recomputed p95 differs from recorded value")
    slowest = max(samples, key=lambda row: row["forward_seconds"])
    memory, baseline = feasibility["memory"], feasibility["memory_baseline_after_warmup"]
    warmup_count = feasibility.get("warmup", {}).get("batches", 0)
    warmup_tokens = [row["effective_tokens"] for row in samples[:warmup_count]]
    parameter_bytes = sum(row["storage_bytes"] for row in evidence.get("parameters", []))
    bands = []
    for low, high in LENGTH_BANDS:
        inside = [row["forward_seconds"] for row in samples if low <= row["effective_tokens"] <= high]
        bands.append({"band": f"{low}-{high}", "n": len(inside),
                      "median_ms": statistics.median(inside) * 1000 if inside else None,
                      "max_ms": max(inside) * 1000 if inside else None})
    return {
        "n": n,
        "median_ms": median * 1000,
        "p95_ms": p95 * 1000,
        "mean_ms": statistics.fmean(durations) * 1000,
        "min_ms": min(durations) * 1000,
        "max_ms": slowest["forward_seconds"] * 1000,
        "max_sample": {"example_id": slowest["example_id"], "effective_tokens": slowest["effective_tokens"]},
        "sum_forward_seconds": math.fsum(durations),
        "derived_forward_only_rate_per_s": n / math.fsum(durations),
        "peak_allocated_mib": memory["peak_allocated_bytes"] / MIB,
        "peak_reserved_mib": memory["peak_reserved_bytes"] / MIB,
        "post_warmup_baseline_allocated_mib": baseline["allocated_bytes"] / MIB,
        "workload_increment_allocated_mib": (memory["peak_allocated_bytes"] - baseline["allocated_bytes"]) / MIB,
        "parameter_storage_mib": parameter_bytes / MIB,
        "quantization_scale_state_mib": _quantization_state_bytes(evidence) / MIB,
        "loading_seconds": feasibility.get("loading_seconds"),
        "warmup_tokens": warmup_tokens,
        "samples_longer_than_any_warmup": sum(row["effective_tokens"] > max(warmup_tokens, default=0)
                                             for row in samples),
        "length_bands": bands,
    }


def summarize(manifest_path):
    bundle = load_bundle(manifest_path)
    schedule = _check_matched(bundle)
    treatments = {precision: summarize_treatment(bundle[precision]) for precision in PRECISIONS}
    base = treatments["fp32"]
    ratios = {precision: {"median_latency_vs_fp32": t["median_ms"] / base["median_ms"],
                          "peak_allocated_vs_fp32": t["peak_allocated_mib"] / base["peak_allocated_mib"],
                          "derived_rate_vs_fp32": t["derived_forward_only_rate_per_s"]
                          / base["derived_forward_only_rate_per_s"]}
              for precision, t in treatments.items()}
    environment = bundle["fp32"]["environment"]
    first = bundle["fp32"]["feasibility"]
    return {
        "schema_version": 1,
        "scope": ("Offline regeneration of single-pass pilot resource observations; no model run. "
                  "Development feasibility only, not a final or controlled speed/memory benchmark."),
        "workload": {"examples": len(schedule), "batch_size": 1,
                     "effective_tokens_min": min(t for _, t in schedule),
                     "effective_tokens_median": statistics.median(t for _, t in schedule),
                     "effective_tokens_max": max(t for _, t in schedule),
                      "treatment_order": "not established by measurement manifests; consult native execution records"},
        "hardware": {"gpu": environment.get("gpu_name"), "allocation_id": environment.get("allocation_id"),
                     "cuda_runtime": environment.get("cuda_runtime"), "versions": environment.get("versions"),
                     "flags": environment.get("flags")},
        "boundaries": {"forward": first.get("forward_boundary"),
                       "memory": ("PyTorch max_memory_allocated/reserved after reset following warm-up; covers "
                                  "resident weights plus the post-warm-up input, forward and score-conversion "
                                  "allocations. Not total device, driver/context or host memory."),
                       "loading": first.get("loading_scope"),
                       "warmup": first.get("warmup"),
                       "p95": P95_DEFINITION, "rate": RATE_DEFINITION},
        "treatments": treatments,
        "ratios_vs_fp32": ratios,
        "samples": {precision: [{"example_id": row["example_id"], "effective_tokens": row["effective_tokens"],
                                 "forward_ms": row["forward_seconds"] * 1000}
                                for row in bundle[precision]["feasibility"]["samples"]]
                    for precision in PRECISIONS},
    }


def _fmt(value, digits=2):
    return "N/A" if value is None else f"{value:.{digits}f}"


def resource_rows(summary):
    rows = []
    for precision in PRECISIONS:
        t, r = summary["treatments"][precision], summary["ratios_vs_fp32"][precision]
        rows.append({"treatment": precision.upper(), "n": t["n"],
                     "median_forward_ms": _fmt(t["median_ms"]), "p95_forward_ms": _fmt(t["p95_ms"]),
                     "max_forward_ms": _fmt(t["max_ms"]),
                     "peak_allocated_mib": _fmt(t["peak_allocated_mib"]),
                     "parameter_storage_mib": _fmt(t["parameter_storage_mib"]),
                     "derived_forward_only_rate_per_s": _fmt(t["derived_forward_only_rate_per_s"], 2),
                     "loading_s": _fmt(t["loading_seconds"], 1),
                     "median_latency_vs_fp32": _fmt(r["median_latency_vs_fp32"]),
                     "peak_allocated_vs_fp32": _fmt(r["peak_allocated_vs_fp32"])})
    return rows


def _csv(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def band_rows(summary):
    rows = []
    for precision in PRECISIONS:
        for band in summary["treatments"][precision]["length_bands"]:
            rows.append({"treatment": precision.upper(), "effective_tokens": band["band"], "n": band["n"],
                         "median_forward_ms": _fmt(band["median_ms"]), "max_forward_ms": _fmt(band["max_ms"])})
    return rows


def markdown(summary):
    w, t = summary["workload"], summary["treatments"]
    lines = [
        "# Pilot resource summary (regenerated offline)", "",
        f"Scope: {summary['scope']}", "",
        f"Workload: {w['examples']} matched training examples, batch size 1, effective tokens "
        f"{w['effective_tokens_min']}-{w['effective_tokens_max']} (median {w['effective_tokens_median']}); "
        f"order {w['treatment_order']}. Hardware: {summary['hardware']['gpu']}, "
        f"CUDA {summary['hardware']['cuda_runtime']}.", "",
        "| Treatment | Median forward (ms) | p95 forward (ms) | Max forward (ms) | Peak allocated (MiB) "
        "| Parameter storage (MiB) | Derived forward-only rate (ex/s) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in resource_rows(summary):
        lines.append(f"| {row['treatment']} | {row['median_forward_ms']} | {row['p95_forward_ms']} | "
                     f"{row['max_forward_ms']} | {row['peak_allocated_mib']} | {row['parameter_storage_mib']} | "
                     f"{row['derived_forward_only_rate_per_s']} |")
    lines += ["", "Median forward time by effective-token band:", "",
              "| Treatment | " + " | ".join(f"{low}-{high} tokens" for low, high in LENGTH_BANDS) + " |",
              "|---|" + "---:|" * len(LENGTH_BANDS)]
    for precision in PRECISIONS:
        cells = [f"{_fmt(b['median_ms'])} (n={b['n']})" for b in t[precision]["length_bands"]]
        lines.append(f"| {precision.upper()} | " + " | ".join(cells) + " |")
    lines += ["", "Boundaries:", ""]
    for key, value in summary["boundaries"].items():
        lines.append(f"- **{key}**: {value if isinstance(value, str) else json.dumps(value, sort_keys=True)}")
    warm = t["fp32"]["warmup_tokens"]
    lines += ["", f"Warm-up inputs had {', '.join(map(str, warm))} tokens; "
              f"{t['fp32']['samples_longer_than_any_warmup']} of {w['examples']} timed samples are longer "
              "than any warm-up input.",
              "INT8 parameter storage excludes its "
              f"{_fmt(t['int8']['quantization_scale_state_mib'])} MiB of float32 LLM.int8 scale state (SCB).", ""]
    return "\n".join(lines)


# Reference categorical slots 1-3 (blue, orange, aqua); validated for all-pairs use.
SERIES = {"fp32": ("#2a78d6", "o"), "fp16": ("#eb6834", "s"), "int8": ("#1baf7a", "^")}


def write_figure(summary, directory):
    """Latency versus effective tokens (log y). Returns written paths, or [] without matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        matplotlib.rcParams["svg.hashsalt"] = "precision-benchmark-resource"  # deterministic SVG IDs
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    except ImportError:
        return []
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=200)
    warm_max = max(summary["treatments"]["fp32"]["warmup_tokens"])
    ax.axvspan(1, warm_max, color="#d9d8d3", alpha=0.45, linewidth=0, zorder=0)
    warm = ", ".join(map(str, summary["treatments"]["fp32"]["warmup_tokens"]))
    ax.text(8, 17, f"up to longest warm-up input\n(warm-up lengths {warm} tokens)", fontsize=6.5,
            color="#52514e", va="bottom")
    medians = {p: summary["treatments"][p]["median_ms"] for p in PRECISIONS}
    # Nudge labels whose medians nearly coincide (multiplicative offsets on the log axis).
    label_y = dict(medians)
    if abs(math.log(medians["fp16"] / medians["fp32"])) < 0.12:
        low, high = sorted(("fp32", "fp16"), key=medians.get)
        label_y[low], label_y[high] = medians[low] / 1.07, medians[high] * 1.07
    for precision in PRECISIONS:
        color, marker = SERIES[precision]
        rows = summary["samples"][precision]
        ax.scatter([r["effective_tokens"] for r in rows], [r["forward_ms"] for r in rows], s=14, marker=marker,
                   facecolor=color, edgecolor="white", linewidth=0.6, label=precision.upper(), zorder=3)
        med = medians[precision]
        ax.axhline(med, color=color, linewidth=1, linestyle="--", zorder=2)
        ax.text(1150, label_y[precision], f"{precision.upper()} median {med:.1f} ms", fontsize=7,
                color="#0b0b0b", va="center", ha="left")
    ax.set_xscale("log")
    ax.set_yscale("log")
    points = [row for rows in summary["samples"].values() for row in rows]
    ax.set_xlim(min(7, min(r["effective_tokens"] for r in points) * 0.8),
                max(1100, max(r["effective_tokens"] for r in points) * 1.05))
    ax.set_ylim(min(15, min(r["forward_ms"] for r in points) * 0.8),
                max(600, max(r["forward_ms"] for r in points) * 1.1))
    ax.yaxis.set_major_locator(FixedLocator([20, 50, 100, 200, 500]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_locator(FixedLocator([10, 30, 100, 300, 1024]))
    ax.xaxis.set_minor_locator(NullLocator())
    plain = FuncFormatter(lambda v, _: f"{v:g}")
    ax.yaxis.set_major_formatter(plain)
    ax.xaxis.set_major_formatter(plain)
    ax.set_xlabel("Effective input tokens (log scale)", fontsize=8, color="#52514e")
    ax.set_ylabel("Synchronized forward time, ms (log)", fontsize=8, color="#52514e")
    ax.tick_params(labelsize=7, colors="#52514e", length=0)
    ax.grid(True, color="#e6e5e0", linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#c3c2b7")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=7, frameon=False, ncol=3,
              handletextpad=0.3, columnspacing=1.2, borderaxespad=0.2)
    gpu = summary["hardware"]["gpu"].removeprefix("NVIDIA ")
    fig.suptitle(f"Per-example forward time, {summary['workload']['examples']} matched pilot inputs, "
                 f"batch {summary['workload']['batch_size']}, one {gpu}", fontsize=8.5,
                 x=0.1, ha="left", color="#0b0b0b")
    fig.subplots_adjust(left=0.1, right=0.76, top=0.84, bottom=0.14)
    paths = []
    for suffix in ("png", "svg"):
        path = Path(directory) / f"latency_vs_tokens.{suffix}"
        fig.savefig(path, metadata={"Date": None} if suffix == "svg" else None)
        paths.append(path)
    plt.close(fig)
    return paths


def write_outputs(summary, output, figure=True):
    output = Path(output)
    require(not output.exists(), "Output directory already exists; preserve earlier summaries")
    output.mkdir(parents=True)
    pilot_inference.write_json(output / "resource_summary.json", summary)
    for name, text in (("resource.csv", _csv(resource_rows(summary))),
                       ("resource_by_length.csv", _csv(band_rows(summary))),
                       ("resource.md", markdown(summary))):
        (output / name).write_text(text, encoding="utf-8", newline="\n")
    if figure:
        write_figure(summary, output)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description="Regenerate the pilot resource table from retained raw samples.")
    parser.add_argument("--manifest", required=True, type=Path, help="comparison.json binding the three runs")
    parser.add_argument("--output", required=True, type=Path, help="New output directory")
    parser.add_argument("--no-figure", action="store_true", help="Skip the optional matplotlib figure")
    args = parser.parse_args(argv)
    try:
        summary = summarize(args.manifest)
        path = write_outputs(summary, args.output, figure=not args.no_figure)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Resource summary failed: {error}", file=sys.stderr)
        return 2
    print(f"Resource summary written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
