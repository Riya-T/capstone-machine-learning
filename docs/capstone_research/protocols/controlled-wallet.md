# Controlled Reward Wallet comparison

Can two certified implementations of the same initial contract give
repeatably different editor outcomes on two requests that exercise the
same state invariant? The two parents are study-authored controlled
interventions. Their outcomes estimate differences on these artifacts
for this editor. They provide no estimate of neutral writer yield.

## Parents and requests

Reuse Reward Wallet's unchanged initial contract and tests from fresh
label validation. Both parents validate the same values at the same
point and expose the same observable behavior. Parent A records
immutable postings in a single ordered ledger and computes balances
on read. Parent B keeps a balance and ordered postings per member, and
a separate global operation ID set. It updates all three on a successful
posting. The representation trades constant-time balance reads for
state that must stay synchronized. The parents are standalone and use
only the initial API. They contain no implementation of later requests.

Each independent edit starts from the original parent. Reverse appends
a compensating posting. Revise changes an existing posting in place.
Both exercise the connection between posting history, available balance
and valid debits. Reverse also enforces globally unique IDs and
one reversal per original. Revise also preserves all historical
nonnegative balance prefixes. Use the existing written requests and
suites unchanged. Their shared invariant does not make them identical
operations. Both requests have equal weight in this study.

Validate both parents on the frozen initial public and private suites
and on a separately authored finite-domain trace oracle. Validate
the oracle against both representation-specific broken controls.
Check the established references and broken controls for both requests.
Apply the independent oracle to preserved behavior at every edit.
Confirm unchanged parents fail the new-feature suites.

## Inference

Use the pinned offline Qwen3-8B Q8_0 editor, same runtime arguments,
prompt, sampling settings, 32,000 accounted tokens, maximum 16,384 per
generation, eight turns, and 600 seconds per edit. No hosted experimental
calls. Observe the subscription allowance before and after the study.
Use the latest previously verified workspace submission policy. A
complete applied Python draft at a budget stop can be behaviorally
scored, with the original termination reason retained. Privately score
new behavior, preserved behavior and the supplemental initial oracle.
The editor sees only the first contract, unchanged source, current
request, and public checks. No future request or private feedback.

Schedule six matched blocks per request using seed 202611132141.
Each block uses the same seed for both parents and a different seed
for the other request. Counterbalance parent and request order.
All 24 attempts are fixed in advance, in two halves of three blocks.
The full schedule fits one three-hour local window. Resume uses the
original deadline and never retries started requests without a receipt.
An infrastructure failure stops affected work. Code failures do not.
No extra attempts, repairs, replacement parents, or setting changes.

## Decision rule

Score each attempt as success only when every applicable suite passes.
To export a preliminary controlled pair, the same parent must lead
overall on both requests, lead by at least four successes out of 12,
and win more matched blocks than it loses. In each of the two halves
it must lead across the two requests taken together and cannot trail
on either request. Allow a within-half per-request tie. Require all
reached outcomes to be behavioral and replay exactly. The decision
must survive every possible binary assignment to budget-dependent
outcomes. A nonbehavioral artifact precludes a pair.

Review the saved defects using executable reproductions and confirm
there is no known starting correctness or scoring confound. Compare
across seeds and report the two halves separately. Any positive pair
is scoped to this controlled comparison. A stable direction on just
one request is useful diagnostic evidence and leaves the pair
unlabeled. A tie, no valid signal, or saturation completes the study
without training. Preserve all previous results and do not push.
