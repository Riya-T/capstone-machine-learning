"""Public checks for clinic.py.

Usage (with clinic.py importable, e.g. in the sandbox):
    python -m pytest public/test_clinic_public.py
"""

import pytest
from clinic import Clinic, ClinicError


@pytest.fixture
def clinic():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.add_doctor("dr_patel")
    return cl


def test_open_slots_are_listed_earliest_first(clinic):
    clinic.open_slot("dr_lee", 1, 600)
    clinic.open_slot("dr_lee", 1, 540)
    clinic.open_slot("dr_lee", 2, 570)
    assert clinic.get_open_slots("dr_lee", 1) == [540, 600]
    assert clinic.get_open_slots("dr_lee", 2) == [570]
    assert clinic.get_open_slots("dr_patel", 1) == []


def test_booking_takes_the_slot_and_records_the_appointment(clinic):
    clinic.open_slot("dr_lee", 1, 540)
    clinic.open_slot("dr_lee", 1, 600)
    clinic.book("dr_lee", 1, 540, "ana")
    assert clinic.get_open_slots("dr_lee", 1) == [600]
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 540)]
    assert clinic.get_appointments("ben") == []


def test_a_booked_slot_cannot_be_booked_again(clinic):
    clinic.open_slot("dr_lee", 1, 540)
    clinic.book("dr_lee", 1, 540, "ana")
    with pytest.raises(ClinicError):
        clinic.book("dr_lee", 1, 540, "ben")
    assert clinic.get_appointments("ben") == []


def test_a_slot_that_was_never_opened_cannot_be_booked(clinic):
    with pytest.raises(ClinicError):
        clinic.book("dr_lee", 1, 540, "ana")


def test_days_and_minutes_are_validated(clinic):
    with pytest.raises(ValueError):
        clinic.open_slot("dr_lee", 0, 540)
    with pytest.raises(ValueError):
        clinic.open_slot("dr_lee", 1, -1)
    assert clinic.get_open_slots("dr_lee", 1) == []


def test_unknown_doctor_raises_key_error(clinic):
    with pytest.raises(KeyError):
        clinic.open_slot("dr_who", 1, 540)
    with pytest.raises(KeyError):
        clinic.get_open_slots("dr_who", 1)
