Add status effects to characters in `party.py`, which limit what they can
do while the effect lasts.

- Add `Party.apply_effect(name, effect)`, `Party.remove_effect(name, effect)`
  and `Party.get_effects(name) -> list[str]`. All three raise `KeyError` for
  an unknown character. The known effects are `"stunned"` and
  `"petrified"`; any other effect raises `ValueError`. New characters have
  no effects. Applying an effect the character already has, or removing one
  they do not have, does nothing. `get_effects` lists the character's
  current effects in the order they were applied.
- Add `class Incapacitated(PartyError)` to `party.py`.
- While a character is stunned or petrified, `equip` and `unequip` for that
  character raise `Incapacitated` and change nothing. While a character is
  petrified, `give_item` to that character also raises `Incapacitated` and
  changes nothing. A character with both effects is treated as petrified.
- When one call has several problems and at least one of them comes from
  this change (an unknown effect, or an incapacitated character), which
  error it raises is unspecified. For example, a petrified character
  equipping an item they do not hold may raise `Incapacitated` or another
  `PartyError`.
- Applying or removing an effect changes no bag and no equipment: items
  that were equipped stay equipped.

All existing behavior must keep working.
