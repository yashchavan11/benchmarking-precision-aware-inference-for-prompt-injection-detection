#!/bin/bash
#SBATCH --job-name=pai-precision-pilot
#SBATCH --account=cs5130.202710
#SBATCH --partition=sharing
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:l40s:1
#SBATCH --time=00:20:00
#SBATCH --output=../pilot-%j.out
#SBATCH --error=../pilot-%j.err
# Arguments: environment, verified tokenizer assets, raw source directory,
# partition directory, full checkpoint, expected pilot-manifest SHA256.
set -euo pipefail
test -n "${SLURM_JOB_ID:-}"
test "$#" -eq 6
readonly run_root="$(pwd -P)"
readonly inference_python="$1/bin/python"
readonly assets="$2" raw_sources="$3" partitions="$4" checkpoint="$5" pilot_sha="$6"
test -x "$inference_python"
test -f "$run_root/stage-manifest.json"
test ! -e "$run_root/run-output"
umask 077
set +u
source /etc/profile
set -u
module load python/3.13.5
cd "$run_root"
export PYTHONNOUSERSITE=1
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_TOKEN_PATH PYTHONOPTIMIZE
export HF_HOME="$run_root/offline-cache"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
export CUBLAS_WORKSPACE_CONFIG=:4096:8
verified_stage="$("$inference_python" scripts/verify_pilot_stage.py stage-manifest.json)"
mkdir run-output
printf '%s\n' "$verified_stage" > run-output/stage-check.json
"$inference_python" -m pip check > run-output/pip-check.txt
"$inference_python" -m pip freeze > run-output/environment-lock.txt
nvidia-smi --query-gpu=name,uuid,driver_version,memory.total,compute_mode --format=csv > run-output/gpu-inventory.csv
"$inference_python" -m unittest discover -s tests -v > run-output/tests.txt 2>&1
for precision in fp32 fp16 int8; do
  "$inference_python" -m precision_benchmark.pilot_inference \
    --pilot pilot/manifest.json --pilot-sha256 "$pilot_sha" \
    --assets "$assets" --checkpoint "$checkpoint" \
    --access docs/evidence/p1a-development-access-20261117.json \
    --access-sha256 83dde0502e9aca5cfd000c5f6ec9631602db9f03a334a2f1a42d9ac3adc3e79b \
    --partitions "$partitions" --raw-dir "$raw_sources" \
    --precision "$precision" --run-id "p1b-20261117-$precision-$SLURM_JOB_ID" \
    --output "run-output/$precision" --device cuda:0
done
