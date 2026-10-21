Let two characters in `party.py` swap items in one step.

- Add `Party.trade(first, first_item, second, second_item)`. `first` hands
  `first_item` to `second` and receives `second_item` in return. Each item
  leaves its old holder's bag and is appended to the end of the new
  holder's bag. Everything else in both bags, and all equipment, stays as
  it was.
- The trade either happens completely or not at all. When it fails, both
  bags are exactly as before, even if one side of the swap would have been
  fine on its own.
- Errors are raised in this order:
  1. `KeyError` for an unknown character (`first` is checked before
     `second`);
  2. `KeyError` for an unknown item (`first_item` before `second_item`);
  3. `ValueError` if `first` and `second` are the same character, or
     `first_item` and `second_item` are the same item;
  4. `PartyError` if `first` does not hold `first_item`, if `second` does
     not hold `second_item`, if either item is currently equipped by its
     holder, or if a character already holds the item they would receive;
  5. `TooHeavy` if, after the swap, either character's carry weight would be
     more than their strength.

All existing behavior must keep working.
