"""Public checks for the c_cancel change (cancelling bookings and closing
slots). Shown to the editor, never to the writer.

Usage (with clinic.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/public/test_cancel_public.py
"""

import pytest
from clinic import Clinic, ClinicError


def test_cancelling_reopens_the_slot_and_drops_the_appointment():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.open_slot("dr_lee", 1, 540)
    cl.open_slot("dr_lee", 1, 600)
    cl.book("dr_lee", 1, 540, "ana")
    cl.book("dr_lee", 1, 600, "ana")
    cl.cancel("dr_lee", 1, 540)
    assert cl.get_open_slots("dr_lee", 1) == [540]
    assert cl.get_appointments("ana") == [("dr_lee", 1, 600)]


def test_closing_removes_an_unbooked_slot():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.open_slot("dr_lee", 1, 540)
    cl.open_slot("dr_lee", 1, 600)
    cl.close_slot("dr_lee", 1, 540)
    assert cl.get_open_slots("dr_lee", 1) == [600]
    with pytest.raises(ClinicError):
        cl.book("dr_lee", 1, 540, "ana")


def test_only_booked_slots_can_be_cancelled():
    cl = Clinic()
    cl.add_doctor("dr_lee")
    cl.open_slot("dr_lee", 1, 540)
    with pytest.raises(ClinicError):
        cl.cancel("dr_lee", 1, 540)
    with pytest.raises(ClinicError):
        cl.cancel("dr_lee", 1, 600)
    assert cl.get_open_slots("dr_lee", 1) == [540]
