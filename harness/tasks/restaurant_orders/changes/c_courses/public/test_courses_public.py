"""Public checks for the c_courses change (dishes grouped into courses).
Shown to the editor, never to the writer.

Usage (with orders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_courses/public/test_courses_public.py
"""

import pytest
from orders import Restaurant


@pytest.fixture
def rest():
    r = Restaurant()
    r.add_dish("soup", 650, course="starter")
    r.add_dish("steak", 2400)
    r.add_dish("cake", 700, course="dessert")
    r.open_table("t1")
    return r


def test_courses_are_listed_in_menu_order(rest):
    assert rest.get_courses() == ["starter", "main", "dessert"]


def test_course_order_and_bill_cover_one_course(rest):
    rest.order("t1", "steak", 2)
    rest.order("t1", "soup", 1)
    rest.order("t1", "cake", 3)
    assert rest.get_course_order("t1", "dessert") == [("cake", 3)]
    assert rest.get_course_bill("t1", "dessert") == 2100
    assert rest.get_course_order("t1", "main") == [("steak", 2)]
    assert rest.get_bill("t1") == 4800 + 650 + 2100


def test_a_course_nobody_ordered_is_empty(rest):
    rest.order("t1", "steak", 1)
    assert rest.get_course_order("t1", "starter") == []
    assert rest.get_course_bill("t1", "starter") == 0
