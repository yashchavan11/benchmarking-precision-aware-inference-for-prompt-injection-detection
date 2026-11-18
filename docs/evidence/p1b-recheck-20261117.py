"""Fresh stdlib-only recheck: no project metric imports, prior-review reliance or model run."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import csv
import hashlib
import json
import math
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "docs/evidence/p1b-pilot-20261117"
OUT = Path(__file__).with_suffix(".json")
METRIC_TOL, SOFTMAX_TOL = 1e-12, 1e-7
CHECKS, HASHES, EXTERNAL = [], [], []


def check(name, condition):
    CHECKS.append({"check": name, "passed": bool(condition)})
    if not condition:
        raise AssertionError(name)


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def bad_constant(_):
    raise ValueError("Nonfinite JSON constant")


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)


def read(name):
    return parse((B / name).read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def hashed(path, expected, context):
    raw = path.read_bytes()
    check("SHA256 " + context, sha(raw) == expected)
    HASHES.append({"context": context, "sha256": sha(raw), "bytes": len(raw)})
    return raw


def jsonl(path):
    result = [parse(line) for line in path.read_bytes().splitlines()]
    check("Unique IDs " + path.name, len({r["example_id"] for r in result}) == len(result))
    return result


def close(a, b):
    return a is b if a is None or b is None else math.isclose(float(a), float(b), abs_tol=METRIC_TOL, rel_tol=0)


def same(a, b, name):
    if isinstance(a, dict):
        check(name + " keys", set(a) == set(b))
        for key in a:
            same(a[key], b[key], name + "/" + str(key))
    elif isinstance(a, list):
        check(name + " length", len(a) == len(b))
        for i, (left, right) in enumerate(zip(a, b)):
            same(left, right, name + "/" + str(i))
    elif isinstance(a, (str, bool)):
        check(name, a == b and type(a) is type(b))
    elif type(a) is int:
        check(name, a == b)
    else:
        check(name, close(a, b))


def metrics(labels, scores, threshold):
    n = len(labels)
    cells = Counter((y, int(p >= threshold)) for y, p in zip(labels, scores))
    tn, fp, fn, tp = [cells[k] for k in ((0, 0), (0, 1), (1, 0), (1, 1))]
    div = lambda x, y: x / y if y else None
    f1p, f1n = div(2 * tp, 2 * tp + fp + fn), div(2 * tn, 2 * tn + fp + fn)
    pos = [p for y, p in zip(labels, scores) if y == 1]
    neg = [p for y, p in zip(labels, scores) if y == 0]
    wins = sum(p > q for p in pos for q in neg)
    ties = sum(p == q for p in pos for q in neg)
    pairs = len(pos) * len(neg)
    auc = float(Fraction(2 * wins + ties, 2 * pairs)) if pairs else None
    bins, terms = [], []
    for i in range(10):
        lo, hi = i / 10, (i + 1) / 10
        selected = [(y, p) for y, p in zip(labels, scores) if lo <= p and (p < hi or i == 9 and p <= hi)]
        count = len(selected)
        average = math.fsum(p for _, p in selected) / count if count else None
        frequency = sum(y for y, _ in selected) / count if count else None
        bins.append({"lower": lo, "upper": hi, "count": count, "mean_score": average, "fraction_positive": frequency})
        terms.append(count / n * abs(average - frequency) if count else 0)
    check("Independent calibration coverage", sum(v["count"] for v in bins) == n)
    values = {"n": n, "benign_support": len(neg), "injection_support": len(pos),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp, "accuracy": (tn + tp) / n,
        "macro_f1": (f1p + f1n) / 2 if f1p is not None and f1n is not None else None,
        "injection_precision": div(tp, tp + fp), "injection_recall": div(tp, tp + fn), "injection_f1": f1p,
        "benign_precision": div(tn, tn + fn), "benign_recall": div(tn, tn + fp), "benign_f1": f1n,
        "fpr": div(fp, fp + tn), "fnr": div(fn, fn + tp), "roc_auc": auc,
        "brier": math.fsum((p - y) ** 2 for y, p in zip(labels, scores)) / n,
        "ece_10_equal_width": math.fsum(terms), "calibration_bins": bins}
    return values, {"positive_negative_pairs": pairs, "wins": wins, "ties": ties, "losses": pairs - wins - ties}


def run():
    inventory = read("inventory.json")
    members = inventory["members"]
    actual = {p.relative_to(B).as_posix() for p in B.rglob("*") if p.is_file() and p.name != "inventory.json"}
    check("Complete portable inventory", set(members) == actual)
    for name, record in members.items():
        check("Inventory size " + name, len(hashed(B / name, record["sha256"], "inventory/" + name)) == record["bytes"])
    check("Inventory total bytes", sum(r["bytes"] for r in members.values()) == inventory["total_bytes"])

    receipt, stage = read("executed-source-receipt.json"), read("executed-source-manifest.json")
    hashed(B / "executed-source-stage.zip", receipt["archive_sha256"], "source archive receipt")
    hashed(B / "executed-source-manifest.json", receipt["stage_manifest_sha256"], "source manifest receipt")
    check("Archive byte count", (B / "executed-source-stage.zip").stat().st_size == receipt["archive_bytes"])
    archive = {}
    with zipfile.ZipFile(B / "executed-source-stage.zip") as z:
        names = {"project/" + name for name in stage["files"]} | {"project/stage-manifest.json"}
        check("Exact ZIP member inventory", set(z.namelist()) == names and len(z.namelist()) == len(names))
        for name, record in stage["files"].items():
            check("ZIP member size " + name, z.getinfo("project/" + name).file_size == record["bytes"])
            archive[name] = z.read("project/" + name)
            check("ZIP member SHA256 " + name, sha(archive[name]) == record["sha256"])
        check("Embedded stage manifest", z.read("project/stage-manifest.json") == (B / "executed-source-manifest.json").read_bytes())
    check("ZIP receipt counts", len(archive) == receipt["files"] and sum(r["bytes"] for r in stage["files"].values()) == stage["total_bytes"] == receipt["uncompressed_bytes"])

    def references(value, owner, pointer=""):
        if isinstance(value, dict):
            if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                relative = value["path"].replace("\\", "/")
                candidate = (ROOT / relative if relative.startswith("docs/evidence/p1b-pilot-20261117/") else owner.parent / relative).resolve()
                if candidate.is_relative_to(B.resolve()) and candidate.is_file():
                    hashed(candidate, value["sha256"], owner.relative_to(B).as_posix() + pointer)
                else:
                    EXTERNAL.append({"owner": owner.relative_to(B).as_posix(), "pointer": pointer, "path": relative,
                                     "disposition": "Out-of-bundle provenance reference, not opened"})
            for key, item in value.items():
                references(item, owner, pointer + "/" + str(key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                references(item, owner, pointer + "/" + str(index))
    for path in B.rglob("*.json"):
        references(parse(path.read_bytes()), path)

    comparison, pilot, saved = read("comparison.json"), read("pilot/manifest.json"), read("analysis/results.json")
    examples = jsonl(B / comparison["examples"]["path"])
    ids, labels = [r["example_id"] for r in examples], [r["label"] for r in examples]
    check("128 reference rows and balanced labels", len(ids) == 128 and Counter(labels) == {0: 64, 1: 64})
    check("Only original training lineage", all(r["source_split"] == "train" and r["data_role"] == "eligible_training"
        and type(r["label"]) is int and type(r["source_row"]) is int
        and r["example_id"] == f'{pilot["dataset_revision"]}:train:{r["source_row"]}' for r in examples))
    check("Ordered selected IDs", ids == pilot["selected_ids"] and [r["source_row"] for r in examples] == sorted(r["source_row"] for r in examples))
    idhash = lambda values: sha("".join(v + "\n" for v in values).encode())
    check("Pilot membership hashes", idhash(ids) == pilot["ordered_id_sha256"] and idhash(sorted(ids)) == pilot["membership_sha256"])
    check("Pilot planned schedule digest", "sha256:" + sha(canonical(pilot["input_schedule"])) == pilot["input_schedule_id"])
    check("Pilot preprocessing digest", "sha256:" + sha(canonical(pilot["preprocessing_contract"])) == pilot["preprocessing_id"])
    check("Provisional scope", comparison["threshold"] == pilot["threshold"] == 0.5 and pilot["cap"] == 1024 and pilot["batch_size"] == 1 and pilot["main_study_freeze"] is False)
    check("Lengths/truncation", all(type(r["original_tokens"]) is int and r["original_tokens"] > 0
        and r["effective_tokens"] == min(r["original_tokens"], 1024) and r["truncated"] is (r["original_tokens"] > 1024) for r in examples))
    for label in (0, 1):
        group = [r for r in examples if r["label"] == label]
        check("Class/length quotas " + str(label), [sum(r["original_tokens"] <= 512 for r in group),
              sum(513 <= r["original_tokens"] <= 1024 for r in group), sum(r["original_tokens"] > 1024 for r in group)] == [48, 8, 8])
    check("16 truncated examples", sum(r["truncated"] for r in examples) == 16)

    runs, predictions, quality, auc_counts, softmax_errors = {}, {}, {}, {}, {}
    common = ("data_role", "population_id", "dataset_revision", "model_revision", "tokenizer_revision",
        "preprocessing_id", "input_schedule_id", "planned_input_schedule_id", "token_schedule_sha256",
        "environment_id", "code_revision", "threshold", "threshold_source", "score_semantics",
        "checkpoint", "source_sha256", "tokenizer_runtime")
    for reference in comparison["runs"]:
        path = B / reference["path"]
        record = parse(hashed(path, reference["sha256"], "comparison/" + reference["path"]))
        mode = record["precision"]
        check("Unique precision " + mode, mode in ("fp32", "fp16", "int8") and mode not in runs)
        runs[mode] = record
        check("Complete run " + mode, record["status"] == "complete" and record["expected_rows"] == record["observed_rows"] == 128 and record["test_performance_released"] is False)
        for key in ("data_role", "population_id", "threshold", "threshold_source"):
            check("Comparison agreement " + mode + "/" + key, record[key] == comparison[key])
        for key in ("dataset_revision", "model_revision", "tokenizer_revision", "preprocessing_id", "score_semantics"):
            check("Pilot agreement " + mode + "/" + key, record[key] == pilot[key])
        check("Pilot-byte binding " + mode, record["pilot_manifest_sha256"] == sha((B / "pilot/manifest.json").read_bytes()))
        check("Planned schedule binding " + mode, record["planned_input_schedule_id"] == pilot["input_schedule_id"])
        schedule = {"planned_schedule": pilot["input_schedule_id"], "token_schedule_sha256": record["token_schedule_sha256"]}
        check("Effective schedule composition " + mode, record["input_schedule_id"] == "sha256:" + sha(canonical(schedule)))
        for name, expected in record["artifact_sha256"].items():
            hashed(path.parent / name, expected, mode + "/artifact/" + name)
        name, expected = record["precision_evidence"].split("#sha256=")
        hashed(path.parent / name, expected, mode + "/precision-evidence")
        environment = parse((path.parent / "environment.json").read_bytes())
        check("Environment ID " + mode, record["environment_id"] == "sha256:" + sha(canonical(environment)))
        for name, expected in record["source_sha256"].items():
            check("Executed source " + mode + "/" + name, name in archive and sha(archive[name]) == expected)
        check("Code identity " + mode, record["code_revision"] == "sha256:" + sha(canonical(record["source_sha256"])))
        execution = parse((path.parent / "execution.json").read_bytes())
        check("Execution completion " + mode, execution["status"] == "complete"
            and execution["completed_rows"] == execution["expected_rows"] == 128
            and execution["run_id"] == record["run_id"] and execution["precision"] == mode
            and execution["test_performance_released"] is False)
        prediction_path = path.parent / record["predictions"]["path"]
        hashed(prediction_path, record["predictions"]["sha256"], mode + "/predictions")
        original = jsonl(prediction_path)
        mapping = {r["example_id"]: r for r in original}
        check("Exact prediction coverage " + mode, set(mapping) == set(ids) and len(original) == 128)
        ordered = [mapping[example_id] for example_id in ids]
        predictions[mode] = ordered
        differences = []
        for row in ordered:
            check("Finite scalar/logit contract " + mode, row["run_id"] == record["run_id"]
                and type(row["prediction"]) is int and row["prediction"] in (0, 1)
                and type(row["score"]) in (int, float) and math.isfinite(row["score"]) and 0 <= row["score"] <= 1
                and isinstance(row["logits"], list) and len(row["logits"]) == 2
                and all(type(v) in (int, float) and math.isfinite(v) for v in row["logits"]))
            check("Threshold convention " + mode, row["prediction"] == int(row["score"] >= comparison["threshold"]))
            z0, z1 = row["logits"]
            maximum = max(z0, z1)
            p0, p1 = math.exp(z0 - maximum), math.exp(z1 - maximum)
            differences.append(abs(p1 / (p0 + p1) - row["score"]))
        softmax_errors[mode] = max(differences)
        check("Independent double/float32 softmax agreement " + mode, max(differences) <= SOFTMAX_TOL)
        quality[mode], auc_counts[mode] = metrics(labels, [r["score"] for r in ordered], comparison["threshold"])
        same(quality[mode], saved["quality"][mode], "quality/" + mode)
        for group, flag in (("untruncated", False), ("truncated", True)):
            selected = [i for i, example in enumerate(examples) if example["truncated"] is flag]
            calculated, _ = metrics([labels[i] for i in selected], [ordered[i]["score"] for i in selected], comparison["threshold"])
            same(calculated, saved["truncation_subgroups"][mode][group], "subgroup/" + mode + "/" + group)
    check("All three modes", set(runs) == {"fp32", "fp16", "int8"})
    for mode in ("fp16", "int8"):
        for key in common:
            check("Matched configuration " + mode + "/" + key, runs[mode][key] == runs["fp32"][key])

    paired, errors, changed = {}, [], []
    for mode in ("fp16", "int8"):
        counts, deltas = Counter(), []
        for index, (example, baseline, candidate) in enumerate(zip(examples, predictions["fp32"], predictions[mode])):
            y = example["label"]
            a, b = baseline["prediction"] == y, candidate["prediction"] == y
            outcome = "both_correct" if a and b else "introduced_errors" if a else "corrected_errors" if b else "both_wrong"
            counts[outcome] += 1
            counts["disagreements"] += baseline["prediction"] != candidate["prediction"]
            delta = candidate["score"] - baseline["score"]
            deltas.append(delta)
            if outcome != "both_correct":
                errors.append({"precision": mode, "example_id": example["example_id"], "label": y, "outcome": outcome,
                    "fp32_score": baseline["score"], "candidate_score": candidate["score"],
                    "fp32_prediction": baseline["prediction"], "candidate_prediction": candidate["prediction"],
                    "score_delta": delta, "fp32_threshold_distance": abs(baseline["score"] - comparison["threshold"]),
                    "candidate_threshold_distance": abs(candidate["score"] - comparison["threshold"]),
                    **{key: example[key] for key in ("original_tokens", "effective_tokens", "truncated")}})
            if baseline["prediction"] != candidate["prediction"]:
                values = {}
                for precision in predictions:
                    row = predictions[precision][index]
                    values[precision] = {**row, "injection_logit_margin": row["logits"][1] - row["logits"][0]}
                changed.append({"candidate": mode, "example_id": example["example_id"], "source_row": example["source_row"],
                    "label": y, "original_tokens": example["original_tokens"], "effective_tokens": example["effective_tokens"],
                    "truncated": example["truncated"], "outcome": outcome, "score_change": delta, "values": values})
        pair = {"n": 128, **{key: counts[key] for key in ("both_correct", "introduced_errors", "corrected_errors", "both_wrong", "disagreements")},
            "disagreement_rate": counts["disagreements"] / 128,
            "accuracy_delta_pp": 100 * (counts["corrected_errors"] - counts["introduced_errors"]) / 128,
            "mean_score_delta": math.fsum(deltas) / 128, "mean_absolute_score_delta": math.fsum(map(abs, deltas)) / 128,
            "max_absolute_score_delta": max(map(abs, deltas))}
        same(pair, saved["paired_vs_fp32"][mode], "paired/" + mode)
        paired[mode] = pair
    keyed = lambda values: {(r["precision"], r["example_id"]): r for r in values}
    expected_errors, actual_errors = keyed(errors), keyed(saved["errors"])
    check("Unique complete error records", len(saved["errors"]) == len(expected_errors) and set(actual_errors) == set(expected_errors))
    for key in expected_errors:
        same(expected_errors[key], actual_errors[key], "error/" + key[0] + "/" + key[1])

    for filename, calculated in (("quality.csv", quality), ("paired.csv", paired)):
        with (B / "analysis" / filename).open(encoding="utf-8", newline="") as stream:
            csv_rows = list(csv.DictReader(stream))
        check("CSV treatment coverage " + filename, len(csv_rows) == len(calculated) and {r["precision"] for r in csv_rows} == set(calculated))
        for row in csv_rows:
            for key, value in row.items():
                if key != "precision":
                    check("CSV numeric " + filename + "/" + row["precision"] + "/" + key, close(float(value) if value else None, calculated[row["precision"]][key]))
    with (B / "analysis/error_analysis.csv").open(encoding="utf-8", newline="") as stream:
        csv_errors = list(csv.DictReader(stream))
    check("Error CSV complete unique keys", len(csv_errors) == len(errors) and set(keyed(csv_errors)) == set(expected_errors))
    for row in csv_errors:
        expected = expected_errors[(row["precision"], row["example_id"])]
        for key, value in row.items():
            if isinstance(expected[key], bool):
                check("Error CSV bool", value.lower() == str(expected[key]).lower())
            elif isinstance(expected[key], str):
                check("Error CSV text field", value == expected[key])
            else:
                check("Error CSV numeric", close(float(value), expected[key]))
    for name, expected in saved["source_sha256"].items():
        path = B / "comparison.json" if name == "manifest" else ROOT / name.replace("\\", "/")
        check("Analysis artifact reference in bundle", path.resolve().is_relative_to(B.resolve()))
        hashed(path, expected, "analysis source map/" + name)
    for name, expected in saved["analysis_sha256"].items():
        key = "precision_benchmark/" + name
        raw = archive[key] if key in archive else (ROOT / key).read_bytes()
        check("Analysis source hash " + name, sha(raw) == expected)
    for name, expected in pilot["code_sha256"].items():
        check("Pilot source in executed archive " + name, name in archive and sha(archive[name]) == expected)

    ranking = {}
    pos, neg = [i for i, y in enumerate(labels) if y], [i for i, y in enumerate(labels) if not y]
    credit = lambda p, n: 1.0 if p > n else .5 if p == n else 0.0
    for mode in ("fp16", "int8"):
        changes = [credit(predictions[mode][p]["score"], predictions[mode][n]["score"])
            - credit(predictions["fp32"][p]["score"], predictions["fp32"][n]["score"]) for p in pos for n in neg]
        ranking[mode] = {"pair_count": len(changes), "pairs_with_changed_credit": sum(v != 0 for v in changes),
            "gained_pair_credit": math.fsum(max(v, 0) for v in changes), "lost_pair_credit": math.fsum(max(-v, 0) for v in changes),
            "net_pair_credit": math.fsum(changes), "auc_delta": math.fsum(changes) / len(changes)}
        check("Pair credits explain AUC delta " + mode, close(ranking[mode]["auc_delta"], quality[mode]["roc_auc"] - quality["fp32"]["roc_auc"]))
    return {"status": "passed", "inventory_members_verified": len(members), "executed_archive_members_verified": len(archive),
        "prediction_rows_checked": sum(map(len, predictions.values())), "quality": quality, "auc_pair_counts": auc_counts,
        "paired_vs_fp32": paired, "ranking_changes_vs_fp32": ranking, "changed_examples": changed,
        "max_softmax_absolute_errors": softmax_errors, "metric_absolute_tolerance": METRIC_TOL,
        "softmax_absolute_tolerance": SOFTMAX_TOL, "matched_fields": list(common),
        "out_of_bundle_references_not_opened": EXTERNAL,
        "limits": ["All declared bundle-local artifact references and inventory/archive hashes checked; inventory is not an independent signature of truth.",
                   "Out-of-bundle raw/model/tokenizer files, dependency wheels/native binaries and hidden actual token vectors were not reread or recomputed.",
                   "Matched declared configurations do not independently prove native kernel/dtype behavior; this is saved-artifact arithmetic.",
                   "Reference annotation truth, pretrained contamination and real-world representativeness are not established.",
                   "No project metric function, prior-review calculation, model, raw prompt, official-test data or network was used."]}


if __name__ == "__main__":
    if OUT.exists():
        raise SystemExit("Existing arithmetic evidence must be preserved")
    result = {"status": "incomplete"}
    try:
        result = run()
    except Exception as error:
        result.update({"status": "failed", "failure_type": type(error).__name__, "failure": str(error)})
    result.update({"date_utc": datetime.now(timezone.utc).isoformat(), "script_sha256": sha(Path(__file__).read_bytes()),
                   "checks": CHECKS, "hash_checks": HASHES})
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "checks": len(CHECKS), "hash_checks": len(HASHES),
                      "failure": result.get("failure"), "output": OUT.relative_to(ROOT).as_posix()}))
    raise SystemExit(0 if result["status"] == "passed" else 1)
