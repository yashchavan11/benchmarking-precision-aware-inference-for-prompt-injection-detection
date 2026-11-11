"""Run with python -m precision_benchmark --manifest ... --output ..."""

import argparse
import sys

from .report import analyze, write_report


def main():
    parser = argparse.ArgumentParser(description="Compare saved FP32/FP16/INT8 development predictions.")
    parser.add_argument("--manifest", required=True, help="Comparison JSON manifest")
    parser.add_argument("--output", required=True, help="New output directory (existing directories are never overwritten)")
    args = parser.parse_args()
    try:
        result = analyze(args.manifest)
        path = write_report(result, args.output)
    except (OSError, ValueError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        return 2
    print(f"Report written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
