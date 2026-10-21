Stop a patient from being booked in two places at once in `clinic.py`.

- Add `class DoubleBooking(ClinicError)` to `clinic.py`.
- `book` raises `DoubleBooking` when the patient already has an
  appointment on the same day and minute with any doctor, and changes
  nothing. Appointments on the same day at another minute, or at the same
  minute on another day, are fine, and different patients may of course be
  booked at the same time.
- `DoubleBooking` is checked last: after the `KeyError` and `ValueError`
  checks, and after the `ClinicError` for a slot that is not open for
  booking. So trying to book a slot that is already booked still raises a
  plain `ClinicError` that is not a `DoubleBooking`, whoever holds it.
- Once an appointment is cancelled, the patient can be booked at that time
  again.
- Add `Clinic.is_free(patient, day, minute) -> bool`, which tells whether
  the patient has no appointment at that day and minute. Raises `ValueError`
  for an invalid day, then an invalid minute, then an invalid patient (a
  patient must be a non-empty string). A patient with no bookings is free
  at every time.

All existing behavior must keep working.
