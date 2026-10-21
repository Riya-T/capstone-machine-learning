Sort the coaches in `seats.py` into groups, such as `"standard"` and
`"comfort"`, and let a booking ask for a group.

- `add_coach` takes a new keyword argument `group="standard"`. It must be
  a non-empty `str`; anything else raises `ValueError` and no coach is
  added. A coach's group never changes.
- Add `SeatPlanner.get_group(coach_id) -> str` (raises `KeyError` for a
  coach that was not added).
- Add `SeatPlanner.get_groups() -> list[str]`: every group that has at
  least one coach, each once, in the order their first coach was added.
- `get_coaches` takes a new keyword argument `group=None`. `None` means
  every coach, as before; otherwise only the coaches of that group are
  returned, still in the order they were added. A group with no coaches
  raises `KeyError`.
- `reserve` takes a new keyword argument `group=None`. `None` means any
  coach, as before. Otherwise the group goes into the first coach *of that
  group* that can take it, and `NotEnoughSeats` is raised if none can, even
  when a coach of another group has room. A group with no coaches raises
  `KeyError`.
- Add `SeatPlanner.get_group_available(group) -> int`: the sum of
  `get_available` over the group's coaches. A group with no coaches raises
  `KeyError`.
- `move` is unchanged: a booking may be moved to a coach of any group.

For `reserve`, the `KeyError` for an unknown group comes after every
`ValueError` and before the `ReservationError` for a booking id that is
already booked. All existing behavior must keep working.
