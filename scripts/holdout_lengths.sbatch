#!/bin/bash
#SBATCH --job-name=pai-test-lengths
#SBATCH --account=cs5130.202710
#SBATCH --partition=courses
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=job-%j.out
#SBATCH --error=job-%j.err

# Additional official-test administrative scope must be approved before submission.
set -euo pipefail
test -n "${SLURM_JOB_ID:-}" || { printf 'Run through Slurm on a compute node.\n'; exit 2; }
readonly audit_root="$(pwd -P)"
readonly requested_env="${PAI_AUDIT_ENV:?Preserved audit environment required}"
readonly requested_assets="${PAI_TOKENIZER_ASSETS:?Preserved tokenizer assets required}"
test -f "$audit_root/stage-manifest.json" || { printf 'Submit in the staged project.\n'; exit 2; }
test ! -e outputs/runtime-native || { printf 'Preserve earlier output; use a new run directory.\n'; exit 2; }
umask 077
set +u
source /etc/profile
set -u
module load python/3.13.5
cd "$audit_root"
readonly audit_env="$(readlink -f -- "$requested_env")"
readonly audit_assets="$(readlink -f -- "$requested_assets")"
case "$audit_env" in
  /scratch/chavan.yas/precision-aware-inference/*/project/runtime-env) ;;
  *) printf 'Unexpected environment location.\n'; exit 2 ;;
esac
case "$audit_assets" in
  /scratch/chavan.yas/precision-aware-inference/*/project/outputs/contract-20261117/model-auth) ;;
  *) printf 'Unexpected tokenizer asset location.\n'; exit 2 ;;
esac
readonly audit_python="$audit_env/bin/python"
test -x "$audit_python" || { printf 'Preserved environment unavailable.\n'; exit 2; }
export PYTHONNOUSERSITE=1
export HF_HOME="$audit_root/runtime-cache/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=true
export RAYON_NUM_THREADS=2
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_TOKEN_PATH PYTHONOPTIMIZE

mkdir -p outputs
mkdir outputs/runtime-native
python3 scripts/verify_holdout_stage.py stage-manifest.json
"$audit_python" -m pip check > outputs/runtime-native/pip-check.txt
"$audit_python" -m pip freeze > outputs/runtime-native/environment-lock.txt
"$audit_python" -m unittest discover -s tests -v > outputs/runtime-native/tests.txt 2>&1
"$audit_python" -m precision_benchmark.holdout_lengths \
  --role administrative_official_test_lengths \
  --assets "$audit_assets" \
  --asset-manifest-sha256 fe4ef4fe0609b4465b1e7b8f2550c9c511fa9d1dc48c1fa34af7cb37cbdd1c23 \
  --raw-dir data/raw/promptshield/a5234cb1f5cdb256600cab64b8c961195b5e8404 \
  --source-sha256 526207c2485829d9961407011d7f4cd929569e7f285dc8396b3f385e0608bc70 \
  --output outputs/official-test-lengths \
  --batch-size 64
