# Clinic appointments

Write a module `clinic.py` that keeps the doctors of a clinic, the
appointment slots each doctor opens, and which patient has booked each slot.

## Interface

```python
class ClinicError(Exception): ...


class Clinic:
    def __init__(self): ...
    def add_doctor(self, doctor: str) -> None: ...
    def open_slot(self, doctor: str, day: int, minute: int) -> None: ...
    def book(self, doctor: str, day: int, minute: int, patient: str) -> None: ...
    def get_open_slots(self, doctor: str, day: int) -> list[int]: ...
    def get_appointments(self, patient: str) -> list[tuple[str, int, int]]: ...
    def get_doctors(self) -> list[str]: ...
```

A slot is identified by its doctor, a day number and a minute of that day.
Days are `int` values starting at 1. Minutes are `int` values from 0
(midnight) to 1439 (23:59), so 9:00 is minute 540.

## Doctors

- `add_doctor(doctor)` adds a doctor with no slots. An empty name raises
  `ValueError`, and a name that already exists raises `ClinicError`.
- `get_doctors()` returns the names of all doctors, in the order they were
  added.
- Every method that takes a doctor name raises `KeyError` when the doctor
  does not exist, including values that are not strings at all, such as
  `None` or `7`.

## Slots and bookings

- `open_slot(doctor, day, minute)` opens a slot the doctor can be booked
  for. A day that is not an `int` of 1 or more, or a minute that is not an
  `int` from 0 to 1439, raises `ValueError`. Opening a slot that doctor
  already has on that day and minute, whether still open or already booked,
  raises `ClinicError`.
- `book(doctor, day, minute, patient)` books the slot for the patient. The
  patient must be a non-empty string, or `ValueError` is raised. Booking a
  slot that is not open for booking, because it was never opened or is
  already booked, raises `ClinicError`.
- `get_open_slots(doctor, day)` returns the minutes of the doctor's slots on
  that day that are still unbooked, earliest first. It raises `ValueError`
  for an invalid day.
- `get_appointments(patient)` returns the patient's bookings as
  `(doctor, day, minute)` tuples, in the order they were booked. Patients
  are not registered anywhere: a patient with no bookings gives `[]`.

When a call has several problems, the first of these is raised:

1. `KeyError` for a doctor that does not exist;
2. `ValueError` for an invalid day;
3. `ValueError` for an invalid minute;
4. `ValueError` for an invalid patient;
5. `ClinicError`.

A failed call has no effect: if a method raises, every slot and every
booking is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` values passed as days or minutes, values that are not
strings passed to `get_appointments`, what happens if a returned list is
changed, the text of error messages, saving the clinic to a file, and use
from several threads.
