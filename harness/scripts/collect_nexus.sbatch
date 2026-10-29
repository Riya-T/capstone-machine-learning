#!/bin/bash
# Runs `python -m harness collect` on a Nexus GPU node, with its own Ollama.
#
# 1. Installs Ollama (pinned version, checksum verified) under
#    ~/.local/ollama if missing.
# 2. Starts `ollama serve` on 127.0.0.1:11434 on the job's GPU. That is the
#    configs' base_url, which is part of the writer key, so the port can't
#    change. The script refuses to start if another server already holds
#    the port, and checks that the one answering is its own.
# 3. Pulls the writer (7B) and editor (14B) models and creates the
#    8192-token-context variants the configs name, if missing. Both stay
#    loaded, which needs an RTX A5000 (24 GB).
# 4. Runs collect with the given config and arguments, then stops Ollama.
#
# Output: runs/slurm-<jobid>.out, plus the Ollama log in
# runs/ollama-<jobid>.log. Collect resumes where it stopped, so a job that
# hits its time limit can simply be submitted again.
#
# Usage (from harness/, on the submission node):
#     sbatch scripts/collect_nexus.sbatch configs/nexus.yaml --until initial
#     sbatch --time=04:00:00 scripts/collect_nexus.sbatch configs/nexus.yaml
#SBATCH --job-name=harness-collect
#SBATCH --partition=class
#SBATCH --account=class
#SBATCH --qos=medium
#SBATCH --gres=gpu:rtxa5000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=runs/slurm-%j.out

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "usage: sbatch scripts/collect_nexus.sbatch <config> [collect arguments]" >&2
    exit 2
fi
CONFIG=$1
shift

OLLAMA_VERSION=v0.40.5
OLLAMA_SHA256=dc5eabc292f9949546c90a97c820f924b035e05243b0de13c7f366182562169c
OLLAMA_DIR=$HOME/.local/ollama/$OLLAMA_VERSION
# <name in the configs>=<Ollama model it is made from>
MODELS="qwen2.5-coder-7b-ctx8k=qwen2.5-coder:7b-instruct
        qwen2.5-coder-14b-ctx8k=qwen2.5-coder:14b-instruct"
PORT=11434                     # the port in the configs' base_url

cd "${SLURM_SUBMIT_DIR:-.}"   # harness/
export XDG_RUNTIME_DIR=/tmp/xdg-$UID-${SLURM_JOB_ID:-local}
mkdir -p "$XDG_RUNTIME_DIR"
echo "job ${SLURM_JOB_ID:-local} on $(hostname), GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo "git: $(git rev-parse --short HEAD)$(git diff --quiet HEAD -- . || echo ' (uncommitted changes)')"

# -- 1. install Ollama ----------------------------------------------------------
# A lock, so two jobs starting together don't install over each other.
mkdir -p "$HOME/.local/ollama"
(
    flock 9
    if [ ! -x "$OLLAMA_DIR/bin/ollama" ]; then
        echo "installing Ollama $OLLAMA_VERSION into $OLLAMA_DIR"
        partial=$(mktemp -d "$HOME/.local/ollama/partial-XXXXXX")
        trap 'rm -rf "$partial"' EXIT
        curl -fsSL -o "$partial/ollama.tar.zst" \
            "https://github.com/ollama/ollama/releases/download/$OLLAMA_VERSION/ollama-linux-amd64.tar.zst"
        echo "$OLLAMA_SHA256  $partial/ollama.tar.zst" | sha256sum -c -
        mkdir "$partial/root"
        tar --zstd -xf "$partial/ollama.tar.zst" -C "$partial/root"
        mv "$partial/root" "$OLLAMA_DIR"   # in place only when complete
    fi
) 9>"$HOME/.local/ollama/.lock"

# -- 2. start Ollama ------------------------------------------------------------
if ss -Hltn "sport = :$PORT" | grep -q .; then
    echo "port $PORT is already in use on $(hostname) (another user's server?); resubmit" >&2
    exit 1
fi
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_KEEP_ALIVE=-1        # never unload: writer and editor alternate
export OLLAMA_MAX_LOADED_MODELS=2  # both fit on the A5000
export OLLAMA_NUM_PARALLEL=1       # the harness calls one model at a time
"$OLLAMA_DIR/bin/ollama" serve >"runs/ollama-${SLURM_JOB_ID:-local}.log" 2>&1 &
OLLAMA_PID=$!
trap 'kill $OLLAMA_PID 2>/dev/null; wait $OLLAMA_PID 2>/dev/null || true' EXIT

for _ in $(seq 120); do
    curl -fs "http://127.0.0.1:$PORT/api/version" >/dev/null 2>&1 && break
    kill -0 $OLLAMA_PID 2>/dev/null || { echo "ollama serve exited; see runs/ollama-${SLURM_JOB_ID:-local}.log" >&2; exit 1; }
    sleep 1
done
# ss names the owning process only for our own sockets.
if ! ss -Hltnp "sport = :$PORT" | grep -q "pid=$OLLAMA_PID,"; then
    echo "the server on port $PORT is not this job's Ollama" >&2
    exit 1
fi
echo "$("$OLLAMA_DIR/bin/ollama" --version | tail -1), serving on $OLLAMA_HOST"

# -- 3. models ------------------------------------------------------------------
ollama() { "$OLLAMA_DIR/bin/ollama" "$@"; }
for pair in $MODELS; do
    model=${pair%%=*} base=${pair#*=}
    if ! ollama show "$model" >/dev/null 2>&1; then
        ollama show "$base" >/dev/null 2>&1 || ollama pull "$base"
        # The context is fixed in a named variant: Ollama's OpenAI-compatible
        # endpoint can't set it per request.
        curl -fsS "http://127.0.0.1:$PORT/api/create" -d "{\"model\": \"$model\",
            \"from\": \"$base\", \"parameters\": {\"num_ctx\": 8192}}" | tail -1
        echo
    fi
done
# Compare the 7B's id with `ollama list` on the laptop: a different base
# model writes different programs under the same writer key.
ollama list

# -- 4. collect -----------------------------------------------------------------
echo "collect --config $CONFIG $*"
uv run python -m harness collect --config "$CONFIG" "$@"
