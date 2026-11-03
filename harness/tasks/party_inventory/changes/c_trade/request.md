Let two characters in `party.py` swap items in one step.

- Add `Party.trade(first, first_item, second, second_item)`. `first` hands
  `first_item` to `second` and receives `second_item` in return. Each item
  leaves its old holder's bag and is appended to the end of the new
  holder's bag. Everything else in both bags, and all equipment, stays as
  it was.
- The trade either happens completely or not at all. When it fails, both
  bags are exactly as before, even if one side of the swap would have been
  fine on its own.
- A trade fails with:
  - `KeyError` for an unknown character or an unknown item, including
    values that are not strings, such as `None`;
  - `ValueError` if `first` and `second` are the same character, or
    `first_item` and `second_item` are the same item;
  - `PartyError`, when both characters and both items are known and
    different, if `first` does not hold `first_item`, if `second` does not
    hold `second_item`, if either item is currently equipped by its holder,
    or if a character already holds the item they would receive;
  - `TooHeavy` if, after the swap, either character's carry weight would be
    more than their strength.
- When a trade has several of these problems, which error it raises is
  unspecified.

All existing behavior must keep working.
