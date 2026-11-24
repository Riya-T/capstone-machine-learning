# History-suite DPO beta/NLL sweep

This follow-up isolates the two untested loss settings while keeping the
selected history-suite setting D fixed at 3 epochs and a learning rate of
`3e-5`. It reuses the 83 history-suite training pairs and runs five settings
for seeds 42, 43 and 44 (15 training runs total):

| Contrast | Beta | NLL weight |
|---|---:|---:|
| Beta low | 0.05 | 1 |
| Baseline D | 0.1 | 1 |
| Beta high | 0.2 | 1 |
| Plain DPO at D's learning rate/epochs | 0.1 | 0 |
| Stronger NLL at D's learning rate/epochs | 0.1 | 2 |

The existing plain-DPO result used different learning-rate/epoch settings, so
the new `beta=0.1, NLL=0` run is needed for a controlled NLL comparison. The
`beta=0.1, NLL=1` baseline is also retrained for all three seeds so every
candidate uses the same fixed setup and input file.

## Prepare and submit

Run preparation on the Nexus checkout, where the history-suite preference
file is available. The HF revision must be a full 40-character commit so all
15 jobs start from the same model:

```sh
cd harness
HF_REVISION=$(curl -fsSL \
  https://huggingface.co/api/models/Qwen/Qwen2.5-Coder-7B-Instruct |
  python -c 'import json,sys; print(json.load(sys.stdin)["sha"])')
uv run python -m harness.dpo_sweep prepare \
  --preferences /path/to/history-suite/preferences.jsonl \
  --hf-revision "$HF_REVISION"
```

Before submitting, run `collect_nexus.sbatch` once to install Ollama and pull
the base models if this Nexus account has not used the harness there before.
Then submit the prepared jobs sequentially:

```sh
bash runs/dpo_sweeps/hist2_beta_nll_dev/submit.sh
```

The generated script chains each training job after the previous dev
collection, and each collection after its training job. It trains via
`scripts/train_nexus.sbatch` and collects the four dev tasks via
`scripts/collect_nexus.sbatch --until initial`; it does not run editing trials
or use held-out eval tasks. Re-run preparation with a new sweep name to create
a distinct set of writer output directories.

## Records and selection

Preparation writes a sweep manifest and one manifest per seed under
`runs/dpo_sweeps/hist2_beta_nll_dev/`. Each records the preference-file hash,
model commit, code revision/dirty state, hyperparameters, evaluation config,
and Slurm job IDs as they are submitted. The training job additionally writes
its full training arguments, optimizer log and build record under
`runs/writers/<run-id>/`; dev collection outputs are in the manifest's
evaluation run directory. Generated model-specific YAMLs live in `configs/`
and are ignored by Git; the committed base config is
`configs/nexus_hist2_dev.yaml`.

Use the historical dev-only rule: a setting is eligible if its mean number of
initially passing programs across the three seeds is at least 20 (two-thirds
of the base writer's 30). Among eligible settings, compare the mean count of
passing copy-design programs. Report ties rather than breaking them after
seeing the outcomes. This is a setup-only workflow: no GPU training or
collection is performed by `prepare`.
