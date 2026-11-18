The displays in our trams fit only 6 stops, so a line in `trams.py` may
have at most 6 stops.

- Add `class LineFull(TramError)` to `trams.py`.
- `add_stop` on a line that already has 6 stops raises `LineFull` and
  changes nothing.
- `merge_lines(first, second)` raises `LineFull` and changes nothing (both
  lines keep their stops, and `second` is not removed) when `first` would
  end up with more than 6 stops. Only the stops that `first` does not have
  yet are added, so only they count: the merge is allowed whenever `first`
  ends up with 6 stops or fewer.
- `remove_stop` and `close_stop` only take stops off lines, so the limit
  never refuses them. A full line has room again once a stop is taken off
  it.
- When a call has another problem as well (a line not in use, the same line
  twice, a stop the line already has), which error is raised is
  unspecified, but the call still changes nothing.
- `undo` works as before: it restores exactly the state before the undone
  call, which always kept to the limit, so `undo` never raises `LineFull`.

All existing behavior must keep working.
