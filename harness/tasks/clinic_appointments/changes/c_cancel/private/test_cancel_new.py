"""Hidden tests for the c_cancel change (cancelling bookings and closing
slots). Never shown to the writer or the editor.

Usage (with clinic.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
"""

import pytest
from clinic import Clinic, ClinicError


@pytest.fixture
def clinic():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.add_doctor("dr_patel")
    cl.open_slot("dr_lee", 1, 540)
    cl.open_slot("dr_lee", 1, 600)
    cl.open_slot("dr_lee", 1, 660)
    cl.open_slot("dr_patel", 1, 540)
    cl.book("dr_lee", 1, 540, "ana")
    cl.book("dr_patel", 1, 540, "ben")
    cl.book("dr_lee", 1, 600, "ana")
    return cl


def state(cl):
    slots = {d: [cl.get_open_slots(d, day) for day in (1, 2)] for d in cl.get_doctors()}
    bookings = {p: cl.get_appointments(p) for p in ("ana", "ben", "cho")}
    return slots, bookings


# --- cancel -----------------------------------------------------------------


def test_cancelling_keeps_the_other_appointments_in_order(clinic):
    clinic.cancel("dr_lee", 1, 540)
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 600)]
    assert clinic.get_appointments("ben") == [("dr_patel", 1, 540)]
    assert clinic.get_open_slots("dr_lee", 1) == [540, 660]


def test_a_cancelled_slot_can_be_booked_by_someone_else(clinic):
    clinic.cancel("dr_lee", 1, 540)
    clinic.book("dr_lee", 1, 540, "cho")
    assert clinic.get_appointments("cho") == [("dr_lee", 1, 540)]
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 600)]
    assert clinic.get_open_slots("dr_lee", 1) == [660]


def test_rebooking_a_cancelled_slot_goes_to_the_end_of_the_list(clinic):
    clinic.cancel("dr_lee", 1, 540)
    clinic.book("dr_lee", 1, 540, "ana")
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 600), ("dr_lee", 1, 540)]


def test_a_cancelled_slot_is_already_open(clinic):
    clinic.cancel("dr_lee", 1, 540)
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.open_slot("dr_lee", 1, 540)
    assert state(clinic) == before


def test_cancelling_every_appointment_leaves_an_empty_list(clinic):
    clinic.cancel("dr_lee", 1, 540)
    clinic.cancel("dr_lee", 1, 600)
    assert clinic.get_appointments("ana") == []
    assert clinic.get_open_slots("dr_lee", 1) == [540, 600, 660]


@pytest.mark.parametrize("minute", [660, 720])
def test_cancelling_an_unbooked_slot_changes_nothing(clinic, minute):
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.cancel("dr_lee", 1, minute)
    assert state(clinic) == before


def test_cancelling_twice_is_rejected(clinic):
    clinic.cancel("dr_lee", 1, 540)
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.cancel("dr_lee", 1, 540)
    assert state(clinic) == before


# --- close_slot -------------------------------------------------------------


def test_closing_leaves_the_other_slots_and_bookings(clinic):
    clinic.close_slot("dr_lee", 1, 660)
    assert clinic.get_open_slots("dr_lee", 1) == []
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 540), ("dr_lee", 1, 600)]
    assert clinic.get_open_slots("dr_patel", 1) == []


def test_a_closed_slot_can_be_opened_again(clinic):
    clinic.close_slot("dr_lee", 1, 660)
    clinic.open_slot("dr_lee", 1, 660)
    assert clinic.get_open_slots("dr_lee", 1) == [660]
    clinic.book("dr_lee", 1, 660, "cho")
    assert clinic.get_appointments("cho") == [("dr_lee", 1, 660)]


def test_a_booked_slot_cannot_be_closed(clinic):
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.close_slot("dr_lee", 1, 540)
    assert state(clinic) == before
    clinic.cancel("dr_lee", 1, 540)
    clinic.close_slot("dr_lee", 1, 540)
    assert clinic.get_open_slots("dr_lee", 1) == [660]


@pytest.mark.parametrize("minute", [720, 0])
def test_closing_a_slot_that_was_never_opened_changes_nothing(clinic, minute):
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.close_slot("dr_lee", 1, minute)
    assert state(clinic) == before


def test_closing_twice_is_rejected(clinic):
    clinic.close_slot("dr_lee", 1, 660)
    with pytest.raises(ClinicError):
        clinic.close_slot("dr_lee", 1, 660)


# --- errors -----------------------------------------------------------------


@pytest.mark.parametrize("method", ["cancel", "close_slot"])
def test_unknown_doctors_raise_key_error(clinic, method):
    before = state(clinic)
    with pytest.raises(KeyError):
        getattr(clinic, method)("dr_who", 1, 540)
    with pytest.raises(KeyError):
        getattr(clinic, method)(None, 0, -1)
    assert state(clinic) == before


@pytest.mark.parametrize("method", ["cancel", "close_slot"])
@pytest.mark.parametrize("day, minute", [(0, 540), ("1", 540), (1, -1), (1, 1440), (1, None)])
def test_invalid_days_and_minutes_raise_value_error(clinic, method, day, minute):
    before = state(clinic)
    with pytest.raises(ValueError):
        getattr(clinic, method)("dr_lee", day, minute)
    assert state(clinic) == before


@pytest.mark.parametrize("method", ["cancel", "close_slot"])
def test_a_bad_day_is_reported_before_a_bad_minute(clinic, method):
    with pytest.raises(ValueError):
        getattr(clinic, method)("dr_lee", 0, 5000)
