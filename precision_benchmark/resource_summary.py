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

from . import pilot_inference

PRECISIONS = ("fp32", "fp16", "int8")
MIB = 2 ** 20
# Effective-token bands used for the shape breakdown (inclusive upper bounds).
LENGTH_BANDS = ((1, 128), (129, 512), (513, 1024))
RATE_DEFINITION = ("Derived forward-only rate = number of samples / sum of their synchronized forward "
                   "durations. Not a measured wall-clock, sustained or end-to-end throughput; "
                   "not 1 / median latency.")
P95_DEFINITION = "Nearest rank: sorted[ceil(0.95 * n) - 1]; median is the conventional median."


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
    return json.loads(Path(path).read_bytes(), parse_constant=bad_constant)


def _verified(path, expected_sha256, label):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"{label} is missing or not a regular file")
    require(pilot_inference.file_hash(path) == expected_sha256, f"{label} hash does not match its manifest")
    return _load_json(path)


def _finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def load_bundle(manifest_path):
    """Return {precision: {run, feasibility, environment, precision_evidence}} after hash checks."""
    manifest_path = Path(manifest_path)
    manifest = _load_json(manifest_path)
    base = manifest_path.parent
    runs = manifest.get("runs")
    require(isinstance(runs, list) and len(runs) == len(PRECISIONS), "Manifest must reference exactly three runs")
    bundle = {}
    for entry in runs:
        require(isinstance(entry, dict) and not Path(entry.get("path", "/")).is_absolute(),
                "Run references must be relative")
        run_path = base / entry["path"]
        run = _verified(run_path, entry.get("sha256"), "run.json")
        precision = run.get("precision")
        require(precision in PRECISIONS and precision not in bundle, "Unexpected or duplicate precision")
        require(run.get("status") == "complete", f"{precision} run is not complete")
        hashes = run.get("artifact_sha256", {})
        loaded = {"run": run}
        for name, key in (("feasibility.json", "feasibility"), ("environment.json", "environment"),
                          ("precision-evidence.json", "precision_evidence")):
            loaded[key] = _verified(run_path.parent / name, hashes.get(name), f"{precision} {name}")
        bundle[precision] = loaded
    require(set(bundle) == set(PRECISIONS), "Bundle lacks one of fp32/fp16/int8")
    return bundle


def _check_matched(bundle):
    """All treatments must time the same examples, token lengths and order on one device."""
    reference = None
    for precision in PRECISIONS:
        samples = bundle[precision]["feasibility"].get("samples")
        require(isinstance(samples, list) and samples, f"{precision} has no raw samples")
        for row in samples:
            require(row.get("batch_size") == 1, "Only batch-size-one samples are supported")
            require(type(row.get("effective_tokens")) is int and row["effective_tokens"] > 0,
                    "Invalid effective token count")
            require(_finite_positive(row.get("forward_seconds")), "Invalid forward duration")
        schedule = [(row["example_id"], row["effective_tokens"]) for row in samples]
        require(len({sid for sid, _ in schedule}) == len(schedule), f"{precision} repeats an example ID")
        if reference is None:
            reference = schedule
        require(schedule == reference, "Treatments did not time the same examples/lengths in the same order")
    devices = {(bundle[p]["environment"].get("gpu_uuid"), bundle[p]["environment"].get("allocation_id"))
               for p in PRECISIONS}
    require(len(devices) == 1, "Treatments ran on different devices or allocations")
    return reference


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
                     "treatment_order": "fp32, fp16, int8 (fixed, separate fresh processes, same allocation)"},
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
    ax.set_xlim(7, 1100)
    ax.set_ylim(15, 600)
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
    fig.suptitle("Per-example forward time, 128 matched pilot inputs, batch 1, one L40S", fontsize=8.5,
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
