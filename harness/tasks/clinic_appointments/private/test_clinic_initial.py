"""Hidden tests for the initial clinic_appointments spec. They decide whether
a program is correct to begin with. Never shown to the writer or the editor.

Usage (with clinic.py importable, e.g. in the sandbox):
    python -m pytest private/test_clinic_initial.py
"""

import pytest
from clinic import Clinic, ClinicError

BAD_DAYS = [0, -1, 1.5, "1", None]
BAD_MINUTES = [-1, 1440, 2000, 1.5, "540", None]
BAD_PATIENTS = ["", None]


@pytest.fixture
def clinic():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.add_doctor("dr_patel")
    cl.open_slot("dr_lee", 1, 540)
    cl.open_slot("dr_lee", 1, 600)
    cl.open_slot("dr_lee", 2, 540)
    cl.open_slot("dr_patel", 1, 540)
    cl.book("dr_lee", 1, 600, "ana")
    return cl


def state(cl):
    """Every doctor's open slots and every known patient's bookings, to check
    that a failed call changed nothing."""
    slots = {d: [cl.get_open_slots(d, day) for day in (1, 2, 3)] for d in cl.get_doctors()}
    bookings = {p: cl.get_appointments(p) for p in ("ana", "ben", "cho")}
    return slots, bookings


# --- doctors ----------------------------------------------------------------


def test_doctors_are_listed_in_the_order_added():
    cl = Clinic()
    for name in ["dr_zhou", "dr_adams", "dr_lee"]:
        cl.add_doctor(name)
    assert cl.get_doctors() == ["dr_zhou", "dr_adams", "dr_lee"]


def test_a_new_doctor_has_no_slots(clinic):
    clinic.add_doctor("dr_kim")
    assert clinic.get_open_slots("dr_kim", 1) == []


@pytest.mark.parametrize("name", [""])
def test_invalid_doctor_names_are_rejected(name):
    cl = Clinic()
    with pytest.raises(ValueError):
        cl.add_doctor(name)
    assert cl.get_doctors() == []


def test_adding_an_existing_doctor_is_rejected_and_keeps_the_slots(clinic):
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.add_doctor("dr_lee")
    assert state(clinic) == before
    assert clinic.get_doctors() == ["dr_lee", "dr_patel"]


@pytest.mark.parametrize(
    "call",
    [
        lambda cl: cl.open_slot("dr_who", 1, 540),
        lambda cl: cl.book("dr_who", 1, 540, "ben"),
        lambda cl: cl.get_open_slots("dr_who", 1),
        lambda cl: cl.open_slot(None, 1, 540),
        lambda cl: cl.book(7, 1, 540, "ben"),
        lambda cl: cl.get_open_slots(None, 1),
    ],
)
def test_unknown_doctors_raise_key_error(clinic, call):
    before = state(clinic)
    with pytest.raises(KeyError):
        call(clinic)
    assert state(clinic) == before


# --- slots ------------------------------------------------------------------


def test_open_slots_are_sorted_by_minute_not_by_opening_order(clinic):
    clinic.open_slot("dr_lee", 3, 900)
    clinic.open_slot("dr_lee", 3, 480)
    clinic.open_slot("dr_lee", 3, 720)
    assert clinic.get_open_slots("dr_lee", 3) == [480, 720, 900]


def test_slots_are_kept_per_doctor_and_per_day(clinic):
    assert clinic.get_open_slots("dr_lee", 1) == [540]
    assert clinic.get_open_slots("dr_lee", 2) == [540]
    assert clinic.get_open_slots("dr_patel", 1) == [540]
    assert clinic.get_open_slots("dr_patel", 2) == []


def test_the_first_and_last_minutes_of_a_day_are_valid(clinic):
    clinic.open_slot("dr_patel", 2, 0)
    clinic.open_slot("dr_patel", 2, 1439)
    assert clinic.get_open_slots("dr_patel", 2) == [0, 1439]


@pytest.mark.parametrize("day", BAD_DAYS)
def test_invalid_days_are_rejected(clinic, day):
    before = state(clinic)
    with pytest.raises(ValueError):
        clinic.open_slot("dr_lee", day, 540)
    with pytest.raises(ValueError):
        clinic.book("dr_lee", day, 540, "ben")
    with pytest.raises(ValueError):
        clinic.get_open_slots("dr_lee", day)
    assert state(clinic) == before


