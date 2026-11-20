# Foresight gates on the history suite's dev tasks

Can the writer, shown a task's later change requests while its training
samples are drawn, write first versions that the editor extends further?
If so, a writer trained on those samples with the plain prompt would learn
to prepare for change without being told the design (context distillation;
`src/harness/foresight.py`). Each variant was gated on the 4 dev tasks of
the history suite (choir_sections, photo_albums, seed_vault, tram_lines),
16 samples per task, against the base writer's plain programs, with the
editor settings of the history-suite eval (Qwen2.5-Coder-14B, 5 turns, 1
trial per sequence, 2 sequences of 3 changes, up to 8 passing programs per
task edited).

The rule was fixed in each config before its run: train foresight writers
if the programs that don't implement a later change early score at least
+0.1 changes per sequence above the plain programs (point estimate), and
at least half as many samples pass the initial checks. A program
implements a later change early when it defines a function, method, class
or keyword parameter that only a later change's request names
(`foresight.implements_later_change`; it flags none of 500 plain programs).

## The variants

| Config | Hinted samples are asked for | Then |
|---|---|---|
| `rtx5070_hist2_dev_foresight.yaml` | a first version, shown the later changes, "do not implement any of them now", made easy to extend | – |
| `rtx5070_hist2_dev_prune.yaml` | the final version, with every later change implemented | the writer deletes what only the changes need, keeping the rest (`writer.prune_prompt`) |
| `rtx5070_hist2_dev_prune_names.yaml` | the same final version (cached answers) | code cuts every function, method and class only a later change names, and every one-line guard raising one of those classes (`writer.prune_names`, `foresight.prune_program`) |

The code-deletion variant was added after looking at the first pared-down
seed_vault programs of the writer-deletion run, before any had been
edited: the writer had deleted the history along with undo.

## Results

| Variant | Samples passing initial checks | Early implementers among them | Edited | Changes before first failure, against plain (2 tasks) | Rule |
|---|---:|---:|---:|---|---|
| Plain prompt | 30 of 64 | 0 | 24 | – | – |
| Don't implement them yet | 14 of 64 | 13 | 0 left | no program to compare | fails |
| Final version, writer deletes | 15 of 64 | 0 | 15 | −0.06 (−0.12 to +0.00) | fails |
| Final version, code deletes | 17 of 64 | 0 | 15 | −0.06 (−0.12 to +0.00) | fails |

Per task (passing samples; mean score of the edited programs):

| Task | Plain | Don't implement yet | Writer deletes | Code deletes |
|---|---|---|---|---|
| choir_sections | 8/16; 0.50 | 0/16; – | 1/16; 0.50 | 1/16; 0.50 |
| photo_albums | 8/16; 0.50 | 0/16; – | 0/16; – | 0/16; – |
| seed_vault | 14/16; 0.38 | 12/16 (11 early); – | 8/16; 0.25 | 10/16; 0.25 |
| tram_lines | 0/16; – | 2/16 (2 early); – | 6/16; 0.50 | 6/16; 0.50 |

Design classes of the passing programs (`scripts/design_classes.py`):

| Variant | Log (operation history) | Snapshot (copy of the state) | Plain |
|---|---:|---:|---:|
| Plain prompt | 0 | 0 | 30 |
| Don't implement them yet | 13 | 0 | 1 |
| Writer deletes | 1 | 0 | 14 |
| Code deletes | 17 | 0 | 0 |

- **Told not to implement the changes, the writer implements them.** The
  names it defines early are undo, seal, unseal, get_sealed, transfer_many
  and LineFull. On choir_sections and photo_albums no sample passes; the
  programs carry undo stacks, capacity limits and extra error classes, and
  the checks the first specification asks for go wrong among them.
- **photo_albums fails in every variant** (plain: 8 of 16). With the longer
  prompt the writer looks for a photo name in the list of the albums'
  photo lists (`photo in self.albums.values()`), so the checks on names in
  use fail.
- **Keeping the history does not help the editor.** Every code-pared
  program keeps its undo log, yet scores no higher than plain programs.
  Even the first variant's programs that already contained an undo (and
  more) score 0.44 on seed_vault against 0.38 for plain programs, the one
  task where both were edited.
- Per sample over the 4 tasks (post hoc; a task without an edited program
  counts 0): plain 0.21, code deletion 0.09.

No foresight writer was trained. The original testbed's gate
(`rtx5070_pc_foresight.yaml`) was stopped 10 minutes in, after the
history-suite result; `rtx5070_pc_prune.yaml` was not run.

## Runs

- Plain programs edited: run 20261119T234540Z-80821b (15:45 to 17:04).
- Don't implement yet: run 20261120T010451Z-fd5346 (17:04 to 17:51).
- Writer deletes: run 20261120T021447Z-7f7105 and its editing run (18:14
  to 19:25).
- Code deletes: 19:25 to 20:11.
- No infrastructure errors in any of them.

## Reproduce

From `harness/`, inside WSL:

```
uv run python -m harness collect --config configs/rtx5070_hist2_dev.yaml
for v in foresight prune prune_names; do
  uv run python -m harness collect --config configs/rtx5070_hist2_dev_$v.yaml
  uv run python scripts/foresight_gate.py --plain configs/rtx5070_hist2_dev.yaml \
      --foresight configs/rtx5070_hist2_dev_$v.yaml
done
(cd scripts && PYTHONPATH=. uv run python design_classes.py \
    --writer plain=../configs/rtx5070_hist2_dev.yaml \
    --writer foresight=../configs/rtx5070_hist2_dev_foresight.yaml \
    --writer pruned=../configs/rtx5070_hist2_dev_prune.yaml \
    --writer cut=../configs/rtx5070_hist2_dev_prune_names.yaml)
```
