#!/bin/bash
#SBATCH --job-name=pai-inference-env
#SBATCH --account=cs5130.202710
#SBATCH --partition=courses
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=setup-%j.out
#SBATCH --error=setup-%j.err
set -euo pipefail
test -n "${SLURM_JOB_ID:-}"
readonly run_root="$(pwd -P)"
test -f "$run_root/requirements-inference.txt"
test ! -e "$run_root/inference-env"
umask 077
set +u
source /etc/profile
set -u
module load python/3.13.5
cd "$run_root"
export PYTHONNOUSERSITE=1
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_TOKEN_PATH PYTHONOPTIMIZE
export HF_HOME="$run_root/cache/huggingface"
export PIP_CACHE_DIR="$run_root/cache/pip"
mkdir setup-evidence
python3 -m venv inference-env
readonly py="$run_root/inference-env/bin/python"
"$py" -m pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu126 \
  --report setup-evidence/torch-install.json torch==2.9.1 > setup-evidence/torch-install.log 2>&1
"$py" -m pip install --only-binary=:all: --index-url https://pypi.org/simple \
  --report setup-evidence/remaining-install.json -r requirements-inference.txt > setup-evidence/remaining-install.log 2>&1
"$py" -m pip check > setup-evidence/pip-check.txt
"$py" -m pip freeze > setup-evidence/environment-lock.txt
"$py" - <<'PY'
import json,sys,platform,importlib.metadata as md
from pathlib import Path
import torch, transformers, tokenizers, bitsandbytes, accelerate
Path('setup-evidence/imports.json').write_text(json.dumps({
 'status':'complete','python':sys.version,'platform':platform.platform(),
 'versions':{n:md.version(n) for n in ('torch','transformers','tokenizers','bitsandbytes','accelerate')},
 'compiled_cuda':torch.version.cuda,'gpu_validation':'pending GPU allocation'},indent=2)+'\n')
PY
