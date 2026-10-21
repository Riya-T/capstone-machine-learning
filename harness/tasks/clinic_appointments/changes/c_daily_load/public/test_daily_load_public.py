"""Public checks for the c_daily_load change (how busy each doctor is).
Shown to the editor, never to the writer.

Usage (with clinic.py importable, e.g. in the sandbox):
    python -m pytest changes/c_daily_load/public/test_daily_load_public.py
"""

from clinic import Clinic


def test_daily_load_counts_booked_slots_only():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.open_slot("dr_lee", 1, 540)
    cl.open_slot("dr_lee", 1, 600)
    cl.open_slot("dr_lee", 1, 660)
    cl.book("dr_lee", 1, 540, "ana")
    cl.book("dr_lee", 1, 600, "ben")
    assert cl.get_daily_load("dr_lee", 1) == 2
    assert cl.get_daily_load("dr_lee", 2) == 0


def test_load_by_day_lists_every_day_with_slots():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.open_slot("dr_lee", 3, 540)
    cl.open_slot("dr_lee", 1, 540)
    cl.book("dr_lee", 3, 540, "ana")
    assert cl.get_load_by_day("dr_lee") == [(1, 0), (3, 1)]


def test_patient_count_counts_each_patient_once():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.open_slot("dr_lee", 1, 540)
    cl.open_slot("dr_lee", 2, 540)
    assert cl.get_patient_count("dr_lee") == 0
    cl.book("dr_lee", 1, 540, "ana")
    cl.book("dr_lee", 2, 540, "ana")
    assert cl.get_patient_count("dr_lee") == 1
