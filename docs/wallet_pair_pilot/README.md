# Reward Wallet preference pilot

**The revised setup made both designs reliably editable for one
request. It produced zero usable preference pairs.** The comparison
supports improving how the team specifies and tests changes before
collecting more preference labels.

| Request | Original ledger / stored balance | Follow-up ledger / stored balance |
| --- | --- | --- |
| Reverse a posting | 1/6 / 4/6 | 1/4 / 2/4 |
| Revise a posting | 0/6 / 1/6 | 4/4 / 4/4 |

The two correct starts use different representations. One calculates
the balance from a single posting ledger. The other stores it alongside
per-member history. Each edit starts with an unchanged program.
The two requests independently exercise balance and history consistency.

## Why the label was withheld

- The original stored-balance lead depended on its only revision pass.
  The unchanged edit raised `TypeError` for a malformed ID. The
  contract requires `ValueError`. The strengthened checks verified
  that problem, leaving **0/6 revisions per design** in the historical
  diagnostic. The original scores are retained.
- The follow-up explicitly named the errors, added a public example
  for each request, and expanded checks for malformed IDs, cross-member
  state, and historical balances. Both starts then passed every revision.
  This is a combined protocol comparison with fresh draws. It cannot
  isolate the effect of wording, public feedback, or randomness.
- The follow-up reversal advantage was **one success in four blocks**.
  It appeared in only one block. Neither start led on both requests.
  Three ledger reversals failed because they accepted an already used
  ID or reserved a new ID before validating funds. Two stored-balance
  reversals failed because they did not add the compensation to the
  lookup used by later reversals. These are observed editing defects.
  This one comparison cannot assign causation to the parent design.

All **40 original outcomes** across the two experiments replayed with
the same test results. In the follow-up, the 16 outcomes used 13
explicit submissions and three public-check fallbacks. The latter
all passed private tests. Five of the 16 submissions failed new behavior.
All preserved-behavior suites passed. The follow-up made 54 offline
Qwen3-8B Q8_0 requests. Neither experiment trained a model.

## What we can use

The follow-up is a worked example of testing labels before collection.
The result supports the team's proposed larger testbed pilot and gives
it a concrete test design. Specify the failure rules in each change,
publish a small example, and independently certify the private tests
before scoring. Then measure whether program rankings transfer to
different requests. This task does not estimate an effect for the team's
current writer or candidate population. Leave these outcomes out of
preference training. [Testbed proposal](testbed.md)

The exact starting files, initial contract, amended requests, targeted
tests, and frozen follow-up protocol are in [method](method). The
[compact outcome file](outcomes.json) preserves all planned attempts,
source hashes, seeds, private failure IDs, and replay status.
From the repository root, run:

```sh
python docs/wallet_pair_pilot/verify.py
```
