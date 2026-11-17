#!/bin/bash
#SBATCH --job-name=pai-token-audit
#SBATCH --account=cs5130.202710
#SBATCH --partition=courses
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=job-%j.out
#SBATCH --error=job-%j.err

# Submit only after the execution route and staged manifest are approved.
set -euo pipefail
test -n "${SLURM_JOB_ID:-}" || { printf 'Run through Slurm on a compute node.\n'; exit 2; }
readonly audit_root="$(pwd -P)"
readonly requested_audit_env="${PAI_AUDIT_ENV:-}"
test -f "$audit_root/stage-manifest.json" || { printf 'Submit with --chdir set to the staged project.\n'; exit 2; }
cd "$audit_root"
umask 077
test ! -e runtime-env || { printf 'Preserve the prior environment; stage a new run directory.\n'; exit 2; }
test ! -e outputs/runtime-native || { printf 'Preserve prior setup evidence; stage a new run directory.\n'; exit 2; }
# The cluster profile references optional interactive-shell variables.
set +u
source /etc/profile
set -u
module load python/3.13.5
cd "$audit_root"
export PYTHONNOUSERSITE=1
export PIP_CACHE_DIR="$audit_root/runtime-cache/pip"
export HF_HOME="$audit_root/runtime-cache/huggingface"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=true
export RAYON_NUM_THREADS=2
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_TOKEN_PATH PYTHONOPTIMIZE

mkdir outputs/runtime-native
python3 scripts/verify_tokenizer_stage.py stage-manifest.json
if [[ -n "$requested_audit_env" ]]; then
  readonly resolved_audit_env="$(readlink -f -- "$requested_audit_env")"
  case "$resolved_audit_env" in
    /scratch/chavan.yas/precision-aware-inference/*/project/runtime-env) ;;
    *) printf 'Reuse must refer to a preserved project audit environment.\n'; exit 2 ;;
  esac
  test -x "$resolved_audit_env/bin/python" || { printf 'Preserved environment is unavailable.\n'; exit 2; }
  readonly audit_python="$resolved_audit_env/bin/python"
  "$audit_python" - <<'PY'
from pathlib import Path
import hashlib, json, sys
prefix = Path(sys.prefix).resolve()
prior = prefix.parent / 'outputs/runtime-native'
names = ('pip-install-report.json', 'environment-lock.txt', 'pip-check.txt')
records = {name: hashlib.sha256((prior/name).read_bytes()).hexdigest() for name in names}
Path('outputs/runtime-native/reused-environment.json').write_text(
    json.dumps({'environment_prefix': str(prefix), 'prior_setup_sha256': records,
                'packages_reinstalled': False}, indent=2) + '\n', encoding='utf-8')
PY
else
  python3 -m venv runtime-env
  readonly audit_python="$audit_root/runtime-env/bin/python"
  "$audit_python" -m pip install --index-url https://pypi.org/simple --only-binary=:all: \
    --report outputs/runtime-native/pip-install-report.json \
    -r requirements-audit.txt > outputs/runtime-native/pip-install.log 2>&1
fi
"$audit_python" -m pip check > outputs/runtime-native/pip-check.txt
"$audit_python" -m pip freeze > outputs/runtime-native/environment-lock.txt
"$audit_python" -m unittest discover -s tests -v > outputs/runtime-native/tests.txt 2>&1
"$audit_python" -m precision_benchmark.tokenizer_audit \
  --assets outputs/contract-20261117/model-auth \
  --asset-manifest-sha256 fe4ef4fe0609b4465b1e7b8f2550c9c511fa9d1dc48c1fa34af7cb37cbdd1c23 \
  --access docs/evidence/p1a-development-access-20261117.json \
  --access-sha256 83dde0502e9aca5cfd000c5f6ec9631602db9f03a334a2f1a42d9ac3adc3e79b \
  --partitions outputs/contract-20261117/partitions-v2 \
  --raw-dir data/raw/promptshield/a5234cb1f5cdb256600cab64b8c961195b5e8404 \
  --batch-size 64 \
  --output outputs/tokenizer-audit-native
