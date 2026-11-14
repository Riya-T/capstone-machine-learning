# Editing results and why the labels were withheld

## First verified starting-program comparison

All six teacher starts passed. Pantry Inventory had three initial
implementation groups. Playlist Manager had one and did not enter
editing. The list and deque Pantry implementations entered the
comparison. The list-based start led on expiry then categories. An
advantage across both sequences remained unconfirmed.

The Pantry roster contained 24 planned checkpoint slots. Twelve
passed, three reached a behavioral failure, four stopped at the token
budget, and five later checkpoints were never reached. The separate
[Pantry outcome rows](data/pantry-trial.json) preserve these states.
[Protocol](protocols/verified-starting-programs.md)

## From collection to replication

The six-family collection started from 24 correct teacher-written
programs and produced zero confirmed families. Recipe Box's promising
direction did not repeat in confirmation. Ring Buffer did not meet the
numerical criterion. Four other families had incomplete behavioral
evidence under the original rule. The
[collection ledger](data/six-family-edits.json) retains the
original statuses, including budget stops and unreached steps.

I reconstructed 13 earlier stopped workspaces using saved replies
and ran them as separate diagnostics. All 13 were complete enough to
test. None passed the full private suite. Seven Robot Fleet drafts
failed to leave the robot unchanged after a rejected move. That
establishes a real behavior gap for those drafts. Their original
budget-stop outcomes remain recorded.

| Replication | First start | Second start | Decision |
| --- | --- | --- | --- |
| Stock Portfolio, sectors then profit | Stored balances 2/6 | Trade ledger 3/6 | Direction reversed on the other sequence |
| Stock Portfolio, undo then sectors | Stored balances 6/6 | Trade ledger 2/6 | Lead limited to this sequence |
| Feature Flags, groups then kill switch | Tuple per flag 4/6 | Split maps 6/6 | Same validation mistake repeated on the tuple start |
| Feature Flags, audit then groups | Tuple per flag 3/6 | Split maps 6/6 | The lead could vanish under the frozen draft sensitivity check |

All 45 reached outcomes replayed exactly. The denominators above are
planned checkpoint slots. The remaining three were never reached.
The [replication ledger](data/replication.json) keeps the observed
states and sensitivity decisions separate.

## Neutral and controlled Wallet

The neutral Reward Wallet starts each passed one of three edits in
each request category. All 12 outcomes replayed and neither start
qualified for confirmation. Repair Queue had one executable group
and did not enter editing.

| Wallet phase | Reverse ledger | Reverse stored | Revise ledger | Revise stored |
| --- | ---: | ---: | ---: | ---: |
| Controlled, original scoring | 1/6 | 4/6 | 0/6 | 1/6 |
| Controlled, saved-artifact diagnostic | 1/6 | 4/6 | 0/6 | 0/6 |
| Clarified contracts, fresh attempts | 1/4 | 2/4 | 4/4 | 4/4 |

The original stored-balance revision success raised `TypeError` for a
malformed identifier, while the contract calls for `ValueError`.
The stronger tests rejected it on the unchanged artifact. All 21
distinct complete intermediate revision drafts also failed at least
one of the combined suites.

In the follow-up, clear error rules and a public example accompanied
the stronger private checks. Every fresh revision passed. In the
reversal failure cases, some edits reserved a compensation ID before
validating funds or skipped the global ID check. Other edits left the
new compensation out of the map used for the next reversal. Focused
tests reproduced those defects. The changes in wording, public
feedback, scoring, and fresh draws make the follow-up a comparison
of whole workflows.

The [Wallet ledger](data/wallet.json) retains the neutral roster and
the diagnostic counts. The follow-up outcome rows and exact starting
programs are in the [Wallet pilot on main](../wallet_pair_pilot).
The [testbed note](../wallet_pair_pilot/testbed.md) explains how to use
these findings before collecting another labeled set.
