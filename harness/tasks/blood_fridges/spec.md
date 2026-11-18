# Blood fridges

Write a module `blood_bank.py` that keeps track of the blood in a hospital's
blood bank: how many units of each blood type are in each fridge, as units
are stored, taken out and moved from one fridge to another.

## Interface

```python
class BloodBankError(Exception): ...


class NotEnoughUnits(BloodBankError): ...


class BloodBank:
    def __init__(self): ...
    def add_fridge(self, name: str) -> None: ...
    def store(self, fridge: str, blood_type: str, count: int) -> None: ...
    def take(self, fridge: str, blood_type: str, count: int) -> None: ...
    def transfer_all(self, from_fridge: str, to_fridge: str) -> int: ...
    def retire_fridge(self, name: str, into: str) -> int: ...
    def get_units(self, fridge: str, blood_type: str) -> int: ...
    def get_blood_types(self, fridge: str) -> list[str]: ...
    def get_fridges(self) -> list[str]: ...
```

Fridge names and blood types (such as `"O-"` or `"AB+"`) are non-empty
strings, and counts are `int`.

## Fridges

- `add_fridge(name)` adds an empty fridge. A name that is already in use
  raises `BloodBankError`.
- `get_fridges()` returns the names of the fridges in use, in the order they
  were added.
- Every other method raises `KeyError` when given a fridge name that is not
  in use: one that was never added, or one that was retired.

## Units

- A count must be greater than 0; otherwise `ValueError` is raised.
- `store(fridge, blood_type, count)` adds `count` units of `blood_type` to
  the fridge. `take(fridge, blood_type, count)` takes them out.
- A fridge never holds fewer than 0 units of a blood type: a `take` of more
  units than the fridge has of that blood type (including a blood type it
  has none of) raises `NotEnoughUnits`.
- `transfer_all(from_fridge, to_fridge)` moves every unit of every blood
  type from `from_fridge` to `to_fridge` and returns how many units it moved
  in total. Afterwards `from_fridge` is empty but still in use. If
  `from_fridge` is empty, nothing changes and it returns 0.
- `retire_fridge(name, into)` moves every unit of every blood type from
  fridge `name` to fridge `into`, then removes fridge `name`: it is no longer
  listed by `get_fridges()`, and every method treats it as not in use. It
  returns how many units it moved in total (0 if the fridge was empty).
- `transfer_all` and `retire_fridge` raise `ValueError` when both names are
  the same fridge.
- `get_units(fridge, blood_type)` returns how many units of `blood_type` are
  in the fridge: 0 for a blood type that has never been there, or whose
  units have all been taken or moved away.
- `get_blood_types(fridge)` returns the blood types in the fridge, in
  alphabetical order (as `sorted` gives them). Every blood type with at
  least one unit in the fridge is listed; whether a blood type whose units
  have all been taken or moved away is still listed is unspecified.

Python note: a `dict` must not gain or lose keys while a `for` loop runs over
it (Python raises `RuntimeError`); if a loop over a fridge's units can add or
remove entries, loop over a copy such as `list(units.items())`.

## Errors

A failed call has no effect: if a method raises, every count and the list of
fridges are unchanged. When a call has more than one problem, which of the
errors is raised is unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type: counts that are not `int` (such as `1.5`,
`"3"`, `True` or `None`), and blood types or fridge names that are not
non-empty strings (such as `""`, `None` or `1`), wherever they are passed.
It also includes which error is raised when a call has several problems,
whether `get_blood_types` lists a blood type that has no units left,
adding a fridge under the name of a retired one, what happens if a returned
list is changed, the text of error messages, saving the bank to a file, and
use from several threads.
