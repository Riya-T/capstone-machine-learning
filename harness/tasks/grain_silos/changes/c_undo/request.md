Add an undo to `silos.py`, so that a mistake, such as blending a silo into
the wrong one, can be taken back.

- Add `Silos.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among the calls that change the silos:
  `add_silo`, `load`, `unload`, `blend_into`, `demolish_silo`, and every
  other method that changes the silos, including methods added by other
  changes. Each further `undo` goes one call further back.
- Undoing a call puts every amount, and the list of silos in its order,
  back to exactly what they were just before that call. A call that moved
  several grains is undone as a whole by one `undo`:
  - an undone `blend_into` puts all the grain it moved back into the silo
    it came from;
  - an undone `demolish_silo` brings the demolished silo back, with all its
    grain and at its original position in `get_silos()`, and takes that
    grain out of the silo it was moved into; its name is in use again;
  - an undone `add_silo` removes the silo, and its name may then be added
    again.
- A `blend_into` or `demolish_silo` that moved 0 tonnes is still a call:
  `undo` reverses it like any other (an undone `demolish_silo` of an empty
  silo brings the silo back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `SiloError` and changes nothing.

All existing behavior must keep working.
