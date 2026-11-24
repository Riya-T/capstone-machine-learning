#!/bin/bash
# Trains a writer with train_dpo.py on a Nexus GPU node and serves it in
# Ollama, keeping every large file on the node's local /scratch0.
#
# Home has about 11 GB free, so only two things come back to it: the LoRA
# adapter (about 150 MB, runs/writers/<name>/) and the Q4_K_M writer in
# Ollama's store (about 4.7 GB, as writer-<name>-ctx8k). On /scratch0, removed
# when the job ends: the training venv and uv cache, the base model (bf16,
# 15 GB), the merged model, the f16 GGUF and llama.cpp.
#
# 1. Installs the training extra into a venv on /scratch0 (uv.lock, --frozen).
# 2. Downloads Qwen/Qwen2.5-Coder-7B-Instruct (HF_REVISION, default main) and
#    logs the commit it got: the PC recorded none, so log it here.
# 3. Runs `python -m harness.train_dpo` with the given arguments.
# 4. Builds the Ollama writer as in the README ("Serving the trained
#    writer"): merge_lora.py, convert_hf_to_gguf.py, the base GGUF's quant
#    types (gguf_quant_types.py), llama-quantize Q4_K_M, the same metadata
#    removed, then `ollama create` from the base writer's Modelfile.
#
# llama.cpp is pinned (LLAMA_CPP_REF) and gets its own venv for the
# converter, so its requirements never touch the training venv.
#
# Output: runs/slurm-<jobid>.out; runs/writers/<name>/ with the adapter,
# train_log.jsonl, train_args.json and build.txt (revisions, checksums).
#
# Usage (from harness/, on the submission node):
#     sbatch scripts/train_nexus.sbatch PREFERENCES.jsonl NAME [train_dpo arguments]
#     sbatch scripts/train_nexus.sbatch runs/nexus_hist/pairs_coarse/preferences.jsonl \
#         hist2_rpo_d_nexus --nll-weight 1 --learning-rate 3e-5 --epochs 3 --beta 0.1
#SBATCH --job-name=harness-train
#SBATCH --partition=class
#SBATCH --account=class
#SBATCH --qos=default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=runs/slurm-%j.out

set -euo pipefail

if [ $# -lt 2 ]; then
    echo "usage: sbatch scripts/train_nexus.sbatch <preferences.jsonl> <name> [train_dpo arguments]" >&2
    exit 2
fi
PREFS=$(realpath "$1")
NAME=$2
shift 2
case $NAME in *[!A-Za-z0-9_.-]*) echo "name may use letters, digits, _ . - only" >&2; exit 2;; esac

BASE_REPO=Qwen/Qwen2.5-Coder-7B-Instruct
HF_REVISION=${HF_REVISION:-main}
LLAMA_CPP_REF=${LLAMA_CPP_REF:-b12613}
OLLAMA_BIN=$HOME/.local/ollama/v0.40.5/bin/ollama   # installed by collect_nexus.sbatch
BASE_WRITER=qwen2.5-coder-7b-ctx8k                   # the Ollama writer this one replaces
MODEL=writer-$NAME-ctx8k

cd "${SLURM_SUBMIT_DIR:-.}"   # harness/
HARNESS=$PWD
OUT=$HARNESS/runs/writers/$NAME
if [ -e "$OUT/adapter_config.json" ]; then
    echo "$OUT already holds an adapter; pick another name" >&2
    exit 1
fi
[ -f "$PREFS" ] || { echo "no such file: $PREFS" >&2; exit 1; }
[ -x "$OLLAMA_BIN" ] || { echo "Ollama not installed; run collect_nexus.sbatch once" >&2; exit 1; }

SCR=/scratch0/$USER/train-${SLURM_JOB_ID:-local}
mkdir -p "$SCR" "$OUT"
export XDG_RUNTIME_DIR=$SCR/xdg
mkdir -p "$XDG_RUNTIME_DIR"
OLLAMA_PID=
cleanup() {
    [ -n "$OLLAMA_PID" ] && { kill "$OLLAMA_PID" 2>/dev/null; wait "$OLLAMA_PID" 2>/dev/null || true; }
    rm -rf "$SCR"
}
trap cleanup EXIT

export UV_CACHE_DIR=$SCR/uv-cache
export HF_HOME=$SCR/hf
export HF_HUB_DISABLE_TELEMETRY=1
step() { echo; echo "== $(date '+%F %T') $*"; }

echo "job ${SLURM_JOB_ID:-local} on $(hostname), GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo "git: $(git rev-parse --short HEAD)$(git diff --quiet HEAD -- . || echo ' (uncommitted changes)')"
echo "preferences: $PREFS ($(wc -l < "$PREFS") pairs, sha256 $(sha256sum "$PREFS" | cut -c1-16))"
echo "train_dpo arguments: $*"
df -h /scratch0 | tail -1

# -- 1. training venv -------------------------------------------------------------
step "installing the training extra"
export UV_PROJECT_ENVIRONMENT=$SCR/venv
uv sync --frozen --extra training --quiet
PY=$SCR/venv/bin/python
"$PY" -c "import torch; assert torch.cuda.is_available(), 'no CUDA'; print('torch', torch.__version__, torch.cuda.get_device_name(0))"

