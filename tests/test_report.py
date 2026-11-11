import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from precision_benchmark.report import analyze, write_csv, write_report
from tests.test_artifacts import FIXTURE


class ReportTests(unittest.TestCase):
    def test_report_matches_fixture_and_preserves_existing_output(self):
        result = analyze(FIXTURE / "comparison.json")
        self.assertEqual(result["quality"]["fp32"]["accuracy"], .5)
        self.assertEqual(result["quality"]["int8"]["accuracy"], .75)
        self.assertEqual(result["paired_vs_fp32"]["int8"]["accuracy_delta_pp"], 25)
        self.assertEqual(result["paired_vs_fp32"]["fp16"]["both_wrong"], 2)
        self.assertEqual(result["truncation_subgroups"]["fp32"]["truncated"]["n"], 4)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report"
            report = write_report(result, output)
            self.assertIn("SYNTHETIC DEMONSTRATION", report.read_text())
            self.assertIn("not model results", report.read_text())
            self.assertEqual(json.loads((output / "results.json").read_text())["quality"], result["quality"])
            with (output / "error_analysis.csv").open() as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 12)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            with self.assertRaises(FileExistsError):
                write_report(result, output)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_cli_success_reproducibility_and_clean_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = [Path(tmp) / "first", Path(tmp) / "second"]
            for output in outputs:
                process = subprocess.run([sys.executable, "-m", "precision_benchmark", "--manifest",
                                          str(FIXTURE / "comparison.json"), "--output", str(output)],
                                         capture_output=True, text=True)
                self.assertEqual(process.returncode, 0, process.stderr)
            for path in outputs[0].iterdir():
                self.assertEqual(path.read_bytes(), (outputs[1] / path.name).read_bytes())
            process = subprocess.run([sys.executable, "-m", "precision_benchmark", "--manifest",
                                      str(FIXTURE / "comparison.json"), "--output", str(outputs[0])],
                                     capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertNotIn("Traceback", process.stderr)

    def test_csv_formula_escaping(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "safe.csv"
            write_csv(path, ["id", "number"], [{"id": "=1+1", "number": -.1}])
            with path.open() as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["id"], "'=1+1")
            self.assertEqual(row["number"], "-0.1")


if __name__ == "__main__":
    unittest.main()
