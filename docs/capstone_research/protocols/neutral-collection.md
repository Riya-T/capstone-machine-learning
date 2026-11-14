# Fresh preference-label validation

## Question

Can two initially correct neutral teacher outputs support a repeatable
preference on different requests drawn from the same declared mix?

Use two new study-only tasks. Reward Wallet models customer credits with
a nonnegative balance and an ordered operation history. Repair Queue
models jobs with ordered creation and constrained state transitions.
These contracts and changes are new to this study. They are outside the
team task directory and are ineligible as evaluation data for a model
trained on them.

## Fixed mix and schedule

Give equal weight to atomic batch operations and historical corrections.
Each task has one discovery request and one different confirmation request
per category. The requests are independent and always start from the
unchanged initial program. Confirmation keeps the same parents and uses
new requests and seeds.

| Category | Reward Wallet discovery / confirmation | Repair Queue discovery / confirmation |
| --- | --- | --- |
| Atomic batches | Post a batch of credits and debits / move credits between members | Start several jobs / finish several jobs |
| Historical corrections | Reverse an operation / revise an operation amount | Rename a job / reopen a finished job |

One category contains changes that publish several changes together or
leave the entire state alone. The other contains changes to an existing
entry that must preserve related observable state. The category weights
describe this bounded study. No real-world request frequencies are known.

Generate four neutral teacher starts per family in round-robin order,
maximum eight hosted calls. Use gpt-6.1-sol medium and the established
workspace worker. Recheck the weekly window before and after each call.
Use a 60%-used ceiling and a maximum increase of 10 percentage points
from the observed start. The inherited guard adds a two-point buffer and
twice the maximum observed per-call increase, with a two-point minimum.
Do not regenerate failed or equivalent starts. Group all passing
implementations based on executable state ownership, validation, and
update paths. Use the lowest-numbered representatives of the first two
different groups. Require both unchanged starts to pass the private
initial oracle before editing.

## Editor and scoring

Reuse the isolated Qwen3-8B Q8_0 editor with the previous exact settings
and complete-workspace budget-draft policy. Compare both parents within
each request and seed block. Counterbalance order. Run three matched
blocks for each discovery request, maximum 24 local edits. Open three
matched blocks per new confirmation request only on a task that clears
discovery and saved-artifact review, maximum 24 further local edits.
Use a single six-hour local window. Keep original per-attempt limits.
The editor sees only the current request, initial contract, initial code,
and public checks. No access to private feedback or other outcomes.

A checkpoint passes if all private new-feature, preserved initial and
interaction tests pass. Keep every terminal status and raw response.
Executable drafts recovered at budget exhaustion are scored, with the
budget reason preserved. A nonsubmission has no observed behavioral
result. Before inference certify each reference, catch an explicit
incorrect control per request and initial contract, and verify that each
unchanged reference fails each new feature suite.

For each candidate direction, require a strict lead in both categories,
at least three additional successful checkpoints out of six, and a lead
in at least two of three matched blocks. Compute the rule for both the
observed scores and every binary assignment to budget-dependent attempts.
An infrastructure failure or unscored artifact blocks the gate for that
task. The direction must survive all budget assignments. Confirmation
must reproduce the discovery direction under the same rule, on the new
requests. Replay every behavioral artifact and investigate failures.
Require executable evidence and no unresolved initial-correctness,
boundary, or scoring confound before admitting a pair. Each admitted pair
is conditional on this editor and request mix. This pilot is too small to
estimate the general label error rate or train a writer.

Freeze task bytes, writer prompts, editor settings, protocol and seeds
before teacher generation. Preserve prior evidence and commit locally.
