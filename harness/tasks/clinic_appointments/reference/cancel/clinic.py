"""Clinic appointments where bookings can be cancelled and slots closed.

Correct solution for clinic_appointments after c_cancel.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from clinic import Clinic
    clinic = Clinic()
    clinic.add_doctor("dr_lee")
    clinic.open_slot("dr_lee", 1, 540)
    clinic.book("dr_lee", 1, 540, "ana")
    clinic.cancel("dr_lee", 1, 540)
"""

MINUTES_PER_DAY = 1440


class ClinicError(Exception):
    pass


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day < 1:
        raise ValueError(f"day must be an int >= 1, got {day!r}")


def check_minute(minute):
    if isinstance(minute, bool) or not isinstance(minute, int) or not 0 <= minute < MINUTES_PER_DAY:
        raise ValueError(f"minute must be an int from 0 to 1439, got {minute!r}")


def check_patient(patient):
    if not isinstance(patient, str) or not patient:
        raise ValueError(f"patient must be a non-empty str, got {patient!r}")


class Clinic:
    def __init__(self):
        self._open = {}  # doctor -> set of (day, minute) open for booking, in doctor order
        self._booked = {}  # doctor -> {(day, minute): patient}
        self._appointments = {}  # patient -> [(doctor, day, minute)] in booking order

    def add_doctor(self, doctor):
        if not isinstance(doctor, str) or not doctor:
            raise ValueError("doctor must be a non-empty str")
        if doctor in self._open:
            raise ClinicError(f"doctor {doctor!r} already exists")
        self._open[doctor] = set()
        self._booked[doctor] = {}

    def open_slot(self, doctor, day, minute):
        key = self._slot(doctor, day, minute)
        if key in self._open[doctor] or key in self._booked[doctor]:
            raise ClinicError(f"slot {key} of {doctor!r} is already open")
        self._open[doctor].add(key)

    def book(self, doctor, day, minute, patient):
        key = self._slot(doctor, day, minute)
        check_patient(patient)
        if key not in self._open[doctor]:
            raise ClinicError(f"slot {key} of {doctor!r} is not open for booking")
        self._open[doctor].remove(key)
        self._booked[doctor][key] = patient
        self._appointments.setdefault(patient, []).append((doctor, day, minute))

    def cancel(self, doctor, day, minute):
        key = self._slot(doctor, day, minute)
        if key not in self._booked[doctor]:
            raise ClinicError(f"slot {key} of {doctor!r} is not booked")
        patient = self._booked[doctor].pop(key)
        self._appointments[patient].remove((doctor, day, minute))
        self._open[doctor].add(key)

    def close_slot(self, doctor, day, minute):
        key = self._slot(doctor, day, minute)
        if key not in self._open[doctor]:
            raise ClinicError(f"slot {key} of {doctor!r} is not open and unbooked")
        self._open[doctor].remove(key)

    def get_open_slots(self, doctor, day):
        self._require(doctor)
        check_day(day)
        return sorted(minute for d, minute in self._open[doctor] if d == day)

    def get_appointments(self, patient):
        return list(self._appointments.get(patient, []))

    def get_doctors(self):
        return list(self._open)

    def _slot(self, doctor, day, minute):
        """Validate a slot's doctor, day and minute, in that order, and return its key."""
        self._require(doctor)
        check_day(day)
        check_minute(minute)
        return (day, minute)

    def _require(self, doctor):
        # Non-str names are never stored, so they count as "unknown" too.
        if not isinstance(doctor, str) or doctor not in self._open:
            raise KeyError(doctor)