@pytest.mark.parametrize("minute", BAD_MINUTES)
def test_invalid_minutes_are_rejected(clinic, minute):
    before = state(clinic)
    with pytest.raises(ValueError):
        clinic.open_slot("dr_lee", 1, minute)
    with pytest.raises(ValueError):
        clinic.book("dr_lee", 1, minute, "ben")
    assert state(clinic) == before


def test_opening_an_open_slot_again_is_rejected(clinic):
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.open_slot("dr_lee", 1, 540)
    assert state(clinic) == before


def test_opening_a_booked_slot_again_is_rejected(clinic):
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.open_slot("dr_lee", 1, 600)
    assert state(clinic) == before
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 600)]


def test_the_same_time_can_be_opened_for_another_doctor(clinic):
    clinic.open_slot("dr_patel", 1, 600)
    assert clinic.get_open_slots("dr_patel", 1) == [540, 600]


# --- bookings ---------------------------------------------------------------


def test_booking_removes_the_slot_from_the_open_list(clinic):
    clinic.book("dr_lee", 1, 540, "ben")
    assert clinic.get_open_slots("dr_lee", 1) == []
    assert clinic.get_open_slots("dr_lee", 2) == [540]


def test_appointments_are_listed_in_booking_order(clinic):
    # Not sorted by day or doctor: the list follows booking order.
    clinic.book("dr_lee", 2, 540, "ana")
    clinic.book("dr_patel", 1, 540, "ana")
    assert clinic.get_appointments("ana") == [
        ("dr_lee", 1, 600),
        ("dr_lee", 2, 540),
        ("dr_patel", 1, 540),
    ]


def test_appointments_are_kept_per_patient(clinic):
    clinic.book("dr_lee", 1, 540, "ben")
    assert clinic.get_appointments("ana") == [("dr_lee", 1, 600)]
    assert clinic.get_appointments("ben") == [("dr_lee", 1, 540)]
    assert clinic.get_appointments("cho") == []


def test_booking_a_booked_slot_changes_nothing(clinic):
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.book("dr_lee", 1, 600, "ben")
    with pytest.raises(ClinicError):
        clinic.book("dr_lee", 1, 600, "ana")
    assert state(clinic) == before


def test_booking_a_slot_that_was_never_opened_changes_nothing(clinic):
    before = state(clinic)
    with pytest.raises(ClinicError):
        clinic.book("dr_lee", 1, 630, "ben")
    with pytest.raises(ClinicError):
        clinic.book("dr_patel", 2, 540, "ben")
    assert state(clinic) == before


@pytest.mark.parametrize("patient", BAD_PATIENTS)
def test_invalid_patients_are_rejected(clinic, patient):
    before = state(clinic)
    with pytest.raises(ValueError):
        clinic.book("dr_lee", 1, 540, patient)
    assert state(clinic) == before


def test_an_unknown_doctor_is_reported_before_a_bad_day(clinic):
    with pytest.raises(KeyError):
        clinic.open_slot("dr_who", 0, -1)
    with pytest.raises(KeyError):
        clinic.book("dr_who", 0, -1, "")


def test_a_bad_day_is_reported_before_a_bad_minute(clinic):
    with pytest.raises(ValueError):
        clinic.open_slot("dr_lee", 0, 5000)


def test_a_bad_minute_is_reported_before_a_bad_patient(clinic):
    with pytest.raises(ValueError):
        clinic.book("dr_lee", 1, 5000, "")


def test_a_bad_patient_is_reported_before_a_taken_slot(clinic):
    with pytest.raises(ValueError):
        clinic.book("dr_lee", 1, 600, "")
    with pytest.raises(ValueError):
        clinic.book("dr_lee", 1, 630, "")


def test_clinics_do_not_share_doctors():
    first, second = Clinic(), Clinic()
    first.add_doctor("dr_lee")
    first.open_slot("dr_lee", 1, 540)
    first.book("dr_lee", 1, 540, "ana")
    assert second.get_doctors() == []
    assert second.get_appointments("ana") == []
    second.add_doctor("dr_lee")
    assert second.get_open_slots("dr_lee", 1) == []
