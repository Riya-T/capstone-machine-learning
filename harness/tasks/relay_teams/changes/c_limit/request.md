Let a meet in `relay.py` limit how many runners a team's lineup may hold,
for example 4 for a 4 x 400 m relay.

- `RelayMeet(max_runners=None)` takes an optional limit, the same for every
  team. `None` (the default) means lineups have no limit. Otherwise the
  limit must be an `int` greater than 0; anything else raises `ValueError`.
- Add `RelayMeet.get_max_runners() -> int | None`, which returns the limit.
- Add `class TeamFull(RelayError)` to `relay.py`.
- A lineup never holds more runners than the limit. Every call that puts
  runners into a team checks this before changing anything: `add_runner`,
  `move_runner` (the team the runner moves to), and `merge_teams` (the team
  merged into, which must have room for every runner of the other team). A
  call that would take a lineup over the limit raises `TeamFull` and
  changes nothing: no runner moves, and `merge_teams` does not remove the
  other team. Filling a lineup exactly up to the limit is allowed.
- Taking runners out is never limited: `remove_runner`, `withdraw_team`,
  and the team a runner leaves are not checked.
- When a call has another problem as well (a team not in use, a runner not
  in a team or already in one, the same team twice), which error it raises
  is unspecified.
- `undo` still restores the exact earlier state: an undone `merge_teams`
  brings the other team back with every one of its runners.

All existing behavior must keep working.
