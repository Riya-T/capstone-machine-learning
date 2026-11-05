# Rough project task list

This is a  rough list of tasks we need to complete and is definitely subject to change.
## 1. Pipeline (done)


- [x] **Harness** — Built the pipeline in `harness/`: loading tasks, calling
  the models, running code in a sandbox, the editor loop, scoring and
  building preference pairs. Runs can stop and resume without repeating work.
- [x] **Harness tests** — Tests for every part of the harness, including a
  full run with a fake model.
- [x] **Editor fix** — Stopped the editor from repeating the same reply until
  it runs out of turns.
- [x] **Task-writing guide** — Instructions for writing a task, in
  `harness/tasks/README.md`.
- [x] **Task rules in the harness** — Every task must have the required
  planted bugs and use change types from the agreed list; eval-only change
  types can't appear in training or dev tasks.

## 2. Tasks (target: Oct 23)

- [ ] **Agree on the task list** — Write a one-line idea for each of the 60
  task families and assign them to people.
- [ ] **Assign splits** — Put each family in train (36), dev (8) or eval (16),
  keeping close variants in the same split.
- [x] **Agree on change types** — The list of change types and which are
  eval-only (in `configs/base.yaml`).
- [ ] **8 Dev Tasks** — Needed first for the calibration
- [ ] **36 train tasks** — Each passes `validate-tasks` and the writer check.
- [ ] **16 eval tasks** — Three changes per sequence, and every sequence uses
  at least one eval-only change type.

## 3. Real model setup and calibration 

- [x] **Real-model config** — `configs/rtx5070_pc.yaml`: the 7B writer and
  the 14B editor, both 4-bit in Ollama. The team moved from the planned
  RTX 5090 to an RTX 5070 (12 GB).
- [x] **Set up the RTX 5070** — Models installed; check the harness runs
  end to end with the 14B editor (`configs/rtx5070_editor_probe.yaml`).
- [x] **Calibrate on dev tasks** — Tune the editor budget, the editor's turn
  history and the writer temperature until programs pass often enough and
  the editor's results spread out (some changes succeed, some fail).
  Results in the README, "2026-11-01: settings frozen".
- [x] **Measure time per editing step** — Check the ~110 GPU-hour estimate.
  47 s per step on average; about 25 hours for the train tasks.
- [x] **Choose the pairing settings** — Pick the preference rule and pairing
  mode that give enough pairs (target 100–300). weak_dominance, all_pairs,
  at most 8 per task, a gap of at least 2 changes.
- [x] **Freeze the settings** — Commit the final config and stop changing it
  before collecting training data. `configs/rtx5070_train.yaml`.

## 4. Training data 

- [ ] **Collect editing runs** — Run the full pipeline on the train tasks.
- [ ] **Build preference pairs** — Check how many usable pairs we get and how
  often repeated runs agree.
- [ ] **Review a sample of pairs** — Read some winning and losing programs to
  make sure winners are really better code, and don't win because of
  comments that hint to the editor.

## 5. Training 

- [ ] **Training code** — DPO training of the writer with QLoRA adapters
  (TRL and PEFT).
- [ ] **Training tests** — Check the loss, which tokens are trained on, that
  the adapters change and that the original weights don't.
- [ ] **Choose training settings on dev tasks** — Learning rate, number of
  passes over the data, and DPO's beta.
- [ ] **Train our writer** — Later-edit training, with several random seeds.
- [ ] **Maintainability prompt** — Write the baseline prompt that asks for
  clean, maintainable code (otherwise identical to the normal prompt).
- [ ] **Correctness-only baseline** — Fine-tune the writer on its own programs
  that pass the initial tests.
- [ ] **Static-ranking baseline** — Train the writer to prefer programs with
  a higher Radon maintainability score (Radon settings chosen on dev tasks).

## 6. Evaluation 

- [x] **Evaluation code** — Matched plans, all main outcome measures, all-generated
  and initially-correct populations, phase-separated costs, comment/source/edit-size
  descriptions, dashboard and verified saved-only reports. The five-condition
  template records three training checkpoints per trained method separately.
  Real container smoke/isolation and Linux/Python 3.11 tests passed. See
  `harness/docs/evaluation-coverage.md` for the proposal checklist and limits.
  Actual trained-model evaluation remains separate work. Optional checkpoint summaries
  retain individual seeds and condition uncertainty on the observed checkpoint set.
  New runs freeze a planned checkpoint roster so missing methods/seeds are detectable.
  A separate paired analysis compares editing on aligned parents that both initially pass.
  See `harness/docs/evaluation-refinements.md` for commands and limitations.
- [ ] **Run all five methods** — Original model, maintainability prompt,
  correctness-only, static ranking and ours, on the held-out tasks with the
  same editor and budget.
- [ ] **Report the main numbers** — Fraction of changes completed before the
  first failure, how often the first version works, how often a whole
  sequence succeeds, how often old behavior breaks, and the cost (tokens and
  time).

## 7. Experimental variations 

- [ ] **Comments removed** — Rerun the evaluation with comments and
  docstrings removed before the editor sees the code.
- [ ] **Comment density** — Reporting code supports all generated and initially
  correct programs; collect and interpret the actual methods' results.
- [ ] **Size-matched check** — A saved-only sensitivity tool now records matching
  rules and family exclusions; freeze and apply the rule to the actual method results.
- [ ] **Shorter or fewer editing runs** — Train with pairs from 1 change
  instead of 2, and from 1 repetition instead of 3, to see if the cheaper
  signal works as well.
- [ ] **Second editor (stretch goal)** — Evaluate with a different, non-Qwen
  editor.

## 8. Analysis and write-up 

- [ ] **Generalization** — Compare results on familiar and eval-only change
  types, and on new task families.
- [ ] **Error analysis** — Sort failed changes by cause: task too hard, bug in
  the first program, editor mistake, unclear test, or infrastructure.
- [ ] **Plots** — PNG/SVG export is implemented; produce and interpret figures from
  the actual held-out results.
- [ ] **Reproduction instructions** — README commands to rerun every result.
- [x] **CI** — Run the CPU tests automatically on GitHub
  (`.github/workflows/tests.yml`).
- [ ] **Release the adapters** — Publish the trained writer's adapters.
- [ ] **Final report** — Research question, methods, results and limitations.
- [ ] **Final presentation**
