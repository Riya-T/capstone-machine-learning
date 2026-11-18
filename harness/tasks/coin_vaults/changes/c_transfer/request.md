Add a way to make several coin moves between vaults in one call that
succeeds or fails as a whole, so that a batch of moves never stops halfway.

- Add `Vaults.transfer(moves) -> int`. `moves` is a list of moves, each a
  tuple `(from_vault, to_vault, denomination, count)`: take `count` coins
  of `denomination` out of `from_vault` and put them into `to_vault`. The
  moves are made in list order, and `transfer` returns the total number of
  coins moved (the sum of the counts). An empty list moves nothing and
  returns 0.
- Each move follows the usual rules: a vault that is not in use raises
  `KeyError`; a count of 0 or less, or the same vault on both sides,
  raises `ValueError`; and `from_vault` must hold at least `count` coins of
  `denomination` at that point, otherwise `NotEnoughCoins` is raised. "At
  that point" counts the coins that earlier moves in the same list took out
  of it or put into it, so a vault may pass on coins it received earlier in
  the list.
- If any move fails, `transfer` raises that move's error and nothing
  changes: the moves before it in the list are not made either.
- When a move has more than one problem, which error is raised is
  unspecified.

All existing behavior must keep working.
