# Independent P1-B pilot analysis review

Date: November 17, 2026. Reviewer: separate automated review agent at Yash's request;
this is not human review. Outcome: **passed within the scope below**.

## Scope and evidence examined

Reviewed `precision_benchmark/pilot_compare.py`, its four tests, and the corresponding
USAGE command. Read the prepared text-free training examples, three saved run manifests
and prediction files, and the generated report under `outputs/pilot-20261117/analysis-01/`.
No raw dataset prompts, official-test examples, Test-A/Test-B performance, checkpoint
weights or credentials were read by this analysis review. Stable training IDs, reference
labels, lengths, logits and scores were accessed as permitted development evidence.

The offline convenience command binds each saved run to the prepared pilot's identities,
threshold and planned/executed schedule, then delegates complete coverage, prediction
hashes, compatible-run checks and metrics to the existing evaluator. It preserves an
incomplete assembly on failure and refuses output reuse. It does not execute a model or
independently establish the truth of a native precision claim; its documentation states
that limitation accurately.

`python -m unittest tests.test_pilot_compare -v` passed all four tests. They exercise a
complete comparison, incomplete runs, incompatible environments, altered predictions,
missing coverage, all treatments sharing wrong pilot metadata, the pilot hash guard, and
the command-line path without native inference. Reviewed source SHA-256:
`6fd7c7d1f748c4748a177a2459acf25e672ae773c143603c2b2bebaec4cd6d8d`.
No blocking implementation defect was found.

## Independent calculations and integrity checks

A separate standard-library Python calculation read the retained JSON/JSONL and CSV
artifacts directly, without importing project evaluator/metric functions. It verified:

- Every declared comparison-to-run/example and run-to-prediction SHA-256 reference.
- Exactly 128 distinct training IDs per treatment, matching the same expected examples;
  64 benign and 64 injection examples; per class, 48 lengths at most 512, eight lengths
  513–1024 and eight lengths above 1024.
- Complete status, eligible-training role, threshold 0.5 and prediction `score >= 0.5`;
  correct run IDs, finite scores and two finite logits.
- Common model, tokenizer, dataset, preprocessing, input schedule, environment, score
  semantics and inference-code identities across all three treatments.
- Two-logit injection softmax recomputed in Python double precision. Maximum absolute
  score differences from the saved float32 conversion were 5.5724e-8 (FP32), 5.1605e-8
  (FP16), and 5.8354e-8 (INT8), all below the declared review tolerance of 1e-7.
- Confusion counts, class support, accuracy, both class-specific precision/recall/F1
  values, macro-F1, FPR/FNR, Brier score and ten equal-width calibration bins/ECE.
- ROC-AUC from all 64 × 64 positive/negative score pairs with half credit for ties,
  independently of the evaluator's ranking implementation.
- All four paired correctness outcomes, disagreements, accuracy differences and score
  delta summaries. Numeric results matched saved JSON to absolute tolerance 1e-12;
  integer counts matched exactly. Numeric CSV cells matched their JSON values.

The displayed Markdown tables were also read and their rounded values checked against
the independent calculations. No metric or threshold was changed by this review.

## Checked preliminary table

All treatments use the same 128 selected training examples and provisional threshold.
Rates below are percentages except macro-F1 and ROC-AUC.

| Treatment | Correct / 128 | TN / FP / FN / TP | Accuracy | Macro-F1 | Injection recall | FPR | FNR | ROC-AUC |
|---|---|---|---|---|---|---|---|---|
| FP32 | 97 | 63 / 1 / 30 / 34 | 75.78125% | 0.7447082288 | 53.125% | 1.5625% | 46.875% | 0.9323730469 |
| FP16 | 97 | 63 / 1 / 30 / 34 | 75.78125% | 0.7447082288 | 53.125% | 1.5625% | 46.875% | 0.9321289063 |
| INT8 | 98 | 63 / 1 / 29 / 35 | 76.5625% | 0.7538461538 | 54.6875% | 1.5625% | 45.3125% | 0.9260253906 |

FP16 versus FP32: 97 both correct, zero introduced errors, zero corrected errors and 31
both wrong. Decisions agree on every example; scores and ranking metrics are not identical.

INT8 versus FP32: 97 both correct, zero introduced errors, one corrected error and 30
both wrong. The sole changed decision is
`a5234cb1f5cdb256600cab64b8c961195b5e8404:train:3949`, reference label 1, original length
288 tokens, untruncated. Its injection score changes from 0.4914744794368744 in FP32 to
0.5186528563499451 in INT8. The accuracy difference is one example, or **0.78125 percentage
points**. Reference labels establish correctness; FP32 is not ground truth.

## Claim limits

These are descriptive development results from a deliberately balanced, length-stratified
training pilot with long inputs overrepresented. They are neither representative source
population estimates nor held-out benchmark findings. The threshold is provisional and
was not selected from FP32 validation predictions. No confidence interval, statistical
superiority, general precision ranking or main-study completion is established.

The only observed disagreement favors INT8 at this operating point. It supplies no
observed positive correction by an FP32 rerun in this small pilot. That fact does not
establish that escalation is generally harmful, useful or unnecessary, and does not test
or replace the committed learned-gate investigation. No oracle or gate benefit is inferred.

This review does not independently validate model loading, effective precision, GPU
provenance, pooling or resource measurement; those require their native evidence review.
The offline report correctly states that its score analysis does not measure resources.
Separately retained feasibility timing/memory observations must retain their own scope
and must not be presented as a final controlled profiling or speedup result.

## Retained identities

Project-relative root: `outputs/pilot-20261117/`.

| Artifact | SHA-256 |
|---|---|
| `attempt-01/comparison.json` | `16b55068b011fc618e6bcc94c5bc9da25839ff34971ee0e135f657f764e8bd1e` |
| Referenced prepared `examples.jsonl` | `828cf651e2ccbeace777eb8936ab91fcbb888f7e903f22825b6c87163c222089` |
| `attempt-01/runs/fp32/run.json` | `74d887efe9950333bdbee0997c7dec55440379c00df53f6b4a9b6cc9b0cf21a9` |
| `attempt-01/runs/fp16/run.json` | `8ab299832a3e826414c2a7de94bdb51f79f1c495ce930b04619b1d6d833af00e` |
| `attempt-01/runs/int8/run.json` | `04faf391c05ffcbe1dc915c844d3b190b72bb34ac579078b900404872a75cd5a` |
| `attempt-01/runs/fp32/predictions.jsonl` | `4934e1bd67221a2d6b1502db4ff16661cedf0c09c639053d47a7a882b23c4bad` |
| `attempt-01/runs/fp16/predictions.jsonl` | `c12f89a2d19e8244b68cc18f8dd7e4f513bcb95dff8d13a175eef916f939b8da` |
| `attempt-01/runs/int8/predictions.jsonl` | `db190d7d1388ca0b66d6601da179e081180d1fe7b6bf3f6be1579fc0343f10ff` |
| `analysis-01/results.json` | `7e60d1dfc4a04b8ae3c86317e2ff08493a185a73aeea750b5dcb5bce248b33fe` |

The output/result identities remain applicable when byte-identical prediction artifacts
are copied into an approved durable bundle. A rewritten comparison containing different
relative paths needs its own new hash and regeneration receipt; it does not change the
underlying predictions or arithmetic when those input hashes remain unchanged.
