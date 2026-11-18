Add two ways to look up one herb across every rack of `drying.py`, for
example to see how much sage is drying and where.

- Add `DryingRoom.get_total(herb) -> int`: the number of bundles of `herb`
  on all racks in use together; 0 for a herb that has no bundle on any
  rack.
- Add `DryingRoom.get_racks_with(herb) -> list[str]`: the names of the
  racks in use that hold at least one bundle of `herb`, in the order of
  `get_racks()`; `[]` when no rack holds any.
- A rack whose bundles of the herb have all been taken down or moved away
  is not listed and adds nothing to the total, and a dismantled rack never
  counts.
- Neither method raises for a herb that has never been hung, and neither
  changes anything.

All existing behavior must keep working.
