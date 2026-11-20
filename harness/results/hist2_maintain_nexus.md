# Maintainability-prompt baseline on the history suite (Nexus cluster)

Run on 2026-11-20 on the UMIACS Nexus class cluster. This is the
history-suite version of the maintainability-prompt baseline of the original
testbed (`maintainability_prompt_eval.md`). It asks whether simply telling the
writer to write maintainable code gives the gain of the DPO+NLL writer
(`hist2_eval.md`).

**Result:** no gain. On the same 9 eval tasks, the editor completes 0.31
changes before the first failure on its programs, the same as the original
writer's 0.31 on the PC. 58% of its samples pass the initial tests, against
64% for the original writer on the PC. The comparison is not matched (see
Caveats), so no intervals are given.

## What was run

- **Writer:** Qwen2.5-Coder-7B-Instruct (Q4, Ollama), temperature 0.4, 16
  samples per task. The prompt is `prompts/writer_maintainable_v1.md`, which is
  `writer_v1.md` plus one paragraph:

  > Write clean, maintainable code. This module will be changed many times
  > later, to add features and to change its rules, so make it easy to read
  > and easy to change.

  There is no training and no design hint.
- **Editor:** Qwen2.5-Coder-14B-Instruct (Q4, Ollama), `editor_v3.md`, 5 turns
  per change, one trial per sequence.
- **Tasks:** the 10 history-suite eval tasks, all passing `validate-tasks`
  under Apptainer before the run.
- **Settings:** everything else is as in `rtx5070_hist2_eval.yaml`, including
  the 180 s sandbox timeout and up to 8 passing programs per task edited.
- **Config:** `configs/nexus_hist2_eval_maintain.yaml`, which extends
  `configs/nexus_hist2_eval.yaml`.
- **Store:** `runs/nexus_hist`.
- **Job:** Slurm job 8484561 on tron46, one RTX A5000 (24 GB), 8 CPUs, 32 GB.
  It ran 6 h 29 min (00:26 to 06:55), exit 0.
  - Ollama v0.40.5, with flash attention and an 8-bit KV cache as on the PC.
  - Apptainer sandbox, image `apptainer:sha256:cee0d1c548ab`.
  - Git commit 90a7e1d. The two `nexus_hist2_*` configs were not yet
    committed.
  - Log: `runs/slurm-8484561.out` (Ollama: `runs/ollama-8484561.log`).
- **Model weights:** the writer is blob
  `sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463`
  (`ollama list` id `dae161e27b0e`). The editor is blob
  `sha256-ac9bc7a69dab38da1c790838955f1293420b55ab555ef6b4615efa1c1507b1ed`
  (id `9ec8897f747e`).
- **Run totals:** 688 model calls, 160 samples, 160 initial checks, 170
  editing steps, 0 infra errors.

## Results

### Per task

| Task | Samples passing | Programs edited | Trials | Changes before first failure | First change works | Whole sequence works |
|---|---:|---:|---:|---:|---:|---:|
| bike_docks | 8 / 16 | 8 | 16 | 0.06 of 3 | 6% | 0% |
| canal_locks | 10 / 16 | 8 | 16 | 0.00 of 3 | 0% | 0% |
| coin_vaults | 7 / 16 | 7 | 14 | 0.07 of 3 | 7% | 0% |
| grain_silos | 7 / 16 | 7 | 14 | 0.43 of 3 | 43% | 0% |
| museum_galleries | 6 / 16 | 6 | 12 | 0.25 of 3 | 25% | 0% |
| recipe_binder | 1 / 16 | 1 | 2 | 0.50 of 3 | 50% | 0% |
| rehearsal_setlists | 7 / 16 | 7 | 14 | 0.50 of 3 | 50% | 0% |
| server_racks | 6 / 16 | 6 | 12 | 0.50 of 3 | 50% | 0% |
| spare_parts | 16 / 16 | 8 | 16 | 0.81 of 3 | 56% | 12% |
| tour_itineraries | 16 / 16 | 8 | 16 | 0.12 of 3 | 12% | 0% |
| **All 10 tasks** | **84 / 160 (53%)** | **66** | **132** | **0.33** | **30%** | **1%** |
| **9 tasks (no recipe_binder)** | **83 / 144 (58%)** | **65** | **130** | **0.31** | **28%** | **1%** |

