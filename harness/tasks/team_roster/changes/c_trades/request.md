Add trades to `roster.py`: some players leave and others join in a single
step, as in a real trade between two teams.

- Add `Roster.trade(outgoing, incoming)`. `outgoing` is a list of names of
  players on the roster. `incoming` is a list of `(name, position, salary)`
  tuples for the players who join. Either list may be empty.
- The trade is checked against the roster as it would be after the trade.
  When there are several problems, the first of these is raised:
  1. `KeyError` for an outgoing name that is not on the roster;
  2. `ValueError` if a name appears twice in `outgoing`;
  3. `ValueError` for an incoming player whose name, position or salary
     `add_player` would reject;
  4. `RosterError` if an incoming name appears twice in `incoming`, or is the
     name of a player who stays on the roster;
  5. `CapExceeded` if the roster after the trade would be over the salary
     cap, judged the same way `add_player` judges it.
- A player who leaves may come straight back in the same trade.
- If the trade raises, nothing changes. Otherwise the outgoing players are
  gone, and the incoming players are added at the end of `get_players()` in the
  order given.

All existing behavior must keep working.
