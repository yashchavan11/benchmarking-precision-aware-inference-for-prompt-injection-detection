import itertools
import unittest

from precision_benchmark.evaluation import compare, metrics


class MetricsTests(unittest.TestCase):
    def test_hand_calculated_confusion_and_metrics(self):
        result = metrics([0, 0, 0, 1, 1, 1], [.1, .2, .9, .8, .7, .3], .5)
        self.assertEqual([result[k] for k in ("tn", "fp", "fn", "tp")], [2, 1, 1, 2])
        for key in ("accuracy", "macro_f1", "injection_precision", "injection_recall", "roc_auc"):
            self.assertAlmostEqual(result[key], 2 / 3)
        self.assertAlmostEqual(result["fpr"], 1 / 3)
        self.assertAlmostEqual(result["fnr"], 1 / 3)
        self.assertAlmostEqual(result["brier"], (.01 + .04 + .81 + .04 + .09 + .49) / 6)

    def test_auc_against_pairwise_reference_including_ties(self):
        labels = [0, 1, 0, 1]
        for scores in itertools.product([0, .5, 1], repeat=4):
            wins = sum((scores[p] > scores[n]) + .5 * (scores[p] == scores[n])
                       for p in (1, 3) for n in (0, 2))
            self.assertEqual(metrics(labels, scores, .5)["roc_auc"], wins / 4)

    def test_threshold_tie_and_calibration(self):
        result = metrics([0, 1], [.5, .5], .5)
        self.assertEqual((result["fp"], result["tp"]), (1, 1))
        self.assertAlmostEqual(result["macro_f1"], 1 / 3)
        self.assertEqual(result["roc_auc"], .5)
        self.assertEqual(result["brier"], .25)
        self.assertEqual(result["ece_10_equal_width"], 0)
        self.assertEqual(result["calibration_bins"][5]["count"], 2)
        endpoints = metrics([0, 1], [0, 1], .5)
        self.assertEqual(endpoints["calibration_bins"][0]["count"], 1)
        self.assertEqual(endpoints["calibration_bins"][9]["count"], 1)
        self.assertIsNone(endpoints["calibration_bins"][1]["mean_score"])
        self.assertEqual(endpoints["brier"], 0)
        self.assertEqual(endpoints["ece_10_equal_width"], 0)
        self.assertAlmostEqual(metrics([0, 1], [.1, .8], .5)["ece_10_equal_width"], .15)

    def test_undefined_metrics_are_not_perfect_scores(self):
        result = metrics([0, 0], [.1, .2], .5)
        for key in ("injection_precision", "injection_recall", "injection_f1", "macro_f1", "roc_auc", "fnr"):
            self.assertIsNone(result[key], key)
        self.assertEqual(result["accuracy"], 1)
        self.assertEqual(result["benign_f1"], 1)
        result = metrics([1, 1], [.8, .9], .5)
        self.assertIsNone(result["fpr"])
        self.assertIsNone(result["benign_recall"])

    def test_invalid_inputs(self):
        for labels, scores, threshold in [([], [], .5), ([0], [], .5), ([True], [.1], .5),
                                          ([2], [.1], .5), ([0], [float("nan")], .5),
                                          ([0], [float("inf")], .5), ([0], [-.1], .5),
                                          ([0], [1.1], .5), ([0], [10 ** 400], .5), ([0], [True], .5),
                                          ([0], [.1], float("nan")), ([0], [.1], "0.5")]:
            with self.subTest(labels=labels, scores=scores, threshold=threshold):
                with self.assertRaises(ValueError):
                    metrics(labels, scores, threshold)

    def test_all_four_paired_outcomes_and_reordered_ids(self):
        examples = {str(i): {"label": label} for i, label in enumerate([0, 0, 1, 1])}
        reference = dict(zip(examples, [.1, .1, .1, .1]))
        candidate = {"3": .1, "2": .9, "1": .9, "0": .1}
        summary, errors = compare(examples, reference, candidate, .5)
        for key in ("both_correct", "introduced_errors", "corrected_errors", "both_wrong"):
            self.assertEqual(summary[key], 1)
        self.assertEqual(summary["disagreement_rate"], .5)
        self.assertEqual(summary["accuracy_delta_pp"], 0)
        self.assertEqual(len(errors), 3)
        self.assertEqual([row["example_id"] for row in errors], ["1", "2", "3"])
        candidate["3"] = .9
        summary, _ = compare(examples, reference, candidate, .5)
        self.assertEqual(summary["accuracy_delta_pp"], 25)
        with self.assertRaises(ValueError):
            compare(examples, reference, {"0": .1}, .5)


if __name__ == "__main__":
    unittest.main()
