Add an injured list to `roster.py`. Injured players stay on the roster, but
their salary no longer counts against the salary cap.

- Add `Roster.place_on_injured_list(name)`, `Roster.activate(name)` and
  `Roster.is_injured(name) -> bool`. All three raise `KeyError` for a name
  that is not on the roster. New players are not injured. Putting an
  injured player on the list again, or activating a player who is not
  injured, does nothing.
- Add `Roster.get_cap_hit() -> int`: the total salary of the players who are not
  injured. `get_payroll()` still counts every player.
- The salary cap now applies to `get_cap_hit()`: `add_player` raises
  `CapExceeded` if the cap hit would go over the cap, and `get_cap_space()`
  returns the cap minus `get_cap_hit()`.
- `activate` raises `CapExceeded`, and the player stays injured, if bringing
  the player back would put the cap hit over the cap.
- `get_players()` and `get_player()` still include injured players. Removing an
  injured player works as before, and a player added again later starts out
  not injured.

All existing behavior must keep working.
