Let several transfers in `vault.py` be made in one call that succeeds or
fails as a whole, for example when the seeds for one planting are gathered
from several drawers.

- Add `SeedVault.transfer_many(transfers) -> int`. `transfers` is a `list`
  of `(variety, from_drawer, to_drawer, count)` tuples. The call makes the
  transfers in list order, each exactly as `transfer` would with the same
  arguments, and returns how many packets it moved in total.
- Each transfer sees the effect of the ones before it in the list: a drawer
  may pass on packets that an earlier transfer in the same call brought to
  it. The counts afterwards are the same as after calling `transfer` once
  per tuple, in list order.
- If any transfer in the list would raise (`KeyError` or `NotEnoughSeeds`,
  as `transfer` does at that point), `transfer_many` raises the error of
  the first transfer that fails and changes nothing at all: the transfers
  before it in the list are not made either.
- An empty list is allowed: nothing changes and it returns 0.
- What happens when `transfers` is not a list of 4-item tuples, or holds a
  transfer that `transfer` leaves unspecified (a count of 0 or less, or the
  same drawer on both sides), is unspecified.

All existing behavior must keep working.
