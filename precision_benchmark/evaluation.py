"""Binary metrics; injection is class 1 and score >= threshold is positive."""

import math
from itertools import groupby


def probability(value, name="score"):
    if type(value) not in (int, float) or not 0 <= value <= 1 or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return value


def binary(value, name="label"):
    if type(value) is not int or value not in (0, 1):
        raise ValueError(f"{name} must be integer 0 or 1")
    return value


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def roc_auc(labels, scores):
    """Mann-Whitney AUC with half credit for tied positive/negative pairs."""
    negatives_seen = 0
    wins = 0.0
    for _, group in groupby(sorted(zip(scores, labels)), key=lambda item: item[0]):
        group_labels = [label for _, label in group]
        positives = sum(group_labels)
        negatives = len(group_labels) - positives
        wins += positives * (negatives_seen + 0.5 * negatives)
        negatives_seen += negatives
    return ratio(wins, sum(labels) * (len(labels) - sum(labels)))


def metrics(labels, scores, threshold):
    labels, scores = list(labels), list(scores)
    if not labels or len(labels) != len(scores):
        raise ValueError("labels and scores must have the same nonzero length")
    probability(threshold, "threshold")
    for label in labels:
        binary(label)
    for score in scores:
        probability(score)
    predicted = [int(score >= threshold) for score in scores]
    tp = sum(y == p == 1 for y, p in zip(labels, predicted))
    tn = sum(y == p == 0 for y, p in zip(labels, predicted))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predicted))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predicted))
    positive_f1 = ratio(2 * tp, 2 * tp + fp + fn)
    negative_f1 = ratio(2 * tn, 2 * tn + fp + fn)
    bins = [[] for _ in range(10)]
    for label, score in zip(labels, scores):
        bins[min(int(score * 10), 9)].append((label, score))
    calibration = []
    ece = 0.0
    for index, bucket in enumerate(bins):
        count = len(bucket)
        mean_score = ratio(sum(score for _, score in bucket), count)
        fraction_positive = ratio(sum(label for label, _ in bucket), count)
        if count:
            ece += count / len(labels) * abs(mean_score - fraction_positive)
        calibration.append({"lower": index / 10, "upper": (index + 1) / 10,
                            "count": count, "mean_score": mean_score,
                            "fraction_positive": fraction_positive})
    return {
        "n": len(labels), "benign_support": tn + fp, "injection_support": tp + fn,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        "accuracy": (tp + tn) / len(labels),
        "macro_f1": ((positive_f1 + negative_f1) / 2
                     if positive_f1 is not None and negative_f1 is not None else None),
        "injection_precision": ratio(tp, tp + fp),
        "injection_recall": ratio(tp, tp + fn), "injection_f1": positive_f1,
        "benign_precision": ratio(tn, tn + fn), "benign_recall": ratio(tn, tn + fp),
        "benign_f1": negative_f1, "fpr": ratio(fp, fp + tn), "fnr": ratio(fn, fn + tp),
        "roc_auc": roc_auc(labels, scores),
        "brier": sum((score - label) ** 2 for label, score in zip(labels, scores)) / len(labels),
        "ece_10_equal_width": ece, "calibration_bins": calibration,
    }


def compare(examples, reference, candidate, threshold):
    """Pair by ID. Corrected/introduced errors describe candidate versus reference."""
    if not examples or set(examples) != set(reference) or set(examples) != set(candidate):
        raise ValueError("paired comparison requires identical nonempty ID coverage")
    probability(threshold, "threshold")
    counts = dict(both_correct=0, introduced_errors=0, corrected_errors=0, both_wrong=0)
    errors = []
    shifts = []
    disagreements = 0
    for example_id in sorted(examples):
        row = examples[example_id]
        label = binary(row["label"])
        high = probability(reference[example_id])
        low = probability(candidate[example_id])
        high_label, low_label = int(high >= threshold), int(low >= threshold)
        high_correct, low_correct = high_label == label, low_label == label
        outcome = ("both_correct" if high_correct and low_correct else
                   "introduced_errors" if high_correct else
                   "corrected_errors" if low_correct else "both_wrong")
        counts[outcome] += 1
        disagreements += high_label != low_label
        shifts.append(low - high)
        if outcome != "both_correct":
            errors.append({"example_id": example_id, "label": label, "outcome": outcome,
                           "fp32_score": high, "candidate_score": low,
                           "fp32_prediction": high_label, "candidate_prediction": low_label,
                           "score_delta": low - high,
                           "fp32_threshold_distance": abs(high - threshold),
                           "candidate_threshold_distance": abs(low - threshold),
                           "original_tokens": row.get("original_tokens"),
                           "effective_tokens": row.get("effective_tokens"),
                           "truncated": row.get("truncated")})
    n = len(examples)
    return {"n": n, **counts, "disagreements": disagreements,
            "disagreement_rate": disagreements / n,
            "accuracy_delta_pp": 100 * (counts["corrected_errors"] - counts["introduced_errors"]) / n,
            "mean_score_delta": sum(shifts) / n,
            "mean_absolute_score_delta": sum(abs(shift) for shift in shifts) / n,
            "max_absolute_score_delta": max(abs(shift) for shift in shifts)}, errors
