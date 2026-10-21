"""Hidden tests for the c_courses change (dishes grouped into courses). Never
shown to the writer or the editor.

Usage (with orders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_courses/private/test_courses_new.py
"""

import pytest
from orders import Restaurant, RestaurantError


@pytest.fixture
def rest():
    r = Restaurant()
    r.add_dish("soup", 650, course="starter")
    r.add_dish("steak", 2400)
    r.add_dish("salad", 900, course="starter")
    r.add_dish("cake", 700, course="dessert")
    r.add_dish("pasta", 1500, course="main")
    r.open_table("t1")
    r.open_table("t2")
    return r


def test_dishes_default_to_the_main_course(rest):
    rest.order("t1", "steak", 1)
    rest.order("t1", "pasta", 1)
    assert rest.get_course_order("t1", "main") == [("steak", 1), ("pasta", 1)]


def test_courses_appear_once_in_the_order_they_were_first_used(rest):
    assert rest.get_courses() == ["starter", "main", "dessert"]
    rest.add_dish("coffee", 300, course="drinks")
    assert rest.get_courses() == ["starter", "main", "dessert", "drinks"]


def test_a_restaurant_with_no_dishes_has_no_courses():
    assert Restaurant().get_courses() == []


def test_course_order_keeps_the_first_ordered_dish_order(rest):
    rest.order("t1", "salad", 1)
    rest.order("t1", "cake", 2)
    rest.order("t1", "soup", 2)
    rest.order("t1", "salad", 1)
    assert rest.get_course_order("t1", "starter") == [("salad", 2), ("soup", 2)]
    assert rest.get_course_order("t1", "dessert") == [("cake", 2)]
    assert rest.get_course_order("t1", "main") == []


def test_course_bills_add_up_to_the_table_bill(rest):
    rest.order("t1", "soup", 2)
    rest.order("t1", "steak", 1)
    rest.order("t1", "cake", 1)
    rest.order("t1", "salad", 1)
    starter = rest.get_course_bill("t1", "starter")
    main = rest.get_course_bill("t1", "main")
    dessert = rest.get_course_bill("t1", "dessert")
    assert (starter, main, dessert) == (2 * 650 + 900, 2400, 700)
    assert starter + main + dessert == rest.get_bill("t1")


def test_course_queries_are_per_table(rest):
    rest.order("t1", "soup", 1)
    rest.order("t2", "salad", 3)
    assert rest.get_course_order("t2", "starter") == [("salad", 3)]
    assert rest.get_course_bill("t2", "starter") == 2700
    assert rest.get_course_order("t1", "starter") == [("soup", 1)]


@pytest.mark.parametrize("course", ["", None, 7])
def test_invalid_courses_are_rejected_when_adding_a_dish(rest, course):
    with pytest.raises(ValueError):
        rest.add_dish("pie", 800, course=course)
    with pytest.raises(KeyError):
        rest.order("t1", "pie", 1)
    assert rest.get_courses() == ["starter", "main", "dessert"]


def test_a_bad_course_is_reported_before_a_duplicate_dish(rest):
    with pytest.raises(ValueError):
        rest.add_dish("soup", 650, course="")
    with pytest.raises(RestaurantError):
        rest.add_dish("soup", 650, course="dessert")
    assert rest.get_courses() == ["starter", "main", "dessert"]


@pytest.mark.parametrize("course", ["brunch", None, 7])
def test_unknown_courses_raise_key_error(rest, course):
    rest.order("t1", "soup", 1)
    with pytest.raises(KeyError):
        rest.get_course_order("t1", course)
    with pytest.raises(KeyError):
        rest.get_course_bill("t1", course)


@pytest.mark.parametrize("table", ["t9", None, 1])
def test_course_queries_on_a_table_that_is_not_open_raise_key_error(rest, table):
    with pytest.raises(KeyError):
        rest.get_course_order(table, "starter")
    with pytest.raises(KeyError):
        rest.get_course_bill(table, "starter")
    rest.close_table("t2")
    with pytest.raises(KeyError):
        rest.get_course_order("t2", "starter")


def test_adding_a_dish_to_a_course_does_not_change_open_orders(rest):
    rest.order("t1", "cake", 1)
    rest.add_dish("tart", 800, course="dessert")
    assert rest.get_course_order("t1", "dessert") == [("cake", 1)]
    assert rest.get_course_bill("t1", "dessert") == 700
