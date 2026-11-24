# Datasets: training data everyone can see

`harness/runs/` holds each person's stores, blobs and logs. It is not in
git: the SQLite stores are large, change on every run, can't be merged, and
are written to while collection runs. So the files that training and our
results depend on, such as the DPO pairs, are copied here instead, into
`harness/data/<dataset>/`, which git tracks. Pull the repository and you
have them.

A dataset is a folder of files plus a `MANIFEST.json` that the tools write.
Nothing here is made automatically: collection still writes to `runs/`, and
a file only lands here when you pass `--dataset` or run `add`, then commit.

## Before you start

- **Where to run:** every command is run from `harness/`. On the Nexus
  cluster, run them on a compute node, not the submission node:
  `srun --partition=class --account=class --qos=default --cpus-per-task=4 --mem=8gb --pty bash`.
- **Which Python:** use `.venv/bin/python` for everything below. Make that
  environment once with `uv sync --extra training` (`match_pairs.py` needs
  the tokenizer from the training extra; the other scripts need only
  `uv sync`). A bare `python` does not find the `harness` package.
- **Names:** dataset and file names use lowercase letters, digits, `.`, `_`
  and `-` (for example `train-v2` or `pairs-karin-v1`).

## Adding your pairs (everyone who collects)

After a collection run, its pairs are in
`runs/<your store>/<run_id>/preferences.jsonl` (the run id is printed at the
end of the run, and the newest folder in your store is the latest run). Add
that file, unfiltered, as a dataset of your own, named after you:

```bash
.venv/bin/python -m harness.datasets add pairs-<yourname>-v1 \
    runs/<your store>/<run_id>/preferences.jsonl
git add data/pairs-<yourname>-v1
git commit
```

Use your own name so that nobody else writes to the same folder: two people
adding to one dataset on different branches gives a git conflict in its
`MANIFEST.json`. If you collect more later, add it as `pairs-<yourname>-v2`.

Each pair records where it came from (next section), so a combined training
set can always be traced back to whose run made each pair.

## Where each pair came from

Since 2026-11-13, every row of `preferences.jsonl` has a `source` block
(`src/harness/collection/source.py`):

| Field | What it is |
|---|---|
| `run_id`, `store`, `config` | the run, the store folder it was written to (such as `nexus_karin`), and the config's `name` |
| `git_commit`, `git_dirty` | the code that made it, and whether it had uncommitted changes |
| `seed` | the config's base seed |
| `writer_key`, `editor_key`, `sandbox_key` | the keys the store filed the results under |
| `sandbox_runtime` | `docker` or `apptainer` |
| `task_version`, `prompt_version` | hashes of the task's files and of the writer prompt |
| `settings`, `settings_hash` | the settings that decide which pairs come out (below) |

`settings` holds the writer and editor models and their sampling settings,
the prompt templates (by content), the editor's budget, reps and
`view_transform`, the sandbox limits, the scorer settings and the task
sequence settings. It leaves out what only differs between machines or
people: server addresses, timeouts and retries, the seed, which tasks you
included, how many samples you drew, the store folder, and the sandbox
runtime and image. **Pairs with the same `settings_hash` come from the same
experiment and can be joined.** Docker and Apptainer pairs count as the same
experiment: their limits differ only for programs near the memory limit or
the timeout (`src/harness/sandbox/apptainer.py`), so `sandbox_runtime` is
recorded but not compared.

Pairs scored before 2026-11-13, including the first 229 (`train-v1` below),
have no `source` block. Rescoring their store with the current code adds it
without any model calls:
`.venv/bin/python -m harness report --config <their config> --out <folder>`.

## Making a training set

The scripts that make training files take `--dataset NAME` in place of an
output path, and write straight into `harness/data/NAME/`:

