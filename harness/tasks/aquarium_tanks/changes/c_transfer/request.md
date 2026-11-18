Let several moves of fish between tanks in `aquarium.py` be made as one
call that happens completely or not at all, for example when a whole
display is rearranged at once.

- Add `Aquarium.transfer(moves) -> int`. `moves` is a list of moves, each
  a tuple `(species, from_tank, to_tank, count)`: move `count` fish of
  `species` from `from_tank` into `to_tank`.
- The moves are made one after another in list order, so a move may use
  fish that an earlier move of the same list brought into its `from_tank`,
  and a later move cannot use fish that an earlier one took away.
- Each move follows these rules: a tank that is not in use raises
  `KeyError`; a `count` of 0 or less, or the same tank on both sides,
  raises `ValueError`; moving more fish than `from_tank` has of that
  species at that point raises `NotEnoughFish`.
- If any move fails, `transfer` raises that error and changes nothing at
  all: the moves before it in the list are not made either.
- On success it returns how many fish it moved in total (the sum of the
  counts). Species and tanks are listed as usual afterwards: a species
  with no fish left in a tank is no longer listed there, and the list of
  tanks does not change.
- An empty list, and which error is raised when a call has more than one
  problem, are unspecified.

All existing behavior must keep working.
