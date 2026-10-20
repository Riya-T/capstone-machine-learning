Group teams into divisions in `season.py`.

- `add_team` takes a new keyword argument `division=None`: the name of the
  team's division as a non-empty `str`, or `None` for a team in no division.
  Anything else raises `ValueError` and adds nothing.
- `get_standings` takes a new optional argument `division`. When it is
  given, only the teams in that division are returned, ranked the same way.
  A division that no team belongs to raises `KeyError`. Without it, every
  team is returned as before.
- `get_record` returns three new keys, `division_wins`, `division_losses`
  and `division_ties`: the results of the team's games against other teams
  in its own division. A team with no division has no division games.

All existing behavior must keep working.
