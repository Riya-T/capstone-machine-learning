Let guests be looked up in `seating.py`, so place cards can show each
guest's table and seat.

- Add `SeatingChart.get_table_of(guest) -> str`, which returns the name
  of the table the guest sits at.
- Add `SeatingChart.get_seat_number(guest) -> int`, which returns the
  guest's place in their table's seating order, counting from 1 for the
  first guest in `get_guests(table)`.
- Both raise `KeyError` for a guest who is not seated: one who was never
  seated, was unseated, or was removed with their table by `clear_table`.
- Both always reflect the current chart: a guest moved by `move_guest` or
  `merge_tables` is found at their new table and place, and when a guest
  leaves a table, every guest after them at that table moves up one
  place.
- Neither method changes anything.

All existing behavior must keep working.
