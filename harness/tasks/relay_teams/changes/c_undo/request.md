Add an undo to `relay.py`, so a mistake in making up the teams can be
taken back.

- Add `RelayMeet.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among `add_team`, `add_runner`,
  `remove_runner`, `move_runner`, `merge_teams` and `withdraw_team`, and
  any other method of `RelayMeet` that changes the teams or their lineups
  (including methods added by other changes). Each further `undo` goes one
  call further back.
- Undoing a call puts every lineup, in running order, and the list of teams
  in its order, back to exactly what they were just before that call. A
  call that does several things is undone as a whole by a single `undo`:
  - an undone `move_runner` puts the runner back in their old team at their
    old position;
  - an undone `merge_teams` brings the merged team back, with its lineup in
    order and at its original position in `get_teams()`, and takes those
    runners out of the team they were merged into; its name is in use
    again;
  - an undone `withdraw_team` brings the team back at its original position
    with its whole lineup; its name is in use again and its runners are in
    it again;
  - an undone `remove_runner` puts the runner back at their old position;
  - an undone `add_runner` takes the runner out of the lineup again;
  - an undone `add_team` removes the team, and its name may then be added
    again.
- A `merge_teams` or `withdraw_team` of an empty team is still a call:
  `undo` reverses it like any other (the empty team comes back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `RelayError` and changes
  nothing.

All existing behavior must keep working.
