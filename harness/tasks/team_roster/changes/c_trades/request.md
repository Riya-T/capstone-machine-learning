Add trades to `roster.py`: some players leave and others join in a single
step, as in a real trade between two teams.

- Add `Roster.trade(outgoing, incoming)`. `outgoing` is a list of names of
  players on the roster. `incoming` is a list of `(name, position, salary)`
  tuples for the players who join. Either list may be empty.
- The trade is checked against the roster as it would be after the trade.
  It raises:
  - `KeyError` for an outgoing name that is not on the roster;
  - `ValueError` if a name appears twice in `outgoing`;
  - `ValueError` for an incoming player whose name, position or salary
    `add_player` would reject;
  - `RosterError` if an incoming name appears twice in `incoming`, or is
    the name of a player who stays on the roster;
  - `CapExceeded` if the roster after the trade would be over the salary
    cap, judged the same way `add_player` judges it.

  Which of these is raised when a trade has several problems is
  unspecified.
- A player who leaves may come straight back in the same trade, with a new
  position and salary: `trade(["Ada"], [("Ada", "SG", 10)])` keeps `Ada`
  on the roster, now at the end of `get_players()`, as a `SG` paid 10.
- If the trade raises, nothing changes. Otherwise the outgoing players are
  gone, and the incoming players are added at the end of `get_players()` in the
  order given.

All existing behavior must keep working.