The 9-task row matches the task set of `hist2_eval.md`. recipe_binder is
left out there because the original writer and the correctness-only control
have no passing program on it.

### Editing steps

| | Steps | Succeed | Run out of turns | New feature fails |
|---|---:|---:|---:|---:|
| Maintainability prompt | 170 | 40 (24%) | 75 (44%) | 55 (32%) |

On sequence s1, which starts with undo, 1 of 66 programs got its first
change done: a spare_parts program that completed all 3 changes.

### Against the other history-suite writers (not matched)

The other rows are the PC results of `hist2_eval.md`, on the same 9 tasks.

| Writer | Machine | Changes before first failure | First change works | Whole sequence works | Samples passing initial tests |
|---|---|---:|---:|---:|---:|
| Original writer | PC | 0.31 | 31% | 0% | 64% |
| **Maintainability prompt** | **cluster** | **0.31** | **28%** | **1%** | **58%** |
| Correctness-only (SFT) | PC | 0.33 | 30% | 0% | 53% |
| DPO+NLL D, seed 42 | PC | 0.55 | 41% | 6% | 42% |
| DPO+NLL D, seed 43 | PC | 0.73 | 46% | 11% | 53% |

Every row is over the same 9 tasks. On all 10 tasks the original writer
passes 58% on the PC (`hist2_eval.md`) and the maintainability prompt 53%
here.

| Editing steps | Succeed | Run out of turns | Undo-first successes |
|---|---:|---:|---:|
| Original writer (PC) | 23% | 47% | 0 of 69 |
| Maintainability prompt (cluster) | 24% | 44% | 1 of 66 |
| DPO+NLL D, seed 42 (PC) | 38% | 28% | 7 of 51 |
| DPO+NLL D, seed 43 (PC) | 46% | 27% | 14 of 64 |

## Reading

- **No gain.** Asking for maintainable code does not make the writer's
  programs easier for the editor to change on the history suite. The editor
  gets as far as on the original writer's programs, gets stuck as often, and
  almost never manages undo as the first change.
- **This doesn't depend on the machine difference.** The DPO+NLL writer's gain
  (+0.24 and +0.43) is far larger than anything that difference could plausibly
  cause. So the gain is not something the prompt gives for free.
- **Correctness:** slightly fewer samples pass the initial tests (58% against
  64% on the 9 tasks; 53% against 58% on all 10). The prompt's effect can't
  be told apart from the machine difference without the original writer on
  the cluster.
- **Same as the original testbed.** There the maintainability prompt also
  changed nothing (+0.00, −0.10 to +0.10; `maintainability_prompt_eval.md`).

## Caveats

- **Not a matched comparison.** The other writers ran on the PC: an RTX
  5070, Docker sandbox and the PC's Ollama build. This run used an A5000,
  Apptainer and Ollama v0.40.5. The model weights are the same Ollama library
  files, and Ollama ran with the PC's flash-attention and KV-cache settings.
  But the GPU, the sandbox and possibly the Ollama version differ, so the same
  seed does not give the same programs. Paired intervals need the original
  writer on the cluster too (`configs/nexus_hist2_eval.yaml`, not yet run).
- **Same limits as `hist2_eval.md`:** 9 tasks, one trial per sequence, and
  at most 8 edited programs per task.

## Reproduce

From `harness/` on the submission node:

```bash
sbatch --time=24:00:00 \
    --export=ALL,OLLAMA_FLASH_ATTENTION=1,OLLAMA_KV_CACHE_TYPE=q8_0 \
    scripts/collect_nexus.sbatch configs/nexus_hist2_eval_maintain.yaml
```

The summary is computed on a compute node:

```bash
srun --partition=class --account=class --qos=default --cpus-per-task=4 --mem=8gb \
    uv run python scripts/eval_summary.py --config configs/nexus_hist2_eval_maintain.yaml
```

To get the matched comparison, run the original writer the same way with
`configs/nexus_hist2_eval.yaml`, then compare the two on a compute node:

```bash
uv run python scripts/eval_compare.py --base configs/nexus_hist2_eval.yaml \
    --other configs/nexus_hist2_eval_maintain.yaml
```