# -- 2. base model ------------------------------------------------------------------
step "downloading $BASE_REPO@$HF_REVISION"
BASE=$SCR/base
BASE_SHA=$("$PY" - "$BASE_REPO" "$HF_REVISION" "$BASE" <<'EOF'
import sys
from huggingface_hub import HfApi, snapshot_download
repo, revision, out = sys.argv[1:]
sha = HfApi().model_info(repo, revision=revision).sha
snapshot_download(repo, revision=sha, local_dir=out,
                  allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.py"])
print(sha)
EOF
)
echo "base revision: $BASE_SHA"

# -- 3. train -----------------------------------------------------------------------
step "training $NAME"
"$PY" -m harness.train_dpo "$PREFS" --model "$BASE" --output-dir "$SCR/adapter" "$@"
cp -r "$SCR/adapter/." "$OUT/"
echo "adapter saved to $OUT"

# -- 4. Ollama writer ---------------------------------------------------------------
step "merging the adapter"
"$PY" scripts/merge_lora.py "$BASE" "$SCR/adapter" "$SCR/merged" --dtype float16
rm -rf "$BASE"   # 15 GB; the merged copy is all that is needed from here

step "building llama.cpp $LLAMA_CPP_REF"
git clone --quiet --depth 1 --branch "$LLAMA_CPP_REF" https://github.com/ggml-org/llama.cpp.git "$SCR/llama.cpp"
cmake -S "$SCR/llama.cpp" -B "$SCR/llama.cpp/build" -DGGML_CUDA=OFF -DLLAMA_CURL=OFF >/dev/null
cmake --build "$SCR/llama.cpp/build" --target llama-quantize -j "${SLURM_CPUS_PER_TASK:-4}" >/dev/null
uv venv --quiet "$SCR/llvenv"
uv pip install --quiet --python "$SCR/llvenv/bin/python" \
    -r "$SCR/llama.cpp/requirements/requirements-convert_hf_to_gguf.txt"
LPY=$SCR/llvenv/bin/python
export PYTHONPATH=$SCR/llama.cpp/gguf-py

step "converting to GGUF"
"$LPY" "$SCR/llama.cpp/convert_hf_to_gguf.py" "$SCR/merged" --outtype f16 --outfile "$SCR/writer-f16.gguf"
rm -rf "$SCR/merged"

# Ollama on its own port; the collect jobs hold 11434 on their nodes.
PORT=$((20000 + ${SLURM_JOB_ID:-0} % 20000))
export OLLAMA_HOST=127.0.0.1:$PORT
"$OLLAMA_BIN" serve >"$SCR/ollama.log" 2>&1 &
OLLAMA_PID=$!
for _ in $(seq 60); do
    curl -fs "http://$OLLAMA_HOST/api/version" >/dev/null 2>&1 && break
    sleep 1
done
"$OLLAMA_BIN" show "$BASE_WRITER" --modelfile > "$SCR/Modelfile.base"
OFFICIAL=$(sed -n 's/^FROM //p' "$SCR/Modelfile.base" | head -1)
[ -f "$OFFICIAL" ] || { echo "base writer GGUF not found: $OFFICIAL" >&2; exit 1; }

step "quantizing to Q4_K_M with the base writer's quant types"
"$LPY" scripts/gguf_quant_types.py "$OFFICIAL" "$SCR/types.txt"
"$SCR/llama.cpp/build/bin/llama-quantize" --tensor-type-file "$SCR/types.txt" \
    "$SCR/writer-f16.gguf" "$SCR/raw.gguf" Q4_K_M
rm -f "$SCR/writer-f16.gguf"
# --force: the script otherwise asks to type YES before removing metadata.
"$LPY" "$SCR/llama.cpp/gguf-py/gguf/scripts/gguf_new_metadata.py" --force \
    --remove-metadata general.sampling.temp --remove-metadata general.sampling.top_k \
    --remove-metadata general.sampling.top_p --remove-metadata general.sampling.penalty_repeat \
    --remove-metadata tokenizer.ggml.add_eos_token --remove-metadata tokenizer.ggml.clean_spaces \
    --remove-metadata tokenizer.ggml.normalizer.nfc "$SCR/raw.gguf" "$SCR/writer-q4km.gguf"
GGUF_SHA=$(sha256sum "$SCR/writer-q4km.gguf" | cut -d' ' -f1)

step "creating $MODEL in Ollama"
sed "s#^FROM .*#FROM $SCR/writer-q4km.gguf#" "$SCR/Modelfile.base" > "$SCR/Modelfile"
"$OLLAMA_BIN" create "$MODEL" -f "$SCR/Modelfile"
"$OLLAMA_BIN" list | grep -E "^($MODEL|$BASE_WRITER)"

cat > "$OUT/build.txt" <<EOF
job ${SLURM_JOB_ID:-local} on $(hostname), $(date '+%F %T')
git $(git rev-parse HEAD)$(git diff --quiet HEAD -- . || echo ' (uncommitted changes)')
preferences $PREFS sha256 $(sha256sum "$PREFS" | cut -d' ' -f1)
train_dpo arguments: $*
base $BASE_REPO revision $BASE_SHA
llama.cpp $LLAMA_CPP_REF
quant types from $OFFICIAL
gguf sha256 $GGUF_SHA
ollama model $MODEL
EOF
cat "$OUT/build.txt"
