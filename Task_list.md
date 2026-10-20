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

- [ ] **5090 config** — A config for the real setup: the 7B writer on vLLM
  and the 14B editor on Ollama.
- [ ] **Set up the 5090** — Install the models and check the harness runs
  end to end on it.
- [ ] **Calibrate on dev tasks** — Tune the editor budget, the editor's turn
  history and the writer temperature until programs pass often enough and
  the editor's results spread out (some changes succeed, some fail).
- [ ] **Measure time per editing step** — Check the ~110 GPU-hour estimate.
- [ ] **Choose the pairing settings** — Pick the preference rule and pairing
  mode that give enough pairs (target 100–300).
- [ ] **Freeze the settings** — Commit the final config and stop changing it
  before collecting training data.

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

- [ ] **Evaluation code** — Run every method on the eval tasks and compute
  the scores, with confidence intervals by resampling task families.
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
- [ ] **Comment density** — Report how much each method's code comments.
- [ ] **Size-matched check** — Check whether gains come only from shorter
  code.
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
- [ ] **Plots** — Charts of the main results and costs.
- [ ] **Reproduction instructions** — README commands to rerun every result.
- [ ] **CI** — Run the CPU tests automatically on GitHub.
- [ ] **Release the adapters** — Publish the trained writer's adapters.
- [ ] **Final report** — Research question, methods, results and limitations.
- [ ] **Final presentation**
