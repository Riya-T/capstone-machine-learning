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

Pairs are only ever made within one task, so pairs from different stores
can be put in one file. One person joins everyone's datasets and filters
the result once, with the same settings as before:

```bash
cat data/train-v1/pairs_cap8_all.jsonl data/pairs-*-v1/preferences.jsonl \
    > runs/combined.jsonl
.venv/bin/python scripts/filter_pairs.py runs/combined.jsonl --dataset train-v2 \
    --min-rep-wins 2 --drop-cosmetic
```

`train-v2` then holds the joined file as `pairs_unfiltered.jsonl` and the
training pairs as `pairs.jsonl`.

**Check before joining.** `cat` only puts the files together. Until a
`merge` command does these checks (planned for when all the data is in):

- Every file should have the same `settings_hash`. Rows without a `source`
  (`train-v1`) can't be checked: they were made with
  `configs/rtx5070_train.yaml`.
- If two people collected the same task, the joined file can hold the same
  pair twice, and more pairs for that task than the scorer's per-task cap
  (8). Such a task then weighs more in training.

To list each file's settings hash and pairs per task:

```bash
for f in data/pairs-*/preferences.jsonl; do
  echo "$f"
  .venv/bin/python -c 'import json, sys, collections
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
print(" settings:", sorted({r.get("source", {}).get("settings_hash", "none")[:12] for r in rows}))
print(" pairs per task:", dict(collections.Counter(r["task_id"] for r in rows)))' "$f"
done
```

## The first training set: train-v1

The first 229 pairs and the files trained on them were made on Karin's PC
(store `runs/rtx5070_pc/`, config `configs/rtx5070_train.yaml`), before
`--dataset` existed. They are not in the repository yet. To add them, Karin
runs on that PC:

```bash
.venv/bin/python -m harness.datasets add train-v1 \
    runs/rtx5070_pc/dpo/pairs_cap8_all.jsonl \
    runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl \
    runs/rtx5070_pc/dpo/radon_cap8_all.jsonl \
    runs/rtx5070_pc/dpo/radon_matched.jsonl \
    runs/rtx5070_pc/dpo/sft_programs.jsonl
```

`add` keeps each file's name, so `train-v1` uses the old names, not the
ones in the table above:

| train-v1 file | What it is | Same as, in later datasets |
|---|---|---|
| `pairs_cap8_all.jsonl` | all 229 scorer pairs, up to 8 per task | `pairs_unfiltered.jsonl` |
| `pairs_cap8_f23_nocosm.jsonl` | **the 160 pairs dpo3 was trained on** (won in at least 2 of 3 reps, cosmetic pairs dropped) | `pairs.jsonl` |
| `radon_cap8_all.jsonl` | every Radon-ranked pair | `radon_all.jsonl` |
| `radon_matched.jsonl` | the static-ranking baseline's 160 pairs | `radon_matched.jsonl` |
| `sft_programs.jsonl` | the correctness-only baseline's 201 programs | `sft_programs.jsonl` |

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
