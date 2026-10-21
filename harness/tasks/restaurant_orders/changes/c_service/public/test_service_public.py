"""Public checks for the c_service change (service charge and takings).
Shown to the editor, never to the writer.

Usage (with orders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_service/public/test_service_public.py
"""

from orders import Restaurant


def test_the_bill_includes_the_service_charge():
    r = Restaurant(service_percent=10)
    r.add_dish("soup", 650)
    r.open_table("t1")
    r.order("t1", "soup", 2)
    assert r.get_subtotal("t1") == 1300
    assert r.get_service_charge("t1") == 130
    assert r.get_bill("t1") == 1430


def test_takings_add_up_closed_tables():
    r = Restaurant(service_percent=10)
    r.add_dish("soup", 650)
    r.open_table("t1")
    r.open_table("t2")
    r.order("t1", "soup", 2)
    r.order("t2", "soup", 1)
    assert r.get_takings() == 0
    r.close_table("t1")
    assert r.get_takings() == 1430
    r.close_table("t2")
    assert r.get_takings() == 1430 + 715


def test_without_a_service_charge_the_bill_is_the_subtotal():
    r = Restaurant()
    r.add_dish("soup", 650)
    r.open_table("t1")
    r.order("t1", "soup", 1)
    assert r.get_service_charge("t1") == 0
    assert r.get_bill("t1") == 650
