Let each section in `choir.py` have a limit on how many singers it may
hold, for example because the stage has room for only so many sopranos.

- Add `Choir.set_limit(section, limit)` and
  `Choir.get_limit(section) -> int | None`. Both raise `KeyError` for a
  section that is not in use.
- `limit` is either `None`, meaning no limit, or an `int` of at least 1.
  A limit of 0 or less raises `ValueError` and changes nothing. Each call
  replaces the section's earlier limit.
- Every new section starts with no limit (`None`).
- Add `class SectionFull(ChoirError)` to `choir.py`.
- Every call that puts singers into a section checks its limit:
  `add_singer`, `move_singer` (the section `to_section`), and `move_all`
  and `merge_sections` (the section `into`). If the section would then
  hold more singers than its limit, the call raises `SectionFull` and
  changes nothing.
- `move_all` and `merge_sections` check all of the source's singers
  together: either they all fit into `into`, or none of them moves (and
  `merge_sections` does not remove the source section).
- A limit does not affect the singers already in the section: setting a
  limit below the number of singers already there is allowed. They stay,
  and can be removed or moved out as before, but nobody can join until the
  section has fewer singers than its limit.
- When a call would also raise `KeyError`, `ValueError` or `ChoirError`
  for another reason, which error it raises is unspecified.
- No other method checks the limit. Taking singers out of a section
  (`remove_singer`, or moving them out with `move_singer`, `move_all` or
  `merge_sections`) is never refused.
- `undo` still puts the choir back exactly as it was before the call it
  reverses, including every section's limit: `set_limit` changes the
  choir, so it is recorded like the other such calls, and `undo` itself
  never checks a limit or raises `SectionFull`.

All existing behavior must keep working.
