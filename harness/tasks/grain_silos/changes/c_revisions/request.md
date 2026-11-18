Several people at the cooperative work on the same silos from different
offices. Let `silos.py` detect when a change is based on a state that
someone else has changed in the meantime.

- Add `class RevisionConflict(SiloError)` to `silos.py`.
- Add `Silos.get_revision() -> int`. It is 0 for a new `Silos` object and
  goes up by exactly 1 with every successful call that changes the silos:
  `add_silo`, `load`, `unload`, `blend_into`, `demolish_silo`, `seal`,
  `unseal`, `undo`, and every other method that changes the silos. It goes
  up by 1 per call, however much grain the call moves; a `blend_into` or
  `demolish_silo` that moved 0 tonnes counts too. Calls that raise, and the
  `get_` methods, leave it unchanged.
- Every method that changes the silos, including `seal`, `unseal` and
  `undo`, takes a new keyword argument `expected_revision=None`. When it is
  not `None` and is not equal to `get_revision()`, the call raises
  `RevisionConflict` and changes nothing. When it is equal, or `None`, the
  call works as before.
- `undo` never puts an older revision number back: like every other
  change, it raises the revision by 1, while it still restores the exact
  earlier silos, grain and seals.
- When a call has a revision conflict and another problem, which error is
  raised is unspecified.

All existing behavior must keep working.
