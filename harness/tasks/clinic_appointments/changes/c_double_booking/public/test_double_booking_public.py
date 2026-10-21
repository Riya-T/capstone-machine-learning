"""Public checks for the c_double_booking change (a patient cannot be booked
twice at the same time). Shown to the editor, never to the writer.

Usage (with clinic.py importable, e.g. in the sandbox):
    python -m pytest changes/c_double_booking/public/test_double_booking_public.py
"""

import pytest
from clinic import Clinic, ClinicError, DoubleBooking


@pytest.fixture
def clinic():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.add_doctor("dr_patel")
    cl.open_slot("dr_lee", 1, 540)
    cl.open_slot("dr_patel", 1, 540)
    cl.open_slot("dr_patel", 1, 600)
    return cl


def test_a_patient_cannot_be_booked_with_two_doctors_at_once(clinic):
    clinic.book("dr_lee", 1, 540, "ana")
    with pytest.raises(DoubleBooking):
        clinic.book("dr_patel", 1, 540, "ana")
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 540)]
    assert clinic.get_open_slots("dr_patel", 1) == [540, 600]


def test_double_booking_is_a_clinic_error(clinic):
    assert issubclass(DoubleBooking, ClinicError)


def test_is_free_reports_the_patients_booked_times(clinic):
    assert clinic.is_free("ana", 1, 540)
    clinic.book("dr_lee", 1, 540, "ana")
    assert not clinic.is_free("ana", 1, 540)
    assert clinic.is_free("ana", 1, 600)
    assert clinic.is_free("ben", 1, 540)
