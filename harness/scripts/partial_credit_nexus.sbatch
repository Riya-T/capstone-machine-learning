#!/bin/bash
# Partial credit on a Nexus compute node: runs the hidden tests on the
# editing steps that ran out of turns (Apptainer sandbox, no GPU, no model),
# then writes the analysis next to this job's log.
#
# Output: runs/slurm-<jobid>.out and runs/partial_credit-<jobid>.md.
# Backfill resumes, so a job that stops can simply be submitted again.
#
# Usage (from harness/, on the submission node):
#     sbatch scripts/partial_credit_nexus.sbatch configs/nexus_hist2_eval_maintain.yaml
#SBATCH --job-name=partial-credit
#SBATCH --partition=class
#SBATCH --account=class
#SBATCH --qos=default
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=runs/slurm-%j.out

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "usage: sbatch scripts/partial_credit_nexus.sbatch <config>" >&2
    exit 2
fi
CONFIG=$1

cd "${SLURM_SUBMIT_DIR:-.}"   # harness/
export XDG_RUNTIME_DIR=/tmp/xdg-$UID-${SLURM_JOB_ID:-local}
mkdir -p "$XDG_RUNTIME_DIR"
echo "job ${SLURM_JOB_ID:-local} on $(hostname)"
echo "git: $(git rev-parse --short HEAD)$(git diff --quiet HEAD -- . || echo ' (uncommitted changes)')"

uv run python scripts/partial_credit.py backfill --config "$CONFIG" --workers 4
uv run python scripts/partial_credit.py analyze --config "$CONFIG" \
    --out "runs/partial_credit-${SLURM_JOB_ID:-local}.md"
