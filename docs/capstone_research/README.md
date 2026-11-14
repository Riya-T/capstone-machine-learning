# Capstone research evidence

This branch extends the [Wallet pilot on main](../wallet_pair_pilot/README.md)
with the work that led to it. The question was whether two initial programs
that satisfy the same specification lead to repeatably different outcomes
when an editor receives new requirements.

We found that a stronger writer can supply correct starting programs.
In a matched six-family comparison, the teacher produced 24 of 24 fully
correct programs and the local writer produced 8 of 24. A separate
public-check selection experiment moved from 8 of 24 to 11 of 24.
Neither experiment establishes improvement from training.

The editing runs produced real differences on some changes. Those
differences did not meet the criteria for new preference-training pairs.
Stock Portfolio reversed direction across change sequences. Feature Flags
showed a split-map advantage that was sensitive to unfinished drafts.
In the controlled Wallet study the stored-balance design's apparent
lead across two requests depended on a revision that failed an added
correctness check. With explicit error behavior and a public example,
both designs passed every later Wallet revision.

| Section | Included evidence |
| --- | --- |
| [Candidate sourcing](candidate-sourcing.md) | Teacher and local correctness, public-check selection, executable diversity |
| [Editing and replication](editing.md) | Six-family collection, Stock Portfolio and Feature Flags, neutral and controlled Wallet results |
| [Protocols](protocols) | Selected written protocols and representative initial source |
| [Structured outcomes](data) | Allowlisted table fields, per-trial outcomes and an export manifest |
| [Runnable Wallet example](examples/reward_wallet/README.md) | Checks both starting programs against 512 small traces |

## Verify the tables

From the repository root, run:

```sh
python docs/capstone_research/verify.py
```

This reads JSON and reproduces the tabulated counts without requiring
the model, Docker, or an account. The export manifest records the exact
hashes of the selected original Git blobs and of the projected files.
The source revision is kept in a separate local archive. Full raw
generations, account records, machine-specific paths, and additional
private evaluation material are held there. The two branches carry
different commit histories. The preserved local archive is needed for
a complete replay of the original experimental environment.

The reported task sets, scoring rules, and editor settings differ by
phase. Use the results within their study, preserve abstentions, and
keep these tables outside training datasets. The team’s aggregate
results are available in the [existing diagnostics](../../harness/results/diagnostics.md).
