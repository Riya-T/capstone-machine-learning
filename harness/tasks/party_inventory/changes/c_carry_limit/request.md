Limit how much a character in `party.py` can carry by their strength.

- Add `class TooHeavy(PartyError)` to `party.py`.
- A character can hold items whose weights add up to at most their
  strength. `give_item` raises `TooHeavy` and changes nothing when the
  weight of the bag plus the weight of the new item would be more than the
  character's strength. Exactly the strength is allowed.
- Add `Party.get_carry_weight(name) -> int`: the total weight of the items
  in the character's bag, equipped or not. An empty bag weighs 0.
- Add `Party.get_strength(name) -> int`: the character's current strength.
- Add `Party.set_strength(name, strength)`, which replaces the strength. It
  raises `KeyError` for an unknown character, `ValueError` for an invalid
  strength (the same rule as `add_character`), and `PartyError` if the
  character already carries more than the new strength. In each case
  nothing changes.
- `get_carry_weight` and `get_strength` raise `KeyError` for an unknown
  character.
- When one call has several problems and at least one of them comes from
  this change (a load that would be too heavy, or any problem in
  `set_strength`), which error it raises is unspecified. For example,
  giving a character an item they already hold that would also be too
  heavy may raise `TooHeavy` or another `PartyError`.

All existing behavior must keep working.
