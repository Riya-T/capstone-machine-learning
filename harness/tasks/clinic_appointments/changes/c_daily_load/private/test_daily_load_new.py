"""Hidden tests for the c_daily_load change (how busy each doctor is). Never
shown to the writer or the editor.

Usage (with clinic.py importable, e.g. in the sandbox):
    python -m pytest changes/c_daily_load/private/test_daily_load_new.py
"""

import pytest
from clinic import Clinic


@pytest.fixture
def clinic():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.add_doctor("dr_patel")
    cl.add_doctor("dr_kim")
    for minute in (540, 600, 660):
        cl.open_slot("dr_lee", 2, minute)
    cl.open_slot("dr_lee", 5, 540)
    cl.open_slot("dr_lee", 1, 900)
    cl.open_slot("dr_patel", 2, 540)
    cl.book("dr_lee", 2, 540, "ana")
    cl.book("dr_lee", 2, 660, "ben")
    cl.book("dr_lee", 5, 540, "ana")
    cl.book("dr_patel", 2, 540, "cho")
    return cl


def state(cl):
    slots = {d: [cl.get_open_slots(d, day) for day in (1, 2, 5)] for d in cl.get_doctors()}
    bookings = {p: cl.get_appointments(p) for p in ("ana", "ben", "cho")}
    return slots, bookings


def test_daily_load_is_per_doctor_and_per_day(clinic):
    assert clinic.get_daily_load("dr_lee", 2) == 2
    assert clinic.get_daily_load("dr_lee", 5) == 1
    assert clinic.get_daily_load("dr_lee", 1) == 0
    assert clinic.get_daily_load("dr_patel", 2) == 1
    assert clinic.get_daily_load("dr_kim", 2) == 0


def test_daily_load_grows_with_each_booking(clinic):
    clinic.book("dr_lee", 2, 600, "cho")
    assert clinic.get_daily_load("dr_lee", 2) == 3
    clinic.book("dr_lee", 1, 900, "cho")
    assert clinic.get_daily_load("dr_lee", 1) == 1


def test_load_by_day_is_sorted_and_includes_fully_booked_days(clinic):
    assert clinic.get_load_by_day("dr_lee") == [(1, 0), (2, 2), (5, 1)]
    assert clinic.get_load_by_day("dr_patel") == [(2, 1)]


def test_a_doctor_without_slots_has_no_load(clinic):
    assert clinic.get_load_by_day("dr_kim") == []
    assert clinic.get_patient_count("dr_kim") == 0


def test_load_by_day_matches_daily_load(clinic):
    for day, booked in clinic.get_load_by_day("dr_lee"):
        assert clinic.get_daily_load("dr_lee", day) == booked


def test_patient_count_counts_distinct_patients(clinic):
    assert clinic.get_patient_count("dr_lee") == 2
    assert clinic.get_patient_count("dr_patel") == 1
    clinic.book("dr_lee", 2, 600, "cho")
    assert clinic.get_patient_count("dr_lee") == 3
    clinic.book("dr_lee", 1, 900, "ben")
    assert clinic.get_patient_count("dr_lee") == 3


def test_reports_do_not_change_anything(clinic):
    before = state(clinic)
    clinic.get_daily_load("dr_lee", 2)
    clinic.get_load_by_day("dr_lee")
    clinic.get_patient_count("dr_lee")
    assert state(clinic) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda cl: cl.get_daily_load("dr_who", 1),
        lambda cl: cl.get_daily_load(None, 0),
        lambda cl: cl.get_load_by_day("dr_who"),
        lambda cl: cl.get_load_by_day(7),
        lambda cl: cl.get_patient_count("dr_who"),
        lambda cl: cl.get_patient_count(None),
    ],
)
def test_unknown_doctors_raise_key_error(clinic, call):
    with pytest.raises(KeyError):
        call(clinic)


@pytest.mark.parametrize("day", [0, -1, 1.5, "2", None])
def test_daily_load_rejects_invalid_days(clinic, day):
    with pytest.raises(ValueError):
        clinic.get_daily_load("dr_lee", day)
