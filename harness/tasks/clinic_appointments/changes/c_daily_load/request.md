Report how busy each doctor is in `clinic.py`.

- Add `Clinic.get_daily_load(doctor, day) -> int`: the number of booked
  slots the doctor has on that day. Raises `KeyError` for a doctor that
  does not exist, then `ValueError` for an invalid day. A day without
  bookings gives 0.
- Add `Clinic.get_load_by_day(doctor) -> list[tuple[int, int]]`: one
  `(day, booked)` tuple for every day on which the doctor has at least one
  slot, open or booked, earliest day first, where `booked` is the number of
  booked slots that day. A doctor without slots gives `[]`. Raises `KeyError`
  for a doctor that does not exist.
- Add `Clinic.get_patient_count(doctor) -> int`: how many different
  patients hold at least one booking with the doctor. Raises `KeyError` for
  a doctor that does not exist.
- These numbers always reflect the current bookings. A slot that is no
  longer booked is not counted, and a patient with no remaining booking with
  the doctor is not counted.

All existing behavior must keep working.
