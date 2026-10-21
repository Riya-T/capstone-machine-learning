Let staff take broken lockers out of service in `lockers.py`, and put them
back once they are repaired.

- Add `LockerRoom.set_out_of_order(locker_id)`,
  `LockerRoom.set_in_service(locker_id)` and
  `LockerRoom.is_out_of_order(locker_id) -> bool`. All three raise
  `KeyError` for a locker id that was not added, including values that are
  not strings. New lockers are in service. Marking a locker out of order
  when it already is, or in service when it already is, does nothing.
- No item can be put into a locker while it is out of order: `store` never
  picks one, and when the only lockers that would fit are out of order,
  `store` raises `NoLockerFree` and changes nothing.
- An out-of-order locker is never listed by `get_free_lockers`, even when
  it is empty.
- A locker may be marked out of order while an item is in it. The item stays
  where it is: `get_locker` still returns that locker and `retrieve` still
  hands the item back. After that the locker is empty but stays out of
  order until it is put back in service.
- Once back in service, an empty locker is free again and takes its usual
  place in `get_free_lockers` and in the choice made by `store`.
- Taking lockers out of service or back changes no fees and no takings.

All existing behavior must keep working.
