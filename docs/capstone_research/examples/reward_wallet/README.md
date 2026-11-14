# Run the Wallet starting-code example

From the repository root, run:

```sh
python docs/capstone_research/examples/reward_wallet/compare_initial.py
```

The command compares both published starting implementations to a small
behavioral reference built from the [initial contract](initial.md). It
tries 512 ordered three-operation traces. It checks the returned error
type, balance and history after every operation, including duplicate
operation IDs across members, overdrafts and rejected inputs.

This is a new public reproduction for reviewing the starting code. The
reported experiment used its frozen evaluation suite and schedules.
You can [verify the saved experiment totals](../../README.md#verify-the-tables)
separately.
