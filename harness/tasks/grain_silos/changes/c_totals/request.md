Add totals to `silos.py`, so the cooperative can see how full each silo is
and how much of each grain it has in all.

- Add `Silos.get_total(silo) -> int`, which returns the tonnes of all
  grains together in the silo: 0 for an empty silo. It raises `KeyError`
  for a silo that is not in use.
- Add `Silos.get_grain_total(grain) -> int`, which returns the tonnes of
  that grain in all the silos in use together: 0 when no silo holds any.
- Both always follow the current amounts: grain moved by `blend_into` or
  `demolish_silo` counts in the silo it was moved into. Neither method
  changes anything.

All existing behavior must keep working.
