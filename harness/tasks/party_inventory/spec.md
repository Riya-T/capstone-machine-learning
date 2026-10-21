# Adventuring party

Write a module `party.py` that keeps track of the characters in an
adventuring party, the items each one carries, and which of those items are
equipped.

## Interface

```python
class PartyError(Exception): ...


class Party:
    def __init__(self): ...
    def add_character(self, name: str, strength: int) -> None: ...
    def define_item(self, item: str, weight: int) -> None: ...
    def give_item(self, name: str, item: str) -> None: ...
    def equip(self, name: str, item: str) -> None: ...
    def unequip(self, name: str, item: str) -> None: ...
    def get_bag(self, name: str) -> list[str]: ...
    def get_equipped(self, name: str) -> list[str]: ...
```

Strengths and weights are whole units, as `int`.

## Characters and items

- `add_character(name, strength)` adds a character with an empty bag. The
  name must be a non-empty string and the strength an `int` greater
  than 0, or `ValueError` is raised. A name that is already in the party
  raises `PartyError`.
- `define_item(item, weight)` defines a kind of item. The item name must be
  a non-empty string and the weight an `int` greater than 0, or
  `ValueError` is raised. An item that is already defined raises
  `PartyError`.
- Every other method raises `KeyError` when given a character name or an
  item that is not known, including values that are not strings at all,
  such as `None` or `1`.

## Bags

- `give_item(name, item)` puts one of the item into the character's bag. A
  character holds at most one of each item: giving an item the character
  already holds raises `PartyError`. Different characters may hold the
  same item.
- `get_bag(name)` returns the items the character holds, in the order they
  were given, whether or not they are equipped.

## Equipment

- `equip(name, item)` equips an item the character holds. Equipping an
  item the character does not hold, or has already equipped, raises
  `PartyError`.
- `unequip(name, item)` takes an equipped item off again; it stays in the
  bag. Unequipping an item that is not equipped raises `PartyError`.
- `get_equipped(name)` returns the character's equipped items, in the order
  they were equipped.

When a call has several problems, the first of these is raised:

1. `KeyError` for an unknown character;
2. `KeyError` for an unknown item;
3. `ValueError` for an invalid argument;
4. `PartyError`.

A failed call has no effect: if a method raises, every bag and every set of
equipped items is unchanged, and no character or item is added.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_character` or
`define_item`, `bool` strengths and weights, a character and an item with
the same name, what happens if a returned list is changed, the text of
error messages, saving the party to a file, and use from several threads.
