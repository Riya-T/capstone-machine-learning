Let bookings be cancelled and unneeded slots be closed in `clinic.py`.

- Add `Clinic.cancel(doctor, day, minute)`, which cancels the booking of
  that slot. The slot becomes open for booking again and the appointment
  disappears from the patient's list; the patient's other appointments
  keep their order. Raises `KeyError` for a doctor that does not exist,
  then `ValueError` for an invalid day, then `ValueError` for an invalid
  minute, then `ClinicError` when the slot is not booked (never opened, or
  open but unbooked).
- Add `Clinic.close_slot(doctor, day, minute)`, which removes an open,
  unbooked slot so it can no longer be booked. Raises `KeyError`, then the
  two `ValueError`s as above, then `ClinicError` when the slot is not open
  and unbooked (never opened, already closed, or currently booked). A
  booked slot has to be cancelled before it can be closed.
- A slot that was closed can be opened again with `open_slot`; a slot that
  was cancelled is already open and `open_slot` still raises `ClinicError`
  for it. A cancelled slot that is booked again is a new appointment, added
  at the end of that patient's list.
- A failed call changes nothing.

All existing behavior must keep working.
