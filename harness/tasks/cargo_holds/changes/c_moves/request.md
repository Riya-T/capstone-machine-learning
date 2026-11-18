Let `ship.py` carry out a restowing plan, a list of moves, as one call.

- Add `Ship.apply_moves(moves) -> int`. `moves` is a list of tuples
  `(cargo, from_hold, to_hold, count)`, each moving `count` crates of
  `cargo` from `from_hold` to `to_hold`. The moves are carried out in list
  order, so a move may use crates that an earlier move in the same list
  brought into its hold. It returns the total number of crates moved (the
  sum of the counts).
- Each move follows the usual rules: both holds must be in use (otherwise
  `KeyError`), the count must be greater than 0 and the two holds must be
  different (otherwise `ValueError`), and when the move is reached
  `from_hold` must hold at least `count` crates of `cargo` (otherwise
  `NotEnoughCrates`).
- The plan succeeds or fails as a whole: if any move breaks a rule,
  `apply_moves` raises that move's error and changes nothing. The moves
  before it in the list do not take effect either: every count is left as
  it was before the call. When several moves break rules, or one move
  breaks several, which error is raised is unspecified.
- `apply_moves` never adds or removes holds, and a cargo type whose crates
  have all left a hold is no longer listed by `get_cargo` for that hold.

All existing behavior must keep working.