| Script | Reads | Writes to the dataset |
|---|---|---|
| `scripts/filter_pairs.py` | the scorer's pairs | `pairs.jsonl` (the DPO training pairs) and `pairs_unfiltered.jsonl` (a copy of its input, so the filter can be rerun or changed later) |
| `scripts/static_ranking.py` | your store, through `--config` | `radon_all.jsonl` and `radon_all_report.json` (every Radon-ranked pair) |
| `scripts/match_pairs.py` | `radon_all.jsonl` and `pairs.jsonl` | `radon_matched.jsonl` (the static-ranking baseline's training pairs) |
| `scripts/sft_programs.py` | your store, through `--config`, and `pairs.jsonl` | `sft_programs.jsonl` (the correctness-only baseline's training file) |

Run them in this order, since each later step reads files the earlier ones
wrote. `static_ranking.py` and `sft_programs.py` read the store and need the
sandbox image to exist (the results are filed under its id), so run them
where the store is.

```bash
# 1. DPO pairs: keep pairs won in at least 2 of 3 reps, drop cosmetic ones
.venv/bin/python scripts/filter_pairs.py runs/<run_id>/preferences.jsonl \
    --dataset train-v2 --min-rep-wins 2 --drop-cosmetic
# 2. every Radon-ranked pair from the store
.venv/bin/python scripts/static_ranking.py --config configs/rtx5070_train.yaml \
    --dataset train-v2
# 3. as many Radon pairs per task as step 1 kept
.venv/bin/python scripts/match_pairs.py data/train-v2/radon_all.jsonl \
    data/train-v2/pairs.jsonl --dataset train-v2 --model Qwen/Qwen2.5-Coder-7B-Instruct
# 4. the passing programs of the same tasks
.venv/bin/python scripts/sft_programs.py --config configs/rtx5070_train.yaml \
    --tasks-from data/train-v2/pairs.jsonl --dataset train-v2
```

Each script prints the `git add` line for what it wrote. Nothing is
committed for you, so look at the files first. `--out` still works for
scratch files that should stay in `runs/`.

Then train from the tracked copy, for example
`.venv/bin/python -m harness.train_dpo data/train-v2/pairs.jsonl ...` (the
full training command is in the main README, "DPO training").

## Joining pairs from several people

Pairs are only ever made within one task, so compatible preference files can
be joined. Validate first, then merge to a scratch file and run the usual
filter once:

```bash
.venv/bin/python -m harness.datasets validate \
    --legacy-config configs/rtx5070_train.yaml \
    data/train-v1/pairs_cap8_all.jsonl data/pairs-*/preferences.jsonl
.venv/bin/python -m harness.datasets merge --out runs/combined.jsonl \
    --legacy-config configs/rtx5070_train.yaml \
    data/train-v1/pairs_cap8_all.jsonl data/pairs-*/preferences.jsonl
.venv/bin/python scripts/filter_pairs.py runs/combined.jsonl --dataset train-v2 \
    --min-rep-wins 2 --drop-cosmetic
```

`--legacy-config` explicitly maps source-less historical rows (such as
`train-v1`) to the settings hash of the config that produced them. Rows with
source metadata are checked against that hash. Both commands reject mixed
settings, malformed pairs, repeated or oppositely labeled comparisons, and
task/prompt version mismatches. By default they also enforce the scorer's
per-task cap of 8; use `--per-task-cap N` to select another cap or
`--no-per-task-cap` only when intentionally combining uncapped results.
`merge` does not silently deduplicate or trim pairs: resolve reported
conflicts before training.

The merge output stays in `runs/`; `filter_pairs.py --dataset` adds the
unfiltered input and filtered training pairs to the tracked dataset.

## The first training set: train-v1

The first 229 pairs and the files trained on them were made on Karin's PC
(store `runs/rtx5070_pc/`, config `configs/rtx5070_train.yaml`), before
`--dataset` existed. They were added on 2026-11-16 with:

```bash
.venv/bin/python -m harness.datasets add train-v1 \
    runs/rtx5070_pc/dpo/pairs_cap8_all.jsonl \
    runs/rtx5070_pc/dpo/pairs_cap8_f23.jsonl \
    runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl \
    runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm_consistent.jsonl \
    runs/rtx5070_pc/dpo/radon_cap8_all.jsonl \
    runs/rtx5070_pc/dpo/radon_matched.jsonl \
    runs/rtx5070_pc/dpo/sft_programs.jsonl
```

`add` keeps each file's name, so `train-v1` uses the old names, not the
ones in the table above:

| train-v1 file | What it is | Same as, in later datasets |
|---|---|---|
| `pairs_cap8_all.jsonl` | all 229 scorer pairs, up to 8 per task | `pairs_unfiltered.jsonl` |
| `pairs_cap8_f23.jsonl` | the 182 of them won in at least 2 of 3 reps | – |
| `pairs_cap8_f23_nocosm.jsonl` | **the 160 pairs dpo2 and dpo3 were trained on** (won in at least 2 of 3 reps, cosmetic pairs dropped) | `pairs.jsonl` |
| `pairs_cap8_f23_nocosm_consistent.jsonl` | a stricter subset of those 160 (98 pairs), made with them and never trained on | – |
| `radon_cap8_all.jsonl` | all 271 Radon-ranked pairs | `radon_all.jsonl` |
| `radon_matched.jsonl` | the static-ranking baseline's 160 pairs | `radon_matched.jsonl` |
| `sft_programs.jsonl` | the correctness-only baseline's 201 programs | `sft_programs.jsonl` |

## Every collection's pairs: pairs-karin-v1

The scorer's pairs of every collection on Karin's PC that gave at least
one pair, one file per config (`<config>.jsonl` for
`configs/<config>.yaml`). They were rebuilt from the store on 2026-11-16
with the current code (no model calls), so every row has a `source` block:

```bash
for c in rtx5070_train rtx5070_pc rtx5070_eval ...; do
  .venv/bin/python -m harness report --config configs/$c.yaml \
      --out runs/rtx5070_pc/pairs_export/$c
  cp runs/rtx5070_pc/pairs_export/$c/preferences.jsonl runs/rtx5070_pc/pairs_export/$c.jsonl
done
.venv/bin/python -m harness.datasets add pairs-karin-v1 runs/rtx5070_pc/pairs_export/*.jsonl
```

| Files | Pairs | What they are |
|---|---:|---|
| `rtx5070_train.jsonl` | 229 | the train tasks: the same 229 pairs as `train-v1/pairs_cap8_all.jsonl`, with `source` blocks |
| `rtx5070_pc.jsonl` | 47 | the dev tasks, base writer |
| `rtx5070_eval.jsonl`, `rtx5070_eval_maintain.jsonl`, `rtx5070_eval_dpo3.jsonl`, `rtx5070_eval_radon.jsonl`, `rtx5070_eval_sft.jsonl` | 119, 109, 100, 94, 111 | the eval tasks, one file per writer (the five methods) |
| the same five with `_nocomments` | 114, 111, 100, 91, 111 | the comment ablation of the five |
| `rtx5070_dev_dpo2.jsonl`, `rtx5070_dev_dpo3.jsonl` | 39, 37 | the dev tasks with the two trained writers, used to choose the learning rate |
| `rtx5070_pc_editor_t02.jsonl`, `_editor_patch`, `_editor_7b`, `_editor_v3`, `_outline`, `_obscure`, `_editor_7b_obscure` | 40, 50, 25, 44, 29, 42, 31 | the dev-task editor probes and readability controls (`harness/results/diagnostics.md`) |
| `rtx5070_pc_hints.jsonl` | 29 | the dev tasks with design-hinted writer samples |
| `rtx5070_pilot_maintain.jsonl` | 1 | the design-sensitive pilot, maintainability prompt |

The 3B editor, the 3B writer and the pilot with the plain prompt gave no
pairs, so they have no file. Apart from `rtx5070_train.jsonl`, these are
dev, eval and probe pairs: nothing was ever trained on them.

## The label-noise control: label-noise-v1

| File | Pairs | What it is |
|---|---:|---|
| `radon_f15.jsonl`, `radon_f30.jsonl`, `radon_f50.jsonl` | 160 each | `train-v1/radon_matched.jsonl` with 24, 48 and 80 pairs swapped (`scripts/flip_pairs.py --rate 0.15`, `0.3`, `0.5`, seed 20261116); every row has `"flipped"` |
| `radon_dev.jsonl` | 60 | Radon-ranked pairs of the base writer's dev-task programs (`scripts/static_ranking.py --config configs/rtx5070_pc.yaml`), for testing on tasks no writer trained on |
| `radon_evaltasks.jsonl` | 114 | the same for the eval-task programs (`--config configs/rtx5070_eval.yaml`) |
| `radon_rel18.jsonl`, `radon_rel18s2.jsonl`, `radon_rel47.jsonl`, `radon_rel80.jsonl` | 160 each | the score-noise control: train programs ranked by Radon MI plus noise drawn once per program (`scripts/static_ranking.py --score-noise 0.18`, the same with `--seed 2`, `0.47`, `0.80`), capped and matched per task to `train-v1/pairs_cap8_f23_nocosm.jsonl` (`scripts/match_pairs.py`); every row has `chosen_mi` and `rejected_mi` |
| `radon_rel18_all.jsonl` | 627 | the same at 0.18 with every unequal pair (`--no-cap`), length-fit |

## Every editing pair: editing-all-v1

The editing results paired the way `radon_rel18_all.jsonl` pairs its noisy
scores: one score per program, its mean over sequences and repetitions,
and every pair of programs whose scores differ (scorer rule `aggregate`,
no per-task cap, min step gap 1). Added on 2026-11-17 with:

```bash
.venv/bin/python -m harness report --config configs/rtx5070_train_aggregate.yaml \
    --out runs/rtx5070_pc/dpo/editing_all
.venv/bin/python scripts/match_pairs.py runs/rtx5070_pc/dpo/editing_all/preferences.jsonl \
    runs/rtx5070_pc/dpo/editing_all/preferences.jsonl runs/rtx5070_pc/dpo/dpo_all.jsonl \
    --model /home/pc/models/hf/Qwen2.5-Coder-7B-Instruct
for c in dev eval; do
  .venv/bin/python -m harness report --config configs/rtx5070_${c}_aggregate.yaml \
      --out /tmp/agg2_$c
  cp /tmp/agg2_$c/preferences.jsonl runs/rtx5070_pc/dpo/editing_${c}_all.jsonl
done
.venv/bin/python -m harness.datasets add editing-all-v1 runs/rtx5070_pc/dpo/dpo_all.jsonl \
    runs/rtx5070_pc/dpo/editing_dev_all.jsonl runs/rtx5070_pc/dpo/editing_eval_all.jsonl
```

| File | Pairs | What it is |
|---|---:|---|
| `dpo_all.jsonl` | 634 | **the training pairs of dpo_all**: every unequal pair on the 36 train tasks (none was too long to train on) |
| `editing_dev_all.jsonl` | 98 | the base writer's dev-task pairs (7 tasks), for testing; never trained on |
| `editing_eval_all.jsonl` | 298 | the base writer's eval-task pairs (16 tasks), for testing; never trained on |

## The rules

- **Files are never replaced.** Writing different content under a name a
  dataset already has is refused. A changed version goes in a new dataset
  (`train-v2`, `train-v3`), so a result trained on `train-v1` always points
  to the same data. Running the same command again and getting the same
  file is fine: nothing changes.
- **No large files.** Anything over 50 MB is refused, since GitHub warns
  about files that big. Stores never belong here.
- **Don't edit `MANIFEST.json` by hand.** For each file it records the
  `sha256`, `bytes` and `rows` (lines of a `.jsonl` file), the command that
  made it (paths inside the repository shown relative to `harness/`, your
  home directory as `~`, so no personal path ends up in git), the
  `git_commit` and `git_dirty` at the time, and when it was `created` (UTC).
- **Checked in CI.** `tests/test_datasets.py` fails if a file no longer
  matches its manifest, or if a folder holds a file the manifest doesn't
  list. To check by hand: `.venv/bin/python -m harness.datasets verify`.
