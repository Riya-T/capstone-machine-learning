"""Hidden tests for the c_double_booking change (a patient cannot be booked
twice at the same time). Never shown to the writer or the editor.

Usage (with clinic.py importable, e.g. in the sandbox):
    python -m pytest changes/c_double_booking/private/test_double_booking_new.py
"""

import pytest
from clinic import Clinic, ClinicError, DoubleBooking


@pytest.fixture
def clinic():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.add_doctor("dr_patel")
    for minute in (540, 600):
        cl.open_slot("dr_lee", 1, minute)
        cl.open_slot("dr_patel", 1, minute)
        cl.open_slot("dr_lee", 2, minute)
    cl.book("dr_lee", 1, 540, "ana")
    return cl


def state(cl):
    slots = {d: [cl.get_open_slots(d, day) for day in (1, 2)] for d in cl.get_doctors()}
    bookings = {p: cl.get_appointments(p) for p in ("ana", "ben")}
    return slots, bookings


def test_the_same_time_with_another_doctor_is_refused(clinic):
    before = state(clinic)
    with pytest.raises(DoubleBooking):
        clinic.book("dr_patel", 1, 540, "ana")
    assert state(clinic) == before


def test_other_times_on_the_same_day_are_fine(clinic):
    clinic.book("dr_patel", 1, 600, "ana")
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 540), ("dr_patel", 1, 600)]


def test_the_same_minute_on_another_day_is_fine(clinic):
    clinic.book("dr_lee", 2, 540, "ana")
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 540), ("dr_lee", 2, 540)]


def test_different_patients_may_share_a_time(clinic):
    clinic.book("dr_patel", 1, 540, "ben")
    assert clinic.get_appointments("ben") == [("dr_patel", 1, 540)]
    assert not clinic.is_free("ben", 1, 540)
    assert not clinic.is_free("ana", 1, 540)


def test_a_taken_slot_raises_a_plain_clinic_error_first(clinic):
    for patient in ("ana", "ben"):
        with pytest.raises(ClinicError) as info:
            clinic.book("dr_lee", 1, 540, patient)
        assert not isinstance(info.value, DoubleBooking)


def test_a_slot_that_was_never_opened_is_reported_before_double_booking(clinic):
    with pytest.raises(ClinicError) as info:
        clinic.book("dr_patel", 3, 540, "ana")
    assert not isinstance(info.value, DoubleBooking)


def test_key_and_value_errors_come_before_double_booking(clinic):
    with pytest.raises(KeyError):
        clinic.book("dr_who", 1, 540, "ana")
    with pytest.raises(ValueError):
        clinic.book("dr_patel", 0, 540, "ana")
    with pytest.raises(ValueError):
        clinic.book("dr_patel", 1, 1440, "ana")
    with pytest.raises(ValueError):
        clinic.book("dr_patel", 1, 540, "")


def test_after_a_cancellation_the_time_is_free_again(clinic):
    clinic.cancel("dr_lee", 1, 540)
    assert clinic.is_free("ana", 1, 540)
    clinic.book("dr_patel", 1, 540, "ana")
    assert clinic.get_appointments("ana") == [("dr_patel", 1, 540)]
    with pytest.raises(DoubleBooking):
        clinic.book("dr_lee", 1, 540, "ana")


def test_a_patient_with_no_bookings_is_free_at_every_time(clinic):
    assert clinic.is_free("ben", 1, 540)
    assert clinic.is_free("ben", 7, 0)
    assert clinic.is_free("ben", 1, 1439)


def test_is_free_tracks_every_appointment(clinic):
    clinic.book("dr_patel", 1, 600, "ana")
    clinic.book("dr_lee", 2, 540, "ana")
    assert [clinic.is_free("ana", 1, 540), clinic.is_free("ana", 1, 600)] == [False, False]
    assert [clinic.is_free("ana", 2, 540), clinic.is_free("ana", 2, 600)] == [False, True]


@pytest.mark.parametrize(
    "patient, day, minute",
    [("ana", 0, 540), ("ana", None, 540), ("ana", 1, -1), ("ana", 1, "540"), ("", 1, 540), (None, 1, 540)],
)
def test_is_free_rejects_invalid_arguments(clinic, patient, day, minute):
    with pytest.raises(ValueError):
        clinic.is_free(patient, day, minute)


def test_is_free_reports_a_bad_day_then_minute_then_patient(clinic):
    with pytest.raises(ValueError):
        clinic.is_free("", 0, 5000)
    with pytest.raises(ValueError):
        clinic.is_free("", 1, 5000)
    with pytest.raises(ValueError):
        clinic.is_free("", 1, 540)
